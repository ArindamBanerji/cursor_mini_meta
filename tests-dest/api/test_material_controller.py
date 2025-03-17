# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Add this at the top of every test file
import os
import sys
from pathlib import Path

# Find project root dynamically
test_file = Path(__file__).resolve()
test_dir = test_file.parent

# Try to find project root by looking for main.py or known directories
project_root = None
for parent in [test_dir] + list(test_dir.parents):
    # Check for main.py as an indicator of project root
    if (parent / "main.py").exists():
        project_root = parent
        break
    # Check for typical project structure indicators
    if all((parent / d).exists() for d in ["services", "models", "controllers"]):
        project_root = parent
        break

# If we still don't have a project root, use parent of the tests-dest directory
if not project_root:
    # Assume we're in a test subdirectory under tests-dest
    for parent in test_dir.parents:
        if parent.name == "tests-dest":
            project_root = parent.parent
            break

# Add project root to path
if project_root and str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the test_import_helper
try:
    from test_import_helper import setup_test_paths
    setup_test_paths()
except ImportError:
    # Fall back if test_import_helper is not available
    if str(test_dir.parent) not in sys.path:
        sys.path.insert(0, str(test_dir.parent))
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root))

# Now regular imports
import pytest
# Rest of imports follow
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

# tests-dest/api/test_material_controller.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

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
    service = MagicMock()
    service.get_material.return_value = TEST_MATERIAL
    service.list_materials.return_value = [TEST_MATERIAL]
    service.create_material.return_value = TEST_MATERIAL
    service.update_material.return_value = TEST_MATERIAL
    service.deprecate_material.return_value = TEST_MATERIAL
    return service

@pytest.fixture
def mock_monitor_service():
    """Create a mock monitor service for testing."""
    service = MagicMock()
    service.log_error = MagicMock()
    return service

# UI Controller Tests

@patch('controllers.material_ui_controller.get_material_service_dependency')
@patch('controllers.material_ui_controller.get_monitor_service_dependency')
async def test_list_materials(mock_get_monitor, mock_get_material, mock_request, mock_material_service, mock_monitor_service):
    """Test the list_materials controller function."""
    # Setup mocks
    mock_get_material.return_value = mock_material_service
    mock_get_monitor.return_value = mock_monitor_service
    
    # Call the function
    result = await list_materials(mock_request)
    
    # Verify result
    assert "materials" in result
    assert result["materials"] == [TEST_MATERIAL]
    assert "count" in result
    assert result["count"] == 1
    mock_material_service.list_materials.assert_called_once()

@patch('controllers.material_ui_controller.get_material_service_dependency')
@patch('controllers.material_ui_controller.get_monitor_service_dependency')
async def test_get_material(mock_get_monitor, mock_get_material, mock_request, mock_material_service, mock_monitor_service):
    """Test the get_material controller function."""
    # Setup mocks
    mock_get_material.return_value = mock_material_service
    mock_get_monitor.return_value = mock_monitor_service
    
    # Call the function
    result = await get_material(mock_request, "MAT12345")
    
    # Verify result
    assert "material" in result
    assert result["material"] == TEST_MATERIAL
    mock_material_service.get_material.assert_called_once_with("MAT12345")

@patch('controllers.material_ui_controller.get_material_service_dependency')
@patch('controllers.material_ui_controller.get_monitor_service_dependency')
async def test_get_material_not_found(mock_get_monitor, mock_get_material, mock_request, mock_material_service, mock_monitor_service):
    """Test the get_material controller function with a not found error."""
    # Setup mocks
    mock_get_material.return_value = mock_material_service
    mock_get_monitor.return_value = mock_monitor_service
    mock_material_service.get_material.side_effect = NotFoundError("Material not found")
    
    # Call the function, expect a redirect
    response = await get_material(mock_request, "NONEXISTENT")
    
    # Verify it's a redirect
    assert isinstance(response, RedirectResponse)
    assert "materials" in response.headers["location"]
    assert "error" in response.headers["location"]
    mock_material_service.get_material.assert_called_once_with("NONEXISTENT")

@patch('controllers.material_ui_controller.get_material_service_dependency')
@patch('controllers.material_ui_controller.get_monitor_service_dependency')
async def test_create_material_form(mock_get_monitor, mock_get_material, mock_request, mock_material_service, mock_monitor_service):
    """Test the create_material_form controller function."""
    # Setup mocks
    mock_get_material.return_value = mock_material_service
    mock_get_monitor.return_value = mock_monitor_service
    
    # Call the function
    result = await create_material_form(mock_request)
    
    # Verify result
    assert "title" in result
    assert "form_action" in result
    assert "options" in result
    assert "types" in result["options"]
    assert "units" in result["options"]
    assert "statuses" in result["options"]

@patch('controllers.material_ui_controller.get_material_service_dependency')
@patch('controllers.material_ui_controller.get_monitor_service_dependency')
async def test_create_material(mock_get_monitor, mock_get_material, mock_request, mock_material_service, mock_monitor_service):
    """Test the create_material controller function."""
    # Setup mocks
    mock_get_material.return_value = mock_material_service
    mock_get_monitor.return_value = mock_monitor_service
    
    # Call the function
    response = await create_material(mock_request)
    
    # Verify it's a redirect to the detail page
    assert isinstance(response, RedirectResponse)
    assert f"/materials/{TEST_MATERIAL.material_number}" in response.headers["location"]
    mock_material_service.create_material.assert_called_once()

@patch('controllers.material_ui_controller.get_material_service_dependency')
@patch('controllers.material_ui_controller.get_monitor_service_dependency')
async def test_create_material_validation_error(mock_get_monitor, mock_get_material, mock_request, mock_material_service, mock_monitor_service):
    """Test the create_material controller function with validation error."""
    # Setup mocks
    mock_get_material.return_value = mock_material_service
    mock_get_monitor.return_value = mock_monitor_service
    mock_material_service.create_material.side_effect = ValidationError(
        message="Validation failed",
        details={"validation_errors": {"name": "Name is required"}}
    )
    
    # Call the function
    result = await create_material(mock_request)
    
    # Verify it returns the form context with errors
    assert "errors" in result
    assert "name" in result["errors"]
    assert "form_data" in result
    mock_material_service.create_material.assert_called_once()

@patch('controllers.material_ui_controller.get_material_service_dependency')
@patch('controllers.material_ui_controller.get_monitor_service_dependency')
async def test_update_material_form(mock_get_monitor, mock_get_material, mock_request, mock_material_service, mock_monitor_service):
    """Test the update_material_form controller function."""
    # Setup mocks
    mock_get_material.return_value = mock_material_service
    mock_get_monitor.return_value = mock_monitor_service
    
    # Call the function
    result = await update_material_form(mock_request, "MAT12345")
    
    # Verify result
    assert "title" in result
    assert "material" in result
    assert result["material"] == TEST_MATERIAL
    assert "form_action" in result
    assert "options" in result
    mock_material_service.get_material.assert_called_once_with("MAT12345")

@patch('controllers.material_ui_controller.get_material_service_dependency')
@patch('controllers.material_ui_controller.get_monitor_service_dependency')
async def test_update_material(mock_get_monitor, mock_get_material, mock_request, mock_material_service, mock_monitor_service):
    """Test the update_material controller function."""
    # Setup mocks
    mock_get_material.return_value = mock_material_service
    mock_get_monitor.return_value = mock_monitor_service
    
    # Call the function
    response = await update_material(mock_request, "MAT12345")
    
    # Verify it's a redirect to the detail page
    assert isinstance(response, RedirectResponse)
    assert f"/materials/{TEST_MATERIAL.material_number}" in response.headers["location"]
    mock_material_service.update_material.assert_called_once()

@patch('controllers.material_ui_controller.get_material_service_dependency')
@patch('controllers.material_ui_controller.get_monitor_service_dependency')
async def test_deprecate_material(mock_get_monitor, mock_get_material, mock_request, mock_material_service, mock_monitor_service):
    """Test the deprecate_material controller function."""
    # Setup mocks
    mock_get_material.return_value = mock_material_service
    mock_get_monitor.return_value = mock_monitor_service
    
    # Call the function
    response = await deprecate_material(mock_request, "MAT12345")
    
    # Verify it's a redirect to the detail page
    assert isinstance(response, RedirectResponse)
    assert f"/materials/{TEST_MATERIAL.material_number}" in response.headers["location"]
    assert "message" in response.headers["location"]
    mock_material_service.deprecate_material.assert_called_once_with("MAT12345")

# API Controller Tests

@patch('controllers.material_api_controller.get_material_service_dependency')
@patch('controllers.material_api_controller.get_monitor_service_dependency')
async def test_api_list_materials(mock_get_monitor, mock_get_material, mock_request, mock_material_service, mock_monitor_service):
    """Test the api_list_materials controller function."""
    # Setup mocks
    mock_get_material.return_value = mock_material_service
    mock_get_monitor.return_value = mock_monitor_service
    
    # Call the function
    response = await api_list_materials(mock_request)
    
    # Verify it's a JSON response with success status
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    content = response.body.decode()
    assert "success" in content
    assert "true" in content.lower()
    assert "materials" in content
    mock_material_service.list_materials.assert_called_once()

@patch('controllers.material_api_controller.get_material_service_dependency')
@patch('controllers.material_api_controller.get_monitor_service_dependency')
async def test_api_get_material(mock_get_monitor, mock_get_material, mock_request, mock_material_service, mock_monitor_service):
    """Test the api_get_material controller function."""
    # Setup mocks
    mock_get_material.return_value = mock_material_service
    mock_get_monitor.return_value = mock_monitor_service
    
    # Call the function
    response = await api_get_material(mock_request, "MAT12345")
    
    # Verify it's a JSON response with success status
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    content = response.body.decode()
    assert "success" in content
    assert "true" in content.lower()
    assert "material" in content
    mock_material_service.get_material.assert_called_once_with("MAT12345")

@patch('controllers.material_api_controller.get_material_service_dependency')
@patch('controllers.material_api_controller.get_monitor_service_dependency')
@patch('controllers.material_api_controller.BaseController.parse_json_body')
async def test_api_create_material(mock_parse_json, mock_get_monitor, mock_get_material, mock_request, mock_material_service, mock_monitor_service):
    """Test the api_create_material controller function."""
    # Setup mocks
    mock_get_material.return_value = mock_material_service
    mock_get_monitor.return_value = mock_monitor_service
    material_data = MaterialCreate(
        name="Test Material",
        description="Test Description",
        type=MaterialType.FINISHED,
        base_unit=UnitOfMeasure.EACH
    )
    mock_parse_json.return_value = material_data
    
    # Call the function
    response = await api_create_material(mock_request)
    
    # Verify it's a JSON response with success status and 201 code
    assert isinstance(response, JSONResponse)
    assert response.status_code == 201
    content = response.body.decode()
    assert "success" in content
    assert "true" in content.lower()
    assert "material" in content
    mock_material_service.create_material.assert_called_once()
    mock_parse_json.assert_called_once()

@patch('controllers.material_api_controller.get_material_service_dependency')
@patch('controllers.material_api_controller.get_monitor_service_dependency')
@patch('controllers.material_api_controller.BaseController.parse_json_body')
async def test_api_update_material(mock_parse_json, mock_get_monitor, mock_get_material, mock_request, mock_material_service, mock_monitor_service):
    """Test the api_update_material controller function."""
    # Setup mocks
    mock_get_material.return_value = mock_material_service
    mock_get_monitor.return_value = mock_monitor_service
    update_data = MaterialUpdate(name="Updated Material")
    mock_parse_json.return_value = update_data
    
    # Call the function
    response = await api_update_material(mock_request, "MAT12345")
    
    # Verify it's a JSON response with success status
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    content = response.body.decode()
    assert "success" in content
    assert "true" in content.lower()
    assert "material" in content
    mock_material_service.update_material.assert_called_once_with("MAT12345", update_data)
    mock_parse_json.assert_called_once()

@patch('controllers.material_api_controller.get_material_service_dependency')
@patch('controllers.material_api_controller.get_monitor_service_dependency')
async def test_api_deprecate_material(mock_get_monitor, mock_get_material, mock_request, mock_material_service, mock_monitor_service):
    """Test the api_deprecate_material controller function."""
    # Setup mocks
    mock_get_material.return_value = mock_material_service
    mock_get_monitor.return_value = mock_monitor_service
    
    # Call the function
    response = await api_deprecate_material(mock_request, "MAT12345")
    
    # Verify it's a JSON response with success status
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    content = response.body.decode()
    assert "success" in content
    assert "true" in content.lower()
    assert "material_number" in content
    assert "status" in content
    mock_material_service.deprecate_material.assert_called_once_with("MAT12345")
