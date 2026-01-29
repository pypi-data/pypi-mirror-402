import sys
from pathlib import Path

import chevron
from rich import print


def to_absolute_path(current_file, relative_path: str) -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # noinspection PyProtectedMember
        script_dir = Path(sys._MEIPASS)
    else:
        script_dir = Path(current_file).parent

    return script_dir / relative_path


def generate_file_from_template(template_filename, out_filename, data):
    print(f"[blue]Generating file {out_filename}...", end=" ")
    with open(template_filename, "r") as template_file:
        generated_content = chevron.render(template_file, data)

    with open(out_filename, "w") as file:
        file.write(generated_content)

    print("[green]Complete")
