from cyclopts import App

from btpy.core.versions import list_bt_versions, get_bt_version

app = App()


@app.command(name="list")
async def list_versions_cmd():
    bt_versions = list_bt_versions()
    print([bt_version.version for bt_version in bt_versions])


@app.command(name="show")
async def show_version_cmd(version: str):
    bt_version = get_bt_version(version)
    print(bt_version)
