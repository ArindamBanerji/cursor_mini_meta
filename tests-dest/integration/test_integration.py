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

# tests-dest/integration/test_integration.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
import urllib.parse

from models.material import (
    Material, MaterialCreate, MaterialUpdate, MaterialType, MaterialStatus, UnitOfMeasure
)
from services.state_manager import StateManager
from services.material_service import MaterialService
from services.monitor_service import MonitorService
from services import register_service, reset_services, clear_service_registry

@pytest.fixture
def state_manager():
    """Create a clean state manager for testing."""
    manager = StateManager()
    manager.clear()
    return manager

@pytest.fixture
def test_services(state_manager):
    """Set up test services with clean state."""
    # Reset all services to ensure clean state
    reset_services()
    
    # Create test services with the clean state manager
    monitor_service = MonitorService(state_manager)
    material_service = MaterialService(state_manager, monitor_service)
    
    # Register services for discovery
    register_service("monitor", monitor_service)
    register_service("material", material_service)
    
    yield {
        "state_manager": state_manager,
        "monitor_service": monitor_service,
        "material_service": material_service
    }
    
    # Clean up
    clear_service_registry()

@pytest.fixture
def test_material():
    """Create a test material for testing."""
    return Material(
        material_number="TEST001",
        name="Test Material",
        description="A test material for integration testing",
        type=MaterialType.FINISHED,
        base_unit=UnitOfMeasure.EACH,
        status=MaterialStatus.ACTIVE
    )

class TestIntegration:
    """
    Integration tests for the SAP Test Harness.
    Tests interactions between controllers and services.
    """
    
    async def test_material_creation_flow(self, test_services, test_material):
        """Test the entire material creation flow from controller to service to data layer."""
        from controllers.material_ui_controller import create_material
        
        # Create a mock request
        mock_request = AsyncMock(spec=Request)
        mock_form = MagicMock()
        mock_form.get = lambda key, default=None: {
            "name": test_material.name,
            "description": test_material.description,
            "type": test_material.type.value,
            "base_unit": test_material.base_unit.value,
            "status": test_material.status.value
        }.get(key, default)
        mock_form.__iter__ = lambda self: iter({"name", "description", "type", "base_unit", "status"})
        mock_request.form = AsyncMock(return_value=mock_form)
        
        # Test that the controller correctly calls the service
        with patch('controllers.material_ui_controller.get_material_service', 
                  return_value=test_services["material_service"]), \
             patch('controllers.material_ui_controller.get_monitor_service', 
                  return_value=test_services["monitor_service"]), \
             patch('controllers.material_ui_controller.get_material_service_dependency', 
                  return_value=test_services["material_service"]), \
             patch('controllers.material_ui_controller.get_monitor_service_dependency', 
                  return_value=test_services["monitor_service"]):
            
            # Call the controller method
            response = await create_material(mock_request)
            
            # Verify the response is a redirect to the material detail page
            assert isinstance(response, RedirectResponse)
            assert "/materials/" in response.headers["location"]
            
            # Get the created material ID from the redirect URL
            material_id = response.headers["location"].split("/materials/")[1]
            if "?" in material_id:
                material_id = material_id.split("?")[0]
            
            # Verify the material was actually created in the database
            created_material = test_services["material_service"].get_material(material_id)
            assert created_material is not None
            assert created_material.name == test_material.name
            assert created_material.description == test_material.description
            
            # Verify that an error log was created for the successful operation
            error_logs = test_services["monitor_service"].get_error_logs(error_type="info")
            assert any("created successfully" in log.message for log in error_logs)
    
    async def test_material_api_update_flow(self, test_services):
        """Test the material API update flow from controller to service to data layer."""
        from controllers.material_api_controller import api_update_material
        
        # First create a material to update
        material_create = MaterialCreate(
            name="Original Name",
            description="Original Description",
            type=MaterialType.FINISHED,
            base_unit=UnitOfMeasure.EACH
        )
        
        material = test_services["material_service"].create_material(material_create)
        material_id = material.material_number
        
        # Create update data
        update_data = MaterialUpdate(
            name="Updated Name",
            description="Updated Description"
        )
        
        # Create a mock request for the API update
        mock_request = AsyncMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = f"/api/v1/materials/{material_id}"
        
        # Test that the controller correctly calls the service
        with patch('controllers.material_api_controller.get_material_service', 
                  return_value=test_services["material_service"]), \
             patch('controllers.material_api_controller.get_monitor_service', 
                  return_value=test_services["monitor_service"]), \
             patch('controllers.material_api_controller.get_material_service_dependency', 
                  return_value=test_services["material_service"]), \
             patch('controllers.material_api_controller.get_monitor_service_dependency', 
                  return_value=test_services["monitor_service"]), \
             patch('controllers.material_api_controller.BaseController.parse_json_body', 
                  return_value=update_data):
            
            # Call the controller method
            response = await api_update_material(mock_request, material_id)
            
            # Verify the response is a JSON success response
            assert isinstance(response, JSONResponse)
            assert response.status_code == 200
            
            # Verify the response data
            response_data = json.loads(response.body)
            assert response_data["success"] == True
            assert response_data["data"]["material"]["name"] == "Updated Name"
            assert response_data["data"]["material"]["description"] == "Updated Description"
            
            # Verify the material was actually updated in the database
            updated_material = test_services["material_service"].get_material(material_id)
            assert updated_material.name == "Updated Name"
            assert updated_material.description == "Updated Description"
    
    async def test_material_not_found_handling(self, test_services):
        """Test handling of not found errors across controller and service."""
        from controllers.material_ui_controller import get_material
        
        # Create a mock request
        mock_request = AsyncMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/materials/NONEXISTENT"
        
        # Test that the controller correctly handles not found errors
        with patch('controllers.material_ui_controller.get_material_service_dependency', 
                  return_value=test_services["material_service"]), \
             patch('controllers.material_ui_controller.get_monitor_service_dependency', 
                  return_value=test_services["monitor_service"]):
            
            # Call the controller method - should redirect to list page
            response = await get_material(mock_request, "NONEXISTENT")
            
            # Verify the response is a redirect to the materials list
            assert isinstance(response, RedirectResponse)
            assert "/materials" in response.headers["location"]
            
            # URL decode the location to properly check for the error message
            decoded_location = urllib.parse.unquote(response.headers["location"])
            assert "error" in decoded_location
            assert "not found" in decoded_location.lower()
    
    async def test_material_api_error_handling(self, test_services):
        """Test API error handling across controller and service layers."""
        from controllers.material_api_controller import api_get_material
        
        # Create a mock request
        mock_request = AsyncMock(spec=Request)
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/v1/materials/NONEXISTENT"
        
        # Test that the API controller correctly handles not found errors
        with patch('controllers.material_api_controller.get_material_service', 
                  return_value=test_services["material_service"]), \
             patch('controllers.material_api_controller.get_monitor_service', 
                  return_value=test_services["monitor_service"]), \
             patch('controllers.material_api_controller.get_material_service_dependency', 
                  return_value=test_services["material_service"]), \
             patch('controllers.material_api_controller.get_monitor_service_dependency', 
                  return_value=test_services["monitor_service"]):
            
            # Call the controller method
            response = await api_get_material(mock_request, "NONEXISTENT")
            
            # Verify the response is a JSON error response with 404 status
            assert isinstance(response, JSONResponse)
            assert response.status_code == 404
            
            # Check the response body
            response_data = json.loads(response.body)
            assert response_data["success"] == False
            assert response_data["error"] == "not_found"
            assert "material_id" in response_data["details"]
            
            # Verify that an error log was created
            error_logs = test_services["monitor_service"].get_error_logs(error_type="not_found_error")
            assert any("not found" in log.message for log in error_logs)
    
    async def test_service_error_logging_integration(self, test_services):
        """Test that service errors are properly logged to the monitor service."""
        material_service = test_services["material_service"]
        monitor_service = test_services["monitor_service"]
        
        # Attempt to perform an operation that will cause an error
        try:
            # Try to update a non-existent material
            material_service.update_material("NONEXISTENT", MaterialUpdate(name="New Name"))
        except Exception:
            # We expect an exception, but we're testing error logging
            pass
        
        # Wait a short time for async operations to complete
        await asyncio.sleep(0.1)
        
        # Verify error was logged
        error_logs = monitor_service.get_error_logs(error_type="not_found_error")
        assert any("NONEXISTENT" in log.message for log in error_logs)
        
        # Verify context information was captured
        log = next((log for log in error_logs if "NONEXISTENT" in log.message), None)
        assert log is not None
        assert "material_id" in log.context
        assert log.context["material_id"] == "NONEXISTENT"
        assert "entity_type" in log.context
        assert log.context["entity_type"] == "Material"
    
    async def test_error_log_filtering(self, test_services):
        """Test error log filtering across controller and service layers."""
        monitor_service = test_services["monitor_service"]
        
        # Create errors from different components
        monitor_service.log_error("validation_error", "Error 1", "component_a")
        monitor_service.log_error("not_found_error", "Error 2", "component_b")
        monitor_service.log_error("validation_error", "Error 3", "component_a")
        
        # Test filtering by component
        component_logs = monitor_service.get_error_logs(component="component_a")
        assert len(component_logs) == 2
        assert all(log.component == "component_a" for log in component_logs)
        
        # Test filtering by error type
        type_logs = monitor_service.get_error_logs(error_type="validation_error")
        assert len(type_logs) == 2
        assert all(log.error_type == "validation_error" for log in type_logs)
        
        # Test combined filtering
        combined_logs = monitor_service.get_error_logs(
            error_type="validation_error", 
            component="component_a"
        )
        assert len(combined_logs) == 2
        assert all(log.error_type == "validation_error" and log.component == "component_a" 
                 for log in combined_logs)
    
    async def test_metrics_collection_and_retrieval(self, test_services):
        """Test metrics collection and retrieval integration."""
        monitor_service = test_services["monitor_service"]
        
        # Collect metrics
        metrics1 = monitor_service.collect_current_metrics()
        
        # Wait a bit to ensure timestamps are different
        await asyncio.sleep(0.1)
        
        # Collect more metrics
        metrics2 = monitor_service.collect_current_metrics()
        
        # Get all metrics
        all_metrics = monitor_service.get_metrics()
        
        # Should have at least 2 metrics entries
        assert len(all_metrics) >= 2
        
        # Get metrics summary
        summary = monitor_service.get_metrics_summary()
        
        # Verify summary contains expected sections
        assert "count" in summary
        assert summary["count"] >= 2
        assert "averages" in summary
        assert "maximums" in summary
        
        # Verify time-based filtering
        # Since we just collected metrics, they should all be within the last hour
        recent_metrics = monitor_service.get_metrics(hours=1)
        assert len(recent_metrics) >= 2
