import asyncio
from types import SimpleNamespace

from btpy.core.envs.env_desc import EnvDesc
from btpy.core.envs.env_utility import to_resource_name
from btpy.core.resource_clients.resource_client import ResourceStatus
from btpy.core.resource_clients.resource_client_factory import get_resource_client


class EnvClient:
    def __init__(self, env_desc: EnvDesc):
        self.desc = env_desc

    async def status(self):
        resource_clients = self.get_resource_clients()
        named_tasks = {
            resource_client.name: asyncio.create_task(resource_client.client.status())
            for resource_client in resource_clients
        }
        status_results = await asyncio.gather(*named_tasks.values())

        service_statuses = [
            SimpleNamespace(name=name, status=result)
            for (name, result) in zip(named_tasks.keys(), status_results)
        ]
        env_status = self._get_env_status_from_service_statuses(service_statuses)

        [await resource_client.client.close() for resource_client in resource_clients]

        return SimpleNamespace(status=env_status, services=service_statuses)

    def get_resource_client(self, resource_name):
        resource_name_parts = resource_name.split(".")
        service_name = resource_name_parts[0]
        resource_name = resource_name_parts[1]
        service_desc = next(
            (service for service in self.desc.services if service.name == service_name),
            None,
        )

        if service_desc is None:
            return None

        resource_desc = next(
            (
                resource
                for resource in service_desc.resources
                if resource.name == resource_name
            ),
            None,
        )

        if resource_desc is None:
            return None

        return get_resource_client(resource_desc)

    def get_resource_clients(self):
        resource_clients = []

        for service in self.desc.services:
            for resource in service.resources:
                client = get_resource_client(resource)
                resource_name = to_resource_name(service.name, resource.name)
                resource_clients.append(
                    SimpleNamespace(name=resource_name, client=client)
                )

        return resource_clients

    @staticmethod
    def _get_env_status_from_service_statuses(service_statuses):
        if all(
            service.status == service_statuses[0].status for service in service_statuses
        ):
            return service_statuses[0].status

        return ResourceStatus.Mixed
