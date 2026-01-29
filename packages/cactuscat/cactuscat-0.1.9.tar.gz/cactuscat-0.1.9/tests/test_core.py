import pytest
from unittest.mock import MagicMock, patch
import json
from cactuscat import Application, ReactiveState

@pytest.fixture
def mock_app():
    # Mock the native module to prevent window creation
    with patch('cactuscat.application._cactuscat') as mock_native:
        app = Application(title="Test App")
        app.handle = MagicMock() # Mock the handle that normally comes from Rust
        return app

def test_reactive_state_sync(mock_app):
    state = mock_app.state
    
    # Test initial state
    state.set("user", "alice")
    assert state.get("user") == "alice"
    
    # Verify that it called eval on the handle for sync
    # The _sync method uses window.dispatchEvent(new CustomEvent('ccat:state-update', ...))
    mock_app.handle.eval.assert_called()
    last_call = mock_app.handle.eval.call_args[0][0]
    assert "ccat:state-update" in last_call
    assert "alice" in last_call

def test_rpc_registration(mock_app):
    @mock_app.rpc
    def multiplier(a, b):
        return a * b
    
    assert "multiplier" in mock_app.functions
    result = mock_app.functions["multiplier"](10, 5)
    assert result == 50

def test_menu_serialization(mock_app):
    file_menu = mock_app.menu.add_menu("File")
    file_menu.add_item("Save", callback=lambda: print("Save"))
    
    serialized = mock_app.menu._prepare()
    assert len(serialized) == 1
    assert serialized[0]["title"] == "File"
    assert serialized[0]["items"][0]["label"] == "Save"
    assert "id" in serialized[0]["items"][0]

def test_event_bus(mock_app):
    received = []
    def handler(data):
        received.append(data)
    
    mock_app.bus.on("test_event", handler)
    mock_app.bus.emit("test_event", "payload")
    
    assert received == ["payload"]

def test_rpc_handling(mock_app):
    # Setup an RPC function
    mock_app.functions["add"] = lambda a, b: a + b
    
    # Simulate a message from JS
    rpc_msg = json.dumps({
        "type": "rpc",
        "method": "add",
        "args": [1, 2],
        "id": "test-id"
    })
    
    # Trigger the internal handler
    # Note: in application.py, on_msg is a closure inside run(). 
    # To test it we might need to expose it or test the logic it calls.
    # We can test _handle_rpc directly.
    mock_app._handle_rpc(json.loads(rpc_msg))
    
    # Check if result was sent back via eval
    mock_app.handle.eval.assert_called()
    last_call = mock_app.handle.eval.call_args[0][0]
    assert "rpc_result_test-id" in last_call
    assert "3" in last_call

def test_state_set_from_js(mock_app):
    # Simulate an update from JS
    # This happens via on_msg -> state_update case
    update = {
        "event": "state_update",
        "key": "theme",
        "value": "dark"
    }
    
    # We'll simulate the part of on_msg that handles this
    mock_app.state._internal_set("theme", "dark")
    assert mock_app.state.get("theme") == "dark"
    # Verify it didn't trigger a sync back to JS (to avoid loops)
    # mock_app.handle.eval should NOT have been called for this specific update
    # We clear previous calls first
    mock_app.handle.eval.reset_mock()
    mock_app.state._internal_set("mode", "light")
    mock_app.handle.eval.assert_not_called()
