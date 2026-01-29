import json
import logging
import os
import sys
from . import _cactuscat
from .apputils.state import ReactiveState
from .plugins import PluginManager
from .menu import MenuBar, Menu
from .apputils.serializer import cactus_serialize, CactusJSONEncoder
from .router import Router
from .inspector import Inspector
from .apputils.updater import Evolution
from .apputils.guard import ProcessGuard
from .apputils import shell
from .engines import get_engine

class EventBus:
    def __init__(self):
        self._listeners = {}

    def on(self, event, callback=None):
        def decorator(func):
            if event not in self._listeners:
                self._listeners[event] = []
            self._listeners[event].append(func)
            return func
        
        if callback:
            return decorator(callback)
        return decorator

    def on_exit(self, callback):
        """Register a callback to run when the app exits."""
        return self.on("exit", callback)

    def emit(self, event, data=None):
        if event in self._listeners:
            for cb in self._listeners[event]:
                cb(data)

class DialogManager:
    def __init__(self, app):
        self._app = app
    
    def info(self, title, message):
        if self._app.handle:
            self._app.handle.message_box(title, message)
        else:
            print(f"Dialog (No handle): {title} - {message}")

class TrayManager:
    def __init__(self, app):
        self._app = app
        self._tooltip = "CactusCat"
        self._menu = Menu("Tray")
        self._icon = None

    def set_tooltip(self, text):
        self._tooltip = text

    def get_menu(self):
        return self._menu

    def set_icon(self, path):
        self._icon = path

    def update(self):
        if self._app.handle:
             mb = MenuBar()
             mb.add_menu(self._menu)
             data = mb._prepare()[0]
             # Transfer callbacks
             self._app.menu._callbacks.update(mb._callbacks)
             self._app.handle.set_tray(json.dumps(data), self._icon)

class ShortcutsManager:
    def __init__(self, app):
        self._app = app
        self._callbacks = {} # id -> callback
        self._accels = {} # id -> accel_str
        self._counter = 2000

    def register(self, accelerator, callback):
        self._counter += 1
        id_ = self._counter
        self._callbacks[id_] = callback
        self._accels[id_] = accelerator
        if self._app.handle:
            self._app.handle.register_shortcut(accelerator, id_)
        return id_

    def _handle(self, id_):
        cb = self._callbacks.get(id_)
        if cb:
            cb()

class App:
    def __init__(self, title=None, url=None, asset_root=None):
        self.settings = self._load_settings()
        
        # Override URL if in dev mode
        dev_url = os.environ.get("CACTUS_DEV_URL")
        if dev_url:
            self.url = dev_url
        else:
            self.url = url or self.settings.get("url", "http://localhost:3000")

        self.title = title or self.settings.get("title", "CactusCat App")
        self.asset_root = asset_root
        
        self.frameless = self.settings.get("frameless", False)
        self.resizable = self.settings.get("resizable", True)
        self.always_on_top = self.settings.get("always_on_top", False)
        self.transparent = self.settings.get("transparent", False)
        self.fullscreen = self.settings.get("fullscreen", False)
        
        # Engine Initialization
        engine_name = self.settings.get("engine", "native")
        if os.environ.get("CACTUS_ENGINE"):
            engine_name = os.environ.get("CACTUS_ENGINE")
        self.engine = get_engine(engine_name, self)
        self.handle = None

        self.msg_handler = None
        self.functions = {
            "minimize": self.minimize,
            "maximize": self.maximize,
            "restore": self.restore,
            "close": self.close,
            "hide": self.hide,
            "show": self.show,
            "set_title": self.set_title,
            "shell_open": shell.open_external,
            "shell_show": shell.show_item_in_folder,
            "system_info": shell.get_system_info,
            "store_get": self.store_get,
            "store_set": self.store_set,
            "store_delete": self.store_delete,
            "message_box": self.message_box,
            "open_file_dialog": self.open_file_dialog,
            "save_file_dialog": self.save_file_dialog,
            "select_folder_dialog": self.select_folder_dialog,
            "get_state": lambda: dict(self.state),
            "log": lambda msg: self.logger.info(f"[JS] {msg}"),
            "report_error": self._handle_js_error,
            "publish_event": self._handle_publish,
            "inspector_snapshot": lambda: self.inspector.get_snapshot(),
            "evolution_check": lambda: self.evolution.check_for_updates(),
            "router_resolve": lambda url: self.router.resolve(url),
            "clipboard_copy": shell.copy_to_clipboard,
            "start_on_boot": lambda enable: shell.set_start_on_boot(self.title, enable),
            "system_notification": self.system_notification,
            "set_taskbar_progress": self.set_taskbar_progress,
            "set_fullscreen": self.set_fullscreen,
            "set_resizable": self.set_resizable,
            "set_always_on_top": self.set_always_on_top,
            "set_window_icon": self.set_window_icon,
            "serve_data": self.serve_data
        }
        self.logger = logging.getLogger("CactusCat")
        
        self.state = ReactiveState(self)
        self._store_path = "storage.json"
        self._store_data = self._load_store()

        self.router = Router()
        self.inspector = Inspector(title or "CactusCat")
        self.inspector.start_telemetry()
        self.guard = ProcessGuard(self)
        
        # Single Instance Check
        if self.settings.get("single_instance", False):
            app_id = self.settings.get("app_id", f"com.cactuscat.{self.title}")
            self.guard.enforce_single_instance(app_id)

        self.evolution = Evolution(
            current_version=self.settings.get("version", "1.0.0"),
            update_url=self.settings.get("update_url", "")
        )

        plugins_dir = self.settings.get("plugins_dir", "plugins")
        storage_dir = self.settings.get("storage_dir", "storage/plugins")
        self.plugin_manager = PluginManager(self, plugins_dir=plugins_dir, storage_dir=storage_dir)
        
        self.served_data = {}
        self._on_exit_callbacks = []
        self.handle = None
        self.bus = EventBus()
        self.dialogs = DialogManager(self)
        self.tray = TrayManager(self)
        self.menu = MenuBar() 
        self.shortcuts = ShortcutsManager(self)

    def _load_settings(self):
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _load_store(self):
        if os.path.exists(self._store_path):
            try:
                with open(self._store_path, "r") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_store(self):
        try:
            with open(self._store_path, "w") as f:
                json.dump(self._store_data, f)
        except:
            pass

    def store_set(self, key, value):
        self._store_data[key] = value
        self._save_store()

    def store_get(self, key, default=None):
        return self._store_data.get(key, default)

    def store_delete(self, key):
        if key in self._store_data:
            del self._store_data[key]
            self._save_store()

    def serve_data(self, key, data, mime_type="application/octet-stream"):
        """Serve binary data via ccat://data/<key>"""
        self.served_data[key] = (data, mime_type)
        if self.handle:
            self.handle.serve_data(key, data, mime_type)

    def on_exit(self, func):
        self._on_exit_callbacks.append(func)
        return func

    def set_title(self, title):
        self.title = title
        if self.handle: self.handle.set_title(title)

    def start_drag(self):
        """Starts a native window drag. Essential for frameless windows."""
        if self.handle:
            self.handle.start_drag()

    def minimize(self):
        if self.handle: self.handle.minimize()

    def maximize(self):
        if self.handle: self.handle.maximize()

    def restore(self):
        if self.handle: self.handle.restore()

    def hide(self):
        """Hides the application window."""
        if self.handle: self.handle.hide()

    def show(self):
        """Shows the application window."""
        if self.handle: self.handle.show()

    def close(self):
        if self.handle: self.handle.close()

    def message_box(self, title, message):
        if self.handle: self.handle.message_box(title, message)
    
    def open_file_dialog(self, title="Open File", default_path=None):
        if self.handle: return self.handle.open_file_dialog(title, default_path)
    
    def save_file_dialog(self, title="Save File", default_path=None):
        if self.handle: return self.handle.save_file_dialog(title, default_path)
    
    def select_folder_dialog(self, title="Select Folder", default_path=None):
        if self.handle: return self.handle.select_folder_dialog(title, default_path)

    def system_notification(self, title, message, icon_path=None):
        """Shows a native system notification."""
        if self.handle:
            self.handle.system_notification(title, message, icon_path)
        else:
            self.notify(title, message) # Fallback to frontend event

    def set_taskbar_progress(self, state, progress=0):
        """
        Sets the taskbar progress state.
        States: "normal", "indeterminate", "error", "paused", "none"
        """
        if self.handle:
            self.handle.set_taskbar_progress(state, progress)

    def set_app_id(self, app_id):
        """Sets the application ID (AppUserModelID on Windows)."""
        if self.handle:
            self.handle.set_app_id(app_id)

    def set_fullscreen(self, fullscreen):
        """Sets the window to fullscreen or windowed mode."""
        self.fullscreen = fullscreen
        if self.handle:
            self.handle.set_fullscreen(fullscreen)

    def set_resizable(self, resizable):
        """Sets whether the window is resizable."""
        self.resizable = resizable
        if self.handle:
            self.handle.set_resizable(resizable)

    def set_always_on_top(self, always_on_top):
        """Sets whether the window stays on top of other windows."""
        self.always_on_top = always_on_top
        if self.handle:
            self.handle.set_always_on_top(always_on_top)

    def set_window_icon(self, icon_path):
        """Changes the window icon at runtime."""
        if self.handle:
            self.handle.set_window_icon(icon_path)

    def rpc(self, obj):
        return self.expose(obj)

    def expose(self, obj=None, name=None):
        """
        Exposes a function, class, or object to the frontend.
        If a class is passed, it will be instantiated and all public methods exposed.
        """
        import inspect
        if obj is None:
            def decorator(func):
                self.expose(func, name=name)
                return func
            return decorator

        # Case 1: Routine (function/method)
        if inspect.isroutine(obj):
            n = name or obj.__name__
            self.functions[n] = obj
            return obj
        
        # Case 2: Class
        if inspect.isclass(obj):
            try:
                instance = obj()
                return self.expose(instance, name=name)
            except Exception as e:
                self.logger.error(f"Failed to instantiate class {obj.__name__}: {e}")
                return obj

        # Case 3: Instance/Object
        for member_name, member in inspect.getmembers(obj):
            if not member_name.startswith('_') and inspect.isroutine(member):
                # If name prefix provided, use it
                fn_name = f"{name}_{member_name}" if name else member_name
                self.functions[fn_name] = member
        return obj

    def shortcut(self, accelerator, callback=None):
        """
        Decorator to register a global keyboard shortcut.
        Example: @app.shortcut("Ctrl+Shift+L")
        """
        if callback is None:
            def decorator(func):
                self.shortcuts.register(accelerator, func)
                return func
            return decorator
        self.shortcuts.register(accelerator, callback)
        return callback

    def notify(self, title, message, type="info", duration=5000):
        """Standard notification helper for the frontend."""
        self.publish("cactus:notification", {
            "title": title,
            "message": message,
            "type": type,
            "duration": duration
        })

    def _handle_js_error(self, error_data):
        msg = error_data.get("message", "Unknown script error")
        stack = error_data.get("stack", "")
        source = error_data.get("source", "unknown")
        line = error_data.get("lineno", "?")
        self.logger.error(f"JavaScript Error: {msg} at {source}:{line}\n{stack}")

    def eval(self, script):
        if self.handle:
            self.handle.eval(script)

    def publish(self, event, data=None):
        """Sends an event to the frontend."""
        json_data = json.dumps(data)
        script = f"window.dispatchEvent(new CustomEvent('{event}', {{ detail: {json_data} }}));"
        self.eval(script)

    def broadcast(self, event, data=None):
        """Broadcasts an event to all potential listeners (alias for publish)."""
        self.publish(event, data)

    def quit(self):
        """Gracefully shuts down the application."""
        self._handle_exit()
        if self.handle:
            self.handle.close()

    def _handle_exit(self):
        """Internal helper to run all exit callbacks."""
        for cb in self._on_exit_callbacks:
            try:
                cb()
            except Exception as e:
                self.logger.error(f"Error in on_exit callback: {e}")
        self.bus.emit("exit")

    def close_splash(self):
        """Closes the native splash screen if one was shown."""
        if self.handle:
            self.handle.close_splash()

    def run(self, url=None, splash_html=None, splash_size=(400, 300)):
        if url:
             self.url = url
        
        target_url = self.url
        if not target_url.startswith(("http", "ccat", "cactus", "file")):
             target_url = os.path.abspath(target_url)
             self.asset_root = os.path.dirname(target_url)
             target_url = f"ccat://localhost/{os.path.basename(target_url)}"

        # Default splash if requested and none provided
        if splash_html == True:
            splash_html = """
            <html>
            <body style="background: #111; color: #fff; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; font-family: sans-serif; border: 1px solid #333;">
                <div style="text-align: center;">
                    <h2 style="margin-bottom: 5px;">🌵 CactusCat</h2>
                    <p style="color: #888; font-size: 14px;">Loading Engine...</p>
                    <div style="margin-top: 15px; width: 40px; height: 40px; border: 3px solid #333; border-top-color: #00ff88; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                </div>
                <style>
                    @keyframes spin { to { transform: rotate(360deg); } }
                </style>
            </body>
            </html>
            """

        # Prepare initialization script
        init_script = ""
        try:
            # Search for ccat/index.js in multiple possible locations
            base_path = os.path.dirname(__file__)
            possible_paths = [
                os.path.join(base_path, "ccat", "index.js"),
                os.path.join(os.path.dirname(base_path), "ccat", "index.js"),
                os.path.join(os.getcwd(), "ccat", "index.js")
            ]
            
            client_lib_path = None
            for p in possible_paths:
                if os.path.exists(p):
                    client_lib_path = p
                    break
            
            if client_lib_path:
                with open(client_lib_path, "r") as f:
                    init_script = f.read()
            else:
                self.logger.warning("Client library index.js not found in any expected location.")
        except Exception as e:
            self.logger.error(f"Failed to load client library: {e}")

        def on_ready(handle):
            self.handle = handle
            self.engine.handle = handle
            if self.handle:
                self.handle.set_title(self.title)
                if self.menu:
                    self.handle.set_menu(json.dumps(self.menu._prepare()))
                self.tray.update()
                for id_, accel in self.shortcuts._accels.items():
                    self.handle.register_shortcut(accel, id_)
                for k, (data, mime) in self.served_data.items():
                    self.handle.serve_data(k, data, mime)
                for k, v in self.state.items():
                    self.state._sync(k, v)
                
                # Set App ID if provided
                app_id = self.settings.get("app_id")
                if app_id:
                    self.handle.set_app_id(app_id)

                # Auto-close splash when everything is mapped
                self.close_splash()
                self.bus.emit("ready")

        def on_msg(msg):
            try:
                data = json.loads(msg)
                msg_type = data.get("type")
                event = data.get("event")
                
                if msg_type == "rpc" or ("method" in data and "id" in data):
                    self._handle_rpc(data)
                elif event == "state_update":
                    self.state._internal_set(data.get("key"), data.get("value"))
                    self.bus.emit(f"state:{data.get('key')}", data.get("value"))
                elif event == "menu_click":
                    self.menu._handle_command(data.get("id"))
                elif event == "shortcut":
                    self.shortcuts._handle(data.get("id"))
                elif event == "native_drop":
                    self.bus.emit("drop", data.get("paths"))
                elif event == "window_close":
                    self._handle_exit()
                elif self.msg_handler:
                    self.msg_handler(data)
            except Exception as e:
                self.logger.error(f"Error in on_msg: {e} | Msg: {msg}")

        self.plugin_manager.discover_and_load()

        if self.settings.get("debug", False):
            try:
                from .commands.ts_gen import generate_ts_definitions
                out = self.settings.get("ts_output", "frontend/src/cactus.d.ts")
                generate_ts_definitions(self, out)
            except Exception as e:
                self.logger.debug(f"Auto-TS generation skipped: {e}")

        # Dead Man's Switch
        self.guard.start_dead_mans_switch()
        
        self._started = True
        
        # Start Engine
        self.engine.start(
            self.title,
            target_url,
            on_ready=on_ready,
            on_msg=on_msg,
            asset_root=self.asset_root,
            initialization_script=init_script,
            frameless=self.frameless,
            resizable=self.resizable,
            always_on_top=self.always_on_top,
            maximized=self.settings.get("maximized", False),
            transparent=self.transparent,
            fullscreen=self.fullscreen,
            splash_html=splash_html,
            splash_width=splash_size[0],
            splash_height=splash_size[1]
        )

    def _handle_publish(self, data):
        event = data.get("event")
        payload = data.get("data")
        # 1. Emit to Python bus
        self.bus.emit(event, payload)
        # 2. Broadcast back to JS (all windows/current window)
        self.publish(event, payload)

    def _handle_rpc(self, data):
        call_id = data.get("id")
        method = data.get("method")
        args = data.get("args", [])
        func = self.functions.get(method)
        if not func:
            self._send_rpc_error(call_id, f"Method '{method}' not found")
            self.inspector.record_ipc(method, args, None, f"Method '{method}' not found")
            return
        try:
            if isinstance(args, dict):
                result = func(**args)
            else:
                result = func(*args)
            self._send_rpc_result(call_id, result)
            self.inspector.record_ipc(method, args, result)
        except Exception as e:
            self._send_rpc_error(call_id, str(e))
            self.inspector.record_ipc(method, args, None, str(e))

    def _send_rpc_result(self, call_id, result):
        payload = json.dumps(cactus_serialize(result, asset_provider=self.serve_data), cls=CactusJSONEncoder)
        script = f"window.dispatchEvent(new CustomEvent('rpc_result_{call_id}', {{ detail: {{ 'result': {payload} }} }}));"
        self.eval(script)

    def _send_rpc_error(self, call_id, error):
        payload = json.dumps(cactus_serialize(error, asset_provider=self.serve_data), cls=CactusJSONEncoder)
        script = f"window.dispatchEvent(new CustomEvent('rpc_result_{call_id}', {{ detail: {{ 'error': {payload} }} }}));"
        self.eval(script)
