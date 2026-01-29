from typing import Annotated

from cyclopts import App, Parameter

from btpy.core.ad import create_ad

app = App()


@app.command(name="test")
async def create_ad_cmd(
    id: Annotated[str, Parameter(name=["-i", "--id"], required=True)],
    name: Annotated[str, Parameter(name=["-n", "--name"], required=True)],
    resource_group: Annotated[
        str, Parameter(name=["-r", "--resource-group"], required=True)
    ],
    location: Annotated[str, Parameter(name=["-l", "--location"], required=True)],
    country_code: Annotated[
        str, Parameter(name=["-c", "--country-code"], required=True)
    ],
    subscription_id: Annotated[
        str, Parameter(name=["-s", "--subscription-id"], required=True)
    ],
):
    await create_ad(id, name, resource_group, location, country_code, subscription_id)
