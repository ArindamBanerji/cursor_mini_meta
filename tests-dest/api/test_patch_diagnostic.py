"""
Diagnostic tests for understanding why patching service getter functions doesn't work with FastAPI dependencies.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import asyncio
import inspect
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Depends
from fastapi.responses import JSONResponse

from controllers.material_common import (
    get_material_service_dependency,
    get_monitor_service_dependency
)
from services import get_material_service, get_monitor_service

# Simple controller function for testing
async 
def setup_module(module):
    """Set up the test module by ensuring PYTEST_CURRENT_TEST is set"""
    logger.info("Setting up test module")
    os.environ["PYTEST_CURRENT_TEST"] = "True"
    
def teardown_module(module):
    """Clean up after the test module"""
    logger.info("Tearing down test module")
    if "PYTEST_CURRENT_TEST" in os.environ:
        del os.environ["PYTEST_CURRENT_TEST"]
def test_controller(
    request: Request,
    material_service = get_material_service_dependency(),
    monitor_service = get_monitor_service_dependency()
):
    """Simple controller function for testing dependency injection."""
    # Print diagnostic information
    print(f"Type of material_service: {type(material_service)}")
    print(f"Material service ID: {id(material_service)}")
    print(f"Type of monitor_service: {type(monitor_service)}")
    print(f"Monitor service ID: {id(monitor_service)}")
    
    # Return a simple response
    return JSONResponse({"status": "ok"})

# Diagnostic function to inspect the dependency functions
def inspect_dependency_functions():
    """Inspect the dependency functions to understand how they work."""
    print("\n--- Inspecting dependency functions ---")
    
    # Get the dependency functions
    material_dep_func = get_material_service_dependency
    monitor_dep_func = get_monitor_service_dependency
    
    # Print information about the dependency functions
    print(f"Material dependency function: {material_dep_func}")
    print(f"Monitor dependency function: {monitor_dep_func}")
    
    # Get the dependency objects
    material_dep = material_dep_func()
    monitor_dep = monitor_dep_func()
    
    # Print information about the dependency objects
    print(f"Material dependency object: {material_dep}")
    print(f"Material dependency object type: {type(material_dep)}")
    print(f"Monitor dependency object: {monitor_dep}")
    print(f"Monitor dependency object type: {type(monitor_dep)}")
    
    # Check what the dependency objects contain
    if hasattr(material_dep, "dependency"):
        print(f"Material dependency.dependency: {material_dep.dependency}")
        print(f"Material dependency.dependency type: {type(material_dep.dependency)}")
    
    if hasattr(monitor_dep, "dependency"):
        print(f"Monitor dependency.dependency: {monitor_dep.dependency}")
        print(f"Monitor dependency.dependency type: {type(monitor_dep.dependency)}")

# Diagnostic function to test patching at different levels
@pytest.mark.asyncio
async def test_patching_levels():
    """Test patching at different levels to understand where the issue is."""
    print("\n--- Testing patching at different levels ---")
    
    # Create mock services
    mock_material_service = MagicMock()
    mock_material_service.list_materials = MagicMock(return_value=["test_material"])
    mock_material_service.__class__.__name__ = "MockMaterialService"
    
    mock_monitor_service = MagicMock()
    mock_monitor_service.log_error = MagicMock()
    mock_monitor_service.__class__.__name__ = "MockMonitorService"
    
    # Create mock request
    mock_request = AsyncMock(spec=Request)
    
    # Test 1: Patch the service getter functions
    print("\nTest 1: Patch the service getter functions")
    with patch('services.get_material_service', return_value=mock_material_service), \
         patch('services.get_monitor_service', return_value=mock_monitor_service):
        
        # Check if the patched functions return our mocks
        service1 = get_material_service()
        service2 = get_monitor_service()
        print(f"Direct call to get_material_service returns: {service1}")
        print(f"Direct call to get_monitor_service returns: {service2}")
        
        # Call the controller
        try:
            result = await test_controller(mock_request)
            print(f"Controller result: {result}")
        except Exception as e:
            print(f"Controller raised exception: {type(e).__name__}: {str(e)}")
    
    # Test 2: Patch the dependency functions
    print("\nTest 2: Patch the dependency functions")
    with patch('controllers.material_common.get_material_service_dependency', return_value=mock_material_service), \
         patch('controllers.material_common.get_monitor_service_dependency', return_value=mock_monitor_service):
        
        # Check if the patched functions return our mocks
        dep1 = get_material_service_dependency()
        dep2 = get_monitor_service_dependency()
        print(f"Direct call to get_material_service_dependency returns: {dep1}")
        print(f"Direct call to get_monitor_service_dependency returns: {dep2}")
        
        # Call the controller
        try:
            result = await test_controller(mock_request)
            print(f"Controller result: {result}")
        except Exception as e:
            print(f"Controller raised exception: {type(e).__name__}: {str(e)}")
    
    # Test 3: Patch the Depends object's dependency attribute
    print("\nTest 3: Patch the Depends object's dependency attribute")
    material_dep = get_material_service_dependency()
    monitor_dep = get_monitor_service_dependency()
    
    original_material_dep = material_dep.dependency
    original_monitor_dep = monitor_dep.dependency
    
    try:
        # Try to modify the dependency attribute
        material_dep.dependency = lambda: mock_material_service
        monitor_dep.dependency = lambda: mock_monitor_service
        
        # Call the controller
        try:
            result = await test_controller(mock_request)
            print(f"Controller result: {result}")
        except Exception as e:
            print(f"Controller raised exception: {type(e).__name__}: {str(e)}")
    finally:
        # Restore original dependencies
        material_dep.dependency = original_material_dep
        monitor_dep.dependency = original_monitor_dep

# Run the diagnostic functions
inspect_dependency_functions()

if __name__ == "__main__":
    # Run the tests directly if this file is executed
    asyncio.run(test_patching_levels()) 