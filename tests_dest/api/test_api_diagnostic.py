# tests_dest/api/test_api_diagnostic.py
# Add path setup for Python to find the tests_dest module
import sys
import os
from pathlib import Path

# Add parent directory to path
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent  # Go up two levels to reach project root
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import helper to fix path issues
from tests_dest.import_helper import fix_imports
fix_imports()

import pytest
import logging
import json
from fastapi import Request, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services and models through service_imports.py
from tests_dest.test_helpers.service_imports import (
    BaseService,
    MaterialService, 
    get_material_service,
    MonitorService, 
    get_monitor_service,
    Material, 
    MaterialStatus, 
    MaterialType, 
    UnitOfMeasure
)
from controllers.material_api_controller import api_list_materials
from controllers.material_common import MaterialFilterParams

# Create request fixtures using real objects
@pytest.fixture
def request_obj():
    """Create a request object for testing."""
    # Use FastAPI's TestClient to create a real request
    app = FastAPI()
    client = TestClient(app)
    return Request({"type": "http", "query_string": b"", "path": "/api/materials"})

@pytest.fixture
def request_with_params():
    """Create a request object with query parameters."""
    app = FastAPI()
    client = TestClient(app)
    return Request({
        "type": "http", 
        "path": "/api/materials",
        "query_string": b"search=test&status=ACTIVE&type=FINISHED&limit=10&offset=0"
    })

@pytest.fixture
def material_service():
    """Create a real material service instance for testing."""
    return get_material_service()

@pytest.fixture
def monitor_service():
    """Create a real monitor service instance for testing."""
    return get_monitor_service()

@pytest.mark.asyncio
async def test_api_list_materials_diagnostic(request_obj, material_service, monitor_service):
    """Test api_list_materials with real dependencies."""
    # Call the function directly with real services
    response = await api_list_materials(
        request=request_obj,
        material_service=material_service,
        monitor_service=monitor_service
    )
    
    # Display diagnostic information
    print("\n--- Diagnostic information ---")
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.body.decode('utf-8')}")
    print(f"material_service type: {type(material_service)}")
    print(f"monitor_service type: {type(monitor_service)}")
    print("--- End diagnostic ---\n")
    
    # Parse response data
    response_data = json.loads(response.body.decode('utf-8'))
    print(f"Parsed response data: {response_data}")
    
    # Assertions
    assert response.status_code == 200
    assert isinstance(response_data, dict)
    assert 'materials' in response_data
    assert isinstance(response_data['materials'], list)
    assert 'count' in response_data
    assert 'filters' in response_data

@pytest.mark.asyncio
async def test_api_list_materials_with_params(request_with_params, material_service, monitor_service):
    """Test with query parameters using real dependencies."""
    # Call the function directly with real services
    response = await api_list_materials(
        request=request_with_params,
        material_service=material_service,
        monitor_service=monitor_service
    )
    
    # Display diagnostic information
    print("\n--- Diagnostic with query parameters ---")
    print(f"Response status code: {response.status_code}")
    print("--- End diagnostic ---\n")
    
    # Assertions
    assert response.status_code == 200
    response_data = json.loads(response.body.decode('utf-8'))
    assert isinstance(response_data, dict)
    assert 'materials' in response_data
    assert isinstance(response_data['materials'], list)
    assert 'filters' in response_data
    assert response_data['filters']['search'] == 'test'
    assert response_data['filters']['status'] == 'ACTIVE'
    assert response_data['filters']['type'] == 'FINISHED'
    assert response_data['filters']['limit'] == 10
    assert response_data['filters']['offset'] == 0

@pytest.mark.asyncio
async def test_material_service_dependency(request_obj):
    """Test dependency injection with real services."""
    # Get real services directly
    material_service = get_material_service()
    monitor_service = get_monitor_service()
    
    # Call the api function directly
    response = await api_list_materials(
        request=request_obj,
        material_service=material_service,
        monitor_service=monitor_service
    )
    
    # Display diagnostic information
    print("\n--- Service Dependency Diagnostic ---")
    print(f"material_service type: {type(material_service)}")
    print(f"material_service is MaterialService: {isinstance(material_service, MaterialService)}")
    print(f"Response status code: {response.status_code}")
    print("--- End Dependency Diagnostic ---\n")
    
    # Assertions
    assert response.status_code == 200
    assert isinstance(material_service, MaterialService)
    assert isinstance(monitor_service, MonitorService)

def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Simple diagnostic test ===")
    print("Successfully executed test_api_diagnostic.py")
    print("All imports resolved correctly")
    return True

if __name__ == "__main__":
    run_simple_test()
