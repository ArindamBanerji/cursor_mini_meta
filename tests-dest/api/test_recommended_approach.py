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
Diagnostic tests demonstrating the recommended approach for testing FastAPI controllers with dependencies.

This file shows:
1. Why the original patching approach doesn't work
2. How our unwrap_dependencies approach solves the problem
3. Best practices for testing FastAPI controllers
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Depends
from fastapi.responses import JSONResponse

from controllers.material_common import (
    get_material_service_dependency,
    get_monitor_service_dependency
)
from controllers.material_ui_controller import list_materials

# Import test helpers with a try-except block to handle both direct execution and pytest
try:
    # Try relative import first (for pytest)
    from .test_helpers import unwrap_dependencies, create_controller_test
except ImportError:
    # Fall back to direct import (for direct execution)
    from test_helpers import unwrap_dependencies, create_controller_test

from models.material import Material, MaterialType, UnitOfMeasure, MaterialStatus

# Create test data
TEST_MATERIAL = Material(
    material_number="MAT12345",
    name="Test Material",
    description="Test Description",
    type=MaterialType.FINISHED,
    base_unit=UnitOfMeasure.EACH,
    status=MaterialStatus.ACTIVE
)

# Fixtures
@pytest.fixture
def mock_request():
    """Create a mock request object for testing."""
    request = AsyncMock(spec=Request)
    request.url = MagicMock()
    request.url.path = "/materials"
    request.query_params = {}
    return request

@pytest.fixture
def mock_material_service():
    """Create a mock material service for testing."""
    from services.material_service import MaterialService
    service = MagicMock(spec=MaterialService)
    service.list_materials.return_value = [TEST_MATERIAL]
    service.get_material.return_value = TEST_MATERIAL
    service.create_material.return_value = TEST_MATERIAL
    service.update_material.return_value = TEST_MATERIAL
    return service

@pytest.fixture
def mock_monitor_service():
    """Create a mock monitor service for testing."""
    from services.monitor_service import MonitorService
    service = MagicMock(spec=MonitorService)
    return service

# Demonstration of why the original approach doesn't work
def demonstrate_original_approach_issue():
    """Demonstrate why the original approach with patch decorators doesn't work."""
    print("\n--- Demonstrating why the original approach doesn't work ---")
    
    # The issue is that the Depends objects are created at import time
    # and stored as default parameter values in the controller function
    
    # Let's inspect the default parameter values of the list_materials function
    import inspect
    sig = inspect.signature(list_materials)
    
    for name, param in sig.parameters.items():
        if name in ["material_service", "monitor_service"]:
            print(f"Parameter: {name}")
            print(f"  Default: {param.default}")
            print(f"  Type: {type(param.default)}")
            
            # Check if it's a Depends parameter
            if hasattr(param.default, "dependency"):
                print(f"  Dependency: {param.default.dependency}")
    
    print("\nWhen we patch the service getter functions, it doesn't affect")
    print("the already-created Depends objects. The controller function")
    print("still receives the original Depends objects as default parameter values.")
    
    print("\nThis is why we need to create a wrapper function that replaces")
    print("the Depends objects with our mock services at call time.")

# Demonstration of the recommended approach
@pytest.mark.asyncio
async def test_recommended_approach(mock_request, mock_material_service, mock_monitor_service):
    """Demonstrate the recommended approach for testing FastAPI controllers."""
    print("\n--- Demonstrating the recommended approach ---")
    
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        list_materials,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    start_time = time.time()
    result = await wrapped(mock_request)
    elapsed_time = time.time() - start_time
    
    # Verify result
    assert "materials" in result
    assert result["materials"] == [TEST_MATERIAL]
    assert "count" in result
    assert result["count"] == 1
    mock_material_service.list_materials.assert_called_once()
    
    # Print diagnostic information
    print(f"Execution time: {elapsed_time:.6f} seconds")
    print(f"Result type: {type(result)}")
    print(f"Materials count: {result['count']}")
    print(f"Mock calls: {mock_material_service.list_materials.call_count}")
    
    print("\nThis approach works because we create a wrapper function that")
    print("replaces the Depends objects with our mock services at call time.")
    print("The controller function never sees the Depends objects, only our mocks.")

# Demonstration of the create_controller_test helper
@pytest.mark.asyncio
async def test_create_controller_test_helper(mock_request, mock_material_service, mock_monitor_service):
    """Demonstrate the create_controller_test helper function."""
    print("\n--- Demonstrating the create_controller_test helper ---")
    
    # Create test function
    test_func = create_controller_test(list_materials)
    
    # Call the test function
    start_time = time.time()
    result = await test_func(
        mock_request=mock_request,
        mock_material_service=mock_material_service,
        mock_monitor_service=mock_monitor_service
    )
    elapsed_time = time.time() - start_time
    
    # Verify result
    assert "materials" in result
    assert result["materials"] == [TEST_MATERIAL]
    assert "count" in result
    assert result["count"] == 1
    assert mock_material_service.list_materials.called
    
    # Print diagnostic information
    print(f"Execution time: {elapsed_time:.6f} seconds")
    print(f"Result type: {type(result)}")
    print(f"Materials count: {result['count']}")
    print(f"Mock calls: {mock_material_service.list_materials.call_count}")
    
    print("\nThe create_controller_test helper function simplifies the process")
    print("by creating a test function that automatically unwraps dependencies.")
    print("This is the most convenient approach for testing FastAPI controllers.")

# Best practices for testing FastAPI controllers
def best_practices():
    """Outline best practices for testing FastAPI controllers."""
    print("\n--- Best practices for testing FastAPI controllers ---")
    
    print("1. Use the unwrap_dependencies function to replace Depends objects with mocks.")
    print("2. Use the create_controller_test helper for even simpler testing.")
    print("3. Create fixtures for common mock objects like request, services, etc.")
    print("4. Test error handling by configuring your mock services to raise exceptions.")
    print("5. Test edge cases like missing dependencies, optional dependencies, etc.")
    print("6. Use pytest.mark.asyncio for async tests.")
    print("7. Keep tests focused on controller behavior, not service implementation.")
    print("8. Use descriptive test names that explain what you're testing.")
    print("9. Group related tests together in test classes.")
    print("10. Use pytest parametrize for testing multiple scenarios.")

# Run the demonstrations
demonstrate_original_approach_issue()

if __name__ == "__main__":
    # Create proper mock objects for running the tests directly
    mock_request = AsyncMock(spec=Request)
    mock_request.url = MagicMock()
    mock_request.url.path = "/materials"
    mock_request.query_params = {}  # Use a real dict
    
    mock_material_service = MagicMock()
    mock_material_service.list_materials.return_value = [TEST_MATERIAL]
    
    mock_monitor_service = MagicMock()
    
    # Run the tests
    asyncio.run(test_recommended_approach(mock_request, mock_material_service, mock_monitor_service))
    asyncio.run(test_create_controller_test_helper(mock_request, mock_material_service, mock_monitor_service))
    best_practices() 