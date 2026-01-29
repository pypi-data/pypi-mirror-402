import sys
import os
import json
from pathlib import Path
from PyInstaller.building.build_main import Analysis

def get_dependency_manifest(script_path, pathex=None, hiddenimports=None):
    """
    Uses PyInstaller's Analysis engine to find all dependencies.
    Returns a dict with 'scripts', 'binaries', 'zipfiles', and 'datas'.
    """
    if pathex is None: pathex = []
    if hiddenimports is None: hiddenimports = []
    
    # We create a dummy build folder
    base_dir = Path(script_path).parent
    workpath = base_dir / "build" / "analysis_temp"
    workpath.mkdir(parents=True, exist_ok=True)
    
    analysis = Analysis(
        [str(script_path)],
        pathex=pathex,
        binaries=[],
        datas=[],
        hiddenimports=hiddenimports,
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=None,
        noarchive=False,
    )
    
    manifest = {
        "scripts": [],
        "binaries": [],
        "zipfiles": [],
        "datas": []
    }
    
    for item in analysis.scripts:
        manifest["scripts"].append({"name": item[0], "path": item[1], "type": item[2]})
    
    for item in analysis.binaries:
        manifest["binaries"].append({"name": item[0], "path": item[1], "type": item[2]})

    for item in analysis.datas:
        manifest["datas"].append({"name": item[0], "path": item[1], "type": item[2]})
        
    return manifest

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <script_path>")
        sys.exit(1)
        
    script = sys.argv[1]
    manifest = get_dependency_manifest(script)
    print(json.dumps(manifest, indent=2))
