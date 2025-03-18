# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Critical imports that must be preserved
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from types import ModuleType

"""Standard test file imports and setup.

This snippet is automatically added to test files by SnippetForTests.py.
It provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration
3. Common test imports and fixtures
4. Service initialization support
5. Logging configuration
"""

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_project_root(test_dir: Path) -> Optional[Path]:
    """Find the project root directory.
    
    Args:
        test_dir: The directory containing the test file
        
    Returns:
        The project root directory or None if not found
    """
    try:
        # Try to find project root by looking for main.py or known directories
        for parent in [test_dir] + list(test_dir.parents):
            # Check for main.py as an indicator of project root
            if (parent / "main.py").exists():
                return parent
            # Check for typical project structure indicators
            if all((parent / d).exists() for d in ["services", "models", "controllers"]):
                return parent
        
        # If we still don't have a project root, use parent of the tests-dest directory
        for parent in test_dir.parents:
            if parent.name == "tests-dest":
                return parent.parent
                
        return None
    except Exception as e:
        logger.error(f"Error finding project root: {e}")
        return None

# Find project root dynamically
test_file = Path(__file__).resolve()
test_dir = test_file.parent
project_root = find_project_root(test_dir)

if project_root:
    logger.info(f"Project root detected at: {project_root}")
    
    # Add project root to path if found
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.info(f"Added {project_root} to Python path")
else:
    logger.warning("Could not detect project root")

# Import the test_import_helper
try:
    from test_import_helper import setup_test_paths, setup_test_env_vars
    setup_test_paths()
    logger.info("Successfully initialized test paths from test_import_helper")
except ImportError as e:
    # Fall back if test_import_helper is not available
    if str(test_dir.parent) not in sys.path:
        sys.path.insert(0, str(test_dir.parent))
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root) if project_root else "")
    logger.warning(f"Failed to import test_import_helper: {e}. Using fallback configuration.")

# Common test imports
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

# Import common fixtures and services
try:
    from conftest import test_services
    from services.base_service import BaseService
    from services.monitor_service import MonitorService
    from services.template_service import TemplateService
    from services.p2p_service import P2PService
    from models.base_model import BaseModel
    from models.material import Material
    from models.requisition import Requisition
    from fastapi import FastAPI, HTTPException
    logger.info("Successfully imported test fixtures and services")
except ImportError as e:
    # Log import error but continue - not all tests need all imports
    logger.warning(f"Optional import failed: {e}")
    logger.debug("Stack trace:", exc_info=True)

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment for each test."""
    setup_test_env_vars(monkeypatch)
    logger.info("Test environment initialized")
    yield
    logger.info("Test environment cleaned up")
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

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
