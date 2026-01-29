import os
import sys
import hashlib
import json
import logging
import subprocess
import bsdiff4
from typing import Optional, Dict

logger = logging.getLogger("CactusCat.Evolution")

class Evolution:
    """
    Handles automatic updates and binary 'Evolution' (patching).
    Designed to update secure binaries with minimal delta downloads.
    """
    def __init__(self, current_version: str, update_url: str):
        self.current_version = current_version
        self.update_url = update_url
        self.update_info: Dict = {}

    def check_for_updates(self) -> bool:
        """Checks if a new version is available."""
        # In a real app, this would fetch from self.update_url
        # For now, we simulate the 'Evolution' logic
        logger.info(f"Checking updates at {self.update_url}...")
        return False

    def apply_patch(self, patch_path: str, target_path: str):
        """
        Applies a binary patch (bsdiff) to the current executable.
        """
        logger.info(f"Applying evolution patch: {patch_path}")
        
        if not bsdiff4:
            logger.error("bsdiff4 not installed. Cannot apply binary patch.")
            return False

        try:
            # We usually patch the executable itself, but on Windows 
            # we need to patch a copy and then move it on next boot.
            temp_path = target_path + ".new"
            with open(target_path, "rb") as old, open(patch_path, "rb") as patch, open(temp_path, "wb") as new:
                new_data = bsdiff4.patch(old.read(), patch.read())
                new.write(new_data)
            
            logger.info(f"Patch applied successfully to {temp_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply bsdiff patch: {e}")
            return False

    def get_binary_hash(self, path: Optional[str] = None) -> str:
        """Returns the SHA256 hash of the current executable."""
        if not path:
            path = sys.executable
        
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def run_installer(self, path: str):
        """Launches an NSIS or MSI installer correctly."""
        logger.info(f"Launching installer: {path}")
        if sys.platform == "win32":
            os.startfile(path)
            sys.exit(0)
        else:
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", path])
            sys.exit(0)
