import sys
import os
import subprocess
import shutil
from pathlib import Path
from ..apputils.console import log, console, print_rule

def check_command(cmd, name):
    path = shutil.which(cmd)
    if path:
        log(f"✅ [green]{name}[/]: Found at {path}")
        return True
    else:
        log(f"❌ [red]{name}[/]: Not found ({cmd})")
        return False

def cmd_doctor():
    print_rule("CactusCat Doctor - System Diagnostics")
    
    # 1. Python Check
    log(f"🐍 Python Version: {sys.version.split()[0]} ({'64-bit' if sys.maxsize > 2**32 else '32-bit'})")
    log(f"📍 Execution Path: {sys.executable}")
    
    # 2. Rust Check
    check_command("cargo", "Rust (Cargo)")
    
    # 3. Frontend Tools
    log("\n[bold]Frontend Stack:[/]")
    check_command("node", "Node.js")
    check_command("npm", "NPM")
    check_command("yarn", "Yarn")
    check_command("pnpm", "PNPM")
    check_command("bun", "Bun")
    
    # 4. Packaging Tools
    log("\n[bold]Packaging & Windows Tools:[/]")
    check_command("pyinstaller", "PyInstaller")
    check_command("nuitka", "Nuitka")
    check_command("rcedit", "rcedit (Metadata Editor)")
    check_command("makensis", "NSIS (makensis)")
    check_command("signtool", "Windows SignTool")

    # 5. Android Development
    log("\n[bold]Android Development:[/]")
    check_command("adb", "ADB (Android Debug Bridge)")
    log(f"🤖 ANDROID_HOME: {os.environ.get('ANDROID_HOME', 'Not Set')}")
    log(f"☕ JAVA_HOME: {os.environ.get('JAVA_HOME', 'Not Set')}")

    # 6. CactusCat Core Check
    log("\n[bold]CactusCat Integrity:[/]")
    try:
        from .. import _cactuscat
        log("✅ CactusCat Native Engine: Loaded successfully")
    except ImportError as e:
        log(f"❌ CactusCat Native Engine: Failed to load ({e})", style="error")
        log("Tip: Run 'pip install -e .' in the cactuscat root directory.")

    # 6. Environment Check
    if Path("env").exists():
        log("✅ Local environment (env/) detected.")
        python_exe = get_python_executable()
        log(f"📍 Local Python: {python_exe}", style="dim")
    else:
        log("ℹ️ No local environment detected. You might be using a global python.")

    # 7. Project Check
    if Path("settings.json").exists():
        log("✅ Project settings.json found.")
    else:
        log("ℹ️ Not in a valid CactusCat project directory (settings.json missing).", style="dim")

    return 0

def get_python_executable():
    cwd = Path.cwd()
    env_dir = cwd / "env"
    if env_dir.exists():
        if sys.platform == "win32":
            return str(env_dir / "Scripts" / "python.exe")
        return str(env_dir / "bin" / "python")
    return sys.executable
