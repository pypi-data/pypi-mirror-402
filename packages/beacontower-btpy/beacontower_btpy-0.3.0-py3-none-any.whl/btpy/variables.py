def parse_tf_file(file):
    """
    Parse the terraform variable file and return a list of variables.
    """
    import re

    with open(file, "r") as f:
        lines = f.readlines()
        regex = re.compile(r'variable "(?P<name>.*)" {')
        terraform_variables = [
            regex.match(line).group("name") for line in lines if regex.match(line)
        ]
        return terraform_variables
