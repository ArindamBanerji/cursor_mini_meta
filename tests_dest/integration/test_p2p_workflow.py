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
    Requisition,
    RequisitionCreate,
    RequisitionItem,
    Order,
    OrderCreate,
    OrderItem,
    DocumentStatus,
    ProcurementType,
    NotFoundError,
    ValidationError,
    BadRequestError,
    create_test_monitor_service,
    create_test_state_manager,
    setup_exception_handlers
)

# Add controller imports
from controllers.p2p_order_api_controller import P2POrderAPIController
from controllers.p2p_requisition_api_controller import P2PRequisitionAPIController

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment for each test."""
    setup_test_env_vars(monkeypatch)
    logger.info("Test environment initialized")
    yield
    logger.info("Test environment cleaned up")
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

class TestP2PWorkflow:
    """Test complete procurement workflows from requisition creation to order completion.
    
    This test class verifies:
    - End-to-end procurement workflows
    - State transitions
    - Integration between requisitions and orders
    """
    
    def setup_method(self):
        """Set up test method."""
        # Create mock services
        self.p2p_service = MagicMock(spec=P2PService)
        self.material_service = MagicMock(spec=MaterialService)
        self.monitor_service = MagicMock(spec=MonitorService)
        
        # Configure service responses
        self.p2p_service.list_requisitions.return_value = []
        self.p2p_service.list_orders.return_value = []
        
        # Set up document numbers for the workflow
        self.requisition_number = "REQ123456"
        self.order_number = "PO123456"
        
        # Set up mock workflow state tracking
        self.setup_workflow_state_tracking()
        
    def setup_workflow_state_tracking(self):
        """Set up service mocks to track document state changes."""
        # Mock get_requisition to return requisition with the current state
        def mock_get_requisition(document_number):
            if document_number != self.requisition_number:
                raise NotFoundError(f"Requisition {document_number} not found")
            return self.create_test_requisition(self.requisition_state)
        self.p2p_service.get_requisition.side_effect = mock_get_requisition
        
        # Mock submit_requisition to change requisition state
        def mock_submit_requisition(document_number):
            if document_number != self.requisition_number:
                raise NotFoundError(f"Requisition {document_number} not found")
            if self.requisition_state != DocumentStatus.DRAFT:
                raise ValidationError(f"Cannot submit requisition in {self.requisition_state} state")
            self.requisition_state = DocumentStatus.SUBMITTED
            return self.create_test_requisition(self.requisition_state)
        self.p2p_service.submit_requisition.side_effect = mock_submit_requisition
        
        # Mock approve_requisition to change requisition state
        def mock_approve_requisition(document_number, comment=None):
            if document_number != self.requisition_number:
                raise NotFoundError(f"Requisition {document_number} not found")
            if self.requisition_state != DocumentStatus.SUBMITTED:
                raise ValidationError(f"Cannot approve requisition in {self.requisition_state} state")
            self.requisition_state = DocumentStatus.APPROVED
            return self.create_test_requisition(self.requisition_state)
        self.p2p_service.approve_requisition.side_effect = mock_approve_requisition
        
        # Mock reject_requisition to change requisition state
        def mock_reject_requisition(document_number, reason):
            if document_number != self.requisition_number:
                raise NotFoundError(f"Requisition {document_number} not found")
            if self.requisition_state != DocumentStatus.SUBMITTED:
                raise ValidationError(f"Cannot reject requisition in {self.requisition_state} state")
            self.requisition_state = DocumentStatus.REJECTED
            return self.create_test_requisition(self.requisition_state)
        self.p2p_service.reject_requisition.side_effect = mock_reject_requisition
        
        # Mock create_order_from_requisition
        def mock_create_order_from_requisition(requisition_number, vendor, payment_terms):
            if requisition_number != self.requisition_number:
                raise NotFoundError(f"Requisition {requisition_number} not found")
            if self.requisition_state != DocumentStatus.APPROVED:
                raise ValidationError(f"Cannot create order from requisition in {self.requisition_state} state")
            self.order_state = DocumentStatus.DRAFT
            self.requisition_state = DocumentStatus.ORDERED
            mock_order = self.create_test_order(self.order_state)
            return mock_order
        self.p2p_service.create_order_from_requisition.side_effect = mock_create_order_from_requisition
        
        # Mock get_order
        def mock_get_order(document_number):
            if document_number != self.order_number or self.order_state is None:
                raise NotFoundError(f"Order {document_number} not found")
            return self.create_test_order(self.order_state)
        self.p2p_service.get_order.side_effect = mock_get_order
        
        # Mock submit_order
        def mock_submit_order(document_number):
            if document_number != self.order_number or self.order_state is None:
                raise NotFoundError(f"Order {document_number} not found")
            if self.order_state != DocumentStatus.DRAFT:
                raise ValidationError(f"Cannot submit order in {self.order_state} state")
            self.order_state = DocumentStatus.SUBMITTED
            return self.create_test_order(self.order_state)
        self.p2p_service.submit_order.side_effect = mock_submit_order
        
        # Mock approve_order
        def mock_approve_order(document_number, comment=None):
            if document_number != self.order_number or self.order_state is None:
                raise NotFoundError(f"Order {document_number} not found")
            if self.order_state != DocumentStatus.SUBMITTED:
                raise ValidationError(f"Cannot approve order in {self.order_state} state")
            self.order_state = DocumentStatus.APPROVED
            return self.create_test_order(self.order_state)
        self.p2p_service.approve_order.side_effect = mock_approve_order
        
        # Mock receive_order
        def mock_receive_order(document_number, receipt_data):
            if document_number != self.order_number or self.order_state is None:
                raise NotFoundError(f"Order {document_number} not found")
            if self.order_state != DocumentStatus.APPROVED:
                raise ValidationError(f"Cannot receive order in {self.order_state} state")
            
            # Check if fully received
            if all(item["received_quantity"] == item["quantity"] for item in receipt_data["items"]):
                self.order_state = DocumentStatus.RECEIVED
            else:
                self.order_state = DocumentStatus.PARTIALLY_RECEIVED
                
            return self.create_test_order(self.order_state)
        self.p2p_service.receive_order.side_effect = mock_receive_order
        
        # Mock complete_order
        def mock_complete_order(document_number):
            if document_number != self.order_number or self.order_state is None:
                raise NotFoundError(f"Order {document_number} not found")
            if self.order_state not in [DocumentStatus.RECEIVED, DocumentStatus.PARTIALLY_RECEIVED]:
                raise ValidationError(f"Cannot complete order in {self.order_state} state")
            self.order_state = DocumentStatus.COMPLETED
            return self.create_test_order(self.order_state)
        self.p2p_service.complete_order.side_effect = mock_complete_order
        
    def create_test_requisition(self, status=DocumentStatus.DRAFT):
        """Create a test requisition for testing with the specified status."""
        items = [
            MagicMock(
                item_number=1,
                material_number="MAT001",
                description="Test Material 1",
                quantity=10,
                unit_price=100.0,
                unit="EA",
                total_price=1000.0
            )
        ]
        
        return MagicMock(
            document_number=self.requisition_number,
            description="Test Requisition",
            created_at="2023-01-15T10:00:00",
            updated_at="2023-01-15T10:30:00",
            requester="John Doe",
            department="IT Department",
            status=status,
            items=items,
            type=ProcurementType.STANDARD,
            notes="Test Notes",
            urgent=False,
            created_by="user1",
            updated_by="user1"
        )
        
    def create_test_order(self, status=DocumentStatus.DRAFT):
        """Create a test order for testing with the specified status."""
        items = [
            MagicMock(
                item_number=1,
                material_number="MAT001",
                description="Test Material 1",
                quantity=10,
                unit_price=100.0,
                unit="EA",
                total_price=1000.0,
                received_quantity=0 if status in [DocumentStatus.DRAFT, DocumentStatus.SUBMITTED, DocumentStatus.APPROVED] else 10,
                currency="USD",
                delivery_date="2023-05-15"
            )
        ]
        
        return MagicMock(
            document_number=self.order_number,
            description="Test Order",
            created_at="2023-01-15T10:00:00",
            updated_at="2023-01-15T10:30:00",
            requester="John Doe",
            vendor="Test Vendor",
            payment_terms="Net 30",
            status=status,
            items=items,
            type=ProcurementType.STANDARD,
            notes="Test Notes",
            urgent=False,
            created_by="user1",
            updated_by="user1",
            requisition_reference=self.requisition_number
        )
        
    def create_test_request(self):
        """Create a test request object for testing."""
        mock_request = MagicMock(spec=Request)
        return mock_request
        
    @pytest.mark.asyncio
    async def test_complete_procurement_workflow(self):
        """Test a complete procurement workflow from requisition creation to order completion."""
        
        # Arrange
        mock_request = self.create_test_request()
        
        # Step 1: Create a requisition
        requisition_data = {
            "description": "Test Requisition",
            "requester": "John Doe",
            "department": "IT Department",
            "type": "STANDARD",
            "notes": "Test Notes",
            "urgent": False,
            "items": [
                {
                    "item_number": 1,
                    "material_number": "MAT001",
                    "description": "Test Material 1",
                    "quantity": 10,
                    "unit_price": 100.0,
                    "unit": "EA"
                }
            ]
        }
        
        # Mock create_requisition to return a requisition with proper document number
        def mock_create_requisition(data):
            self.requisition_state = DocumentStatus.DRAFT
            return self.create_test_requisition(self.requisition_state)
        self.p2p_service.create_requisition.side_effect = mock_create_requisition
        
        # Override the parse_json_body method for all API calls
        with patch("controllers.BaseController.parse_json_body") as mock_parse_json:
            # Set up mock for create requisition
            mock_parse_json.return_value = requisition_data
            
            # Create controller instances
            requisition_controller = P2PRequisitionAPIController(
                p2p_service=self.p2p_service,
                monitor_service=self.monitor_service
            )
            order_controller = P2POrderAPIController(
                p2p_service=self.p2p_service,
                monitor_service=self.monitor_service
            )
            
            # Act - Step 1: Create a requisition
            result = await requisition_controller.api_create_requisition(mock_request)
            assert result["success"] is True
            self.requisition_number = result["data"]["document_number"]
            
            # Step 2: Submit requisition
            mock_parse_json.return_value = {"comment": "Submit comment"}
            result = await requisition_controller.api_submit_requisition(mock_request, self.requisition_number)
            assert result["success"] is True
            
            # Step 3: Approve requisition
            mock_parse_json.return_value = {"comment": "Approval comment"}
            result = await requisition_controller.api_approve_requisition(mock_request, self.requisition_number)
            assert result["success"] is True
            
            # Step 4: Create order from requisition
            mock_parse_json.return_value = {"vendor": "Test Vendor", "payment_terms": "Net 30"}
            result = await order_controller.api_create_order_from_requisition(mock_request, self.requisition_number)
            assert result["success"] is True
            self.order_number = result["data"]["document_number"]
            
            # Step 5: Submit order
            mock_parse_json.return_value = {"comment": "Submit comment"}
            result = await order_controller.api_submit_order(mock_request, self.order_number)
            assert result["success"] is True
            
            # Step 6: Approve order
            mock_parse_json.return_value = {"comment": "Approval comment"}
            result = await order_controller.api_approve_order(mock_request, self.order_number)
            assert result["success"] is True
            
            # Step 7: Receive order
            mock_parse_json.return_value = {
                "items": [
                    {
                        "item_number": 1,
                        "quantity": 10,
                        "received_quantity": 10
                    }
                ]
            }
            result = await order_controller.api_receive_order(mock_request, self.order_number)
            assert result["success"] is True
            
            # Step 8: Complete order
            mock_parse_json.return_value = {"comment": "Completion comment"}
            result = await order_controller.api_complete_order(mock_request, self.order_number)
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_workflow_with_partial_receipt(self):
        """Test procurement workflow with partial receipt."""
        # Arrange
        mock_request = self.create_test_request()
        
        # Reset workflow state
        self.requisition_state = DocumentStatus.APPROVED
        self.order_state = DocumentStatus.APPROVED
        
        # Create controller instance
        order_controller = P2POrderAPIController(
            p2p_service=self.p2p_service,
            monitor_service=self.monitor_service
        )
        
        # Override the parse_json_body method for all API calls
        with patch("controllers.BaseController.parse_json_body") as mock_parse_json:
            # Act - Step 1: Receive partial quantity
            mock_parse_json.return_value = {
                "items": [
                    {
                        "item_number": 1,
                        "quantity": 10,
                        "received_quantity": 5  # Partial receipt
                    }
                ]
            }
            result = await order_controller.api_receive_order(mock_request, self.order_number)
            assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_invalid_workflow_transition(self):
        """Test invalid workflow transitions are prevented."""
        # Arrange
        mock_request = self.create_test_request()
        
        # Reset workflow state
        self.requisition_state = DocumentStatus.DRAFT
        self.order_state = None
        
        # Create controller instance
        requisition_controller = P2PRequisitionAPIController(
            p2p_service=self.p2p_service,
            monitor_service=self.monitor_service
        )
        
        # Try to approve requisition without submitting first
        with patch("controllers.BaseController.parse_json_body", return_value={"comment": "Approval comment"}):
            # Act & Assert
            result = await requisition_controller.api_approve_requisition(mock_request, self.requisition_number)
            
            # Should fail because requisition is in DRAFT state
            assert result["success"] is False
            assert "error" in result["status"].lower()
            assert "state" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_create_order_from_non_approved_requisition(self):
        """Test creating an order from a non-approved requisition."""
        # Arrange
        mock_request = self.create_test_request()
        
        # Reset workflow state to DRAFT
        self.requisition_state = DocumentStatus.DRAFT
        self.order_state = None
        
        # Create controller instance
        order_controller = P2POrderAPIController(
            p2p_service=self.p2p_service,
            monitor_service=self.monitor_service
        )
        
        # Try to create order from non-approved requisition
        with patch("controllers.BaseController.parse_json_body", return_value={"vendor": "Test Vendor", "payment_terms": "Net 30"}):
            # Act
            result = await order_controller.api_create_order_from_requisition(mock_request, self.requisition_number)
            
            # Assert
            assert result["success"] is False
            assert "error" in result["status"].lower()
            assert "state" in result["message"].lower()
    
    def test_requisition_to_order_state_tracking(self):
        """Test that requisition state is tracked when converted to order."""
        # Arrange
        requisition_number = self.requisition_number
        self.requisition_state = DocumentStatus.APPROVED
        
        # Act - Create order from requisition
        order = self.p2p_service.create_order_from_requisition(
            requisition_number=requisition_number,
            vendor="Test Vendor",
            payment_terms="Net 30"
        )
        
        # Assert
        # Verify order was created
        assert order is not None
        assert order.document_number == self.order_number
        assert order.requisition_reference == requisition_number
        
        # Verify requisition state changed to ORDERED
        assert self.requisition_state == DocumentStatus.ORDERED
        
        # Verify order is in DRAFT state
        assert self.order_state == DocumentStatus.DRAFT 