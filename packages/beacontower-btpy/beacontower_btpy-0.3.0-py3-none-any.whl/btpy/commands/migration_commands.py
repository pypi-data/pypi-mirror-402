import json
from typing import Annotated

from cyclopts import App
from typer import Argument

from btpy.core.migrations.migration_loader import (
    find_migrations,
    get_migration,
    list_migrations,
)
from btpy.print_utility import DateTimeJsonEncoder

app = App()


@app.command(name="list")
async def list_migrations_cmd():
    migrations = await list_migrations()

    for migration in migrations:
        print(migration)


@app.command(name="show")
async def show_migration_cmd(migration_id: str):
    try:
        migration = await get_migration(migration_id)

        migration_json = json.dumps(migration, indent=4, cls=DateTimeJsonEncoder)
        print(migration_json)
    except Exception as e:
        print(e)


@app.command(name="find")
async def find_migrations_cmd(
    from_version: Annotated[str, Argument(help="wtf??")],
    to_version: Annotated[str, Argument()],
):
    try:
        matched_migrations = await find_migrations(from_version, to_version)

        for migration in matched_migrations:
            print(json.dumps(migration, indent=4, cls=DateTimeJsonEncoder))
    except Exception as e:
        print(e)
