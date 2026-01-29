from cyclopts import App
from rich.progress import Progress, TimeElapsedColumn

from btpy.az import az
from btpy.iac import misc

app = App()

logger = misc.setup_logging()


def fetch_all_versions():
    exit_code, result_dict, logs = az(
        "acr repository list -n beacontower --output json"
    )
    if exit_code != 0:
        logger.error(logs)
        exit(1)
    logger.debug(result_dict)
    release_dict = {}

    with Progress(
        *Progress.get_default_columns(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task(
            "fetching versions for repositories",
            filename="repositories",
            start=True,
            total=len(result_dict) + 1,
        )
        for repo in result_dict:
            exit_code, result_dict, logs = az(
                f"acr repository show-tags -n beacontower --repository {repo} --output json --top 5 --orderby time_desc"
            )
            if exit_code != 0:
                logger.error(logs)
                exit(1)
            logger.debug(result_dict)
            for tag in result_dict:
                logger.info(f"{repo}:{tag}")
            repovalue = f"{repo}:{result_dict[1]}"
            container_name = repo.replace("beacontower-", "")
            release_dict[f"{container_name}-version"] = repovalue
            progress.update(task, advance=1)

        exit_code, result_dict, logs = az(
            'storage blob list --container-name "beacontower-webclient" --connection-string "DefaultEndpointsProtocol=https;AccountName=storbtrelease;AccountKey=syy2XekWvISccZFWQ+ivfTHR0XY6EmTkAaErAv9H4kDPa6DTx4mIbsDooRDQQJbXZl6uFVlnlL5tfL8x6dI5uw==;EndpointSuffix=core.windows.net;" --output json --query "[].name"'
        )
        # remove the .zip extension on each item and store it in a new list
        versions = []
        for item in result_dict:
            versions.append(item.replace(".zip", ""))

        logger.debug(versions)
        # filter out versions that are not semantically versioned
        versions = [version for version in versions if version.count(".") == 2]
        # sort the list containing semantically versioned strings
        versions.sort(key=lambda x: tuple(map(int, x.split("."))))
        logger.debug(versions)
        release_dict["frontend-version"] = versions[-1]
        progress.update(task, advance=1)
    # # pretty print the dictionary
    # for key, value in release_dict.items():
    #     print(f"{key}: {value}")
    return release_dict


@app.command
def auto_tfvars():
    release_dict = fetch_all_versions()
    misc.write_json("beacontower-versions.auto.tfvars.json", release_dict)


@app.command
def list():
    release_dict = fetch_all_versions()
    for key, value in release_dict.items():
        print(f"{key}: {value}")
