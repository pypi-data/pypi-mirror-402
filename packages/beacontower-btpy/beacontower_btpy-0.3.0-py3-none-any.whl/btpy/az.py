import json
import platform
import shlex
import subprocess


def az(command: str, subscription_id: str = None):
    args = ["az", *shlex.split(command), "--output", "json"]

    if subscription_id:
        args.extend(["--subscription", subscription_id])

    program = subprocess.run(
        args, capture_output=True, text=True, shell=(platform.system() == "Windows")
    )

    stdout_data = None
    if program.stdout and program.stdout.strip():
        try:
            stdout_data = json.loads(program.stdout)
        except json.JSONDecodeError:
            stdout_data = program.stdout

    return program.returncode, stdout_data, program.stderr
