from rich import print

from btpy.core.envs.env_desc_loader import load_env_desc
from btpy.core.migrations.migration_loader import (
    find_migrations,
    to_pretty_migration_name,
)
from btpy.core.migrations.migration_runner import run_migration


async def migrate_env(env_name: str, to_version: str):
    try:
        env_desc = await load_env_desc(env_name)

        if env_desc.version == to_version:
            print(f"[yellow]Env {env_name} already at version {to_version}")
            return

        if env_desc.version > to_version:
            print(
                f"[red]New version must be higher than current version ({env_desc.version})"
            )
            return

        required_migrations = await find_migrations(env_desc.version, to_version)

        if len(required_migrations) == 0:
            print(
                f"[cyan]No migrations required for upgrade from {env_desc.version} to {to_version}"
            )
        else:
            print(
                f"[cyan]Found {len(required_migrations)} migrations required for upgrade from {env_desc.version} to {to_version}"
            )

        for migration in required_migrations:
            print(f"[cyan]Running migration: {to_pretty_migration_name(migration)}")
            migration_result = await run_migration(env_desc, migration)

            if not migration_result:
                print("[red]Migration failed")
                return
            else:
                print("[green]Migration done")
    except Exception as e:
        print(f"[red]ERROR: {e}")
