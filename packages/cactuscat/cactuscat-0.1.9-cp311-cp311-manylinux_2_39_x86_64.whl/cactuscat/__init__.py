from .application import App, App as Application
from .apputils.state import ReactiveState
from .apputils.console import log, console
from .menu import Menu, MenuBar
from .apputils.metadata import MetadataEditor
import os
import sys
import io

# --- UTF-8 Hook (Experimental) ---
def _apply_utf8_hook():
    """Ensure stdout/stderr use UTF-8 on Windows to avoid encoding errors."""
    if sys.platform != "win32":
        return
        
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='surrogatepass')
            sys.stderr.reconfigure(encoding='utf-8', errors='surrogatepass')
        except:
            pass
    elif hasattr(sys.stdout, "buffer"):
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='surrogatepass')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='surrogatepass')
        except:
            pass

if not "pytest" in sys.modules:
    _apply_utf8_hook()

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for bundled apps.
    """
    if os.path.isabs(relative_path):
        return relative_path
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)

__all__ = ["App", "log", "console", "Menu", "MenuBar", "get_resource_path"]
