"""
Test the dependency unwrapping solution.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Depends
from fastapi.responses import JSONResponse

from controllers.material_common import (
    get_material_service_dependency,
    get_monitor_service_dependency
)
from controllers.material_ui_controller import list_materials
from api.test_helpers import unwrap_dependencies, create_controller_test

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
            materials = material_service.list_materials()
            print(f"list_materials returned: {materials}")
        else:
            print("material_service does NOT have list_materials method")
            
        if hasattr(monitor_service, 'log_error'):
            print("monitor_service has log_error method")
            monitor_service.log_error(error_type="test", message="Test error")
            print("log_error called successfully")
        else:
            print("monitor_service does NOT have log_error method")
    except Exception as e:
        print(f"Error accessing service methods: {str(e)}")
    
    # Return a simple response
    return JSONResponse({"status": "ok"})

@pytest.mark.asyncio
async def test_unwrap_dependencies():
    """Test the unwrap_dependencies function."""
    print("\n--- Testing unwrap_dependencies ---")
    
    # Create mock services
    mock_material_service = MagicMock()
    mock_material_service.list_materials = MagicMock(return_value=["test_material"])
    
    mock_monitor_service = MagicMock()
    mock_monitor_service.log_error = MagicMock()
    
    # Create mock request
    mock_request = AsyncMock(spec=Request)
    
    # Create wrapped controller
    wrapped_controller = unwrap_dependencies(
        test_controller,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the wrapped controller
    response = await wrapped_controller(mock_request)
    
    # Verify the response
    assert response.status_code == 200
    assert response.body.decode('utf-8') == '{"status":"ok"}'
    
    # Verify the mocks were called
    mock_material_service.list_materials.assert_called_once()
    mock_monitor_service.log_error.assert_called_once_with(
        error_type="test", message="Test error"
    )

@pytest.mark.asyncio
async def test_create_controller_test():
    """Test the create_controller_test function."""
    print("\n--- Testing create_controller_test ---")
    
    # Create mock services
    mock_material_service = MagicMock()
    mock_material_service.list_materials = MagicMock(return_value=["test_material"])
    
    mock_monitor_service = MagicMock()
    mock_monitor_service.log_error = MagicMock()
    
    # Create mock request
    mock_request = AsyncMock(spec=Request)
    
    # Create test function
    test_func = create_controller_test(test_controller)
    
    # Call the test function
    response = await test_func(
        mock_request=mock_request,
        mock_material_service=mock_material_service,
        mock_monitor_service=mock_monitor_service
    )
    
    # Verify the response
    assert response.status_code == 200
    assert response.body.decode('utf-8') == '{"status":"ok"}'
    
    # Verify the mocks were called
    mock_material_service.list_materials.assert_called_once()
    mock_monitor_service.log_error.assert_called_once_with(
        error_type="test", message="Test error"
    )

@pytest.mark.asyncio
async def test_real_controller():
    """Test a real controller function from the codebase."""
    print("\n--- Testing real controller ---")
    
    # Create mock services
    mock_material_service = MagicMock()
    mock_material_service.list_materials = MagicMock(return_value=["test_material"])
    
    mock_monitor_service = MagicMock()
    mock_monitor_service.log_error = MagicMock()
    
    # Create mock request
    mock_request = AsyncMock(spec=Request)
    mock_request.query_params = {}
    
    # Create wrapped controller
    wrapped_controller = unwrap_dependencies(
        list_materials,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the wrapped controller
    result = await wrapped_controller(mock_request)
    
    # Verify the result
    assert "materials" in result
    assert result["materials"] == ["test_material"]
    assert "count" in result
    assert result["count"] == 1
    
    # Verify the mock was called
    mock_material_service.list_materials.assert_called_once()

if __name__ == "__main__":
    # Run the tests directly if this file is executed
    asyncio.run(test_unwrap_dependencies())
    asyncio.run(test_create_controller_test())
    asyncio.run(test_real_controller()) 