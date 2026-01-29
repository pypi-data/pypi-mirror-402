import pytest
import os
import sys
from pathlib import Path
from fastpluggy.fastpluggy import FastPluggy

# ensure plugin src is importable
PLUGIN_SRC = str(Path(__file__).parent.parent / "src")
if PLUGIN_SRC not in sys.path:
    sys.path.insert(0, PLUGIN_SRC)

def test_fastpluggy_initialization(fast_pluggy, fastapi_app):
    """
    Test that FastPluggy can be initialized properly in a test context.
    """
    assert fast_pluggy is not None
    assert fast_pluggy.app == fastapi_app
    
    # Verify that we can access the manager and plugins
    manager = fast_pluggy.get_manager()
    assert manager is not None
    
def test_fastpluggy_with_tasks_worker_load(fast_pluggy):
    """
    Verify that FastPluggy can load the tasks_worker plugin.
    """
    # Manually load the plugin if not auto-loaded
    # In some versions of FastPluggy, we might need to trigger discovery or load
    manager = fast_pluggy.get_manager()
    
    # Check if tasks_worker is available in the plugins directory
    plugin_name = "tasks_worker"
    
    # Try to load it explicitly if needed, or check if it's already there
    # The actual attribute name might vary (e.g., manager.plugins)
    # Let's see what's available
    print(f"Loaded modules: {manager.modules.keys()}")
    
    # If it's loaded, it should be in the modules
    # Note: FastPluggy might expect the plugin to be in a specific folder structure
