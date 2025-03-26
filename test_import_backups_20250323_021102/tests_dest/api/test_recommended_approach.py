# Import helper to fix path issues
from tests-dest.import_helper import fix_imports
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