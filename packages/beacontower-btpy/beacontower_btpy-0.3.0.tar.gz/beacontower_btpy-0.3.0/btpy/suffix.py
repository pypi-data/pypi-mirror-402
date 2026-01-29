import json
import os
import random
import string

from btpy import application, environment, misc

logger = misc.setup_logging()


def generate(prefix=""):
    suffix = "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(4)
    )
    return {f"{prefix}suffix": suffix}


def write(data, filename="suffix.json", rewrite=False):
    """
    Write suffix to file. If file exists, ask user if they want to overwrite.
    return if we allow re-writing of suffixes.
    """
    try:
        if rewrite:
            misc.write_json(filename, data)
            return True
        existing_suffix = get_data(filename, in_parent_directories=False)
        key = os.path.basename(filename).split(".")[0]
        new_suffix = input(
            f"Suffix already exists. ({existing_suffix[key]}) Do you want to generate a new one? (N/y): "
        )
        if new_suffix == "y":
            misc.write_json(filename, data)
            return True
        else:
            return False
    except FileNotFoundError:
        logger.info("Suffix file not found. Generating a new one.")
        misc.write_json(filename, data)


def get_data(filename="suffix.json", in_parent_directories=True):
    path = (
        misc.find_file_in_parent_directories(filename)
        if in_parent_directories
        else filename
    )
    with open(path, "r") as f:
        return json.load(f)


def write_global_suffix(suffix=None, rewrite=False):
    data = (
        generate(prefix="global_")
        if not suffix
        else {"global_suffix": suffix["suffix"]}
    )
    app_dir = application.get_directory()
    write(data, filename=os.path.join(app_dir, "global_suffix.json"), rewrite=rewrite)


def get_global_suffix():
    app_dir = application.get_directory()
    return get_data(filename=os.path.join(app_dir, "global_suffix.json"))


def write_environment_suffix(suffix=None, rewrite=False):
    data = (
        generate(prefix="environment_")
        if not suffix
        else {"environment_suffix": suffix["suffix"]}
    )
    env_dir = environment.get_directory()
    write(
        data, filename=os.path.join(env_dir, "environment_suffix.json"), rewrite=rewrite
    )


def get_environment_suffix():
    env_dir = environment.get_directory()
    return get_data(filename=os.path.join(env_dir, "environment_suffix.json"))
