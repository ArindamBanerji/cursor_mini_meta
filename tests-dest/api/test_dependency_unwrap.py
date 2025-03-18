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
Test the dependency unwrapping solution.

This file tests the unwrap_dependencies and create_controller_test functions
that help with testing FastAPI controllers that use dependency injection.
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
async def test_controller(
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