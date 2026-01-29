import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

import yaml

from btpy.configuration.config import StorageAccountConfig, get_config_value
from btpy.core.azure_utility import get_storage_table_entry, list_storage_table_entries

BT_VERSIONS_TABLE_NAME = "btversions"


@dataclass
class BtServiceVersion:
    version: str
    image: str | None


@dataclass
class BtVersion:
    version: str
    release_date: datetime | None
    services: list[BtServiceVersion]


@dataclass
class VersionFileData:
    version: str
    upgraded_from: str | None
    upgraded_at: str


def list_bt_versions() -> list[BtVersion]:
    storage_account_info = _get_storage_account_info()
    result = list_storage_table_entries(
        storage_account_info.name,
        BT_VERSIONS_TABLE_NAME,
        storage_account_info.subscription,
    )
    return [BtVersion(**json.loads(version["data"])) for version in result["items"]]


def get_bt_version(version) -> BtVersion | None:
    storage_account_info = _get_storage_account_info()
    result = get_storage_table_entry(
        storage_account_info.name,
        BT_VERSIONS_TABLE_NAME,
        storage_account_info.subscription,
        version,
        version,
    )
    if not result:
        return None
    return BtVersion(**json.loads(result["data"]))


def write_version_file(repo_path, new_version, old_version, overwrite=False):
    version_file_path = get_version_file_path(repo_path)
    if os.path.exists(version_file_path) and not overwrite:
        return
    version_data = VersionFileData(
        new_version, old_version, datetime.now(timezone.utc).isoformat()
    )
    with open(version_file_path, "w") as version_file:
        yaml.safe_dump(asdict(version_data), version_file)


def read_version_file(repo_path):
    version_file_path = get_version_file_path(repo_path)
    with open(version_file_path, "r") as version_file:
        return VersionFileData(**yaml.safe_load(version_file))


def get_version_file_path(repo_path):
    return os.path.join(repo_path, ".bt-version")


def _get_storage_account_info():
    storage_account_info = StorageAccountConfig(
        **get_config_value("version_storage_account")
    )

    if not storage_account_info:
        raise Exception("Version storage account config not found")

    return storage_account_info
