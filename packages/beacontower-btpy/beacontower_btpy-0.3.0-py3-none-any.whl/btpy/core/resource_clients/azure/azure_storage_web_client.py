from azure.storage.blob.aio import BlobServiceClient

from btpy.core.azure_utility import get_azure_credential
from btpy.core.envs.env_desc import ResourceDesc
from btpy.core.resource_clients.resource_client import ResourceClient, ResourceStatus


class AzureStorageWebClient(ResourceClient):
    def __init__(self, desc: ResourceDesc):
        credential = get_azure_credential()

        self.desc = desc
        self.client = BlobServiceClient(
            f"https://{desc.cloud_resource.name}.blob.core.windows.net",
            credential=credential,
        )

    async def close(self):
        await self.client.close()

    async def status(self):
        web_properties = await self._get_web_properties()

        return (
            ResourceStatus.Running if web_properties.enabled else ResourceStatus.Stopped
        )

    async def get_api_url(self):
        # web_properties = await self._get_web_properties()
        return "no_url_in_web_props..."

    async def _get_web_properties(self):
        service_properties = await self.client.get_service_properties()
        return service_properties["static_website"]
