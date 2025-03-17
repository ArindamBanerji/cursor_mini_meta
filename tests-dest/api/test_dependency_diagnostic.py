"""
Diagnostic tests for understanding FastAPI dependency injection in tests.
This file contains tests to diagnose issues with mocking FastAPI dependencies.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
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
    print(f"Type of monitor_service: {type(monitor_service)}")
    
    # Try to access methods on the services
    try:
        if hasattr(material_service, 'list_materials'):
            print("material_service has list_materials method")
        else:
            print("material_service does NOT have list_materials method")
            
        if hasattr(monitor_service, 'log_error'):
            print("monitor_service has log_error method")
        else:
            print("monitor_service does NOT have log_error method")
    except Exception as e:
        print(f"Error accessing service methods: {str(e)}")
    
    # Return a simple response
    return JSONResponse({"status": "ok"})

# Test with different mocking approaches
@pytest.mark.parametrize("mock_approach", [
    "mock_dependency_function",
    "mock_service_getter",
    "direct_injection"
])
async def test_dependency_injection(mock_approach):
    """Test different approaches to mocking FastAPI dependencies."""
    print(f"\n--- Testing approach: {mock_approach} ---")
    
    # Create mock services
    mock_material_service = MagicMock()
    mock_material_service.list_materials = MagicMock(return_value=[])
    
    mock_monitor_service = MagicMock()
    mock_monitor_service.log_error = MagicMock()
    
    # Create mock request
    mock_request = AsyncMock(spec=Request)
    
    # Different mocking approaches
    if mock_approach == "mock_dependency_function":
        # Approach 1: Mock the dependency functions
        with patch('controllers.material_common.get_material_service_dependency') as mock_get_material_dep, \
             patch('controllers.material_common.get_monitor_service_dependency') as mock_get_monitor_dep:
            
            print("Setting up mock dependency functions")
            mock_get_material_dep.return_value = mock_material_service
            mock_get_monitor_dep.return_value = mock_monitor_service
            
            # Call the controller
            response = await test_controller(mock_request)
            print(f"Response status code: {response.status_code}")
    
    elif mock_approach == "mock_service_getter":
        # Approach 2: Mock the service getter functions
        with patch('services.get_material_service') as mock_get_material, \
             patch('services.get_monitor_service') as mock_get_monitor:
            
            print("Setting up mock service getters")
            mock_get_material.return_value = mock_material_service
            mock_get_monitor.return_value = mock_monitor_service
            
            # Call the controller
            response = await test_controller(mock_request)
            print(f"Response status code: {response.status_code}")
    
    elif mock_approach == "direct_injection":
        # Approach 3: Create a modified controller function with direct injection
        async def modified_controller(request, material_service, monitor_service):
            return await test_controller(request)
        
        print("Using direct injection")
        # Call the modified controller
        response = await modified_controller(mock_request, mock_material_service, mock_monitor_service)
        print(f"Response status code: {response.status_code}")

# Additional diagnostic test to inspect the Depends object
async def test_inspect_depends_object():
    """Inspect the Depends object to understand its structure."""
    print("\n--- Inspecting Depends objects ---")
    
    # Get the dependency objects
    material_dep = get_material_service_dependency()
    monitor_dep = get_monitor_service_dependency()
    
    # Print information about the dependency objects
    print(f"Type of material_dep: {type(material_dep)}")
    print(f"Dir of material_dep: {dir(material_dep)}")
    print(f"Repr of material_dep: {repr(material_dep)}")
    
    # Try to access the dependency callable
    if hasattr(material_dep, 'dependency'):
        print(f"material_dep.dependency: {material_dep.dependency}")
    
    # Check what happens when we call the dependency
    try:
        material_service = get_material_service()
        print(f"Type of material_service from direct call: {type(material_service)}")
        print(f"Has list_materials: {hasattr(material_service, 'list_materials')}")
    except Exception as e:
        print(f"Error calling get_material_service: {str(e)}")

if __name__ == "__main__":
    # Run the tests directly if this file is executed
    import asyncio
    
    async def run_tests():
        await test_dependency_injection("mock_dependency_function")
        await test_dependency_injection("mock_service_getter")
        await test_dependency_injection("direct_injection")
        await test_inspect_depends_object()
    
    asyncio.run(run_tests()) 