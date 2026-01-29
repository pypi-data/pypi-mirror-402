import pytest
import os
import json
import shutil
from unittest.mock import MagicMock, patch
from cactuscat import Application

@pytest.fixture
def temp_plugins(tmp_path):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    
    # Create a dummy plugin
    test_plugin = plugins_dir / "test_plugin"
    test_plugin.mkdir()
    
    manifest = {
        "name": "TestPlugin",
        "version": "1.0.0",
        "ui_entry": "index.js",
        "slot": "top-bar"
    }
    
    with open(test_plugin / "manifest.json", "w") as f:
        json.dump(manifest, f)
        
    with open(test_plugin / "main.py", "w") as f:
        f.write("def setup(app):\n    app.state.set('plugin_loaded', True)")
        
    return plugins_dir

def test_plugin_loading(temp_plugins):
    with patch('cactuscat.application._cactuscat'):
        app = Application(title="Plugin Test")
        # Override the plugins dir to our temp one
        app.plugin_manager.plugins_dir = str(temp_plugins)
        app.asset_root = os.path.dirname(str(temp_plugins))
        
        app.plugin_manager.discover_and_load()
        
        assert "TestPlugin" in app.plugin_manager.plugins
        assert app.state.get("plugin_loaded") is True
        
        # Verify UI metadata in state
        plugins_in_state = app.state.get("_plugins")
        assert len(plugins_in_state) == 1
        assert plugins_in_state[0]["name"] == "TestPlugin"
        assert "ccat://" in plugins_in_state[0]["ui_entry"]
