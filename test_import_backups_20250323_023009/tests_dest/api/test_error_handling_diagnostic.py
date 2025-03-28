# Import helper to fix path issues
import sys
import os
from pathlib import Path

# Add parent directory to path
current_file = Path(__file__).resolve()
tests_dest_dir = current_file.parent.parent
project_root = tests_dest_dir.parent
if str(tests_dest_dir) not in sys.path:
    sys.path.insert(0, str(tests_dest_dir))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now we can import the helper
from tests_dest.import_helper import fix_imports
fix_imports()

import pytest
import logging
import asyncio
import inspect
import json
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException
from fastapi.responses import JSONResponse

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
Diagnostic tests for the error test controller.

This file tests our dependency unwrapping approach with a controller
that raises different types of errors to verify error handling.
"""

# Import test helpers from the correct location
from tests_dest.api.test_helpers import unwrap_dependencies, create_controller_test
from utils.error_utils import NotFoundError, ValidationError, BadRequestError
from controllers import BaseController  # BaseController is defined directly in __init__.py

# Import with aliases to avoid pytest collecting them as tests
from controllers.error_test_controller import (
    test_not_found as controller_not_found,
    test_validation_error as controller_validation_error,
    test_bad_request as controller_bad_request,
    test_success_response as controller_success_response
)

# Add a simple diagnostic test for direct execution
def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Simple diagnostic test ===")
    print("Successfully executed test_error_handling_diagnostic.py")
    print("All imports resolved correctly")
    return True

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
    
    # Test validation error
    with pytest.raises(ValidationError) as excinfo:
        await wrapped_validation(mock_request)
    assert "This is a test ValidationError" in str(excinfo.value)
    
    # Test bad request error
    with pytest.raises(BadRequestError) as excinfo:
        await wrapped_bad_request(mock_request)
    assert "This is a test BadRequestError" in str(excinfo.value)
    
    # Test success response
    result = await wrapped_success(mock_request)
    assert isinstance(result, JSONResponse)
    content = json.loads(result.body.decode('utf-8'))
    assert content["data"]["test"] == "value"
    
    print("All unwrapped controllers behaved as expected")

@pytest.mark.asyncio
async def test_with_create_controller_test(mock_request):
    """Test using create_controller_test with error controllers."""
    print("\n--- Testing create_controller_test with error controllers ---")
    
    # Create test functions for controllers
    test_not_found = create_controller_test(controller_not_found)
    test_validation = create_controller_test(controller_validation_error)
    test_bad_request = create_controller_test(controller_bad_request)
    test_success = create_controller_test(controller_success_response)
    
    # Run tests
    try:
        result = await test_not_found(mock_request)
        assert False, "Should have raised NotFoundError"
    except NotFoundError as e:
        print(f"NotFoundError correctly raised: {e}")
    
    try:
        result = await test_validation(mock_request)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        print(f"ValidationError correctly raised: {e}")
    
    try:
        result = await test_bad_request(mock_request)
        assert False, "Should have raised BadRequestError"
    except BadRequestError as e:
        print(f"BadRequestError correctly raised: {e}")
    
    # Success case
    result = await test_success(mock_request)
    assert isinstance(result, JSONResponse)
    content = json.loads(result.body.decode('utf-8'))
    assert content["data"]["test"] == "value"
    
    print("All controller test functions behaved as expected")

# Utility function to help debug controller parameters
def inspect_controller_parameters():
    """Inspect the parameters of the error test controllers."""
    print("\n--- Inspecting controller parameters ---")
    
    controllers = [
        controller_not_found,
        controller_validation_error,
        controller_bad_request,
        controller_success_response
    ]
    
    for i, controller in enumerate(controllers):
        signature = inspect.signature(controller)
        print(f"Controller {i+1}: {controller.__name__}")
        print(f"  Parameters: {signature.parameters}")
        
        # Check for async
        if asyncio.iscoroutinefunction(controller):
            print("  Is async: Yes")
        else:
            print("  Is async: No")
        
        print()

if __name__ == "__main__":
    # Run the simple diagnostic test to verify imports
    run_simple_test()
    
    # For debugging, you can uncomment this to inspect controller parameters
    # inspect_controller_parameters()
    
    # Run the tests with pytest
    sys.exit(pytest.main(["-v", __file__])) 