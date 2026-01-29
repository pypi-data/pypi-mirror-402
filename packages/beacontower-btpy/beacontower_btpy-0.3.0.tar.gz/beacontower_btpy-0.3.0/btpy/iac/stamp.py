import json

from btpy import misc

stampjs = "stamp.json"


def get_directory():
    c = misc.find_file_in_parent_directories(stampjs)
    return misc.get_directory_of_file(c)


def get_data():
    c = misc.find_file_in_parent_directories(stampjs)
    with open(c, "r") as f:
        return json.load(f)
