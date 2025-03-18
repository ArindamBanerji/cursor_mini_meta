# controllers/material_common.py
"""
Common functionality for material controllers.

This module contains shared functions and utilities used by both
the UI and API material controllers.
"""

import logging
from typing import Dict, Any, Optional, List, Callable, Type

from pydantic import BaseModel, Field

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse

from models.material import (
    Material, MaterialCreate, MaterialUpdate, MaterialType, MaterialStatus, UnitOfMeasure
)
from services import get_material_service, get_monitor_service
from controllers import BaseController
from utils.error_utils import NotFoundError, ValidationError, BadRequestError

# Configure logging
logger = logging.getLogger("material_controllers")

# Service dependencies
def get_material_service_dependency():
    """Dependency for material service injection"""
    return Depends(get_material_service)

def get_monitor_service_dependency():
    """Dependency for monitor service injection"""
    return Depends(get_monitor_service)

# Common error handling functions

def format_material_for_response(material: Material) -> Dict[str, Any]:
    """
    Format a material object for response (both API and UI).
    
    Args:
        material: Material object
        
    Returns:
        Formatted material dictionary
    """
    return {
        "material_number": material.material_number,
        "name": material.name,
        "description": material.description,
        "type": material.type.value,
        "status": material.status.value,
        "base_unit": material.base_unit.value,
        "weight": material.weight,
        "volume": material.volume,
        "dimensions": material.dimensions,
        "created_at": material.created_at.isoformat(),
        "updated_at": material.updated_at.isoformat()
    }

def format_materials_list(materials: List[Material], filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Format a list of materials for response.
    
    Args:
        materials: List of material objects
        filters: Optional filter criteria used
        
    Returns:
        Formatted materials list dictionary
    """
    return {
        "materials": [format_material_for_response(m) for m in materials],
        "count": len(materials),
        "filters": filters or {}
    }

def get_material_type_options() -> List[str]:
    """Get all available material types as string values"""
    return [t.value for t in MaterialType]

def get_material_status_options() -> List[str]:
    """Get all available material statuses as string values"""
    return [s.value for s in MaterialStatus]

def get_unit_of_measure_options() -> List[str]:
    """Get all available units of measure as string values"""
    return [u.value for u in UnitOfMeasure]

def handle_material_not_found(material_id: str, request: Request) -> RedirectResponse:
    """
    Handle not found errors consistently.
    
    Args:
        material_id: Material ID that was not found
        request: FastAPI request
        
    Returns:
        Redirect response to materials list with 303 See Other status
    """
    logger.warning(f"Material {material_id} not found, redirecting to list")
    
    # Return a redirect to the materials list with error message
    return BaseController.redirect_to_route(
        route_name="material_list",
        query_params={"error": f"Material {material_id} not found"},
        status_code=303  # Use 303 See Other for redirects after operations
    )

def log_controller_error(monitor_service, e: Exception, request: Request, component: str, material_id: Optional[str] = None) -> None:
    """
    Log controller errors consistently.
    
    Args:
        monitor_service: Monitor service for logging
        e: Exception that occurred
        request: FastAPI request
        component: Component name for logging
        material_id: Optional material ID for context
    """
    # Build context
    context = {"path": str(request.url)}
    if material_id:
        context["material_id"] = material_id
    
    # Log the error
    logger.error(f"Error in {component}: {str(e)}", exc_info=True)
    monitor_service.log_error(
        error_type="controller_error",
        message=f"Error in {component}: {str(e)}",
        component="material_controller",
        context=context
    )

class MaterialFilterParams(BaseModel):
    """Parameters for material search and filtering"""
    search: Optional[str] = None
    type: Optional[MaterialType] = None
    status: Optional[MaterialStatus] = None
    limit: Optional[int] = Field(None, ge=1, le=100)
    offset: Optional[int] = Field(None, ge=0)

# Add imports for BaseModel and Field
from pydantic import BaseModel, Field