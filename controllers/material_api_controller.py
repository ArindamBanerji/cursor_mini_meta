# controllers/material_api_controller.py
"""
Controller for Material API endpoints.

This module handles all REST API routes for material management including:
- Listing materials (GET /api/v1/materials)
- Getting material details (GET /api/v1/materials/{material_id})
- Creating materials (POST /api/v1/materials)
- Updating materials (PUT /api/v1/materials/{material_id})
- Deprecating materials (POST /api/v1/materials/{material_id}/deprecate)
"""

from fastapi import Request, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List

from models.material import (
    Material, MaterialCreate, MaterialUpdate
)
from controllers import BaseController
from controllers.material_common import (
    get_material_service_dependency,
    get_monitor_service_dependency,
    format_material_for_response,
    format_materials_list,
    log_controller_error,
    MaterialFilterParams
)
from utils.error_utils import NotFoundError, ValidationError, BadRequestError

# API Controller Methods

async def api_list_materials(
    request: Request,
    material_service = get_material_service_dependency(),
    monitor_service = get_monitor_service_dependency()
):
    """
    List materials with optional filtering (API endpoint).
    
    Args:
        request: FastAPI request
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        JSON response with materials data
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
    except ValidationError as e:
        monitor_service.log_error(
            error_type="validation_error",
            message=f"Invalid query parameters in API list materials: {str(e)}",
            component="material_api_controller.api_list_materials",
            context={"path": str(request.url), "query_params": str(request.query_params)}
        )
        return BaseController.create_error_response(
            message=f"Invalid query parameters: {e.message}",
            error_code="validation_error",
            details=e.details,
            status_code=400
        )
    except Exception as e:
        log_controller_error(monitor_service, e, request, "api_list_materials")
        raise

async def api_get_material(
    request: Request,
    material_id: str,
    material_service = get_material_service_dependency(),
    monitor_service = get_monitor_service_dependency()
):
    """
    Get material details (API endpoint).
    
    Args:
        request: FastAPI request
        material_id: Material ID or number
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        JSON response with material data
    """
    try:
        # Get the material
        material = material_service.get_material(material_id)
        
        # Format material for response
        material_data = format_material_for_response(material)
        
        # Build API response
        return BaseController.create_success_response(
            data={"material": material_data},
            message=f"Material {material_id} retrieved successfully"
        )
    except NotFoundError as e:
        monitor_service.log_error(
            error_type="not_found_error",
            message=f"Material {material_id} not found in API request",
            component="material_api_controller.api_get_material",
            context={"path": str(request.url), "material_id": material_id}
        )
        return BaseController.create_error_response(
            message=f"Material {material_id} not found",
            error_code="not_found",
            details={"material_id": material_id},
            status_code=404
        )
    except Exception as e:
        log_controller_error(monitor_service, e, request, "api_get_material", material_id)
        raise

async def api_create_material(
    request: Request,
    material_service = get_material_service_dependency(),
    monitor_service = get_monitor_service_dependency()
):
    """
    Create a new material (API endpoint).
    
    Args:
        request: FastAPI request
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        JSON response with created material data
    """
    try:
        # Parse request body
        material_data = await BaseController.parse_json_body(request, MaterialCreate)
        
        # Create the material
        material = material_service.create_material(material_data)
        
        # Format response
        formatted_material = format_material_for_response(material)
        
        # Return success response
        return BaseController.create_success_response(
            data={"material": formatted_material},
            message="Material created successfully",
            status_code=201  # Created
        )
    except ValidationError as e:
        monitor_service.log_error(
            error_type="validation_error",
            message=f"Invalid material data in API create: {str(e)}",
            component="material_api_controller.api_create_material",
            context={"path": str(request.url), "details": e.details}
        )
        return BaseController.create_error_response(
            message=f"Invalid material data: {e.message}",
            error_code="validation_error",
            details=e.details,
            status_code=400
        )
    except BadRequestError as e:
        monitor_service.log_error(
            error_type="bad_request",
            message=f"Bad request in API create material: {str(e)}",
            component="material_api_controller.api_create_material",
            context={"path": str(request.url)}
        )
        return BaseController.create_error_response(
            message=str(e),
            error_code="bad_request",
            status_code=400
        )
    except Exception as e:
        log_controller_error(monitor_service, e, request, "api_create_material")
        raise

async def api_update_material(
    request: Request,
    material_id: str,
    material_service = get_material_service_dependency(),
    monitor_service = get_monitor_service_dependency()
):
    """
    Update an existing material (API endpoint).
    
    Args:
        request: FastAPI request
        material_id: Material ID or number
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        JSON response with updated material data
    """
    try:
        # Parse request body
        update_data = await BaseController.parse_json_body(request, MaterialUpdate)
        
        # Update the material
        material = material_service.update_material(material_id, update_data)
        
        # Format response
        formatted_material = format_material_for_response(material)
        
        # Return success response
        return BaseController.create_success_response(
            data={"material": formatted_material},
            message=f"Material {material_id} updated successfully"
        )
    except NotFoundError as e:
        monitor_service.log_error(
            error_type="not_found_error",
            message=f"Material {material_id} not found in API update request",
            component="material_api_controller.api_update_material",
            context={"path": str(request.url), "material_id": material_id}
        )
        return BaseController.create_error_response(
            message=f"Material {material_id} not found",
            error_code="not_found",
            details={"material_id": material_id},
            status_code=404
        )
    except ValidationError as e:
        monitor_service.log_error(
            error_type="validation_error",
            message=f"Invalid update data in API update material: {str(e)}",
            component="material_api_controller.api_update_material",
            context={"path": str(request.url), "material_id": material_id}
        )
        return BaseController.create_error_response(
            message=f"Invalid update data: {e.message}",
            error_code="validation_error",
            details=e.details,
            status_code=400
        )
    except BadRequestError as e:
        monitor_service.log_error(
            error_type="bad_request",
            message=f"Bad request in API update material: {str(e)}",
            component="material_api_controller.api_update_material",
            context={"path": str(request.url), "material_id": material_id}
        )
        return BaseController.create_error_response(
            message=str(e),
            error_code="bad_request",
            status_code=400
        )
    except Exception as e:
        log_controller_error(monitor_service, e, request, "api_update_material", material_id)
        raise

async def api_deprecate_material(
    request: Request,
    material_id: str,
    material_service = get_material_service_dependency(),
    monitor_service = get_monitor_service_dependency()
):
    """
    Deprecate a material (API endpoint).
    
    Args:
        request: FastAPI request
        material_id: Material ID or number
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        JSON response with deprecation result
    """
    try:
        # Deprecate the material
        material = material_service.deprecate_material(material_id)
        
        # Format response
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
    except NotFoundError as e:
        monitor_service.log_error(
            error_type="not_found_error",
            message=f"Material {material_id} not found in API deprecate request",
            component="material_api_controller.api_deprecate_material",
            context={"path": str(request.url), "material_id": material_id}
        )
        return BaseController.create_error_response(
            message=f"Material {material_id} not found",
            error_code="not_found",
            details={"material_id": material_id},
            status_code=404
        )
    except ValidationError as e:
        monitor_service.log_error(
            error_type="validation_error",
            message=f"Cannot deprecate material {material_id}: {str(e)}",
            component="material_api_controller.api_deprecate_material",
            context={"path": str(request.url), "material_id": material_id}
        )
        return BaseController.create_error_response(
            message=f"Cannot deprecate material: {e.message}",
            error_code="validation_error",
            details=e.details,
            status_code=400
        )
    except Exception as e:
        log_controller_error(monitor_service, e, request, "api_deprecate_material", material_id)
        raise