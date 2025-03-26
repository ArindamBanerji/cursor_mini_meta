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
Diagnostic tests for edge cases and error handling with dependency unwrapping.

This file tests:
1. Controllers with missing dependencies
2. Controllers with extra dependencies
3. Error propagation
4. Performance with many dependencies
"""

import pytest
import logging
import time
import json
import inspect
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services through the service_imports facade
from tests_dest.test_helpers.service_imports import (
    get_material_service,
    get_monitor_service,
    get_state_manager
)

# Custom exception classes
class ValidationError(Exception):
    """Custom validation error."""
    # Avoid using custom constructor that calls dunder methods
    pass
        
class NotFoundError(Exception):
    """Custom not found error."""
    pass

# Helper to create a validation error with details
def create_validation_error(message, details=None):
    error = ValidationError(message)
    error.details = details or {}
    return error


# Create real dependencies for testing
def get_material_service_dependency():
    return Depends(get_material_service)

def get_monitor_service_dependency():
    return Depends(get_monitor_service)

# Controller implementations
async def list_materials(request: Request = None):
    return JSONResponse({"materials": ["test"]})


# Helper function to extract JSON data from a response
def get_json_data(response):
    """Extract JSON data from a FastAPI response object."""
    if isinstance(response, JSONResponse):
        return json.loads(response.body.decode('utf-8'))
    return response


# Implementation for unwrap_dependencies and other helper functions
def unwrap_dependencies(controller_func, **dependencies):
    """Unwrap FastAPI dependencies for easier testing.
    
    This function takes a controller function that has Depends() injected parameters
    and returns a new function where those parameters are replaced with the provided
    dependency implementations.
    """
    # Get the signature of the controller function
    sig = inspect.signature(controller_func)
    param_names = list(sig.parameters.keys())
    
    async def wrapper(*args, **kwargs):
        # Create a new kwargs dict with the dependencies
        new_kwargs = kwargs.copy()
        
        # Add our provided dependencies, but only if they are valid parameters
        for name, impl in dependencies.items():
            if name in param_names:
                new_kwargs[name] = impl
            
        # Call the original function with our arguments and dependencies
        return await controller_func(*args, **new_kwargs)
        
    return wrapper


def create_controller_test(controller_func):
    """Create a test helper for the given controller function."""
    
    async def test_func(request=None, **services):
        # Create a wrapped version of the controller with our services
        wrapped = unwrap_dependencies(controller_func, **services)
        
        # Call the controller with the request
        result = await wrapped(request) if request else await wrapped()
        
        # Return the result, extracting JSON if needed
        return get_json_data(result)
    
    return test_func


# Test controller implementations
async def controller_no_deps(request: Request):
    """Controller function with no dependencies."""
    return JSONResponse({"status": "ok"})


async def controller_optional_deps(
    request: Request,
    optional_service = None
):
    """Controller function with an optional dependency."""
    if optional_service:
        return JSONResponse({
            "status": "ok", 
            "service": True,
            "service_type": str(type(optional_service))
        })
    return JSONResponse({"status": "ok", "service": False})


async def controller_with_errors(
    request: Request,
    error_type: str = None,
    material_service = Depends(get_material_service),
    monitor_service = Depends(get_monitor_service)
):
    """Controller function that can raise different types of errors."""
    if error_type == "validation":
        raise create_validation_error("Validation failed", {"field": "missing"})
    elif error_type == "not_found":
        raise NotFoundError("Resource not found")
    elif error_type == "http":
        raise HTTPException(status_code=404, detail="Not found")
    elif error_type == "generic":
        raise Exception("Generic error")
    
    return JSONResponse({
        "status": "ok",
        "material_service": str(type(material_service)),
        "monitor_service": str(type(monitor_service))
    })


async def controller_many_deps(
    request: Request,
    service1 = Depends(get_material_service),
    service2 = Depends(get_monitor_service),
    service3 = Depends(get_state_manager),
    service4 = Depends(get_material_service),
    service5 = Depends(get_monitor_service),
    service6 = Depends(get_state_manager),
    service7 = Depends(get_material_service),
    service8 = Depends(get_monitor_service),
    service9 = Depends(get_state_manager),
    service10 = Depends(get_material_service)
):
    """Controller function with many dependencies to test performance."""
    return JSONResponse({"status": "ok", "deps": 10})


# Controller that requires material_service but doesn't have a default fallback
async def strict_materials_controller(
    request: Request,
    material_service: object  # This parameter has no default value
):
    """List materials using the material service - strict version with no default."""
    # Don't hide errors, let them propagate
    if material_service is None:
        raise ValueError("material_service is required but was None")
        
    materials = material_service.list_materials()
    return JSONResponse({"materials": materials})


@pytest.fixture
def real_request():
    """Create a real request object for testing."""
    app = FastAPI()
    client = TestClient(app)
    
    scope = {
        "type": "http",
        "path": "/test",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 50000)
    }
    
    return Request(scope)


@pytest.mark.asyncio
async def test_controller_no_deps(real_request):
    """Test a controller with no dependencies."""
    # Direct call
    response = await controller_no_deps(real_request)
    data = get_json_data(response)
    assert data["status"] == "ok"
    
    # Using the helper
    test = create_controller_test(controller_no_deps)
    result = await test(real_request)
    assert result["status"] == "ok"
    
    # Try unwrapping with an extra parameter that won't be used
    wrapped = unwrap_dependencies(controller_no_deps, extra="not_used")
    response = await wrapped(real_request)
    data = get_json_data(response)
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_controller_optional_deps(real_request):
    """Test a controller with optional dependencies."""
    # Call without the optional dependency
    response = await controller_optional_deps(real_request)
    data = get_json_data(response)
    assert data["status"] == "ok"
    assert data["service"] is False
    
    # Call with a real service instance
    material_service = get_material_service()
    response = await controller_optional_deps(real_request, optional_service=material_service)
    data = get_json_data(response)
    assert data["status"] == "ok"
    assert data["service"] is True
    assert "MaterialService" in data["service_type"]
    
    # Using the helper
    test = create_controller_test(controller_optional_deps)
    result = await test(real_request, optional_service=material_service)
    assert result["status"] == "ok"
    assert result["service"] is True


@pytest.mark.asyncio
async def test_controller_with_errors(real_request):
    """Test a controller that raises different types of errors."""
    # Get the real services
    material_service = get_material_service()
    monitor_service = get_monitor_service()
    
    # Create a wrapped controller
    wrapped = unwrap_dependencies(
        controller_with_errors,
        material_service=material_service,
        monitor_service=monitor_service
    )
    
    # Test normal operation
    response = await wrapped(real_request)
    data = get_json_data(response)
    assert data["status"] == "ok"
    assert "MaterialService" in data["material_service"]
    assert "MonitorService" in data["monitor_service"]
    
    # Test ValidationError
    with pytest.raises(ValidationError) as excinfo:
        await wrapped(real_request, error_type="validation")
    assert "Validation failed" in str(excinfo.value)
    assert excinfo.value.details == {"field": "missing"}
    
    # Test NotFoundError
    with pytest.raises(NotFoundError) as excinfo:
        await wrapped(real_request, error_type="not_found")
    assert "Resource not found" in str(excinfo.value)
    
    # Test HTTPException
    with pytest.raises(HTTPException) as excinfo:
        await wrapped(real_request, error_type="http")
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Not found"
    
    # Test generic Exception
    with pytest.raises(Exception) as excinfo:
        await wrapped(real_request, error_type="generic")
    assert "Generic error" in str(excinfo.value)


@pytest.mark.asyncio
async def test_controller_many_deps_performance(real_request):
    """Test performance with many dependencies."""
    # Get real service instances
    services = {
        "service1": get_material_service(),
        "service2": get_monitor_service(),
        "service3": get_state_manager(),
        "service4": get_material_service(),
        "service5": get_monitor_service(),
        "service6": get_state_manager(),
        "service7": get_material_service(),
        "service8": get_monitor_service(),
        "service9": get_state_manager(),
        "service10": get_material_service()
    }
    
    # Create wrapped controller
    wrapped = unwrap_dependencies(controller_many_deps, **services)
    
    # Measure the time to call it
    start_time = time.time()
    response = await wrapped(real_request)
    end_time = time.time()
    elapsed = end_time - start_time
    
    # Check the result
    data = get_json_data(response)
    assert data["status"] == "ok"
    assert data["deps"] == 10
    
    # The time should be reasonable - typically under 10ms, but we'll allow for CI/CD system differences
    logger.info(f"Time to call controller with 10 dependencies: {elapsed:.6f} seconds")
    assert elapsed < 1.0, f"Controller call took too long: {elapsed:.6f} seconds"


@pytest.mark.asyncio
async def test_missing_dependency(real_request):
    """Test calling a controller that expects a dependency that we don't provide."""
    # Call the strict_materials_controller without providing the required material_service
    # This should fail because material_service has no default value
    with pytest.raises(TypeError) as excinfo:
        # We're not providing the required material_service parameter
        await strict_materials_controller(real_request)
    
    # Verify the error message is about the missing parameter
    assert "missing 1 required positional argument" in str(excinfo.value)
    assert "material_service" in str(excinfo.value)
    
    # Now provide the service, which should work
    material_service = get_material_service()
    response = await strict_materials_controller(real_request, material_service=material_service)
    data = get_json_data(response)
    assert "materials" in data
    assert isinstance(data["materials"], list)


@pytest.mark.asyncio
async def test_extra_dependency(real_request):
    """Test providing a dependency that the controller doesn't expect."""
    # Call the list_materials controller directly
    response = await list_materials(real_request)
    expected_data = get_json_data(response)
    
    # Define a wrapper that ignores extra parameters
    async def direct_wrapper(request):
        # We're ignoring the extra_service parameter here
        return await list_materials(request)
    
    # Create a wrapper with an extra service parameter
    wrapped = unwrap_dependencies(direct_wrapper, extra_service=get_material_service())
    
    # Call it - this should work and just ignore the extra parameter
    response = await wrapped(real_request)
    data = get_json_data(response)
    
    # Should match the direct call
    assert data == expected_data
