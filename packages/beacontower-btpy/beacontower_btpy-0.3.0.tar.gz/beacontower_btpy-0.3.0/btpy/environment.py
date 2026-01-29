import json

from btpy import misc

envjs = "environment.json"


def get_directory():
    c = misc.find_file_in_parent_directories(envjs)
    return misc.get_directory_of_file(c)


def get_data():
    c = misc.find_file_in_parent_directories(envjs)
    with open(c, "r") as f:
        return json.load(f)
