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

"""
Unit tests for the BaseService class.

This file tests the core functionality of the BaseService class:
1. State management (get, set, clear)
2. Item operations (get, set, delete)
3. State validation
4. State persistence (save, load)
5. Error handling
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from datetime import datetime
from typing import Dict, Any, Optional
from services.base_service import BaseService
from pydantic import BaseModel

# Define a simple model for testing with BaseService
class TestModel(BaseModel):
    id: str
    name: str
    value: int

# Define a mock state manager for testing
class MockStateManager:
    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        self.state = initial_state or {}
    
    def save_state(self, state: Dict[str, Any]) -> None:
        self.state = state.copy()
    
    def load_state(self) -> Dict[str, Any]:
        return self.state.copy()

@pytest.fixture
def mock_state_manager():
    """Fixture for a mock state manager."""
    return MockStateManager({"test_key": "test_value"})

@pytest.fixture
def base_service():
    """Fixture for a basic BaseService instance without state manager."""
    return BaseService[TestModel]()

@pytest.fixture
def base_service_with_state_manager(mock_state_manager):
    """Fixture for a BaseService instance with state manager."""
    return BaseService[TestModel](state_manager=mock_state_manager)

class TestBaseService:
    """Tests for the BaseService class."""
    
    def test_init(self):
        """Test service initialization."""
        # Test initialization without state manager
        service = BaseService[TestModel]()
        assert service.state_manager is None
        assert service._state == {}
        assert service._last_updated is None
        
        # Test initialization with state manager
        state_manager = MockStateManager()
        service = BaseService[TestModel](state_manager=state_manager)
        assert service.state_manager is state_manager
        assert service._state == {}
        assert service._last_updated is None
    
    def test_get_state(self, base_service):
        """Test get_state method."""
        # Initial state should be empty
        assert base_service.get_state() == {}
        
        # Set some state and verify get_state returns a copy
        test_state = {"key1": "value1", "key2": 123}
        base_service._state = test_state
        
        # Verify get_state returns a copy of the state
        retrieved_state = base_service.get_state()
        assert retrieved_state == test_state
        assert retrieved_state is not test_state  # Should be a copy
        
        # Modify the retrieved state and verify it doesn't affect the original
        retrieved_state["key3"] = "new_value"
        assert "key3" not in base_service._state
    
    def test_set_state(self, base_service):
        """Test set_state method."""
        # Initial state should be empty and no last_updated
        assert base_service._state == {}
        assert base_service._last_updated is None
        
        # Set a new state
        test_state = {"key1": "value1", "key2": 123}
        base_service.set_state(test_state)
        
        # Verify state was set correctly
        assert base_service._state == test_state
        assert base_service._state is not test_state  # Should be a copy
        assert base_service._last_updated is not None  # Should have a timestamp
        
        # Modify the original state and verify it doesn't affect service state
        test_state["key3"] = "new_value"
        assert "key3" not in base_service._state
    
    def test_get_last_updated(self, base_service):
        """Test get_last_updated method."""
        # Initially, last_updated should be None
        assert base_service.get_last_updated() is None
        
        # After setting state, last_updated should be a datetime
        base_service.set_state({"key": "value"})
        assert isinstance(base_service.get_last_updated(), datetime)
        
        # After clearing state, last_updated should be None again
        base_service.clear_state()
        assert base_service.get_last_updated() is None
    
    def test_validate_state(self, base_service):
        """Test validate_state method."""
        # Empty dict is valid
        assert base_service.validate_state() is True
        
        # Populated dict is valid
        base_service.set_state({"key": "value"})
        assert base_service.validate_state() is True
        
        # Non-dict state is invalid
        base_service._state = "not a dict"
        assert base_service.validate_state() is False
        
        # Exception during validation returns False
        with patch.object(base_service, '_state', side_effect=Exception("Test exception")):
            assert base_service.validate_state() is False
    
    def test_save_state(self, base_service_with_state_manager):
        """Test save_state method with state manager."""
        service = base_service_with_state_manager
        
        # Set up a test state
        test_state = {"key1": "value1", "key2": 123}
        service.set_state(test_state)
        
        # Save state should succeed and return True
        assert service.save_state() is True
        
        # Verify state was saved to state manager
        assert service.state_manager.state == test_state
    
    def test_save_state_no_manager(self, base_service):
        """Test save_state method without state manager."""
        # Set up a test state
        base_service.set_state({"key": "value"})
        
        # Save state should fail and return False
        assert base_service.save_state() is False
    
    def test_save_state_error(self, base_service_with_state_manager):
        """Test save_state method with error."""
        service = base_service_with_state_manager
        
        # Mock state manager to raise exception
        service.state_manager.save_state = MagicMock(side_effect=Exception("Test exception"))
        
        # Save state should fail and return False
        assert service.save_state() is False
    
    def test_load_state(self, base_service_with_state_manager):
        """Test load_state method with state manager."""
        service = base_service_with_state_manager
        
        # Set up a test state in state manager
        test_state = {"key1": "value1", "key2": 123}
        service.state_manager.state = test_state
        
        # Load state should succeed and return True
        assert service.load_state() is True
        
        # Verify state was loaded from state manager
        assert service._state == test_state
        assert service._last_updated is not None
    
    def test_load_state_no_manager(self, base_service):
        """Test load_state method without state manager."""
        # Load state should fail and return False
        assert base_service.load_state() is False
    
    def test_load_state_error(self, base_service_with_state_manager):
        """Test load_state method with error."""
        service = base_service_with_state_manager
        
        # Mock state manager to raise exception
        service.state_manager.load_state = MagicMock(side_effect=Exception("Test exception"))
        
        # Load state should fail and return False
        assert service.load_state() is False
    
    def test_load_state_empty(self, base_service_with_state_manager):
        """Test load_state method with empty state."""
        service = base_service_with_state_manager
        
        # Mock state manager to return None/falsy value
        service.state_manager.load_state = MagicMock(return_value=None)
        
        # Load state should fail and return False
        assert service.load_state() is False
    
    def test_clear_state(self, base_service):
        """Test clear_state method."""
        # Set up a test state
        test_state = {"key1": "value1", "key2": 123}
        base_service.set_state(test_state)
        
        # Verify state was set
        assert base_service._state == test_state
        assert base_service._last_updated is not None
        
        # Clear state
        base_service.clear_state()
        
        # Verify state was cleared
        assert base_service._state == {}
        assert base_service._last_updated is None
    
    def test_get_item(self, base_service):
        """Test get_item method."""
        # Set up a test state
        test_state = {"key1": "value1", "key2": 123}
        base_service.set_state(test_state)
        
        # Get existing items
        assert base_service.get_item("key1") == "value1"
        assert base_service.get_item("key2") == 123
        
        # Get non-existing item with default
        assert base_service.get_item("key3") is None
        assert base_service.get_item("key3", "default") == "default"
    
    def test_set_item(self, base_service):
        """Test set_item method."""
        # Initial state should be empty
        assert base_service._state == {}
        
        # Set items
        base_service.set_item("key1", "value1")
        base_service.set_item("key2", 123)
        
        # Verify items were set
        assert base_service._state == {"key1": "value1", "key2": 123}
        assert base_service._last_updated is not None
        
        # Update an item
        last_updated = base_service._last_updated
        # Sleep a small amount to ensure timestamp changes
        time.sleep(0.01)
        base_service.set_item("key1", "new_value")
        
        # Verify item was updated
        assert base_service._state["key1"] == "new_value"
        assert base_service._last_updated > last_updated
    
    def test_delete_item(self, base_service):
        """Test delete_item method."""
        # Set up a test state
        test_state = {"key1": "value1", "key2": 123}
        base_service.set_state(test_state)
        
        # Delete existing item
        assert base_service.delete_item("key1") is True
        assert "key1" not in base_service._state
        assert base_service._state == {"key2": 123}
        
        # Delete non-existing item
        assert base_service.delete_item("key3") is False
        assert base_service._state == {"key2": 123}
    
    def test_generic_type_parameter(self):
        """Test that the generic type parameter works correctly."""
        # Create a service with a specific model type
        service = BaseService[TestModel]()
        
        # The type parameter should be stored for reference
        assert service.__orig_class__.__args__[0] == TestModel 