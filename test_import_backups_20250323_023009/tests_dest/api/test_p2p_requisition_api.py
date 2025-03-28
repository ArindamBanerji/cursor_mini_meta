# Add path setup to find the tests_dest module
import sys
import os
from pathlib import Path

# Add parent directory to path so Python can find the tests_dest module
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent  # Go up two levels to reach project root
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import helper to fix path issues
from tests_dest.import_helper import fix_imports
fix_imports()
# Import helper to fix path issues
from tests_dest.import_helper import fix_imports
fix_imports()

import pytest
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Optional imports - these might fail but won't break tests
try:
    from services.base_service import BaseService
    from services.monitor_service import MonitorService
    from models.base_model import BaseModel
except ImportError as e:
    logger.warning(f"Optional import failed: {e}")


# tests_dest/api/test_p2p_requisition_api.py
import json
from datetime import datetime, date, timedelta
from fastapi.responses import JSONResponse

from models.p2p import (
    Requisition, RequisitionCreate, RequisitionItem, 
    DocumentStatus, ProcurementType
)
from utils.error_utils import NotFoundError, ValidationError, BadRequestError
from controllers.p2p_requisition_api_controller import (
    api_list_requisitions,
    api_get_requisition,
    api_create_requisition,
    api_update_requisition,
    api_submit_requisition,
    api_approve_requisition,
    api_reject_requisition
)

class TestRequisitionAPIEndpoints:
    """Tests for the requisition API endpoints"""

    def setup_method(self):
        """Set up test data and mocks for each test"""
        # Create mock requisition item
        self.mock_item = MagicMock(spec=RequisitionItem)
        self.mock_item.item_number = 1
        self.mock_item.material_number = "MAT-001"
        self.mock_item.description = "Test Material"
        self.mock_item.quantity = 10
        self.mock_item.unit = "EA"
        self.mock_item.price = 25.0
        self.mock_item.currency = "USD"
        self.mock_item.delivery_date = date(2023, 6, 1)
        self.mock_item.status = DocumentStatus.APPROVED
        self.mock_item.assigned_to_order = None

        # Create mock requisition
        self.mock_requisition = MagicMock(spec=Requisition)
        self.mock_requisition.document_number = "REQ-001"
        self.mock_requisition.description = "Test Requisition"
        self.mock_requisition.requester = "Test User"
        self.mock_requisition.department = "IT"
        self.mock_requisition.type = ProcurementType.STANDARD
        self.mock_requisition.status = DocumentStatus.DRAFT
        self.mock_requisition.notes = "Test notes"
        self.mock_requisition.urgent = True
        self.mock_requisition.items = [self.mock_item]
        self.mock_requisition.total_value = 250.0
        self.mock_requisition.created_at = datetime(2023, 5, 1, 12, 0, 0)
        self.mock_requisition.updated_at = datetime(2023, 5, 2, 14, 30, 0)

        # Create mock services
        self.mock_p2p_service = MagicMock()
        self.mock_monitor_service = MagicMock()

        # Configure mock P2P service
        self.mock_p2p_service.get_requisition.return_value = self.mock_requisition
        self.mock_p2p_service.list_requisitions.return_value = [self.mock_requisition]
        self.mock_p2p_service.create_requisition.return_value = self.mock_requisition
        self.mock_p2p_service.update_requisition.return_value = self.mock_requisition
        self.mock_p2p_service.submit_requisition.return_value = self.mock_requisition
        self.mock_p2p_service.approve_requisition.return_value = self.mock_requisition
        self.mock_p2p_service.reject_requisition.return_value = self.mock_requisition

    @pytest.mark.asyncio
    async def test_api_list_requisitions(self):
        """Test listing requisitions"""
        # Create mock request
        mock_request = MagicMock(spec=Request)
        
        # Mock the BaseController.parse_query_params method
        filter_params = MagicMock()
        filter_params.status = None
        filter_params.requester = None
        filter_params.department = None
        filter_params.search = None
        filter_params.date_from = None
        filter_params.date_to = None
        filter_params.limit = None
        filter_params.offset = None
        
        with patch('controllers.BaseController.parse_query_params', return_value=filter_params):
            # Call the API endpoint
            response = await api_list_requisitions(
                request=mock_request,
                p2p_service=self.mock_p2p_service,
                monitor_service=self.mock_monitor_service
            )
            
            # Check the response
            assert isinstance(response, JSONResponse)
            content = response.body.decode('utf-8')
            data = json.loads(content)
            
            # Verify the service was called correctly
            self.mock_p2p_service.list_requisitions.assert_called_once_with(
                status=None,
                requester=None,
                department=None,
                search_term=None,
                date_from=None,
                date_to=None
            )
            
            # Verify the response data
            assert data["count"] == 1
            assert data["filters"] == {
                "search": None,
                "status": None,
                "requester": None,
                "department": None,
                "date_from": None,
                "date_to": None,
                "limit": None,
                "offset": None
            }
            assert len(data["requisitions"]) == 1
            req = data["requisitions"][0]
            assert req["document_number"] == "REQ-001"
            assert req["description"] == "Test Requisition"

    @pytest.mark.asyncio
    async def test_api_list_requisitions_with_filters(self):
        """Test listing requisitions with filters"""
        # Create mock request
        mock_request = MagicMock(spec=Request)
        
        # Mock the BaseController.parse_query_params method
        filter_params = MagicMock()
        filter_params.status = DocumentStatus.DRAFT
        filter_params.requester = "Test User"
        filter_params.department = "IT"
        filter_params.search = "Test"
        filter_params.date_from = date(2023, 1, 1)
        filter_params.date_to = date(2023, 12, 31)
        filter_params.limit = 10
        filter_params.offset = 0
        
        with patch('controllers.BaseController.parse_query_params', return_value=filter_params):
            # Call the API endpoint
            response = await api_list_requisitions(
                request=mock_request,
                p2p_service=self.mock_p2p_service,
                monitor_service=self.mock_monitor_service
            )
            
            # Check the response
            assert isinstance(response, JSONResponse)
            content = response.body.decode('utf-8')
            data = json.loads(content)
            
            # Verify the service was called correctly
            self.mock_p2p_service.list_requisitions.assert_called_once_with(
                status=DocumentStatus.DRAFT,
                requester="Test User",
                department="IT",
                search_term="Test",
                date_from=date(2023, 1, 1),
                date_to=date(2023, 12, 31)
            )
            
            # Verify the response data
            assert data["count"] == 1
            assert data["filters"]["status"] == "DRAFT"
            assert data["filters"]["requester"] == "Test User"
            assert data["filters"]["department"] == "IT"
            assert data["filters"]["search"] == "Test"
            assert data["filters"]["date_from"] == "2023-01-01"
            assert data["filters"]["date_to"] == "2023-12-31"
            assert data["filters"]["limit"] == 10
            assert data["filters"]["offset"] == 0

    @pytest.mark.asyncio
    async def test_api_list_requisitions_with_error(self):
        """Test listing requisitions with an error"""
        # Create mock request
        mock_request = MagicMock(spec=Request)
        
        # Set up P2P service to raise an exception
        self.mock_p2p_service.list_requisitions.side_effect = Exception("Test error")
        
        # Mock the BaseController methods
        with patch('controllers.BaseController.parse_query_params') as mock_parse_params, \
             patch('controllers.BaseController.handle_api_error') as mock_handle_error:
            
            # Configure mocks
            mock_parse_params.return_value = MagicMock()
            mock_handle_error.return_value = JSONResponse(content={"error_code": "Test error"}, status_code=500)
            
            # Call the API endpoint
            response = await api_list_requisitions(
                request=mock_request,
                p2p_service=self.mock_p2p_service,
                monitor_service=self.mock_monitor_service
            )
            
            # Verify error was logged
            self.mock_monitor_service.log_error.assert_called_once()
            
            # Verify error was handled
            mock_handle_error.assert_called_once()
            
            # Check the response
            assert response.status_code == 500
            content = response.body.decode('utf-8')
            data = json.loads(content)
            assert data["error"] == "Test error"

    @pytest.mark.asyncio
    async def test_api_get_requisition(self):
        """Test getting a requisition by document number"""
        # Create mock request
        mock_request = MagicMock(spec=Request)
        
        # Call the API endpoint
        response = await api_get_requisition(
            request=mock_request,
            document_number="REQ-001",
            p2p_service=self.mock_p2p_service,
            monitor_service=self.mock_monitor_service
        )
        
        # Check the response
        assert isinstance(response, JSONResponse)
        content = response.body.decode('utf-8')
        data = json.loads(content)
        
        # Verify the service was called correctly
        self.mock_p2p_service.get_requisition.assert_called_once_with("REQ-001")
        
        # Verify the response data
        assert data["document_number"] == "REQ-001"
        assert data["description"] == "Test Requisition"
        assert data["status"] == "DRAFT"
        assert data["urgent"] is True
        assert len(data["items"]) == 1
        
        # Check item data
        item = data["items"][0]
        assert item["item_number"] == 1
        assert item["material_number"] == "MAT-001"
        assert item["description"] == "Test Material"
        assert item["quantity"] == 10
        assert item["price"] == 25.0

    @pytest.mark.asyncio
    async def test_api_get_requisition_not_found(self):
        """Test getting a non-existent requisition"""
        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.url = "http://testserver/api/v1/p2p/requisitions/REQ-999"
        
        # Set up P2P service to raise NotFoundError
        self.mock_p2p_service.get_requisition.side_effect = NotFoundError("Requisition REQ-999 not found")
        
        # Mock the BaseController.handle_api_error method
        with patch('controllers.BaseController.handle_api_error') as mock_handle_error:
            # Configure mock
            mock_handle_error.return_value = JSONResponse(
                content={"error_code": "Requisition REQ-999 not found"}, 
                status_code=404
            )
            
            # Call the API endpoint
            response = await api_get_requisition(
                request=mock_request,
                document_number="REQ-999",
                p2p_service=self.mock_p2p_service,
                monitor_service=self.mock_monitor_service
            )
            
            # Verify error was logged
            self.mock_monitor_service.log_error.assert_called_once_with(
                error_type="not_found_error",
                message="Requisition REQ-999 not found in API request",
                component="p2p_requisition_api_controller",
                context={"path": str(mock_request.url), "document_number": "REQ-999"}
            )
            
            # Verify error was handled
            mock_handle_error.assert_called_once()
            
            # Check the response
            assert response.status_code == 404
            content = response.body.decode('utf-8')
            data = json.loads(content)
            assert data["error"] == "Requisition REQ-999 not found"

    @pytest.mark.asyncio
    async def test_api_create_requisition(self):
        """Test creating a new requisition"""
        # Create mock request
        mock_request = MagicMock(spec=Request)
        
        # Create requisition data
        requisition_data = RequisitionCreate(
            description="New Requisition",
            requester="New User",
            department="HR",
            type=ProcurementType.STANDARD,
            notes="Creation test",
            urgent=False,
            items=[{
                "item_number": "001",
                "material_number": "MAT-002",
                "description": "New Material",
                "quantity": 5,
                "unit": "EA",
                "price": 20.0,
                "currency": "USD"
            }]
        )
        
        # Mock the BaseController.parse_json_body method
        with patch('controllers.BaseController.parse_json_body', return_value=requisition_data), \
             patch('controllers.BaseController.create_success_response') as mock_success_response:
            
            # Configure mock success response
            mock_success_response.return_value = JSONResponse(
                content={
                    "message": "Requisition created successfully",
                    "data": {"requisition": {"document_number": "REQ-001"}}
                },
                status_code=201
            )
            
            # Call the API endpoint
            response = await api_create_requisition(
                request=mock_request,
                p2p_service=self.mock_p2p_service,
                monitor_service=self.mock_monitor_service
            )
            
            # Verify the service was called correctly
            self.mock_p2p_service.create_requisition.assert_called_once_with(requisition_data)
            
            # Verify the success response was created
            mock_success_response.assert_called_once()
            _, kwargs = mock_success_response.call_args
            assert kwargs["status_code"] == 201
            assert "Requisition created successfully" in kwargs["message"]
            assert "requisition" in kwargs["data"]
            
            # Check the response
            assert response.status_code == 201
            content = response.body.decode('utf-8')
            data = json.loads(content)
            assert data["message"] == "Requisition created successfully"
            assert "requisition" in data["data"]

    @pytest.mark.asyncio
    async def test_api_create_requisition_validation_error(self):
        """Test creating a requisition with validation error"""
        # Create mock request
        mock_request = MagicMock(spec=Request)
        
        # Set up BaseController to raise ValidationError
        validation_error = ValidationError("Invalid requisition data", {"description": ["Field required"]})
        
        with patch('controllers.BaseController.parse_json_body', side_effect=validation_error), \
             patch('controllers.BaseController.handle_api_error') as mock_handle_error:
            
            # Configure mock
            mock_handle_error.return_value = JSONResponse(
                content={
                    "error_code": "Validation error",
                    "details": {"description": ["Field required"]}
                },
                status_code=422
            )
            
            # Call the API endpoint
            response = await api_create_requisition(
                request=mock_request,
                p2p_service=self.mock_p2p_service,
                monitor_service=self.mock_monitor_service
            )
            
            # Verify error was logged
            self.mock_monitor_service.log_error.assert_called_once()
            
            # Verify error was handled
            mock_handle_error.assert_called_once_with(validation_error)
            
            # Check the response
            assert response.status_code == 422
            content = response.body.decode('utf-8')
            data = json.loads(content)
            assert data["error"] == "Validation error"
            assert data["details"]["description"] == ["Field required"]

    @pytest.mark.asyncio
    async def test_api_update_requisition(self):
        """Test updating an existing requisition"""
        # Create mock request
        mock_request = MagicMock(spec=Request)
        
        # Create update data
        update_data = MagicMock()
        update_data.description = "Updated Requisition"
        update_data.notes = "Update test"
        
        # Mock the BaseController methods
        with patch('controllers.BaseController.parse_json_body', return_value=update_data), \
             patch('controllers.BaseController.create_success_response') as mock_success_response:
            
            # Configure mock success response
            mock_success_response.return_value = JSONResponse(
                content={
                    "message": "Requisition REQ-001 updated successfully",
                    "data": {"requisition": {"document_number": "REQ-001"}}
                },
                status_code=200
            )
            
            # Call the API endpoint
            response = await api_update_requisition(
                request=mock_request,
                document_number="REQ-001",
                p2p_service=self.mock_p2p_service,
                monitor_service=self.mock_monitor_service
            )
            
            # Verify the service was called correctly
            self.mock_p2p_service.update_requisition.assert_called_once_with("REQ-001", update_data)
            
            # Verify the success response was created
            mock_success_response.assert_called_once()
            _, kwargs = mock_success_response.call_args
            assert "REQ-001 updated successfully" in kwargs["message"]
            assert "requisition" in kwargs["data"]
            
            # Check the response
            assert response.status_code == 200
            content = response.body.decode('utf-8')
            data = json.loads(content)
            assert data["message"] == "Requisition REQ-001 updated successfully"
            assert "requisition" in data["data"]

    @pytest.mark.asyncio
    async def test_api_submit_requisition(self):
        """Test submitting a requisition"""
        # Create mock request
        mock_request = MagicMock(spec=Request)
        
        # Update mock requisition status for the response
        self.mock_requisition.status = DocumentStatus.SUBMITTED
        
        # Mock the BaseController.create_success_response method
        with patch('controllers.BaseController.create_success_response') as mock_success_response:
            # Configure mock success response
            mock_success_response.return_value = JSONResponse(
                content={
                    "message": "Requisition REQ-001 submitted successfully",
                    "data": {"requisition": {"document_number": "REQ-001", "status": "SUBMITTED"}}
                },
                status_code=200
            )
            
            # Call the API endpoint
            response = await api_submit_requisition(
                request=mock_request,
                document_number="REQ-001",
                p2p_service=self.mock_p2p_service,
                monitor_service=self.mock_monitor_service
            )
            
            # Verify the service was called correctly
            self.mock_p2p_service.submit_requisition.assert_called_once_with("REQ-001")
            
            # Verify the success response was created
            mock_success_response.assert_called_once()
            _, kwargs = mock_success_response.call_args
            assert "submitted for approval" in kwargs["message"]

    @pytest.mark.asyncio
    async def test_api_approve_requisition(self):
        """Test approving a requisition"""
        # Create mock request
        mock_request = MagicMock(spec=Request)
        
        # Update mock requisition status for the response
        self.mock_requisition.status = DocumentStatus.APPROVED
        
        # Mock the BaseController.create_success_response method
        with patch('controllers.BaseController.create_success_response') as mock_success_response:
            # Configure mock success response
            mock_success_response.return_value = JSONResponse(
                content={
                    "message": "Requisition REQ-001 approved successfully",
                    "data": {"requisition": {"document_number": "REQ-001", "status": "APPROVED"}}
                },
                status_code=200
            )
            
            # Call the API endpoint
            response = await api_approve_requisition(
                request=mock_request,
                document_number="REQ-001",
                p2p_service=self.mock_p2p_service,
                monitor_service=self.mock_monitor_service
            )
            
            # Verify the service was called correctly
            self.mock_p2p_service.approve_requisition.assert_called_once_with("REQ-001")
            
            # Verify the success response was created
            mock_success_response.assert_called_once()
            _, kwargs = mock_success_response.call_args
            assert "has been approved" in kwargs["message"]

    @pytest.mark.asyncio
    async def test_api_reject_requisition(self):
        """Test rejecting a requisition"""
        # Create mock request
        mock_request = MagicMock(spec=Request)
        
        # Update mock requisition status for the response
        self.mock_requisition.status = DocumentStatus.REJECTED
        
        # Mock JSON body data
        json_data = {"reason": "Budget constraints"}
        
        # Mock the BaseController methods
        with patch('controllers.BaseController.parse_json_body', return_value=json_data), \
             patch('controllers.BaseController.create_success_response') as mock_success_response:
            # Configure mock success response
            mock_success_response.return_value = JSONResponse(
                content={
                    "message": "Requisition REQ-001 rejected successfully",
                    "data": {"requisition": {"document_number": "REQ-001", "status": "REJECTED"}}
                },
                status_code=200
            )
            
            # Set up mock_p2p_service.reject_requisition
            self.mock_p2p_service.reject_requisition.return_value = self.mock_requisition
            
            # Call the API endpoint
            response = await api_reject_requisition(
                request=mock_request,
                document_number="REQ-001",
                p2p_service=self.mock_p2p_service,
                monitor_service=self.mock_monitor_service
            )
            
            # Access the mock directly to check call
            call_args = self.mock_p2p_service.reject_requisition.call_args
            assert call_args is not None
            args = call_args[0]
            assert args[0] == "REQ-001"
            
            # Verify the success response was created
            mock_success_response.assert_called_once()
            _, kwargs = mock_success_response.call_args
            assert "rejected" in kwargs["message"]

    @pytest.mark.asyncio
    async def test_api_workflow_state_error(self):
        """Test workflow state transition error"""
        # Create mock request
        mock_request = MagicMock(spec=Request)
        
        # Set up P2P service to raise BadRequestError
        self.mock_p2p_service.submit_requisition.side_effect = BadRequestError(
            "Cannot submit requisition", 
            "Requisition is already submitted"
        )
        
        # Mock the BaseController.handle_api_error method
        with patch('controllers.BaseController.handle_api_error') as mock_handle_error:
            # Configure mock
            mock_handle_error.return_value = JSONResponse(
                content={
                    "error_code": "Cannot submit requisition",
                    "details": "Requisition is already submitted"
                },
                status_code=400
            )
            
            # Call the API endpoint
            response = await api_submit_requisition(
                request=mock_request,
                document_number="REQ-001",
                p2p_service=self.mock_p2p_service,
                monitor_service=self.mock_monitor_service
            )
            
            # Verify error was logged
            self.mock_monitor_service.log_error.assert_called_once()
            
            # Verify error was handled
            mock_handle_error.assert_called_once()
            
            # Check the response
            assert response.status_code == 400
            content = response.body.decode('utf-8')
            data = json.loads(content)
            assert data["error"] == "Cannot submit requisition"
            assert data["details"] == "Requisition is already submitted" 
def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Simple diagnostic test ===")
    print("Successfully executed test_p2p_requisition_api.py")
    print("All imports resolved correctly")
    return True

if __name__ == "__main__":
    run_simple_test()
