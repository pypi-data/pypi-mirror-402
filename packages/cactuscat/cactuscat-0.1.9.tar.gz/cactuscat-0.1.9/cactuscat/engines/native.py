from .. import _cactuscat
import json

class NativeEngine:
    def __init__(self, app):
        self.app = app
        self.handle = None

    def start(self, title, url, on_ready, on_msg, **kwargs):
        _cactuscat.start_engine(
            title,
            url,
            on_ready,
            on_msg,
            kwargs.get("asset_root"),
            kwargs.get("initialization_script"),
            kwargs.get("frameless", False),
            kwargs.get("resizable", True),
            kwargs.get("always_on_top", False),
            kwargs.get("maximized", False),
            kwargs.get("transparent", False),
            kwargs.get("splash_html"),
            kwargs.get("splash_width", 400),
            kwargs.get("splash_height", 300),
            kwargs.get("fullscreen", False)
        )

    def eval(self, script):
        if self.handle:
            self.handle.eval(script)
