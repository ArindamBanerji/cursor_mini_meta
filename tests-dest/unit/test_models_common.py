# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Critical imports that must be preserved
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

"""Standard test file imports and setup.

This snippet is automatically added to test files by SnippetForTests.py.
It provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration
3. Common test imports and fixtures
4. Service initialization support
"""

# Find project root dynamically
test_file = Path(__file__).resolve()
test_dir = test_file.parent

# Try to find project root by looking for main.py or known directories
project_root: Optional[Path] = None
for parent in [test_dir] + list(test_dir.parents):
    # Check for main.py as an indicator of project root
    if (parent / "main.py").exists():
        project_root = parent
        break
    # Check for typical project structure indicators
    if all((parent / d).exists() for d in ["services", "models", "controllers"]):
        project_root = parent
        break

# If we still don't have a project root, use parent of the tests-dest directory
if not project_root:
    # Assume we're in a test subdirectory under tests-dest
    for parent in test_dir.parents:
        if parent.name == "tests-dest":
            project_root = parent.parent
            break

# Add project root to path if found
if project_root and str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the test_import_helper
try:
    from test_import_helper import setup_test_paths
    setup_test_paths()
except ImportError:
    # Fall back if test_import_helper is not available
    if str(test_dir.parent) not in sys.path:
        sys.path.insert(0, str(test_dir.parent))
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root) if project_root else "")

# Common test imports
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

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
    from fastapi.testclient import TestClient
except ImportError as e:
    # Log import error but continue - not all tests need all imports
    import logging
    logging.warning(f"Optional import failed: {e}")
    logging.debug("Stack trace:", exc_info=True)
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

# tests-dest/unit/test_models_common.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from datetime import datetime, timedelta
from models.common import BaseDataModel, EntityCollection


def setup_module(module):
    """Set up the test module by ensuring PYTEST_CURRENT_TEST is set"""
    logger.info("Setting up test module")
    os.environ["PYTEST_CURRENT_TEST"] = "True"
    
def teardown_module(module):
    """Clean up after the test module"""
    logger.info("Tearing down test module")
    if "PYTEST_CURRENT_TEST" in os.environ:
        del os.environ["PYTEST_CURRENT_TEST"]
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
