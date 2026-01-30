import argparse
import shutil
from pathlib import Path
import pkg_resources

def create_env_file(project_path: Path):
    """
    Create a .env file in the new project with placeholder values.
    """
    env_content = """# Environment variables for your RAG project
PINECONE_API_KEY=xxxxx
OPENAI_API_KEY=xxxxx
# Add other keys as needed
"""
    env_path = project_path / ".env"
    if not env_path.exists():
        with open(env_path, "w") as f:
            f.write(env_content)
        print("✅ Created .env with placeholder values")
    else:
        print("⚠️ .env already exists — skipping")

def init_project(project_name: str):
    """
    Copy the project skeleton into a new folder, then add .env file.
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

    # Create a .env file with defaults
    create_env_file(target)

def main():
    parser = argparse.ArgumentParser(prog="dj-rag")
    parser.add_argument("command", choices=["init"])
    parser.add_argument("name", help="Name of the project to create")
    args = parser.parse_args()

    if args.command == "init":
        init_project(args.name)
