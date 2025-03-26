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

# tests-dest/unit/test_models_common.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from datetime import datetime, timedelta
from models.common import BaseDataModel, EntityCollection

class TestBaseDataModel:
    def test_init_with_defaults(self):
        """Test initialization with default values"""
        model = BaseDataModel()
        
        # ID should be None by default
        assert model.id is None
        
        # created_at should be set automatically
        assert isinstance(model.created_at, datetime)
        
        # updated_at should be set automatically now
        assert model.updated_at is not None
        assert isinstance(model.updated_at, datetime)
    
    def test_init_with_values(self):
        """Test initialization with provided values"""
        now = datetime.now()
        model = BaseDataModel(id="test-id", created_at=now)
        
        assert model.id == "test-id"
        assert model.created_at == now
    
    def test_update_method(self):
        """Test the update method"""
        model = BaseDataModel(id="test-id")
        original_created_at = model.created_at
        original_updated_at = model.updated_at
        
        # Sleep briefly to ensure updated_at will be different
        import time
        time.sleep(0.001)
        
        # Update the model
        model.update({"id": "new-id"})
        
        # Check that id was updated
        assert model.id == "new-id"
        
        # Check that created_at was not changed
        assert model.created_at == original_created_at
        
        # Check that updated_at was set to a newer time
        assert model.updated_at is not None
        assert model.updated_at > original_updated_at
    
    def test_update_ignores_nonexistent_fields(self):
        """Test that update ignores fields that don't exist in the model"""
        model = BaseDataModel(id="test-id")
        
        # Update with a non-existent field
        model.update({"nonexistent_field": "value"})
        
        # Check that the model doesn't have the field
        assert not hasattr(model, "nonexistent_field")

class TestEntityCollection:
    def test_init(self):
        """Test initialization"""
        collection = EntityCollection(name="test-collection")
        
        assert collection.name == "test-collection"
        assert collection.entities == {}
    
    def test_add_and_get(self):
        """Test adding and getting entities"""
        collection = EntityCollection(name="test-collection")
        entity = BaseDataModel(id="test-id")
        
        # Add the entity
        collection.add("test-id", entity)
        
        # Get the entity
        retrieved = collection.get("test-id")
        
        assert retrieved == entity
    
    def test_get_nonexistent(self):
        """Test getting a non-existent entity"""
        collection = EntityCollection(name="test-collection")
        
        # Get a non-existent entity
        retrieved = collection.get("nonexistent")
        
        assert retrieved is None
    
    def test_get_all(self):
        """Test getting all entities"""
        collection = EntityCollection(name="test-collection")
        entity1 = BaseDataModel(id="test-id-1")
        entity2 = BaseDataModel(id="test-id-2")
        
        # Add entities
        collection.add("test-id-1", entity1)
        collection.add("test-id-2", entity2)
        
        # Get all entities
        all_entities = collection.get_all()
        
        assert len(all_entities) == 2
        assert entity1 in all_entities
        assert entity2 in all_entities
    
    def test_remove(self):
        """Test removing an entity"""
        collection = EntityCollection(name="test-collection")
        entity = BaseDataModel(id="test-id")
        
        # Add the entity
        collection.add("test-id", entity)
        
        # Remove the entity
        result = collection.remove("test-id")
        
        assert result is True
        assert collection.get("test-id") is None
    
    def test_remove_nonexistent(self):
        """Test removing a non-existent entity"""
        collection = EntityCollection(name="test-collection")
        
        # Remove a non-existent entity
        result = collection.remove("nonexistent")
        
        assert result is False
    
    def test_count(self):
        """Test counting entities"""
        collection = EntityCollection(name="test-collection")
        
        # Initially empty
        assert collection.count() == 0
        
        # Add entities
        collection.add("test-id-1", BaseDataModel(id="test-id-1"))
        collection.add("test-id-2", BaseDataModel(id="test-id-2"))
        
        # Count should be 2
        assert collection.count() == 2
        
        # Remove an entity
        collection.remove("test-id-1")
        
        # Count should be 1
        assert collection.count() == 1
