import json
import os

from btpy import variables


def create_tfvars_directory(directory):
    """
    Create a tfvars directory in a directory.
    """
    tfvars_dir = os.path.join(directory, "tfvars")
    if not os.path.exists(tfvars_dir):
        os.mkdir(tfvars_dir)
    return tfvars_dir


def write_config_data_to_tfvars_json_file(tfname, tfvars_dir, data):
    """
    Write a <tfname>.tfvars.json file to a tfvar directory.
    """
    # reformat data to be compatible with terraform output format
    output = {}
    for key, value in data.items():
        output[key] = {"value": value}
    write_tfvars_json_file(tfname, tfvars_dir, output)


def write_tfvars_json_file(tfname, tfvars_dir, tfvars_json):
    """
    Write a <tfname>.tfvars.json file to a tfvar directory.
    """
    with open(os.path.join(tfvars_dir, f"{tfname}.tfvars.json"), "w") as f:
        f.write(json.dumps(tfvars_json, indent=4))


def find_all_directories(starting_directory, excluded_dirs=[]):
    """
    find all tfvars directories in all subdirectories of a starting directory.
    This can be used to find all directories where a to update a tfvars.json file.

    exclude is a list of directories to exclude from the returned list.

    """
    for root, dirs, files in os.walk(starting_directory):
        if "tfvars" in dirs:
            if root not in excluded_dirs:
                yield os.path.join(root, "tfvars")


def merge_all_tfvars(tfvars_dir):
    """
    Merge all tfvars files in the tfvars directory into a single dictionary.
    """
    # get all tfvars files in the tfvars directory
    tfvars_files = [
        os.path.join(tfvars_dir, file)
        for file in sorted(os.listdir(tfvars_dir))
        if file.endswith(".tfvars.json")
    ]

    # merge all tfvars json files
    merged_tfvars = {}
    for tfvars_file in tfvars_files:
        try:
            with open(tfvars_file, "r") as f:
                merged_tfvars = {**merged_tfvars, **json.load(f)}
        except ValueError:
            print(f"Error reading {tfvars_file}")

    return merged_tfvars


def write_file_and_update(output, tfvars_dir, tfname):
    """
    Write <output> to <tfname>.tfvars.json file in <tfvars_dir> and run the
    create_tfvars.py to generate a new terraform.tvars.json in parent dir of <tfvars_dir>.
    """
    write_tfvars_json_file(tfname, tfvars_dir, output)
    merged_tfvars = merge_all_tfvars(tfvars_dir)
    drive, path = os.path.splitdrive(tfvars_dir)
    tfvars_dir_list = path.split(os.sep)
    parent_dir = os.path.join(os.sep, *tfvars_dir_list[:-1])
    if drive:
        parent_dir = os.path.join("C:\\", parent_dir)

    vars = variables.parse_tf_file(os.path.join(parent_dir, "variables.tf"))

    create_filtered_tfvars_file(parent_dir, vars, merged_tfvars)


def create_filtered_tfvars_file(dir, variables, merged_tfvars):
    """
    Create a tfvars json file with only the merged_tfvars entries present as variables in variable.tf
    """
    filtered_variables = [
        variable for variable in variables if variable in merged_tfvars.keys()
    ]
    with open(os.path.join(dir, "terraform.tfvars.json"), "w") as f:
        json.dump(
            {
                variable: merged_tfvars[variable]["value"]
                for variable in filtered_variables
            },
            f,
            indent=4,
        )
