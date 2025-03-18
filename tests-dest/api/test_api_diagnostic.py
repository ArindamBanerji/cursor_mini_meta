# tests-dest/api/test_api_diagnostic.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock, call
from fastapi import Request
import json
import logging

logger = logging.getLogger(__name__)

from models.material import Material, MaterialStatus, MaterialType, UnitOfMeasure
from controllers.material_api_controller import api_list_materials
from controllers.material_common import MaterialFilterParams
from api.test_helpers import unwrap_dependencies

# Create a test material
TEST_MATERIAL = Material(
    material_number="MAT12345",
    name="Test Material",
    description="Test Description",
    type=MaterialType.FINISHED,
    base_unit=UnitOfMeasure.EACH,
    status=MaterialStatus.ACTIVE
)

@pytest.fixture
def mock_request():
    """Create a mock request object for testing."""
    request = AsyncMock(spec=Request)
    request.url = MagicMock()
    request.url.path = "/api/materials"
    request.query_params = {}
    return request

@pytest.fixture
def mock_request_with_params():
    """Create a mock request object with query parameters."""
    request = AsyncMock(spec=Request)
    request.url = MagicMock()
    request.url.path = "/api/materials"
    # Simulate query params
    params = {
        "search": "test",
        "status": "ACTIVE",
        "type": "FINISHED",
        "limit": "10",
        "offset": "0"
    }
    request.query_params = params
    return request

@pytest.fixture
def mock_material_service():
    """Create a diagnostic mock material service that records all calls."""
    service = MagicMock()
    service.list_materials.return_value = [TEST_MATERIAL]
    return service

@pytest.fixture
def mock_monitor_service():
    """Create a mock monitor service."""
    service = MagicMock()
    return service

@pytest.mark.asyncio
async def test_api_list_materials_diagnostic(mock_request, mock_material_service, mock_monitor_service):
    """Diagnostic test to trace exactly what's happening with api_list_materials."""
    # Create wrapped controller
    wrapped = unwrap_dependencies(
        api_list_materials,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    response = await wrapped(mock_request)
    
    # Display all calls to list_materials for diagnostic purposes
    print("\n--- Diagnostic information ---")
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.body.decode('utf-8')}")
    print(f"list_materials was called: {mock_material_service.list_materials.called}")
    print(f"Call count: {mock_material_service.list_materials.call_count}")
    if mock_material_service.list_materials.call_args:
        args, kwargs = mock_material_service.list_materials.call_args
        print(f"Args: {args}")
        print(f"Kwargs: {kwargs}")
    print("--- End diagnostic ---\n")
    
    # This assertion will likely fail, showing us the exact error
    try:
        response_data = json.loads(response.body.decode('utf-8'))
        print(f"Parsed response data: {response_data}")
    except Exception as e:
        print(f"Could not parse response body: {e}")

@pytest.mark.asyncio
async def test_api_list_materials_with_params(mock_request_with_params, mock_material_service, mock_monitor_service):
    """Diagnostic test to see how query parameters affect the calls."""
    # Create wrapped controller
    wrapped = unwrap_dependencies(
        api_list_materials,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    response = await wrapped(mock_request_with_params)
    
    # Display diagnostic information
    print("\n--- Diagnostic with query parameters ---")
    print(f"Request query params: {mock_request_with_params.query_params}")
    print(f"Response status code: {response.status_code}")
    if mock_material_service.list_materials.call_args:
        args, kwargs = mock_material_service.list_materials.call_args
        print(f"list_materials was called with kwargs: {kwargs}")
    print("--- End diagnostic ---\n")

@pytest.mark.asyncio
@patch('controllers.material_api_controller.BaseController.parse_query_params')
async def test_parse_params_diagnostic(mock_parse_query, mock_request, mock_material_service, mock_monitor_service):
    """Diagnostic test to understand query parameter parsing."""
    # Set up the mock to return a specific filter params object
    params = MaterialFilterParams(
        status=None,
        type=None,
        search=None,
        limit=10,
        offset=0
    )
    mock_parse_query.return_value = params
    
    # Create wrapped controller
    wrapped = unwrap_dependencies(
        api_list_materials,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    response = await wrapped(mock_request)
    
    # Display diagnostic information
    print("\n--- Parse parameters diagnostic ---")
    print(f"Response status code: {response.status_code}")
    if mock_material_service.list_materials.call_args:
        args, kwargs = mock_material_service.list_materials.call_args
        print(f"list_materials was called with kwargs: {kwargs}")
    print("--- End diagnostic ---\n") 

@pytest.mark.asyncio
async def test_material_service_dependency_diagnostic(mock_request, mock_monitor_service):
    """Diagnostic test to specifically examine the material service dependency."""
    from services.material_service import MaterialService
    from controllers.material_api_controller import api_list_materials
    
    # Create a mock without 'dependency' attribute
    mock_material_service = MagicMock(spec=MaterialService)
    mock_material_service.list_materials.return_value = [TEST_MATERIAL]
    
    # Create a controller with direct mock injection (no unwrap_dependencies)
    async def direct_call():
        return await api_list_materials(
            request=mock_request,
            material_service=mock_material_service,
            monitor_service=mock_monitor_service
        )
    
    # Call the function directly
    print("\n--- Material Service Dependency Diagnostic ---")
    print(f"mock_material_service type: {type(mock_material_service)}")
    print(f"mock_material_service is MaterialService: {isinstance(mock_material_service, MaterialService)}")
    print(f"hasattr mock_material_service 'dependency': {hasattr(mock_material_service, 'dependency')}")
    
    response = await direct_call()
    print(f"Response status code: {response.status_code}")
    
    # Check if list_materials was called
    print(f"list_materials was called: {mock_material_service.list_materials.called}")
    if mock_material_service.list_materials.call_args:
        args, kwargs = mock_material_service.list_materials.call_args
        print(f"Args: {args}")
        print(f"Kwargs: {kwargs}")
    print("--- End Dependency Diagnostic ---\n") 