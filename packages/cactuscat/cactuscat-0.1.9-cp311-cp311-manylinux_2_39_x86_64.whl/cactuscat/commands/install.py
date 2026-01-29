import argparse
import sys
import subprocess
import venv
import json
from pathlib import Path
from ..apputils.console import log, console, print_rule

REQUIREMENTS_JSON = Path("requirements.json")

def load_requirements() -> dict:
    if REQUIREMENTS_JSON.exists():
        try:
            return json.loads(REQUIREMENTS_JSON.read_text())
        except:
            pass
    return {"dependencies": [], "plugins": []}

def save_requirements(data: dict):
    REQUIREMENTS_JSON.write_text(json.dumps(data, indent=4))

def get_python_executable():
    cwd = Path.cwd()
    env_dir = cwd / "env"
    if env_dir.exists():
        if sys.platform == "win32":
            return str(env_dir / "Scripts" / "python.exe")
        return str(env_dir / "bin" / "python")
    return sys.executable

def cmd_install(args):
    print_rule("CactusCat Installer")
    venv_dir = Path("env")

    if not venv_dir.exists():
        log(f"Creating virtual environment in {venv_dir}...", style="info")
        venv.create(venv_dir, with_pip=True)

    python_exe = get_python_executable()
    req_data = load_requirements()

    if args.packages:
        # Install specific packages
        cmd = [python_exe, "-m", "pip", "install"] + args.packages
        log(f"Installing: {' '.join(args.packages)}", style="info")
        try:
            subprocess.run(cmd, check=True)
            # Update requirements.json
            for p in args.packages:
                if p not in req_data["dependencies"]:
                    req_data["dependencies"].append(p)
            save_requirements(req_data)
            log("Requirements updated.", style="success")
        except subprocess.CalledProcessError:
            log("Installation failed.", style="error")
            return 1
    else:
        # Install from requirements.json
        deps = req_data.get("dependencies", [])
        if deps:
            cmd = [python_exe, "-m", "pip", "install"] + deps
            log("Installing dependencies from requirements.json...", style="info")
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError:
                log("Installation failed.", style="error")
                return 1
        else:
            log("No dependencies to install.", style="dim")
    
    return 0
