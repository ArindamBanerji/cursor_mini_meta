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

from fastapi import Request, Depends, Response, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import logging

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
from services import get_material_service, get_monitor_service
from services.material_service import MaterialService
from services.monitor_service import MonitorService
from utils.error_utils import NotFoundError, ValidationError, BadRequestError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Material API Controller class for dependency injection
class MaterialAPIController:
    """Material API controller class that handles material-related API operations."""
    
    def __init__(self, material_service=None, monitor_service=None):
        """Initialize with required services."""
        self.material_service = material_service
        self.monitor_service = monitor_service
    
    async def api_get_material(self, request: Request, material_id: str):
        """API endpoint to get a material by ID."""
        try:
            material = self.material_service.get_material(material_id)
            if not material:
                raise HTTPException(status_code=404, detail=f"Material {material_id} not found")
            return {"status": "success", "data": material}
        except Exception as e:
            logger.error(f"Error getting material {material_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def api_list_materials(self, request: Request):
        """API endpoint to list all materials."""
        try:
            materials = self.material_service.list_materials()
            return {"status": "success", "data": materials}
        except Exception as e:
            logger.error(f"Error listing materials: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def api_create_material(self, request: Request):
        """API endpoint to create a new material."""
        try:
            data = await request.json()
            material = self.material_service.create_material(data)
            return {"status": "success", "data": material}
        except Exception as e:
            logger.error(f"Error creating material: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def api_update_material(self, request: Request, material_id: str):
        """API endpoint to update an existing material."""
        try:
            data = await request.json()
            material = self.material_service.update_material(material_id, data)
            if not material:
                raise HTTPException(status_code=404, detail=f"Material {material_id} not found")
            return {"status": "success", "data": material}
        except Exception as e:
            logger.error(f"Error updating material {material_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def api_deprecate_material(self, request: Request, material_id: str):
        """API endpoint to deprecate a material."""
        try:
            success = self.material_service.deprecate_material(material_id)
            if not success:
                raise HTTPException(status_code=404, detail=f"Material {material_id} not found")
            return {"status": "success", "message": f"Material {material_id} deprecated"}
        except Exception as e:
            logger.error(f"Error deprecating material {material_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Function to create a material API controller instance
def get_material_api_controller(material_service=None, monitor_service=None):
    """Create a material API controller instance.
    
    Args:
        material_service: The material service to use
        monitor_service: The monitor service to use
        
    Returns:
        A MaterialAPIController instance
    """
    return MaterialAPIController(
        material_service=material_service,
        monitor_service=monitor_service
    )

# API endpoint functions - these are wrappers around the controller methods
async def api_get_material(request: Request, material_id: str):
    """API endpoint to get a material by ID."""
    controller = get_material_api_controller()
    return await controller.api_get_material(request, material_id)

async def api_list_materials(request: Request):
    """API endpoint to list all materials."""
    controller = get_material_api_controller()
    return await controller.api_list_materials(request)

async def api_create_material(request: Request):
    """API endpoint to create a new material."""
    controller = get_material_api_controller()
    return await controller.api_create_material(request)

async def api_update_material(request: Request, material_id: str):
    """API endpoint to update an existing material."""
    controller = get_material_api_controller()
    return await controller.api_update_material(request, material_id)

async def api_deprecate_material(request: Request, material_id: str):
    """API endpoint to deprecate a material."""
    controller = get_material_api_controller()
    return await controller.api_deprecate_material(request, material_id)

# API Controller Methods

async def api_list_materials(
    request: Request,
    material_service=None,
    monitor_service=None
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
    # Get services if not provided (for testing)
    if material_service is None or (not isinstance(material_service, MaterialService) and hasattr(material_service, 'dependency')):
        material_service = get_material_service_dependency()
        if not isinstance(material_service, MaterialService) and hasattr(material_service, 'dependency'):
            material_service = get_material_service()
            
    if monitor_service is None or (not isinstance(monitor_service, MonitorService) and hasattr(monitor_service, 'dependency')):
        monitor_service = get_monitor_service_dependency()
        if not isinstance(monitor_service, MonitorService) and hasattr(monitor_service, 'dependency'):
            monitor_service = get_monitor_service()
        
    try:
        # Parse query parameters
        params = await BaseController.parse_query_params(request, MaterialFilterParams)
        
        # Get materials with filtering - only pass parameters supported by the service
        materials = material_service.list_materials(
            status=params.status,
            type=params.type,
            search_term=params.search
        )
        
        # Apply pagination in memory if needed
        if params.limit is not None or params.offset is not None:
            offset = params.offset or 0
            limit = params.limit or len(materials)
            materials = materials[offset:offset + limit]
        
        # Format the response
        response_data = format_materials_list(materials, {
            "search": params.search,
            "type": params.type.value if params.type else None,
            "status": params.status.value if params.status else None,
            "limit": params.limit,
            "offset": params.offset
        })
        
        return JSONResponse(content=response_data)
    except Exception as e:
        log_controller_error(monitor_service, e, request, "api_list_materials")
        return BaseController.handle_api_error(e)

async def api_get_material(
    request: Request,
    material_id: str,
    material_service=None,
    monitor_service=None
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
    # Get services if not provided (for testing)
    if material_service is None or (not isinstance(material_service, MaterialService) and hasattr(material_service, 'dependency')):
        material_service = get_material_service_dependency()
        if not isinstance(material_service, MaterialService) and hasattr(material_service, 'dependency'):
            material_service = get_material_service()
            
    if monitor_service is None or (not isinstance(monitor_service, MonitorService) and hasattr(monitor_service, 'dependency')):
        monitor_service = get_monitor_service_dependency()
        if not isinstance(monitor_service, MonitorService) and hasattr(monitor_service, 'dependency'):
            monitor_service = get_monitor_service()
        
    try:
        # Get the material
        material = material_service.get_material(material_id)
        
        # Format the response
        response_data = format_material_for_response(material)
        
        return JSONResponse(content=response_data)
    except NotFoundError as e:
        # Log the not found error
        monitor_service.log_error(
            error_type="not_found_error",
            message=f"Material {material_id} not found in API request",
            component="material_api_controller",
            context={"path": str(request.url), "material_id": material_id}
        )
        return BaseController.handle_api_error(e)
    except Exception as e:
        log_controller_error(monitor_service, e, request, "api_get_material", material_id)
        return BaseController.handle_api_error(e)

async def api_create_material(
    request: Request,
    material_service=None,
    monitor_service=None
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
    # Get services if not provided (for testing)
    if material_service is None or (not isinstance(material_service, MaterialService) and hasattr(material_service, 'dependency')):
        material_service = get_material_service_dependency()
        if not isinstance(material_service, MaterialService) and hasattr(material_service, 'dependency'):
            material_service = get_material_service()
            
    if monitor_service is None or (not isinstance(monitor_service, MonitorService) and hasattr(monitor_service, 'dependency')):
        monitor_service = get_monitor_service_dependency()
        if not isinstance(monitor_service, MonitorService) and hasattr(monitor_service, 'dependency'):
            monitor_service = get_monitor_service()
        
    try:
        # Parse request body using the helper method
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
    except Exception as e:
        log_controller_error(monitor_service, e, request, "api_create_material")
        return BaseController.handle_api_error(e)

async def api_update_material(
    request: Request,
    material_id: str,
    material_service=None,
    monitor_service=None
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
    # Get services if not provided (for testing)
    if material_service is None or (not isinstance(material_service, MaterialService) and hasattr(material_service, 'dependency')):
        material_service = get_material_service_dependency()
        if not isinstance(material_service, MaterialService) and hasattr(material_service, 'dependency'):
            material_service = get_material_service()
            
    if monitor_service is None or (not isinstance(monitor_service, MonitorService) and hasattr(monitor_service, 'dependency')):
        monitor_service = get_monitor_service_dependency()
        if not isinstance(monitor_service, MonitorService) and hasattr(monitor_service, 'dependency'):
            monitor_service = get_monitor_service()
        
    try:
        # Parse request body using the helper method
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
        # Log the not found error
        monitor_service.log_error(
            error_type="not_found_error",
            message=f"Material {material_id} not found in API update request",
            component="material_api_controller",
            context={"path": str(request.url), "material_id": material_id}
        )
        return BaseController.handle_api_error(e)
    except Exception as e:
        log_controller_error(monitor_service, e, request, "api_update_material", material_id)
        return BaseController.handle_api_error(e)

async def api_deprecate_material(
    request: Request,
    material_id: str,
    material_service=None,
    monitor_service=None
):
    """
    Deprecate an existing material (API endpoint).
    
    Args:
        request: FastAPI request
        material_id: Material ID or number
        material_service: Injected material service
        monitor_service: Injected monitor service
        
    Returns:
        JSON response with deprecation status
    """
    # Get services if not provided (for testing)
    if material_service is None or (not isinstance(material_service, MaterialService) and hasattr(material_service, 'dependency')):
        material_service = get_material_service_dependency()
        if not isinstance(material_service, MaterialService) and hasattr(material_service, 'dependency'):
            material_service = get_material_service()
            
    if monitor_service is None or (not isinstance(monitor_service, MonitorService) and hasattr(monitor_service, 'dependency')):
        monitor_service = get_monitor_service_dependency()
        if not isinstance(monitor_service, MonitorService) and hasattr(monitor_service, 'dependency'):
            monitor_service = get_monitor_service()
        
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
        # Log the not found error
        monitor_service.log_error(
            error_type="not_found_error",
            message=f"Material {material_id} not found in API deprecate request",
            component="material_api_controller",
            context={"path": str(request.url), "material_id": material_id}
        )
        return BaseController.handle_api_error(e)
    except Exception as e:
        log_controller_error(monitor_service, e, request, "api_deprecate_material", material_id)
        return BaseController.handle_api_error(e)