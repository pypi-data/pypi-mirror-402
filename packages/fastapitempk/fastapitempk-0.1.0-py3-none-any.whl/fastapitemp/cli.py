import shutil
import sys
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print("Usage: fastapitempk create <project_name>")
        return

    command = sys.argv[1]
    project_name = sys.argv[2]

    if command != "create":
        print("Unknown command")
        return

    template_dir = Path(__file__).parent / "template"
    target_dir = Path.cwd() / project_name

    shutil.copytree(template_dir, target_dir)
    print(f"✅ FastAPI project '{project_name}' created")
