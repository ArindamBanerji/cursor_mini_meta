# controllers/p2p_order_common.py
"""
Common utilities specific to order handling.

This module provides specialized utilities for order operations,
including formatting functions, validation helpers, and error handling
specific to order processing.
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, date

from fastapi import Request, Depends
from fastapi.responses import RedirectResponse

from models.p2p import (
    Order, OrderCreate, OrderUpdate, 
    DocumentStatus, OrderItem
)
from services.p2p_service import P2PService
from services.monitor_service import MonitorService
from services import get_p2p_service, get_monitor_service

from controllers import BaseController
from controllers.p2p_common import (
    format_timestamp, get_status_badge_color, 
    log_controller_error, OrderFilterParams
)
from utils.error_utils import NotFoundError, ValidationError, BadRequestError

# Configure logging
logger = logging.getLogger("p2p_order_controllers")

def format_order_for_response(order: Order) -> Dict[str, Any]:
    """
    Format an order object for response (both API and UI).
    
    Args:
        order: Order object
        
    Returns:
        Formatted order dictionary
    """
    return {
        "document_number": order.document_number,
        "description": order.description,
        "requester": order.requester,
        "vendor": order.vendor,
        "payment_terms": order.payment_terms,
        "type": order.type.value,
        "status": order.status.value,
        "status_color": get_status_badge_color(order.status),
        "notes": order.notes,
        "urgent": order.urgent,
        "items": [format_order_item(item) for item in order.items],
        "total_value": order.total_value,
        "requisition_reference": order.requisition_reference,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
        "created_at_formatted": format_timestamp(order.created_at),
        "updated_at_formatted": format_timestamp(order.updated_at)
    }

def format_order_item(item: OrderItem) -> Dict[str, Any]:
    """
    Format an order item for response.
    
    Args:
        item: OrderItem object
        
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
        "received_quantity": item.received_quantity,
        "remaining_quantity": item.quantity - item.received_quantity,
        "requisition_reference": item.requisition_reference,
        "requisition_item": item.requisition_item
    }

def format_orders_list(
    orders: List[Order], 
    filters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format a list of orders for response.
    
    Args:
        orders: List of order objects
        filters: Optional filter criteria used
        
    Returns:
        Formatted orders list dictionary
    """
    return {
        "orders": [format_order_for_response(o) for o in orders],
        "count": len(orders),
        "filters": filters or {}
    }

def handle_order_not_found(document_number: str, request: Request) -> RedirectResponse:
    """
    Handle order not found errors consistently.
    
    Args:
        document_number: Order document number that wasn't found
        request: FastAPI request
        
    Returns:
        Redirect response to orders list with 303 See Other status
    """
    logger.warning(f"Order {document_number} not found, redirecting to list")
    
    # Return a redirect to the orders list with error message
    return BaseController.redirect_to_route(
        route_name="order_list",
        query_params={"error": f"Order {document_number} not found"},
        status_code=303  # Use 303 See Other for redirects after operations
    )

def log_order_error(
    monitor_service: MonitorService,
    e: Exception,
    request: Request,
    operation: str,
    document_number: Optional[str] = None
) -> None:
    """
    Log order controller errors consistently.
    
    Args:
        monitor_service: Monitor service for logging
        e: Exception that occurred
        request: FastAPI request
        operation: Operation that triggered the error
        document_number: Optional order document number for context
    """
    component = f"p2p_order_controller.{operation}"
    log_controller_error(monitor_service, e, request, component, document_number)
