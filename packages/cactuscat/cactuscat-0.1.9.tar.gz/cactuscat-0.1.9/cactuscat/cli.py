import argparse
import sys
from .commands.init import init_project
from .commands.run import cmd_run
from .commands.doctor import cmd_doctor
from .commands.install import cmd_install
from .commands.package import cmd_package
from .commands.plugin import cmd_plugin
from .commands.android import cmd_android
from .commands.harvest import cmd_harvest
from .commands.ts_gen import cmd_ts_gen
from .commands.workflow import cmd_workflow
from .commands.engine import cmd_engine

def main():
    parser = argparse.ArgumentParser(description="CactusCat CLI - The powerful Python/Rust hybrid framework")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize a new CactusCat project")
    init_parser.add_argument("name", help="Name of the project (or '.' for current dir)")
    init_parser.add_argument("--template", default="vanilla", help="Frontend template (vanilla, react, vue, svelte, next)")

    # run command
    run_parser = subparsers.add_parser("run", help="Run a CactusCat application")
    run_parser.add_argument("script", nargs="?", default="app.py", help="Python script to run (default: app.py)")
    run_parser.add_argument("--dev", action="store_true", help="Enable hot-reload and frontend dev server orchestration")
    run_parser.add_argument("--no-build", action="store_true", help="Skip frontend build")
    run_parser.add_argument("--engine", help="Force a specific web engine (native, edge, webkit)")
    run_parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Arguments passed to the app")

    # install command
    install_parser = subparsers.add_parser("install", help="Install project dependencies")
    install_parser.add_argument("packages", nargs="*", help="Specific packages to install and save")
    install_parser.add_argument("--plugin", action="store_true", help="Install a CactusCat plugin")

    # package command
    package_parser = subparsers.add_parser("package", help="Bundle app into an executable")
    package_parser.add_argument("script", nargs="?", default="app.py", help="Script to package")
    package_parser.add_argument("--name", help="Output executable name")
    package_parser.add_argument("--icon", help="Path to icon file")
    package_parser.add_argument("--onefile", action="store_true", help="Bundle into a single file")
    package_parser.add_argument("--nuitka", action="store_true", help="Use Nuitka for compilation (machine code)")
    package_parser.add_argument("--no-secure", action="store_true", help="Disable secure Rust bootloader (use standard bundler)")
    package_parser.add_argument("--installer", action="store_true", help="Create a native installer (NSIS)")
    package_parser.add_argument("--native", action="store_true", help="Experimental Native Bundle (CNB) - Uses Rust VFS")
    package_parser.add_argument("--bsdiff", action="store_true", default=True, help="Generate bsdiff patches for binary evolution (default: True)")

    # plugin command
    plugin_parser = subparsers.add_parser("plugin", help="Manage plugins")
    plugin_sub = plugin_parser.add_subparsers(dest="plugin_cmd")
    plugin_sub.add_parser("list", help="List installed plugins")
    plugin_create = plugin_sub.add_parser("create", help="Create a new plugin template")
    plugin_create.add_argument("name", help="Plugin name")
    plugin_parser.add_argument("packages", nargs="*", help="Args for subcommands")

    # engine command
    engine_parser = subparsers.add_parser("engine", help="Manage browser engines (native, chrome, etc.)")
    engine_sub = engine_parser.add_subparsers(dest="engine_cmd")
    engine_install = engine_sub.add_parser("install", help="Install a browser engine")
    engine_install.add_argument("name", help="Engine name (e.g., chrome)")
    engine_sub.add_parser("list", help="List available engines")

    # android command
    android_parser = subparsers.add_parser("android", help="Android development pipeline")
    android_sub = android_parser.add_subparsers(dest="android_cmd")
    android_sub.add_parser("init", help="Scaffold Android project")
    android_sub.add_parser("sync", help="Sync assets with Android project")
    android_sub.add_parser("build", help="Build Android APK")
    android_sub.add_parser("run", help="Run on Android device")
    android_sub.add_parser("logcat", help="Stream Android logs")

    # ts-gen command
    ts_parser = subparsers.add_parser("ts-gen", help="Generate TypeScript definitions for your app")
    ts_parser.add_argument("script", nargs="?", default="app.py", help="Script to scan")
    ts_parser.add_argument("--output", help="Output file path")

    # harvest command
    subparsers.add_parser("harvest", help="Nuclear dependency scraper (Fixes missing library errors)")

    # workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Execute agentic workflows")
    workflow_parser.add_argument("name", nargs="?", help="Name of the workflow to run")

    # doctor command
    subparsers.add_parser("doctor", help="Check system requirements and health")

    args = parser.parse_args()

    if args.command == "init":
        sys.exit(init_project(args) or 0)
    elif args.command == "run":
        sys.exit(cmd_run(args) or 0)
    elif args.command == "install":
        sys.exit(cmd_install(args) or 0)
    elif args.command == "package":
        sys.exit(cmd_package(args) or 0)
    elif args.command == "plugin":
        sys.exit(cmd_plugin(args) or 0)
    elif args.command == "android":
        sys.exit(cmd_android(args) or 0)
    elif args.command == "ts-gen":
        sys.exit(cmd_ts_gen(args) or 0)
    elif args.command == "harvest":
        sys.exit(cmd_harvest(args) or 0)
    elif args.command == "workflow":
        sys.exit(cmd_workflow(args) or 0)
    elif args.command == "doctor":
        sys.exit(cmd_doctor() or 0)
    elif args.command == "engine":
        sys.exit(cmd_engine(args) or 0)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
