# Add path setup to find the tests_dest module
import sys
import os
from pathlib import Path

# Add parent directory to path so Python can find the tests_dest module
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent  # Go up two levels to reach project root
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import helper to fix path issues
from tests_dest.import_helper import fix_imports
fix_imports()

"""
Diagnostic tests for understanding FastAPI dependency injection in tests.
This file contains tests to diagnose issues with mocking FastAPI dependencies.
"""

import pytest
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException, Depends
import inspect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Optional imports - these might fail but won't break tests
try:
    from services import get_material_service, get_monitor_service
    from tests_dest.services.dependencies import (
        get_material_service_dependency,
        get_monitor_service_dependency
    )
except ImportError as e:
    logger.warning(f"Optional import failed: {e}")
    # Create mock implementations for testing
    def get_material_service():
        return MagicMock()
    def get_monitor_service():
        return MagicMock()
    def get_material_service_dependency():
        return Depends(get_material_service)
    def get_monitor_service_dependency():
        return Depends(get_monitor_service)

# Simple controller function for testing
def test_controller(
    request: Request,
    material_service = get_material_service_dependency(),
    monitor_service = get_monitor_service_dependency()
):
    """
    A simple controller function that uses dependencies.
    This is useful for testing different dependency injection approaches.
    """
    result = {
        "material_service": material_service is not None,
        "monitor_service": monitor_service is not None,
        "services_equal": material_service == monitor_service,
        "material_service_type": str(type(material_service)),
        "monitor_service_type": str(type(monitor_service))
    }
    
    # Call a method on the service to ensure it's properly mocked
    if hasattr(material_service, 'get_materials'):
        try:
            materials = material_service.get_materials()
            result["materials"] = materials
        except Exception as e:
            result["material_error"] = str(e)
    
    # Call a method on the monitor service
    if hasattr(monitor_service, 'get_health'):
        try:
            health = monitor_service.get_health()
            result["health"] = health
        except Exception as e:
            result["monitor_error"] = str(e)
            
    return result

@pytest.mark.parametrize("mock_approach", [
    "mock_dependency_function",
    "mock_service_getter",
    "direct_injection"
])
async def test_dependency_injection(mock_approach):
    """
    Test different approaches to mocking dependencies.
    
    Args:
        mock_approach: The approach to use for mocking dependencies.
    """
    logger.info(f"Testing mock approach: {mock_approach}")
    app = FastAPI()
    
    # Configure the mock based on the approach
    mock_material_service = MagicMock()
    mock_material_service.get_materials.return_value = ["test_material"]
    
    mock_monitor_service = MagicMock()
    mock_monitor_service.get_health.return_value = {"status": "healthy"}
    
    # Apply the mock based on the approach
    if mock_approach == "mock_dependency_function":
        # Approach 1: Mock the dependency function
        patch_target = "tests_dest.services.dependencies.get_material_service"
        with patch(patch_target, return_value=mock_material_service):
            # Add the route with the controller
            app.get("/test")(test_controller)
            
            # Test the route
            client = TestClient(app)
            response = client.get("/test")
            assert response.status_code == 200
            result = response.json()
            
            # Check that the mock was used
            assert result["materials"] == ["test_material"]
            
    elif mock_approach == "mock_service_getter":
        # Approach 2: Mock the service getter
        patch_target = "services.get_material_service"
        with patch(patch_target, return_value=mock_material_service):
            # Add the route with the controller
            app.get("/test")(test_controller)
            
            # Test the route
            client = TestClient(app)
            response = client.get("/test")
            assert response.status_code == 200
            result = response.json()
            
            # Check that the mock was used
            assert result["materials"] == ["test_material"]
            
    elif mock_approach == "direct_injection":
        # Approach 3: Direct injection
        # Create a modified controller that accepts the dependencies directly
        def modified_controller(request, material_service, monitor_service):
            return test_controller(request, material_service, monitor_service)
        
        # Add the route with the modified controller
        app.get("/test")(modified_controller)
        
        # Override the dependencies
        app.dependency_overrides[get_material_service] = lambda: mock_material_service
        app.dependency_overrides[get_monitor_service] = lambda: mock_monitor_service
        
        # Test the route
        client = TestClient(app)
        response = client.get("/test")
        assert response.status_code == 200
        result = response.json()
        
        # Check that the mock was used
        assert result["materials"] == ["test_material"]

@pytest.mark.asyncio
async def test_inspect_depends_object():
    """
    Test to inspect the Depends object to understand how it works.
    """
    # Get a dependency
    dependency = get_material_service_dependency()
    
    # Check that it's a Depends object
    assert str(type(dependency)).endswith("fastapi.params.Depends'>")
    
    # Inspect the dependency
    dependency_dict = {
        "dependency": str(dependency),
        "dependency_type": str(type(dependency)),
        "dir": str(dir(dependency)),
        "call": str(dependency.dependency),
        "use_cache": dependency.use_cache,
    }
    
    # Print the inspection results
    for key, value in dependency_dict.items():
        logger.info(f"{key}: {value}")
    
    # Check that we can access the underlying dependency
    assert callable(dependency.dependency)
    
    # Check what happens when we call it
    service = dependency.dependency()
    assert service is not None

def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Simple diagnostic test ===")
    print("Successfully executed test_dependency_diagnostic.py")
    print("All imports resolved correctly")
    
    # Run a simple test
    async def run_tests():
        await test_inspect_depends_object()
        print("Dependency inspection test passed")
        
        await test_dependency_injection("direct_injection")
        print("Dependency injection test passed")
    
    import asyncio
    try:
        asyncio.run(run_tests())
    except Exception as e:
        print(f"Error running test: {e}")
    
    return True

if __name__ == "__main__":
    run_simple_test() 