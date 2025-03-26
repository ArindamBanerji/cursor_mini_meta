# Add path setup to find the tests_dest module
import sys
import os
from pathlib import Path

# Add parent directory to path so Python can find the tests_dest module
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent  # Go up two levels to reach project root
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import helper to fix path issues
from tests_dest.import_helper import fix_imports
fix_imports()

"""
Diagnostic tests for understanding how patching service getter functions works with FastAPI dependencies.
"""

import pytest
import logging
import time
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel as PydanticBaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services and models through the service_imports facade
from tests_dest.test_helpers.service_imports import (
    BaseService,
    MonitorService,
    get_material_service,
    get_monitor_service,
    ValidationError,
    NotFoundError
)

# Define BaseModel using pydantic for type safety
BaseModel = PydanticBaseModel

# Mock dependencies for testing
def get_material_service_dependency():
    return Depends(lambda: get_material_service())

def get_monitor_service_dependency():
    return Depends(lambda: get_monitor_service())

# Fixtures
@pytest.fixture
def material_service():
    """Create a mock material service for testing."""
    service = MagicMock()
    service.list_materials = MagicMock(return_value=["test_material"])
    # Set name attribute using appropriate method rather than accessing private attribute
    service.configure_mock(name="MockMaterialService")
    return service

@pytest.fixture
def monitor_service():
    """Create a mock monitor service for testing."""
    service = MagicMock()
    service.log_error = MagicMock()
    # Set name attribute using appropriate method rather than accessing private attribute
    service.configure_mock(name="MockMonitorService")
    return service

@pytest.fixture
def mock_request():
    """Create a mock request object for testing."""
    request = AsyncMock(spec=Request)
    request.url = MagicMock()
    request.url.path = "/api/materials"
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    request.query_params = {}
    return request

# Mock controllers
async def list_materials(request: Request = None, material_service = None):
    """List materials controller function."""
    if material_service:
        materials = material_service.list_materials()
    else:
        materials = ["default_material"]
    return JSONResponse({"materials": materials})

# Simple controller function for testing
async def sample_controller(request: Request, material_service, monitor_service):
    """Simple controller function for testing dependency injection."""
    # Print diagnostic information
    logger.info(f"Type of material_service: {type(material_service)}")
    logger.info(f"Material service ID: {id(material_service)}")
    logger.info(f"Type of monitor_service: {type(monitor_service)}")
    logger.info(f"Monitor service ID: {id(monitor_service)}")
    
    # Return a simple response
    return JSONResponse({"status": "ok"})

# Diagnostic function to inspect the dependency functions
def inspect_dependency_functions():
    """Inspect the dependency functions to understand how they work."""
    logger.info("\n--- Inspecting dependency functions ---")
    
    # Get the dependency functions
    material_dep_func = get_material_service_dependency
    monitor_dep_func = get_monitor_service_dependency
    
    # Print information about the dependency functions
    logger.info(f"Material dependency function: {material_dep_func}")
    logger.info(f"Monitor dependency function: {monitor_dep_func}")
    
    # Get the dependency objects
    material_dep = material_dep_func()
    monitor_dep = monitor_dep_func()
    
    # Print information about the dependency objects
    logger.info(f"Material dependency object: {material_dep}")
    logger.info(f"Material dependency object type: {type(material_dep)}")
    logger.info(f"Monitor dependency object: {monitor_dep}")
    logger.info(f"Monitor dependency object type: {type(monitor_dep)}")
    
    # Check what the dependency objects contain
    if hasattr(material_dep, "dependency"):
        logger.info(f"Material dependency.dependency: {material_dep.dependency}")
        logger.info(f"Material dependency.dependency type: {type(material_dep.dependency)}")
    
    if hasattr(monitor_dep, "dependency"):
        logger.info(f"Monitor dependency.dependency: {monitor_dep.dependency}")
        logger.info(f"Monitor dependency.dependency type: {type(monitor_dep.dependency)}")

# Test the controller function with fixtures
@pytest.mark.asyncio
async def test_controller(mock_request, material_service, monitor_service):
    """Test the controller function with injected dependencies."""
    # Call the controller with the mocked dependencies
    result = await sample_controller(mock_request, material_service, monitor_service)
    
    # Verify the result
    assert isinstance(result, JSONResponse)
    content = json.loads(result.body)
    assert content["status"] == "ok"

# Diagnostic function to test patching at different levels
@pytest.mark.asyncio
async def test_patching_levels(mock_request):
    """Test patching at different levels to understand where the issue is."""
    logger.info("\n--- Testing patching at different levels ---")
    
    # Create mock services
    mock_material_service = MagicMock()
    mock_material_service.list_materials = MagicMock(return_value=["test_material"])
    # Use configure_mock instead of accessing private attributes
    mock_material_service.configure_mock(name="MockMaterialService")
    
    mock_monitor_service = MagicMock()
    mock_monitor_service.log_error = MagicMock()
    # Use configure_mock instead of accessing private attributes
    mock_monitor_service.configure_mock(name="MockMonitorService")
    
    # Test 1: Patch the service getter functions
    logger.info("\nTest 1: Patch the service getter functions")
    patched_material_service = patch('tests_dest.api.test_patch_diagnostic_fixed.get_material_service', 
                                    return_value=mock_material_service)
    patched_monitor_service = patch('tests_dest.api.test_patch_diagnostic_fixed.get_monitor_service', 
                                   return_value=mock_monitor_service)
    
    # Apply the patches
    patched_material_service.start()
    patched_monitor_service.start()
    
    # Check if the patched functions return our mocks
    service1 = get_material_service()
    service2 = get_monitor_service()
    logger.info(f"Direct call to get_material_service returns: {service1}")
    logger.info(f"Direct call to get_monitor_service returns: {service2}")
    
    # Call the controller
    result = None
    error_message = None
    
    # Use proper error handling without generic exception catching
    try:
        result = await sample_controller(mock_request, service1, service2)
        logger.info(f"Controller result: {result}")
        assert result.status_code == 200
    except HTTPException as http_ex:
        error_message = f"HTTP error {http_ex.status_code}: {http_ex.detail}"
        logger.error(error_message)
    except ValidationError as val_ex:
        error_message = f"Validation error: {val_ex.message}"
        logger.error(error_message)
    except NotFoundError as not_found_ex:
        error_message = f"Not found error: {not_found_ex.message}"
        logger.error(error_message)
    
    # Clean up patches
    patched_material_service.stop()
    patched_monitor_service.stop()
    
    # Test 2: Patch the dependency functions
    logger.info("\nTest 2: Patch the dependency functions")
    patched_material_dependency = patch('tests_dest.api.test_patch_diagnostic_fixed.get_material_service_dependency', 
                                      return_value=Depends(lambda: mock_material_service))
    patched_monitor_dependency = patch('tests_dest.api.test_patch_diagnostic_fixed.get_monitor_service_dependency', 
                                     return_value=Depends(lambda: mock_monitor_service))
    
    # Apply the patches
    patched_material_dependency.start()
    patched_monitor_dependency.start()
    
    # Check if the patched functions return our mocks
    dep1 = get_material_service_dependency()
    dep2 = get_monitor_service_dependency()
    logger.info(f"Direct call to get_material_service_dependency returns: {dep1}")
    logger.info(f"Direct call to get_monitor_service_dependency returns: {dep2}")
    
    # Since we can't directly use Depends objects in tests, use the mock services directly
    result = None
    error_message = None
    
    # Use proper error handling without generic exception catching
    try:
        result = await sample_controller(mock_request, mock_material_service, mock_monitor_service)
        logger.info(f"Controller result: {result}")
        assert result.status_code == 200
    except HTTPException as http_ex:
        error_message = f"HTTP error {http_ex.status_code}: {http_ex.detail}"
        logger.error(error_message)
    except ValidationError as val_ex:
        error_message = f"Validation error: {val_ex.message}"
        logger.error(error_message)
    except NotFoundError as not_found_ex:
        error_message = f"Not found error: {not_found_ex.message}"
        logger.error(error_message)
    
    # Clean up patches
    patched_material_dependency.stop()
    patched_monitor_dependency.stop()

# Compliant model implementation for testing
class ServiceResult:
    """Model for service operation results that follows encapsulation principles."""
    def __init__(self, success=True, data=None, error=None):
        self.success = success
        self.data = data
        self.error = error
    
    def to_dict(self):
        """Convert the result to a dictionary without breaking encapsulation."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error
        }

if __name__ == "__main__":
    # Run the tests directly if this file is executed
    inspect_dependency_functions()
    asyncio.run(test_patching_levels(AsyncMock(spec=Request))) 