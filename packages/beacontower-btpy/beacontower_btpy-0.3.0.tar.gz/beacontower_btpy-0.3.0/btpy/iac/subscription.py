import time

from rich.progress import Progress, TimeElapsedColumn

from btpy import misc
from btpy.az import az

logger = misc.setup_logging()


def get_providers():
    exit_code, result_dict, logs = az("provider list")
    if exit_code != 0:
        logger.error(logs)
        exit(1)
    result_dict = [x for x in result_dict if "namespace" in x]
    return result_dict


def check_if_registered(
    provider_name,
):
    providers = get_providers()
    provider = [x for x in providers if x["namespace"] == provider_name]
    print(provider[0]["registrationState"])
    return "Registered" == provider[0]["registrationState"]


def register_provider(provider_name):
    """ """
    timeout = 300  # 5 minutes
    interval = 5  # 5 seconds
    elapsed_time = 0

    exit_code, result_dict, logs = az(f"provider register --namespace {provider_name}")
    if exit_code != 0:
        logger.error(logs)
        exit(1)
    elif logs:
        logger.info(logs)
    with Progress(
        *Progress.get_default_columns(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task(
            f"Registering provider {provider_name}",
            filename=provider_name,
            start=True,
            total=None,
        )
        while elapsed_time < timeout:
            exit_code, result_dict, logs = az(f"provider show -n {provider_name}")
            if exit_code != 0:
                logger.error(logs)
                exit(1)
            elif logs:
                logger.info(logs)

            if result_dict["registrationState"] == "Registered":
                logger.info(f"{provider_name} registration completed")
                return result_dict

            time.sleep(interval)
            progress.update(task)
            elapsed_time += interval

    # return result_dict
    logger.error(f"{provider_name} registration timed out")
    exit(1)
