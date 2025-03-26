# controllers/p2p_order_api_controller.py
"""
API controller for order endpoints.

This module handles all REST API routes for order management including:
- Listing orders (GET /api/v1/p2p/orders)
- Getting order details (GET /api/v1/p2p/orders/{document_number})
- Creating orders (POST /api/v1/p2p/orders)
- Updating orders (PUT /api/v1/p2p/orders/{document_number})
- Workflow state transitions (submit, approve, receive, complete)
"""

from fastapi import Request, Depends, Response, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import logging
import json

from models.p2p import (
    Order, OrderCreate, OrderUpdate, 
    DocumentStatus
)
from controllers import BaseController
from controllers.p2p_common import (
    get_p2p_service_dependency,
    get_monitor_service_dependency,
    get_material_service_dependency,
    OrderFilterParams
)
from controllers.p2p_order_common import (
    format_order_for_response,
    format_orders_list,
    log_order_error
)
from services import get_p2p_service, get_monitor_service
from services.p2p_service import P2PService
from services.monitor_service import MonitorService
from utils.error_utils import NotFoundError, ValidationError, BadRequestError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# P2P Order API Controller class for dependency injection
class P2POrderAPIController:
    """P2P Order API controller class that handles order-related API operations."""
    
    def __init__(self, p2p_service=None, monitor_service=None):
        """Initialize with required services."""
        self.p2p_service = p2p_service or get_p2p_service()
        self.monitor_service = monitor_service or get_monitor_service()
    
    def _serialize_order(self, order):
        """Serialize an Order object to a dictionary using the best available method."""
        if hasattr(order, 'model_dump'):
            return order.model_dump()
        elif hasattr(order, 'dict'):
            return order.dict()
        elif hasattr(order, '__dict__'):
            return order.__dict__
        else:
            # Fallback: convert attributes manually
            return {
                'id': getattr(order, 'id', None),
                'document_number': getattr(order, 'document_number', None),
                'description': getattr(order, 'description', None),
                'requester': getattr(order, 'requester', None),
                'vendor': getattr(order, 'vendor', None),
                'requisition_id': getattr(order, 'requisition_id', None),
                'status': getattr(order, 'status', None).value if getattr(order, 'status', None) else None,
                'items': getattr(order, 'items', []),
                'created_at': getattr(order, 'created_at', None),
                'updated_at': getattr(order, 'updated_at', None)
            }
    
    def _serialize_orders_list(self, orders):
        """Serialize a list of Order objects to a list of dictionaries."""
        return [self._serialize_order(order) for order in orders]
    
    def _create_success_response(self, data=None, message=None):
        """Create a standardized success response."""
        response = {
            "success": True,
            "status": "success"
        }
        if data is not None:
            if isinstance(data, Order):
                response["data"] = self._serialize_order(data)
            elif isinstance(data, list) and all(isinstance(item, Order) for item in data):
                response["data"] = self._serialize_orders_list(data)
            else:
                response["data"] = data
        if message:
            response["message"] = message
        return response
    
    def _create_error_response(self, message, error_code="error", details=None, status_code=400):
        """Create a standardized error response."""
        response = {
            "success": False,
            "status": "error",
            "message": message,
            "error_code": error_code
        }
        if details:
            response["details"] = details
        return response
    
    async def api_get_order(self, request: Request, order_id: str):
        """API endpoint to get an order by ID."""
        try:
            order = self.p2p_service.get_order(order_id)
            if not order:
                return self._create_error_response(
                    message=f"Order {order_id} not found",
                    error_code="not_found",
                    status_code=404
                )
            return self._create_success_response(data=order)
        except NotFoundError as e:
            self.monitor_service.log_error(
                error_type="not_found_error",
                message=f"Order {order_id} not found in API get request",
                component="p2p_order_api_controller",
                context={"path": str(request.url), "document_number": order_id}
            )
            return self._create_error_response(
                message=str(e),
                error_code="not_found",
                status_code=404
            )
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            log_order_error(self.monitor_service, e, request, "api_get_order", order_id)
            return self._create_error_response(
                message=f"Error retrieving order: {str(e)}",
                error_code="server_error",
                status_code=500
            )
    
    async def api_list_orders(self, request: Request):
        """API endpoint to list all orders."""
        try:
            orders = self.p2p_service.list_orders()
            return self._create_success_response(data=orders)
        except Exception as e:
            logger.error(f"Error listing orders: {e}")
            log_order_error(self.monitor_service, e, request, "api_list_orders")
            return self._create_error_response(
                message=f"Error listing orders: {str(e)}",
                error_code="server_error",
                status_code=500
            )
    
    async def api_create_order(self, request: Request):
        """API endpoint to create a new order."""
        try:
            data = await request.json()
            order = self.p2p_service.create_order(data)
            return self._create_success_response(
                data=order,
                message="Order created successfully"
            )
        except ValidationError as e:
            log_order_error(self.monitor_service, e, request, "api_create_order")
            return self._create_error_response(
                message=str(e),
                error_code="validation_error",
                details=getattr(e, "details", None),
                status_code=400
            )
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            log_order_error(self.monitor_service, e, request, "api_create_order")
            return self._create_error_response(
                message=f"Error creating order: {str(e)}",
                error_code="server_error",
                status_code=500
            )
    
    async def api_create_order_from_requisition(self, request: Request, requisition_id: str):
        """API endpoint to create a new order from a requisition."""
        try:
            # Parse request body for vendor and payment terms
            body_data = await request.json()
            vendor = body_data.get("vendor")
            payment_terms = body_data.get("payment_terms")
            
            if not vendor:
                return self._create_error_response(
                    message="Vendor is required",
                    error_code="validation_error",
                    details={"vendor": "This field is required"},
                    status_code=400
                )
            
            # Create the order
            order = self.p2p_service.create_order_from_requisition(requisition_id, vendor, payment_terms)
            
            # Format response to match expected format in tests
            return self._create_success_response(
                data={
                    "document_number": order.document_number,
                    "status": order.status.value if hasattr(order.status, "value") else str(order.status),
                    "requisition_reference": requisition_id
                },
                message=f"Order created from requisition {requisition_id}"
            )
        except NotFoundError as e:
            log_order_error(self.monitor_service, e, request, "api_create_order_from_requisition", requisition_id)
            return self._create_error_response(
                message=str(e),
                error_code="not_found",
                status_code=404
            )
        except ValidationError as e:
            log_order_error(self.monitor_service, e, request, "api_create_order_from_requisition", requisition_id)
            return self._create_error_response(
                message=str(e),
                error_code="validation_error",
                details=getattr(e, "details", None),
                status_code=400
            )
        except Exception as e:
            logger.error(f"Error creating order from requisition {requisition_id}: {e}")
            log_order_error(self.monitor_service, e, request, "api_create_order_from_requisition", requisition_id)
            return self._create_error_response(
                message=f"Error creating order from requisition: {str(e)}",
                error_code="server_error",
                status_code=500
            )
    
    async def api_update_order(self, request: Request, order_id: str):
        """API endpoint to update an existing order."""
        try:
            data = await request.json()
            order = self.p2p_service.update_order(order_id, data)
            return self._create_success_response(
                data=order,
                message=f"Order {order_id} updated successfully"
            )
        except NotFoundError as e:
            log_order_error(self.monitor_service, e, request, "api_update_order", order_id)
            return self._create_error_response(
                message=str(e),
                error_code="not_found",
                status_code=404
            )
        except ValidationError as e:
            log_order_error(self.monitor_service, e, request, "api_update_order", order_id)
            return self._create_error_response(
                message=str(e),
                error_code="validation_error",
                details=getattr(e, "details", None),
                status_code=400
            )
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {e}")
            log_order_error(self.monitor_service, e, request, "api_update_order", order_id)
            return self._create_error_response(
                message=f"Error updating order: {str(e)}",
                error_code="server_error",
                status_code=500
            )
    
    async def api_submit_order(self, request: Request, order_id: str):
        """API endpoint to submit an order for approval."""
        try:
            order = self.p2p_service.submit_order(order_id)
            return self._create_success_response(
                data={
                    "document_number": order.document_number,
                    "status": order.status.value if hasattr(order.status, "value") else str(order.status),
                    "updated_at": order.updated_at.isoformat() if hasattr(order.updated_at, "isoformat") else order.updated_at
                },
                message=f"Order {order_id} submitted for approval"
            )
        except NotFoundError as e:
            log_order_error(self.monitor_service, e, request, "api_submit_order", order_id)
            return self._create_error_response(
                message=str(e),
                error_code="not_found",
                status_code=404
            )
        except ValidationError as e:
            log_order_error(self.monitor_service, e, request, "api_submit_order", order_id)
            return self._create_error_response(
                message=str(e),
                error_code="validation_error",
                details=getattr(e, "details", None),
                status_code=400
            )
        except Exception as e:
            logger.error(f"Error submitting order {order_id}: {e}")
            log_order_error(self.monitor_service, e, request, "api_submit_order", order_id)
            return self._create_error_response(
                message=f"Error submitting order: {str(e)}",
                error_code="server_error",
                status_code=500
            )

    async def api_approve_order(self, request: Request, order_id: str):
        """API endpoint to approve an order."""
        try:
            order = self.p2p_service.approve_order(order_id)
            response_data = {
                "document_number": order.document_number,
                "status": order.status.value if hasattr(order.status, "value") else str(order.status),
                "updated_at": order.updated_at.isoformat() if hasattr(order.updated_at, "isoformat") else order.updated_at
            }
            return self._create_success_response(
                data=response_data,
                message=f"Order {order_id} has been approved"
            )
        except NotFoundError as e:
            self.monitor_service.log_error(
                error_type="not_found_error",
                message=f"Order {order_id} not found in API approve request",
                component="p2p_order_api_controller",
                context={"path": str(request.url), "document_number": order_id}
            )
            return self._create_error_response(
                message=str(e),
                error_code="not_found",
                status_code=404
            )
        except Exception as e:
            log_order_error(self.monitor_service, e, request, "api_approve_order", order_id)
            return self._create_error_response(
                message=f"Error approving order: {str(e)}",
                error_code="server_error",
                status_code=500
            )

    async def api_receive_order(self, request: Request, order_id: str):
        """API endpoint to mark an order as received."""
        try:
            # Parse receipt data from request body
            body_data = await request.json()
            receipt_data = body_data
            
            order = self.p2p_service.receive_order(order_id, receipt_data)
            response_data = {
                "document_number": order.document_number,
                "status": order.status.value if hasattr(order.status, "value") else str(order.status),
                "updated_at": order.updated_at.isoformat() if hasattr(order.updated_at, "isoformat") else order.updated_at,
                "items": [
                    {
                        "item_number": item.item_number,
                        "received_quantity": item.received_quantity,
                        "status": item.status.value if hasattr(item.status, "value") else str(item.status)
                    }
                    for item in order.items
                ]
            }
            return self._create_success_response(
                data=response_data,
                message=f"Order {order_id} items received"
            )
        except NotFoundError as e:
            self.monitor_service.log_error(
                error_type="not_found_error",
                message=f"Order {order_id} not found in API receive request",
                component="p2p_order_api_controller",
                context={"path": str(request.url), "document_number": order_id}
            )
            return self._create_error_response(
                message=str(e),
                error_code="not_found",
                status_code=404
            )
        except ValidationError as e:
            log_order_error(self.monitor_service, e, request, "api_receive_order", order_id)
            return self._create_error_response(
                message=str(e),
                error_code="validation_error",
                details=getattr(e, "details", None),
                status_code=400
            )
        except Exception as e:
            log_order_error(self.monitor_service, e, request, "api_receive_order", order_id)
            return self._create_error_response(
                message=f"Error receiving order: {str(e)}",
                error_code="server_error",
                status_code=500
            )

    async def api_complete_order(self, request: Request, order_id: str):
        """API endpoint to mark an order as completed."""
        try:
            order = self.p2p_service.complete_order(order_id)
            response_data = {
                "document_number": order.document_number,
                "status": order.status.value if hasattr(order.status, "value") else str(order.status),
                "updated_at": order.updated_at.isoformat() if hasattr(order.updated_at, "isoformat") else order.updated_at
            }
            return self._create_success_response(
                data=response_data,
                message=f"Order {order_id} has been completed"
            )
        except NotFoundError as e:
            self.monitor_service.log_error(
                error_type="not_found_error",
                message=f"Order {order_id} not found in API complete request",
                component="p2p_order_api_controller",
                context={"path": str(request.url), "document_number": order_id}
            )
            return self._create_error_response(
                message=str(e),
                error_code="not_found",
                status_code=404
            )
        except Exception as e:
            log_order_error(self.monitor_service, e, request, "api_complete_order", order_id)
            return self._create_error_response(
                message=f"Error completing order: {str(e)}",
                error_code="server_error",
                status_code=500
            )

    async def api_cancel_order(self, request: Request, order_id: str):
        """API endpoint to cancel an order."""
        try:
            request_data = await request.json()
            reason = request_data.get("reason", "")
            if not reason:
                return self._create_error_response(
                    message="Cancellation reason is required",
                    error_code="validation_error",
                    details={"reason": "This field is required"},
                    status_code=400
                )
            order = self.p2p_service.cancel_order(order_id, reason)
            response_data = {
                "document_number": order.document_number,
                "status": order.status.value if hasattr(order.status, "value") else str(order.status),
                "updated_at": order.updated_at.isoformat() if hasattr(order.updated_at, "isoformat") else order.updated_at,
                "reason": reason
            }
            return self._create_success_response(
                data=response_data,
                message=f"Order {order_id} has been cancelled"
            )
        except NotFoundError as e:
            self.monitor_service.log_error(
                error_type="not_found_error",
                message=f"Order {order_id} not found in API cancel request",
                component="p2p_order_api_controller",
                context={"path": str(request.url), "document_number": order_id}
            )
            return self._create_error_response(
                message=str(e),
                error_code="not_found",
                status_code=404
            )
        except Exception as e:
            log_order_error(self.monitor_service, e, request, "api_cancel_order", order_id)
            return self._create_error_response(
                message=f"Error cancelling order: {str(e)}",
                error_code="server_error",
                status_code=500
            )

# Function to create a P2P order API controller instance
def get_p2p_order_api_controller(p2p_service=None, monitor_service=None):
    """Create a P2P order API controller instance.
    
    Args:
        p2p_service: The P2P service to use
        monitor_service: The monitor service to use
        
    Returns:
        A P2POrderAPIController instance
    """
    return P2POrderAPIController(
        p2p_service=p2p_service,
        monitor_service=monitor_service
    )

# API endpoint functions - these are wrappers around the controller methods
async def api_get_order(request: Request, order_id: str, p2p_service=None, monitor_service=None):
    """API endpoint to get an order by ID."""
    controller = get_p2p_order_api_controller(p2p_service, monitor_service)
    return await controller.api_get_order(request, order_id)

async def api_list_orders(request: Request, p2p_service=None, monitor_service=None):
    """API endpoint to list all orders."""
    controller = get_p2p_order_api_controller(p2p_service, monitor_service)
    return await controller.api_list_orders(request)

async def api_create_order(request: Request, p2p_service=None, monitor_service=None):
    """API endpoint to create a new order."""
    controller = get_p2p_order_api_controller(p2p_service, monitor_service)
    return await controller.api_create_order(request)

async def api_create_order_from_requisition(request: Request, requisition_id: str, p2p_service=None, monitor_service=None):
    """API endpoint to create a new order from a requisition."""
    controller = get_p2p_order_api_controller(p2p_service, monitor_service)
    return await controller.api_create_order_from_requisition(request, requisition_id)

async def api_update_order(request: Request, order_id: str, p2p_service=None, monitor_service=None):
    """API endpoint to update an existing order."""
    controller = get_p2p_order_api_controller(p2p_service, monitor_service)
    return await controller.api_update_order(request, order_id)

async def api_submit_order(request: Request, order_id: str, p2p_service=None, monitor_service=None):
    """API endpoint to submit an order for approval."""
    controller = get_p2p_order_api_controller(p2p_service, monitor_service)
    return await controller.api_submit_order(request, order_id)

async def api_approve_order(request: Request, order_id: str, p2p_service=None, monitor_service=None):
    """API endpoint to approve an order."""
    controller = get_p2p_order_api_controller(p2p_service, monitor_service)
    return await controller.api_approve_order(request, order_id)

async def api_receive_order(request: Request, order_id: str, p2p_service=None, monitor_service=None):
    """API endpoint to mark an order as received."""
    controller = get_p2p_order_api_controller(p2p_service, monitor_service)
    return await controller.api_receive_order(request, order_id)

async def api_complete_order(request: Request, order_id: str, p2p_service=None, monitor_service=None):
    """API endpoint to mark an order as completed."""
    controller = get_p2p_order_api_controller(p2p_service, monitor_service)
    return await controller.api_complete_order(request, order_id)

async def api_cancel_order(request: Request, order_id: str, p2p_service=None, monitor_service=None):
    """API endpoint to cancel an order."""
    controller = get_p2p_order_api_controller(p2p_service, monitor_service)
    return await controller.api_cancel_order(request, order_id)
