import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import Request
from fastapi.responses import JSONResponse
from models.requisition import RequisitionCreate, DocumentStatus
from services.p2p_service import P2PService
from controllers.requisition_controller import api_create_requisition, api_submit_requisition, api_approve_requisition, api_reject_requisition

class TestP2PRequisitionAPI:
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

        # Mock the BaseController.create_success_response method
        with patch('controllers.BaseController.create_success_response') as mock_success_response:

            # Configure mock success response
            mock_success_response.return_value = JSONResponse(
                content={
                    "message": "Requisition REQ-001 created successfully",
                    "data": {"requisition": {"document_number": "REQ-001"}}
                },
                status_code=200
            )

            # Call the API endpoint
            response = await api_create_requisition(
                request=mock_request,
                requisition_data=requisition_data,
                p2p_service=self.mock_p2p_service,
                monitor_service=self.mock_monitor_service
            )

            # Verify the service was called correctly
            self.mock_p2p_service.create_requisition.assert_called_once_with(requisition_data)

            # Verify the success response was created
            mock_success_response.assert_called_once()
            _, kwargs = mock_success_response.call_args
            assert "created successfully" in kwargs["message"]

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

            # Verify the service was called correctly with exact parameters
            self.mock_p2p_service.reject_requisition.assert_called_once()
            args, kwargs = self.mock_p2p_service.reject_requisition.call_args
            assert args[0] == "REQ-001"
            assert kwargs.get("reason") == "Budget constraints" 