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

# Import services and models from service_imports
from tests_dest.test_helpers.service_imports import (
    BaseService, 
    MonitorService,
    BaseDataModel,
    Requisition, 
    RequisitionCreate, 
    RequisitionItem, 
    DocumentStatus, 
    ProcurementType
)

# tests_dest/api/test_p2p_requisition_api.py
import json
from datetime import datetime, date, timedelta
from fastapi.responses import JSONResponse

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
        
        # Create a serializable response content (dictionary instead of MagicMock)
        requisition_dict = {
            "document_number": "REQ-001",
            "description": "Test Requisition",
            "requester": "Test User",
            "department": "IT",
            "status": "DRAFT",
            "urgent": True,
            "items": [
                {
                    "item_number": 1,
                    "material_number": "MAT-001",
                    "description": "Test Material",
                    "quantity": 10,
                    "price": 25.0
                }
            ]
        }
        
        with patch('controllers.BaseController.parse_query_params', return_value=filter_params), \
             patch('controllers.p2p_requisition_api_controller.get_p2p_requisition_api_controller') as mock_get_controller:
            
            # Configure mock controller
            mock_controller = MagicMock()
            mock_controller.p2p_service = self.mock_p2p_service
            mock_controller.monitor_service = self.mock_monitor_service
            # Use AsyncMock for async methods
            mock_controller.api_list_requisitions = AsyncMock(return_value=JSONResponse(
                content={"status": "success", "data": [requisition_dict]},
                status_code=200
            ))
            mock_get_controller.return_value = mock_controller
            
            # Call the API endpoint
            response = await api_list_requisitions(request=mock_request)
            
            # Check the response
            assert isinstance(response, JSONResponse)
            assert response.status_code == 200
            
            # Verify the controller was called correctly
            mock_controller.api_list_requisitions.assert_called_once_with(mock_request)

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
        
        # Create a serializable response content (dictionary instead of MagicMock)
        requisition_dict = {
            "document_number": "REQ-001",
            "description": "Test Requisition",
            "requester": "Test User",
            "department": "IT",
            "status": "DRAFT",
            "urgent": True,
            "items": [
                {
                    "item_number": 1,
                    "material_number": "MAT-001",
                    "description": "Test Material",
                    "quantity": 10,
                    "price": 25.0
                }
            ]
        }
        
        with patch('controllers.BaseController.parse_query_params', return_value=filter_params), \
             patch('controllers.p2p_requisition_api_controller.get_p2p_requisition_api_controller') as mock_get_controller:
            
            # Configure mock controller
            mock_controller = MagicMock()
            mock_controller.p2p_service = self.mock_p2p_service
            mock_controller.monitor_service = self.mock_monitor_service
            # Use AsyncMock for async methods
            mock_controller.api_list_requisitions = AsyncMock(return_value={
                "status": "success", 
                "data": [requisition_dict]
            })
            mock_get_controller.return_value = mock_controller
            
            # Call the API endpoint
            response = await api_list_requisitions(request=mock_request)
            
            # Check the response is what we expect
            assert response["status"] == "success"
            assert len(response["data"]) == 1
            
            # Verify the controller was called correctly
            mock_controller.api_list_requisitions.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_api_list_requisitions_with_error(self):
        """Test listing requisitions with an error"""
        # Create mock request
        mock_request = MagicMock(spec=Request)

        # Set up error response
        error_response = JSONResponse(
            content={"error_code": "Test error"},
            status_code=500
        )

        # Setup HTTPException to be raised
        http_exception = HTTPException(status_code=500, detail="Test error")

        with patch('controllers.p2p_requisition_api_controller.get_p2p_requisition_api_controller') as mock_get_controller:
            # Configure mock controller to raise HTTPException
            mock_controller = MagicMock()
            mock_controller.api_list_requisitions = AsyncMock(side_effect=http_exception)
            mock_get_controller.return_value = mock_controller

            # Mock BaseController.handle_api_error for HTTPException
            with patch('controllers.BaseController.handle_api_error', return_value=error_response):
                # Call the API endpoint
                try:
                    await api_list_requisitions(request=mock_request)
                    assert False, "Expected HTTPException was not raised"
                except HTTPException as e:
                    # Verify the exception details
                    assert e.status_code == 500
                    assert e.detail == "Test error"

    @pytest.mark.asyncio
    async def test_api_get_requisition(self):
        """Test getting a requisition by document number"""
        # Create mock request
        mock_request = MagicMock(spec=Request)

        # Create a serializable response content (dictionary instead of MagicMock)
        requisition_dict = {
            "document_number": "REQ-001",
            "description": "Test Requisition",
            "requester": "Test User",
            "department": "IT",
            "status": "DRAFT",
            "urgent": True,
            "items": [
                {
                    "item_number": 1,
                    "material_number": "MAT-001",
                    "description": "Test Material",
                    "quantity": 10,
                    "price": 25.0
                }
            ]
        }

        with patch('controllers.p2p_requisition_api_controller.get_p2p_requisition_api_controller') as mock_get_controller:
            # Configure mock controller
            mock_controller = MagicMock()
            mock_controller.p2p_service = self.mock_p2p_service
            mock_controller.monitor_service = self.mock_monitor_service
            # Use AsyncMock for async methods
            mock_controller.api_get_requisition = AsyncMock(return_value=JSONResponse(
                content={"status": "success", "data": requisition_dict},
                status_code=200
            ))
            mock_get_controller.return_value = mock_controller
            
            # Call the API endpoint
            response = await api_get_requisition(
                request=mock_request,
                requisition_id="REQ-001"
            )
            
            # Check the response
            assert isinstance(response, JSONResponse)
            assert response.status_code == 200
            
            # Verify the controller was called correctly
            mock_controller.api_get_requisition.assert_called_once_with(mock_request, "REQ-001")

    @pytest.mark.asyncio
    async def test_api_get_requisition_not_found(self):
        """Test getting a non-existent requisition"""
        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.url = "http://testserver/api/v1/p2p/requisitions/REQ-999"

        # Set up error response
        error_response = JSONResponse(
            content={"error_code": "Requisition REQ-999 not found"},
            status_code=404
        )

        # Setup HTTPException to be raised
        http_exception = HTTPException(status_code=404, detail="Requisition REQ-999 not found")

        with patch('controllers.p2p_requisition_api_controller.get_p2p_requisition_api_controller') as mock_get_controller:
            # Configure mock controller to raise HTTPException
            mock_controller = MagicMock()
            mock_controller.api_get_requisition = AsyncMock(side_effect=http_exception)
            mock_get_controller.return_value = mock_controller

            # Mock BaseController.handle_api_error for HTTPException
            with patch('controllers.BaseController.handle_api_error', return_value=error_response):
                # Call the API endpoint
                try:
                    await api_get_requisition(
                        request=mock_request,
                        requisition_id="REQ-999"
                    )
                    assert False, "Expected HTTPException was not raised"
                except HTTPException as e:
                    # Verify the exception details
                    assert e.status_code == 404
                    assert e.detail == "Requisition REQ-999 not found"

    @pytest.mark.asyncio
    async def test_api_create_requisition(self):
        """Test creating a new requisition"""
        # Create mock request
        mock_request = MagicMock(spec=Request)

        # Create result dictionary instead of using MagicMock
        result_dict = {
            "message": "Requisition created successfully",
            "data": {
                "requisition": {
                    "document_number": "REQ-001"
                }
            }
        }

        with patch('controllers.p2p_requisition_api_controller.get_p2p_requisition_api_controller') as mock_get_controller:
            # Configure mock controller
            mock_controller = MagicMock()
            mock_controller.p2p_service = self.mock_p2p_service
            mock_controller.monitor_service = self.mock_monitor_service
            # Use AsyncMock for async methods
            mock_controller.api_create_requisition = AsyncMock(return_value=result_dict)
            mock_get_controller.return_value = mock_controller
            
            # Call the API endpoint
            response = await api_create_requisition(request=mock_request)
            
            # Check the response
            assert response is result_dict
            
            # Verify the controller was called correctly
            mock_controller.api_create_requisition.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_api_create_requisition_validation_error(self):
        """Test creating a requisition with validation error"""
        # Create mock request
        mock_request = MagicMock(spec=Request)

        # Set up error response
        error_response = JSONResponse(
            content={
                "error_code": "Validation error",
                "details": {"description": ["Field required"]}
            },
            status_code=422
        )

        # Setup HTTPException to be raised
        http_exception = HTTPException(
            status_code=422, 
            detail={"message": "Invalid requisition data", "errors": {"description": ["Field required"]}}
        )

        with patch('controllers.p2p_requisition_api_controller.get_p2p_requisition_api_controller') as mock_get_controller:
            # Configure mock controller to raise HTTPException
            mock_controller = MagicMock()
            mock_controller.api_create_requisition = AsyncMock(side_effect=http_exception)
            mock_get_controller.return_value = mock_controller

            # Mock BaseController.handle_api_error for HTTPException
            with patch('controllers.BaseController.handle_api_error', return_value=error_response):
                # Call the API endpoint
                try:
                    await api_create_requisition(request=mock_request)
                    assert False, "Expected HTTPException was not raised"
                except HTTPException as e:
                    # Verify the exception details
                    assert e.status_code == 422
                    assert "Invalid requisition data" in str(e.detail)

    @pytest.mark.asyncio
    async def test_api_update_requisition(self):
        """Test updating an existing requisition"""
        # Create mock request
        mock_request = MagicMock(spec=Request)

        # Create result dictionary instead of using MagicMock
        result_dict = {
            "message": "Requisition REQ-001 updated successfully",
            "data": {
                "requisition": {
                    "document_number": "REQ-001"
                }
            }
        }

        with patch('controllers.p2p_requisition_api_controller.get_p2p_requisition_api_controller') as mock_get_controller:
            # Configure mock controller
            mock_controller = MagicMock()
            mock_controller.p2p_service = self.mock_p2p_service
            mock_controller.monitor_service = self.mock_monitor_service
            # Use AsyncMock for async methods
            mock_controller.api_update_requisition = AsyncMock(return_value=result_dict)
            mock_get_controller.return_value = mock_controller
            
            # Call the API endpoint
            response = await api_update_requisition(
                request=mock_request,
                requisition_id="REQ-001"
            )
            
            # Check the response
            assert response is result_dict
            
            # Verify the controller was called correctly
            mock_controller.api_update_requisition.assert_called_once_with(mock_request, "REQ-001")

    @pytest.mark.asyncio
    async def test_api_submit_requisition(self):
        """Test submitting a requisition"""
        # Create mock request
        mock_request = MagicMock(spec=Request)

        # Create result dictionary instead of using MagicMock
        result_dict = {
            "message": "Requisition REQ-001 submitted successfully",
            "data": {
                "requisition": {
                    "document_number": "REQ-001",
                    "status": "SUBMITTED"
                }
            }
        }

        with patch('controllers.p2p_requisition_api_controller.get_p2p_requisition_api_controller') as mock_get_controller:
            # Configure mock controller
            mock_controller = MagicMock()
            mock_controller.p2p_service = self.mock_p2p_service
            mock_controller.monitor_service = self.mock_monitor_service
            # Use AsyncMock for async methods
            mock_controller.api_submit_requisition = AsyncMock(return_value=result_dict)
            mock_get_controller.return_value = mock_controller
            
            # Call the API endpoint
            response = await api_submit_requisition(
                request=mock_request,
                requisition_id="REQ-001"
            )
            
            # Check the response
            assert response is result_dict
            
            # Verify the controller was called correctly
            mock_controller.api_submit_requisition.assert_called_once_with(mock_request, "REQ-001")

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

        # Set up error response
        error_response = JSONResponse(
            content={
                "error_code": "Cannot submit requisition",
                "details": "Requisition is already submitted"
            },
            status_code=400
        )

        # Setup HTTPException to be raised
        http_exception = HTTPException(
            status_code=400, 
            detail="Cannot submit requisition: Requisition is already submitted"
        )

        with patch('controllers.p2p_requisition_api_controller.get_p2p_requisition_api_controller') as mock_get_controller:
            # Configure mock controller to raise HTTPException
            mock_controller = MagicMock()
            mock_controller.api_submit_requisition = AsyncMock(side_effect=http_exception)
            mock_get_controller.return_value = mock_controller

            # Mock BaseController.handle_api_error for HTTPException
            with patch('controllers.BaseController.handle_api_error', return_value=error_response):
                # Call the API endpoint
                try:
                    await api_submit_requisition(
                        request=mock_request,
                        requisition_id="REQ-001"
                    )
                    assert False, "Expected HTTPException was not raised"
                except HTTPException as e:
                    # Verify the exception details
                    assert e.status_code == 400
                    assert "Cannot submit requisition" in e.detail

def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Simple diagnostic test ===")
    print("Successfully executed test_p2p_requisition_api.py")
    print("All imports resolved correctly")
    return True

if __name__ == "__main__":
    run_simple_test()
