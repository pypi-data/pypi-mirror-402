import json
import os
import shutil
import stat
import subprocess
import time
from dataclasses import asdict, dataclass

from rich import print

from btpy.configuration.config import KeyVaultInfo, get_config_value
from btpy.core.azure_utility import (
    assign_subscription_role,
    create_service_principal,
    delete_service_principal,
    get_current_subscription,
    get_keyvault_secret,
    get_keyvault_secret_to_file,
    get_service_principals_by_name,
    get_storage_table_entry,
    list_storage_table_entries,
    location_tag,
    set_keyvault_admin_rbac,
    upload_keyvault_secret,
    upload_keyvault_secret_file,
    upsert_table_storage_entry,
)
from btpy.core.file_utility import generate_file_from_template, to_absolute_path
from btpy.core.misc_utility import (
    create_domain,
    get_gh_btenvs_app_info,
    init_git_repo,
    setup_ssh_keys,
)
from btpy.core.rancher_utility import (
    get_or_create_rancher_azure_credential,
    get_rancher_mgmt_info,
)
from btpy.core.iac_utility import bootstrap_tf_repo, get_keyvault_name
from btpy.iac.suffix import generate

ENV_LIST_TABLE_NAME = "envs"


@dataclass
class EnvListInfo:
    tenant_id: str
    subscription_id: str
    name: str


@dataclass
class EnvInfo:
    tenant_id: str
    subscription_id: str
    name: str
    keyvault_name: str


@dataclass
class EnvTemplateData:
    customer: str
    environment: str
    resource_group: str
    location: str
    shloc: str
    suffix: str
    keyvault_name: str
    tenant_id: str
    sp_client_id: str
    sp_client_secret: str
    rancher_api_url: str
    rancher_api_token: str
    rancher_cloud_creds_name: str
    gh_btenvs_app_id: str
    gh_btenvs_app_private_key_path: str
    gh_btenvs_installation_id: str
    env_domain: str


def list_envs() -> list[EnvInfo]:
    env_list_info = _get_env_list_info()
    query_result = list_storage_table_entries(
        env_list_info.name, ENV_LIST_TABLE_NAME, env_list_info.subscription_id
    )
    return [EnvInfo(**json.loads(entry["Data"])) for entry in query_result["items"]]


def get_env_info(env_name) -> EnvInfo | None:
    env_list_info = _get_env_list_info()
    query_result = get_storage_table_entry(
        env_list_info.name,
        ENV_LIST_TABLE_NAME,
        env_list_info.subscription_id,
        env_name,
        env_name,
    )

    if query_result:
        return EnvInfo(**json.loads(query_result["Data"]))
    return None


@dataclass
class EnvCreationOptions:
    customer: str
    environment: str
    location: str
    suffix: str | None = None
    regen_ssh: bool = False
    regen_sp: bool = False
    subdomain: str | None = None


def create_env(options: EnvCreationOptions):
    if options.suffix is None:
        options.suffix = generate()["suffix"]

    shloc = location_tag(options.location)

    env_name = f"{options.customer}-{options.environment}-{shloc}{options.suffix}"
    folder = f"env-{options.customer}-{options.environment}-{shloc}{options.suffix}"
    infra_folder = os.path.join(folder, "terraform")
    flux_infra_folder = os.path.join(folder, "kubernetes", "infrastructure", "configs")

    print(f"[cyan]Creating env {env_name}")

    # Clone env template repo
    if not os.path.isdir(folder):

        def __on_rm_error(func, path, exc):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        repo_url = "https://github.com/beacontower/env-template.git"
        subprocess.run(
            ["git", "clone", "--branch", "master", repo_url, folder], check=True
        )
        shutil.rmtree(os.path.join(folder, ".git"), onerror=__on_rm_error)
    else:
        print(f"[blue]Repo folder {folder} already exists")

    # Set up resource group, storage account for TF and key vault
    tf_data = bootstrap_tf_repo(
        options.customer,
        options.environment,
        options.location,
        options.suffix,
        prefix="env",
        folder=infra_folder,
    )
    time.sleep(6)  # Wait and hope role assignment has refreshed cache on the servers

    if tf_data is None:
        return

    keyvault_name = tf_data.keyvault_name

    # Register env in env list
    _add_env_to_storage(env_name, keyvault_name)

    # Generate and store git repo SSH key
    secrets_folder_name = ".secrets"
    secrets_path = os.path.join(folder, "terraform", secrets_folder_name)
    if not os.path.isdir(secrets_path):
        os.mkdir(secrets_path)

    setup_ssh_keys(
        keyvault_name,
        secrets_path,
        "Auto-generated BT env repo SSH keys",
        options.regen_ssh,
    )

    # Set up service principal used for key vault and monitoring access
    sp = _setup_service_principal(
        f"sp-bt-env-{env_name}",
        keyvault_name,
        tf_data.keyvault_id,
        tf_data.subscription_id,
    )

    # Misc secrets
    upload_keyvault_secret(keyvault_name, "env-name", env_name)
    rancher_credentials = get_or_create_rancher_azure_credential(
        tf_data.tenant_id, tf_data.subscription_id
    )
    _setup_charts_ssh_key(keyvault_name, secrets_path)
    upload_keyvault_secret(
        keyvault_name,
        "otel-url",
        "http://otel-collector.monitoring.svc.cluster.local:4317",
    )
    upload_keyvault_secret(keyvault_name, "az-tenant-id", tf_data.tenant_id)
    upload_keyvault_secret(keyvault_name, "az-subscription-id", tf_data.subscription_id)

    # Get github btenvs repo auth info and store in secret file
    gh_btenvs_app_info = get_gh_btenvs_app_info()
    gh_btenvs_app_key_filename = "gh_betenvs_app_key.pem"
    gh_btenvs_app_private_key_path = os.path.join(
        secrets_path, gh_btenvs_app_key_filename
    )
    relative_gh_btenvs_app_private_key_path = os.path.join(
        secrets_folder_name, gh_btenvs_app_key_filename
    )
    with open(gh_btenvs_app_private_key_path, "w") as key_file:
        key_file.write(gh_btenvs_app_info.private_key)

    rancher_mgmt_info = get_rancher_mgmt_info()

    env_domain = create_domain(options.subdomain)
    upload_keyvault_secret(keyvault_name, "env-domain", env_domain)

    env_data = EnvTemplateData(
        customer=tf_data.customer,
        environment=tf_data.environment,
        resource_group=tf_data.resource_group,
        location=tf_data.location,
        shloc=tf_data.shloc,
        suffix=tf_data.suffix,
        keyvault_name=keyvault_name,
        tenant_id=tf_data.tenant_id,
        sp_client_id=sp["appId"],
        sp_client_secret=sp["password"],
        rancher_api_url=rancher_mgmt_info.url,
        rancher_api_token=rancher_mgmt_info.token,
        rancher_cloud_creds_name=rancher_credentials.name,
        gh_btenvs_app_id=gh_btenvs_app_info.app_id,
        gh_btenvs_app_private_key_path=relative_gh_btenvs_app_private_key_path,
        gh_btenvs_installation_id=gh_btenvs_app_info.installation_id,
        env_domain=env_domain,
    )
    generate_file_from_template(
        to_absolute_path(__file__, "templates/env-terraform.tfvars.json.mustache"),
        os.path.join(infra_folder, "terraform.tfvars.json"),
        asdict(env_data),
    )
    generate_file_from_template(
        to_absolute_path(__file__, "templates/env-eso.yaml.mustache"),
        os.path.join(flux_infra_folder, "external-secrets.yaml"),
        asdict(env_data),
    )
    generate_file_from_template(
        to_absolute_path(__file__, "templates/env-config.yaml.mustache"),
        os.path.join(flux_infra_folder, "env-config.yaml"),
        asdict(env_data),
    )

    # Prepare git repo
    if not init_git_repo(folder, "env"):
        return


def _setup_charts_ssh_key(env_keyvault, secret_folder_path):
    # Copy from global key vault
    global_kv_info = KeyVaultInfo(**get_config_value("global_keyvault"))
    key_path = os.path.join(secret_folder_path, "charts_repo_ssh_key")
    get_keyvault_secret_to_file(global_kv_info.name, "charts-repo-ssh-key", key_path)
    upload_keyvault_secret_file(env_keyvault, "charts-repo-ssh-key", key_path)


def _setup_service_principal(name, keyvault_name, keyvault_id, subscription_id):
    existing_sp_client_id = get_keyvault_secret(keyvault_name, "sp-client-id")
    existing_sp_client_secret = get_keyvault_secret(keyvault_name, "sp-client-secret")

    if existing_sp_client_id and existing_sp_client_secret:
        # Ensure existing SP has Contributor role
        set_keyvault_admin_rbac(keyvault_id, existing_sp_client_id)
        _setup_service_principal_roles(subscription_id, existing_sp_client_id)
        return {"appId": existing_sp_client_id, "password": existing_sp_client_secret}

    # Clean up potentially existing SPs
    existing_sps = get_service_principals_by_name(name)

    if existing_sps:
        for sp in existing_sps:
            delete_service_principal(sp["id"])

    sp = create_service_principal(name)
    set_keyvault_admin_rbac(keyvault_id, sp["appId"])

    # Assign Contributor role for Azure resource management (e.g., disk provisioning)
    _setup_service_principal_roles(subscription_id, sp["appId"])

    upload_keyvault_secret(keyvault_name, "sp-client-id", sp["appId"])
    upload_keyvault_secret(keyvault_name, "sp-client-secret", sp["password"])

    return sp


def _setup_service_principal_roles(subscription_id, sp_client_id):
    assign_subscription_role(subscription_id, sp_client_id, "Contributor")
    assign_subscription_role(subscription_id, sp_client_id, "Monitoring Reader")


def _add_env_to_storage(env_name, keyvault_name):
    print("[blue]Adding env to global env list...", end=" ")
    env_list_info = _get_env_list_info()
    list_sub_id = env_list_info.subscription_id
    list_name = env_list_info.name
    sub_info = get_current_subscription()
    env_info = EnvInfo(
        tenant_id=sub_info["tenantId"],
        subscription_id=sub_info["id"],
        name=env_name,
        keyvault_name=keyvault_name,
    )
    min_env_data = json.dumps(asdict(env_info), separators=(",", ":"))
    upsert_table_storage_entry(
        list_name,
        ENV_LIST_TABLE_NAME,
        env_name,
        env_name,
        min_env_data,
        list_sub_id,
        log=False,
    )
    print("[green]Complete")


def get_env_kubectl(env_name):
    env_info = get_env_info(env_name)
    return get_keyvault_secret(env_info.keyvault_name, "kubeconfig")


def _get_env_list_info() -> EnvListInfo:
    env_acc_config = KeyVaultInfo(**get_config_value("env_list_storage_account"))
    return EnvListInfo(
        tenant_id=env_acc_config.tenant,
        subscription_id=env_acc_config.subscription,
        name=env_acc_config.name,
    )


@dataclass
class EnvMonitorInfo:
    url: str


def get_env_monitor_info(env) -> EnvMonitorInfo:
    keyvault_name = get_keyvault_name(env)
    env_domain = get_keyvault_secret(keyvault_name, "env-domain")

    return EnvMonitorInfo(f"https://{env_domain}/monitor")
