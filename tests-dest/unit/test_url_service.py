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

# tests-dest/unit/test_url_service.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from meta_routes import RouteDefinition, HttpMethod, ALL_ROUTES
from services.url_service import URLService
from models.base_model import BaseModel
from utils.error_utils import ValidationError

# Create test routes for isolated testing
TEST_ROUTES = [
    RouteDefinition(
        name="test_simple",
        path="/test",
        methods=[HttpMethod.GET],
        controller="controllers.test_controller.test_action",
        template=None
    ),
    RouteDefinition(
        name="test_with_param",
        path="/test/{id}",
        methods=[HttpMethod.GET],
        controller="controllers.test_controller.test_with_param",
        template=None
    ),
    RouteDefinition(
        name="test_with_multiple_params",
        path="/test/{category}/{id}",
        methods=[HttpMethod.GET],
        controller="controllers.test_controller.test_with_multiple_params",
        template=None
    )
]

# Test data
TEST_URL = "https://example.com/api/v1/materials"
TEST_PARAMS = {"id": "123", "type": "raw"}
TEST_HEADERS = {"Authorization": "Bearer token123"}

class TestURLService:
    def setup_method(self):
        # Create a URLService with our test routes
        self.url_service = URLService()
        # Override the route_map with our test routes
        self.url_service.route_map = {route.name: route for route in TEST_ROUTES}
    
    def test_get_url_for_simple_route(self):
        """Test generating a URL for a simple route with no parameters"""
        url = self.url_service.get_url_for_route("test_simple")
        assert url == "/test"
    
    def test_get_url_with_param(self):
        """Test generating a URL with a parameter"""
        url = self.url_service.get_url_for_route("test_with_param", {"id": 123})
        assert url == "/test/123"
    
    def test_get_url_with_multiple_params(self):
        """Test generating a URL with multiple parameters"""
        url = self.url_service.get_url_for_route("test_with_multiple_params", {
            "category": "books",
            "id": 456
        })
        assert url == "/test/books/456"
    
    def test_nonexistent_route(self):
        """Test that a ValueError is raised for a non-existent route"""
        with pytest.raises(ValueError) as excinfo:
            self.url_service.get_url_for_route("nonexistent_route")
        assert "not found in route registry" in str(excinfo.value)
    
    def test_param_substitution_type_handling(self):
        """Test parameter values of different types"""
        # Test with integer
        url = self.url_service.get_url_for_route("test_with_param", {"id": 123})
        assert url == "/test/123"
        
        # Test with string
        url = self.url_service.get_url_for_route("test_with_param", {"id": "abc"})
        assert url == "/test/abc"
        
        # Test with boolean
        url = self.url_service.get_url_for_route("test_with_param", {"id": True})
        assert url == "/test/True"

    def test_real_route_compatibility(self):
        """Test that our service works with the actual routes in ALL_ROUTES"""
        # Create a new service with the actual routes
        real_service = URLService()
        
        # Test that we can generate a URL for the dashboard route
        url = real_service.get_url_for_route("dashboard")
        assert url == "/dashboard"
        
        # Test that we can generate a URL for the root route
        url = real_service.get_url_for_route("root")
        assert url == "/"
    
    # New tests for material routes
    def test_material_list_url(self):
        """Test generating URL for material list route"""
        real_service = URLService()
        url = real_service.get_url_for_route("material_list")
        assert url == "/materials"
    
    def test_material_detail_url(self):
        """Test generating URL for material detail route with parameter"""
        real_service = URLService()
        url = real_service.get_url_for_route("material_detail", {"material_id": "MAT12345"})
        assert url == "/materials/MAT12345"
    
    def test_material_create_form_url(self):
        """Test generating URL for material create form route"""
        real_service = URLService()
        url = real_service.get_url_for_route("material_create_form")
        assert url == "/materials/create"
    
    def test_material_update_form_url(self):
        """Test generating URL for material update form route with parameter"""
        real_service = URLService()
        url = real_service.get_url_for_route("material_update_form", {"material_id": "MAT12345"})
        assert url == "/materials/MAT12345/edit"
    
    def test_material_deprecate_url(self):
        """Test generating URL for material deprecate route with parameter"""
        real_service = URLService()
        url = real_service.get_url_for_route("material_deprecate", {"material_id": "MAT12345"})
        assert url == "/materials/MAT12345/deprecate"
    
    # Tests for material API routes
    def test_api_material_list_url(self):
        """Test generating URL for material list API route"""
        real_service = URLService()
        url = real_service.get_url_for_route("api_material_list")
        assert url == "/api/v1/materials"
    
    def test_api_material_detail_url(self):
        """Test generating URL for material detail API route with parameter"""
        real_service = URLService()
        url = real_service.get_url_for_route("api_material_detail", {"material_id": "MAT12345"})
        assert url == "/api/v1/materials/MAT12345"
    
    def test_api_material_create_url(self):
        """Test generating URL for material create API route"""
        real_service = URLService()
        url = real_service.get_url_for_route("api_material_create")
        assert url == "/api/v1/materials"
    
    def test_api_material_update_url(self):
        """Test generating URL for material update API route with parameter"""
        real_service = URLService()
        url = real_service.get_url_for_route("api_material_update", {"material_id": "MAT12345"})
        assert url == "/api/v1/materials/MAT12345"
    
    def test_api_material_deprecate_url(self):
        """Test generating URL for material deprecate API route with parameter"""
        real_service = URLService()
        url = real_service.get_url_for_route("api_material_deprecate", {"material_id": "MAT12345"})
        assert url == "/api/v1/materials/MAT12345/deprecate"
    
    # Tests for monitor API routes
    def test_api_monitor_health_url(self):
        """Test generating URL for monitor health API route"""
        real_service = URLService()
        url = real_service.get_url_for_route("api_monitor_health")
        assert url == "/api/v1/monitor/health"
    
    def test_api_monitor_metrics_url(self):
        """Test generating URL for monitor metrics API route"""
        real_service = URLService()
        url = real_service.get_url_for_route("api_monitor_metrics")
        assert url == "/api/v1/monitor/metrics"
    
    def test_api_monitor_errors_url(self):
        """Test generating URL for monitor errors API route"""
        real_service = URLService()
        url = real_service.get_url_for_route("api_monitor_errors")
        assert url == "/api/v1/monitor/errors"
    
    def test_api_monitor_collect_metrics_url(self):
        """Test generating URL for monitor collect metrics API route"""
        real_service = URLService()
        url = real_service.get_url_for_route("api_monitor_collect_metrics")
        assert url == "/api/v1/monitor/metrics/collect"
    
    # Additional tests for path parameter handling
    def test_material_route_missing_parameter(self):
        """Test error handling when required parameter is missing"""
        real_service = URLService()
        with pytest.raises(ValueError) as excinfo:
            real_service.get_url_for_route("material_detail")
        assert "Missing required parameters" in str(excinfo.value)
    
    def test_material_route_invalid_parameter(self):
        """Test with invalid parameter name"""
        real_service = URLService()
        with pytest.raises(ValueError) as excinfo:
            real_service.get_url_for_route("material_detail", {"invalid_param": "MAT12345"})
        assert "Missing required parameters" in str(excinfo.value)
    
    def test_material_route_extra_parameters(self):
        """Test with extra parameters (should be ignored)"""
        real_service = URLService()
        url = real_service.get_url_for_route("material_detail", {
            "material_id": "MAT12345",
            "extra_param": "something"
        })
        assert url == "/materials/MAT12345"
    
    def test_material_route_complex_parameter(self):
        """Test with complex parameter values"""
        real_service = URLService()
        
        # Test with parameter containing special characters (should be handled by string conversion)
        url = real_service.get_url_for_route("material_detail", {
            "material_id": "MAT@#$%"
        })
        assert url == "/materials/MAT@#$%"
        
        # Test with numeric parameter
        url = real_service.get_url_for_route("material_detail", {
            "material_id": 12345
        })
        assert url == "/materials/12345"
