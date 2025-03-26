# controllers/material_ui_controller.py
"""
Controller for Material UI endpoints.

This module handles all user interface routes for material management including:
- Listing materials
- Viewing material details
- Creating materials
- Updating materials
- Deprecating materials
"""

from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional, List
import logging

from models.material import (
    Material, MaterialCreate, MaterialUpdate, MaterialStatus
)
from services.url_service import url_service
from services import get_material_service, get_monitor_service
from services.material_service import MaterialService
from services.monitor_service import MonitorService
from controllers import BaseController
from controllers.material_common import (
    get_material_service_dependency,
    get_monitor_service_dependency,
    get_material_type_options,
    get_material_status_options,
    get_unit_of_measure_options,
    handle_material_not_found,
    log_controller_error,
    MaterialFilterParams
)
from controllers.session_utils import (
    get_template_context_with_session,
    handle_form_error,
    handle_form_validation_error,
    redirect_with_success,
    redirect_with_error
)
from utils.error_utils import NotFoundError, ValidationError, BadRequestError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Material UI Controller class for dependency injection
class MaterialUIController:
    """Material UI controller class that handles material-related UI operations."""
    
    def __init__(self, material_service=None, monitor_service=None):
        """Initialize with required services."""
        self.material_service = material_service
        self.monitor_service = monitor_service
    
    async def get_material(self, request: Request, material_id: str):
        """UI endpoint to get a material by ID."""
        try:
            material = self.material_service.get_material(material_id)
            if not material:
                return {"error": f"Material {material_id} not found"}
            return {"material": material}
        except Exception as e:
            logger.error(f"Error getting material {material_id}: {e}")
            return {"error": str(e)}
    
    async def list_materials(self, request: Request):
        """UI endpoint to list all materials."""
        try:
            materials = self.material_service.list_materials()
            return {"materials": materials}
        except Exception as e:
            logger.error(f"Error listing materials: {e}")
            return {"error": str(e)}
    
    async def create_material_form(self, request: Request):
        """UI endpoint to show the create material form."""
        return {}
    
    async def create_material(self, request: Request):
        """UI endpoint to create a new material."""
        try:
            form_data = await request.form()
            material_data = dict(form_data)
            material = self.material_service.create_material(material_data)
            return RedirectResponse(url="/materials", status_code=303)
        except Exception as e:
            logger.error(f"Error creating material: {e}")
            return {"error": str(e)}
    
    async def update_material_form(self, request: Request, material_id: str):
        """UI endpoint to show the update material form."""
        try:
            material = self.material_service.get_material(material_id)
            if not material:
                return {"error": f"Material {material_id} not found"}
            return {"material": material}
        except Exception as e:
            logger.error(f"Error getting material {material_id}: {e}")
            return {"error": str(e)}
    
    async def update_material(self, request: Request, material_id: str):
        """UI endpoint to update an existing material."""
        try:
            form_data = await request.form()
            material_data = dict(form_data)
            material = self.material_service.update_material(material_id, material_data)
            if not material:
                return {"error": f"Material {material_id} not found"}
            return RedirectResponse(url="/materials", status_code=303)
        except Exception as e:
            logger.error(f"Error updating material {material_id}: {e}")
            return {"error": str(e)}
    
    async def deprecate_material(self, request: Request, material_id: str):
        """UI endpoint to deprecate a material."""
        try:
            success = self.material_service.deprecate_material(material_id)
            if not success:
                return {"error": f"Material {material_id} not found"}
            return RedirectResponse(url="/materials", status_code=303)
        except Exception as e:
            logger.error(f"Error deprecating material {material_id}: {e}")
            return {"error": str(e)}

# Function to create a material UI controller instance
def get_material_ui_controller(material_service=None, monitor_service=None):
    """Create a material UI controller instance.
    
    Args:
        material_service: The material service to use
        monitor_service: The monitor service to use
        
    Returns:
        A MaterialUIController instance
    """
    return MaterialUIController(
        material_service=material_service,
        monitor_service=monitor_service
    )

# UI endpoint functions - these are wrappers around the controller methods
async def get_material(request: Request, material_id: str):
    """UI endpoint to get a material by ID."""
    controller = get_material_ui_controller()
    return await controller.get_material(request, material_id)

async def list_materials(request: Request):
    """UI endpoint to list all materials."""
    controller = get_material_ui_controller()
    return await controller.list_materials(request)

async def create_material_form(request: Request):
    """UI endpoint to show the create material form."""
    controller = get_material_ui_controller()
    return await controller.create_material_form(request)

async def create_material(request: Request):
    """UI endpoint to create a new material."""
    controller = get_material_ui_controller()
    return await controller.create_material(request)

async def update_material_form(request: Request, material_id: str):
    """UI endpoint to show the update material form."""
    controller = get_material_ui_controller()
    return await controller.update_material_form(request, material_id)

async def update_material(request: Request, material_id: str):
    """UI endpoint to update an existing material."""
    controller = get_material_ui_controller()
    return await controller.update_material(request, material_id)

async def deprecate_material(request: Request, material_id: str):
    """UI endpoint to deprecate a material."""
    controller = get_material_ui_controller()
    return await controller.deprecate_material(request, material_id)

# UI Controller Methods

async def list_materials(
    request: Request,
    material_service=None,
    monitor_service=None
):
    """
    List materials with optional filtering (UI endpoint).
    
    Args:
        request: FastAPI request
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        Template context dictionary
    """
    # Get services if not provided (for testing)
    if material_service is None or (not isinstance(material_service, MaterialService) and hasattr(material_service, 'dependency')):
        material_service = get_material_service()
    if monitor_service is None or (not isinstance(monitor_service, MonitorService) and hasattr(monitor_service, 'dependency')):
        monitor_service = get_monitor_service()
        
    try:
        # Parse query parameters
        params = await BaseController.parse_query_params(request, MaterialFilterParams)
        
        # Get materials with filtering
        materials = material_service.list_materials(
            status=params.status,
            type=params.type,
            search_term=params.search
        )
        
        # Get material type options for the filter
        material_types = get_material_type_options()
        material_statuses = get_material_status_options()
        
        # Build template context
        context = {
            "materials": materials,
            "count": len(materials),
            "filters": {
                "search": params.search,
                "type": params.type.value if params.type else None,
                "status": params.status.value if params.status else None
            },
            "filter_options": {
                "types": material_types,
                "statuses": material_statuses
            },
            "title": "Materials"
        }
        
        # Add session data to context
        return get_template_context_with_session(request, context)
    except Exception as e:
        log_controller_error(monitor_service, e, request, "list_materials")
        raise

async def get_material(
    request: Request,
    material_id: str,
    material_service=None,
    monitor_service=None
):
    """
    Get material details (UI endpoint).
    
    Args:
        request: FastAPI request
        material_id: Material ID or number
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        Template context dictionary or redirect response
    """
    # Get services if not provided (for testing)
    if material_service is None or (not isinstance(material_service, MaterialService) and hasattr(material_service, 'dependency')):
        material_service = get_material_service()
    if monitor_service is None or (not isinstance(monitor_service, MonitorService) and hasattr(monitor_service, 'dependency')):
        monitor_service = get_monitor_service()
        
    try:
        # Get the material
        material = material_service.get_material(material_id)
        
        # Get related procurement information
        # In this version we don't have the p2p_controller yet, so just prepare for future integration
        related_documents = {
            "requisitions": [],
            "orders": []
        }
        
        # Build template context
        context = {
            "material": material,
            "related_documents": related_documents,
            "title": f"Material: {material.name}"
        }
        
        # Add session data to context
        return get_template_context_with_session(request, context)
    except NotFoundError as e:
        # Log the not found error before redirecting
        monitor_service.log_error(
            error_type="not_found_error",
            message=f"Material {material_id} not found in UI request",
            component="material_controller",
            context={"path": str(request.url), "material_id": material_id}
        )
        return handle_material_not_found(material_id, request)
    except Exception as e:
        log_controller_error(monitor_service, e, request, "get_material", material_id)
        raise

async def create_material_form(
    request: Request,
    material_service = Depends(get_material_service_dependency),
    monitor_service = Depends(get_monitor_service_dependency)
):
    """
    Display the material creation form (UI endpoint).
    
    Args:
        request: FastAPI request
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        Template context dictionary
    """
    try:
        # Get options for dropdowns
        material_types = get_material_type_options()
        units_of_measure = get_unit_of_measure_options()
        
        # Build template context
        context = {
            "title": "Create Material",
            "form_action": url_service.get_url_for_route("material_create"),
            "form_method": "POST",
            "material_types": material_types,
            "units_of_measure": units_of_measure
        }
        
        # Add session data to context
        return get_template_context_with_session(request, context)
    except Exception as e:
        log_controller_error(monitor_service, e, request, "create_material_form")
        raise

async def create_material(
    request: Request,
    material_service = Depends(get_material_service_dependency),
    monitor_service = Depends(get_monitor_service_dependency)
):
    """
    Create a new material (UI form handler).
    
    Args:
        request: FastAPI request
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        Redirect response or template context with errors
    """
    try:
        # Parse form data
        form_data = await request.form()
        form_dict = dict(form_data)
        
        # Try to create a new material
        try:
            # Extract form data
            material_data = {
                "name": form_dict.get("name", ""),
                "description": form_dict.get("description", ""),
                "material_type": form_dict.get("material_type", ""),
                "unit_of_measure": form_dict.get("unit_of_measure", ""),
                "price": float(form_dict.get("price", 0) or 0),
                "currency": form_dict.get("currency", "USD"),
                "vendor": form_dict.get("vendor", ""),
                "min_order_quantity": float(form_dict.get("min_order_quantity", 0) or 0),
                "lead_time_days": int(form_dict.get("lead_time_days", 0) or 0)
            }
            
            # Create model instance
            material_create = MaterialCreate(**material_data)
            
            # Create the material
            material = material_service.create_material(material_create)
            
            # Redirect to material detail page with success message
            return await redirect_with_success(
                url_service.get_url_for_route("material_detail", {"material_id": material.material_number}),
                request,
                f"Material {material.material_number} created successfully"
            )
        except ValidationError as e:
            # Handle validation errors
            await handle_form_validation_error(request, form_dict, e.errors)
            url = url_service.get_url_for_route("material_create_form")
            return RedirectResponse(url, status_code=303)
        except Exception as e:
            # Handle other errors
            await handle_form_error(
                request, 
                form_dict, 
                f"Error creating material: {str(e)}"
            )
            url = url_service.get_url_for_route("material_create_form")
            return RedirectResponse(url, status_code=303)
    except Exception as e:
        log_controller_error(monitor_service, e, request, "create_material")
        raise

async def update_material_form(
    request: Request,
    material_id: str,
    material_service = Depends(get_material_service_dependency),
    monitor_service = Depends(get_monitor_service_dependency)
):
    """
    Display the material update form (UI endpoint).
    
    Args:
        request: FastAPI request
        material_id: Material ID
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        Template context dictionary or redirect response
    """
    try:
        # Get the material
        material = material_service.get_material(material_id)
        
        # Get options for dropdowns
        material_types = get_material_type_options()
        units_of_measure = get_unit_of_measure_options()
        
        # Build template context
        context = {
            "title": f"Edit Material: {material.name}",
            "form_action": url_service.get_url_for_route("material_update", {"material_id": material_id}),
            "form_method": "POST",
            "material_types": material_types,
            "units_of_measure": units_of_measure,
            "material": material
        }
        
        # Add session data to context
        return get_template_context_with_session(request, context)
    except NotFoundError:
        return handle_material_not_found(material_id, request)
    except Exception as e:
        log_controller_error(monitor_service, e, request, "update_material_form", material_id)
        raise

async def update_material(
    request: Request,
    material_id: str,
    material_service = Depends(get_material_service_dependency),
    monitor_service = Depends(get_monitor_service_dependency)
):
    """
    Update a material (UI form handler).
    
    Args:
        request: FastAPI request
        material_id: Material ID
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        Redirect response or template context with errors
    """
    try:
        # Parse form data
        form_data = await request.form()
        form_dict = dict(form_data)
        
        # Try to update the material
        try:
            # Extract form data
            material_data = {
                "name": form_dict.get("name", ""),
                "description": form_dict.get("description", ""),
                "material_type": form_dict.get("material_type", ""),
                "unit_of_measure": form_dict.get("unit_of_measure", ""),
                "price": float(form_dict.get("price", 0) or 0),
                "currency": form_dict.get("currency", "USD"),
                "vendor": form_dict.get("vendor", ""),
                "min_order_quantity": float(form_dict.get("min_order_quantity", 0) or 0),
                "lead_time_days": int(form_dict.get("lead_time_days", 0) or 0)
            }
            
            # Create model instance
            material_update = MaterialUpdate(**material_data)
            
            # Update the material
            material = material_service.update_material(material_id, material_update)
            
            # Redirect to material detail page with success message
            return await redirect_with_success(
                url_service.get_url_for_route("material_detail", {"material_id": material.material_number}),
                request,
                f"Material {material.material_number} updated successfully"
            )
        except ValidationError as e:
            # Handle validation errors
            await handle_form_validation_error(request, form_dict, e.errors)
            url = url_service.get_url_for_route("material_update_form", {"material_id": material_id})
            return RedirectResponse(url, status_code=303)
        except Exception as e:
            # Handle other errors
            await handle_form_error(
                request, 
                form_dict, 
                f"Error updating material: {str(e)}"
            )
            url = url_service.get_url_for_route("material_update_form", {"material_id": material_id})
            return RedirectResponse(url, status_code=303)
    except NotFoundError:
        return handle_material_not_found(material_id, request)
    except Exception as e:
        log_controller_error(monitor_service, e, request, "update_material", material_id)
        raise

async def deprecate_material(
    request: Request,
    material_id: str,
    material_service = Depends(get_material_service_dependency),
    monitor_service = Depends(get_monitor_service_dependency)
):
    """
    Deprecate a material (UI endpoint).
    
    Args:
        request: FastAPI request
        material_id: Material ID
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        Redirect response
    """
    try:
        # Try to deprecate the material
        try:
            material = material_service.update_material_status(material_id, MaterialStatus.INACTIVE)
            
            # Redirect to material detail page with success message
            return await redirect_with_success(
                url_service.get_url_for_route("material_detail", {"material_id": material.material_number}),
                request,
                f"Material {material.material_number} deprecated successfully"
            )
        except Exception as e:
            # Handle other errors
            return await redirect_with_error(
                url_service.get_url_for_route("material_detail", {"material_id": material_id}),
                request,
                f"Error deprecating material: {str(e)}"
            )
    except NotFoundError:
        return handle_material_not_found(material_id, request)
    except Exception as e:
        log_controller_error(monitor_service, e, request, "deprecate_material", material_id)
        raise