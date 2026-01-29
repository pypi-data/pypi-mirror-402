import os
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

ENV_DATA_STORAGE_NAME_ENV_VAR_KEY = "BTPY_ENV_DATA_STORAGE_NAME"
ENV_DATA_STORAGE_NAME_CONFIG_KEY = "EnvDataStorageName"


@dataclass
class KeyVaultInfo:
    name: str
    tenant: str
    subscription: str


@dataclass
class RancherMgmtConfig:
    url: str


@dataclass
class DomainConfig:
    default: str


@dataclass
class StorageAccountConfig:
    name: str
    tenant: str
    subscription: str


@dataclass
class BtpyConfig:
    domain: DomainConfig
    EnvDataStorageName: str
    env_list_storage_account: KeyVaultInfo
    global_keyvault: KeyVaultInfo
    rancher_mgmt: RancherMgmtConfig
    version_storage_account: StorageAccountConfig


def get_config_path() -> Path:
    if os.name == "nt":  # Windows
        return Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "btpy"
    elif os.name == "posix":  # Unix-like systems (Linux, macOS, etc.)
        if sys.platform == "darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "btpy"
        else:  # Linux and other Unix-like systems
            return Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "btpy"
    else:
        raise NotImplementedError(f"Unsupported platform: {os.name}")


def get_config_value(key):
    config_path = get_config_path()
    config_file_path = os.path.expanduser(os.path.join(config_path, "config.yaml"))

    if not os.path.exists(config_file_path):
        write_default_config(config_file_path)

    with open(config_file_path, "r") as config_file:
        config_yaml = yaml.safe_load(config_file)
        return config_yaml.get(key)


def get_config() -> BtpyConfig:
    """Load the full typed config"""
    config_path = get_config_path()
    config_file_path = os.path.expanduser(os.path.join(config_path, "config.yaml"))

    if not os.path.exists(config_file_path):
        write_default_config(config_file_path)

    with open(config_file_path, "r") as config_file:
        config_yaml = yaml.safe_load(config_file)
        return BtpyConfig(
            EnvDataStorageName=config_yaml["EnvDataStorageName"],
            env_list_storage_account=KeyVaultInfo(
                **config_yaml["env_list_storage_account"]
            ),
            global_keyvault=KeyVaultInfo(**config_yaml["global_keyvault"]),
            rancher_mgmt=RancherMgmtConfig(**config_yaml["rancher_mgmt"]),
            domain=DomainConfig(**config_yaml["domain"]),
            version_storage_account=StorageAccountConfig(
                **config_yaml["version_storage_account"]
            ),
        )


def get_env_data_storage_name():
    # Try env var
    env_value = os.getenv(ENV_DATA_STORAGE_NAME_ENV_VAR_KEY)

    if env_value:
        return env_value

    # Try user config file
    conf = get_config_path()
    # conf = get_config_path().mkdir(parents=True, exist_ok=True)
    config_file_path = os.path.expanduser(os.path.join(conf, "config.yaml"))

    if not os.path.exists(config_file_path):
        raise FileNotFoundError(
            f"Failed to read env data storage name from file: {config_file_path} \
        (can also be set through env var: {ENV_DATA_STORAGE_NAME_ENV_VAR_KEY})"
        )

    with open(config_file_path, "r") as config_file:
        config_yaml = yaml.safe_load(config_file)
        config_value = config_yaml[ENV_DATA_STORAGE_NAME_CONFIG_KEY]

        if config_value:
            return config_value
        return None


def write_default_config(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as config_file:
        config_file.write(
            """
EnvDataStorageName: stgbttfdata
env_list_storage_account:
  tenant: 953ee0f9-5c0c-4769-b099-eca3c4193550
  subscription: bf222aeb-b358-4dc5-b2a3-07503773a0e3
  name: stgbttfdata
global_keyvault:
  tenant: 953ee0f9-5c0c-4769-b099-eca3c4193550
  subscription: bf222aeb-b358-4dc5-b2a3-07503773a0e3
  name: btdeploymentdata
version_storage_account:
  tenant: 953ee0f9-5c0c-4769-b099-eca3c4193550
  subscription: bf222aeb-b358-4dc5-b2a3-07503773a0e3
  name: stgbttfdata
rancher_mgmt:
  url: https://bt-rancher.northeurope.cloudapp.azure.com/v3
domain:
  default: beacontower.app
"""
        )
