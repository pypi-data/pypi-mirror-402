import os
import subprocess
import tempfile
import venv

from rich import print

from btpy.core.azure_utility import get_blob_client, get_blob_container_client
from btpy.core.envs.env_desc import EnvDesc
from btpy.core.migrations.migration_loader import MIGRATIONS_CONTAINER_NAME


async def run_migration(env_desc: EnvDesc, migration: dict):
    # TODO: Verify that migration files exist

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            _create_venv(temp_dir)
            await _download_migration_files(migration, temp_dir)
            _install_requirements(temp_dir)
            _execute_migration_python_files(temp_dir)

            # TODO: Handle output and errors in a good way

            return True
        except Exception as e:
            print(e)
            return False


async def _download_migration_files(migration: dict, temp_dir: str):
    print("[blue]Downloading migration files...", end=" ")

    try:
        migration_file_blob_it = get_blob_container_client(
            MIGRATIONS_CONTAINER_NAME
        ).list_blobs(name_starts_with=f"{migration['id']}/")

        for migration_file_blob_entry in migration_file_blob_it:
            migration_file_blob = get_blob_client(
                MIGRATIONS_CONTAINER_NAME, migration_file_blob_entry.name
            )
            migration_file_content = migration_file_blob.download_blob().readall()
            migration_file_path = os.path.join(
                temp_dir, os.path.basename(migration_file_blob_entry.name)
            )

            with open(migration_file_path, "w") as migration_file:
                migration_file.write(migration_file_content.decode("utf-8"))

        print("[green]Done")
    except Exception as e:
        print(f"[red]Failed ({e})")
        return None


def _create_venv(temp_dir: str) -> str:
    print("[blue]Creating venv...", end=" ")

    try:
        venv_dir = os.path.join(temp_dir, ".venv")
        venv.create(venv_dir, with_pip=True)

        # with_pip failed every time earlier, so I went with this
        # python_bin = os.path.join(venv_dir, "Scripts", "python")
        # subprocess.check_call([python_bin, "-m", "ensurepip", "--upgrade", "--default-pip"])

        print("[green]Done")
        return venv_dir
    except Exception as e:
        print(f"[red]Failed ({e})")
        raise


def _install_requirements(temp_dir: str):
    requirements_file = os.path.join(temp_dir, "requirements.txt")

    if not os.path.exists(requirements_file):
        return

    print("[blue]Installing requirements...", end=" ")

    result = subprocess.run(
        ["pip", "install", "-r", requirements_file], capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"[red]Failed ({result.stderr})")
        return

    print("[green]Done")


def _execute_migration_python_files(temp_dir: str):
    print("[blue]Executing python file...", end=" ")

    entry_point_file = os.path.join(temp_dir, "main.py")
    result = subprocess.run(
        ["python", entry_point_file], capture_output=True, text=True
    )
    # result = subprocess.run(["python", entry_point_file])

    if result.returncode != 0:
        # print(f"[red]Failed ({result.stderr})")
        print("[red]Failed")
        return

    print("[green]Done")
