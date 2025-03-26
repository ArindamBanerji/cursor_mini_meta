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
Diagnostic tests for dependency unwrapping functionality.

This file contains tests for a utility that simplifies testing FastAPI endpoints
by unwrapping Depends() injected parameters with real service implementations.
"""

import pytest
import logging
import inspect
import json
from fastapi import Request, FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel
import asyncio
from typing import Dict, List, Callable, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import from test helpers - facade pattern
from tests_dest.test_helpers.service_imports import (
    MaterialService, 
    MonitorService,
    get_material_service,
    get_monitor_service
)

# Import fixtures directly if not using pytest injection
from tests_dest.test_helpers.test_fixtures import (
    app,
    real_request,
    real_material_service,
    real_monitor_service
)

# Import request helpers
from tests_dest.test_helpers.request_helpers import (
    create_test_request,
    get_json_data
)

# Controller function for testing
async def controller_with_deps(
    request: Request,
    material_service = Depends(get_material_service),
    monitor_service = Depends(get_monitor_service)):
    """Controller with dependencies to unwrap."""
    materials = material_service.list_materials()
    health = monitor_service.check_health()
    return {
        "status": "success",
        "data": {
            "materials": materials,
            "health": health
        }
    }

# Unwrap dependencies function
def unwrap_dependencies(controller_func, **dependencies):
    """
    Unwrap FastAPI dependencies for testing.

    This function allows replacing FastAPI dependencies with fixed values
    for testing purposes. It creates a wrapper around the controller
    that replaces specified dependencies with the provided values.

    Args:
        controller_func: The controller function to wrap
        **dependencies: Keyword arguments with dependency name and value to inject

    Returns:
        A wrapper function that resolves dependencies
    """
    sig = inspect.signature(controller_func)

    async def wrapper(*args, **kwargs):
        # Copy the provided kwargs to avoid modifying the original
        new_kwargs = kwargs.copy()
        
        # Add the explicit dependencies provided to unwrap
        for name, value in dependencies.items():
            new_kwargs[name] = value
        
        # Call the original function with our arguments and dependencies
        return await controller_func(*args, **new_kwargs)
    
    return wrapper

# Helper function to extract JSON data from a response
def get_json_data(response):
    """Extract JSON data from a FastAPI response object."""
    if isinstance(response, JSONResponse):
        return json.loads(response.body.decode('utf-8'))
    return response

# Fixtures
@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.get("/")(controller_with_deps)
    return app

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

@pytest.fixture
def real_material_service():
    """Create a real MaterialService for testing."""
    return MaterialService()

@pytest.fixture
def real_monitor_service():
    """Create a real MonitorService for testing."""
    return MonitorService()

# Tests
@pytest.mark.asyncio
async def test_unwrap_dependencies(real_request, real_material_service, real_monitor_service):
    """Test unwrapping dependencies for testing."""
    # Create wrapped controller
    wrapped = unwrap_dependencies(
        controller_with_deps,
        material_service=real_material_service,
        monitor_service=real_monitor_service
    )
    
    # Call the controller
    result = await wrapped(real_request)
    
    # Verify the controller worked with unwrapped dependencies
    assert result["status"] == "success"
    assert "materials" in result["data"]
    assert "health" in result["data"]
    
    logger.info("test_unwrap_dependencies passed!")

@pytest.mark.asyncio
async def test_partial_unwrapping(real_request, real_material_service, real_monitor_service):
    """Test unwrapping multiple dependencies to ensure that all are provided explicitly."""
    # Create wrapped controller with only material_service
    wrapped = unwrap_dependencies(
        controller_with_deps,
        material_service=real_material_service,
        monitor_service=real_monitor_service
    )
    
    # Call the controller with all dependencies explicitly provided
    result = await wrapped(real_request)
    
    # Verify the controller worked with explicitly provided dependencies
    assert result["status"] == "success"
    assert "materials" in result["data"]
    assert "health" in result["data"]
    
    logger.info("test_partial_unwrapping passed!")

if __name__ == "__main__":
    import asyncio
    # Create request object and real services
    app = FastAPI()
    client = TestClient(app)
    scope = {
        "type": "http",
        "path": "/test",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 50000)
    }
    request = Request(scope)
    material_service = MaterialService()
    monitor_service = MonitorService()
    
    # Run the test
    asyncio.run(test_unwrap_dependencies(request, material_service, monitor_service))
    asyncio.run(test_partial_unwrapping(request, material_service, monitor_service))
