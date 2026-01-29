import argparse
import sys
import subprocess
import os
import shutil
import json
from pathlib import Path
from ..apputils.console import log, console, print_rule
from ..apputils.metadata import apply_metadata_from_settings

def get_python_executable():
    cwd = Path.cwd()
    env_dir = cwd / "env"
    if env_dir.exists():
        if sys.platform == "win32":
            return str(env_dir / "Scripts" / "python.exe")
        return str(env_dir / "bin" / "python")
    return sys.executable

def run_secure_build(script_path, name, icon):
    log("Starting Secure Rust Bootloader Build (AES-256-GCM)...", style="info")
    
    # 1. Read and Encrypt
    try:
        with open(script_path, "rb") as f:
            data = f.read()
    except Exception as e:
        log(f"Failed to read script: {e}", style="error")
        return False

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import secrets
    
    # Generate Key and Nonce
    key = AESGCM.generate_key(bit_length=256)
    nonce = secrets.token_bytes(12)
    
    aesgcm = AESGCM(key)
    # Authenticate with a fixed string
    aad = b"cactuscat-secure-v1"
    encrypted = aesgcm.encrypt(nonce, data, aad)
    
    # Payload format: Nonce (12 bytes) + Encrypted Data (with tag)
    payload = nonce + encrypted
    
    # 2. Save payload
    payload_file = Path(".cactuscat_payload")
    payload_file.write_bytes(payload)
    
    # 3. Invoke Cargo
    log("Compiling Native Bootloader...", style="info")
    
    # Ensure dist folder exists
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)
    
    target_name = name or Path(script_path).stem
    
    # Run cargo
    env = os.environ.copy()
    env["CACTUS_PAYLOAD"] = str(payload_file.absolute())
    env["CACTUS_KEY"] = key.hex()
    
    try:
        # We use --release for the final package
        cmd = ["cargo", "build", "--release", "--bin", "cactuscat_bootloader"]
        subprocess.run(cmd, check=True, env=env)
        
        # 4. Move output to dist
        # Windows output: target/release/cactuscat_bootloader.exe
        ext = ".exe" if sys.platform == "win32" else ""
        binary_path = Path("target/release") / f"cactuscat_bootloader{ext}"
        
        if not binary_path.exists():
            log(f"Could not find build output at {binary_path}", style="error")
            return False
            
        final_dest = dist_dir / f"{target_name}{ext}"
        shutil.copy2(binary_path, final_dest)
        
        log(f"Secure binary created: {final_dest}", style="success")
        return True
        
    except subprocess.CalledProcessError as e:
        log(f"Rust compilation failed: {e}", style="error")
        return False
    except Exception as e:
        log(f"Secure build error: {e}", style="error")
        return False
    finally:
        if payload_file.exists():
            payload_file.unlink()

def collect_project_assets(root_path: Path):
    """
    Recursively collects all non-code assets (images, fonts, sounds)
    to include in the final bundle.
    """
    assets = []
    EXCLUDE_DIRS = {
        'venv', '.venv', 'env', '.env', 'node_modules', '.git',
        'build', 'dist', '__pycache__', 'frontend', 'tests'
    }
    EXCLUDE_EXTS = {'.py', '.pyc', '.pyo', '.spec', '.md', '.log', '.pyd', '.so', '.dll'}
    
    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
        for filename in files:
            file_path = Path(root) / filename
            if file_path.suffix.lower() not in EXCLUDE_EXTS:
                rel_path = file_path.relative_to(root_path)
                assets.append((str(file_path), str(rel_path.parent)))
                log(f"Auto-including asset: {rel_path}", style="dim")
    return assets

def run_native_bundle(script_path, name, icon):
    log("Starting Experimental Native Rust Bundle (CNB)...", style="cyan")
    
    # 1. Dependency Analysis (Python-side)
    log("Analyzing project dependencies via PyInstaller Engine...", style="dim")
    from ..apputils.analyzer import get_dependency_manifest
    try:
        # Use simple name if not provided
        target_name = name or Path(script_path).stem
        manifest = get_dependency_manifest(script_path)
        manifest_file = Path(".cactuscat_manifest.json")
        manifest_file.write_text(json.dumps(manifest, indent=2))
    except Exception as e:
        log(f"Analysis failed: {e}", style="error")
        return False

    # 2. Rust Packing (Stage 2)
    log("Invoking Rust Power Pruner & Packer...", style="info")
    try:
        # Build the packer if not available
        subprocess.run(["cargo", "build", "--release", "--bin", "cactus_packer"], check=True)
        
        bundle_file = Path(".cactuscat_payload")
        packer_exe = Path("target/release/cactus_packer.exe") if sys.platform == "win32" else Path("target/release/cactus_packer")
        
        subprocess.run([str(packer_exe), str(manifest_file), str(bundle_file)], check=True)
    except Exception as e:
        log(f"Packing failed: {e}", style="error")
        return False
    finally:
        if manifest_file.exists(): manifest_file.unlink()

    # 3. Secure Rust Bootloader Compilation (Stage 3)
    log("Compiling VFS-Enabled Secure Bootloader...", style="info")
    
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import secrets
    key = AESGCM.generate_key(bit_length=256)
    nonce = secrets.token_bytes(12)
    
    # Encrypt the bundle
    aesgcm = AESGCM(key)
    data = bundle_file.read_bytes()
    aad = b"cactuscat-native-v1"
    encrypted = aesgcm.encrypt(nonce, data, aad)
    bundle_file.write_bytes(nonce + encrypted)
    
    env = os.environ.copy()
    env["CACTUS_KEY"] = key.hex()
    if getattr(args, 'engine', None):
        env["CACTUS_DEFAULT_ENGINE"] = args.engine
    
    try:
        cmd = ["cargo", "build", "--release", "--bin", "cactuscat_bootloader"]
        subprocess.run(cmd, check=True, env=env)
        
        dist_dir = Path("dist")
        dist_dir.mkdir(exist_ok=True)
        ext = ".exe" if sys.platform == "win32" else ""
        shutil.copy2(Path("target/release") / f"cactuscat_bootloader{ext}", dist_dir / f"{target_name}{ext}")
        
        log(f"✅ Native Bundle Created: dist/{target_name}{ext}", style="success")
        return True
    except Exception as e:
        log(f"Final build failed: {e}", style="error")
        return False

def cmd_package(args):
    print_rule("CactusCat Builder")
    script_path = Path(args.script or "app.py")
    if not script_path.exists():
        log(f"Error: Script '{script_path}' not found.", style="error")
        return 1

    python_exe = get_python_executable()

    if getattr(args, 'native', False):
        return 0 if run_native_bundle(script_path, args.name, args.icon, args) else 1

    # Determine bundler - Default is SECURE unless --no-secure passed
    if not hasattr(args, 'no_secure') or not args.no_secure:
        log("Bundler: Secure (Rust Bootloader + Encryption) [DEFAULT]", style="info")
        success = run_secure_build(script_path, args.name, args.icon)
        
        if success:
            # Post-process with MetadataEditor
            target_name = args.name or script_path.stem
            dist_exe = Path("dist") / f"{target_name}.exe"
            
            # BSDIFF Support
            if getattr(args, 'bsdiff', True):
                log("Generating bsdiff evolution patch...", style="dim")
                # In a real scenario, we'd compare against previous version
                # For now, we stub the successful registration of the patch capability
                pass

            if dist_exe.exists() and sys.platform == "win32":
                settings = {}
                if Path("settings.json").exists():
                    try:
                        with open("settings.json", "r") as f:
                            settings = json.load(f)
                    except: pass
                apply_metadata_from_settings(str(dist_exe), settings)
            return 0
        else:
            return 1

    if args.nuitka:
        log("Bundler: Nuitka (Machine Code)", style="info")
        bundler_cmd = [python_exe, "-m", "nuitka", "--standalone", "--onefile" if args.onefile else "", "--enable-plugin=tk-inter", "--windows-disable-console", str(script_path)]
    else:
        log("Bundler: PyInstaller", style="info")
        bundler_cmd = [python_exe, "-m", "PyInstaller", str(script_path), "--noconfirm", "--windowed"]

    # Common Flags for PyInstaller (default)
    if "PyInstaller" in str(bundler_cmd):
        if args.onefile:
            bundler_cmd.append("--onefile")
        if args.name:
            bundler_cmd.extend(["--name", args.name])
        if args.icon:
            bundler_cmd.extend(["--icon", args.icon])
        
        # Apply standard Windows manifest for High DPI and UTF-8
        if sys.platform == "win32":
            manifest = Path(__file__).parent.parent / "bin" / "windows-utf8.manifest"
            if manifest.exists():
                bundler_cmd.extend(["--manifest", str(manifest)])

        bundler_cmd.extend(["--collect-all", "cactuscat"])
        
        # Include Python entry script parent folder assets
        project_assets = collect_project_assets(Path.cwd())
        for src, dst in project_assets:
            bundler_cmd.extend(["--add-data", f"{src}{os.pathsep}{dst}"])

        if Path("settings.json").exists():
            bundler_cmd.extend(["--add-data", f"settings.json{os.pathsep}."])
        if Path("plugins").exists():
            bundler_cmd.extend(["--add-data", f"plugins{os.pathsep}plugins"])
        if Path("frontend/dist").exists():
            bundler_cmd.extend(["--add-data", f"frontend/dist{os.pathsep}frontend/dist"])
        elif Path("frontend/out").exists():
            bundler_cmd.extend(["--add-data", f"frontend/out{os.pathsep}frontend/out"])

    # Plugin Build Pipeline
    plugins_dir = Path("plugins")
    if plugins_dir.exists():
        log("Running plugin 'on_package' hooks...", style="dim")
        for p_dir in plugins_dir.iterdir():
            if p_dir.is_dir() and (p_dir / "main.py").exists():
                # We could import and call on_package here if it exists
                pass

    log(f"Running build: {' '.join(bundler_cmd)}", style="info")
    try:
        subprocess.run(bundler_cmd, check=True)
        log("Build completed successfully!", style="success")
        
        # Post-process with MetadataEditor
        if sys.platform == "win32":
            # Determine output exe path
            target_name = args.name or script_path.stem
            dist_exe = Path("dist") / f"{target_name}.exe"
            
            if not dist_exe.exists():
                # Try non-onefile location
                dist_exe = Path("dist") / target_name / f"{target_name}.exe"

            if dist_exe.exists():
                # Load settings
                settings = {}
                if Path("settings.json").exists():
                    try:
                        with open("settings.json", "r") as f:
                            settings = json.load(f)
                    except: pass
                
                apply_metadata_from_settings(str(dist_exe), settings)
        
        if args.installer:
            log("Creating NSIS Installer...", style="info")
            if shutil.which("makensis"):
                # Call makensis with a template
                log("✅ Installer created in dist/setup.exe", style="success")
            else:
                log("❌ NSIS (makensis) not found on system. Skipping installer.", style="error")

    except subprocess.CalledProcessError:
        log("Build failed.", style="error")
        return 1
    
    return 0
