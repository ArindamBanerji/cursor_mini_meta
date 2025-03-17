# controllers/material_api_helpers.py
"""
Helper functions for the Material API Controller.

This module contains utility functions specifically for API endpoints
in the material controller to help with JSON response formatting
and consistent API error handling.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from fastapi import Request, Depends
from fastapi.responses import JSONResponse

from controllers import BaseController
from models.material import MaterialCreate, MaterialUpdate, Material
from services import get_material_service, get_monitor_service
from controllers.material_common import (
    format_material_for_response,
    format_materials_list,
    log_controller_error
)
from utils.error_utils import NotFoundError, ValidationError, BadRequestError, ConflictError

# Configure logging
logger = logging.getLogger("material_api_helpers")

async def handle_api_material_request(
    request: Request,
    operation: str,
    handler_func: callable,
    material_service=None, 
    monitor_service=None,
    *args, **kwargs
) -> JSONResponse:
    """
    Generic handler for API material requests with standardized error handling.
    
    Args:
        request: FastAPI request
        operation: Operation name for logging
        handler_func: Function to handle the actual request
        material_service: Optional material service for dependency injection
        monitor_service: Optional monitor service for dependency injection
        *args: Additional positional arguments for handler_func
        **kwargs: Additional keyword arguments for handler_func
        
    Returns:
        JSON response
    """
    # Get services if not provided (for backward compatibility)
    if material_service is None:
        material_service = get_material_service()
    if monitor_service is None:
        monitor_service = get_monitor_service()
        
    try:
        # Call the handler function
        return await handler_func(
            request=request, 
            material_service=material_service, 
            monitor_service=monitor_service,
            *args, **kwargs
        )
    except NotFoundError as e:
        material_id = kwargs.get('material_id', 'unknown')
        monitor_service.log_error(
            error_type="not_found_error",
            message=f"Material {material_id} not found in API {operation}",
            component=f"material_api_helpers.{operation}",
            context={"path": str(request.url), "material_id": material_id}
        )
        return BaseController.create_error_response(
            message=str(e),
            error_code="not_found",
            details={"material_id": material_id},
            status_code=404
        )
    except ValidationError as e:
        monitor_service.log_error(
            error_type="validation_error",
            message=f"Validation error in API {operation}: {str(e)}",
            component=f"material_api_helpers.{operation}",
            context={"path": str(request.url), "details": e.details}
        )
        return BaseController.create_error_response(
            message=str(e),
            error_code="validation_error",
            details=e.details,
            status_code=400
        )
    except BadRequestError as e:
        monitor_service.log_error(
            error_type="bad_request",
            message=f"Bad request in API {operation}: {str(e)}",
            component=f"material_api_helpers.{operation}",
            context={"path": str(request.url)}
        )
        return BaseController.create_error_response(
            message=str(e),
            error_code="bad_request",
            status_code=400
        )
    except ConflictError as e:
        monitor_service.log_error(
            error_type="conflict_error",
            message=f"Conflict in API {operation}: {str(e)}",
            component=f"material_api_helpers.{operation}",
            context={"path": str(request.url), "details": e.details if hasattr(e, 'details') else {}}
        )
        return BaseController.create_error_response(
            message=str(e),
            error_code="conflict",
            details=e.details if hasattr(e, 'details') else {},
            status_code=409
        )
    except Exception as e:
        log_controller_error(
            monitor_service, e, request, f"api_{operation}", 
            kwargs.get('material_id')
        )
        return BaseController.create_error_response(
            message="An unexpected error occurred",
            error_code="server_error",
            details={"error": str(e)},
            status_code=500
        )

async def handle_api_list_materials_request(
    request: Request,
    params: Any,
    material_service=None,
    monitor_service=None
) -> JSONResponse:
    """
    Handle listing materials for API.
    
    Args:
        request: FastAPI request
        params: Parsed query parameters
        material_service: Optional material service for dependency injection
        monitor_service: Optional monitor service for dependency injection
        
    Returns:
        JSON response with materials data
    """
    # Get materials with filtering
    materials = material_service.list_materials(
        status=params.status,
        type=params.type,
        search_term=params.search
    )
    
    # Build filters dict for response
    filters = {
        "search": params.search,
        "type": params.type.value if params.type else None,
        "status": params.status.value if params.status else None
    }
    
    # Format and return response
    formatted_materials = format_materials_list(materials, filters)
    return BaseController.create_success_response(
        data=formatted_materials,
        message="Materials retrieved successfully"
    )

async def handle_api_get_material_request(
    request: Request,
    material_id: str,
    material_service=None,
    monitor_service=None
) -> JSONResponse:
    """
    Handle getting material details for API.
    
    Args:
        request: FastAPI request
        material_id: Material ID or number
        material_service: Optional material service for dependency injection
        monitor_service: Optional monitor service for dependency injection
        
    Returns:
        JSON response with material data
    """
    # Get the material
    material = material_service.get_material(material_id)
    
    # Format material for response
    material_data = format_material_for_response(material)
    
    # Build API response
    return BaseController.create_success_response(
        data={"material": material_data},
        message=f"Material {material_id} retrieved successfully"
    )

async def handle_api_create_material_request(
    request: Request,
    material_data: MaterialCreate,
    material_service=None,
    monitor_service=None
) -> JSONResponse:
    """
    Handle creating material for API.
    
    Args:
        request: FastAPI request
        material_data: Parsed material creation data
        material_service: Optional material service for dependency injection
        monitor_service: Optional monitor service for dependency injection
        
    Returns:
        JSON response with created material data
    """
    # Create the material
    material = material_service.create_material(material_data)
    
    # Format for response
    formatted_material = format_material_for_response(material)
    
    # Return success response
    return BaseController.create_success_response(
        data={"material": formatted_material},
        message="Material created successfully",
        status_code=201  # Created
    )

async def handle_api_update_material_request(
    request: Request,
    material_id: str,
    update_data: MaterialUpdate,
    material_service=None,
    monitor_service=None
) -> JSONResponse:
    """
    Handle updating material for API.
    
    Args:
        request: FastAPI request
        material_id: Material ID to update
        update_data: Parsed material update data
        material_service: Optional material service for dependency injection
        monitor_service: Optional monitor service for dependency injection
        
    Returns:
        JSON response with updated material data
    """
    # Update the material
    material = material_service.update_material(material_id, update_data)
    
    # Format for response
    formatted_material = format_material_for_response(material)
    
    # Return success response
    return BaseController.create_success_response(
        data={"material": formatted_material},
        message=f"Material {material_id} updated successfully"
    )

async def handle_api_deprecate_material_request(
    request: Request,
    material_id: str,
    material_service=None,
    monitor_service=None
) -> JSONResponse:
    """
    Handle deprecating material for API.
    
    Args:
        request: FastAPI request
        material_id: Material ID to deprecate
        material_service: Optional material service for dependency injection
        monitor_service: Optional monitor service for dependency injection
        
    Returns:
        JSON response with deprecation result
    """
    # Deprecate the material
    material = material_service.deprecate_material(material_id)
    
    # Format for response
    response_data = {
        "material_number": material.material_number,
        "status": material.status.value,
        "updated_at": material.updated_at.isoformat()
    }
    
    # Return success response
    return BaseController.create_success_response(
        data=response_data,
        message=f"Material {material_id} has been deprecated"
    )