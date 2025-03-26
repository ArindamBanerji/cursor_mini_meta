# controllers/p2p_requisition_api_controller.py
"""
API controller for requisition endpoints.

This module handles all REST API routes for requisition management including:
- Listing requisitions (GET /api/v1/p2p/requisitions)
- Getting requisition details (GET /api/v1/p2p/requisitions/{document_number})
- Creating requisitions (POST /api/v1/p2p/requisitions)
- Updating requisitions (PUT /api/v1/p2p/requisitions/{document_number})
- Workflow state transitions (submit, approve, reject)
"""

from fastapi import Request, Depends, Response, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import logging

from models.p2p import (
    Requisition, RequisitionCreate, RequisitionUpdate, 
    DocumentStatus
)
from controllers import BaseController
from controllers.p2p_common import (
    get_p2p_service_dependency,
    get_monitor_service_dependency,
    get_material_service_dependency,
    RequisitionFilterParams
)
from controllers.p2p_requisition_common import (
    format_requisition_for_response,
    format_requisitions_list,
    log_requisition_error
)
from services import get_p2p_service, get_monitor_service
from services.p2p_service import P2PService
from services.monitor_service import MonitorService
from utils.error_utils import NotFoundError, ValidationError, BadRequestError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# P2P Requisition API Controller class for dependency injection
class P2PRequisitionAPIController:
    """P2P Requisition API controller class that handles requisition-related API operations."""
    
    def __init__(self, p2p_service=None, monitor_service=None):
        """Initialize with required services."""
        self.p2p_service = p2p_service or get_p2p_service()
        self.monitor_service = monitor_service or get_monitor_service()
    
    async def api_get_requisition(self, request: Request, requisition_id: str):
        """API endpoint to get a requisition by ID."""
        try:
            requisition = self.p2p_service.get_requisition(requisition_id)
            if not requisition:
                raise HTTPException(status_code=404, detail=f"Requisition {requisition_id} not found")
            return {"status": "success", "data": requisition}
        except Exception as e:
            logger.error(f"Error getting requisition {requisition_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def api_list_requisitions(self, request: Request):
        """API endpoint to list all requisitions."""
        try:
            requisitions = self.p2p_service.list_requisitions()
            return {"status": "success", "data": requisitions}
        except Exception as e:
            logger.error(f"Error listing requisitions: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def api_create_requisition(self, request: Request):
        """API endpoint to create a new requisition."""
        try:
            data = await request.json()
            requisition = self.p2p_service.create_requisition(data)
            return {
                "success": True,
                "status": "success", 
                "data": requisition,
                "message": "Requisition created successfully"
            }
        except ValidationError as e:
            log_requisition_error(self.monitor_service, e, request, "api_create_requisition")
            return JSONResponse(
                content={
                    "success": False,
                    "status": "error",
                    "message": str(e),
                    "error_code": "validation_error",
                    "details": getattr(e, "details", {})
                },
                status_code=400
            )
        except Exception as e:
            logger.error(f"Error creating requisition: {e}")
            log_requisition_error(self.monitor_service, e, request, "api_create_requisition")
            return JSONResponse(
                content={
                    "success": False,
                    "status": "error",
                    "message": f"Error creating requisition: {str(e)}",
                    "error_code": "server_error"
                },
                status_code=500
            )
    
    async def api_update_requisition(self, request: Request, requisition_id: str):
        """API endpoint to update an existing requisition."""
        try:
            data = await request.json()
            requisition = self.p2p_service.update_requisition(requisition_id, data)
            if not requisition:
                raise HTTPException(status_code=404, detail=f"Requisition {requisition_id} not found")
            return {"status": "success", "data": requisition}
        except Exception as e:
            logger.error(f"Error updating requisition {requisition_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def api_submit_requisition(self, request: Request, requisition_id: str):
        """API endpoint to submit a requisition for approval."""
        try:
            requisition = self.p2p_service.submit_requisition(requisition_id)
            return {
                "success": True,
                "data": {
                    "document_number": requisition.document_number,
                    "status": requisition.status.value
                },
                "message": f"Requisition {requisition_id} submitted successfully"
            }
        except NotFoundError as e:
            self.monitor_service.log_error(
                error_type="not_found_error",
                message=f"Requisition {requisition_id} not found in API submit request",
                component="p2p_requisition_api_controller",
                context={"document_number": requisition_id}
            )
            return {
                "success": False,
                "status": "error",
                "message": str(e),
                "error_code": "not_found",
                "details": {"document_number": requisition_id}
            }
        except ValidationError as e:
            log_requisition_error(self.monitor_service, e, request, "api_submit_requisition", requisition_id)
            return {
                "success": False,
                "status": "error",
                "message": str(e),
                "error_code": "validation_error",
                "details": getattr(e, "details", {})
            }
        except Exception as e:
            log_requisition_error(self.monitor_service, e, request, "api_submit_requisition", requisition_id)
            return {
                "success": False,
                "status": "error",
                "message": f"Error submitting requisition: {str(e)}",
                "error_code": "server_error"
            }
    
    async def api_approve_requisition(self, request: Request, document_number: str):
        """API endpoint to approve a requisition."""
        try:
            # Approve the requisition
            requisition = self.p2p_service.approve_requisition(document_number)
            
            # Format response
            response_data = {
                "success": True,
                "data": {
                    "document_number": requisition.document_number,
                    "status": requisition.status.value,
                    "updated_at": requisition.updated_at if isinstance(requisition.updated_at, str) else 
                                 (requisition.updated_at.isoformat() if hasattr(requisition, "updated_at") else None)
                },
                "message": f"Requisition {document_number} has been approved"
            }
            
            # Return success response
            return response_data
        except NotFoundError as e:
            # Log the not found error
            self.monitor_service.log_error(
                error_type="not_found_error",
                message=f"Requisition {document_number} not found in API approve request",
                component="p2p_requisition_api_controller",
                context={"document_number": document_number}
            )
            return {
                "success": False,
                "status": "error",
                "message": str(e),
                "error_code": "not_found",
                "details": {"document_number": document_number}
            }
        except ValidationError as e:
            log_requisition_error(self.monitor_service, e, request, "api_approve_requisition", document_number)
            return {
                "success": False,
                "status": "error",
                "message": str(e),
                "error_code": "validation_error",
                "details": getattr(e, "details", {})
            }
        except Exception as e:
            log_requisition_error(self.monitor_service, e, request, "api_approve_requisition", document_number)
            return {
                "success": False,
                "status": "error",
                "message": f"Error approving requisition: {str(e)}",
                "error_code": "server_error"
            }
    
    async def api_reject_requisition(self, request: Request, document_number: str):
        """API endpoint to reject a requisition."""
        try:
            # Parse request body for reason
            body_data = await BaseController.parse_json_body(request)
            reason = body_data.get("reason", "")
            
            if not reason:
                return {
                    "success": False,
                    "status": "error",
                    "message": "Rejection reason is required",
                    "error_code": "validation_error",
                    "details": {"reason": "This field is required"}
                }
            
            # Reject the requisition
            requisition = self.p2p_service.reject_requisition(document_number, reason)
            
            # Format response
            response_data = {
                "success": True,
                "data": {
                    "document_number": requisition.document_number,
                    "status": requisition.status.value,
                    "updated_at": requisition.updated_at if isinstance(requisition.updated_at, str) else 
                                 (requisition.updated_at.isoformat() if hasattr(requisition, "updated_at") else None),
                    "reason": reason
                },
                "message": f"Requisition {document_number} has been rejected"
            }
            
            # Return success response
            return response_data
        except NotFoundError as e:
            # Log the not found error
            self.monitor_service.log_error(
                error_type="not_found_error",
                message=f"Requisition {document_number} not found in API reject request",
                component="p2p_requisition_api_controller",
                context={"document_number": document_number}
            )
            return {
                "success": False,
                "status": "error",
                "message": str(e),
                "error_code": "not_found",
                "details": {"document_number": document_number}
            }
        except ValidationError as e:
            log_requisition_error(self.monitor_service, e, request, "api_reject_requisition", document_number)
            return {
                "success": False,
                "status": "error",
                "message": str(e),
                "error_code": "validation_error",
                "details": getattr(e, "details", {})
            }
        except Exception as e:
            log_requisition_error(self.monitor_service, e, request, "api_reject_requisition", document_number)
            return {
                "success": False,
                "status": "error",
                "message": f"Error rejecting requisition: {str(e)}",
                "error_code": "server_error"
            }

# Function to create a P2P requisition API controller instance
def get_p2p_requisition_api_controller(p2p_service=None, monitor_service=None):
    """Create a P2P requisition API controller instance.
    
    Args:
        p2p_service: The P2P service to use
        monitor_service: The monitor service to use
        
    Returns:
        A P2PRequisitionAPIController instance
    """
    return P2PRequisitionAPIController(
        p2p_service=p2p_service,
        monitor_service=monitor_service
    )

# API endpoint functions - these are wrappers around the controller methods
async def api_get_requisition(request: Request, requisition_id: str):
    """API endpoint to get a requisition by ID."""
    controller = get_p2p_requisition_api_controller()
    return await controller.api_get_requisition(request, requisition_id)

async def api_list_requisitions(request: Request):
    """API endpoint to list all requisitions."""
    controller = get_p2p_requisition_api_controller()
    return await controller.api_list_requisitions(request)

async def api_create_requisition(request: Request):
    """API endpoint to create a new requisition."""
    controller = get_p2p_requisition_api_controller()
    return await controller.api_create_requisition(request)

async def api_update_requisition(request: Request, requisition_id: str):
    """API endpoint to update an existing requisition."""
    controller = get_p2p_requisition_api_controller()
    return await controller.api_update_requisition(request, requisition_id)

async def api_submit_requisition(request: Request, requisition_id: str):
    """API endpoint to submit a requisition for approval."""
    controller = get_p2p_requisition_api_controller()
    return await controller.api_submit_requisition(request, requisition_id)

async def api_approve_requisition(
    request: Request,
    document_number: str,
    p2p_service=None,
    monitor_service=None
):
    """
    Approve a requisition (API endpoint).
    
    Args:
        request: FastAPI request
        document_number: Requisition document number
        p2p_service: Injected P2P service
        monitor_service: Injected monitor service
        
    Returns:
        JSON response with approval status
    """
    # Get services if not provided (for testing)
    if p2p_service is None:
        p2p_service = get_p2p_service()
    if monitor_service is None:
        monitor_service = get_monitor_service()
        
    try:
        # Approve the requisition
        requisition = p2p_service.approve_requisition(document_number)
        
        # Format response
        response_data = {
            "document_number": requisition.document_number,
            "status": requisition.status.value,
            "updated_at": requisition.updated_at if isinstance(requisition.updated_at, str) else 
                         (requisition.updated_at.isoformat() if hasattr(requisition, "updated_at") else None)
        }
        
        # Return success response
        return BaseController.create_success_response(
            data=response_data,
            message=f"Requisition {document_number} has been approved"
        )
    except NotFoundError as e:
        # Log the not found error
        monitor_service.log_error(
            error_type="not_found_error",
            message=f"Requisition {document_number} not found in API approve request",
            component="p2p_requisition_api_controller",
            context={"path": str(request.url), "document_number": document_number}
        )
        return BaseController.handle_api_error(e)
    except Exception as e:
        log_requisition_error(monitor_service, e, request, "api_approve_requisition", document_number)
        return BaseController.handle_api_error(e)

async def api_reject_requisition(
    request: Request,
    document_number: str,
    p2p_service=None,
    monitor_service=None
):
    """
    Reject a requisition (API endpoint).
    
    Args:
        request: FastAPI request
        document_number: Requisition document number
        p2p_service: Injected P2P service
        monitor_service: Injected monitor service
        
    Returns:
        JSON response with rejection status
    """
    # Get services if not provided (for testing)
    if p2p_service is None:
        p2p_service = get_p2p_service()
    if monitor_service is None:
        monitor_service = get_monitor_service()
        
    try:
        # Parse request body for reason
        body_data = await request.json()
        reason = body_data.get("reason", "")
        
        if not reason:
            return BaseController.create_error_response(
                message="Rejection reason is required",
                error_code="validation_error",
                details={"reason": "This field is required"},
                status_code=400
            )
        
        # Reject the requisition
        requisition = p2p_service.reject_requisition(document_number, reason)
        
        # Format response
        response_data = {
            "document_number": requisition.document_number,
            "status": requisition.status.value,
            "updated_at": requisition.updated_at if isinstance(requisition.updated_at, str) else 
                         (requisition.updated_at.isoformat() if hasattr(requisition, "updated_at") else None),
            "reason": reason
        }
        
        # Return success response
        return BaseController.create_success_response(
            data=response_data,
            message=f"Requisition {document_number} has been rejected"
        )
    except NotFoundError as e:
        # Log the not found error
        monitor_service.log_error(
            error_type="not_found_error",
            message=f"Requisition {document_number} not found in API reject request",
            component="p2p_requisition_api_controller",
            context={"path": str(request.url), "document_number": document_number}
        )
        return BaseController.handle_api_error(e)
    except Exception as e:
        log_requisition_error(monitor_service, e, request, "api_reject_requisition", document_number)
        return BaseController.handle_api_error(e)
