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
Diagnostic tests for edge cases and error handling with dependency unwrapping.

This file tests:
1. Controllers with missing dependencies
2. Controllers with extra dependencies
3. Error propagation
4. Performance with many dependencies
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Depends, HTTPException
from fastapi.responses import JSONResponse

from api.test_helpers import unwrap_dependencies, create_controller_test
from utils.error_utils import NotFoundError, ValidationError

# Test controllers with different dependency patterns

# Controller with no dependencies
async def controller_no_deps(request: Request):
    """Controller with no dependencies."""
    return {"status": "ok"}

# Controller with optional dependencies
async def controller_optional_deps(
    request: Request,
    optional_service = None
):
    """Controller with optional dependencies."""
    if optional_service:
        return {"status": "ok", "service": "present"}
    return {"status": "ok", "service": "absent"}

# Controller that raises different exceptions
async def controller_with_errors(
    request: Request,
    error_type: str = None,
    material_service = Depends(lambda: None),
    monitor_service = Depends(lambda: None)
):
    """Controller that raises different types of errors."""
    if error_type == "http":
        raise HTTPException(status_code=400, detail="Bad request")
    elif error_type == "validation":
        raise ValidationError("Validation error", details={"field": "Invalid"})
    elif error_type == "not_found":
        raise NotFoundError("Resource not found")
    elif error_type == "runtime":
        raise RuntimeError("Unexpected error")
    
    return {"status": "ok"}

# Controller with many dependencies to test performance
async def controller_many_deps(
    request: Request,
    service1 = Depends(lambda: None),
    service2 = Depends(lambda: None),
    service3 = Depends(lambda: None),
    service4 = Depends(lambda: None),
    service5 = Depends(lambda: None),
    service6 = Depends(lambda: None),
    service7 = Depends(lambda: None),
    service8 = Depends(lambda: None),
    service9 = Depends(lambda: None),
    service10 = Depends(lambda: None)
):
    """Controller with many dependencies to test performance."""
    return {"status": "ok", "deps_count": 10}

# Fixtures
@pytest.fixture
def mock_request():
    """Create a mock request object for testing."""
    request = AsyncMock(spec=Request)
    request.url = MagicMock()
    request.url.path = "/test"
    request.query_params = {}
    return request

# Tests for edge cases

@pytest.mark.asyncio
async def test_controller_no_deps(mock_request):
    """Test unwrapping a controller with no dependencies."""
    print("\n--- Testing controller with no dependencies ---")
    
    # Create wrapped controller
    wrapped = unwrap_dependencies(controller_no_deps)
    
    # Call the function
    result = await wrapped(mock_request)
    
    # Verify result
    assert result["status"] == "ok"
    print(f"Result: {result}")

@pytest.mark.asyncio
async def test_controller_optional_deps(mock_request):
    """Test unwrapping a controller with optional dependencies."""
    print("\n--- Testing controller with optional dependencies ---")
    
    # Test without providing the optional service
    wrapped1 = unwrap_dependencies(controller_optional_deps)
    result1 = await wrapped1(mock_request)
    assert result1["status"] == "ok"
    assert result1["service"] == "absent"
    print(f"Result without service: {result1}")
    
    # Test with providing the optional service
    mock_service = MagicMock()
    wrapped2 = unwrap_dependencies(controller_optional_deps, optional_service=mock_service)
    result2 = await wrapped2(mock_request)
    assert result2["status"] == "ok"
    assert result2["service"] == "present"
    print(f"Result with service: {result2}")

@pytest.mark.asyncio
async def test_controller_with_errors(mock_request):
    """Test error handling with unwrapped controllers."""
    print("\n--- Testing error handling with unwrapped controllers ---")
    
    # Create mock services
    mock_material_service = MagicMock()
    mock_monitor_service = MagicMock()
    
    # Create wrapped controller
    wrapped = unwrap_dependencies(
        controller_with_errors,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Test different error types
    error_types = ["http", "validation", "not_found", "runtime"]
    
    for error_type in error_types:
        print(f"\nTesting error type: {error_type}")
        try:
            result = await wrapped(mock_request, error_type=error_type)
            print(f"Unexpected success: {result}")
        except Exception as e:
            print(f"Caught exception: {type(e).__name__}: {str(e)}")
            # Verify the exception is of the expected type
            if error_type == "http":
                assert isinstance(e, HTTPException)
            elif error_type == "validation":
                assert isinstance(e, ValidationError)
            elif error_type == "not_found":
                assert isinstance(e, NotFoundError)
            elif error_type == "runtime":
                assert isinstance(e, RuntimeError)

@pytest.mark.asyncio
async def test_controller_many_deps_performance(mock_request):
    """Test performance with many dependencies."""
    print("\n--- Testing performance with many dependencies ---")
    
    # Create mock services
    mocks = {
        f"service{i}": MagicMock() for i in range(1, 11)
    }
    
    # Measure time to create wrapped controller
    start_time = time.time()
    wrapped = unwrap_dependencies(controller_many_deps, **mocks)
    wrap_time = time.time() - start_time
    
    # Measure time to call the controller
    start_time = time.time()
    result = await wrapped(mock_request)
    call_time = time.time() - start_time
    
    # Verify result
    assert result["status"] == "ok"
    assert result["deps_count"] == 10
    
    # Print performance metrics
    print(f"Time to create wrapped controller: {wrap_time:.6f} seconds")
    print(f"Time to call wrapped controller: {call_time:.6f} seconds")
    print(f"Total time: {wrap_time + call_time:.6f} seconds")

@pytest.mark.asyncio
async def test_missing_dependency(mock_request):
    """Test behavior when a required dependency is missing."""
    print("\n--- Testing behavior with missing dependency ---")
    
    # Create wrapped controller with only one of the required services
    wrapped = unwrap_dependencies(
        controller_with_errors,
        material_service=MagicMock()
        # monitor_service is missing
    )
    
    # Call the controller and see what happens
    try:
        result = await wrapped(mock_request)
        print(f"Controller executed successfully: {result}")
    except Exception as e:
        print(f"Controller raised exception: {type(e).__name__}: {str(e)}")
        # We don't assert here because we're just diagnosing the behavior

@pytest.mark.asyncio
async def test_extra_dependency(mock_request):
    """Test behavior when an extra dependency is provided."""
    print("\n--- Testing behavior with extra dependency ---")
    
    # Create wrapped controller with an extra service that isn't used
    wrapped = unwrap_dependencies(
        controller_no_deps,
        extra_service=MagicMock()
    )
    
    # Call the controller and see what happens
    try:
        result = await wrapped(mock_request)
        print(f"Controller executed successfully: {result}")
        assert result["status"] == "ok"
    except Exception as e:
        print(f"Controller raised exception: {type(e).__name__}: {str(e)}")
        pytest.fail(f"Should not have raised an exception: {e}")

if __name__ == "__main__":
    # Run the tests directly if this file is executed
    asyncio.run(test_controller_no_deps(AsyncMock()))
    asyncio.run(test_controller_optional_deps(AsyncMock()))
    asyncio.run(test_controller_with_errors(AsyncMock()))
    asyncio.run(test_controller_many_deps_performance(AsyncMock()))
    asyncio.run(test_missing_dependency(AsyncMock()))
    asyncio.run(test_extra_dependency(AsyncMock())) 