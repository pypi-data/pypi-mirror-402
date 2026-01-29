import sys
import os
import subprocess
import platform
import webbrowser

def open_external(url):
    """Opens a URL or file in the system default browser/app."""
    webbrowser.open(url)

def copy_to_clipboard(text):
    """Copies text to the system clipboard."""
    if platform.system() == "Windows":
        try:
            import ctypes
            cf_unicode_text = 13
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            if user32.OpenClipboard(None):
                user32.EmptyClipboard()
                h_data = kernel32.GlobalAlloc(0x0042, (len(text) + 1) * 2)
                p_data = kernel32.GlobalLock(h_data)
                ctypes.memmove(p_data, text, len(text) * 2)
                kernel32.GlobalUnlock(h_data)
                user32.SetClipboardData(cf_unicode_text, h_data)
                user32.CloseClipboard()
                return True
        except: pass
    return False

def set_start_on_boot(app_name, enable=True):
    """Configures the app to launch on system startup (Windows only for now)."""
    if platform.system() == "Windows":
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            if enable:
                exe_path = f'"{sys.executable}"'
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
            else:
                try: winreg.DeleteValue(key, app_name)
                except FileNotFoundError: pass
            winreg.CloseKey(key)
            return True
        except: pass
    return False

def show_item_in_folder(path):
    """Opens the folder containing the item and selects it."""
    path = os.path.abspath(path)
    if platform.system() == "Windows":
        subprocess.run(["explorer", "/select,", path])
    elif platform.system() == "Darwin":
        subprocess.run(["open", "-R", path])
    else:
        # On Linux, we just open the directory for now
        subprocess.run(["xdg-open", os.path.dirname(path)])

def get_system_info():
    """Returns basic system information."""
    return {
        "os": platform.system(),
        "release": platform.release(),
        "arch": platform.machine(),
        "python": platform.python_version()
    }
