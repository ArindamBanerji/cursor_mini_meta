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
async def test_controller(
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