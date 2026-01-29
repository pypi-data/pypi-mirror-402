import json

from dda_python_terraform import Terraform


def get_output():
    t = Terraform()
    return_code, out, err = t.output_cmd("-json", capture_output=True)
    return json.loads(out)


def clean_output(output):
    return {key: value["value"] for key, value in output.items()}
