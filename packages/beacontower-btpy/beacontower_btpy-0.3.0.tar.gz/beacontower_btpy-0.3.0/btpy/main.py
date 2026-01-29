import importlib.metadata

from cyclopts import App

from btpy.commands import (
    config_commands,
    env_commands,
    iac_commands,
    migration_commands,
    software_commands,
    tenant_commands,
    version_commands,
    ad_commands,
)


def get_version():
    return importlib.metadata.version("beacontower-btpy")


app = App(version=get_version)

app.command(env_commands.app, name="env")
app.command(software_commands.app, name="software")
app.command(iac_commands.app, name="iac")
app.command(migration_commands.app, name="migration")
app.command(tenant_commands.app, name="tenant")
app.command(config_commands.app, name="config")
app.command(version_commands.app, name="version")
app.command(ad_commands.app, name="ad")

if __name__ == "__main__":
    app()
