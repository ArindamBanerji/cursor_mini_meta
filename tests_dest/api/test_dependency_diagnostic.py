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
This file contains tests to verify real FastAPI dependencies.
"""

import pytest
import logging
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException, Depends
import inspect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services through the service_imports facade
from tests_dest.test_helpers.service_imports import (
    get_material_service,
    get_monitor_service
)

# Create dependency functions
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
    
    # Call a method on the material service
    if hasattr(material_service, 'get_materials'):
        # Use proper error handling without concealing errors
        materials = material_service.get_materials()
        result["materials"] = materials
    
    # Call a method on the monitor service
    if hasattr(monitor_service, 'get_health'):
        # Use proper error handling without concealing errors
        health = monitor_service.get_health()
        result["health"] = health
    
    return result

@pytest.mark.parametrize("override_approach", [
    "override_material",
    "override_monitor",
    "override_both"
])
async def test_dependency_injection(override_approach):
    """
    Test different approaches to override dependencies with real services.
    
    Args:
        override_approach: The approach to use for overriding dependencies.
    """
    logger.info(f"Testing override approach: {override_approach}")
    app = FastAPI()
    
    # Get real services
    real_material_service = get_material_service()
    real_monitor_service = get_monitor_service()
    
    # Apply the override based on the approach
    if override_approach == "override_material":
        # Add the route with the controller
        app.get("/test")(test_controller)
        
        # Override only the material service
        app.dependency_overrides[get_material_service] = lambda: real_material_service
        
        # Test the route
        client = TestClient(app)
        response = client.get("/test")
        assert response.status_code == 200
        result = response.json()
        
        # Check that the real service was used
        assert result["material_service"] is True
        if "materials" in result:
            assert isinstance(result["materials"], list)
        
    elif override_approach == "override_monitor":
        # Add the route with the controller
        app.get("/test")(test_controller)
        
        # Override only the monitor service
        app.dependency_overrides[get_monitor_service] = lambda: real_monitor_service
        
        # Test the route
        client = TestClient(app)
        response = client.get("/test")
        assert response.status_code == 200
        result = response.json()
        
        # Check that the real service was used
        assert result["monitor_service"] is True
        if "health" in result:
            assert isinstance(result["health"], dict)
        
    elif override_approach == "override_both":
        # Add the route with the controller
        app.get("/test")(test_controller)
        
        # Override both dependencies
        app.dependency_overrides[get_material_service] = lambda: real_material_service
        app.dependency_overrides[get_monitor_service] = lambda: real_monitor_service
        
        # Test the route
        client = TestClient(app)
        response = client.get("/test")
        assert response.status_code == 200
        result = response.json()
        
        # Check that both real services were used
        assert result["material_service"] is True
        assert result["monitor_service"] is True
        if "materials" in result:
            assert isinstance(result["materials"], list)
        if "health" in result:
            assert isinstance(result["health"], dict)

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
    assert service == get_material_service()

def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Simple diagnostic test ===")
    print("Successfully executed test_dependency_diagnostic.py")
    print("All imports resolved correctly")
    
    # Run a simple test
    async def run_tests():
        await test_inspect_depends_object()
        print("Dependency inspection test passed")
        
    import asyncio
    asyncio.run(run_tests())

if __name__ == "__main__":
    run_simple_test() 