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

# tests-dest/integration/test_material_p2p_integration.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from models.material import (
    Material, MaterialCreate, MaterialUpdate, MaterialType, MaterialStatus
)
from models.p2p import (
    Requisition, RequisitionCreate, RequisitionUpdate, RequisitionItem,
    Order, OrderCreate, OrderUpdate, OrderItem,
    DocumentStatus, DocumentItemStatus
)
from services.material_service import MaterialService
from services.p2p_service import P2PService
from services.monitor_service import MonitorService
from services.state_manager import StateManager
from utils.error_utils import NotFoundError, ValidationError, ConflictError

# Import fixtures from conftest
from conftest import test_services

class TestMaterialP2PIntegration:
    """
    Tests for integration between Material and P2P services with focus on
    business scenarios and advanced workflows.
    """

    @pytest.fixture(autouse=True)
    def setup(self, test_services):
        """Set up test environment using the standardized service fixture."""
        self.state_manager = test_services["state_manager"]
        self.monitor_service = test_services["monitor_service"]
        self.material_service = test_services["material_service"]
        self.p2p_service = test_services["p2p_service"]
        
        # Create test materials with different types and statuses
        self.setup_test_materials()
    
    def setup_test_materials(self):
        """Set up various test materials with different statuses"""
        # Active materials of different types
        self.material_service.create_material(
            MaterialCreate(
                material_number="RAW001",
                name="Raw Material",
                type=MaterialType.RAW,
                description="Active raw material"
            )
        )
        
        self.material_service.create_material(
            MaterialCreate(
                material_number="FIN001",
                name="Finished Product",
                type=MaterialType.FINISHED,
                description="Active finished product"
            )
        )
        
        self.material_service.create_material(
            MaterialCreate(
                material_number="SRV001",
                name="Service Item",
                type=MaterialType.SERVICE,
                description="Active service item"
            )
        )
        
        # Inactive material
        self.material_service.create_material(
            MaterialCreate(
                material_number="INACTIVE001",
                name="Inactive Material",
                type=MaterialType.RAW,
                description="Inactive material"
            )
        )
        self.material_service.update_material(
            "INACTIVE001",
            MaterialUpdate(status=MaterialStatus.INACTIVE)
        )
        
        # Deprecated material
        self.material_service.create_material(
            MaterialCreate(
                material_number="DEPR001",
                name="Deprecated Material",
                type=MaterialType.FINISHED,
                description="Deprecated material"
            )
        )
        self.material_service.deprecate_material("DEPR001")
    
    def test_material_lifecycle_with_procurement(self):
        """Test the full lifecycle of a material in relation to procurement documents"""
        # Create a new material
        material = self.material_service.create_material(
            MaterialCreate(
                material_number="LIFECYCLE001",
                name="Lifecycle Test Material",
                type=MaterialType.RAW
            )
        )
        
        # Create a requisition using the material
        req_data = RequisitionCreate(
            document_number="REQ_LIFECYCLE",
            description="Lifecycle Test Requisition",
            requester="Test User",
            items=[
                RequisitionItem(
                    item_number=1,
                    material_number="LIFECYCLE001",
                    description="Lifecycle Material Item",
                    quantity=10,
                    unit="KG",
                    price=50
                )
            ]
        )
        
        requisition = self.p2p_service.create_requisition(req_data)
        assert requisition.items[0].material_number == "LIFECYCLE001"
        
        # Make the material inactive
        self.material_service.update_material(
            "LIFECYCLE001",
            MaterialUpdate(status=MaterialStatus.INACTIVE)
        )
        
        # Should still be able to submit and approve the requisition
        self.p2p_service.submit_requisition("REQ_LIFECYCLE")
        self.p2p_service.approve_requisition("REQ_LIFECYCLE")
        
        # Create an order from the requisition
        order = self.p2p_service.create_order_from_requisition(
            requisition_number="REQ_LIFECYCLE",
            vendor="Test Vendor"
        )
        
        # Verify the order contains the material
        assert order.items[0].material_number == "LIFECYCLE001"
        
        # Now deprecate the material
        self.material_service.deprecate_material("LIFECYCLE001")
        
        # Should still be able to submit, approve, and complete the order
        self.p2p_service.submit_order(order.document_number)
        self.p2p_service.approve_order(order.document_number)
        self.p2p_service.receive_order(order.document_number)
        self.p2p_service.complete_order(order.document_number)
        
        # Try to create a new requisition with the deprecated material
        req_data2 = RequisitionCreate(
            description="Requisition with Deprecated Material",
            requester="Test User",
            items=[
                RequisitionItem(
                    item_number=1,
                    material_number="LIFECYCLE001",
                    description="Deprecated Material Item",
                    quantity=10,
                    unit="KG",
                    price=50
                )
            ]
        )
        
        # This should fail because the material is now deprecated
        with pytest.raises(ValidationError) as excinfo:
            self.p2p_service.create_requisition(req_data2)
        
        assert "Invalid material" in str(excinfo.value.message)
        assert "LIFECYCLE001" in str(excinfo.value.message)
    
    def test_multi_material_requisition(self):
        """Test creating a requisition with multiple materials of different types"""
        # Create a requisition with multiple materials
        req_data = RequisitionCreate(
            document_number="MULTI001",
            description="Multi-Material Requisition",
            requester="Test User",
            items=[
                RequisitionItem(
                    item_number=1,
                    material_number="RAW001",
                    description="Raw Material Item",
                    quantity=10,
                    unit="KG",
                    price=50
                ),
                RequisitionItem(
                    item_number=2,
                    material_number="FIN001",
                    description="Finished Product Item",
                    quantity=5,
                    unit="EA",
                    price=200
                ),
                RequisitionItem(
                    item_number=3,
                    material_number="SRV001",
                    description="Service Item",
                    quantity=1,
                    unit="HR",
                    price=100
                )
            ]
        )
        
        requisition = self.p2p_service.create_requisition(req_data)
        
        # Verify all materials were included
        assert len(requisition.items) == 3
        assert requisition.items[0].material_number == "RAW001"
        assert requisition.items[1].material_number == "FIN001"
        assert requisition.items[2].material_number == "SRV001"
        
        # Try a mix of valid and invalid materials
        req_data2 = RequisitionCreate(
            description="Mixed Validity Requisition",
            requester="Test User",
            items=[
                RequisitionItem(
                    item_number=1,
                    material_number="RAW001",  # Valid
                    description="Valid Material Item",
                    quantity=10,
                    unit="KG",
                    price=50
                ),
                RequisitionItem(
                    item_number=2,
                    material_number="DEPR001",  # Invalid (deprecated)
                    description="Deprecated Material Item",
                    quantity=5,
                    unit="EA",
                    price=200
                )
            ]
        )
        
        # Should fail due to the deprecated material
        with pytest.raises(ValidationError) as excinfo:
            self.p2p_service.create_requisition(req_data2)
        
        assert "Invalid material" in str(excinfo.value.message)
        assert "DEPR001" in str(excinfo.value.message)
    
    def test_error_details_propagation(self):
        """Test that error details are properly propagated between services"""
        # Try to get a non-existent material
        material_id = "NONEXISTENT"
        
        # Material service should raise NotFoundError
        with pytest.raises(NotFoundError) as excinfo:
            self.material_service.get_material(material_id)
        
        # Check error details
        assert excinfo.value.message == f"Material with ID {material_id} not found"
        assert "material_id" in excinfo.value.details
        assert excinfo.value.details["material_id"] == material_id
        
        # Use the non-existent material in a requisition
        req_data = RequisitionCreate(
            description="Requisition with Non-existent Material",
            requester="Test User",
            items=[
                RequisitionItem(
                    item_number=1,
                    material_number=material_id,
                    description="Non-existent Material Item",
                    quantity=10,
                    unit="EA",
                    price=100
                )
            ]
        )
        
        # P2P service should convert NotFoundError to ValidationError
        with pytest.raises(ValidationError) as excinfo:
            self.p2p_service.create_requisition(req_data)
        
        # Check that the original error info is preserved in details
        assert "Invalid material" in str(excinfo.value.message)
        assert material_id in str(excinfo.value.message)
        if hasattr(excinfo.value, 'details') and "item_number" in excinfo.value.details:
            assert excinfo.value.details["item_number"] == 1
    
    def test_material_update_with_active_orders(self):
        """Test updating a material that is referenced in active orders"""
        # Create a material
        material = self.material_service.create_material(
            MaterialCreate(
                material_number="UPDATE001",
                name="Material to Update",
                type=MaterialType.RAW
            )
        )
        
        # Create a requisition using the material
        req_data = RequisitionCreate(
            document_number="REQ_UPDATE",
            description="Update Test Requisition",
            requester="Test User",
            items=[
                RequisitionItem(
                    item_number=1,
                    material_number="UPDATE001",
                    description="Material to Update Item",
                    quantity=10,
                    unit="KG",
                    price=50
                )
            ]
        )
        
        requisition = self.p2p_service.create_requisition(req_data)
        self.p2p_service.submit_requisition("REQ_UPDATE")
        self.p2p_service.approve_requisition("REQ_UPDATE")
        
        # Create an order from the requisition
        order = self.p2p_service.create_order_from_requisition(
            requisition_number="REQ_UPDATE",
            vendor="Test Vendor"
        )
        
        # Update the material name (should work)
        updated = self.material_service.update_material(
            "UPDATE001",
            MaterialUpdate(name="Updated Material Name")
        )
        assert updated.name == "Updated Material Name"
        
        # Make it inactive (should work)
        updated = self.material_service.update_material(
            "UPDATE001",
            MaterialUpdate(status=MaterialStatus.INACTIVE)
        )
        assert updated.status == MaterialStatus.INACTIVE
        
        # Deprecate the material (should work)
        updated = self.material_service.deprecate_material("UPDATE001")
        assert updated.status == MaterialStatus.DEPRECATED
        
        # Verify the material in the order still exists and hasn't been modified
        # by getting the order and checking its items
        updated_order = self.p2p_service.get_order(order.document_number)
        assert updated_order.items[0].material_number == "UPDATE001"
    
    def test_material_filter_by_procurement(self):
        """Test material filtering based on procurement data"""
        # Create materials for this test
        for i in range(5):
            self.material_service.create_material(
                MaterialCreate(
                    material_number=f"FILTER{i+1:03d}",
                    name=f"Filter Test Material {i+1}",
                    type=MaterialType.FINISHED
                )
            )
        
        # Create requisitions using only materials 1, 2, and 3
        for i in range(3):
            req_data = RequisitionCreate(
                document_number=f"REQ_FILTER{i+1:03d}",
                description=f"Filter Test Requisition {i+1}",
                requester="Test User",
                items=[
                    RequisitionItem(
                        item_number=1,
                        material_number=f"FILTER{i+1:03d}",
                        description=f"Filter Test Item {i+1}",
                        quantity=10,
                        unit="EA",
                        price=100
                    )
                ]
            )
            self.p2p_service.create_requisition(req_data)
        
        # List all materials
        all_materials = self.material_service.list_materials()
        filter_materials = [m for m in all_materials if m.material_number.startswith("FILTER")]
        assert len(filter_materials) == 5
        
        # This test would ideally check the ability to filter materials used in procurement,
        # but that functionality would need to be added to the material service
        # This is a placeholder for that functionality
    
    def test_error_handling_for_edge_cases(self):
        """Test error handling for edge cases in service interactions"""
        # Case 1: Create a requisition with an inactive material (should work)
        req_data = RequisitionCreate(
            document_number="EDGE001",
            description="Edge Case Requisition 1",
            requester="Test User",
            items=[
                RequisitionItem(
                    item_number=1,
                    material_number="INACTIVE001",  # This is inactive but not deprecated
                    description="Inactive Material Item",
                    quantity=10,
                    unit="KG",
                    price=50
                )
            ]
        )
        
        # This should work - inactive materials can be used
        requisition = self.p2p_service.create_requisition(req_data)
        assert requisition.items[0].material_number == "INACTIVE001"
        
        # Case 2: Attempt to create a requisition with a null material number but valid description
        req_data = RequisitionCreate(
            document_number="EDGE002",
            description="Edge Case Requisition 2",
            requester="Test User",
            items=[
                RequisitionItem(
                    item_number=1,
                    material_number=None,  # No material number
                    description="Non-Material Item",
                    quantity=10,
                    unit="EA",
                    price=100
                )
            ]
        )
        
        # This should work - material number is optional
        requisition = self.p2p_service.create_requisition(req_data)
        assert requisition.items[0].material_number is None
        assert requisition.items[0].description == "Non-Material Item"
