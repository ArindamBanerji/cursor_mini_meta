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

# tests-dest/services/test_material_service.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from models.material import (
    Material, MaterialCreate, MaterialUpdate, MaterialDataLayer,
    MaterialType, UnitOfMeasure, MaterialStatus
)
from services.material_service import MaterialService
from services.state_manager import StateManager
from utils.error_utils import NotFoundError, ValidationError, ConflictError

class TestMaterialService:
    def setup_method(self):
        """Set up test environment before each test"""
        # Create a state manager just for testing
        self.state_manager = StateManager()
        # Create the service with our test state manager
        self.material_service = MaterialService(self.state_manager)
    
    def test_get_material(self):
        """Test getting a material by ID"""
        # Create a test material
        material_data = MaterialCreate(
            material_number="TEST001",
            name="Test Material"
        )
        created_material = self.material_service.create_material(material_data)
        
        # Get the material
        material = self.material_service.get_material("TEST001")
        
        assert material is not None
        assert material.material_number == "TEST001"
        assert material.name == "Test Material"
    
    def test_get_material_not_found(self):
        """Test getting a non-existent material"""
        with pytest.raises(NotFoundError):
            self.material_service.get_material("NONEXISTENT")
    
    def test_list_materials(self):
        """Test listing materials with filtering"""
        # Create test materials
        self.material_service.create_material(
            MaterialCreate(material_number="RAW001", name="Raw Material", type=MaterialType.RAW)
        )
        self.material_service.create_material(
            MaterialCreate(material_number="FINISHED001", name="Finished Product", type=MaterialType.FINISHED)
        )
        self.material_service.create_material(
            MaterialCreate(material_number="RAW002", name="Another Raw Material", type=MaterialType.RAW)
        )
        
        # List all materials
        all_materials = self.material_service.list_materials()
        assert len(all_materials) == 3
        
        # Filter by type
        raw_materials = self.material_service.list_materials(type=MaterialType.RAW)
        assert len(raw_materials) == 2
        assert all(m.type == MaterialType.RAW for m in raw_materials)
        
        # Filter by search term
        search_materials = self.material_service.list_materials(search_term="Finished")
        assert len(search_materials) == 1
        assert search_materials[0].material_number == "FINISHED001"
    
    def test_create_material(self):
        """Test creating a material"""
        # Create a material with minimal data
        material_data = MaterialCreate(name="New Material")
        material = self.material_service.create_material(material_data)
        
        assert material is not None
        assert material.name == "New Material"
        assert material.material_number is not None
        assert material.status == MaterialStatus.ACTIVE
        
        # Create a material with all fields
        material_data = MaterialCreate(
            material_number="FULL001",
            name="Full Material",
            description="A complete test material",
            type=MaterialType.SEMIFINISHED,
            base_unit=UnitOfMeasure.KILOGRAM,
            weight=10.5,
            dimensions={"length": 10, "width": 5, "height": 2}
        )
        material = self.material_service.create_material(material_data)
        
        assert material.material_number == "FULL001"
        assert material.name == "Full Material"
        assert material.description == "A complete test material"
        assert material.type == MaterialType.SEMIFINISHED
        assert material.base_unit == UnitOfMeasure.KILOGRAM
        assert material.weight == 10.5
        assert material.dimensions == {"length": 10, "width": 5, "height": 2}
    
    def test_create_material_duplicate(self):
        """Test creating a material with duplicate material number"""
        # Create a material
        material_data = MaterialCreate(
            material_number="DUP001",
            name="Original Material"
        )
        self.material_service.create_material(material_data)
        
        # Try to create another material with the same number
        duplicate_data = MaterialCreate(
            material_number="DUP001",
            name="Duplicate Material"
        )
        
        with pytest.raises(ConflictError):
            self.material_service.create_material(duplicate_data)
    
    def test_update_material(self):
        """Test updating a material"""
        # Create a material
        material_data = MaterialCreate(
            material_number="UPDATE001",
            name="Original Name"
        )
        original = self.material_service.create_material(material_data)
        
        # Update the material
        update_data = MaterialUpdate(
            name="Updated Name",
            description="Added description"
        )
        updated = self.material_service.update_material("UPDATE001", update_data)
        
        assert updated.material_number == "UPDATE001"
        assert updated.name == "Updated Name"
        assert updated.description == "Added description"
        assert updated.updated_at > original.created_at
    
    def test_update_material_not_found(self):
        """Test updating a non-existent material"""
        update_data = MaterialUpdate(name="New Name")
        
        with pytest.raises(NotFoundError):
            self.material_service.update_material("NONEXISTENT", update_data)
    
    def test_update_material_status_validation(self):
        """Test that deprecated materials cannot be changed to active"""
        # Create a material and mark it as deprecated
        material_data = MaterialCreate(
            material_number="DEPRECATED001",
            name="Deprecated Material"
        )
        material = self.material_service.create_material(material_data)
        self.material_service.deprecate_material("DEPRECATED001")
        
        # Try to set status back to ACTIVE
        update_data = MaterialUpdate(status=MaterialStatus.ACTIVE)
        
        with pytest.raises(ValidationError):
            self.material_service.update_material("DEPRECATED001", update_data)
    
    def test_delete_material(self):
        """Test deleting a material"""
        # Create a material
        material_data = MaterialCreate(
            material_number="DELETE001",
            name="Material to Delete"
        )
        material = self.material_service.create_material(material_data)
        
        # Mark it as inactive (can't delete active materials)
        update_data = MaterialUpdate(status=MaterialStatus.INACTIVE)
        self.material_service.update_material("DELETE001", update_data)
        
        # Delete the material
        result = self.material_service.delete_material("DELETE001")
        assert result is True
        
        # Verify it's gone
        with pytest.raises(NotFoundError):
            self.material_service.get_material("DELETE001")
    
    def test_delete_active_material(self):
        """Test that active materials cannot be deleted"""
        # Create a material
        material_data = MaterialCreate(
            material_number="ACTIVE001",
            name="Active Material"
        )
        material = self.material_service.create_material(material_data)
        
        # Try to delete it
        with pytest.raises(ValidationError):
            self.material_service.delete_material("ACTIVE001")
    
    def test_deprecate_material(self):
        """Test deprecating a material"""
        # Create a material
        material_data = MaterialCreate(
            material_number="DEPRECATE001",
            name="Material to Deprecate"
        )
        material = self.material_service.create_material(material_data)
        
        # Deprecate the material
        deprecated = self.material_service.deprecate_material("DEPRECATE001")
        
        assert deprecated.status == MaterialStatus.DEPRECATED
    
    def test_deprecate_already_deprecated(self):
        """Test that already deprecated materials are handled correctly"""
        # Create and deprecate a material
        material_data = MaterialCreate(
            material_number="ALREADY001",
            name="Already Deprecated"
        )
        material = self.material_service.create_material(material_data)
        self.material_service.deprecate_material("ALREADY001")
        
        # Try to deprecate it again
        with pytest.raises(ValidationError):
            self.material_service.deprecate_material("ALREADY001")
    
    def test_count_materials(self):
        """Test counting materials with filtering"""
        # Create test materials
        self.material_service.create_material(
            MaterialCreate(material_number="COUNT001", name="Material 1", type=MaterialType.RAW)
        )
        self.material_service.create_material(
            MaterialCreate(material_number="COUNT002", name="Material 2", type=MaterialType.FINISHED)
        )
        self.material_service.create_material(
            MaterialCreate(material_number="COUNT003", name="Material 3", type=MaterialType.RAW)
        )
        
        # Make one inactive
        self.material_service.update_material(
            "COUNT001", 
            MaterialUpdate(status=MaterialStatus.INACTIVE)
        )
        
        # Count all materials
        count_all = self.material_service.count_materials()
        assert count_all == 3
        
        # Count by type
        count_raw = self.material_service.count_materials(type=MaterialType.RAW)
        assert count_raw == 2
        
        # Count by status
        count_active = self.material_service.count_materials(status=MaterialStatus.ACTIVE)
        assert count_active == 2
        
        count_inactive = self.material_service.count_materials(status=MaterialStatus.INACTIVE)
        assert count_inactive == 1
    
    def test_get_material_by_number(self):
        """Test getting a material by material number"""
        # Create a test material
        material_data = MaterialCreate(
            material_number="NUMBER001",
            name="Test Material"
        )
        created_material = self.material_service.create_material(material_data)
        
        # Get the material by number
        material = self.material_service.get_material("NUMBER001")
        
        assert material is not None
        assert material.material_number == "NUMBER001"
        assert material.name == "Test Material"
    
    def test_generate_material_number(self):
        """Test material number generation based on type"""
        # Test with default type (FINISHED)
        material_data = MaterialCreate(name="Default Type")
        material = self.material_service.create_material(material_data)
        assert material.material_number.startswith("FIN")
        
        # Test with RAW type
        material_data = MaterialCreate(name="Raw Material", type=MaterialType.RAW)
        material = self.material_service.create_material(material_data)
        assert material.material_number.startswith("RAW")
        
        # Test with SERVICE type
        material_data = MaterialCreate(name="Service", type=MaterialType.SERVICE)
        material = self.material_service.create_material(material_data)
        assert material.material_number.startswith("SRV")
