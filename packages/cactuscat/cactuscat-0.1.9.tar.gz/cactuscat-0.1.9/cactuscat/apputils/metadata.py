import os
import subprocess
import shutil
from pathlib import Path
from .console import log

class MetadataEditor:
    """
    Utility for editing executable metadata (Version, Copyright, Icons).
    Primary: Rust-powered metaedit (cross-platform).
    Fallback: rcedit.exe (Windows only).
    """
    def __init__(self, exe_path: str, rcedit_path: str = None):
        self.exe_path = os.path.abspath(exe_path)
        self.rcedit_path = rcedit_path or self._find_rcedit()
        self.use_native = False
        
        try:
            import _metaedit as metaedit
            self.native_editor = metaedit.MetadataEditor(self.exe_path)
            self.use_native = True
        except ImportError:
            self.native_editor = None

    def _find_rcedit(self):
        # Look in cactuscat/bin/rcedit.exe or system path
        base_dir = Path(__file__).parent
        possible_paths = [
            base_dir / "bin" / "rcedit.exe",
            base_dir.parent / "bin" / "rcedit.exe",
            shutil.which("rcedit.exe")
        ]
        
        for p in possible_paths:
            if p and os.path.exists(p):
                return str(p)
        return None

    def set_version(self, version: str):
        if self.use_native:
            self.native_editor.set_version(version)
        else:
            self._run("--set-file-version", version)
            self._run("--set-product-version", version)

    def set_icon(self, icon_path: str):
        if self.use_native:
            self.native_editor.set_icon(icon_path)
        else:
            if os.path.exists(icon_path):
                self._run("--set-icon", icon_path)

    def set_version_string(self, key: str, value: str):
        if self.use_native:
            self.native_editor.set_string(key, value)
        else:
            self._run("--set-version-string", key, value)

    def apply(self):
        """Finalizes the metadata changes."""
        if self.use_native:
            try:
                self.native_editor.apply()
                return True
            except Exception as e:
                log(f"Native metadata update failed: {e}. Falling back to rcedit...", style="warning")
        return True

    def _run(self, *args):
        if not self.rcedit_path:
            log("Warning: rcedit.exe not found. Metadata update skipped.", style="warning")
            return
        
        if not os.path.exists(self.exe_path):
            log(f"Error: Target executable '{self.exe_path}' not found.", style="error")
            return

        cmd = [self.rcedit_path, self.exe_path] + list(args)
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            log(f"Error updating metadata: {e.stderr.decode()}", style="error")

def apply_metadata_from_settings(exe_path, settings):
    """Convenience function to apply settings.json metadata to an executable."""
    editor = MetadataEditor(exe_path)
    
    log(f"Applying metadata to {os.path.basename(exe_path)}...", style="dim")
    
    version = settings.get("version", "1.0.0")
    editor.set_version(version)
    
    editor.set_version_string("CompanyName", settings.get("author", "CactusCat User"))
    editor.set_version_string("FileDescription", settings.get("description", "A CactusCat Application"))
    editor.set_version_string("LegalCopyright", settings.get("copyright", f"Copyright © 2026"))
    editor.set_version_string("ProductName", settings.get("title", "CactusCat App"))
    
    icon = settings.get("icon")
    if icon and os.path.exists(icon):
        editor.set_icon(icon)

    editor.apply()
