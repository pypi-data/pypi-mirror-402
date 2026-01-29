import argparse
import os
import json
import shutil
from pathlib import Path
from ..apputils.console import log, console, print_rule

def cmd_plugin(args):
    if args.plugin_cmd == "list":
        return list_plugins()
    elif args.plugin_cmd == "create":
        return create_plugin(args.name)
    else:
        log("Use 'cactuscat plugin --help' for usage info.", style="info")
    return 0

def list_plugins():
    print_rule("CactusCat Plugins")
    plugins_dir = Path("plugins")
    if not plugins_dir.exists():
        log("No plugins directory found.", style="dim")
        return 0
    
    found = False
    for item in plugins_dir.iterdir():
        if item.is_dir():
            manifest = item / "manifest.json"
            if manifest.exists():
                try:
                    data = json.loads(manifest.read_text())
                    name = data.get("name", item.name)
                    version = data.get("version", "unknown")
                    log(f"🧩 [cyan]{name}[/] (v{version}) - {item.name}")
                    found = True
                except:
                    pass
    
    if not found:
        log("No plugins installed.", style="dim")
    return 0

def create_plugin(name):
    print_rule(f"Creating Plugin: {name}")
    plugins_dir = Path("plugins")
    if not plugins_dir.exists():
        plugins_dir.mkdir()
    
    target = plugins_dir / name
    if target.exists():
        log(f"Error: Plugin folder '{name}' already exists.", style="error")
        return 1
    
    target.mkdir()
    
    # Create manifest.json
    manifest = {
        "name": name,
        "version": "0.1.0",
        "description": f"{name} plugin for CactusCat",
        "author": "Developer"
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=4))
    
    # Create main.py
    main_py = """def setup(app):
    print(f"Initializing {name} plugin...")
    
    @app.expose
    def plugin_greet():
        return "Hello from {name} plugin!"
"""
    (target / "main.py").write_text(main_py.format(name=name))
    
    log(f"Plugin '{name}' created at {target}", style="success")
    return 0
