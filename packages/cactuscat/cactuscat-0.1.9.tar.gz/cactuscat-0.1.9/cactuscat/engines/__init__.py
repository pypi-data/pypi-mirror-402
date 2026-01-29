from .native import NativeEngine

def get_engine(name, app):
    name = (name or "native").lower()
    if name == "native":
        return NativeEngine(app)
    elif name == "chrome" or name == "electron":
        try:
            from .chrome import ChromeEngine
            return ChromeEngine(app)
        except ImportError:
            raise ImportError("Chrome engine dependencies are missing. Run 'cactuscat engine build chrome' first.")
    else:
        raise ValueError(f"Unknown engine: {name}")
