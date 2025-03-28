# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Critical imports that must be preserved
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from types import ModuleType

"""Standard test file imports and setup.

This snippet is automatically added to test files by SnippetForTests.py.
It provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration
3. Common test imports and fixtures
4. Service initialization support
5. Logging configuration
"""
        # Add project root to path
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        logging.warning("Could not find import_helper.py. Using fallback configuration.")
except Exception as e:
    logging.warning(f"Failed to import import_helper: {{e}}. Using fallback configuration.")
    # Add project root to path
    current_file = Path(__file__).resolve()
    test_dir = current_file.parent.parent
    project_root = test_dir.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_project_root(test_dir: Path) -> Optional[Path]:
    """Find the project root directory.
    
    Args:
        test_dir: The directory containing the test file
        
    Returns:
        The project root directory or None if not found
    """
    try:
        # Try to find project root by looking for main.py or known directories
        for parent in [test_dir] + list(test_dir.parents):
            # Check for main.py as an indicator of project root
            if (parent / "main.py").exists():
                return parent
            # Check for typical project structure indicators
            if all((parent / d).exists() for d in ["services", "models", "controllers"]):
                return parent
        
        # If we still don't have a project root, use parent of the tests-dest directory
        for parent in test_dir.parents:
            if parent.name == "tests-dest":
                return parent.parent
                
        return None
    except Exception as e:
        logger.error(f"Error finding project root: {e}")
        return None

# Find project root dynamically
test_file = Path(__file__).resolve()
test_dir = test_file.parent
project_root = find_project_root(test_dir)

if project_root:
    logger.info(f"Project root detected at: {project_root}")
    
    # Add project root to path if found
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.info(f"Added {project_root} to Python path")
else:
    logger.warning("Could not detect project root")

# Import the test_import_helper
try:
    from test_import_helper import setup_test_paths, setup_test_env_vars
    setup_test_paths()
    logger.info("Successfully initialized test paths from test_import_helper")
except ImportError as e:
    # Fall back if test_import_helper is not available
    if str(test_dir.parent) not in sys.path:
        sys.path.insert(0, str(test_dir.parent))
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root) if project_root else "")
    logger.warning(f"Failed to import test_import_helper: {e}. Using fallback configuration.")

# Common test imports
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

# Import common fixtures and services
try:
    from conftest import test_services
    from services.base_service import BaseService
    from services.monitor_service import MonitorService
    from services.template_service import TemplateService
    from services.p2p_service import P2PService
    from models.base_model import BaseModel
    from models.material import Material
    from models.requisition import Requisition
    from fastapi import FastAPI, HTTPException
    logger.info("Successfully imported test fixtures and services")
except ImportError as e:
    # Log import error but continue - not all tests need all imports
    logger.warning(f"Optional import failed: {e}")
    logger.debug("Stack trace:", exc_info=True)

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment for each test."""
    setup_test_env_vars(monkeypatch)
    logger.info("Test environment initialized")
    yield
    logger.info("Test environment cleaned up")
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

# tests-dest/unit/test_state_manager.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import os
import tempfile
import json
from services.state_manager import StateManager
from models.common import BaseDataModel

class TestStateManager:
    def setup_method(self):
        """Create a fresh StateManager for each test"""
        self.state_manager = StateManager()
    
    def test_set_and_get(self):
        """Test setting and getting values"""
        # Set a value
        self.state_manager.set("test_key", "test_value")
        
        # Get the value
        value = self.state_manager.get("test_key")
        
        assert value == "test_value"
    
    def test_get_nonexistent(self):
        """Test getting a non-existent key"""
        # Get a non-existent key
        value = self.state_manager.get("nonexistent")
        
        assert value is None
    
    def test_get_with_default(self):
        """Test getting a non-existent key with a default value"""
        # Get a non-existent key with a default value
        value = self.state_manager.get("nonexistent", "default")
        
        assert value == "default"
    
    def test_delete(self):
        """Test deleting a key"""
        # Set a value
        self.state_manager.set("test_key", "test_value")
        
        # Delete the key
        result = self.state_manager.delete("test_key")
        
        assert result is True
        assert self.state_manager.get("test_key") is None
    
    def test_delete_nonexistent(self):
        """Test deleting a non-existent key"""
        # Delete a non-existent key
        result = self.state_manager.delete("nonexistent")
        
        assert result is False
    
    def test_get_all_keys(self):
        """Test getting all keys"""
        # Set some values
        self.state_manager.set("key1", "value1")
        self.state_manager.set("key2", "value2")
        
        # Get all keys
        keys = self.state_manager.get_all_keys()
        
        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys
    
    def test_clear(self):
        """Test clearing all state"""
        # Set some values
        self.state_manager.set("key1", "value1")
        self.state_manager.set("key2", "value2")
        
        # Clear all state
        self.state_manager.clear()
        
        assert len(self.state_manager.get_all_keys()) == 0
    
    def test_pydantic_model_storage(self):
        """Test storing and retrieving Pydantic models"""
        # Create a model
        model = BaseDataModel(id="test-id")
        
        # Store the model
        self.state_manager.set_model("model", model)
        
        # Retrieve the model
        retrieved = self.state_manager.get_model("model", BaseDataModel)
        
        assert retrieved is not None
        assert retrieved.id == "test-id"
    
    def test_persistence(self):
        """Test state persistence to file"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp_path = temp.name
        
        try:
            # Create a StateManager with persistence
            persistent_manager = StateManager(persistence_file=temp_path)
            
            # Set some values
            persistent_manager.set("key1", "value1")
            persistent_manager.set("key2", "value2")
            
            # Create a new StateManager that should load from the file
            loaded_manager = StateManager(persistence_file=temp_path)
            
            # Check that the values were loaded
            assert loaded_manager.get("key1") == "value1"
            assert loaded_manager.get("key2") == "value2"
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
