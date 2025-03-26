# controllers/p2p_requisition_common.py
"""
Common utilities specific to requisition handling.

This module provides specialized utilities for requisition operations,
including formatting functions, validation helpers, and error handling
specific to requisition processing.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, date

from fastapi import Request, Depends
from fastapi.responses import RedirectResponse

from models.p2p import (
    Requisition, RequisitionCreate, RequisitionUpdate, 
    DocumentStatus, RequisitionItem
)
from services.p2p_service import P2PService
from services.monitor_service import MonitorService
from services import get_p2p_service, get_monitor_service

from controllers import BaseController
from controllers.p2p_common import (
    format_timestamp, get_status_badge_color, 
    log_controller_error, RequisitionFilterParams
)
from utils.error_utils import NotFoundError, ValidationError, BadRequestError

# Configure logging
logger = logging.getLogger("p2p_requisition_controllers")

def format_requisition_for_response(requisition: Requisition) -> Dict[str, Any]:
    """
    Format a requisition object for response (both API and UI).
    
    Args:
        requisition: Requisition object
        
    Returns:
        Formatted requisition dictionary
    """
    return {
        "document_number": requisition.document_number,
        "description": requisition.description,
        "requester": requisition.requester,
        "department": requisition.department,
        "type": requisition.type.value,
        "status": requisition.status.value,
        "status_color": get_status_badge_color(requisition.status),
        "notes": requisition.notes,
        "urgent": requisition.urgent,
        "items": [format_requisition_item(item) for item in requisition.items],
        "total_value": requisition.total_value,
        "created_at": requisition.created_at.isoformat(),
        "updated_at": requisition.updated_at.isoformat(),
        "created_at_formatted": format_timestamp(requisition.created_at),
        "updated_at_formatted": format_timestamp(requisition.updated_at)
    }

def format_requisition_item(item: RequisitionItem) -> Dict[str, Any]:
    """
    Format a requisition item for response.
    
    Args:
        item: RequisitionItem object
        
    Returns:
        Formatted item dictionary
    """
    return {
        "item_number": item.item_number,
        "material_number": item.material_number,
        "description": item.description,
        "quantity": item.quantity,
        "unit": item.unit,
        "price": item.price,
        "currency": item.currency,
        "delivery_date": item.delivery_date.isoformat() if item.delivery_date else None,
        "status": item.status.value,
        "value": item.quantity * item.price,
        "assigned_to_order": item.assigned_to_order
    }

def format_requisitions_list(
    requisitions: List[Requisition], 
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format a list of requisitions for response.
    
    Args:
        requisitions: List of requisition objects
        filters: Optional filter criteria used
        
    Returns:
        Formatted requisitions list dictionary
    """
    return {
        "requisitions": [format_requisition_for_response(r) for r in requisitions],
        "count": len(requisitions),
        "filters": filters or {}
    }

def validate_requisition_items_input(items: List[Dict[str, Any]], material_service) -> List[Dict[str, str]]:
    """
    Validate requisition items from user input.
    
    Args:
        items: List of item dictionaries from form/API
        material_service: Material service for validation
        
    Returns:
        List of validation errors, empty if no errors
    """
    errors = []
    
    for i, item in enumerate(items):
        item_errors = {}
        
        # Validate required fields
        if not item.get("description"):
            item_errors["description"] = "Description is required"
        
        try:
            quantity = float(item.get("quantity", 0))
            if quantity <= 0:
                item_errors["quantity"] = "Quantity must be greater than 0"
        except (ValueError, TypeError):
            item_errors["quantity"] = "Quantity must be a valid number"
            
        try:
            price = float(item.get("price", 0))
            if price < 0:
                item_errors["price"] = "Price cannot be negative"
        except (ValueError, TypeError):
            item_errors["price"] = "Price must be a valid number"
            
        # Validate material if specified
        material_number = item.get("material_number")
        if material_number:
            try:
                material = material_service.get_material(material_number)
                if material.status == "DEPRECATED":
                    item_errors["material_number"] = "Deprecated materials cannot be used"
            except NotFoundError:
                item_errors["material_number"] = f"Material {material_number} not found"
            except Exception as e:
                item_errors["material_number"] = f"Error validating material: {str(e)}"
        
        if item_errors:
            errors.append({
                "item_index": i,
                "item_number": item.get("item_number", i+1),
                "errors": item_errors
            })
    
    return errors

def handle_requisition_not_found(document_number: str, request: Request) -> RedirectResponse:
    """
    Handle requisition not found errors consistently.
    
    Args:
        document_number: Requisition document number that wasn't found
        request: FastAPI request
        
    Returns:
        Redirect response to requisitions list with 303 See Other status
    """
    logger.warning(f"Requisition {document_number} not found, redirecting to list")
    
    # Return a redirect to the requisitions list with error message
    return BaseController.redirect_to_route(
        route_name="requisition_list",
        query_params={"error": f"Requisition {document_number} not found"},
        status_code=303  # Use 303 See Other for redirects after operations
    )

def log_requisition_error(
    monitor_service: MonitorService,
    e: Exception,
    request: Request,
    operation: str,
    document_number: Optional[str] = None
) -> None:
    """
    Log requisition controller errors consistently.
    
    Args:
        monitor_service: Monitor service for logging
        e: Exception that occurred
        request: FastAPI request
        operation: Operation that triggered the error
        document_number: Optional requisition document number for context
    """
    component = f"p2p_requisition_controller.{operation}"
    log_controller_error(monitor_service, e, request, component, document_number)
