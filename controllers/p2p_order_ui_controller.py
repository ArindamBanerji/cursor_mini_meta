# controllers/p2p_order_ui_controller.py
"""
UI controller for order management.

This module handles all user interface routes for order management including:
- Listing orders
- Viewing order details
- Creating and editing orders
- Workflow actions (submit, approve, receive)
"""

from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional, List

from models.p2p import (
    Order, OrderCreate, OrderUpdate, OrderItem,
    DocumentStatus, ProcurementType
)
from services.url_service import url_service
from services import get_p2p_service, get_monitor_service, get_material_service
from services.p2p_service import P2PService
from services.monitor_service import MonitorService
from services.material_service import MaterialService

from controllers import BaseController
from controllers.p2p_common import (
    get_p2p_service_dependency,
    get_monitor_service_dependency,
    get_material_service_dependency,
    log_controller_error,
    OrderFilterParams,
    STATUS_BADGE_COLORS
)
from controllers.p2p_order_common import (
    format_order_for_response,
    format_orders_list,
    handle_order_not_found,
    log_order_error
)
from controllers.session_utils import (
    get_template_context_with_session,
    handle_form_error,
    handle_form_validation_error,
    redirect_with_success,
    redirect_with_error
)
from utils.error_utils import NotFoundError, ValidationError, BadRequestError

# UI Controller Methods

async def list_orders(
    request: Request,
    p2p_service=None,
    monitor_service=None
):
    """
    List orders with optional filtering (UI endpoint).
    
    Args:
        request: FastAPI request
        p2p_service: Injected P2P service
        monitor_service: Injected monitor service
        
    Returns:
        Template context dictionary
    """
    # Get services if not provided (for testing)
    if p2p_service is None:
        p2p_service = get_p2p_service()
    if monitor_service is None:
        monitor_service = get_monitor_service()
        
    try:
        # Parse query parameters
        params = await BaseController.parse_query_params(request, OrderFilterParams)
        
        # Get orders with filtering
        orders = p2p_service.list_orders(
            status=params.status,
            vendor=params.vendor,
            requisition_reference=params.requisition_reference,
            search_term=params.search,
            date_from=params.date_from,
            date_to=params.date_to
        )
        
        # Get document status options for the filter
        document_statuses = [status.value for status in DocumentStatus]
        
        # Build template context
        context = {
            "orders": orders,
            "count": len(orders),
            "filters": {
                "search": params.search,
                "status": params.status.value if params.status else None,
                "vendor": params.vendor,
                "requisition_reference": params.requisition_reference,
                "date_from": params.date_from,
                "date_to": params.date_to
            },
            "filter_options": {
                "statuses": document_statuses
            },
            "title": "Purchase Orders"
        }
        
        # Add session data to context
        return get_template_context_with_session(request, context)
    except Exception as e:
        log_order_error(monitor_service, e, request, "list_orders")
        raise

async def get_order(
    request: Request,
    document_number: str,
    p2p_service=None,
    monitor_service=None
):
    """
    Get order details (UI endpoint).
    
    Args:
        request: FastAPI request
        document_number: Order document number
        p2p_service: Injected P2P service
        monitor_service: Injected monitor service
        
    Returns:
        Template context dictionary or redirect response
    """
    # Get services if not provided (for testing)
    if p2p_service is None:
        p2p_service = get_p2p_service()
    if monitor_service is None:
        monitor_service = get_monitor_service()
        
    try:
        # Get the order
        order = p2p_service.get_order(document_number)
        
        # Format the order for the UI
        formatted_order = format_order_for_response(order)
        
        # Get related requisition if available
        related_requisition = None
        if order.requisition_reference:
            try:
                related_requisition = p2p_service.get_requisition(order.requisition_reference)
            except NotFoundError:
                # Related requisition not found, just continue
                pass
        
        # Determine available actions based on status
        context = {
            "order": order,
            "formatted_order": formatted_order,
            "related_requisition": related_requisition,
            "status_colors": STATUS_BADGE_COLORS,
            "can_edit": order.status == DocumentStatus.DRAFT,
            "can_submit": order.status == DocumentStatus.DRAFT,
            "can_approve": order.status == DocumentStatus.SUBMITTED,
            "can_reject": order.status == DocumentStatus.SUBMITTED,
            "can_receive": order.status == DocumentStatus.APPROVED,
            "can_complete": order.status in [DocumentStatus.RECEIVED, DocumentStatus.PARTIALLY_RECEIVED],
            "can_cancel": order.status not in [DocumentStatus.COMPLETED, DocumentStatus.CANCELED],
            "title": f"Purchase Order: {document_number}"
        }
        
        # Add session data to context
        return get_template_context_with_session(request, context)
    except NotFoundError as e:
        # Log the not found error before redirecting
        monitor_service.log_error(
            error_type="not_found_error",
            message=f"Order {document_number} not found in UI request",
            component="p2p_order_ui_controller",
            context={"path": str(request.url), "document_number": document_number}
        )
        return handle_order_not_found(document_number, request)
    except Exception as e:
        log_order_error(monitor_service, e, request, "get_order", document_number)
        raise

async def create_order_form(
    request: Request,
    material_service=None,
    monitor_service=None
):
    """
    Display the order creation form (UI endpoint).
    
    Args:
        request: FastAPI request
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        Template context dictionary
    """
    # Get services if not provided (for testing)
    if material_service is None:
        material_service = get_material_service()
    if monitor_service is None:
        monitor_service = get_monitor_service()
        
    try:
        # Get materials for dropdown
        materials = material_service.list_materials(status=["ACTIVE", "INACTIVE"])
        
        # Get procurement types
        procurement_types = [proc_type.value for proc_type in ProcurementType]
        
        # Check if creating from a requisition
        requisition_number = request.query_params.get("from_requisition")
        requisition = None
        
        if requisition_number:
            try:
                # Try to get the requisition
                p2p_service = get_p2p_service()
                requisition = p2p_service.get_requisition(requisition_number)
                
                # Check if requisition is approved
                if requisition.status != DocumentStatus.APPROVED:
                    return RedirectResponse(
                        url=f"/p2p/requisitions/{requisition_number}?error=Only+approved+requisitions+can+be+converted+to+orders",
                        status_code=303  # See Other
                    )
            except NotFoundError:
                # Requisition not found, just continue without it
                pass
        
        # Build template context
        context = {
            "title": "Create Purchase Order",
            "form_action": url_service.get_url_for_route("order_create"),
            "form_method": "POST",
            "materials": materials,
            "procurement_types": procurement_types,
            "initial_items": [{}],  # Start with one empty item
            "requisition": requisition
        }
        
        # Add session data to context
        return get_template_context_with_session(request, context)
    except Exception as e:
        log_order_error(monitor_service, e, request, "create_order_form")
        raise

async def create_order(
    request: Request,
    p2p_service=None,
    material_service=None,
    monitor_service=None
):
    """
    Create a new order (UI form handler).
    
    Args:
        request: FastAPI request
        p2p_service: Injected P2P service
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        Redirect response or template context with errors
    """
    # Get services if not provided (for testing)
    if p2p_service is None:
        p2p_service = get_p2p_service()
    if material_service is None:
        material_service = get_material_service()
    if monitor_service is None:
        monitor_service = get_monitor_service()
        
    try:
        # Parse form data
        form_data = await request.form()
        form_dict = dict(form_data)
        
        # Check if creating from a requisition
        from_requisition = form_dict.get("from_requisition")
        if from_requisition:
            # Create an order from the requisition
            vendor = form_dict.get("vendor", "")
            payment_terms = form_dict.get("payment_terms", "")
            
            if not vendor:
                # Handle validation error
                await handle_form_validation_error(
                    request, 
                    form_dict,
                    {"vendor": "Vendor is required"}
                )
                url = url_service.get_url_for_route("order_create_form", 
                                                   {"from_requisition": from_requisition})
                return RedirectResponse(url, status_code=303)
            
            try:
                order = p2p_service.create_order_from_requisition(
                    from_requisition, vendor, payment_terms
                )
                
                # Redirect to the order detail page with success message
                return await redirect_with_success(
                    url_service.get_url_for_route("order_detail", {"document_number": order.document_number}),
                    request,
                    f"Order created successfully from requisition {from_requisition}"
                )
            except Exception as e:
                # Handle error
                await handle_form_error(
                    request,
                    form_dict,
                    f"Error creating order from requisition: {str(e)}"
                )
                url = url_service.get_url_for_route("order_create_form", 
                                                   {"from_requisition": from_requisition})
                return RedirectResponse(url, status_code=303)
        
        # Try to create a new order
        try:
            # Extract form data
            order_data = {
                "description": form_dict.get("description", ""),
                "requester": form_dict.get("requester", ""),
                "vendor": form_dict.get("vendor", ""),
                "payment_terms": form_dict.get("payment_terms", ""),
                "procurement_type": form_dict.get("procurement_type", "STANDARD"),
                "notes": form_dict.get("notes", "")
            }
            
            # Process items (using existing functionality)
            from controllers.p2p_requisition_common import validate_requisition_items_input
            items_data = validate_requisition_items_input(form_dict, material_service)
            
            # Create model instance
            order_create = OrderCreate(
                **order_data,
                items=items_data
            )
            
            # Create the order
            order = p2p_service.create_order(order_create)
            
            # Redirect to order detail page with success message
            return await redirect_with_success(
                url_service.get_url_for_route("order_detail", {"document_number": order.document_number}),
                request,
                f"Order {order.document_number} created successfully"
            )
        except ValidationError as e:
            # Handle validation errors
            await handle_form_validation_error(request, form_dict, e.errors)
            url = url_service.get_url_for_route("order_create_form")
            return RedirectResponse(url, status_code=303)
        except Exception as e:
            # Handle other errors
            await handle_form_error(
                request, 
                form_dict, 
                f"Error creating order: {str(e)}"
            )
            url = url_service.get_url_for_route("order_create_form")
            return RedirectResponse(url, status_code=303)
    except Exception as e:
        log_order_error(monitor_service, e, request, "create_order")
        raise

async def update_order_form(
    request: Request,
    document_number: str,
    p2p_service=None,
    material_service=None,
    monitor_service=None
):
    """
    Display the order update form (UI endpoint).
    
    Args:
        request: FastAPI request
        document_number: Order document number
        p2p_service: Injected P2P service
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        Template context dictionary or redirect response
    """
    # Get services if not provided (for testing)
    if p2p_service is None:
        p2p_service = get_p2p_service()
    if material_service is None:
        material_service = get_material_service()
    if monitor_service is None:
        monitor_service = get_monitor_service()
        
    try:
        # Get the order
        order = p2p_service.get_order(document_number)
        
        # Check if order can be edited
        if order.status != DocumentStatus.DRAFT:
            return RedirectResponse(
                url=f"/p2p/orders/{document_number}?error=Only+draft+orders+can+be+edited",
                status_code=303  # See Other
            )
        
        # Get materials for dropdown
        materials = material_service.list_materials(status=["ACTIVE", "INACTIVE"])
        
        # Get procurement types
        procurement_types = [proc_type.value for proc_type in ProcurementType]
        
        # Build template context
        context = {
            "title": f"Edit Order: {document_number}",
            "order": order,
            "form_action": url_service.get_url_for_route("order_update", {"document_number": document_number}),
            "form_method": "POST",
            "materials": materials,
            "procurement_types": procurement_types,
            "form_data": {}
        }
        
        return context
    except NotFoundError:
        return handle_order_not_found(document_number, request)
    except Exception as e:
        log_order_error(monitor_service, e, request, "update_order_form", document_number)
        raise

async def update_order(
    request: Request,
    document_number: str,
    p2p_service=None,
    material_service=None, 
    monitor_service=None
):
    """
    Process the update order form submission.
    
    Args:
        request: FastAPI request
        document_number: Order document number to update
        p2p_service: Injected P2P service
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        Redirect response
    """
    # Get services if not provided (for testing)
    if p2p_service is None:
        p2p_service = get_p2p_service()
    if material_service is None:
        material_service = get_material_service()
    if monitor_service is None:
        monitor_service = get_monitor_service()
        
    try:
        # Get the existing order
        order = p2p_service.get_order(document_number)
        
        # Parse form data
        form_data = await BaseController.parse_form_data(request)
        
        # Create update object
        update_data = OrderUpdate(
            description=form_data.get("description", ""),
            vendor=form_data.get("vendor", ""),
            expected_delivery_date=form_data.get("expected_delivery_date"),
            items=[]  # Will be populated below
        )
        
        # Process item data
        item_count = int(form_data.get("item_count", 0))
        for i in range(item_count):
            item_prefix = f"item_{i}_"
            
            # Only add items that have a material number and quantity
            material_number = form_data.get(f"{item_prefix}material_number")
            quantity = form_data.get(f"{item_prefix}quantity")
            
            if material_number and quantity:
                try:
                    # Verify material exists
                    material = material_service.get_material(material_number)
                    
                    # Create item
                    item = OrderItem(
                        material_number=material_number,
                        description=material.description,
                        quantity=float(quantity),
                        unit_of_measure=material.unit_of_measure,
                        unit_price=float(form_data.get(f"{item_prefix}unit_price", 0))
                    )
                    update_data.items.append(item)
                except Exception as e:
                    # Log material errors but continue with other items
                    monitor_service.log_error(f"Error processing item {i}: {str(e)}")
        
        # Update the order
        updated_order = p2p_service.update_order(document_number, update_data)
        
        # Redirect with success message
        return await redirect_with_success(
            request=request,
            url=f"/p2p/orders/{document_number}",
            message=f"Order {document_number} updated successfully"
        )
    except NotFoundError as e:
        # Document not found, redirect to list with error
        return await redirect_with_error(
            request=request,
            url="/p2p/orders",
            message=str(e)
        )
    except ValidationError as e:
        # Validation error, preserve form data and show errors
        return await handle_order_form_errors(
            request=request,
            form_type="update",
            errors=e.errors,
            form_data=form_data,
            material_service=material_service,
            monitor_service=monitor_service,
            document_number=document_number
        )
    except Exception as e:
        # Log other errors
        log_order_error(monitor_service, e, request, "update_order", document_number)
        
        # Redirect with generic error
        return await redirect_with_error(
            request=request,
            url=f"/p2p/orders/{document_number}/edit",
            message=f"An error occurred while updating the order: {str(e)}"
        )

async def receive_order_form(
    request: Request,
    document_number: str,
    p2p_service=None,
    monitor_service=None
):
    """
    Display form for receiving order items (UI endpoint).
    
    Args:
        request: FastAPI request
        document_number: Order document number
        p2p_service: Injected P2P service
        monitor_service: Injected monitor service
        
    Returns:
        Template context dictionary or redirect response
    """
    # Get services if not provided (for testing)
    if p2p_service is None:
        p2p_service = get_p2p_service()
    if monitor_service is None:
        monitor_service = get_monitor_service()
        
    try:
        # Get the order
        order = p2p_service.get_order(document_number)
        
        # Check if order can be received
        if order.status != DocumentStatus.APPROVED:
            return RedirectResponse(
                url=f"/p2p/orders/{document_number}?error=Only+approved+orders+can+be+received",
                status_code=303  # See Other
            )
        
        # Build template context
        context = {
            "title": f"Receive Order: {document_number}",
            "order": order,
            "form_action": url_service.get_url_for_route("order_receive", {"document_number": document_number}),
            "form_method": "POST",
            "form_data": {}
        }
        
        return context
    except NotFoundError:
        return handle_order_not_found(document_number, request)
    except Exception as e:
        log_order_error(monitor_service, e, request, "receive_order_form", document_number)
        raise

# Helper function for handling form errors
async def handle_order_form_errors(
    request: Request,
    form_type: str,
    errors: Dict[str, Any],
    form_data: Dict[str, Any],
    material_service: MaterialService,
    monitor_service: MonitorService,
    document_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handle order form errors.
    
    Args:
        request: FastAPI request
        form_type: Form type ("create" or "update")
        errors: Validation errors
        form_data: Submitted form data
        material_service: Material service
        monitor_service: Monitor service
        document_number: Optional document number (for updates)
    
    Returns:
        Template context with error information
    """
    try:
        # Get materials for dropdown
        materials = material_service.list_materials(status=["ACTIVE", "INACTIVE"])
        
        # Get procurement types
        procurement_types = [proc_type.value for proc_type in ProcurementType]
        
        # Build context based on form type
        if form_type == "create":
            title = "Create Purchase Order"
            form_action = url_service.get_url_for_route("order_create")
        else:
            title = f"Edit Order: {document_number}"
            form_action = url_service.get_url_for_route("order_update", {"document_number": document_number})
            
            # Get order for update form
            if document_number:
                p2p_service = get_p2p_service()
                order = p2p_service.get_order(document_number)
                context = {
                    "order": order,
                }
            
        # Build template context
        context = {
            "title": title,
            "form_action": form_action,
            "form_method": "POST",
            "materials": materials,
            "procurement_types": procurement_types,
            "errors": errors,
            "form_data": form_data
        }
        
        # Add session data to context
        return get_template_context_with_session(request, context)
    except Exception as e:
        log_order_error(
            monitor_service, e, request, 
            f"handle_{form_type}_form_errors", 
            document_number
        )
        raise
