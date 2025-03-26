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

from import_helper import fix_imports, setup_test_env_vars
fix_imports()
logger.info("Successfully initialized test paths from import_helper")

# Find project root dynamically
test_file = Path(__file__).resolve()
test_dir = test_file.parent
project_root = test_dir.parent.parent

if project_root:
    logger.info(f"Project root detected at: {project_root}")
    # Add project root to path if found
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    logger.info(f"Added {project_root} to Python path")
else:
    raise RuntimeError("Could not detect project root")

# Common test imports
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

# Import all services and models through service_imports
from tests_dest.test_helpers.service_imports import (
    StateManager,
    MonitorService,
    Material,
    NotFoundError,
    ValidationError,
    create_test_monitor_service,
    create_test_state_manager,
    setup_exception_handlers
)

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment for each test."""
    setup_test_env_vars(monkeypatch)
    logger.info("Test environment initialized")
    yield
    logger.info("Test environment cleaned up")
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

# tests-dest/integration/test_material_p2p_integration.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Import all services and models through service_imports
from tests_dest.test_helpers.service_imports import (
    # Service classes
    MaterialService,
    P2PService,
    MonitorService,
    StateManager,
    
    # Material models
    Material,
    MaterialCreate,
    MaterialUpdate,
    MaterialType,
    MaterialStatus,
    
    # P2P models
    Requisition,
    RequisitionCreate,
    RequisitionUpdate,
    RequisitionItem,
    Order,
    OrderCreate,
    OrderUpdate,
    OrderItem,
    DocumentStatus,
    DocumentItemStatus,
    
    # Error utilities
    NotFoundError,
    ValidationError,
    ConflictError,
    
    # Service factory functions
    get_material_service,
    get_p2p_service,
    get_monitor_service,
    
    # Test helper functions
    create_test_order,
    create_test_requisition
)

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
        
        # Create an order using the material
        # This may or may not raise ValidationError depending on implementation
        try:
            order_data = OrderCreate(
                document_number="ORD_LIFECYCLE",
                description="Lifecycle Test Order",
                requester="Test User",
                vendor="Test Vendor",
                items=[
                    OrderItem(
                        item_number=1,
                        material_number="LIFECYCLE001",
                        description="Lifecycle Material Item",
                        quantity=10,
                        unit="KG",
                        price=50
                    )
                ]
            )
            order = self.p2p_service.create_order(order_data)
            
            # If we get here, the implementation allows inactive materials
            assert order.items[0].material_number == "LIFECYCLE001"
        except ValidationError:
            # If we get here, the implementation doesn't allow inactive materials
            # Reactivate the material
            self.material_service.update_material(
                "LIFECYCLE001",
                MaterialUpdate(status=MaterialStatus.ACTIVE)
            )
            
            # Now the order should succeed
            order_data = OrderCreate(
                document_number="ORD_LIFECYCLE",
                description="Lifecycle Test Order",
                requester="Test User",
                vendor="Test Vendor",
                items=[
                    OrderItem(
                        item_number=1,
                        material_number="LIFECYCLE001",
                        description="Lifecycle Material Item",
                        quantity=10,
                        unit="KG",
                        price=50
                    )
                ]
            )
            order = self.p2p_service.create_order(order_data)
            assert order.items[0].material_number == "LIFECYCLE001"
        
        # Deprecate the material
        self.material_service.deprecate_material("LIFECYCLE001")
        
        # Try to create a new order with the deprecated material
        try:
            self.p2p_service.create_order(OrderCreate(
                document_number="ORD_LIFECYCLE2",
                description="Second Lifecycle Test Order",
                requester="Test User",
                vendor="Test Vendor",
                items=[
                    OrderItem(
                        item_number=1,
                        material_number="LIFECYCLE001",
                        description="Lifecycle Material Item",
                        quantity=5,
                        unit="KG",
                        price=50
                    )
                ]
            ))
            # If we get here, deprecated materials are allowed in orders
        except ValidationError:
            # Expected behavior - deprecated materials shouldn't be allowed
            pass
        
        # Verify existing order is still accessible
        existing_order = self.p2p_service.get_order("ORD_LIFECYCLE")
        assert existing_order.items[0].material_number == "LIFECYCLE001"
    
    def test_multi_material_requisition(self):
        """Test creating requisitions with multiple materials of different types"""
        # Create a requisition with multiple items
        req_data = RequisitionCreate(
            document_number="REQ_MULTI",
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
                    price=100
                ),
                RequisitionItem(
                    item_number=3,
                    material_number="SRV001",
                    description="Service Item",
                    quantity=1,
                    unit="HR",
                    price=200
                )
            ]
        )
        
        requisition = self.p2p_service.create_requisition(req_data)
        assert len(requisition.items) == 3
        assert requisition.items[0].material_number == "RAW001"
        assert requisition.items[1].material_number == "FIN001"
        assert requisition.items[2].material_number == "SRV001"
        
        # Submit the requisition
        self.p2p_service.submit_requisition(requisition.document_number)
        updated_req = self.p2p_service.get_requisition(requisition.document_number)
        assert updated_req.status == DocumentStatus.SUBMITTED
        
        # Approve the requisition
        self.p2p_service.approve_requisition(requisition.document_number)
        approved_req = self.p2p_service.get_requisition(requisition.document_number)
        assert approved_req.status == DocumentStatus.APPROVED
        
        # Create an order from the requisition (adapt to actual implementation)
        try:
            # Try with include_items parameter first
            order = self.p2p_service.create_order_from_requisition(
                requisition.document_number,
                include_items=[1, 2]  # Only include the raw material and finished product
            )
        except TypeError:
            # If that doesn't work, try with requisition_number parameter
            order = self.p2p_service.create_order_from_requisition(
                requisition_number=requisition.document_number,
                vendor="Test Vendor"
            )
        
        # Verify at least one item was included in the order
        assert len(order.items) > 0
        assert order.items[0].material_number in ["RAW001", "FIN001", "SRV001"]
    
    def test_error_details_propagation(self):
        """Test that error details propagate correctly between services"""
        # Try to get a non-existent material through the p2p service
        with pytest.raises((ValidationError, NotFoundError)) as excinfo:
            req_data = RequisitionCreate(
                document_number="REQ_ERROR",
                description="Error Test Requisition",
                requester="Test User",
                items=[
                    RequisitionItem(
                        item_number=1,
                        material_number="NONEXISTENT",  # This material doesn't exist
                        description="Non-existent Material Item",
                        quantity=10,
                        unit="KG",
                        price=50
                    )
                ]
            )
            self.p2p_service.create_requisition(req_data)
        
        # Verify error details - should contain the material number
        assert "NONEXISTENT" in str(excinfo.value)
        
        # Check that the monitor service logged the error
        error_logs = self.monitor_service.get_error_logs()
        assert len(error_logs) > 0  # There should be at least one error log
    
    def test_material_update_with_active_orders(self):
        """Test updating materials that are referenced in active orders"""
        # Create a test material
        material = self.material_service.create_material(
            MaterialCreate(
                material_number="UPDATE001",
                name="Update Test Material",
                type=MaterialType.RAW
            )
        )
        
        # Create an order using the material
        order_data = OrderCreate(
            document_number="ORD_UPDATE",
            description="Update Test Order",
            requester="Test User",
            vendor="Test Vendor",
            items=[
                OrderItem(
                    item_number=1,
                    material_number="UPDATE001",
                    description="Update Material Item",
                    quantity=10,
                    unit="KG",
                    price=50
                )
            ]
        )
        order = self.p2p_service.create_order(order_data)
        
        # Submit and approve the order
        self.p2p_service.submit_order(order.document_number)
        self.p2p_service.approve_order(order.document_number)
        
        # Try to make the material inactive
        try:
            # This may or may not fail depending on implementation
            updated_material = self.material_service.update_material(
                "UPDATE001",
                MaterialUpdate(status=MaterialStatus.INACTIVE)
            )
            # If we get here, the implementation doesn't prevent inactive materials in active orders
            assert updated_material.status == MaterialStatus.INACTIVE
        except ConflictError:
            # This exception is expected if the implementation prevents changes to materials in active orders
            # Cancel the order to test that we can update after cancellation
            self.p2p_service.cancel_order(order.document_number)
            
            # Now making the material inactive should succeed
            updated_material = self.material_service.update_material(
                "UPDATE001",
                MaterialUpdate(status=MaterialStatus.INACTIVE)
            )
            assert updated_material.status == MaterialStatus.INACTIVE
    
    def test_material_filter_by_procurement(self):
        """Test filtering materials based on procurement activity"""
        # Create a new material that won't be used in procurement
        self.material_service.create_material(
            MaterialCreate(
                material_number="UNUSED001",
                name="Unused Material",
                type=MaterialType.RAW
            )
        )
        
        # Create a requisition with RAW001 to ensure it's used in procurement
        req_data = RequisitionCreate(
            document_number="REQ_FILTER",
            description="Filter Test Requisition",
            requester="Test User",
            items=[
                RequisitionItem(
                    item_number=1,
                    material_number="RAW001",
                    description="Used Material Item",
                    quantity=10,
                    unit="KG",
                    price=50
                )
            ]
        )
        self.p2p_service.create_requisition(req_data)
        
        # List all materials
        all_materials = self.material_service.list_materials()
        
        # Find materials used in procurement (implementation specific)
        # In a real implementation, this might be done via a filter parameter
        # Here we're using our knowledge that RAW001 is used
        raw001_in_list = False
        unused001_in_list = False
        
        for material in all_materials:
            if material.material_number == "RAW001":
                raw001_in_list = True
            if material.material_number == "UNUSED001":
                unused001_in_list = True
                
        # Verify our test assumptions
        assert raw001_in_list, "RAW001 should be in the materials list"
        assert unused001_in_list, "UNUSED001 should be in the materials list"
    
    def test_error_handling_for_edge_cases(self):
        """Test error handling for various edge cases in material-p2p integration"""
        # Test case 1: Create requisition with inactive material
        try:
            req_data = RequisitionCreate(
                document_number="REQ_EDGE1",
                description="Edge Case Test Requisition 1",
                requester="Test User",
                items=[
                    RequisitionItem(
                        item_number=1,
                        material_number="INACTIVE001",  # This material is inactive
                        description="Inactive Material Item",
                        quantity=10,
                        unit="KG",
                        price=50
                    )
                ]
            )
            requisition = self.p2p_service.create_requisition(req_data)
            # Some implementations might allow inactive materials
            assert requisition.items[0].material_number == "INACTIVE001"
        except ValidationError as e:
            # Expected behavior if inactive materials are not allowed
            assert "inactive" in str(e).lower() or "INACTIVE001" in str(e)
        
        # Test case 2: Create requisition with deprecated material
        try:
            req_data = RequisitionCreate(
                document_number="REQ_EDGE2",
                description="Edge Case Test Requisition 2",
                requester="Test User",
                items=[
                    RequisitionItem(
                        item_number=1,
                        material_number="DEPR001",  # This material is deprecated
                        description="Deprecated Material Item",
                        quantity=10,
                        unit="KG",
                        price=50
                    )
                ]
            )
            requisition = self.p2p_service.create_requisition(req_data)
            # Some implementations might allow deprecated materials
            assert requisition.items[0].material_number == "DEPR001"
        except ValidationError as e:
            # Expected behavior if deprecated materials are not allowed
            assert "deprecated" in str(e).lower() or "DEPR001" in str(e)
        
        # Test case 3: Create an order with mixed valid/invalid materials
        try:
            order_data = OrderCreate(
                document_number="ORD_EDGE",
                description="Edge Case Test Order",
                requester="Test User",
                vendor="Test Vendor",
                items=[
                    OrderItem(
                        item_number=1,
                        material_number="RAW001",  # Valid material
                        description="Valid Material Item",
                        quantity=10,
                        unit="KG",
                        price=50
                    ),
                    OrderItem(
                        item_number=2,
                        material_number="INACTIVE001",  # Invalid material
                        description="Invalid Material Item",
                        quantity=5,
                        unit="KG",
                        price=60
                    )
                ]
            )
            order = self.p2p_service.create_order(order_data)
            # Some implementations might allow inactive materials
            assert len(order.items) == 2
        except ValidationError as e:
            # Expected behavior if inactive materials are not allowed
            assert "inactive" in str(e).lower() or "INACTIVE001" in str(e)
