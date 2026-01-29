import json

class ReactiveState(dict):
    """
    A dictionary that syncs its changes to the frontend via IPC.
    Supports dot access (app.state.count = 1).
    """
    def __init__(self, app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app
        self._suppress_sync = False # Flag to prevent infinite loops when updating from JS
        
    def __getattr__(self, key):
        # Allow dot access for getting values (app.state.key)
        try:
            return self[key]
        except KeyError:
            if key.startswith("_"):
                return super().__getattribute__(key)
            return None 

    def __setattr__(self, key, value):
        # Allow dot access for setting values
        if key.startswith("_"):
             super().__setattr__(key, value)
        else:
             self[key] = value # Redirects to __setitem__

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if not self._suppress_sync:
            self._sync(key, value)
        
    def __delitem__(self, key):
        super().__delitem__(key)
        if not self._suppress_sync:
            self._sync(key, None, deleted=True)

    def set(self, key, value):
        """Explicitly set a value and sync."""
        self[key] = value

    def get(self, key, default=None):
        """Explicitly get a value."""
        return super().get(key, default)
        
    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        if not self._suppress_sync:
            if args and isinstance(args[0], dict):
                for k, v in args[0].items(): self._sync(k, v)
            for k, v in kwargs.items(): self._sync(k, v)

    def _sync(self, key, value, deleted=False):
        if self._app and self._app.handle:
            payload = {
                "key": key,
                "value": value,
                "deleted": deleted
            }
            json_payload = json.dumps(payload)
            script = f"window.dispatchEvent(new CustomEvent('ccat:state-update', {{ detail: {json_payload} }}));"
            self._app.eval(script)
            
    def _internal_set(self, key, value):
        """Set value without broadcasting change (used when receiving update from JS)"""
        self._suppress_sync = True
        try:
            self[key] = value
        finally:
            self._suppress_sync = False
