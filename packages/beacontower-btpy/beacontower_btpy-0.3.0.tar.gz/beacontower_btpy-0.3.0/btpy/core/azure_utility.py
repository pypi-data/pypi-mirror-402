import shlex
import time
from dataclasses import dataclass
from typing import Optional

from azure.identity import AzureCliCredential, DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.storage.blob import BlobServiceClient, ContainerClient
from msgraph import GraphServiceClient
from msgraph.generated.models.application import Application
from msgraph.generated.models.password_credential import PasswordCredential
from msgraph.generated.models.web_application import WebApplication
from rich import print

from btpy.az import az
from btpy.configuration.config import get_env_data_storage_name


@dataclass
class AzureADInfo:
    """Azure AD B2C tenant information"""

    tenant_id: str
    domain_name: str
    resource_id: str
    location: str
    billing_type: Optional[str]
    sku: Optional[str]
    properties: dict


@dataclass
class AzureADAppInfo:
    """Azure AD app registration information"""

    id: str  # Object ID
    app_id: str  # Application (client) ID
    display_name: str
    sign_in_audience: Optional[str]
    redirect_uris: list[str]


@dataclass
class AzureADAppSecretInfo:
    """Azure AD app registration secret information"""

    key_id: str
    display_name: str
    start_date_time: Optional[str]
    end_date_time: Optional[str]
    hint: Optional[str]  # Last few characters of the secret
    secret_text: Optional[str] = None  # Only available at creation time


_blob_service_client = None


def get_azure_credential():
    return AzureCliCredential()
    # return DefaultAzureCredential()


def to_azure_appsetting_format(setting_value: str) -> str:
    return setting_value.replace(":", "__")


def from_azure_appsetting_format(setting_value: str) -> str:
    return setting_value.replace("__", ":")


def get_blob_service_client() -> BlobServiceClient:
    global _blob_service_client

    if _blob_service_client is None:
        credential = get_azure_credential()
        blob_account_url = (
            f"https://{get_env_data_storage_name()}.blob.core.windows.net"
        )
        _blob_service_client = BlobServiceClient(
            blob_account_url, credential=credential
        )

    return _blob_service_client


def get_blob_container_client(container_name: str) -> ContainerClient:
    blob_service_client = get_blob_service_client()
    return blob_service_client.get_container_client(container_name)


def get_blob_client(container_name: str, blob_name: str):
    container_client = get_blob_container_client(container_name)
    return container_client.get_blob_client(blob_name)


def to_blob_index_format(tag: str) -> str:
    return tag.replace("-", "_")


def storage_account_exists(storage_account_name):
    exit_code, result, err = az(f"storage account check-name -n {storage_account_name}")

    if exit_code != 0:
        print(
            f"[red]Failed to check if Azure storage account exists ({exit_code} - {err})"
        )
        raise Exception("Failed to check if Azure storage account exists")

    return not result["nameAvailable"]


def resource_group_exists(resource_group_name):
    exit_code, result, err = az(f"group exists -n {resource_group_name}")

    if exit_code != 0:
        print(
            f"[red]Failed to check if Azure resource group exists ({exit_code} - {err})"
        )
        raise Exception("Failed to check if Azure resource group exists")

    return result


def create_storage_account(resource_group_name, storage_account_name, location):
    if storage_account_exists(storage_account_name):
        print(f"[blue]Storage account {storage_account_name} already exists")
        return

    print(f"[blue]Creating Azure storage account {storage_account_name}...", end=" ")
    exit_code, result, err = az(
        f"storage account create -g {resource_group_name} -n {storage_account_name} --sku Standard_LRS -l {location}"
    )

    if exit_code != 0:
        print(f"[red]Failed ({exit_code} - {err})")
        raise Exception("Failed to create Azure storage account")

    print("[green]Complete")


def list_storage_table_entries(storage_account_name, table_name, subscription_id=None):
    exit_code, result, err = az(
        f"storage entity query --account-name {storage_account_name} --table-name {table_name}",
        subscription_id,
    )

    if exit_code != 0:
        raise Exception(
            f"Failed to list Azure table storage table entries ({exit_code} - {err})"
        )

    return result


def get_storage_table_entry(
    storage_account_name, table_name, subscription_id, partition_key, row_key
):
    exit_code, result, err = az(
        f"storage entity show --account-name {storage_account_name} --table-name {table_name} --partition-key {partition_key} --row-key {row_key}",
        subscription_id,
    )

    if exit_code != 0:
        if "The specified resource does not exist." in err:
            return None
        raise Exception(
            f"Failed to get Azure table storage table entry ({exit_code} - {err})"
        )

    return result


def upsert_table_storage_entry(
    storage_account_name,
    table_name,
    partition_key,
    row_key,
    data,
    subscription_id=None,
    log=True,
):
    if log:
        print(
            f"[blue]Upserting Azure table storage entity {partition_key}-{row_key}...",
            end=" ",
        )
    exit_code, result, err = az(
        f"storage entity insert --table-name {table_name} --account-name {storage_account_name} --entity PartitionKey='{partition_key}' RowKey='{row_key}' Data='{data}' --if-exists replace",
        subscription_id,
    )

    if exit_code != 0:
        if log:
            print(f"[red]Failed ({exit_code} - {err})")
        raise Exception(
            f"Failed to upsert Azure table storage table entry ({exit_code} - {err})"
        )

    if log:
        print("[green]Complete")


def create_resource_group(resource_group_name, location):
    if resource_group_exists(resource_group_name):
        print(f"[blue]Resource group {resource_group_name} already exists")
        return

    print(f"[blue]Creating Azure resource group {resource_group_name}...", end=" ")
    exit_code, result, err = az(f"group create -n {resource_group_name} -l {location}")

    if exit_code != 0:
        print(f"[red]Failed ({exit_code} - {err})")
        raise Exception("Failed to create Azure resource group")

    print("[green]Complete")


def container_exists(storage_connection_string, container):
    exit_code, result, err = az(
        f'storage container exists --connection-string "{storage_connection_string}" --name {container} --query exists'
    )

    if exit_code != 0:
        print(
            f"[red]Failed to check if blob container {container} exists ({exit_code} - {err})"
        )
        raise Exception("Failed to check if Azure blob container exists")

    return result


def create_container(storage_connection_string, container):
    if container_exists(storage_connection_string, container):
        print(f"[blue]Blob container {container} already exists")
        return None

    print(f"[blue]Creating Azure blob container {container}...", end=" ")
    exit_code, result, err = az(
        f"storage container create --connection-string {storage_connection_string} --name {container}"
    )

    if exit_code != 0:
        print(f"[red]Failed ({exit_code} - {err})")
        raise Exception("Failed to create Azure blob container")

    print("[green]Complete")

    return result


def get_storage_connection_string(storage_name):
    exit_code, result, err = az(
        f"storage account show-connection-string --name {storage_name} --query connectionString"
    )

    if exit_code != 0:
        print(
            f"[red]Failed to get Azure storage account connection string ({exit_code} - {err})"
        )
        raise Exception("Failed to get Azure storage account connection string")

    return result


def blob_exists(storage_connection_string, container, blob_name):
    exit_code, result, err = az(
        f'storage blob exists --connection-string "{storage_connection_string}" --container-name {container} --name {blob_name} --query exists'
    )

    if exit_code != 0:
        print(f"[red]Failed to check if Azure blob exists ({exit_code} - {err})")
        raise Exception("Failed to check if Azure blob exists")

    return result


def get_current_azure_user_id():
    exit_code, result, err = az("ad signed-in-user show --query id -o tsv")

    if exit_code != 0:
        raise Exception(f"Failed to get current user ID ({exit_code} - {err})")

    return result


def assign_keyvault_reader_role(kv_id, user_id, subscription_id):
    name = kv_id.split("/")[-1]
    print(
        f"[blue]Assigning secret user role to {user_id} for Azure key vault {name}...",
        end=" ",
    )
    exit_code, result, err = az(
        f'role assignment create --role "Key Vault Secrets User" --assignee {user_id} --scope {kv_id}',
        subscription_id,
    )

    if exit_code != 0:
        print(f"[red]Failed ({exit_code} - {err})")
        raise Exception(
            f"Failed to assign key vault secret user role to {user_id} for Azure key vault {name}"
        )

    print("[green]Complete")
    return result


def set_keyvault_admin_rbac(kv_id, user_id):
    name = kv_id.split("/")[-1]
    print(
        f"[blue]Assigning admin role to {user_id} for Azure key vault {name}...",
        end=" ",
    )
    exit_code, result, err = az(
        f'role assignment create --role "Key Vault Administrator" --assignee {user_id} --scope {kv_id}'
    )

    if exit_code != 0:
        print(f"[red]Failed ({exit_code} - {err})")
        raise Exception(
            f"Failed to assign admin role to {user_id} for Azure key vault {name}"
        )

    print("[green]Complete")
    return result


def assign_subscription_role(subscription_id, assignee_id, role):
    print(
        f"[blue]Assigning {role} role to {assignee_id} for subscription {subscription_id}...",
        end=" ",
    )
    scope = f"/subscriptions/{subscription_id}"
    exit_code, result, err = az(
        f'role assignment create --role "{role}" --assignee {assignee_id} --scope {scope}'
    )

    if exit_code != 0:
        print(f"[red]Failed ({exit_code} - {err})")
        raise Exception(
            f"Failed to assign {role} role to {assignee_id} for subscription {subscription_id} ({exit_code} - {err})"
        )

    print("[green]Complete")
    return result


def is_keyvault_admin(kv_id, user_id):
    exit_code, result, err = az(f'role assignment list --scope "{kv_id}"')

    if exit_code != 0:
        raise Exception(
            f"Failed to get Azure key vault admin list ({exit_code} - {err})"
        )

    for admin in result:
        if (
            admin["principalId"] == user_id
            and admin["roleDefinitionName"] == "Key Vault Administrator"
        ):
            return True

    return False


def await_keyvault_admin_assignment(kv_id, user_id, timeout_s=60):
    poll_timer_s = 2
    start_time = time.time()

    while time.time() - start_time < timeout_s:
        time.sleep(poll_timer_s)
        if is_keyvault_admin(kv_id, user_id):
            return True

    return False


def keyvault_id(resource_group, name):
    exit_code, result, err = az(
        f"keyvault show --name {name} --resource-group {resource_group} --query id -o tsv"
    )
    return result


def keyvault_exists(resource_group, name):
    exit_code, result, err = az(
        f"keyvault show --name {name} --resource-group {resource_group} --query id -o tsv"
    )
    return exit_code == 0


def get_keyvault(resource_group, name):
    exit_code, result, err = az(
        f"keyvault show --name {name} --resource-group {resource_group}"
    )

    if exit_code != 0:
        raise Exception("Failed to get Azure key vault")

    return result


def create_keyvault(resource_group, name, location):
    if keyvault_exists(resource_group, name):
        print(f"[blue]Azure key vault {name} already exists")
        return get_keyvault(resource_group, name)

    print(f"[blue]Creating Azure key vault {name}...", end=" ")
    exit_code, result, err = az(
        f'keyvault create --name "{name}" --resource-group "{resource_group}" --location "{location}" --sku standard'
    )

    if exit_code != 0:
        print(f"[red]Failed ({exit_code} - {err})")
        raise Exception("Failed to create Azure key vault")

    print("[green]Complete")

    id = result["id"]
    user_id = get_current_azure_user_id()
    set_keyvault_admin_rbac(id, user_id)

    return result


def get_keyvault_id(kv_name):
    exit_code, result, err = az(f"keyvault show --name {kv_name} --query id -o tsv")

    if exit_code != 0:
        print(f"[red]Failed to get Azure key vault id ({exit_code} - {err})")
        raise Exception("Failed to get Azure key vault id")

    return result


def get_keyvault_secret(kv_name, secret_name):
    exit_code, result, err = az(
        f"keyvault secret show --vault-name {kv_name} --name {secret_name} --query value -o tsv"
    )

    if exit_code != 0:
        if "was not found in this key vault" in err:
            return None
        print(f"[red]Failed to get Azure key vault secret value ({exit_code} - {err})")
        raise Exception(
            f"Failed to get Azure key vault secret value ({exit_code} - {err})"
        )

    return result


def get_keyvault_secret_to_file(kv_name, secret_name, path):
    secret_value = get_keyvault_secret(kv_name, secret_name)

    with open(path, "w") as f:
        f.write(secret_value)


def query_keyvault_secrets(kv_name, jmespath_query, subscription_id=None):
    exit_code, result, err = az(
        f'keyvault secret list --vault-name {kv_name} --query "{jmespath_query}"',
        subscription_id,
    )

    if exit_code != 0:
        raise Exception(
            f"Failed to query Azure key vault secrets ({exit_code} - {err})"
        )

    return result


def upload_keyvault_secret_file(kv_name, secret_name, file_path):
    print(f"[blue]Uploading Azure key vault secret {secret_name} from file...", end=" ")
    exit_code, result, err = az(
        f"keyvault secret set --vault-name {kv_name} --name {secret_name} --file {file_path}"
    )

    if exit_code != 0:
        print(f"[red]Failed ({exit_code} - {err})")
        raise Exception(
            f"Failed to upload Azure key vault secret from file ({exit_code} - {err})"
        )

    print("[green]Complete")
    return result


def upload_keyvault_secret(kv_name, secret_name, secret_value):
    print(f"[blue]Uploading Azure key vault secret {secret_name}...", end=" ")
    exit_code, result, err = az(
        f"keyvault secret set --vault-name {kv_name} --name {secret_name} --value {shlex.quote(secret_value)}"
    )

    if exit_code != 0:
        print(f"[red]Failed ({exit_code} - {err})")
        raise Exception(
            f"Failed to upload Azure key vault secret ({exit_code} - {err})"
        )

    print("[green]Complete")
    return result


def delete_keyvault_secret(kv_name, secret_name):
    print(f"[blue]Deleting Azure key vault secret {secret_name}...", end=" ")
    exit_code, result, err = az(
        f"keyvault secret delete --vault-name {kv_name} --name {secret_name}"
    )

    if exit_code != 0:
        print(f"[red]Failed ({exit_code} - {err})")
        raise Exception(
            f"Failed to delete Azure key vault secret ({exit_code} - {err})"
        )

    exit_code, result, err = az(
        f"keyvault secret purge --vault-name {kv_name} --name {secret_name}"
    )

    if exit_code != 0:
        print(f"[red]Failed ({exit_code} - {err})")
        raise Exception(f"Failed to purge Azure key vault secret ({exit_code} - {err})")

    print("[green]Complete")


def get_azure_service_principal(env_name):
    sp_name = f"sp-bt-env-{env_name}"
    exit_code, result, err = az(f'ad sp list --display-name "{sp_name}"')

    if exit_code != 0:
        print(
            f"[red]Failed to get Azure service principal exists ({exit_code} - {err})"
        )
        raise Exception(
            f"Failed to get Azure service principal exists ({exit_code} - {err})"
        )

    return result[0] if len(result) > 0 else None


def azure_service_principal_exists(env_name):
    sp_name = f"sp-bt-env-{env_name}"
    exit_code, result, err = az(f'ad sp list --display-name "{sp_name}"')

    if exit_code != 0:
        print(
            f"[red]Failed to check if Azure service principal exists ({exit_code} - {err})"
        )
        raise Exception(
            f"Failed to check if Azure service principal exists ({exit_code} - {err})"
        )

    return len(result) > 0


def validate_current_tenant(expected_tenant_id):
    """Validate that the current Azure CLI context matches the expected tenant.

    Raises an exception if there's a mismatch.
    """
    exit_code, result, err = az("account show")
    if exit_code != 0:
        raise Exception(f"Failed to get current Azure account ({exit_code} - {err})")

    current_tenant = result.get("tenantId")
    if current_tenant != expected_tenant_id:
        raise Exception(
            f"Azure CLI tenant mismatch!\n"
            f"  Expected tenant: {expected_tenant_id}\n"
            f"  Current tenant:  {current_tenant}\n"
            f"  Please switch tenant with: az login --tenant {expected_tenant_id}"
        )


def validate_current_subscription(expected_subscription_id):
    """Validate that the current Azure CLI context matches the expected subscription.

    Raises an exception if there's a mismatch.
    """
    exit_code, result, err = az("account show")
    if exit_code != 0:
        raise Exception(f"Failed to get current Azure account ({exit_code} - {err})")

    current_subscription = result.get("id")
    if current_subscription != expected_subscription_id:
        raise Exception(
            f"Azure CLI subscription mismatch!\n"
            f"  Expected subscription: {expected_subscription_id}\n"
            f"  Current subscription:  {current_subscription}\n"
            f"  Please switch subscription with: az account set --subscription {expected_subscription_id}"
        )


def create_service_principal(name, tenant_id=None):
    print("[blue]Creating Azure service principal...", end=" ")

    if tenant_id:
        validate_current_tenant(tenant_id)

    exit_code, result, err = az(f'ad sp create-for-rbac --name "{name}"')

    if exit_code != 0:
        print(f"[red]Failed ({exit_code} - {err})")
        raise Exception(
            f"Failed to create Azure service principal ({exit_code} - {err})"
        )

    print("[green]Complete")
    return result


def get_service_principals_by_name(name):
    exit_code, result, err = az(f"""ad sp list --filter "displayname eq '{name}'" """)

    if exit_code != 0:
        raise Exception(
            f"Failed to list Azure service principals ({exit_code} - {err})"
        )

    return result


def delete_service_principal(id):
    exit_code, result, err = az(f"ad sp delete --id {id}")

    if exit_code != 0:
        raise Exception(
            f"Failed to delete Azure service principal ({exit_code} - {err})"
        )


def get_current_subscription():
    exit_code, result, err = az("account show")

    if exit_code != 0:
        raise Exception(f"Failed to get Azure tenant ID ({exit_code} - {err})")

    return result


def get_azure_tenant_id():
    exit_code, result, err = az("account show --query tenantId -o tsv")

    if exit_code != 0:
        raise Exception(f"Failed to get Azure tenant ID ({exit_code} - {err})")

    return result


def create_azure_ad(
    id, name, resource_group, location, country_code, subscription_id
) -> AzureADInfo:
    """
    Create an Azure Active Directory B2C tenant within the specified resource group in the provided
    Azure subscription. This function initializes a `ResourceManagementClient` using Azure's default
    credentials to manage the Azure resources.

    Parameters
    ----------
    id : str
        The unique identifier for the Azure Active Directory B2C tenant. E.g. btglobalneu1234.
    name : str
        The display name for the Azure Active Directory B2C tenant. E.g. Glaze.
    resource_group : str
        The name of the Azure resource group within which the directory will be created.
    location : str
        The geographic location for the Azure Active Directory B2C tenant. NOTE: These are not the standard Azure location names! Valid values are: "United States", "Europe", "Asia Pacific" and "Australia".
    country_code: str
        The country code within the location specified. Regular country codes. Used for billing etc. E.g. "SE".
    subscription_id : str
        The Azure subscription ID under which the resource group and the tenant reside.

    Returns
    -------
    AzureADInfo
        Information about the created Azure AD B2C tenant.
    """
    credential = DefaultAzureCredential()
    client = ResourceManagementClient(credential, subscription_id)
    tenant_domain = f"{id}.onmicrosoft.com"

    result = client.resources.begin_create_or_update(
        resource_group_name=resource_group,
        resource_provider_namespace="Microsoft.AzureActiveDirectory",
        parent_resource_path="",
        resource_type="b2cDirectories",
        resource_name=tenant_domain,
        api_version="2021-04-01",
        parameters={
            "location": location,
            "sku": {"name": "Standard", "tier": "A0"},
            "properties": {
                "createTenantProperties": {
                    "displayName": name,
                    "countryCode": country_code,
                }
            },
        },
    ).result()

    # Construct AzureADInfo from creation result
    return AzureADInfo(
        tenant_id=result.properties.get("tenantId"),
        domain_name=result.name,
        resource_id=result.id,
        location=result.location,
        billing_type=result.properties.get("billingConfig", {}).get("billingType"),
        sku=result.sku.name if result.sku else None,
        properties=result.properties,
    )


def get_azure_ad(
    tenant_domain, resource_group, subscription_id
) -> Optional[AzureADInfo]:
    credential = DefaultAzureCredential()
    client = ResourceManagementClient(credential, subscription_id)

    try:
        resource = client.resources.get(
            resource_group_name=resource_group,
            resource_provider_namespace="Microsoft.AzureActiveDirectory",
            parent_resource_path="",
            resource_type="b2cDirectories",
            resource_name=tenant_domain,
            api_version="2021-04-01",
        )

        # Extract useful info
        return AzureADInfo(
            tenant_id=resource.properties.get("tenantId"),
            domain_name=resource.name,
            resource_id=resource.id,
            location=resource.location,
            billing_type=resource.properties.get("billingConfig", {}).get(
                "billingType"
            ),
            sku=resource.sku.name if resource.sku else None,
            properties=resource.properties,
        )
    except Exception as e:
        print(f"WTF BRO ({e})")
        return None


def _app_to_info(app) -> AzureADAppInfo:
    """Convert Graph SDK Application object to AzureADAppInfo."""
    redirect_uris = []
    if app.web and app.web.redirect_uris:
        redirect_uris = app.web.redirect_uris
    return AzureADAppInfo(
        id=app.id,
        app_id=app.app_id,
        display_name=app.display_name,
        sign_in_audience=app.sign_in_audience,
        redirect_uris=redirect_uris,
    )


def _secret_to_info(cred, secret_text=None) -> AzureADAppSecretInfo:
    """Convert Graph SDK PasswordCredential to AzureADAppSecretInfo."""
    return AzureADAppSecretInfo(
        key_id=str(cred.key_id) if cred.key_id else "",
        display_name=cred.display_name or "",
        start_date_time=cred.start_date_time.isoformat()
        if cred.start_date_time
        else None,
        end_date_time=cred.end_date_time.isoformat() if cred.end_date_time else None,
        hint=cred.hint,
        secret_text=secret_text or cred.secret_text,
    )


async def create_azure_ad_app(name, redirect_uris, tenant_id) -> AzureADAppInfo:
    from msgraph.generated.models.implicit_grant_settings import ImplicitGrantSettings

    credential = DefaultAzureCredential(additionally_allowed_tenants=[tenant_id])
    client = GraphServiceClient(
        credentials=credential, scopes=["https://graph.microsoft.com/.default"]
    )
    app_desc = Application(
        display_name=name,
        sign_in_audience="AzureADandPersonalMicrosoftAccount",
        web=WebApplication(
            redirect_uris=redirect_uris,
            implicit_grant_settings=ImplicitGrantSettings(
                enable_id_token_issuance=True,
                enable_access_token_issuance=True,
            ),
        ),
    )
    app = await client.applications.post(app_desc)
    return _app_to_info(app)


async def azure_ad_app_exists(name, tenant_id) -> bool:
    return await get_azure_ad_app_by_name(name, tenant_id) is not None


async def get_azure_ad_app_by_name(name, tenant_id) -> Optional[AzureADAppInfo]:
    from msgraph.generated.applications.applications_request_builder import (
        ApplicationsRequestBuilder,
    )

    credential = DefaultAzureCredential(additionally_allowed_tenants=[tenant_id])
    client = GraphServiceClient(
        credentials=credential, scopes=["https://graph.microsoft.com/.default"]
    )

    query_params = (
        ApplicationsRequestBuilder.ApplicationsRequestBuilderGetQueryParameters(
            filter=f"displayName eq '{name}'"
        )
    )
    config = (
        ApplicationsRequestBuilder.ApplicationsRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )
    )
    apps = await client.applications.get(request_configuration=config)

    if apps and apps.value and len(apps.value) > 0:
        return _app_to_info(apps.value[0])
    return None


async def get_azure_ad_apps(tenant_id) -> list[AzureADAppInfo]:
    credential = DefaultAzureCredential(additionally_allowed_tenants=[tenant_id])
    client = GraphServiceClient(
        credentials=credential, scopes=["https://graph.microsoft.com/.default"]
    )
    result = await client.applications.get()
    if result and result.value:
        return [_app_to_info(app) for app in result.value]
    return []


async def get_azure_ad_app(app_id, tenant_id) -> Optional[AzureADAppInfo]:
    credential = DefaultAzureCredential(additionally_allowed_tenants=[tenant_id])
    client = GraphServiceClient(
        credentials=credential, scopes=["https://graph.microsoft.com/.default"]
    )
    app = await client.applications.by_application_id(app_id).get()
    if app:
        return _app_to_info(app)
    return None


async def create_azure_ad_app_secret(
    app_id, secret_name, tenant_id
) -> AzureADAppSecretInfo:
    credential = DefaultAzureCredential(additionally_allowed_tenants=[tenant_id])
    client = GraphServiceClient(
        credentials=credential, scopes=["https://graph.microsoft.com/.default"]
    )
    secret_desc = PasswordCredential(display_name=secret_name)
    cred = await client.applications.by_application_id(app_id).add_password.post(
        secret_desc
    )
    return _secret_to_info(cred)


async def get_azure_ad_app_secret_by_name(
    app_id, secret_name, tenant_id
) -> Optional[AzureADAppSecretInfo]:
    """Get app secret metadata by display name.

    Note: The actual secret value is only available at creation time.
    This returns metadata (key_id, display_name, end_date_time, etc.)
    """
    credential = DefaultAzureCredential(additionally_allowed_tenants=[tenant_id])
    client = GraphServiceClient(
        credentials=credential, scopes=["https://graph.microsoft.com/.default"]
    )
    app = await client.applications.by_application_id(app_id).get()
    if app and app.password_credentials:
        for cred in app.password_credentials:
            if cred.display_name == secret_name:
                return _secret_to_info(cred)
    return None


def listen_to_eventhub(connection_string):
    return


def location_tag(location):
    match location.lower():
        case "australiacentral":
            return "auc"
        case "australiacentral2":
            return "auc2"
        case "australiaeast":
            return "aue"
        case "australiasoutheast":
            return "ause"
        case "austriaeast":
            return "ate"
        case "belgiumcentral":
            return "bec"
        case "brazilsouth":
            return "brs"
        case "brazilsoutheast":
            return "brse"
        case "canadacentral":
            return "cac"
        case "canadaeast":
            return "cae"
        case "centralindia":
            return "cin"
        case "centralus":
            return "cus"
        case "chilecentral":
            return "clc"
        case "eastasia":
            return "eas"
        case "eastus":
            return "eus"
        case "eastus2":
            return "eus2"
        case "francecentral":
            return "frc"
        case "francesouth":
            return "frs"
        case "germanynorth":
            return "gen"
        case "germanywestcentral":
            return "gewc"
        case "indonesiacentral":
            return "idc"
        case "israelcentral":
            return "ilc"
        case "italynorth":
            return "itn"
        case "japaneast":
            return "jpe"
        case "japanwest":
            return "jpw"
        case "koreacentral":
            return "krc"
        case "koreasouth":
            return "krs"
        case "malaysiawest":
            return "myw"
        case "mexicocentral":
            return "mxc"
        case "newzealandnorth":
            return "nzn"
        case "northcentralus":
            return "ncus"
        case "northeurope":
            return "neu"
        case "norwayeast":
            return "noe"
        case "norwaywest":
            return "now"
        case "polandcentral":
            return "plc"
        case "qatarcentral":
            return "qac"
        case "southafricanorth":
            return "zan"
        case "southafricawest":
            return "zaw"
        case "southcentralus":
            return "scus"
        case "southindia":
            return "sin"
        case "southeastasia":
            return "seas"
        case "spaincentral":
            return "esc"
        case "swedencentral":
            return "sec"
        case "switzerlandnorth":
            return "chn"
        case "switzerlandwest":
            return "chw"
        case "uaecentral":
            return "aec"
        case "uaenorth":
            return "aen"
        case "uksouth":
            return "uks"
        case "ukwest":
            return "ukw"
        case "westcentralus":
            return "wcus"
        case "westeurope":
            return "weu"
        case "westindia":
            return "win"
        case "westus":
            return "wus"
        case "westus2":
            return "wus2"
        case "westus3":
            return "wus3"
        case _:
            raise ValueError(f"Unexpected Azure location: {location}")


if __name__ == "__main__":
    keyvault_exists("rg-bt-env-glaze-env3-neu6vyx", "kvbtglazeenv3neu6vyx")
