import os

from cyclopts import App

from btpy.configuration.config import get_config_path, write_default_config

app = App()


@app.command(name="reset")
async def reset_config_cmd():
    config_path = get_config_path()
    write_default_config(os.path.join(config_path, "config.yaml"))
