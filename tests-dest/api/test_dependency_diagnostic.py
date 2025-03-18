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
            response = test_controller(mock_request)
            print(f"Response status code: {response.status_code}")
            
    elif mock_approach == "mock_service_getter":
        # Approach 2: Mock the service getter functions
        with patch('services.get_material_service') as mock_get_material, \
             patch('services.get_monitor_service') as mock_get_monitor:
            
            print("Setting up mock service getters")
            mock_get_material.return_value = mock_material_service
            mock_get_monitor.return_value = mock_monitor_service
            
            # Call the controller
            response = test_controller(mock_request)
            print(f"Response status code: {response.status_code}")
            
    elif mock_approach == "direct_injection":
        # Approach 3: Create a modified controller function with direct injection
        def modified_controller(request, material_service, monitor_service):
            return test_controller(request)
            
        print("Using direct injection")
        # Call the modified controller
        response = modified_controller(mock_request, mock_material_service, mock_monitor_service)
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