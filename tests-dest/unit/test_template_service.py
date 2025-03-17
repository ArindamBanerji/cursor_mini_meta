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

# tests-dest/unit/test_template_service.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from unittest.mock import patch, MagicMock
import pytest
from fastapi import Request
from fastapi.templating import Jinja2Templates
from services.template_service import TemplateService
from services.url_service import url_service
from models.material import Material, MaterialType, UnitOfMeasure, MaterialStatus
from datetime import datetime

class TestTemplateService:
    def setup_method(self):
        # Create a mocked Jinja2Templates instance
        with patch('services.template_service.Jinja2Templates') as mock_jinja:
            # Create a mock for globals that we can inspect later
            self.mock_globals = {}
            
            # Set up the mock environment with the globals
            self.mock_env = MagicMock()
            self.mock_env.globals = self.mock_globals
            
            # Set up the mock templates with the mock environment
            self.mock_templates = MagicMock()
            self.mock_templates.env = self.mock_env
            mock_jinja.return_value = self.mock_templates
            
            # Create the TemplateService
            self.template_service = TemplateService()
            
            # Verify Jinja2Templates was called with the correct directory
            mock_jinja.assert_called_once_with(directory="templates")
    
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
            
            # Call url_for
            result = self.template_service.url_for("test_route", id=123)
            
            # Verify url_service was called
            mock_get_url.assert_called_once_with("test_route", {"id": 123})
            assert result == "/test/123"
    
    def test_render_template_calls_jinja_templates(self):
        """Test that render_template calls the Jinja2Templates instance"""
        # Create a mock request
        mock_request = MagicMock()
        
        # Create a mock context
        context = {"test_key": "test_value"}
        
        # Call render_template
        self.template_service.render_template(mock_request, "test.html", context)
        
        # Verify Jinja2Templates.TemplateResponse was called
        self.mock_templates.TemplateResponse.assert_called_once()
        
        # Get the call arguments
        args, kwargs = self.mock_templates.TemplateResponse.call_args
        
        # Verify template name
        assert args[0] == "test.html"
        
        # Verify context - it should include the request and our context
        context_arg = args[1]
        assert "request" in context_arg
        assert context_arg["request"] == mock_request
        assert "test_key" in context_arg
        assert context_arg["test_key"] == "test_value"
    
    # Tests for material templates
    
    def test_material_list_template_rendering(self):
        """Test rendering the material list template"""
        # Create a mock request
        mock_request = MagicMock()
        
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
        
        # Call render_template
        self.template_service.render_template(mock_request, "material/list.html", context)
        
        # Verify Jinja2Templates.TemplateResponse was called
        self.mock_templates.TemplateResponse.assert_called_once()
        
        # Check template name
        args, kwargs = self.mock_templates.TemplateResponse.call_args
        assert args[0] == "material/list.html"
        
        # Verify context
        context_arg = args[1]
        assert "request" in context_arg
        assert "materials" in context_arg
        assert "count" in context_arg
        assert "filters" in context_arg
        assert "filter_options" in context_arg
        assert "title" in context_arg
        
        # Check materials are passed correctly
        assert len(context_arg["materials"]) == 2
        assert context_arg["materials"][0].material_number == "MAT12345"
        assert context_arg["materials"][1].material_number == "MAT67890"
    
    def test_material_detail_template_rendering(self):
        """Test rendering the material detail template"""
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
        
        # Call render_template
        self.template_service.render_template(mock_request, "material/detail.html", context)
        
        # Verify Jinja2Templates.TemplateResponse was called
        self.mock_templates.TemplateResponse.assert_called_once()
        
        # Check template name
        args, kwargs = self.mock_templates.TemplateResponse.call_args
        assert args[0] == "material/detail.html"
        
        # Verify context
        context_arg = args[1]
        assert "request" in context_arg
        assert "material" in context_arg
        assert "related_documents" in context_arg
        assert "title" in context_arg
        
        # Check material is passed correctly
        assert context_arg["material"].material_number == "MAT12345"
        assert context_arg["material"].name == "Test Material"
        assert context_arg["material"].type == MaterialType.RAW
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
