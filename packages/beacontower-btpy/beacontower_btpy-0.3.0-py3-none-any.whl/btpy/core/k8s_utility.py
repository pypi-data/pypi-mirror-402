import json
import shlex
import subprocess


def kubectl(kubeconfig_path, command):
    if isinstance(command, list):
        args = ["kubectl", f"--kubeconfig={kubeconfig_path}"] + command
    else:
        args = ["kubectl", f"--kubeconfig={kubeconfig_path}", *shlex.split(command)]

    # print(args)
    program = subprocess.run(args, capture_output=True, text=True)

    stdout_data = None
    # print(program.stdout)
    # print("-------")
    # print(program.stderr)
    if program.stdout and program.stdout.strip():
        try:
            stdout_data = json.loads(program.stdout)
        except json.JSONDecodeError:
            stdout_data = program.stdout

    return program.returncode, stdout_data, program.stderr


def parallel_pod_curl(
    kubeconfig_path,
    namespace,
    endpoint,
    services=None,
    method="GET",
    body=None,
    port=80,
):
    """
    DO NOT TOUCH THIS FUNCTION. The escaping works. Do not ask why.

    Returns result as a set of lines of the format `<pod_name>|<curl_response>`
    """
    if services:
        services_str = ",".join(services)
        label_selector = f"app.kubernetes.io/name in ({services_str})"
    else:
        label_selector = "beacontower.io/telemetry=true"
    output_format = r'{range .items[*]}{.metadata.name}{"\t"}{.status.podIP}{"\n"}{end}'
    _, output, _ = kubectl(
        kubeconfig_path,
        f"get pods -n {namespace} -l '{label_selector}' -o jsonpath='{output_format}'",
    )

    if not output:
        return {}

    pods = [line.split("\t") for line in output.strip().split("\n") if line]
    ip_to_pod = {pod[1]: pod[0] for pod in pods}
    pod_ips = [pod[1] for pod in pods]
    ips_str = " ".join(pod_ips)
    optional_port_part = f":{port}" if port else ""
    if method == "GET":
        curl_cmd = f"curl -s http://{{}}{optional_port_part}{endpoint}"
    else:
        curl_cmd = f"curl -s -X {method} http://{{}}{optional_port_part}{endpoint}"
        if body:
            curl_cmd += f" -H 'Content-Type: application/json' -d '{body}'"

    inner_cmd = f"printf '%s\\n' {ips_str} | xargs -P 20 -I {{}} sh -c 'echo \"{{}}|$({curl_cmd})\"'"
    cmd = ["exec", "-n", namespace, "deploy/nats-box", "--", "sh", "-c", inner_cmd]

    _, output, stderr = kubectl(kubeconfig_path, cmd)

    responses = {}
    for line in output.strip().split("\n"):
        if "|" in line:
            line_parts = line.split("|", 1)
            ip = line_parts[0].strip()
            json_str = line_parts[1].strip()
            if not ip or not json_str:
                continue
            pod_name = ip_to_pod.get(ip, ip)
            responses[pod_name] = json.loads(json_str)

    return responses
