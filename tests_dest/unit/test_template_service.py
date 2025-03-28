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
        # Add project root to path
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        logging.warning("Could not find import_helper.py. Using fallback configuration.")
except Exception as e:
    logging.warning(f"Failed to import import_helper: {{e}}. Using fallback configuration.")
    # Add project root to path
    current_file = Path(__file__).resolve()
    test_dir = current_file.parent.parent
    project_root = test_dir.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

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

# tests-dest/unit/test_template_service.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, Response
from services.template_service import TemplateService
from services.url_service import url_service
from models.material import Material, MaterialType, UnitOfMeasure, MaterialStatus
from datetime import datetime

class TestTemplateService:
    def setup_method(self):
        """Set up test environment before each test"""
        # Create a mocked Jinja2Templates instance
        self.templates_patcher = patch('services.template_service.Jinja2Templates')
        self.mock_jinja = self.templates_patcher.start()
        
        # Create a mock for globals that we can inspect
        self.mock_globals = {}
        
        # Set up the mock environment with the globals
        self.mock_env = MagicMock()
        self.mock_env.globals = self.mock_globals
        
        # Set up the mock templates with the mock environment
        self.mock_templates = MagicMock()
        self.mock_templates.env = self.mock_env
        
        # Configure the mock TemplateResponse to return a proper Response object
        mock_response = HTMLResponse(content="<html>Test</html>")
        self.mock_templates.TemplateResponse.return_value = mock_response
        
        self.mock_jinja.return_value = self.mock_templates
        
        # Create the TemplateService
        self.template_service = TemplateService()
        
        # Verify Jinja2Templates was called with the correct directory
        self.mock_jinja.assert_called_once_with(directory="templates")
    
    def teardown_method(self):
        """Clean up after each test"""
        self.templates_patcher.stop()
    
    def test_url_for_registered_in_globals(self):
        """Test that url_for is registered in the Jinja2 globals"""
        # Check that url_for was added to the environment globals
        assert "url_for" in self.mock_globals
        # Verify it points to our method
        assert self.mock_globals["url_for"] == self.template_service.url_for
    
    def test_url_for_method_calls_url_service(self):
        """Test that url_for method calls the url_service"""
        # Mock the url_service.get_url_for_route method
        with patch('services.template_service.url_service.get_url_for_route') as mock_get_url:
            mock_get_url.return_value = "/test/123"
            
            # Test with kwargs
            result = self.template_service.url_for("test_route", id=123)
            mock_get_url.assert_called_with("test_route", {"id": 123}, None)
            assert result == "/test/123"
            
            # Test with dict params
            result = self.template_service.url_for("test_route", params={"id": 123})
            mock_get_url.assert_called_with("test_route", {"id": 123}, None)
            assert result == "/test/123"
            
            # Test with no params
            result = self.template_service.url_for("test_route")
            mock_get_url.assert_called_with("test_route", None, None)
            assert result == "/test/123"
    
    @pytest.mark.asyncio
    async def test_render_template_returns_html_response(self):
        """Test that render_template always returns HTMLResponse"""
        # Create a mock request
        mock_request = AsyncMock(spec=Request)
        
        # Test with HTMLResponse from Jinja
        html_response = HTMLResponse(content="<html>Test</html>")
        self.mock_templates.TemplateResponse.return_value = html_response
        
        result = self.template_service.render_template(mock_request, "test.html", {})
        assert isinstance(result, HTMLResponse)
        assert result.body == b"<html>Test</html>"
        
        # Test with non-HTMLResponse from Jinja
        plain_response = Response(content="Test", media_type="text/plain")
        self.mock_templates.TemplateResponse.return_value = plain_response
        
        result = self.template_service.render_template(mock_request, "test.html", {})
        assert isinstance(result, HTMLResponse)
        # The content type should be preserved from the original response
        assert result.headers["content-type"] == "text/plain; charset=utf-8"
    
    @pytest.mark.asyncio
    async def test_render_template_error_handling(self):
        """Test template rendering error handling"""
        mock_request = AsyncMock(spec=Request)
        
        # Test with invalid template name
        self.mock_templates.TemplateResponse.side_effect = Exception("Template not found")
        
        with pytest.raises(Exception) as exc_info:
            self.template_service.render_template(mock_request, "nonexistent.html", {})
        assert "Template not found" in str(exc_info.value)
    
    # Tests for material templates
    
    @pytest.mark.asyncio
    async def test_material_list_template_rendering(self):
        """Test rendering the material list template"""
        # Create a mock request
        mock_request = AsyncMock(spec=Request)
        
        # Create sample materials
        materials = [
            Material(
                material_number="MAT12345",
                name="Test Material 1",
                description="Test Description 1",
                type=MaterialType.RAW,
                base_unit=UnitOfMeasure.EACH,
                status=MaterialStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            Material(
                material_number="MAT67890",
                name="Test Material 2",
                description="Test Description 2",
                type=MaterialType.FINISHED,
                base_unit=UnitOfMeasure.KILOGRAM,
                status=MaterialStatus.INACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        # Create context
        context = {
            "materials": materials,
            "count": len(materials),
            "filters": {
                "search": None,
                "type": None,
                "status": None
            },
            "filter_options": {
                "types": [t.value for t in MaterialType],
                "statuses": [s.value for s in MaterialStatus]
            },
            "title": "Materials"
        }
        
        # Configure mock response
        mock_response = HTMLResponse(content="<html>Material List</html>")
        self.mock_templates.TemplateResponse.return_value = mock_response
        
        # Call render_template
        response = self.template_service.render_template(mock_request, "material/list.html", context)
        
        # Verify response type and content
        assert isinstance(response, HTMLResponse)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        
        # Verify template was called with correct arguments
        self.mock_templates.TemplateResponse.assert_called_once()
        args, kwargs = self.mock_templates.TemplateResponse.call_args
        
        # Check template name
        assert args[0] == "material/list.html"
        
        # Verify context
        context_arg = args[1]
        assert "request" in context_arg
        assert context_arg["request"] == mock_request
        assert "materials" in context_arg
        assert "count" in context_arg
        assert "filters" in context_arg
        assert "filter_options" in context_arg
        assert "title" in context_arg
        
        # Check materials are passed correctly
        assert len(context_arg["materials"]) == 2
        assert context_arg["materials"][0].material_number == "MAT12345"
        assert context_arg["materials"][1].material_number == "MAT67890"
    
    @pytest.mark.asyncio
    async def test_material_detail_template_rendering(self):
        """Test rendering the material detail template"""
        # Create a mock request
        mock_request = AsyncMock(spec=Request)
        
        # Create a sample material
        material = Material(
            material_number="MAT12345",
            name="Test Material",
            description="Test Description",
            type=MaterialType.RAW,
            base_unit=UnitOfMeasure.EACH,
            status=MaterialStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            weight=10.5,
            volume=5.2
        )
        
        # Create related documents
        related_documents = {
            "requisitions": [],
            "orders": []
        }
        
        # Create context
        context = {
            "material": material,
            "related_documents": related_documents,
            "title": f"Material: {material.name}"
        }
        
        # Configure mock response
        mock_response = HTMLResponse(content="<html>Material Detail</html>")
        self.mock_templates.TemplateResponse.return_value = mock_response
        
        # Call render_template
        response = self.template_service.render_template(mock_request, "material/detail.html", context)
        
        # Verify response type and content
        assert isinstance(response, HTMLResponse)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        
        # Verify template was called with correct arguments
        self.mock_templates.TemplateResponse.assert_called_once()
        args, kwargs = self.mock_templates.TemplateResponse.call_args
        
        # Check template name
        assert args[0] == "material/detail.html"
        
        # Verify context
        context_arg = args[1]
        assert "request" in context_arg
        assert context_arg["request"] == mock_request
        assert "material" in context_arg
        assert "related_documents" in context_arg
        assert "title" in context_arg
        
        # Check material data
        assert context_arg["material"] == material
        assert context_arg["material"].material_number == "MAT12345"
        assert context_arg["material"].weight == 10.5
        assert context_arg["material"].volume == 5.2
    
    def test_material_create_template_rendering(self):
        """Test rendering the material create template"""
        # Create a mock request
        mock_request = MagicMock()
        
        # Create context
        context = {
            "title": "Create Material",
            "form_action": url_service.get_url_for_route("material_create"),
            "form_method": "POST",
            "options": {
                "types": [t.value for t in MaterialType],
                "units": [u.value for u in UnitOfMeasure],
                "statuses": [s.value for s in MaterialStatus]
            }
        }
        
        # Call render_template
        self.template_service.render_template(mock_request, "material/create.html", context)
        
        # Verify Jinja2Templates.TemplateResponse was called
        self.mock_templates.TemplateResponse.assert_called_once()
        
        # Check template name
        args, kwargs = self.mock_templates.TemplateResponse.call_args
        assert args[0] == "material/create.html"
        
        # Verify context
        context_arg = args[1]
        assert "request" in context_arg
        assert "title" in context_arg
        assert "form_action" in context_arg
        assert "form_method" in context_arg
        assert "options" in context_arg
        
        # Check options are passed correctly
        assert "types" in context_arg["options"]
        assert "units" in context_arg["options"]
        assert "statuses" in context_arg["options"]
        assert len(context_arg["options"]["types"]) == len(MaterialType)
        assert len(context_arg["options"]["units"]) == len(UnitOfMeasure)
        assert len(context_arg["options"]["statuses"]) == len(MaterialStatus)
    
    def test_material_update_template_rendering(self):
        """Test rendering the material update template"""
        # Create a mock request
        mock_request = MagicMock()
        
        # Create a sample material
        material = Material(
            material_number="MAT12345",
            name="Test Material",
            description="Test Description",
            type=MaterialType.RAW,
            base_unit=UnitOfMeasure.EACH,
            status=MaterialStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Create context
        context = {
            "title": f"Edit Material: {material.name}",
            "material": material,
            "form_action": url_service.get_url_for_route("material_update", {"material_id": material.material_number}),
            "form_method": "POST",
            "options": {
                "types": [t.value for t in MaterialType],
                "units": [u.value for u in UnitOfMeasure],
                "statuses": [s.value for s in MaterialStatus]
            }
        }
        
        # Call render_template
        self.template_service.render_template(mock_request, "material/create.html", context)
        
        # Verify Jinja2Templates.TemplateResponse was called
        self.mock_templates.TemplateResponse.assert_called_once()
        
        # Check template name
        args, kwargs = self.mock_templates.TemplateResponse.call_args
        assert args[0] == "material/create.html"
        
        # Verify context
        context_arg = args[1]
        assert "request" in context_arg
        assert "title" in context_arg
        assert "material" in context_arg
        assert "form_action" in context_arg
        assert "form_method" in context_arg
        assert "options" in context_arg
        
        # Check material is passed correctly
        assert context_arg["material"].material_number == "MAT12345"
        assert context_arg["material"].name == "Test Material"
        
        # Check form action is correct
        assert "MAT12345/edit" in context_arg["form_action"]
    
    def test_template_with_validation_errors(self):
        """Test template rendering with validation errors"""
        # Create a mock request
        mock_request = MagicMock()
        
        # Create context with validation errors
        context = {
            "title": "Create Material",
            "form_action": url_service.get_url_for_route("material_create"),
            "form_method": "POST",
            "options": {
                "types": [t.value for t in MaterialType],
                "units": [u.value for u in UnitOfMeasure],
                "statuses": [s.value for s in MaterialStatus]
            },
            "errors": {
                "name": "Name is required",
                "type": "Invalid material type"
            },
            "form_data": {
                "description": "Test Description",
                "base_unit": UnitOfMeasure.EACH.value
            }
        }
        
        # Call render_template
        self.template_service.render_template(mock_request, "material/create.html", context)
        
        # Verify Jinja2Templates.TemplateResponse was called
        self.mock_templates.TemplateResponse.assert_called_once()
        
        # Check template name
        args, kwargs = self.mock_templates.TemplateResponse.call_args
        assert args[0] == "material/create.html"
        
        # Verify context
        context_arg = args[1]
        assert "errors" in context_arg
        assert "form_data" in context_arg
        
        # Check errors are passed correctly
        assert "name" in context_arg["errors"]
        assert "type" in context_arg["errors"]
        assert context_arg["errors"]["name"] == "Name is required"
        
        # Check form data is passed correctly
        assert "description" in context_arg["form_data"]
        assert "base_unit" in context_arg["form_data"]
        assert context_arg["form_data"]["description"] == "Test Description"
        assert context_arg["form_data"]["base_unit"] == UnitOfMeasure.EACH.value
