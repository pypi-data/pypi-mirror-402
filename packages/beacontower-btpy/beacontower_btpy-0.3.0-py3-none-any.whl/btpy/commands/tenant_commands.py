from typing import Annotated

from cyclopts import App, Parameter
from rich import print
from rich.table import Table

from btpy.configuration.aliases import (
    load_aliases,
    remove_alias,
    resolve_env_alias,
    resolve_tenant_alias,
    set_alias,
)
from btpy.core.tenant.tenant import (
    TenantCreationOptions,
    create_tenant,
    list_tenants,
    register_tenant_in_env,
    unregister_tenant_from_env,
    get_tenant_debug_telemetry_config,
    set_tenant_debug_telemetry_loglevel,
    listen_to_tenant_eventhub,
    set_tenant_debug_telemetry_tracing,
    get_tenant_login_info,
)

app = App()


@app.command(name="create")
async def create_tenant_cmd(
    *,
    customer: Annotated[str, Parameter(name=["-c", "--customer"], required=True)],
    tenant_env: Annotated[str, Parameter(name=["-t", "--tenant-env"], required=True)],
    location: Annotated[str, Parameter(name=["-l", "--location"], required=True)],
    cluster_env: Annotated[
        str, Parameter(name=["-e", "--environment"], required=True)
    ] = None,
    version: Annotated[
        str, Parameter(name=["-v", "--version"], required=False)
    ] = "latest",
    subdomain: Annotated[
        str, Parameter(name=["-d", "--subdomain"], required=False)
    ] = None,
    suffix: Annotated[str, Parameter(name=["-s", "--suffix"])] = None,
    regen_ssh: Annotated[bool, Parameter(name=["--regen-ssh"])] = False,
):
    """Create a new tenant repo folder and necessary resources.

    Args:
        -c, --customer: Customer name or identifier.
        -t, --tenant-env: Tenant environment name (e.g., dev, test, prod).
        -l, --location: Cloud location/region (e.g., westeurope, eastus).
        -e, --environment: Cluster environment name or alias.
        -v, --version: Version to use for templates/resources. Defaults to "latest".
        -d, --subdomain: Subdomain used for the tenant ingress. Defaults to tenant name, e.g. "glaze-prod-neu1234".
        -s, --suffix: Optional suffix appended to generated resource names. Will be generated if unset.
        --regen-ssh: Regenerate SSH keys even if they already exist in Key Vault.
    """

    cluster_env = resolve_env_alias(cluster_env)

    options = TenantCreationOptions(
        customer,
        tenant_env,
        location,
        cluster_env,
        subdomain,
        version,
        suffix,
        regen_ssh,
    )
    create_tenant(options)


@app.command(name="list")
async def list_tenants_cmd(
    *,
    env: Annotated[str, Parameter(name=["-e", "--env"], required=True)],
    by_repo: Annotated[
        bool, Parameter(name=["-r", "--by-repo"], required=False)
    ] = False,
):
    """List registered tenants.

    Lists tenants for the specified environment. Use ``--by-repo`` to list
    tenants discovered from repository configuration instead of environment registration.

    Args:
        -e, --env: Environment name or alias to filter tenants by. Required.
        -r, --by-repo: If set, list tenants by repository instead of environment. Optional.
    """
    method = "env-list" if not by_repo else "repo"
    env_name = resolve_env_alias(env)
    tenants = list_tenants(env_name, method)
    table = Table()

    table.add_column("name")

    for tenant in tenants:
        table.add_row(tenant)

    print(table)


@app.command(name="register")
async def register_tenant_repo_cmd(tenant_name):
    """Registers tenant with environment and its flux system"""

    tenant_name = resolve_tenant_alias(tenant_name)
    register_tenant_in_env(tenant_name)


@app.command(name="unregister")
async def unregister_tenant_repo_cmd(tenant_name):
    """Unregisters tenant from environment and its flux system"""

    tenant_name = resolve_tenant_alias(tenant_name)
    unregister_tenant_from_env(tenant_name)


@app.command(name="log")
async def tenant_log_level_cmd(
    log_level: str = None,
    *,
    tenant: Annotated[str, Parameter(name=["-t", "--tenant"], required=True)],
    services: Annotated[list[str], Parameter(name=["-s", "--service"])] = None,
):
    tenant_name = resolve_tenant_alias(tenant)

    if not log_level:
        log_levels = get_tenant_debug_telemetry_config(tenant_name, services)
        table = Table()
        table.add_column("pod")
        table.add_column("log level")

        for pod in sorted(log_levels.items()):
            table.add_row(pod[0], pod[1]["logLevel"])

        print(table)
    else:
        log_levels = set_tenant_debug_telemetry_loglevel(
            tenant_name, log_level, services
        )
        table = Table()
        table.add_column("pod")
        table.add_column("log level")

        for pod in sorted(log_levels.items()):
            table.add_row(pod[0], pod[1]["logLevel"])

        print(table)


@app.command(name="trace")
async def tenant_trace_cmd(
    trace_enabled: bool = None,
    *,
    tenant: Annotated[str, Parameter(name=["-t", "--tenant"], required=True)],
    services: Annotated[list[str], Parameter(name=["-s", "--service"])] = None,
):
    tenant_name = resolve_tenant_alias(tenant)

    if trace_enabled is None:
        trace_settings = get_tenant_debug_telemetry_config(tenant_name, services)
        table = Table()
        table.add_column("pod")
        table.add_column("tracing")

        for pod in sorted(trace_settings.items()):
            table.add_row(pod[0], pod[1]["tracingEnabled"])

        print(table)
    else:
        trace_settings = set_tenant_debug_telemetry_tracing(
            tenant_name, trace_enabled, services
        )
        table = Table()
        table.add_column("pod")
        table.add_column("tracing")

        for pod in sorted(trace_settings.items()):
            table.add_row(pod[0], str(pod[1]["tracingEnabled"]))

        print(table)


@app.command(name="eh-listen")
async def tenant_listen_eh_cmd(
    eh_name: str,
    *,
    tenant: Annotated[str, Parameter(name=["-t", "--tenant"], required=True)],
):
    """Listen to event hub events

    Args:
        eh_name: Event hub name (without `eh-` prefix), e.g. device, ingress, orleans or timeseries.
    """
    tenant_name = resolve_tenant_alias(tenant)

    listen_to_tenant_eventhub(tenant_name, eh_name)


@app.command(name="login")
async def tenant_login_info_cmd(
    *, tenant: Annotated[str, Parameter(name=["-t", "--tenant"], required=True)]
):
    tenant_name = resolve_tenant_alias(tenant)
    login_info = get_tenant_login_info(tenant_name)
    print(login_info.url)
    print(login_info.email)
    print(login_info.password)


alias_app = App(name="alias", help="Manage tenant name aliases")


@alias_app.command(name="set")
def alias_set_cmd(alias: str, tenant_name: str):
    """Set an alias for a tenant name.

    Args:
        alias: Short name to use (e.g., 'prod-tenant')
        tenant_name: Full tenant name or keyvault name
    """
    set_alias(alias, tenant_name, alias_type="tenant")
    print(f"[green]Tenant alias '{alias}' -> '{tenant_name}' set successfully")


@alias_app.command(name="list")
def alias_list_cmd():
    """List all configured tenant aliases."""
    aliases = load_aliases(alias_type="tenant")

    if not aliases:
        print("[yellow]No tenant aliases configured")
        return

    table = Table(title="Tenant Aliases")
    table.add_column("Alias", style="cyan")
    table.add_column("Tenant Name", style="blue")

    for alias, tenant_name in sorted(aliases.items()):
        table.add_row(alias, tenant_name)

    print(table)


@alias_app.command(name="remove")
def alias_remove_cmd(alias: str):
    """Remove a tenant alias.

    Args:
        alias: The alias to remove
    """
    if remove_alias(alias, alias_type="tenant"):
        print(f"[green]Tenant alias '{alias}' removed successfully")
    else:
        print(f"[yellow]Tenant alias '{alias}' not found")


app.command(alias_app)
