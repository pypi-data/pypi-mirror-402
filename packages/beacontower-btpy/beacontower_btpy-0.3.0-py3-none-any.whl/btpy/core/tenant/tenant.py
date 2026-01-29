import json
import os
import secrets
import shutil
import stat
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass

import yaml
from azure.eventhub import EventHubConsumerClient
from rich import print

from btpy.core.azure_utility import (
    assign_keyvault_reader_role,
    create_service_principal,
    delete_keyvault_secret,
    delete_service_principal,
    get_current_subscription,
    get_keyvault_secret,
    get_keyvault_secret_to_file,
    get_service_principals_by_name,
    location_tag,
    query_keyvault_secrets,
    upload_keyvault_secret,
    upload_keyvault_secret_file,
    upsert_table_storage_entry,
)
from btpy.core.envs.env2 import get_env_info, get_env_kubectl, _get_env_list_info
from btpy.core.file_utility import generate_file_from_template, to_absolute_path
from btpy.core.iac_utility import bootstrap_tf_repo, get_keyvault_name
from btpy.core.k8s_utility import parallel_pod_curl
from btpy.core.misc_utility import (
    create_domain,
    generate_password,
    get_gh_btenvs_app_info,
    init_git_repo,
    setup_ssh_keys,
)
from btpy.core.versions import get_bt_version, write_version_file
from btpy.iac.suffix import generate

TENANT_LIST_TABLE_NAME = "tenants"


@dataclass
class TenantTemplateData:
    resource_group: str
    env_name: str
    customer: str
    suffix: str
    location: str
    shloc: str
    keyvault_name: str
    acr_name: str
    acr_password: str
    acr_registry: str
    kubeconfig_path: str
    keyvault_sp_id: str
    keyvault_sp_secret: str
    tenant_namespace: str
    github_app_id: str
    github_app_private_key_path: str
    github_installation_id: str
    az_tenant_id: str
    tenant_domain: str
    subscription_id: str
    provider_iothubs: str


def list_tenants(env, method="env-list"):
    env_info = get_env_info(env)

    if method == "env-list":
        tenant_secret_prefix = "tenant-"
        tenant_secrets = query_keyvault_secrets(
            env_info.keyvault_name,
            f"[?contains(name, '{tenant_secret_prefix}')].name",
            env_info.subscription_id,
        )
        tenants = [name.removeprefix("tenant-repo-ssh-key-") for name in tenant_secrets]
        return tenants
    elif method == "repo":
        result = subprocess.run(
            [
                "gh",
                "repo",
                "list",
                "beacontower",
                "--json",
                "name",
                "-q",
                """.[]|select(.name|startswith("tenant-"))""",
            ],
            capture_output=True,
        )

        if result.returncode != 0:
            print(result.stderr)
            print(result.stdout)
            print("[red]Failed to query gh CLI for beacontower tenant repos")
            return

        tenants = json.loads(result.stdout)
        print(tenants)


@dataclass
class TenantCreationOptions:
    customer: str
    tenant_env: str
    location: str
    cluster_env: str
    subdomain: str | None = None
    version: str = "latest"
    suffix: str | None = None
    regen_ssh: bool = False


def create_tenant(options: TenantCreationOptions):
    env = get_env_info(options.cluster_env)

    if not env:
        print(f"[red]Environment cluster {options.cluster_env} does not exist")
        return

    env_kv = env.keyvault_name
    version = get_bt_version(options.version)

    if not version:
        print(f"[red]BT version {options.version} not found")
        return

    if options.suffix is None:
        options.suffix = generate()["suffix"]

    shloc = location_tag(options.location)
    tenant_name = f"{options.customer}-{options.tenant_env}-{shloc}{options.suffix}"
    folder = f"tenant-{tenant_name}"
    tf_folder = os.path.join(folder, "terraform")
    k8s_folder = os.path.join(folder, "kubernetes")

    print(f"[cyan]Creating tenant {tenant_name}")

    # Clone the tenant base repo and remove the .git folder
    if not os.path.isdir(folder):

        def __on_rm_error(func, path, exc):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        # TODO: Should use version tags eventually
        repo_url = "https://github.com/beacontower/tenant-template.git"
        subprocess.run(
            ["git", "clone", "--branch", "master", repo_url, folder], check=True
        )
        shutil.rmtree(os.path.join(folder, ".git"), onerror=__on_rm_error)
    else:
        print(f"[blue]Repo folder {folder} already exists")

    # Gather some env values
    acr_name = get_keyvault_secret(env_kv, "acr-username")
    acr_password = get_keyvault_secret(env_kv, "acr-password")
    acr_registry = get_keyvault_secret(env_kv, "acr-registry")
    otel_url = get_keyvault_secret(env_kv, "otel-url")
    az_sub = get_current_subscription()
    subscription_id = az_sub["id"]

    # Init tfvars data
    tf_data = bootstrap_tf_repo(
        options.customer,
        options.tenant_env,
        options.location,
        options.suffix,
        "tenant",
        tf_folder,
    )

    if tf_data is None:
        return

    # TODO: Find better way to make sure rbac has been refreshed, if it fails when run, just run again
    time.sleep(6)

    keyvault_name = tf_data.keyvault_name
    sp = _setup_eso_reader_sp(
        f"sp-bt-tenant-{tenant_name}-kvr",
        keyvault_name,
        tf_data.keyvault_id,
        tf_data.subscription_id,
    )

    # Add tenant to tenant list
    _add_tenant_to_storage(tenant_name, env.name, keyvault_name)

    # Set some secrets in tenant key vault
    secrets_folder_name = ".secrets"
    secrets_path = os.path.join(tf_folder, secrets_folder_name)
    if not os.path.exists(secrets_path):
        os.mkdir(secrets_path)

    kubeconfig_path = os.path.join(secrets_path, "kubeconfig.yaml")
    relative_kubeconfig_path = os.path.join(secrets_folder_name, "kubeconfig.yaml")
    get_keyvault_secret_to_file(env_kv, "kubeconfig", kubeconfig_path)
    upload_keyvault_secret_file(keyvault_name, "kubeconfig", kubeconfig_path)
    upload_keyvault_secret(keyvault_name, "otel-url", otel_url)

    setup_ssh_keys(
        keyvault_name,
        secrets_path,
        "Auto-generated BT tenant repo SSH keys",
        options.regen_ssh,
    )

    _setup_charts_ssh_key(env_kv, keyvault_name, secrets_path)

    upload_keyvault_secret(keyvault_name, "env-keyvault-name", env_kv)
    upload_keyvault_secret(keyvault_name, "env-name", options.cluster_env)
    upload_keyvault_secret(keyvault_name, "tenant-name", tenant_name)

    # Get github auth info and store in secret file
    gh_app_info = get_gh_btenvs_app_info()
    gh_app_key_filename = "gh_app_key.pem"
    gh_app_private_key_path = os.path.join(secrets_path, gh_app_key_filename)
    relative_gh_app_private_key_path = os.path.join(
        secrets_folder_name, gh_app_key_filename
    )
    with open(gh_app_private_key_path, "w") as key_file:
        key_file.write(gh_app_info.private_key)

    # Generate tenant's domain
    tenant_subdomain = options.subdomain if options.subdomain else tenant_name
    tenant_domain = create_domain(tenant_subdomain)
    upload_keyvault_secret(keyvault_name, "tenant-domain", tenant_domain)

    iothub_name = f"iot-bt-device-{tenant_name}"
    provider_iothubs_string = json.dumps(
        [
            {
                "name": iothub_name,
                "resource_group": tf_data.resource_group,
                "dedicated": True,
                "dedicated_id": "defaultIotHubProvider",
            }
        ]
    )

    tenant_data = TenantTemplateData(
        resource_group=tf_data.resource_group,
        env_name=options.tenant_env,
        customer=options.customer,
        suffix=options.suffix,
        location=options.location,
        shloc=shloc,
        keyvault_name=keyvault_name,
        acr_name=acr_name,
        acr_password=acr_password,
        acr_registry=acr_registry,
        kubeconfig_path=relative_kubeconfig_path,
        keyvault_sp_id=sp.client_id,
        keyvault_sp_secret=sp.client_secret,
        tenant_namespace=f"tenant-{tenant_name}",
        github_app_id=gh_app_info.app_id,
        github_app_private_key_path=relative_gh_app_private_key_path,
        github_installation_id=gh_app_info.installation_id,
        az_tenant_id=tf_data.tenant_id,
        tenant_domain=tenant_domain,
        subscription_id=subscription_id,
        provider_iothubs=provider_iothubs_string,
    )
    generate_file_from_template(
        to_absolute_path(__file__, "templates/tenant-terraform.tfvars.json.mustache"),
        os.path.join(tf_folder, "terraform.tfvars.json"),
        asdict(tenant_data),
    )

    # Prepare git repo
    if not init_git_repo(folder, "tenant"):
        return

    write_version_file(folder, options.version, None, overwrite=False)

    # Generate app config values
    _create_app_config_values(keyvault_name, acr_registry, acr_name, acr_password)

    # TODO: Write next instructions as output


@dataclass
class ServicePrincipal:
    client_id: str
    client_secret: str


def _setup_charts_ssh_key(env_keyvault, tenant_keyvault, secret_folder_path):
    """Copy charts repo SSH key from env Key Vault to tenant Key Vault."""
    key_path = os.path.join(secret_folder_path, "charts_repo_ssh_key")
    get_keyvault_secret_to_file(env_keyvault, "charts-repo-ssh-key", key_path)
    upload_keyvault_secret_file(tenant_keyvault, "charts-repo-ssh-key", key_path)


def _setup_eso_reader_sp(name, keyvault_name, keyvault_id, subscription_id):
    existing_client_id = get_keyvault_secret(keyvault_name, "keyvault-sp-id")
    existing_client_secret = get_keyvault_secret(keyvault_name, "keyvault-sp-secret")

    if existing_client_id and existing_client_secret:
        # Make sure existing SP is key vault reader
        assign_keyvault_reader_role(keyvault_id, existing_client_id, subscription_id)
        return ServicePrincipal(existing_client_id, existing_client_secret)

    # Clean up potentially existing SPs
    existing_sps = get_service_principals_by_name(name)

    if existing_sps:
        for sp in existing_sps:
            delete_service_principal(sp["id"])

    sp = create_service_principal(name)
    assign_keyvault_reader_role(keyvault_id, sp["appId"], subscription_id)

    upload_keyvault_secret(keyvault_name, "keyvault-sp-id", sp["appId"])
    upload_keyvault_secret(keyvault_name, "keyvault-sp-secret", sp["password"])

    return ServicePrincipal(sp["appId"], sp["password"])


def _create_app_config_values(keyvault_name, acr_registry, acr_username, acr_password):
    # ACR credentials for pulling container images
    upload_keyvault_secret(keyvault_name, "acr-url", acr_registry)
    upload_keyvault_secret(keyvault_name, "acr-username", acr_username)
    upload_keyvault_secret(keyvault_name, "acr-password", acr_password)

    _create_user_service_config_values(keyvault_name)
    _create_arangodb_config_values(keyvault_name)


def _create_user_service_config_values(keyvault_name):
    # Default user
    upload_keyvault_secret(
        keyvault_name, "user-service-default-user-email", "beacontower@admin.io"
    )
    user_service_default_user_password = generate_password()
    upload_keyvault_secret(
        keyvault_name,
        "user-service-default-user-password",
        user_service_default_user_password,
    )

    # SpiceDB values
    upload_keyvault_secret(
        keyvault_name, "spicedb-postgres-username", "spicedb"
    )  # NOTE: Username must match the owner specified in the helmrelease in tenant-template
    spicedb_postgres_password = generate_password(uppercase=False, symbols=None)
    upload_keyvault_secret(
        keyvault_name, "spicedb-postgres-password", spicedb_postgres_password
    )

    spicedb_token = secrets.token_urlsafe(32)
    upload_keyvault_secret(keyvault_name, "spicedb-token", spicedb_token)

    # Timescale values
    upload_keyvault_secret(keyvault_name, "timescale-username", "timescale")
    timescale_password = generate_password(uppercase=False, symbols=None)
    upload_keyvault_secret(keyvault_name, "timescale-password", timescale_password)

    # TODO: Remove these temporary values when b2c/entry can be set up automatically
    upload_keyvault_secret(
        keyvault_name,
        "b2c-authority",
        "https://btglobalweufa2r.b2clogin.com/btglobalweufa2r.onmicrosoft.com/B2C_1_btsign_in/v2.0/",
    )
    upload_keyvault_secret(
        keyvault_name,
        "b2c-authority-web-client",
        "https://btglobalweufa2r.b2clogin.com/btglobalweufa2r.onmicrosoft.com/B2C_1_btsign_in",
    )
    upload_keyvault_secret(
        keyvault_name, "b2c-tenant-domain", "btglobalweufa2r.onmicrosoft.com"
    )
    upload_keyvault_secret(
        keyvault_name, "b2c-known-authority", "btglobalweufa2r.b2clogin.com"
    )
    upload_keyvault_secret(
        keyvault_name, "b2c-app-client-id", "7f535b5e-65e9-4d61-a6e5-e114687e909f"
    )
    upload_keyvault_secret(
        keyvault_name,
        "b2c-app-client-secret",
        "XrW8Q~AlsQBp5UxPG9_ncTxf.S-nQypP5~H4jaVX",
    )
    upload_keyvault_secret(
        keyvault_name,
        "b2c-metadata-url",
        "https://btglobalweufa2r.b2clogin.com/btglobalweufa2r.onmicrosoft.com/B2C_1_btsign_in/v2.0/.well-known/openid-configuration",
    )


def _create_arangodb_config_values(keyvault_name):
    arangodb_password = generate_password(uppercase=False, symbols=None)
    upload_keyvault_secret(keyvault_name, "arangodb-username", "beacontower")
    upload_keyvault_secret(keyvault_name, "arangodb-password", arangodb_password)


@dataclass
class TenantInfo:
    tenant_id: str
    subscription_id: str
    name: str
    env_name: str
    keyvault_name: str


def _add_tenant_to_storage(tenant_name, env_name, keyvault_name):
    print("[blue]Adding tenant to global env list...", end=" ")
    env_table_info = _get_env_list_info()
    sub_info = get_current_subscription()
    tenant_info = TenantInfo(
        tenant_id=sub_info["tenantId"],
        subscription_id=sub_info["id"],
        name=tenant_name,
        env_name=env_name,
        keyvault_name=keyvault_name,
    )
    upsert_table_storage_entry(
        env_table_info.name,
        TENANT_LIST_TABLE_NAME,
        tenant_name,
        tenant_name,
        tenant_info,
        env_table_info.subscription_id,
    )


def keyvault_name_to_tenant_name(keyvault_name):
    return keyvault_name[4:]


def register_tenant_in_env(tenant_name):
    print("[blue]Reading values...", end=" ")
    tenant_keyvault_name = get_keyvault_name(tenant_name)
    env_name = get_keyvault_secret(tenant_keyvault_name, "env-name")
    env_info = get_env_info(env_name)
    env_keyvault_name = env_info.keyvault_name
    tenant_name = get_keyvault_secret(tenant_keyvault_name, "tenant-name")
    env_name = get_keyvault_secret(env_keyvault_name, "env-name")
    az_tenant_id = env_info.tenant_id
    tenant_domain = get_keyvault_secret(tenant_keyvault_name, "tenant-domain")

    print("[green]Complete")

    # Register tenant repo SSH key in env key vault
    with tempfile.TemporaryDirectory() as temp_folder:
        tenant_ssh_key_path = os.path.join(temp_folder, "repo-ssh-key")
        get_keyvault_secret_to_file(
            tenant_keyvault_name, "repo-ssh-key", tenant_ssh_key_path
        )
        tenant_key_name = env_tenant_ssh_key_name(tenant_name)
        upload_keyvault_secret_file(
            env_keyvault_name, tenant_key_name, tenant_ssh_key_path
        )

    # Create tenant namespace and keyvault-sp-credentials secret
    print("[blue]Creating tenant namespace and credentials secret...", end=" ")
    tenant_namespace = f"tenant-{tenant_name}"

    kubeconfig_content = get_env_kubectl(env_name)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as kc_file:
        kc_file.write(kubeconfig_content)
        kubeconfig_path = kc_file.name

    try:
        # Create namespace (ignore if exists)
        result = subprocess.run(
            [
                "kubectl",
                "--kubeconfig",
                kubeconfig_path,
                "create",
                "namespace",
                tenant_namespace,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 and "already exists" not in result.stderr:
            print(f"[red]Failed to create namespace ({result.stderr})")
            return

        # Get SP credentials from tenant KV
        sp_client_id = get_keyvault_secret(tenant_keyvault_name, "keyvault-sp-id")
        sp_client_secret = get_keyvault_secret(
            tenant_keyvault_name, "keyvault-sp-secret"
        )

        # Create secret (delete first if exists to allow update)
        subprocess.run(
            [
                "kubectl",
                "--kubeconfig",
                kubeconfig_path,
                "delete",
                "secret",
                "keyvault-sp-credentials",
                "-n",
                tenant_namespace,
                "--ignore-not-found",
            ],
            capture_output=True,
            text=True,
        )

        result = subprocess.run(
            [
                "kubectl",
                "--kubeconfig",
                kubeconfig_path,
                "create",
                "secret",
                "generic",
                "keyvault-sp-credentials",
                f"--from-literal=client_id={sp_client_id}",
                f"--from-literal=client_secret={sp_client_secret}",
                "-n",
                tenant_namespace,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"[red]Failed to create secret ({result.stderr})")
            return
        print("[green]Complete")
    finally:
        os.unlink(kubeconfig_path)

    # Create tenant flux files in env repo
    with tempfile.TemporaryDirectory() as temp_folder:
        # Generate tenant file
        tenant_file_name = f"tenant-{tenant_name}.yaml"
        tenant_path = os.path.join(temp_folder, tenant_file_name)
        tenant_namespace = f"tenant-{tenant_name}"
        tenant_file_data = {
            "tenant_name": tenant_name,
            "tenant_namespace": tenant_namespace,
            "tenant_domain": tenant_domain,
            "az_tenant_id": az_tenant_id,
            "keyvault_name": tenant_keyvault_name,
        }

        generate_file_from_template(
            to_absolute_path(__file__, "templates/flux-tenant.yaml.mustache"),
            tenant_path,
            tenant_file_data,
        )

        # Clone env repo
        print("[blue]Cloning env repo...", end=" ")
        env_repo_name = f"env-{env_name}"
        env_repo_url = f"https://github.com/btenvs/{env_repo_name}.git"
        env_repo_folder = os.path.join(temp_folder, "repo")

        result = subprocess.run(
            ["git", "clone", env_repo_url, env_repo_folder],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("[green]Complete")
        else:
            print(f"[red]Failed ({result.stderr})")
            return

        # Update tenant kustomization.yaml to include new tenant file
        print(
            "[blue]Add tenant flux .yaml file into tenants kustomization list...",
            end=" ",
        )
        env_tenant_folder = os.path.join(env_repo_folder, "kubernetes", "tenants")
        tenant_kustomization_path = os.path.join(
            env_tenant_folder, "kustomization.yaml"
        )
        with open(tenant_kustomization_path, "r") as tenants_kustomization_file:
            tenants_file = yaml.safe_load(tenants_kustomization_file)

        if tenant_file_name not in tenants_file["resources"]:
            tenants_file["resources"].append(tenant_file_name)

            with open(tenant_kustomization_path, "w") as tenants_kustomization_file:
                yaml.safe_dump(
                    tenants_file,
                    tenants_kustomization_file,
                    sort_keys=False,
                    default_flow_style=False,
                )

            print("[green]Complete")
        else:
            print("[green]Skipped (tenant already listed)")

        # Move tenant file into env repo
        print("[blue]Move tenant flux .yaml file into local env repo...", end=" ")
        tenant_path_in_env_repo = os.path.join(env_tenant_folder, tenant_file_name)
        os.replace(tenant_path, tenant_path_in_env_repo)
        print("[green]Complete")

        # Sync changes (if any)
        print("[blue]Sync tenant file changes to repo (if any)...", end=" ")
        result = subprocess.run(
            ["git", "add", "."], cwd=env_repo_folder, capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"[red]Failed `git add` ({result.stderr})")
            return
        result = subprocess.run(
            ["git", "commit", "-m", f"Add tenant {tenant_name} to flux"],
            cwd=env_repo_folder,
            capture_output=True,
            text=True,
        )
        if "nothing to commit" in result.stdout.lower() and result.returncode != 0:
            nothing_to_commit = True
        elif result.returncode != 0:
            print(f"[red]Failed `git commit` ({result.stderr})")
            return
        else:
            nothing_to_commit = False

        if not nothing_to_commit:
            result = subprocess.run(
                ["git", "push", "origin", "master"],
                cwd=env_repo_folder,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"[red]Failed `git push` ({result.stderr})")
                return
        print("[green]Complete")

    # TOOD: Trigger reconciliation


def unregister_tenant_from_env(tenant_name):
    print("[blue]Reading values...", end=" ")
    tenant_keyvault_name = get_keyvault_name(tenant_name)
    env_name = get_keyvault_secret(tenant_keyvault_name, "env-name")
    env_keyvault_name = get_env_info(env_name).keyvault_name
    tenant_name = get_keyvault_secret(tenant_keyvault_name, "tenant-name")
    env_name = get_keyvault_secret(env_keyvault_name, "env-name")
    print("[green]Complete")

    # Delete tenant namespace and keyvault-sp-credentials secret
    print("[blue]Deleting tenant namespace and credentials secret...", end=" ")
    tenant_namespace = f"tenant-{tenant_name}"

    kubeconfig_content = get_env_kubectl(env_name)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as kc_file:
        kc_file.write(kubeconfig_content)
        kubeconfig_path = kc_file.name

    try:
        # Delete namespace (this also deletes all resources in it, including the secret)
        result = subprocess.run(
            [
                "kubectl",
                "--kubeconfig",
                kubeconfig_path,
                "delete",
                "namespace",
                tenant_namespace,
                "--ignore-not-found",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"[red]Failed to delete namespace ({result.stderr})")
            # Continue anyway to clean up flux files
        else:
            print("[green]Complete")
    finally:
        os.unlink(kubeconfig_path)

    # Remove tenant flux files from env repo
    with tempfile.TemporaryDirectory() as temp_folder:
        tenant_file_name = f"tenant-{tenant_name}.yaml"
        tenant_path = os.path.join(temp_folder, tenant_file_name)

        # Clone env repo
        print("[blue]Cloning env repo...", end=" ")
        env_repo_name = f"env-{env_name}"
        env_repo_url = f"https://github.com/btenvs/{env_repo_name}.git"
        env_repo_folder = os.path.join(temp_folder, "repo")

        result = subprocess.run(
            ["git", "clone", env_repo_url, env_repo_folder],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            print("[green]Complete")
        else:
            print(f"[red]Failed ({result.stderr})")
            return

        # Remove tenant flux file from kustomization.yaml resource list
        print(
            "[blue]Delete tenant flux .yaml file from tenants kustomization list...",
            end=" ",
        )
        env_tenant_folder = os.path.join(env_repo_folder, "kubernetes", "tenants")
        tenant_kustomization_path = os.path.join(
            env_tenant_folder, "kustomization.yaml"
        )
        with open(tenant_kustomization_path, "r") as tenants_kustomization_file:
            tenants_file = yaml.safe_load(tenants_kustomization_file)

        if tenant_file_name in tenants_file["resources"]:
            tenants_file["resources"].remove(tenant_file_name)

            with open(tenant_kustomization_path, "w") as tenants_kustomization_file:
                yaml.safe_dump(
                    tenants_file,
                    tenants_kustomization_file,
                    sort_keys=False,
                    default_flow_style=False,
                )

            print("[green]Complete")
        else:
            print("[green]Skipped (tenant not found)")

        # Remove the tenant flux file
        print("[blue]Delete tenant flux .yaml file from local env repo...", end=" ")
        tenant_path_in_env_repo = os.path.join(env_tenant_folder, tenant_file_name)
        if os.path.exists(tenant_path_in_env_repo):
            os.remove(tenant_path_in_env_repo)
            print("[green]Complete")
        else:
            print("[green]Skipped (file not found)")

        # Sync changes (if any)
        print("[blue]Sync tenant file changes to repo (if any)...", end=" ")
        result = subprocess.run(
            ["git", "add", "."], cwd=env_repo_folder, capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"[red]Failed `git add` ({result.stderr})")
            return
        result = subprocess.run(
            ["git", "commit", "-m", f"Remove tenant {tenant_name} from flux"],
            cwd=env_repo_folder,
            capture_output=True,
            text=True,
        )
        if "nothing to commit" in result.stdout.lower() and result.returncode != 0:
            nothing_to_commit = True
        elif result.returncode != 0:
            print(f"[red]Failed `git commit` ({result.stderr})")
            return
        else:
            nothing_to_commit = False

        if not nothing_to_commit:
            result = subprocess.run(
                ["git", "push", "origin", "master"],
                cwd=env_repo_folder,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"[red]Failed `git push` ({result.stderr})")
                return
        print("[green]Complete")

    # Unregister tenant repo SSH key from env key vault
    tenant_key_name = env_tenant_ssh_key_name(tenant_name)
    delete_keyvault_secret(env_keyvault_name, tenant_key_name)

    return


def get_tenant_k8s_ns(tenant_name):
    return f"tenant-{tenant_name}"


def env_tenant_ssh_key_name(tenant_name):
    return f"tenant-repo-ssh-key-{tenant_name}"


def env_tenant_ssh_pub_key_name(tenant_name):
    return f"tenant-repo-ssh-pub-key-{tenant_name}"


def get_tenant_debug_telemetry_config(tenant_name, services=None):
    keyvault_name = get_keyvault_name(tenant_name)

    with tempfile.TemporaryDirectory() as temp_folder:
        kubeconfig_path = os.path.join(temp_folder, "kubeconfig")
        get_keyvault_secret_to_file(keyvault_name, "kubeconfig", kubeconfig_path)
        tenant_ns = get_tenant_k8s_ns(tenant_name)
        responses = parallel_pod_curl(
            kubeconfig_path, tenant_ns, "/debug/telemetry", services, port=8080
        )

        return responses


def set_tenant_debug_telemetry_loglevel(tenant_name, log_level, services=None):
    log_level_map = {
        "dbg": "debug",
        "info": "information",
        "warn": "warning",
        "err": "error",
    }
    dotnet_level = log_level_map.get(log_level.lower(), log_level.lower())
    keyvault_name = get_keyvault_name(tenant_name)

    with tempfile.TemporaryDirectory() as temp_folder:
        kubeconfig_path = os.path.join(temp_folder, "kubeconfig")
        get_keyvault_secret_to_file(keyvault_name, "kubeconfig", kubeconfig_path)
        tenant_ns = get_tenant_k8s_ns(tenant_name)
        responses = parallel_pod_curl(
            kubeconfig_path,
            tenant_ns,
            f"/debug/telemetry/loglevel?level={dotnet_level}",
            services,
            method="POST",
            port=8080,
        )

        return responses


def set_tenant_debug_telemetry_tracing(tenant_name, tracing_enabled, services=None):
    keyvault_name = get_keyvault_name(tenant_name)

    with tempfile.TemporaryDirectory() as temp_folder:
        kubeconfig_path = os.path.join(temp_folder, "kubeconfig")
        get_keyvault_secret_to_file(keyvault_name, "kubeconfig", kubeconfig_path)
        tenant_ns = get_tenant_k8s_ns(tenant_name)
        responses = parallel_pod_curl(
            kubeconfig_path,
            tenant_ns,
            f"/debug/telemetry/tracing?enabled={str(tracing_enabled).lower()}",
            services,
            method="POST",
            port=8080,
        )

        return responses


def listen_to_tenant_eventhub(
    tenant, eh_name, consumer_group="monitor", show_full_event=True
):
    keyvault_name = get_keyvault_name(tenant)
    secret_name_cs_r = f"{eh_name}-eh-connection-string-r"
    secret_name_cs_rw = f"{eh_name}-eh-connection-string-rw"
    eh_connection_string = get_keyvault_secret(
        keyvault_name, secret_name_cs_r
    ) or get_keyvault_secret(keyvault_name, secret_name_cs_rw)

    if not eh_connection_string:
        print(
            f"[red]Tenant event hub connection string not found for event hub {eh_name}"
        )
        return

    def on_event(partition_context, event):
        prefix = f"[blue][{partition_context.partition_id}][/blue]"
        if show_full_event:
            print(f"{prefix} {event}")
        else:
            print(f"{prefix} {event.body_as_str()}")

    client = EventHubConsumerClient.from_connection_string(
        eh_connection_string, consumer_group
    )
    print(f"[blue]Listening to {client.eventhub_name}...")
    try:
        with client:
            client.receive(on_event=on_event, starting_position="@latest")
    except KeyboardInterrupt:
        print("[blue]Stopped listening")  # Doesn't work


@dataclass
class TenantLoginInfo:
    email: str
    password: str
    url: str


def get_tenant_login_info(tenant) -> TenantLoginInfo:
    keyvault_name = get_keyvault_name(tenant)
    email = get_keyvault_secret(keyvault_name, "user-service-default-user-email")
    password = get_keyvault_secret(keyvault_name, "user-service-default-user-password")
    tenant_domain = get_keyvault_secret(keyvault_name, "tenant-domain")
    url = f"https://{tenant_domain}"

    return TenantLoginInfo(email, password, url)
