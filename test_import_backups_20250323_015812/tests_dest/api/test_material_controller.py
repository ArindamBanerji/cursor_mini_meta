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


# tests-dest/api/test_material_controller.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

from models.material import Material, MaterialCreate, MaterialUpdate, MaterialStatus, MaterialType, UnitOfMeasure
from controllers.material_ui_controller import (
    list_materials, get_material, create_material_form, 
    create_material, update_material_form, update_material, 
    deprecate_material
)
from controllers.material_api_controller import (
    api_list_materials, api_get_material, api_create_material,
    api_update_material, api_deprecate_material
)
from utils.error_utils import NotFoundError, ValidationError
from api.test_helpers import unwrap_dependencies, create_controller_test

# Test data
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
    request.url.path = "/materials"
    request.query_params = {}
    # Make form method return a dict-like object asynchronously
    form_data = MagicMock()
    form_data.get = lambda key, default=None: {
        "name": "Test Material",
        "description": "Test Description",
        "type": "FINISHED",
        "base_unit": "EA",
        "status": "ACTIVE",
        "weight": "10.5",
        "volume": "5.0"
    }.get(key, default)
    form_data.__iter__ = lambda self: iter({"name", "description", "type", "base_unit", "status", "weight", "volume"})
    request.form = AsyncMock(return_value=form_data)
    return request

@pytest.fixture
def mock_material_service():
    """Create a mock material service for testing."""
    from services.material_service import MaterialService
    service = MagicMock(spec=MaterialService)
    service.get_material.return_value = TEST_MATERIAL
    # Configure list_materials to accept any arguments and still return the test material
    service.list_materials.return_value = [TEST_MATERIAL]
    service.create_material.return_value = TEST_MATERIAL
    service.update_material.return_value = TEST_MATERIAL
    service.deprecate_material.return_value = TEST_MATERIAL
    return service

@pytest.fixture
def mock_monitor_service():
    """Create a mock monitor service for testing."""
    from services.monitor_service import MonitorService
    service = MagicMock(spec=MonitorService)
    service.log_error = MagicMock()
    return service

# UI Controller Tests

@pytest.mark.asyncio
async def test_list_materials(mock_request, mock_material_service, mock_monitor_service):
    """Test the list_materials controller function."""
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        list_materials,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    result = await wrapped(mock_request)
    
    # Verify result
    assert "materials" in result
    assert isinstance(result["materials"], list)
    assert len(result["materials"]) == 1
    assert result["materials"][0].material_number == TEST_MATERIAL.material_number

@pytest.mark.asyncio
async def test_get_material(mock_request, mock_material_service, mock_monitor_service):
    """Test the get_material controller function."""
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        get_material,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    result = await wrapped(mock_request, "MAT12345")
    
    # Verify result
    assert "material" in result
    assert result["material"] == TEST_MATERIAL
    mock_material_service.get_material.assert_called_once_with("MAT12345")

@pytest.mark.asyncio
async def test_get_material_not_found(mock_request, mock_material_service, mock_monitor_service):
    """Test the get_material controller function with a not found error."""
    # Setup mocks
    mock_material_service.get_material.side_effect = NotFoundError("Material not found")
    
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        get_material,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function, expect a redirect
    response = await wrapped(mock_request, "NONEXISTENT")
    
    # Verify it's a redirect
    assert isinstance(response, RedirectResponse)
    assert response.status_code == 303  # Redirect status code is 303 See Other
    assert "materials" in response.headers["location"]
    assert "error" in response.headers["location"]
    mock_material_service.get_material.assert_called_once_with("NONEXISTENT")

@pytest.mark.asyncio
async def test_create_material_form(mock_request, mock_material_service, mock_monitor_service):
    """Test the create_material_form controller function."""
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        create_material_form,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    result = await wrapped(mock_request)
    
    # Verify result
    assert "title" in result
    assert "form_action" in result
    assert "options" in result
    assert "types" in result["options"]
    assert "units" in result["options"]
    assert "statuses" in result["options"]

@pytest.mark.asyncio
async def test_create_material(mock_request, mock_material_service, mock_monitor_service):
    """Test the create_material controller function."""
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        create_material,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    response = await wrapped(mock_request)
    
    # Verify it's a redirect to the detail page
    assert isinstance(response, RedirectResponse)
    assert response.status_code == 303  # POST redirect should use 303 See Other
    assert f"/materials/{TEST_MATERIAL.material_number}" in response.headers["location"]
    mock_material_service.create_material.assert_called_once()

@pytest.mark.asyncio
async def test_create_material_validation_error(mock_request, mock_material_service, mock_monitor_service):
    """Test the create_material controller function with validation error."""
    # Setup mocks
    mock_material_service.create_material.side_effect = ValidationError(
        message="Validation error",
        details={"name": "Name is required"}
    )
    
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        create_material,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    result = await wrapped(mock_request)
    
    # Verify result contains errors
    assert "errors" in result
    assert "name" in result["errors"]
    assert "form_data" in result
    mock_material_service.create_material.assert_called_once()

@pytest.mark.asyncio
async def test_update_material_form(mock_request, mock_material_service, mock_monitor_service):
    """Test the update_material_form controller function."""
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        update_material_form,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    result = await wrapped(mock_request, "MAT12345")
    
    # Verify result
    assert "material" in result
    assert result["material"] == TEST_MATERIAL
    assert "options" in result
    assert "types" in result["options"]
    assert "units" in result["options"]
    assert "statuses" in result["options"]
    mock_material_service.get_material.assert_called_once_with("MAT12345")

@pytest.mark.asyncio
async def test_update_material(mock_request, mock_material_service, mock_monitor_service):
    """Test the update_material controller function."""
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        update_material,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    response = await wrapped(mock_request, "MAT12345")
    
    # Verify it's a redirect to the detail page
    assert isinstance(response, RedirectResponse)
    assert response.status_code == 303  # POST redirect should use 303 See Other
    assert f"/materials/{TEST_MATERIAL.material_number}" in response.headers["location"]
    mock_material_service.update_material.assert_called_once()

@pytest.mark.asyncio
async def test_deprecate_material(mock_request, mock_material_service, mock_monitor_service):
    """Test the deprecate_material controller function."""
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        deprecate_material,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    response = await wrapped(mock_request, "MAT12345")
    
    # Verify it's a redirect to the detail page
    assert isinstance(response, RedirectResponse)
    assert response.status_code == 303  # POST redirect should use 303 See Other
    assert f"/materials/{TEST_MATERIAL.material_number}" in response.headers["location"]
    mock_material_service.deprecate_material.assert_called_once_with("MAT12345")

# API Controller Tests

@pytest.mark.asyncio
async def test_api_list_materials(mock_request, mock_material_service, mock_monitor_service):
    """Test the api_list_materials controller function."""
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        api_list_materials,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    response = await wrapped(mock_request)
    
    # Verify response
    assert response.status_code == 200
    data = response.body.decode('utf-8')
    assert "materials" in data
    assert "count" in data
    mock_material_service.list_materials.assert_called_once()

@pytest.mark.asyncio
async def test_api_get_material(mock_request, mock_material_service, mock_monitor_service):
    """Test the api_get_material controller function."""
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        api_get_material,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    response = await wrapped(mock_request, "MAT12345")
    
    # Verify response
    assert response.status_code == 200
    data = response.body.decode('utf-8')
    assert "material_number" in data
    assert "name" in data
    mock_material_service.get_material.assert_called_once_with("MAT12345")

@pytest.mark.asyncio
@patch('controllers.material_api_controller.BaseController.parse_json_body')
async def test_api_create_material(mock_parse_json, mock_request, mock_material_service, mock_monitor_service):
    """Test the api_create_material controller function."""
    # Setup mocks
    material_data = MaterialCreate(
        name="Test Material",
        description="Test Description",
        type=MaterialType.FINISHED,
        base_unit=UnitOfMeasure.EACH
    )
    mock_parse_json.return_value = material_data
    
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        api_create_material,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    response = await wrapped(mock_request)
    
    # Verify response
    assert response.status_code == 201
    data = response.body.decode('utf-8')
    assert "material_number" in data
    assert "name" in data
    mock_material_service.create_material.assert_called_once_with(material_data)

@pytest.mark.asyncio
@patch('controllers.material_api_controller.BaseController.parse_json_body')
async def test_api_update_material(mock_parse_json, mock_request, mock_material_service, mock_monitor_service):
    """Test the api_update_material controller function."""
    # Setup mocks
    update_data = MaterialUpdate(name="Updated Material")
    mock_parse_json.return_value = update_data
    
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        api_update_material,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    response = await wrapped(mock_request, "MAT12345")
    
    # Verify response
    assert response.status_code == 200
    data = response.body.decode('utf-8')
    assert "material_number" in data
    assert "name" in data
    mock_material_service.update_material.assert_called_once_with("MAT12345", update_data)

@pytest.mark.asyncio
async def test_api_deprecate_material(mock_request, mock_material_service, mock_monitor_service):
    """Test the api_deprecate_material controller function."""
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        api_deprecate_material,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Call the function
    response = await wrapped(mock_request, "MAT12345")
    
    # Verify response
    assert response.status_code == 200
    data = response.body.decode('utf-8')
    assert "material_number" in data
    assert "status" in data
    mock_material_service.deprecate_material.assert_called_once_with("MAT12345")
