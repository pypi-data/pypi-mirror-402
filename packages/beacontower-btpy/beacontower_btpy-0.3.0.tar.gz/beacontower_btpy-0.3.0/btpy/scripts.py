import os
import sys


def check_if_script_dir_exists():
    """
    Check if the script is being run from the root of the terraform entity.
    All scripts are expected to have the terraform main.tf file in
    the current working directory.

    return the name of the current directory which is the name of the current feature
    """
    if not os.path.exists(os.path.join(os.getcwd(), "scripts")):
        print("Please run this script from the root of the repository.")
        sys.exit(1)
    else:
        return os.getcwd().split(os.sep)[-1].strip().replace(" ", "_")
