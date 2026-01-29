import os
from dataclasses import asdict, dataclass

from rich import print

from btpy.core.azure_utility import (
    create_container,
    create_keyvault,
    create_resource_group,
    create_storage_account,
    get_azure_tenant_id,
    get_current_subscription,
    get_storage_connection_string,
    location_tag,
)
from btpy.core.file_utility import generate_file_from_template, to_absolute_path
from btpy.iac.suffix import generate


@dataclass
class TerraformBootstrapData:
    resource_group: str
    storage_account_name: str
    container_name: str
    tf_blob_name: str
    keyvault_name: str
    keyvault_id: str
    customer: str
    environment: str
    env_prefix: str | None
    location: str
    shloc: str
    suffix: str
    tenant_id: str
    subscription_id: str


# TODO: Move out from this file? Rename file?
def bootstrap_tf_repo(customer, env, location, suffix=None, prefix=None, folder=None):
    if suffix is None:
        suffix = generate()["suffix"]

    shloc = location_tag(location)
    repo_name = f"{customer}-{env}-{shloc}{suffix}"
    repo_name_no_hyphens = get_no_hyphen_name(repo_name)
    customer_env_name = f"{customer}-{env}"
    customer_env_name_no_hyphens = f"{customer}{env}"
    keyvault_name = get_keyvault_name(repo_name)

    if len(keyvault_name) > 24:
        print(f"[red]Key vault name {keyvault_name} is too long (24 is max)")
        raise f"Key vault name {keyvault_name} is too long (24 is max)"

    if prefix is not None:
        customer_env_name = f"{prefix}-{customer_env_name}"

    resource_group_name = f"rg-bt-{repo_name}"
    storage_account_name = f"stgtf{repo_name_no_hyphens}"
    storage_account_container = "tfstate"
    storage_account_blob_name = "terraform.tfstate"
    tenant_id = get_azure_tenant_id()

    try:
        create_resource_group(resource_group_name, location)
        create_storage_account(resource_group_name, storage_account_name, location)
        storage_connection_string = get_storage_connection_string(storage_account_name)
        create_container(storage_connection_string, storage_account_container)
        keyvault_info = create_keyvault(resource_group_name, keyvault_name, location)
    except Exception as e:
        print(f"[red]Terraform bootstrapping failed ({e})")
        return None

    subscription_id = get_current_subscription()["id"]
    data = TerraformBootstrapData(
        resource_group=resource_group_name,
        storage_account_name=storage_account_name,
        container_name=storage_account_container,
        tf_blob_name=storage_account_blob_name,
        keyvault_name=keyvault_name,
        keyvault_id=keyvault_info["id"],
        customer=customer,
        environment=env,
        env_prefix=prefix,
        location=location,
        shloc=shloc,
        suffix=suffix,
        tenant_id=tenant_id,
        subscription_id=subscription_id,
    )

    backend_path = os.path.join(folder if folder is not None else "", "backend.tf")
    generate_file_from_template(
        to_absolute_path(__file__, "../iac/templates/backend.mustache"),
        backend_path,
        asdict(data),
    )

    return data


def get_keyvault_name(name):
    return f"kvbt{get_no_hyphen_name(name)}"


def get_no_hyphen_name(name):
    return name.replace("-", "")
