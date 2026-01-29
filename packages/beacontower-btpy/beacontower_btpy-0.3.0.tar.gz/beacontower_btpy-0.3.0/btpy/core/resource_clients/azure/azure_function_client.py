from urllib.parse import urljoin

from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.web.aio import WebSiteManagementClient
from azure.mgmt.web.v2022_09_01.models import Site

from btpy.core.azure_utility import get_azure_credential
from btpy.core.envs.env_desc import ResourceDesc
from btpy.core.resource_clients.resource_client import ResourceClient, ResourceStatus


class AzureFunctionClient(ResourceClient):
    def __init__(self, desc: ResourceDesc):
        credential = get_azure_credential()

        self.desc = desc
        self.client = WebSiteManagementClient(
            credential=credential, subscription_id=desc.cloud_resource.sub_id
        )

    async def close(self):
        await self.client.close()

    async def status(self):
        try:
            app_client: Site = await self.client.web_apps.get(
                self.desc.cloud_resource.group, self.desc.cloud_resource.name
            )

            return ResourceStatus.from_str(app_client.state)
        except ResourceNotFoundError:
            return ResourceStatus.Unknown

    async def get_api_url(self):
        app_client: Site = await self.client.web_apps.get(
            self.desc.cloud_resource.group, self.desc.cloud_resource.name
        )
        api_addition = (
            f"/{self.desc.api_url_addition}"
            if self.desc.api_url_addition is not None
            else ""
        )

        return urljoin(f"https://{app_client.default_host_name}/api", api_addition)
