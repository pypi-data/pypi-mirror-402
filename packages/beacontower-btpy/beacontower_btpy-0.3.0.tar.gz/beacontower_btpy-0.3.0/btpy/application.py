import json
import os

import chevron

from btpy import misc

filename = "customer.json"
appjs = "application.json"


def get_directory():
    c = misc.find_file_in_parent_directories(appjs)
    return misc.get_directory_of_file(c)


def get_data():
    c = misc.find_file_in_parent_directories(appjs)
    with open(c, "r") as f:
        return json.load(f)


def genenerate_tfbackend_from_template(data):
    """
    Generate tfbackend.tf from template
    data should contain
    - resource_group_name
    - storage_account_name
    - container_name
    - key
    """
    appdir = get_directory()
    with open(os.path.join(appdir, "templates", "backend.mustache"), "r") as f:
        return chevron.render(f, data)


def genenerate_tfproviders_from_template(data):
    """
    Generate tfproviders.tf from template
    data should contain
     - providers - list of providers with object containing
        - name
        - version
        - source
    """
    appdir = get_directory()
    with open(os.path.join(appdir, "templates", "tfproviders.mustache"), "r") as f:
        return chevron.render(f, data)
