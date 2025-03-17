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
        
        # Replace Depends objects with mocks
        for param_name, param in sig.parameters.items():
            # Skip parameters that were provided in args/kwargs
            if param_name in new_kwargs:
                continue
                
            # Get the default value (which might be a Depends object)
            default = param.default
            
            # Check if this is a dependency parameter and we have a mock for it
            is_depends = default is not inspect.Parameter.empty and hasattr(default, "dependency")
            if is_depends and param_name in mocks:
                new_kwargs[param_name] = mocks[param_name]
        
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
        return await wrapped(mock_request, **kwargs)
    
    return test_func 