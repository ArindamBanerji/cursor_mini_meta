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
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Optional imports - these might fail but won't break tests
try:
    from services.base_service import BaseService
    from services.monitor_service import MonitorService
    from models.base_model import BaseModel
except ImportError as e:
    logger.warning(f"Optional import failed: {e}")


"""
Test helper functions for working with FastAPI dependencies.
"""

import inspect
from typing import Callable, Dict, Any, Awaitable
from fastapi import Depends
from unittest.mock import MagicMock

def unwrap_dependencies(func: Callable, **mocks) -> Callable:
    """
    Create a wrapper function that replaces FastAPI Depends objects with mock objects.
    
    Args:
        func: The controller function to wrap
        **mocks: Mapping of parameter names to mock objects
        
    Returns:
        A wrapped function that uses the provided mocks instead of Depends objects
    """
    # Get the signature of the original function
    sig = inspect.signature(func)
    
    # Create a wrapper function
    async def wrapper(*args, **kwargs):
        # Create a new kwargs dict with the mocks injected
        new_kwargs = {}
        
        # Add any provided positional args to kwargs by name
        params = list(sig.parameters.keys())
        for i, arg in enumerate(args):
            if i < len(params):
                new_kwargs[params[i]] = arg
        
        # Add any provided keyword args
        new_kwargs.update(kwargs)
        
        # Replace Depends objects with mocks and handle optional dependencies
        for param_name, param in sig.parameters.items():
            # Skip parameters that were provided in args/kwargs
            if param_name in new_kwargs:
                continue
                
            # Get the default value
            default = param.default
            
            # Check if this is a dependency parameter and we have a mock for it
            is_depends = default is not inspect.Parameter.empty and hasattr(default, "dependency")
            
            # If we have a mock for this parameter, use it regardless of whether it's a Depends
            if param_name in mocks:
                new_kwargs[param_name] = mocks[param_name]
            # If it's a Depends parameter but we don't have a mock, leave it as is
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
        A test function that takes mock services and a request
    """
    async def test_func(mock_request, mock_material_service=None, mock_monitor_service=None, **kwargs):
        # Create mocks dict
        mocks = {}
        if mock_material_service:
            mocks['material_service'] = mock_material_service
        if mock_monitor_service:
            mocks['monitor_service'] = mock_monitor_service
        
        # Add any additional mocks
        mocks.update(kwargs)
        
        # Create wrapped controller
        wrapped = unwrap_dependencies(controller_func, **mocks)
        
        # Call the wrapped controller
        return await wrapped(mock_request)
    
    return test_func

def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Simple test_helpers diagnostic test ===")
    print("Successfully loaded test_helpers.py")
    print("unwrap_dependencies and create_controller_test functions are available")
    return True

if __name__ == "__main__":
    run_simple_test()
