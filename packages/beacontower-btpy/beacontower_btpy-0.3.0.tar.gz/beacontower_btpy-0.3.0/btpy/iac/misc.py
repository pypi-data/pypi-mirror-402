import json
import logging
import os
import pathlib
import shutil
import tempfile

from btpy.az import az


def get_connection_string():
    """Get the connection string."""

    logger = setup_logging()
    conn_str = os.getenv("DEPLOYMENT_DATA_CONNECTION_STRING")
    if conn_str:
        return conn_str
    else:
        exit_code, result_dict, logs = az(
            'keyvault secret show --name "deployment-data-connection-string" --vault-name "btdeploymentdata" --subscription "bf222aeb-b358-4dc5-b2a3-07503773a0e3" --query "value"'
        )
        if exit_code != 0:
            logger.error(logs)
            exit(1)
        os.putenv("DEPLOYMENT_DATA_CONNECTION_STRING", result_dict)
        return result_dict


def setup_logging():
    """Setup logging."""
    log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
    logger = logging.getLogger("btpy")
    logger.setLevel(log_level)
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def find_file_in_parent_directories(filename):
    """Find a file in the current directory or any parent directory."""
    current_directory = pathlib.Path(os.path.curdir).absolute()
    while True:
        locate_path = os.path.join(current_directory, filename)
        if os.path.exists(locate_path):
            return locate_path
        parent_directory = os.path.dirname(current_directory)
        if parent_directory == current_directory:
            raise FileNotFoundError(
                f"Could not find {filename} in any parent directory"
            )
        current_directory = parent_directory


def get_directory_of_file(filename):
    """Get the directory of a file."""
    return os.path.dirname(pathlib.Path(filename).absolute())


def write_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f)


def create_local_temp_directory():
    """Create a local temp directory."""
    return tempfile.mkdtemp()


def remove_local_temp_directory(directory):
    """Remove a local temp directory."""
    shutil.rmtree(directory)


def sync_tfoutput_to_blob(tfname, tfoutput, data, datestamp):
    """Sync tfoutput to blob."""
    tmp_dir = create_local_temp_directory()
    cleaned_tfoutput = {k: v["value"] for k, v in tfoutput.items()}
    fname = os.path.join(tmp_dir, "output.json")
    with open(fname, "w") as f:
        f.write(json.dumps(cleaned_tfoutput, indent=4))
    latest_bloburl = f"{data['deployment_data']}/{data['application']}/{data['environment']}/{data['shloc']}{data['stamp']}/@latest/{tfname}.json"
    datestamp_bloburl = f"{data['deployment_data']}/{data['application']}/{data['environment']}/{data['shloc']}{data['stamp']}/{datestamp}/{tfname}.json"
    connection_string = get_connection_string()
    az(
        f"storage blob upload --overwrite --connection-string {connection_string} --blob-url {latest_bloburl} --file {fname}"
    )
    az(
        f"storage blob upload --overwrite --connection-string {connection_string} --blob-url {datestamp_bloburl} --file {fname}"
    )
    # print(
    #     f"storage blob upload --overwrite --connection-string {connection_string} --blob-url {latest_bloburl} --file {fname}"
    # )
    # print(
    #     f"storage blob upload --overwrite --connection-string {connection_string} --blob-url {datestamp_bloburl} --file {fname}"
    # )
    remove_local_temp_directory(tmp_dir)


def sync_env_to_blob(tfname, data, datestamp):
    """Sync tfoutput to blob."""
    tmp_dir = create_local_temp_directory()
    fname = os.path.join(tmp_dir, "output.json")
    with open(fname, "w") as f:
        f.write(json.dumps(data, indent=4))
    latest_bloburl = f"{data['deployment_data']}/{data['application']}/{data['environment']}/{data['shloc']}{data['stamp']}/@latest/{tfname}-environment-data.json"
    datestamp_bloburl = f"{data['deployment_data']}/{data['application']}/{data['environment']}/{data['shloc']}{data['stamp']}/{datestamp}/{tfname}-environment-data.json"
    connection_string = get_connection_string()
    az(
        f"storage blob upload --overwrite --connection-string {connection_string} --blob-url {latest_bloburl} --file {fname}"
    )
    az(
        f"storage blob upload --overwrite --connection-string {connection_string} --blob-url {datestamp_bloburl} --file {fname}"
    )
    # print(
    #     f"storage blob upload --overwrite --connection-string {connection_string} --blob-url {latest_bloburl} --file {fname}"
    # )
    # print(
    #     f"storage blob upload --overwrite --connection-string {connection_string} --blob-url {datestamp_bloburl} --file {fname}"
    # )
    remove_local_temp_directory(tmp_dir)
