# controllers/p2p_common.py
"""
Common functionality shared by all P2P controllers.

This module provides shared utilities, dependency functions, 
error handling, and common data structures used throughout 
the P2P controllers (both UI and API).
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, date
from fastapi import Request, Depends
from pydantic import BaseModel, Field

from models.p2p import (
    Requisition, RequisitionCreate, RequisitionUpdate, 
    Order, OrderCreate, OrderUpdate,
    DocumentStatus, ProcurementType
)
from models.material import MaterialStatus

from services import get_p2p_service, get_monitor_service, get_material_service
from services.p2p_service import P2PService
from services.monitor_service import MonitorService
from services.material_service import MaterialService

from controllers import BaseController
from utils.error_utils import NotFoundError, ValidationError, BadRequestError, ConflictError

# Configure logging
logger = logging.getLogger("p2p_controllers")

# Service dependencies
def get_p2p_service_dependency():
    """Dependency for P2P service injection"""
    return Depends(get_p2p_service)

def get_monitor_service_dependency():
    """Dependency for monitor service injection"""
    return Depends(get_monitor_service)

def get_material_service_dependency():
    """Dependency for material service injection"""
    return Depends(get_material_service)

# Common error handling functions
def log_controller_error(
    monitor_service: MonitorService,
    e: Exception,
    request: Request,
    component: str,
    document_number: Optional[str] = None
) -> None:
    """
    Log controller errors consistently.
    
    Args:
        monitor_service: Monitor service for logging
        e: Exception that occurred
        request: FastAPI request
        component: Component name for logging
        document_number: Optional document number for context
    """
    # Build context
    context = {"path": str(request.url)}
    if document_number:
        context["document_number"] = document_number
    
    # Log the error
    logger.error(f"Error in {component}: {str(e)}", exc_info=True)
    monitor_service.log_error(
        error_type="controller_error",
        message=f"Error in {component}: {str(e)}",
        component="p2p_controller",
        context=context
    )

def handle_document_not_found(
    document_number: str,
    request: Request,
    document_type: str = "Document"
) -> Any:
    """
    Handle not found errors consistently.
    
    Args:
        document_number: Document number that was not found
        request: FastAPI request
        document_type: Type of document ("Requisition" or "Order")
        
    Returns:
        Redirect response to appropriate list with 303 See Other status
    """
    logger.warning(f"{document_type} {document_number} not found, redirecting to list")
    
    # Determine the route name based on document type
    route_name = "requisition_list" if document_type == "Requisition" else "order_list"
    
    # Return a redirect to the appropriate list with error message
    return BaseController.redirect_to_route(
        route_name=route_name,
        query_params={"error": f"{document_type} {document_number} not found"},
        status_code=303  # Use 303 See Other for redirects after operations
    )

# Common filter parameter models
class DocumentFilterParams(BaseModel):
    """Base parameters for document search and filtering"""
    search: Optional[str] = None
    status: Optional[DocumentStatus] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    limit: Optional[int] = Field(None, ge=1, le=100)
    offset: Optional[int] = Field(None, ge=0)

class RequisitionFilterParams(DocumentFilterParams):
    """Parameters for requisition search and filtering"""
    requester: Optional[str] = None
    department: Optional[str] = None
    urgent: Optional[bool] = None

class OrderFilterParams(DocumentFilterParams):
    """Parameters for order search and filtering"""
    vendor: Optional[str] = None
    requisition_reference: Optional[str] = None

# Common utility functions for formatting timestamps
def format_timestamp(dt: datetime) -> str:
    """Format a datetime for display in the UI"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def format_date(dt: date) -> str:
    """Format a date for display in the UI"""
    return dt.strftime("%Y-%m-%d")

# Document status style mappings
STATUS_BADGE_COLORS = {
    DocumentStatus.DRAFT: "secondary",
    DocumentStatus.SUBMITTED: "info",
    DocumentStatus.APPROVED: "primary",
    DocumentStatus.REJECTED: "danger",
    DocumentStatus.ORDERED: "success",
    DocumentStatus.RECEIVED: "success",
    DocumentStatus.PARTIALLY_RECEIVED: "warning",
    DocumentStatus.COMPLETED: "success",
    DocumentStatus.CANCELED: "dark"
}

def get_status_badge_color(status: DocumentStatus) -> str:
    """Get the appropriate Bootstrap color class for a status badge"""
    return STATUS_BADGE_COLORS.get(status, "secondary")
