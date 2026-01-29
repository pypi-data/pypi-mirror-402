from btpy.core.envs.env_desc import CloudResourceType, ResourceDesc
from btpy.core.resource_clients.azure.azure_appservice_client import (
    AzureAppServiceClient,
)
from btpy.core.resource_clients.azure.azure_function_client import AzureFunctionClient
from btpy.core.resource_clients.azure.azure_storage_web_client import (
    AzureStorageWebClient,
)
from btpy.core.resource_clients.azure.azure_vm_client import AzureVmClient
from btpy.core.resource_clients.resource_client import ResourceClient


def get_resource_client(desc: ResourceDesc) -> ResourceClient:
    if desc.cloud_resource.type == CloudResourceType.AzureAppService:
        return AzureAppServiceClient(desc)
    if desc.cloud_resource.type == CloudResourceType.AzureVm:
        return AzureVmClient(desc)
    elif desc.cloud_resource.type == CloudResourceType.AzureFunction:
        return AzureFunctionClient(desc)
    elif desc.cloud_resource.type == CloudResourceType.AzureStorageWeb:
        return AzureStorageWebClient(desc)
    else:
        raise ValueError("Invalid CloudResource type")
