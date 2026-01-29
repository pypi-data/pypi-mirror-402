from ..apputils.console import log, print_rule
import sys
import os
from pathlib import Path
from importlib import metadata as importlib_metadata

def generate_nuclear_hooks(output_dir: Path):
    """
    Scans the current Python environment and writes PyInstaller hook files 
    that call `collect_all` for each installed distribution. 
    This is the 'Nuclear Option' to fix missing dependency issues.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    log(f"Initiating Nuclear Hook Generation in {output_dir}...", style="info")

    blacklist = {
        'pyinstaller', 'cactuscat', 'setuptools', 'pip', 'wheel',
        'altgraph', 'pefile', 'pyinstaller-hooks-contrib'
    }

    count = 0
    dists = importlib_metadata.distributions()
    
    for dist in dists:
        name = dist.metadata.get('Name') or getattr(dist, 'name', None)
        if not name or name.lower() in blacklist:
            continue

        safe_name = name.replace('-', '_')
        hook_content = f"""
# Auto-generated nuclear hook for {name} by CactusCat
from PyInstaller.utils.hooks import collect_all

try:
    binaries, hiddenimports, datas = collect_all('{name}')
except Exception:
    binaries, hiddenimports, datas = [], [], []
"""
        hook_file = output_dir / f"hook-{safe_name}.py"
        try:
            hook_file.write_text(hook_content, encoding='utf-8')
            count += 1
        except Exception as e:
            log(f"Warning: failed to write hook for {name}: {e}", style="warning")

    log(f"Generated {count} nuclear hooks. PyInstaller can't miss anything now.", style="success")

def cmd_harvest(args):
    print_rule("CactusCat Library Harvester")
    
    output_path = Path("hooks")
    generate_nuclear_hooks(output_path)
    
    log("✅ Harvest complete. Use '--additional-hooks-dir=hooks' with PyInstaller.", style="success")
    return 0
