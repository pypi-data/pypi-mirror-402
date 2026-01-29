import argparse
import sys
import shutil
import subprocess
import json
import os
import re
import threading
from pathlib import Path
from ..apputils.console import log, console
from rich.text import Text

try:
    from watchfiles import watch, DefaultFilter
except ImportError:
    DefaultFilter = object

class CactusFilter(DefaultFilter):
    def __init__(self, frontend_dir: Path = None, **kwargs):
        self.frontend_dir = frontend_dir.resolve() if frontend_dir else None
        self.ignore_dirs = {
            ".git", "__pycache__", "node_modules", "dist", "build", 
            ".next", ".output", "coverage", "env", "venv", "cactuscat"
        }
        super().__init__(**kwargs)

    def __call__(self, change, path):
        path_obj = Path(path).resolve()
        if any(part in self.ignore_dirs for part in path_obj.parts):
            return False
        if self.frontend_dir:
            try:
                if self.frontend_dir in path_obj.parents or self.frontend_dir == path_obj:
                    rel = path_obj.relative_to(self.frontend_dir)
                    if any(str(rel).startswith(p) for p in ["src", "public", "assets", "node_modules"]):
                        return False
            except ValueError: pass
        return super().__call__(change, path)

def get_python_executable():
    cwd = Path.cwd()
    env_dir = cwd / "env"
    if env_dir.exists():
        if sys.platform == "win32":
            python_exe = env_dir / "Scripts" / "python.exe"
        else:
            python_exe = env_dir / "bin" / "python"
        if python_exe.exists():
            return str(python_exe)
    return sys.executable

def run_dev_mode(script: Path, args) -> int:
    extra_args = args.extra_args or []
    try:
        from watchfiles import watch
    except ImportError:
        log("watchfiles is required for --dev mode. Install it with: pip install watchfiles", style="error")
        return 1

    frontend_dir = Path("frontend")
    watcher_filter = CactusFilter(frontend_dir=frontend_dir if frontend_dir.exists() else None)

    npm_proc = None
    dev_server_url = None

    if frontend_dir.exists():
        log("Checking for frontend dev server...", style="info")
        pkg_path = frontend_dir / "package.json"
        if pkg_path.exists():
            pkg_data = json.loads(pkg_path.read_text())
            scripts = pkg_data.get("scripts", {})
            if "dev" in scripts:
                log("Starting Vite dev server...", style="success")
                proc_env = os.environ.copy()
                proc_env["FORCE_COLOR"] = "1"
                
                npm_proc = subprocess.Popen(
                    ["npm", "run", "dev"],
                    cwd=str(frontend_dir),
                    shell=(sys.platform == "win32"),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=proc_env,
                    text=True,
                    bufsize=1,
                )

                url_found_event = threading.Event()
                def scan_output():
                    nonlocal dev_server_url
                    url_regex = re.compile(r"http://localhost:\d+")
                    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
                    while npm_proc and npm_proc.poll() is None:
                        line = npm_proc.stdout.readline()
                        if not line: break
                        clean_line = ansi_escape.sub("", line)
                        console.print(Text(f"[npm] ", style="dim") + Text.from_ansi(line.strip()))
                        if not dev_server_url:
                            match = url_regex.search(clean_line)
                            if match:
                                dev_server_url = match.group(0)
                                log(f"Frontend ready at {dev_server_url}", style="success")
                                url_found_event.set()
                
                threading.Thread(target=scan_output, daemon=True).start()
                url_found_event.wait(timeout=10)

    app_proc = None

    def kill_app():
        nonlocal app_proc
        if app_proc:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(app_proc.pid)], capture_output=True)
            else:
                app_proc.terminate()
            app_proc = None

    def start_app():
        nonlocal app_proc
        kill_app()
        log("Starting Python app...", style="info")
        python_exe = get_python_executable()
        env = os.environ.copy()
        if dev_server_url:
            env["CACTUS_DEV_URL"] = dev_server_url
        if getattr(args, "engine", None):
            env["CACTUS_ENGINE"] = args.engine
        app_proc = subprocess.Popen([python_exe, str(script)] + extra_args, env=env)

    try:
        start_app()
        log(f"Watching for changes in {Path.cwd()}...", style="success")
        for changes in watch(str(Path.cwd()), watch_filter=watcher_filter):
            log("Restarting due to changes...", style="dim")
            start_app()
    except KeyboardInterrupt: pass
    finally:
        kill_app()
        if npm_proc:
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(npm_proc.pid)], capture_output=True)
            else:
                npm_proc.terminate()
    return 0

def cmd_run(args):
    script_path = args.script or "app.py"
    path = Path(script_path)
    if not path.exists():
        log(f"Error: Script '{script_path}' not found.", style="error")
        return 1

    if args.dev:
        return run_dev_mode(path, args)

    # Production run
    python_exe = get_python_executable()
    env = os.environ.copy()
    if args.engine:
        env["CACTUS_ENGINE"] = args.engine
    
    cmd = [python_exe, str(path)] + (args.extra_args or [])
    log(f"Running engine: {args.engine or 'native'}", style="info")
    log(f"Command: {' '.join(cmd)}", style="dim")
    return subprocess.call(cmd, env=env)
