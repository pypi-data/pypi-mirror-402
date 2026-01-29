from enum import Enum


class EnvDesc:
    def __init__(self, desc_obj: dict):
        self.tenant = TenantDesc(desc_obj["tenant"])
        self.version = desc_obj["version"]
        self.default_user = DefaultUserDesc(desc_obj["defaultUser"])
        self.services = [ServiceDesc(service) for service in desc_obj["services"]]


class TenantDesc:
    def __init__(self, desc_obj: dict):
        self.id = desc_obj["id"]
        self.client_id = desc_obj["clientId"]
        self.sign_in_flow = desc_obj["signInFlow"]


class DefaultUserDesc:
    def __init__(self, desc_obj: dict):
        self.email = desc_obj["email"]
        self.password = desc_obj["password"]


class ServiceDesc:
    def __init__(self, desc_obj: dict):
        self.name = desc_obj["name"]
        self.resources = [ResourceDesc(resource) for resource in desc_obj["resources"]]
        # self.settings = load_service_settings_from_json(desc_obj.get("settings"))


class ResourceDesc:
    def __init__(self, desc_obj: dict):
        self.name = desc_obj["name"]
        self.cloud_resource = load_cloud_resource_desc_from_json(
            desc_obj["cloudResource"]
        )
        self.api_url_addition = desc_obj.get("apiUrlAddition")
        self.settings = desc_obj.get("settings")


class AzureAppServiceDesc:
    def __init__(self, desc_obj: dict):
        if desc_obj["type"] != CloudResourceType.AzureAppService.value:
            raise ValueError("Invalid CloudResource type")

        self.type = CloudResourceType.AzureAppService
        self.name = desc_obj["name"]
        self.group = desc_obj["group"]
        self.sub_id = desc_obj["subscriptionId"]
        # self.tenant_id = desc_obj["tenantId"]


class AzureFunctionDesc:
    def __init__(self, desc_obj: dict):
        if desc_obj["type"] != CloudResourceType.AzureFunction.value:
            raise ValueError("Invalid CloudResource type")

        self.type = CloudResourceType.AzureFunction
        self.name = desc_obj["name"]
        self.group = desc_obj["group"]
        self.sub_id = desc_obj["subscriptionId"]
        # self.tenant_id = desc_obj["tenantId"]


class AzureVmDesc:
    def __init__(self, desc_obj: dict):
        if desc_obj["type"] != CloudResourceType.AzureVm.value:
            raise ValueError("Invalid CloudResource type")

        self.type = CloudResourceType.AzureVm
        self.name = desc_obj["name"]
        self.group = desc_obj["group"]
        self.sub_id = desc_obj["subscriptionId"]
        # self.tenant_id = desc_obj["tenantId"]
        self.sub_desc = load_vm_sub_desc_from_json(desc_obj["subDesc"])


class AzureStorageWebDesc:
    def __init__(self, desc_obj: dict):
        if desc_obj["type"] != CloudResourceType.AzureStorageWeb.value:
            raise ValueError("Invalid CloudResource type")

        self.type = CloudResourceType.AzureStorageWeb
        self.name = desc_obj["name"]
        self.group = desc_obj["group"]
        self.sub_id = desc_obj["subscriptionId"]
        # self.tenant_id = desc_obj["tenantId"]


class CloudResourceType(Enum):
    AzureAppService = "AzureAppService"
    AzureFunction = "AzureFunction"
    AzureVm = "AzureVm"
    AzureStorageWeb = "AzureStorageWeb"


class VmDockerComposeSubDesc:
    def __init__(self, desc_obj: dict):
        if desc_obj["type"] != VmSubDescType.DockerCompose.value:
            raise ValueError("Invalid VmSubDesc type")

        self.type = VmSubDescType.DockerCompose
        self.path = desc_obj["path"]
        self.config_files = desc_obj.get("configFiles")


class VmSubDescType(Enum):
    DockerCompose = "DockerCompose"


def load_vm_sub_desc_from_json(desc_obj: dict):
    desc_type = desc_obj["type"]

    if desc_type == "DockerCompose":
        return VmDockerComposeSubDesc(desc_obj)


def load_cloud_resource_desc_from_json(desc_obj: dict):
    desc_type = desc_obj["type"]

    if desc_type == "AzureAppService":
        return AzureAppServiceDesc(desc_obj)
    elif desc_type == "AzureFunction":
        return AzureFunctionDesc(desc_obj)
    elif desc_type == "AzureVm":
        return AzureVmDesc(desc_obj)
    elif desc_type == "AzureStorageWeb":
        return AzureStorageWebDesc(desc_obj)
    else:
        raise ValueError(f"Invalid CloudResource type: {desc_type}")
