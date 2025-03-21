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
Diagnostic tests for the error test controller.

This file tests our dependency unwrapping approach with a controller
that raises different types of errors to verify error handling.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import asyncio
import inspect
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from fastapi.responses import JSONResponse

# Import with aliases to avoid pytest collecting them as tests
from controllers.error_test_controller import (
    test_not_found as controller_not_found,
    test_validation_error as controller_validation_error,
    test_bad_request as controller_bad_request,
    test_success_response as controller_success_response
)
from api.test_helpers import unwrap_dependencies, create_controller_test
from utils.error_utils import NotFoundError, ValidationError, BadRequestError
from controllers import BaseController

# Fixtures
@pytest.fixture
def mock_request():
    """Create a mock request object for testing."""
    request = AsyncMock(spec=Request)
    request.url = MagicMock()
    request.url.path = "/test-error"
    return request

# Diagnostic tests
@pytest.mark.asyncio
async def test_not_found_error(mock_request):
    """Test the not found error controller."""
    print("\n--- Testing not found error controller ---")
    
    # Call the function and expect an error
    with pytest.raises(NotFoundError) as excinfo:
        await controller_not_found(mock_request)
    
    # Verify error details
    assert "This is a test NotFoundError" in str(excinfo.value)
    print(f"Error message: {excinfo.value}")

@pytest.mark.asyncio
async def test_validation_error_controller(mock_request):
    """Test the validation error controller."""
    print("\n--- Testing validation error controller ---")
    
    # Call the function and expect an error
    with pytest.raises(ValidationError) as excinfo:
        await controller_validation_error(mock_request)
    
    # Verify error details
    assert "This is a test ValidationError" in str(excinfo.value)
    assert hasattr(excinfo.value, "details")
    assert "field1" in excinfo.value.details
    assert "field2" in excinfo.value.details
    print(f"Error message: {excinfo.value}")
    print(f"Error details: {excinfo.value.details}")

@pytest.mark.asyncio
async def test_bad_request_error(mock_request):
    """Test the bad request error controller."""
    print("\n--- Testing bad request error controller ---")
    
    # Call the function and expect an error
    with pytest.raises(BadRequestError) as excinfo:
        await controller_bad_request(mock_request)
    
    # Verify error details
    assert "This is a test BadRequestError" in str(excinfo.value)
    print(f"Error message: {excinfo.value}")

@pytest.mark.asyncio
async def test_success_response_controller(mock_request):
    """Test the success response controller."""
    print("\n--- Testing success response controller ---")
    
    # Mock the BaseController.create_success_response method
    with patch.object(BaseController, 'create_success_response', wraps=BaseController.create_success_response) as mock_success:
        # Call the function
        result = await controller_success_response(mock_request)
        
        # Verify result is a JSONResponse
        assert isinstance(result, JSONResponse)
        
        # Extract the content from the JSONResponse
        content = json.loads(result.body.decode('utf-8'))
        
        # Verify content
        assert "data" in content
        assert "message" in content
        assert content["data"]["test"] == "value"
        assert content["data"]["items"] == [1, 2, 3]
        assert content["message"] == "This is a test success response"
        
        # Verify BaseController.create_success_response was called
        mock_success.assert_called_once()
        
        print(f"Result status code: {result.status_code}")
        print(f"Result content: {content}")

@pytest.mark.asyncio
async def test_with_unwrap_dependencies(mock_request):
    """Test using unwrap_dependencies with error controllers."""
    print("\n--- Testing unwrap_dependencies with error controllers ---")
    
    # Create wrapped controllers
    wrapped_not_found = unwrap_dependencies(controller_not_found)
    wrapped_validation = unwrap_dependencies(controller_validation_error)
    wrapped_bad_request = unwrap_dependencies(controller_bad_request)
    wrapped_success = unwrap_dependencies(controller_success_response)
    
    # Test not found error
    with pytest.raises(NotFoundError) as excinfo:
        await wrapped_not_found(mock_request)
    assert "This is a test NotFoundError" in str(excinfo.value)
    print(f"Not found error message: {excinfo.value}")
    
    # Test validation error
    with pytest.raises(ValidationError) as excinfo:
        await wrapped_validation(mock_request)
    assert "This is a test ValidationError" in str(excinfo.value)
    print(f"Validation error message: {excinfo.value}")
    
    # Test bad request error
    with pytest.raises(BadRequestError) as excinfo:
        await wrapped_bad_request(mock_request)
    assert "This is a test BadRequestError" in str(excinfo.value)
    print(f"Bad request error message: {excinfo.value}")
    
    # Test success response
    with patch.object(BaseController, 'create_success_response', wraps=BaseController.create_success_response):
        result = await wrapped_success(mock_request)
        
        # Verify result is a JSONResponse
        assert isinstance(result, JSONResponse)
        
        # Extract the content from the JSONResponse
        content = json.loads(result.body.decode('utf-8'))
        
        # Verify content
        assert "data" in content
        assert "message" in content
        
        print(f"Success response status code: {result.status_code}")
        print(f"Success response content: {content}")

@pytest.mark.asyncio
async def test_with_create_controller_test(mock_request):
    """Test using create_controller_test with error controllers."""
    print("\n--- Testing create_controller_test with error controllers ---")
    
    # Create test functions
    test_not_found_func = create_controller_test(controller_not_found)
    test_validation_func = create_controller_test(controller_validation_error)
    test_bad_request_func = create_controller_test(controller_bad_request)
    test_success_func = create_controller_test(controller_success_response)
    
    # Test not found error
    with pytest.raises(NotFoundError) as excinfo:
        await test_not_found_func(mock_request=mock_request)
    assert "This is a test NotFoundError" in str(excinfo.value)
    print(f"Not found error message: {excinfo.value}")
    
    # Test validation error
    with pytest.raises(ValidationError) as excinfo:
        await test_validation_func(mock_request=mock_request)
    assert "This is a test ValidationError" in str(excinfo.value)
    print(f"Validation error message: {excinfo.value}")
    
    # Test bad request error
    with pytest.raises(BadRequestError) as excinfo:
        await test_bad_request_func(mock_request=mock_request)
    assert "This is a test BadRequestError" in str(excinfo.value)
    print(f"Bad request error message: {excinfo.value}")
    
    # Test success response
    with patch.object(BaseController, 'create_success_response', wraps=BaseController.create_success_response):
        result = await test_success_func(mock_request=mock_request)
        
        # Verify result is a JSONResponse
        assert isinstance(result, JSONResponse)
        
        # Extract the content from the JSONResponse
        content = json.loads(result.body.decode('utf-8'))
        
        # Verify content
        assert "data" in content
        assert "message" in content
        
        print(f"Success response status code: {result.status_code}")
        print(f"Success response content: {content}")

# Diagnostic function to inspect controller parameters
def inspect_controller_parameters():
    """Inspect the parameters of the controller functions."""
    print("\n--- Inspecting error test controller parameters ---")
    
    # Get the signature of the controller functions
    sig_not_found = inspect.signature(controller_not_found)
    sig_validation = inspect.signature(controller_validation_error)
    sig_bad_request = inspect.signature(controller_bad_request)
    sig_success = inspect.signature(controller_success_response)
    
    # Print information about each parameter for test_not_found
    print("test_not_found parameters:")
    for name, param in sig_not_found.parameters.items():
        print(f"Parameter: {name}")
        print(f"  Default: {param.default}")
        print(f"  Annotation: {param.annotation}")
        
        # Check if it's a Depends parameter
        if param.default is not inspect.Parameter.empty and hasattr(param.default, "dependency"):
            print(f"  Is Depends: True")
            print(f"  Dependency: {param.default.dependency}")
        else:
            print(f"  Is Depends: False")
        
        print()

# Run the diagnostic function
inspect_controller_parameters()

if __name__ == "__main__":
    # Run the tests directly if this file is executed
    asyncio.run(test_not_found_error(AsyncMock()))
    asyncio.run(test_validation_error_controller(AsyncMock()))
    asyncio.run(test_bad_request_error(AsyncMock()))
    asyncio.run(test_success_response_controller(AsyncMock()))
    asyncio.run(test_with_unwrap_dependencies(AsyncMock()))
    asyncio.run(test_with_create_controller_test(AsyncMock())) 