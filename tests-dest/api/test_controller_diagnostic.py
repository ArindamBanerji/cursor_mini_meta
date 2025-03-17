"""
Diagnostic tests for comparing different approaches to testing FastAPI controllers.

This file contains tests that compare:
1. The original approach using patch decorators
2. The new approach using unwrap_dependencies
3. A hybrid approach

The goal is to understand the pros and cons of each approach and identify any issues.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import asyncio
import inspect
import time
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Depends
from fastapi.responses import JSONResponse

from controllers.material_common import (
    get_material_service_dependency,
    get_monitor_service_dependency
)
from controllers.material_ui_controller import list_materials
from api.test_helpers import unwrap_dependencies, create_controller_test
from models.material import Material, MaterialType, UnitOfMeasure, MaterialStatus

# Create test data
TEST_MATERIAL = Material(
    material_number="MAT12345",
    name="Test Material",
    description="Test Description",
    type=MaterialType.FINISHED,
    base_unit=UnitOfMeasure.EACH,
    status=MaterialStatus.ACTIVE
)

# Fixtures
@pytest.fixture
def mock_request():
    """Create a mock request object for testing."""
    request = AsyncMock(spec=Request)
    request.url = MagicMock()
    request.url.path = "/materials"
    request.query_params = {}
    return request

@pytest.fixture
def mock_material_service():
    """Create a mock material service for testing."""
    service = MagicMock()
    service.get_material.return_value = TEST_MATERIAL
    service.list_materials.return_value = [TEST_MATERIAL]
    return service

@pytest.fixture
def mock_monitor_service():
    """Create a mock monitor service for testing."""
    service = MagicMock()
    service.log_error = MagicMock()
    return service

# Diagnostic tests

@pytest.mark.asyncio
@patch('services.get_material_service')
@patch('services.get_monitor_service')
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
def test_original_approach(mock_get_monitor, mock_get_material, mock_request, mock_material_service, mock_monitor_service):
    """Test the original approach using patch decorators."""
    print("\n--- Testing original approach with patch decorators ---")
    start_time = time.time()
    
    # Setup mocks
    mock_get_material.return_value = mock_material_service
    mock_get_monitor.return_value = mock_monitor_service
    
    # Call the function - expect it to fail with AttributeError
    with pytest.raises(AttributeError) as excinfo:
        await list_materials(mock_request)
    
    # Verify the error message
    assert "'Depends' object has no attribute" in str(excinfo.value)
    
    # Print diagnostic information
    print(f"Original approach execution time: {time.time() - start_time:.6f} seconds")
    print(f"Expected error occurred: {excinfo.value}")
    print("This demonstrates why the original approach doesn't work with FastAPI dependencies.")

@pytest.mark.asyncio
async def test_unwrap_approach(mock_request, mock_material_service, mock_monitor_service):
    """Test the new approach using unwrap_dependencies."""
    print("\n--- Testing new approach with unwrap_dependencies ---")
    start_time = time.time()
    
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        list_materials,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    result = await wrapped(mock_request)
    
    # Verify result
    assert "materials" in result
    assert result["materials"] == [TEST_MATERIAL]
    assert "count" in result
    assert result["count"] == 1
    mock_material_service.list_materials.assert_called_once()
    
    # Print diagnostic information
    print(f"Unwrap approach execution time: {time.time() - start_time:.6f} seconds")
    print(f"Result type: {type(result)}")
    print(f"Materials count: {result['count']}")
    print(f"Mock calls: {mock_material_service.list_materials.call_count}")

@pytest.mark.asyncio
async def test_create_controller_test_approach(mock_request, mock_material_service, mock_monitor_service):
    """Test the approach using create_controller_test."""
    print("\n--- Testing approach with create_controller_test ---")
    start_time = time.time()
    
    # Create test function
    test_func = create_controller_test(list_materials)
    
    # Call the test function
    result = await test_func(
        mock_request=mock_request,
        mock_material_service=mock_material_service,
        mock_monitor_service=mock_monitor_service
    )
    
    # Verify result
    assert "materials" in result
    assert result["materials"] == [TEST_MATERIAL]
    assert "count" in result
    assert result["count"] == 1
    mock_material_service.list_materials.assert_called_once()
    
    # Print diagnostic information
    print(f"create_controller_test approach execution time: {time.time() - start_time:.6f} seconds")
    print(f"Result type: {type(result)}")
    print(f"Materials count: {result['count']}")
    print(f"Mock calls: {mock_material_service.list_materials.call_count}")

# Diagnostic function to inspect controller parameters
def inspect_controller_parameters():
    """Inspect the parameters of the controller function."""
    print("\n--- Inspecting controller parameters ---")
    
    # Get the signature of the controller function
    sig = inspect.signature(list_materials)
    
    # Print information about each parameter
    for name, param in sig.parameters.items():
        print(f"Parameter: {name}")
        print(f"  Default: {param.default}")
        print(f"  Annotation: {param.annotation}")
        
        # Check if it's a Depends parameter
        if param.default is not inspect.Parameter.empty and hasattr(param.default, "dependency"):
            print(f"  Is Depends: True")
            print(f"  Dependency: {param.default.dependency}")
        else:
            print(f"  Is Depends: False")
        
        print()

# Run the diagnostic function
inspect_controller_parameters()

if __name__ == "__main__":
    # Run the tests directly if this file is executed
    asyncio.run(test_original_approach(MagicMock(), MagicMock(), AsyncMock(), MagicMock(), MagicMock()))
    asyncio.run(test_unwrap_approach(AsyncMock(), MagicMock(), MagicMock()))
    asyncio.run(test_create_controller_test_approach(AsyncMock(), MagicMock(), MagicMock())) 