import pytest
from unittest.mock import MagicMock, patch
import json
from cactuscat import Application

@pytest.fixture
def mock_app():
    with patch('cactuscat.application._cactuscat') as mock_native:
        app = Application(title="Test App")
        app.handle = MagicMock()
        return app

def test_shortcut_registration(mock_app):
    callback = MagicMock()
    id_ = mock_app.shortcuts.register("Ctrl+P", callback)
    
    # Check if native register was called
    mock_app.handle.register_shortcut.assert_called_with("Ctrl+P", id_)
    
    # Simulate shortcut trigger from Rust
    mock_app.shortcuts._handle(id_)
    callback.assert_called_once()

def test_tray_update(mock_app):
    mock_app.tray.set_tooltip("My Tray")
    mock_app.tray.get_menu().add_item("Test", callback=lambda: None)
    
    mock_app.tray.update()
    
    # Check if native set_tray was called
    mock_app.handle.set_tray.assert_called()
    args = mock_app.handle.set_tray.call_args[0]
    data = json.loads(args[0])
    assert data["title"] == "Tray"
    assert data["items"][0]["label"] == "Test"

def test_dialogs(mock_app):
    mock_app.dialogs.info("Hello", "World")
    mock_app.handle.message_box.assert_called_with("Hello", "World")

def test_publish(mock_app):
    mock_app.publish("custom_event", {"key": "value"})
    mock_app.handle.eval.assert_called()
    last_eval = mock_app.handle.eval.call_args[0][0]
    assert "custom_event" in last_eval
    assert '{"key": "value"}' in last_eval
