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

import pytest
import logging
import inspect
from typing import Callable, Dict, Any, Awaitable
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException, Depends
from pydantic import BaseModel as PydanticBaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services from service_imports
from tests_dest.test_helpers.service_imports import (
    BaseService,
    MonitorService, 
    get_monitor_service,
    get_material_service,
    BaseDataModel
)

"""
Helper functions for working with FastAPI dependencies.
"""

def unwrap_dependencies(func: Callable, **services) -> Callable:
    """
    Create a wrapper function that replaces FastAPI Depends objects with real service objects.
    
    Args:
        func: The controller function to wrap
        **services: Mapping of parameter names to service objects
        
    Returns:
        A wrapped function that uses the provided services instead of Depends objects
    """
    # Get the signature of the original function
    sig = inspect.signature(func)
    
    # Create a wrapper function
    async def wrapper(*args, **kwargs):
        # Create a new kwargs dict with the services injected
        new_kwargs = {}
        
        # Add any provided positional args to kwargs by name
        params = list(sig.parameters.keys())
        for i, arg in enumerate(args):
            if i < len(params):
                new_kwargs[params[i]] = arg
        
        # Add any provided keyword args
        new_kwargs.update(kwargs)
        
        # Replace Depends objects with services and handle optional dependencies
        for param_name, param in sig.parameters.items():
            # Skip parameters that were provided in args/kwargs
            if param_name in new_kwargs:
                continue
                
            # Get the default value
            default = param.default
            
            # Check if this is a dependency parameter and we have a service for it
            is_depends = default is not inspect.Parameter.empty and hasattr(default, "dependency")
            
            # If we have a service for this parameter, use it regardless of whether it's a Depends
            if param_name in services:
                new_kwargs[param_name] = services[param_name]
            # If it's a Depends parameter but we don't have a service, leave it as is
            elif is_depends:
                new_kwargs[param_name] = default
            # If it's a parameter with a default value, use the default
            elif default is not inspect.Parameter.empty:
                new_kwargs[param_name] = default
        
        # Call the original function with the new kwargs
        return await func(**new_kwargs)
    
    return wrapper

def create_controller_test(controller_func: Callable) -> Callable:
    """
    Create a test function for a controller that automatically unwraps dependencies.
    
    Args:
        controller_func: The controller function to test
        
    Returns:
        A test function that takes service instances and a request
    """
    async def test_func(request, material_service=None, monitor_service=None, **kwargs):
        # Create services dict
        services = {}
        if material_service:
            services['material_service'] = material_service
        if monitor_service:
            services['monitor_service'] = monitor_service
        
        # Add any additional services
        services.update(kwargs)
        
        # Create wrapped controller
        wrapped = unwrap_dependencies(controller_func, **services)
        
        # Call the wrapped controller
        return await wrapped(request)
    
    return test_func

def test_unwrap_dependencies():
    """Test the unwrap_dependencies function with real services."""
    # Define a simple controller function
    async def test_controller(
        request: Request,
        material_service = Depends(get_material_service),
        monitor_service = Depends(get_monitor_service)
    ):
        # Return basic info about the services
        return {
            "material_service_available": material_service is not None,
            "monitor_service_available": monitor_service is not None,
            "materials": material_service.list_materials() if material_service else []
        }
    
    # Create a test request
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
    
    # Get real services
    material_service = get_material_service()
    monitor_service = get_monitor_service()
    
    # Create wrapped controller with real services
    wrapped = unwrap_dependencies(
        test_controller,
        material_service=material_service,
        monitor_service=monitor_service
    )
    
    # Call the wrapped controller
    import asyncio
    result = asyncio.run(wrapped(request))
    
    # Verify the result
    assert result["material_service_available"] is True
    assert result["monitor_service_available"] is True
    assert isinstance(result["materials"], list)
    
    # Test the create_controller_test function
    test_func = create_controller_test(test_controller)
    result2 = asyncio.run(test_func(
        request=request,
        material_service=material_service,
        monitor_service=monitor_service
    ))
    
    # Verify the result
    assert result2["material_service_available"] is True
    assert result2["monitor_service_available"] is True
    assert isinstance(result2["materials"], list)
    
    return True

def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Simple test_helpers diagnostic test ===")
    print("Successfully loaded test_helpers.py")
    print("unwrap_dependencies and create_controller_test functions are available")
    return True

if __name__ == "__main__":
    run_simple_test()
    test_unwrap_dependencies()
