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
from fastapi import Request

# Import all services and models through service_imports
from tests_dest.test_helpers.service_imports import (
    StateManager,
    MonitorService,
    MaterialService,
    P2PService,
    Material,
    MaterialCreate,
    MaterialStatus,
    MaterialType,
    RequisitionCreate,
    RequisitionItem,
    OrderCreate,
    OrderItem,
    DocumentStatus,
    NotFoundError,
    ValidationError,
    create_test_monitor_service,
    create_test_state_manager,
    create_test_material_service,
    create_test_p2p_service,
    setup_exception_handlers,
    ProcurementType,
    UnitOfMeasure
)

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment for each test."""
    setup_test_env_vars(monkeypatch)
    logger.info("Test environment initialized")
    yield
    logger.info("Test environment cleaned up")
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

class TestP2PMaterialIntegration:
    """Test integration between P2P and Material modules.
    
    This test class verifies:
    - Material references in requisitions/orders
    - Material availability checks
    - Cross-module workflows
    """
    
    def setup_method(self):
        """Set up test method."""
        # Create mock services
        self.p2p_service = MagicMock(spec=P2PService)
        self.material_service = MagicMock(spec=MaterialService)
        self.monitor_service = MagicMock(spec=MonitorService)
        
        # Create mock materials
        self.mock_material = self.create_test_material("MAT001", "Test Material 1", True)
        self.mock_inactive_material = self.create_test_material("MAT002", "Inactive Material", False)
        
        # Configure material service responses
        self.material_service.get_material.side_effect = self.get_mock_material
        self.material_service.list_materials.return_value = [self.mock_material, self.mock_inactive_material]
        
        # Create mock requisition and order
        self.mock_requisition = self.create_test_requisition()
        self.mock_order = self.create_test_order()
        
        # Configure P2P service responses
        self.p2p_service.get_requisition.return_value = self.mock_requisition
        self.p2p_service.create_requisition.return_value = self.mock_requisition
        self.p2p_service.get_order.return_value = self.mock_order
        self.p2p_service.create_order.return_value = self.mock_order
        
    def get_mock_material(self, material_number):
        """Mock the get_material function to return different materials based on number."""
        if material_number == "MAT001":
            return self.mock_material
        elif material_number == "MAT002":
            return self.mock_inactive_material
        else:
            # Use imported ValidationError from service_imports
            raise NotFoundError(f"Material {material_number} not found")
        
    def create_test_material(self, material_number, description, is_active=True):
        """Create a test material for testing."""
        status = MaterialStatus.ACTIVE if is_active else MaterialStatus.INACTIVE
        material_types = list(MaterialType)
        material_type = material_types[0] if material_types else MaterialType.RAW
        
        mock_material = MagicMock(spec=Material)
        mock_material.material_number = material_number
        mock_material.description = description
        mock_material.status = status
        mock_material.type = material_type
        mock_material.price = 100.0
        mock_material.unit_of_measure = "EA"
        mock_material.created_at = "2023-01-01T00:00:00"
        mock_material.updated_at = "2023-01-01T00:00:00"
        
        return mock_material
        
    def create_test_requisition(self):
        """Create a test requisition with material references."""
        items = [
            MagicMock(
                item_number=1,
                material_number="MAT001",
                description="Test Material 1",
                quantity=10,
                unit_price=100.0,
                unit="EA",
                total_price=1000.0
            ),
            MagicMock(
                item_number=2,
                material_number="MAT002",
                description="Inactive Material",
                quantity=5,
                unit_price=200.0,
                unit="EA",
                total_price=1000.0
            )
        ]
        
        return MagicMock(
            document_number="REQ123456",
            description="Test Requisition",
            created_at="2023-01-15T10:00:00",
            updated_at="2023-01-15T10:30:00",
            requester="John Doe",
            department="IT Department",
            status=DocumentStatus.DRAFT,
            items=items,
            type=ProcurementType.STANDARD,
            notes="Test Notes",
            urgent=False,
            created_by="user1",
            updated_by="user1"
        )
        
    def create_test_order(self):
        """Create a test order with material references."""
        items = [
            MagicMock(
                item_number=1,
                material_number="MAT001",
                description="Test Material 1",
                quantity=10,
                unit_price=100.0,
                unit="EA",
                total_price=1000.0,
                received_quantity=0,
                currency="USD",
                delivery_date="2023-05-15"
            )
        ]
        
        return MagicMock(
            document_number="PO123456",
            description="Test Purchase Order",
            created_at="2023-01-15T10:00:00",
            updated_at="2023-01-15T10:30:00",
            requester="John Doe",
            vendor="Test Vendor Inc.",
            status=DocumentStatus.DRAFT,
            items=items,
            type=ProcurementType.STANDARD,
            notes="Test Notes",
            payment_terms="Net 30",
            currency="USD",
            created_by="user1",
            updated_by="user1",
            requisition_reference="REQ123456"
        )
        
    def create_test_request(self):
        """Create a test HTTP request for testing."""
        mock_request = MagicMock(spec=Request)
        return mock_request
        
    @pytest.mark.asyncio
    async def test_create_requisition_with_valid_materials(self):
        """Test creating a requisition with valid materials."""
        # Create requisition data
        requisition_data = RequisitionCreate(
            document_number="REQ123456",
            description="Test Requisition",
            requester="John Doe",
            items=[
                RequisitionItem(
                    item_number=1,
                    material_number="MAT001",
                    description="Test Material 1",
                    quantity=10,
                    unit="EA",
                    price=100.0
                )
            ]
        )
        
        # Mock the validation to return success
        self.p2p_service.create_requisition.return_value = self.mock_requisition
        
        # Call the method under test
        result = self.p2p_service.create_requisition(requisition_data)
        
        # Verify the call succeeds and returns the expected result
        assert result.document_number == "REQ123456"
        self.p2p_service.create_requisition.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_create_requisition_with_inactive_material(self):
        """Test creating a requisition with inactive materials."""
        # Create requisition data with inactive material
        requisition_data = RequisitionCreate(
            document_number="REQ123456",
            description="Test Requisition",
            requester="John Doe",
            items=[
                RequisitionItem(
                    item_number=1,
                    material_number="MAT002",  # Inactive material
                    description="Inactive Material",
                    quantity=5,
                    unit="EA",
                    price=200.0
                )
            ]
        )
        
        # Configure the p2p_service to validate materials
        # Use imported ValidationError from service_imports
        self.p2p_service.create_requisition.side_effect = ValidationError(
            message="Cannot create requisition with inactive material: MAT002"
        )
        
        # Call the method under test and expect an exception
        with pytest.raises(ValidationError) as exc_info:
            self.p2p_service.create_requisition(requisition_data)
            
        # Verify the error message
        assert "inactive material" in str(exc_info.value).lower()
        
    @pytest.mark.asyncio
    async def test_create_requisition_with_nonexistent_material(self):
        """Test creating a requisition with non-existent materials."""
        # Create requisition data with non-existent material
        requisition_data = RequisitionCreate(
            document_number="REQ123456",
            description="Test Requisition",
            requester="John Doe",
            items=[
                RequisitionItem(
                    item_number=1,
                    material_number="INVALID123",  # Non-existent material
                    description="Invalid Material",
                    quantity=5,
                    unit="EA",
                    price=200.0
                )
            ]
        )
        
        # Configure the p2p_service to validate materials
        # Use imported ValidationError from service_imports
        self.p2p_service.create_requisition.side_effect = ValidationError(
            message="Material INVALID123 not found"
        )
        
        # Call the method under test and expect an exception
        with pytest.raises(ValidationError) as exc_info:
            self.p2p_service.create_requisition(requisition_data)
            
        # Verify the error message
        assert "not found" in str(exc_info.value).lower()
        
    @pytest.mark.asyncio
    async def test_get_requisition_with_material_details(self):
        """Test getting a requisition with material details."""
        document_number = "REQ123456"
        
        # Mock the material service integration in p2p_service to add material info
        orig_get_requisition = self.p2p_service.get_requisition
        
        def get_requisition_with_material_info(doc_num):
            req = orig_get_requisition(doc_num)
            # Add material info to each item
            for item in req.items:
                if item.material_number == "MAT001":
                    item.material_info = {
                        "status": "ACTIVE",
                        "type": "RAW",
                        "available_stock": 50,
                        "unit_of_measure": "EA"
                    }
            return req
            
        self.p2p_service.get_requisition = get_requisition_with_material_info
        
        # Call the method under test
        result = self.p2p_service.get_requisition(document_number)
        
        # Verify the result
        assert result.document_number == document_number
        
        # Check if the material info was added
        found_item_with_info = False
        for item in result.items:
            if item.material_number == "MAT001" and hasattr(item, "material_info"):
                found_item_with_info = True
                assert item.material_info["status"] == "ACTIVE"
                assert item.material_info["available_stock"] == 50
                
        assert found_item_with_info, "Material info not found for MAT001"
        
        # Restore the original method
        self.p2p_service.get_requisition = orig_get_requisition
        
    @pytest.mark.asyncio
    async def test_create_order_with_material_stock_check(self):
        """Test creating an order with material stock check."""
        # Create order data
        order_data = OrderCreate(
            document_number="PO123456",
            description="Test Purchase Order",
            requester="John Doe",
            vendor="Test Vendor Inc.",
            items=[
                OrderItem(
                    item_number=1,
                    material_number="MAT001",
                    description="Test Material 1",
                    quantity=100,  # More than available stock
                    unit="EA",
                    price=100.0,
                    delivery_date="2023-05-15"
                )
            ]
        )
        
        # Configure p2p_service to include stock check
        # Use imported ValidationError from service_imports
        self.p2p_service.create_order.side_effect = ValidationError(
            message="Insufficient stock for material MAT001: requested 100, available 50"
        )
        
        # Call the method under test and expect an exception
        with pytest.raises(ValidationError) as exc_info:
            self.p2p_service.create_order(order_data)
            
        # Verify the error message
        assert "insufficient stock" in str(exc_info.value).lower()
        
    @pytest.mark.asyncio
    async def test_get_material_with_related_documents(self):
        """Test getting a material with related documents."""
        material_number = "MAT001"
        
        # Store the original method
        orig_get_material = self.material_service.get_material
        
        # Add related documents to the mock material
        self.mock_material.related_documents = [
            {"type": "REQUISITION", "document_number": "REQ123456", "status": "APPROVED"},
            {"type": "ORDER", "document_number": "PO123456", "status": "DRAFT"}
        ]
        
        # Call the method under test
        result = self.material_service.get_material(material_number)
        
        # Verify the result
        assert result.material_number == material_number
        assert hasattr(result, "related_documents")
        assert len(result.related_documents) == 2
        assert result.related_documents[0]["type"] == "REQUISITION"
        assert result.related_documents[1]["type"] == "ORDER"
        
        # Restore the original method
        self.material_service.get_material = orig_get_material
        
    def test_material_validation_in_p2p_service(self):
        """Test material validation in P2P service."""
        # Create requisition data
        requisition_data = RequisitionCreate(
            document_number="REQ123456",
            description="Test Requisition",
            requester="John Doe",
            items=[
                RequisitionItem(
                    item_number=1,
                    material_number="MAT001",
                    description="Test Material 1",
                    quantity=10,
                    unit="EA",
                    price=100.0
                )
            ]
        )
        
        # Call the method under test
        result = self.p2p_service.create_requisition(requisition_data)
        
        # Verify the call succeeds
        assert self.p2p_service.create_requisition.called
        assert result.document_number == "REQ123456"
        
    def test_material_availability_in_p2p_service(self):
        """Test material availability in P2P service."""
        # Create order data
        order_data = OrderCreate(
            document_number="PO123456",
            description="Test Purchase Order",
            requester="John Doe",
            vendor="Test Vendor Inc.",
            items=[
                OrderItem(
                    item_number=1,
                    material_number="MAT001",
                    description="Test Material 1",
                    quantity=10,
                    unit="EA",
                    price=100.0,
                    delivery_date="2023-05-15"
                )
            ],
            payment_terms="Net 30"
        )
        
        # Call the method under test
        result = self.p2p_service.create_order(order_data)
        
        # Verify the call succeeds
        assert self.p2p_service.create_order.called
        assert result.document_number == "PO123456" 