from typing import Callable, Dict

class ShortcutManager:
    def __init__(self, app):
        self.app = app
        self.shortcuts: Dict[int, Callable] = {}

    def register(self, accelerator: str, callback: Callable):
        """
        Registers a global shortcut.
        Example: 'Ctrl+Shift+F12'
        """
        # We need a numeric ID for the shortcut. 
        # A simple way is to hash the accelerator string or use a counter.
        # But wait, Tao uses Accelerator::from_str which presumably has its own hash.
        # Actually, let's just use a hash for mapping back.
        import hashlib
        # Tao's GlobalShortcut ID is a hash of the accelerator.
        # We should probably just send the string and let Rust handle it, 
        # and Rust sends back the ID which is hash(accel).
        
        # For simplicity, let's just store by accelerator string if we can.
        # But Rust sends back id.0 which is a primitive.
        
        if self.app.handle:
            self.app.handle.register_shortcut(accelerator)
            # We don't know the exact ID Tao will generate unless we replicate it, 
            # but usually it's a predictable hash.
            # Let's just track them.
            self.shortcuts[accelerator] = callback
        else:
             # Queue for when app is ready?
             pass

    def _handle_shortcut(self, shortcut_id: int):
        # This is the tricky part: Tao's ID is internal.
        # We might need to send the ID back from Rust when registering?
        # Or just pass the callback to App.
        pass
