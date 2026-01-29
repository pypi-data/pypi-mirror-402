import asyncio
from typing import Annotated

from cyclopts import App, Parameter
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from btpy.configuration.aliases import (
    load_aliases,
    remove_alias,
    resolve_env_alias,
    set_alias,
)
from btpy.configuration.config import get_config_path
from btpy.core.envs import env_desc_loader
from btpy.core.envs.env2 import (
    EnvCreationOptions,
    create_env,
    get_env_kubectl,
    list_envs,
    get_env_monitor_info,
)
from btpy.core.envs.env_client import EnvClient
from btpy.core.envs.env_desc_loader import load_env_version
from btpy.core.envs.env_migrator import migrate_env
from btpy.print_utility import print_status

app = App()


@app.command(name="create")
async def create_env_cmd(
    *,
    customer: Annotated[str, Parameter(name=["-c", "--customer"], required=True)],
    environment: Annotated[str, Parameter(name=["-e", "--environment"], required=True)],
    location: Annotated[str, Parameter(name=["-l", "--location"], required=True)],
    suffix: Annotated[str, Parameter(name=["-s", "--suffix"])] = None,
    regen_ssh: Annotated[bool, Parameter(name=["--regen-ssh"])] = False,
    regen_sp: Annotated[bool, Parameter(name=["--regen-sp"])] = False,
):
    """Create a new environment with specified parameters.

    Args:
        -c, --customer: Customer name or identifier
        -e, --environment: Environment name (e.g., dev, test, prod)
        -l, --location: Azure region location
        -s, --suffix: Optional 4 char custom suffix for environment name, will be randomized otherwise
        --regen-ssh: If True, regenerate SSH keys even if they exist
        --regen-sp: If True, regenerate service principal credentials even if they exist
    """
    options = EnvCreationOptions(
        customer=customer,
        environment=environment,
        location=location,
        suffix=suffix,
        regen_ssh=regen_ssh,
        regen_sp=regen_sp,
    )
    create_env(options)


@app.command(name="list")
async def list_envs_cmd():
    env_list = list_envs()
    table = Table()

    table.add_column("env")
    table.add_column("desc")
    table.add_column("keyvault")
    table.add_column("sub")
    table.add_column("tenant")

    for env in env_list:
        table.add_row(
            env.name, "", env.keyvault_name, env.subscription_id, env.tenant_id
        )

    print(table)


alias_app = App(name="alias", help="Manage environment name aliases")


@alias_app.command(name="set")
def alias_set_cmd(alias: str, env_name: str):
    """Set an alias for an environment name.

    Args:
        alias: Short name to use (e.g., 'test')
        env_name: Full environment name (e.g., 'glaze-test-neu1234')
    """
    set_alias(alias, env_name)
    print(f"[green]Alias '{alias}' -> '{env_name}' set successfully")


@alias_app.command(name="list")
def alias_list_cmd():
    """List all configured aliases."""
    aliases = load_aliases()

    if not aliases:
        print("[yellow]No aliases configured")
        return

    table = Table(title="Environment Aliases")
    table.add_column("Alias", style="cyan")
    table.add_column("Environment Name", style="blue")

    for alias, env_name in sorted(aliases.items()):
        table.add_row(alias, env_name)

    print(table)


@alias_app.command(name="remove")
def alias_remove_cmd(alias: str):
    """Remove an alias.

    Args:
        alias: The alias to remove
    """
    if remove_alias(alias):
        print(f"[green]Alias '{alias}' removed successfully")
    else:
        print(f"[yellow]Alias '{alias}' not found")


app.command(alias_app)


@app.command(name="connect")
async def connect_env_cmd(env_name: str):
    env_name = resolve_env_alias(env_name)
    kubeconfig = get_env_kubectl(env_name)

    if not kubeconfig:
        print("[red]Env kubeconfig not found")
        return

    env_kubeconfig_path = get_config_path() / f"kubeconfig-{env_name}"
    with open(env_kubeconfig_path, "w") as kubeconfig_file:
        kubeconfig_file.write(kubeconfig)

    print(f"export KUBECONFIG={env_kubeconfig_path}")
    return


@app.command(name="monitor")
async def monitor_info_cmd(
    *, env: Annotated[str, Parameter(name=["-e", "--env"], required=True)]
):
    env_name = resolve_env_alias(env)
    monitor_info = get_env_monitor_info(env_name)
    print(monitor_info.url)


# TODO: Add validation command to check repo, azure resources?, cluster status?


@app.command(name="version")
async def env_version_cmd(env_name: str):
    try:
        version = await load_env_version(env_name)
        print(version)
    except Exception as e:
        print(e)


@app.command(name="status")
async def env_status_cmd(env_name: str):
    try:
        env_desc = await env_desc_loader.load_env_desc(env_name)

        if env_desc is None:
            print("Env not found")
            return
    except Exception as e:
        print(e)
        return

    env_client = EnvClient(env_desc)
    resource_clients = env_client.get_resource_clients()

    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        TextColumn("{task.fields[result]}"),
    ) as table:
        loop = asyncio.get_event_loop()
        tasks = [
            (
                resource_client,
                loop.create_task(_get_formatted_status(resource_client.client)),
                table.add_task(f"[blue]{resource_client.name}[/blue]", result=""),
            )
            for resource_client in resource_clients
        ]

        while not table.finished:
            for resource_client, task, table_task in tasks:
                if task.done():
                    table.update(
                        table_task, total=100, completed=100, result=task.result()
                    )

            await asyncio.sleep(0.1)

    [await resource_client.client.close() for resource_client in resource_clients]


@app.command(name="upgrade")
async def upgrade_env_cmd(env_name: str, to_version: str):
    await migrate_env(env_name, to_version)


async def _get_formatted_status(resource_client):
    status = await resource_client.status()
    return print_status(status)
