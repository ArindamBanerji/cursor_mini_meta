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

# tests-dest/models/test_material_models.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from datetime import datetime
from pydantic import ValidationError as PydanticValidationError
from models.material import (
    MaterialType, UnitOfMeasure, MaterialStatus,
    MaterialCreate, MaterialUpdate, Material, MaterialDataLayer
)
from models.common import EntityCollection
from services.state_manager import StateManager

class TestMaterialModels:
    def test_material_create_minimal(self):
        """Test creating a material with minimal fields"""
        material_data = MaterialCreate(
            name="Test Material"
        )
        
        assert material_data.name == "Test Material"
        assert material_data.material_number is None
        assert material_data.type == MaterialType.FINISHED
        assert material_data.base_unit == UnitOfMeasure.EACH
        assert material_data.status == MaterialStatus.ACTIVE
    
    def test_material_create_full(self):
        """Test creating a material with all fields"""
        material_data = MaterialCreate(
            material_number="MAT123",
            name="Test Material",
            description="A test material",
            type=MaterialType.RAW,
            base_unit=UnitOfMeasure.KILOGRAM,
            status=MaterialStatus.ACTIVE,
            weight=10.5,
            volume=5.2,
            dimensions={"length": 10, "width": 5, "height": 2}
        )
        
        assert material_data.material_number == "MAT123"
        assert material_data.name == "Test Material"
        assert material_data.description == "A test material"
        assert material_data.type == MaterialType.RAW
        assert material_data.base_unit == UnitOfMeasure.KILOGRAM
        assert material_data.status == MaterialStatus.ACTIVE
        assert material_data.weight == 10.5
        assert material_data.volume == 5.2
        assert material_data.dimensions == {"length": 10, "width": 5, "height": 2}
    
    def test_material_create_validation(self):
        """Test validation for material create"""
        # Test invalid material number
        with pytest.raises(PydanticValidationError):
            MaterialCreate(
                material_number="MAT 123",  # Space not allowed
                name="Test Material"
            )
        
        # Test empty name
        with pytest.raises(PydanticValidationError):
            MaterialCreate(
                name=""
            )
        
        # Test negative weight
        with pytest.raises(PydanticValidationError):
            MaterialCreate(
                name="Test Material",
                weight=-10
            )
    
    def test_material_update(self):
        """Test material update model"""
        update_data = MaterialUpdate(
            name="Updated Name",
            status=MaterialStatus.INACTIVE
        )
        
        assert update_data.name == "Updated Name"
        assert update_data.status == MaterialStatus.INACTIVE
        assert update_data.description is None
    
    def test_material_model(self):
        """Test main material model"""
        material = Material(
            id="MAT123",
            material_number="MAT123",
            name="Test Material",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert material.id == "MAT123"
        assert material.material_number == "MAT123"
        assert material.name == "Test Material"
        assert material.type == MaterialType.FINISHED
        assert material.status == MaterialStatus.ACTIVE
    
    def test_create_from_create_model(self):
        """Test creating material from create model"""
        create_data = MaterialCreate(
            name="Test Material",
            type=MaterialType.SERVICE,
            description="A test service"
        )
        
        material = Material.create_from_create_model(create_data, "MAT123")
        
        assert material.id == "MAT123"
        assert material.material_number == "MAT123"
        assert material.name == "Test Material"
        assert material.type == MaterialType.SERVICE
        assert material.description == "A test service"
    
    def test_create_from_create_model_autogen_id(self):
        """Test auto-generation of material number"""
        create_data = MaterialCreate(
            name="Test Material"
        )
        
        material = Material.create_from_create_model(create_data)
        
        assert material.id is not None
        assert material.material_number is not None
        assert material.material_number.startswith("MAT")
        assert len(material.material_number) > 3
        assert material.id == material.material_number
    
    def test_update_from_update_model(self):
        """Test updating material from update model"""
        material = Material(
            id="MAT123",
            material_number="MAT123",
            name="Original Name",
            description="Original description",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        update_data = MaterialUpdate(
            name="Updated Name",
            status=MaterialStatus.INACTIVE
        )
        
        material.update_from_update_model(update_data)
        
        assert material.name == "Updated Name"
        assert material.status == MaterialStatus.INACTIVE
        assert material.description == "Original description"  # Unchanged
        assert material.material_number == "MAT123"  # Unchanged

class TestMaterialDataLayer:
    def setup_method(self):
        """Set up a fresh state manager and data layer for each test"""
        self.state_manager = StateManager()
        self.data_layer = MaterialDataLayer(self.state_manager)
    
    def test_create_material(self):
        """Test creating a material through the data layer"""
        create_data = MaterialCreate(
            material_number="MAT001",
            name="Test Material"
        )
        
        material = self.data_layer.create(create_data)
        
        assert material.material_number == "MAT001"
        assert material.name == "Test Material"
        
        # Check it was added to state
        collection = self.state_manager.get_model(self.data_layer.state_key, EntityCollection)
        assert collection is not None
        assert collection.count() == 1
        assert collection.get("MAT001") is not None
    
    def test_get_material(self):
        """Test getting a material by ID"""
        # Create a material first
        create_data = MaterialCreate(
            material_number="MAT001",
            name="Test Material"
        )
        self.data_layer.create(create_data)
        
        # Get it back
        material = self.data_layer.get_by_id("MAT001")
        
        assert material is not None
        assert material.material_number == "MAT001"
        assert material.name == "Test Material"
    
    def test_list_materials(self):
        """Test listing all materials"""
        # Create a few materials
        self.data_layer.create(MaterialCreate(material_number="MAT001", name="Material 1"))
        self.data_layer.create(MaterialCreate(material_number="MAT002", name="Material 2"))
        self.data_layer.create(MaterialCreate(material_number="MAT003", name="Material 3"))
        
        # List them
        materials = self.data_layer.list_all()
        
        assert len(materials) == 3
        assert any(m.material_number == "MAT001" for m in materials)
        assert any(m.material_number == "MAT002" for m in materials)
        assert any(m.material_number == "MAT003" for m in materials)
    
    def test_update_material(self):
        """Test updating a material"""
        # Create a material first
        self.data_layer.create(MaterialCreate(
            material_number="MAT001",
            name="Original Name",
            description="Original description"
        ))
        
        # Update it
        update_data = MaterialUpdate(
            name="Updated Name",
            status=MaterialStatus.INACTIVE
        )
        
        updated = self.data_layer.update("MAT001", update_data)
        
        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.status == MaterialStatus.INACTIVE
        assert updated.description == "Original description"  # Unchanged
        
        # Get it again to verify persistence
        material = self.data_layer.get_by_id("MAT001")
        assert material.name == "Updated Name"
        assert material.status == MaterialStatus.INACTIVE
    
    def test_delete_material(self):
        """Test deleting a material"""
        # Create a material first
        self.data_layer.create(MaterialCreate(material_number="MAT001", name="Material 1"))
        
        # Verify it exists
        assert self.data_layer.get_by_id("MAT001") is not None
        
        # Delete it
        result = self.data_layer.delete("MAT001")
        
        assert result is True
        assert self.data_layer.get_by_id("MAT001") is None
    
    def test_filter_materials(self):
        """Test filtering materials"""
        # Create some materials with different types
        self.data_layer.create(MaterialCreate(
            material_number="MAT001",
            name="Raw Material",
            type=MaterialType.RAW
        ))
        self.data_layer.create(MaterialCreate(
            material_number="MAT002",
            name="Finished Product",
            type=MaterialType.FINISHED
        ))
        self.data_layer.create(MaterialCreate(
            material_number="MAT003",
            name="Another Raw Material",
            type=MaterialType.RAW
        ))
        
        # Filter by type
        raw_materials = self.data_layer.filter(type=MaterialType.RAW)
        
        assert len(raw_materials) == 2
        assert all(m.type == MaterialType.RAW for m in raw_materials)
        
        # Filter by name containing a substring
        # This is more complex and not directly supported by the filter method,
        # but we can show how it would be done
        all_materials = self.data_layer.list_all()
        materials_with_raw = [m for m in all_materials if "Raw" in m.name]
        assert len(materials_with_raw) == 2
