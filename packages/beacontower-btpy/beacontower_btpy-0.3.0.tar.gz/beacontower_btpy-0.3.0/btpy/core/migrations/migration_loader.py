import yaml

from btpy.core.azure_utility import get_blob_client, get_blob_container_client
from btpy.core.envs.env_desc_loader import get_service_versions

MIGRATIONS_CONTAINER_NAME = "migrations"

APPLIES_TO_KEY = "applies_to"
SERVICE_KEY = "service"
VERSION_KEY = "version"


async def list_migrations() -> list[str]:
    migrations_container_client = get_blob_container_client(MIGRATIONS_CONTAINER_NAME)
    migration_id_it = migrations_container_client.list_blob_names()
    migration_names = []

    for migration_id in migration_id_it:
        if "/" not in migration_id:
            migration_blob = get_blob_client(MIGRATIONS_CONTAINER_NAME, migration_id)
            migration = yaml.safe_load(migration_blob.download_blob().readall())

            migration_names.append(to_pretty_migration_name(migration))

    return migration_names


async def get_migration(migration_id: str) -> dict:
    migration_blob = get_blob_client(MIGRATIONS_CONTAINER_NAME, f"{migration_id}.yaml")

    if not migration_blob.exists():
        raise Exception(f"Migration does not exist ({migration_id})")

    return yaml.safe_load(migration_blob.download_blob().readall())


async def find_migrations(from_version: str, to_version: str):
    service_version_changes = _merge_service_versions(
        await get_service_versions(from_version), await get_service_versions(to_version)
    )
    migrations = []
    migration_ids = set()
    all_migrations = await _load_all_migrations()

    for service, versions in service_version_changes.items():
        # Unhandled cases:
        # - If a removed service requires cleanup of database, how do you apply this with `applies_to` list?
        # - If a previously existed service is reintroduced and requires a migration, `from_version` will probably
        # be `None`.
        service_migrations = await find_service_migrations(
            all_migrations, service, versions[0], versions[1]
        )

        for service_migration in service_migrations:
            if service_migration["id"] in migration_ids:
                continue

            migration_ids.add(service_migration["id"])
            migrations.append(service_migration)

    return migrations


async def find_service_migrations(
    all_migrations: list[dict], service: str, from_version: str, to_version: str
):
    if from_version is None or to_version is None:
        return []
    if from_version > to_version:
        raise Exception(
            f"from_version must not be higher than to_version ({from_version}, {to_version})"
        )
    if from_version == to_version:
        return []

    matched_migrations = []

    for migration in all_migrations:
        if _matches_service_version(migration, service, from_version, to_version):
            matched_migrations.append(migration)

    return matched_migrations


async def _load_all_migrations():
    migration_container = get_blob_container_client(MIGRATIONS_CONTAINER_NAME)
    migration_blob_name_it = migration_container.list_blob_names()
    migrations = []

    for migration_blob_name in migration_blob_name_it:
        if "/" not in migration_blob_name:
            migrations.append(
                await get_migration(_without_file_ext(migration_blob_name))
            )

    return migrations


def _matches_service_version(
    migration: dict, service: str, min_version: str, max_version: str
):
    if APPLIES_TO_KEY not in migration:
        raise Exception(f"Invalid migration (missing property {APPLIES_TO_KEY})")

    for service_version in migration[APPLIES_TO_KEY]:
        if service_version[SERVICE_KEY] == service:
            version = service_version[VERSION_KEY]
            if min_version < version <= max_version:
                return True


def _merge_service_versions(from_versions: dict, to_versions: dict):
    service_version_changes = {}

    for service_name, version in from_versions.items():
        if service_name in service_version_changes:
            raise Exception(f"Duplicate service from-version found ({service_name})")

        service_version_changes[service_name] = (version, None)

    for service_name, version in to_versions.items():
        if service_name not in service_version_changes:
            service_version_changes[service_name] = (None, version)
            continue

        if service_version_changes[service_name][1] is not None:
            raise Exception(f"Duplicate service to-version found ({service_name})")

        service_version_changes[service_name] = (
            service_version_changes[service_name][0],
            version,
        )

    return service_version_changes


def to_pretty_migration_name(migration: dict):
    return f"{migration['id']} - {migration['name']}"


def _without_file_ext(filename: str):
    return filename.rsplit(".", 1)[0]
