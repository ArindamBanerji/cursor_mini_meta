# controllers/material_controller_helpers.py
"""
Helper functions for the Material UI Controller.

This module contains utility functions and helpers for UI handling in the material controller.
These functions support the UI controller with form processing and context preparation.
"""

import logging
from typing import Dict, Any, Optional, List, Union, Tuple, cast
from fastapi import Request
from fastapi.responses import RedirectResponse

from models.material import (
    Material, MaterialCreate, MaterialUpdate, MaterialType, MaterialStatus, UnitOfMeasure
)
from services import get_material_service, get_monitor_service
from controllers import BaseController
from controllers.material_common import (
    get_material_type_options,
    get_material_status_options,
    get_unit_of_measure_options,
    handle_material_not_found,
    log_controller_error
)
from utils.error_utils import NotFoundError, ValidationError, BadRequestError

# Configure logging
logger = logging.getLogger("material_controller_helpers")

async def prepare_material_list_context(
    request: Request,
    material_service=None,
    monitor_service=None
) -> Dict[str, Any]:
    """
    Prepare context for material list template.
    
    Args:
        request: FastAPI request
        material_service: Optional material service for dependency injection
        monitor_service: Optional monitor service for dependency injection
        
    Returns:
        Template context dictionary
    """
    # Get services if not provided (for backward compatibility)
    if material_service is None:
        material_service = get_material_service()
    if monitor_service is None:
        monitor_service = get_monitor_service()
    
    try:
        # Parse query parameters
        from controllers.material_common import MaterialFilterParams
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
        log_controller_error(
            monitor_service, e, request, "prepare_material_list_context"
        )
        raise

async def prepare_material_detail_context(
    request: Request,
    material_id: str,
    material_service=None,
    monitor_service=None
) -> Dict[str, Any]:
    """
    Prepare context for material detail template.
    
    Args:
        request: FastAPI request
        material_id: Material ID or number
        material_service: Optional material service for dependency injection
        monitor_service: Optional monitor service for dependency injection
        
    Returns:
        Template context dictionary
    """
    # Get services if not provided (for backward compatibility)
    if material_service is None:
        material_service = get_material_service()
    if monitor_service is None:
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
        
        return context
    except NotFoundError:
        # Log the error
        monitor_service.log_error(
            error_type="not_found_error",
            message=f"Material {material_id} not found in detail page",
            component="material_controller_helpers",
            context={"path": str(request.url), "material_id": material_id}
        )
        
        # Re-raise the error for controller to handle redirect
        raise
    except Exception as e:
        log_controller_error(
            monitor_service, e, request, "prepare_material_detail_context", material_id
        )
        raise

async def prepare_create_form_context(
    request: Request,
    material_service=None,
    monitor_service=None
) -> Dict[str, Any]:
    """
    Prepare context for material creation form.
    
    Args:
        request: FastAPI request
        material_service: Optional material service for dependency injection
        monitor_service: Optional monitor service for dependency injection
        
    Returns:
        Template context dictionary
    """
    # Get services if not provided (for backward compatibility)
    if monitor_service is None:
        monitor_service = get_monitor_service()
    
    try:
        # Get options for form dropdowns
        material_types = get_material_type_options()
        units_of_measure = get_unit_of_measure_options()
        material_statuses = get_material_status_options()
        
        # Build template context
        from services.url_service import url_service
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
        log_controller_error(
            monitor_service, e, request, "prepare_create_form_context"
        )
        raise

async def prepare_update_form_context(
    request: Request,
    material_id: str,
    material_service=None,
    monitor_service=None
) -> Dict[str, Any]:
    """
    Prepare context for material update form.
    
    Args:
        request: FastAPI request
        material_id: Material ID or number
        material_service: Optional material service for dependency injection
        monitor_service: Optional monitor service for dependency injection
        
    Returns:
        Template context dictionary
    """
    # Get services if not provided (for backward compatibility)
    if material_service is None:
        material_service = get_material_service()
    if monitor_service is None:
        monitor_service = get_monitor_service()
    
    try:
        # Get the material
        material = material_service.get_material(material_id)
        
        # Get options for form dropdowns
        material_types = get_material_type_options()
        units_of_measure = get_unit_of_measure_options()
        material_statuses = get_material_status_options()
        
        # Build template context
        from services.url_service import url_service
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
        # Log the error and re-raise for controller to handle redirect
        monitor_service.log_error(
            error_type="not_found_error",
            message=f"Material {material_id} not found in update form",
            component="material_controller_helpers",
            context={"path": str(request.url), "material_id": material_id}
        )
        raise
    except Exception as e:
        log_controller_error(
            monitor_service, e, request, "prepare_update_form_context", material_id
        )
        raise

async def process_create_form(
    request: Request,
    material_service=None,
    monitor_service=None
) -> Union[Material, Dict[str, Any]]:
    """
    Process the material creation form submission.
    
    Args:
        request: FastAPI request
        material_service: Optional material service for dependency injection
        monitor_service: Optional monitor service for dependency injection
        
    Returns:
        Created material or form context with errors
    """
    # Get services if not provided (for backward compatibility)
    if material_service is None:
        material_service = get_material_service()
    if monitor_service is None:
        monitor_service = get_monitor_service()
    
    try:
        # Parse form data asynchronously
        form_data = await request.form()
        form_dict = dict(form_data)
        
        # Build material creation data
        material_data = {
            "name": form_dict.get("name"),
            "description": form_dict.get("description"),
            "type": form_dict.get("type"),
            "base_unit": form_dict.get("base_unit"),
            "status": form_dict.get("status", MaterialStatus.ACTIVE.value)
        }
        
        # Add optional numeric fields if provided
        if form_dict.get("weight"):
            try:
                material_data["weight"] = float(form_dict.get("weight"))
            except (ValueError, TypeError):
                # Handle invalid number format
                raise ValidationError(
                    message="Invalid weight value",
                    details={"validation_errors": {"weight": "Weight must be a valid number"}}
                )
                
        if form_dict.get("volume"):
            try:
                material_data["volume"] = float(form_dict.get("volume"))
            except (ValueError, TypeError):
                # Handle invalid number format
                raise ValidationError(
                    message="Invalid volume value",
                    details={"validation_errors": {"volume": "Volume must be a valid number"}}
                )
        
        # Create the material
        material_create = MaterialCreate(**material_data)
        material = material_service.create_material(material_create)
        
        return material
    except ValidationError as e:
        # Return to form with validation errors
        context = await prepare_create_form_context(request, material_service, monitor_service)
        context["errors"] = e.details.get("validation_errors", {})
        context["form_data"] = form_dict
        return context
    except Exception as e:
        log_controller_error(
            monitor_service, e, request, "process_create_form"
        )
        raise

async def process_update_form(
    request: Request,
    material_id: str,
    material_service=None,
    monitor_service=None
) -> Union[Material, Dict[str, Any]]:
    """
    Process the material update form submission.
    
    Args:
        request: FastAPI request
        material_id: Material ID or number
        material_service: Optional material service for dependency injection
        monitor_service: Optional monitor service for dependency injection
        
    Returns:
        Updated material or form context with errors
    """
    # Get services if not provided (for backward compatibility)
    if material_service is None:
        material_service = get_material_service()
    if monitor_service is None:
        monitor_service = get_monitor_service()
    
    try:
        # Parse form data asynchronously
        form_data = await request.form()
        form_dict = dict(form_data)
        
        # Build material update data
        material_data = {}
        
        # Only include fields that were actually submitted
        if "name" in form_dict:
            material_data["name"] = form_dict.get("name")
        if "description" in form_dict:
            material_data["description"] = form_dict.get("description")
        if "type" in form_dict:
            material_data["type"] = form_dict.get("type")
        if "base_unit" in form_dict:
            material_data["base_unit"] = form_dict.get("base_unit")
        if "status" in form_dict:
            material_data["status"] = form_dict.get("status")
        
        # Add optional numeric fields if provided
        if "weight" in form_dict and form_dict.get("weight"):
            try:
                material_data["weight"] = float(form_dict.get("weight"))
            except (ValueError, TypeError):
                # Handle invalid number format
                raise ValidationError(
                    message="Invalid weight value",
                    details={"validation_errors": {"weight": "Weight must be a valid number"}}
                )
                
        if "volume" in form_dict and form_dict.get("volume"):
            try:
                material_data["volume"] = float(form_dict.get("volume"))
            except (ValueError, TypeError):
                # Handle invalid number format
                raise ValidationError(
                    message="Invalid volume value",
                    details={"validation_errors": {"volume": "Volume must be a valid number"}}
                )
        
        # Update the material
        material_update = MaterialUpdate(**material_data)
        material = material_service.update_material(material_id, material_update)
        
        return material
    except ValidationError as e:
        try:
            # Return to form with validation errors
            context = await prepare_update_form_context(request, material_id, material_service, monitor_service)
            context["errors"] = e.details.get("validation_errors", {})
            context["form_data"] = form_dict
            return context
        except NotFoundError:
            # Let the controller handle the redirect
            raise
    except NotFoundError:
        # Let the controller handle the redirect
        monitor_service.log_error(
            error_type="not_found_error",
            message=f"Material {material_id} not found in update form submission",
            component="material_controller_helpers",
            context={"path": str(request.url), "material_id": material_id}
        )
        raise
    except Exception as e:
        log_controller_error(
            monitor_service, e, request, "process_update_form", material_id
        )
        raise