import json
from dataclasses import asdict, dataclass, field

from btpy.core import rancher

from btpy.configuration.config import KeyVaultInfo, get_config_value
from btpy.core.azure_utility import get_keyvault_secret
from btpy.core.misc_utility import get_or_create_azure_tenant_sp


@dataclass
class RancherManagementConfig:
    url: str


@dataclass
class RancherCredential:
    client_id: str
    client_secret: str
    subscription_id: str
    tenant_id: str
    name: str


@dataclass
class RancherKeys:
    access_key: str
    secret_key: str


@dataclass
class AzureCredentialConfig:
    clientId: str
    clientSecret: str
    subscriptionId: str
    tenantId: str


@dataclass
class RancherCloudCredentialRequest:
    annotations: dict[str, str]
    name: str
    azurecredentialConfig: AzureCredentialConfig


def get_or_create_rancher_azure_credential(
    tenant_id, subscription_id
) -> RancherCredential:
    client = _get_rancher_client()
    cloud_credentials = client.list_cloud_credential()["data"]
    rancher_cred = None

    for cred in cloud_credentials:
        if cred["annotations"]["provisioning.cattle.io/driver"] != "azure":
            continue
        if cred["azurecredentialConfig"]["tenantId"] != tenant_id:
            continue
        if cred["azurecredentialConfig"]["subscriptionId"] != subscription_id:
            continue

        az_sp = get_or_create_azure_tenant_sp(
            cred["azurecredentialConfig"]["tenantId"],
            cred["azurecredentialConfig"]["subscriptionId"],
        )
        rancher_cred = RancherCredential(
            client_id=cred["azurecredentialConfig"]["clientId"],
            client_secret=az_sp.client_secret,
            subscription_id=cred["azurecredentialConfig"]["subscriptionId"],
            tenant_id=cred["azurecredentialConfig"]["tenantId"],
            name=cred["name"],
        )
        break
    if not rancher_cred:
        az_sp = get_or_create_azure_tenant_sp(tenant_id, subscription_id)
        cred_config = RancherCloudCredentialRequest(
            annotations={"provisioning.cattle.io/driver": "azure"},
            name=f"az-tenant-{tenant_id}-{subscription_id}",
            azurecredentialConfig=AzureCredentialConfig(
                clientId=az_sp.client_id,
                clientSecret=az_sp.client_secret,
                subscriptionId=subscription_id,
                tenantId=tenant_id,
            ),
        )
        created_cred = client.create_cloud_credential(asdict(cred_config))
        rancher_cred = RancherCredential(
            client_id=created_cred["azurecredentialConfig"]["clientId"],
            client_secret=az_sp.client_secret,
            subscription_id=created_cred["azurecredentialConfig"]["subscriptionId"],
            tenant_id=created_cred["azurecredentialConfig"]["tenantId"],
            name=created_cred["name"],
        )

    return rancher_cred


def _get_rancher_client():
    mgmt_info = get_rancher_mgmt_info()
    return rancher.Client(
        url=mgmt_info.url,
        access_key=mgmt_info.access_key,
        secret_key=mgmt_info.secret_key,
    )


@dataclass
class RancherMgmtInfo:
    url: str
    access_key: str
    secret_key: str
    token: str = field(init=False)

    def __post_init__(self):
        self.token = f"{self.access_key}:{self.secret_key}"


def get_rancher_mgmt_info() -> RancherMgmtInfo:
    rancher_mgmt_config = RancherManagementConfig(**get_config_value("rancher_mgmt"))
    if not rancher_mgmt_config:
        raise Exception("[red]Rancher management config not found in btpy config")

    kv_info = KeyVaultInfo(**get_config_value("global_keyvault"))
    rancher_keys = RancherKeys(
        **json.loads(get_keyvault_secret(kv_info.name, "rancher-mgmt-keys"))
    )
    if not rancher_keys:
        raise Exception("[red]Rancher management keys not found in global key vault")

    return RancherMgmtInfo(
        url=rancher_mgmt_config.url,
        access_key=rancher_keys.access_key,
        secret_key=rancher_keys.secret_key,
    )
