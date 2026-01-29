from azure.mgmt.compute.aio import ComputeManagementClient

from btpy.core.azure_utility import get_azure_credential
from btpy.core.envs.env_desc import ResourceDesc
from btpy.core.resource_clients.resource_client import ResourceClient, ResourceStatus


class AzureVmClient(ResourceClient):
    def __init__(self, desc: ResourceDesc):
        credential = get_azure_credential()

        self.desc = desc
        self.management_client = ComputeManagementClient(
            credential=credential, subscription_id=desc.cloud_resource.sub_id
        )

    async def close(self):
        await self.management_client.close()

    async def status(self):
        # vm_client: VirtualMachine = await self.management_client.virtual_machines.get(
        #     self.desc.cloud_resource.group, self.desc.cloud_resource.name
        # )

        # return vm_client.instance_view.statuses  # TODO: Check if this even works
        return ResourceStatus.Unknown
