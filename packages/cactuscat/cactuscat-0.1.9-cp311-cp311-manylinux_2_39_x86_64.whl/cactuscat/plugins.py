import os
import json
import importlib.util
import sys
import logging
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger("CactusCat.Plugins")

class PluginStorage:
    """Provides namespaced JSON storage for plugins."""
    def __init__(self, base_path: str, plugin_id: str):
        self.path = os.path.join(base_path, f"{plugin_id}.json")
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load storage for plugin: {e}")

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save storage for plugin: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        self.data[key] = value
        self.save()

class SupervisedApp:
    """
    A proxy for the main App class that limits plugin access 
    and prevents plugin crashes from taking down the main app.
    """
    def __init__(self, app, plugin_id: str):
        self._app = app
        self._plugin_id = plugin_id

    @property
    def state(self):
        """Access to the global reactive state."""
        return self._app.state

    def __getattr__(self, name):
        # Allow access to specific safe methods
        safe_methods = ["notify", "get_version", "resolve_path", "broadcast", "publish"]
        if name in safe_methods:
            return getattr(self._app, name)
        
        # Block access to dangerous internals
        raise AttributeError(f"Plugin '{self._plugin_id}' attempted to access restricted attribute '{name}'")

    def call_js(self, func: str, *args):
        """Plugin-scoped JS call."""
        args_json = json.dumps(args)
        # Execute JS in the context of the plugin namespace
        # We look for window.cactus.plugins[plugin_id] which is where cactus-client.js
        # usually attaches plugin-provided JS methods.
        script = f"if(window.cactus && window.cactus.plugins && window.cactus.plugins['{self._plugin_id}']) window.cactus.plugins['{self._plugin_id}'].{func}(...{args_json});"
        return self._app.eval(script)

class Plugin:
    def __init__(self, name, path, manifest):
        self.name = name
        self.path = path
        self.manifest = manifest
        self.module = None
        self.id = manifest.get("id", name)
        self.instance = None
        self.storage: Optional[PluginStorage] = None

    def load(self, app, storage_base):
        main_py = os.path.join(self.path, "main.py")
        if not os.path.exists(main_py):
            return False

        try:
            self.storage = PluginStorage(storage_base, self.id)
            spec = importlib.util.spec_from_file_location(f"cactuscat.plugins.{self.id}", main_py)
            self.module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = self.module
            spec.loader.exec_module(self.module)
            
            # Setup with supervisor
            if hasattr(self.module, "setup"):
                supervisor = SupervisedApp(app, self.id)
                self.instance = self.module.setup(supervisor, self.storage)
            elif hasattr(self.module, "init"):
                supervisor = SupervisedApp(app, self.id)
                self.instance = self.module.init(supervisor, self.storage)
            
            return True
        except Exception as e:
            logger.error(f"Failed to load plugin {self.id}: {e}", exc_info=True)
            return False

class PluginManager:
    def __init__(self, app, plugins_dir="plugins", storage_dir="storage/plugins"):
        self.app = app
        self.plugins_dir = plugins_dir
        self.storage_dir = storage_dir
        self.plugins: Dict[str, Plugin] = {}
        self.logger = logging.getLogger("CactusCat.Plugins")

    def discover_and_load(self):
        if not os.path.exists(self.plugins_dir):
            return

        for entry in os.scandir(self.plugins_dir):
            if entry.is_dir():
                # Support both Pytron's 'plugin.json' and generic 'manifest.json'
                manifest_path = os.path.join(entry.path, "plugin.json")
                if not os.path.exists(manifest_path):
                    manifest_path = os.path.join(entry.path, "manifest.json")
                
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, "r") as f:
                            manifest = json.load(f)
                        
                        plugin_name = manifest.get("name", entry.name)
                        plugin = Plugin(plugin_name, entry.path, manifest)
                        if plugin.load(self.app, self.storage_dir):
                            self.plugins[plugin.id] = plugin
                            self.logger.info(f"Loaded plugin: {plugin_name} ({plugin.id})")
                            
                            # Sync UI info to state for client-side injection
                            ui_entry = manifest.get("ui_entry")
                            if ui_entry:
                                # Create a ccat:// URL that points to the UI asset
                                # We use the path relative to the current working directory
                                full_ui_path = os.path.join(entry.path, ui_entry)
                                rel_ui_path = os.path.relpath(full_ui_path, os.getcwd())
                                ui_url = f"ccat://{rel_ui_path}".replace("\\", "/")
                                
                                current_plugins = self.app.state.get("_plugins", [])
                                current_plugins.append({
                                    "id": plugin.id,
                                    "name": plugin_name,
                                    "ui_entry": ui_url,
                                    "slot": manifest.get("slot", "sidebar")
                                })
                                self.app.state.set("_plugins", current_plugins)
                    except Exception as e:
                        self.logger.error(f"Failed to load plugin from {entry.path}: {e}")

    def broadcast(self, event: str, *args, **kwargs):
        """Send an event to all loaded plugins."""
        for plugin_id, plugin in self.plugins.items():
            if plugin.instance and hasattr(plugin.instance, event):
                try:
                    getattr(plugin.instance, event)(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Plugin '{plugin_id}' error during '{event}': {e}")
