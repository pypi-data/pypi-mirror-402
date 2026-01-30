import argparse
import shutil
from pathlib import Path
import pkg_resources

def init_project(project_name: str):
    """
    Copy the project skeleton into a new folder.
    """
    target = Path.cwd() / project_name
    template_dir = pkg_resources.resource_filename(
        "dj_rag_pipeline", "templates/project_skeleton"
    )

    if target.exists():
        print(f"❌ Error: '{project_name}' already exists!")
        return

    shutil.copytree(template_dir, target)
    print(f"✅ Project '{project_name}' created at {target}")

def main():
    parser = argparse.ArgumentParser(prog="dj-rag")
    parser.add_argument("command", choices=["init"])
    parser.add_argument("name", help="Name of the project to create")
    args = parser.parse_args()

    if args.command == "init":
        init_project(args.name)

