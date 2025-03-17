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

from models.material import (
    Material, MaterialCreate, MaterialUpdate, MaterialStatus
)
from services.url_service import url_service
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
from utils.error_utils import NotFoundError, ValidationError, BadRequestError

# UI Controller Methods

async def list_materials(
    request: Request,
    material_service = get_material_service_dependency(),
    monitor_service = get_monitor_service_dependency()
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
        
        return context
    except Exception as e:
        log_controller_error(monitor_service, e, request, "list_materials")
        raise

async def get_material(
    request: Request,
    material_id: str,
    material_service = get_material_service_dependency(),
    monitor_service = get_monitor_service_dependency()
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
        
        return context
    except NotFoundError:
        return handle_material_not_found(material_id, request)
    except Exception as e:
        log_controller_error(monitor_service, e, request, "get_material", material_id)
        raise

async def create_material_form(
    request: Request,
    material_service = get_material_service_dependency(),
    monitor_service = get_monitor_service_dependency()
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
        # Get options for form dropdowns
        material_types = get_material_type_options()
        units_of_measure = get_unit_of_measure_options()
        material_statuses = get_material_status_options()
        
        # Build template context
        context = {
            "title": "Create Material",
            "form_action": url_service.get_url_for_route("material_create"),
            "form_method": "POST",
            "options": {
                "types": material_types,
                "units": units_of_measure,
                "statuses": material_statuses
            },
            # Always include an empty form_data dictionary to prevent template errors
            "form_data": {}
        }
        
        return context
    except Exception as e:
        log_controller_error(monitor_service, e, request, "create_material_form")
        raise

async def create_material(
    request: Request,
    material_service = get_material_service_dependency(),
    monitor_service = get_monitor_service_dependency()
):
    """
    Create a new material (UI endpoint).
    
    Args:
        request: FastAPI request
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        Redirect to the new material or back to the form with errors
    """
    try:
        # Parse form data
        form_data = await request.form()
        
        # Build material creation data
        material_data = {
            "name": form_data.get("name"),
            "description": form_data.get("description"),
            "type": form_data.get("type"),
            "base_unit": form_data.get("base_unit"),
            "status": form_data.get("status", MaterialStatus.ACTIVE.value)
        }
        
        # Add optional numeric fields if provided
        if form_data.get("weight"):
            material_data["weight"] = float(form_data.get("weight"))
        if form_data.get("volume"):
            material_data["volume"] = float(form_data.get("volume"))
        
        # Create the material
        material_create = MaterialCreate(**material_data)
        material = material_service.create_material(material_create)
        
        # Redirect to the material detail page
        return RedirectResponse(
            url=f"/materials/{material.material_number}",
            status_code=303  # See Other
        )
    except ValidationError as e:
        # Get options for form dropdowns
        material_types = get_material_type_options()
        units_of_measure = get_unit_of_measure_options()
        material_statuses = get_material_status_options()
        
        # Create context with form data and errors
        context = {
            "title": "Create Material",
            "form_action": url_service.get_url_for_route("material_create"),
            "form_method": "POST",
            "options": {
                "types": material_types,
                "units": units_of_measure,
                "statuses": material_statuses
            },
            "errors": e.details,
            "form_data": dict(await request.form())
        }
        
        # Return to form with validation errors
        return context
    except Exception as e:
        log_controller_error(monitor_service, e, request, "create_material")
        raise

async def update_material_form(
    request: Request,
    material_id: str,
    material_service = get_material_service_dependency(),
    monitor_service = get_monitor_service_dependency()
):
    """
    Display the material update form (UI endpoint).
    
    Args:
        request: FastAPI request
        material_id: Material ID or number
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        Template context dictionary or redirect response
    """
    try:
        # Get the material
        material = material_service.get_material(material_id)
        
        # Get options for form dropdowns
        material_types = get_material_type_options()
        units_of_measure = get_unit_of_measure_options()
        material_statuses = get_material_status_options()
        
        # Build template context
        context = {
            "title": f"Edit Material: {material.name}",
            "material": material,
            "form_action": url_service.get_url_for_route("material_update", {"material_id": material_id}),
            "form_method": "POST",
            "options": {
                "types": material_types,
                "units": units_of_measure,
                "statuses": material_statuses
            },
            # Always include an empty form_data dictionary
            "form_data": {}
        }
        
        return context
    except NotFoundError:
        return handle_material_not_found(material_id, request)
    except Exception as e:
        log_controller_error(monitor_service, e, request, "update_material_form", material_id)
        raise

async def update_material(
    request: Request,
    material_id: str,
    material_service = get_material_service_dependency(),
    monitor_service = get_monitor_service_dependency()
):
    """
    Update an existing material (UI endpoint).
    
    Args:
        request: FastAPI request
        material_id: Material ID or number
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        Redirect to the material or back to the form with errors
    """
    try:
        # Parse form data
        form_data = await request.form()
        
        # Build material update data
        material_data = {}
        
        # Only include fields that were actually submitted
        if "name" in form_data:
            material_data["name"] = form_data.get("name")
        if "description" in form_data:
            material_data["description"] = form_data.get("description")
        if "type" in form_data:
            material_data["type"] = form_data.get("type")
        if "base_unit" in form_data:
            material_data["base_unit"] = form_data.get("base_unit")
        if "status" in form_data:
            material_data["status"] = form_data.get("status")
        if "weight" in form_data and form_data.get("weight"):
            material_data["weight"] = float(form_data.get("weight"))
        if "volume" in form_data and form_data.get("volume"):
            material_data["volume"] = float(form_data.get("volume"))
        
        # Update the material
        material_update = MaterialUpdate(**material_data)
        material = material_service.update_material(material_id, material_update)
        
        # Redirect to the material detail page
        return RedirectResponse(
            url=f"/materials/{material.material_number}",
            status_code=303  # See Other
        )
    except ValidationError as e:
        try:
            # Get the material for display in the form
            material = material_service.get_material(material_id)
            
            # Get options for form dropdowns
            material_types = get_material_type_options()
            units_of_measure = get_unit_of_measure_options()
            material_statuses = get_material_status_options()
            
            # Create context with form data and errors
            context = {
                "title": f"Edit Material: {material.name}",
                "material": material,
                "form_action": url_service.get_url_for_route("material_update", {"material_id": material_id}),
                "form_method": "POST",
                "options": {
                    "types": material_types,
                    "units": units_of_measure,
                    "statuses": material_statuses
                },
                "errors": e.details,
                "form_data": dict(await request.form())
            }
            
            # Return to form with validation errors
            return context
        except NotFoundError:
            return handle_material_not_found(material_id, request)
    except NotFoundError:
        return handle_material_not_found(material_id, request)
    except Exception as e:
        log_controller_error(monitor_service, e, request, "update_material", material_id)
        raise

async def deprecate_material(
    request: Request,
    material_id: str,
    material_service = get_material_service_dependency(),
    monitor_service = get_monitor_service_dependency()
):
    """
    Deprecate a material (UI endpoint).
    
    Args:
        request: FastAPI request
        material_id: Material ID or number
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        Redirect to the material or to the list with an error
    """
    try:
        # Deprecate the material
        material = material_service.deprecate_material(material_id)
        
        # Log successful action
        monitor_service.log_error(
            error_type="info",
            message=f"Material {material_id} successfully deprecated",
            component="material_ui_controller.deprecate_material",
            context={"path": str(request.url), "material_id": material_id}
        )
        
        # Redirect to the material detail page
        return RedirectResponse(
            url=f"/materials/{material.material_number}?message=Material+has+been+deprecated",
            status_code=303  # See Other
        )
    except ValidationError as e:
        # Log validation error
        monitor_service.log_error(
            error_type="validation_error",
            message=f"Error deprecating material {material_id}: {str(e)}",
            component="material_ui_controller.deprecate_material",
            context={"path": str(request.url), "material_id": material_id}
        )
        
        # If validation fails, redirect with error
        return RedirectResponse(
            url=f"/materials/{material_id}?error={str(e)}",
            status_code=303  # See Other
        )
    except NotFoundError:
        return handle_material_not_found(material_id, request)
    except Exception as e:
        log_controller_error(monitor_service, e, request, "deprecate_material", material_id)
        raise