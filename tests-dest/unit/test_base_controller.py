# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Critical imports that must be preserved
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, ModuleType

"""Standard test file imports and setup.

This snippet is automatically added to test files by SnippetForTests.py.
It provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration
3. Common test imports and fixtures
4. Service initialization support
5. Logging configuration
6. Test environment variable management
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
    from test_import_helper import setup_test_paths
    setup_test_paths()
    logger.info("Successfully initialized test paths from test_import_helper")
except ImportError as e:
    # Fall back if test_import_helper is not available
    if str(test_dir.parent) not in sys.path:
        sys.path.insert(0, str(test_dir.parent))
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root) if project_root else "")
    logger.warning(f"Failed to import test_import_helper: {e}. Using fallback configuration.")

# Set up test environment variables
def setup_test_env() -> None:
    """Set up test environment variables."""
    try:
        os.environ.setdefault("PYTEST_CURRENT_TEST", "True")
        logger.info("Test environment variables initialized")
    except Exception as e:
        logger.error(f"Error setting up test environment: {e}")

def teardown_test_env() -> None:
    """Clean up test environment variables."""
    try:
        if "PYTEST_CURRENT_TEST" in os.environ:
            del os.environ["PYTEST_CURRENT_TEST"]
        logger.info("Test environment variables cleaned up")
    except KeyError:
        logger.warning("PYTEST_CURRENT_TEST was already removed")
    except Exception as e:
        logger.error(f"Error cleaning up test environment: {e}")

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

# Register setup/teardown hooks
def setup_module(module: ModuleType) -> None:
    """Set up the test module.
    
    Args:
        module: The test module being set up
    """
    logger.info("Setting up test module")
    setup_test_env()

def teardown_module(module: ModuleType) -> None:
    """Tear down the test module.
    
    Args:
        module: The test module being torn down
    """
    logger.info("Tearing down test module")
    teardown_test_env()
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

# tests-dest/unit/test_base_controller.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from controllers import BaseController
from utils.error_utils import ValidationError, BadRequestError

# Test models - renamed to avoid pytest collection warnings

@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment for each test."""
    logger.info("Setting up test environment")
    os.environ["PYTEST_CURRENT_TEST"] = "True"
    yield
    logger.info("Tearing down test environment")
    if "PYTEST_CURRENT_TEST" in os.environ:
        del os.environ["PYTEST_CURRENT_TEST"]

class RequestTestModel(BaseModel):
    name: str
    age: int = Field(gt=0)

class QueryTestModel(BaseModel):
    search: str
    limit: int = 10
    offset: int = 0

class TestBaseController:
    def setup_method(self):
        """Setup for each test"""
        self.controller = BaseController()
    
    @pytest.mark.asyncio
    async def test_parse_json_body_valid(self):
        """Test parsing valid JSON body"""
        # Create a mock request with valid JSON
        mock_request = MagicMock(spec=Request)
        mock_request.json.return_value = {"name": "Test User", "age": 30}
        
        # Parse the body
        result = await BaseController.parse_json_body(mock_request, RequestTestModel)
        
        # Check the result
        assert isinstance(result, RequestTestModel)
        assert result.name == "Test User"
        assert result.age == 30
    
    @pytest.mark.asyncio
    async def test_parse_json_body_invalid(self):
        """Test parsing invalid JSON body"""
        # Create a mock request with invalid JSON (negative age)
        mock_request = MagicMock(spec=Request)
        mock_request.json.return_value = {"name": "Test User", "age": -5}
        
        # Parsing should raise ValidationError
        with pytest.raises(ValidationError) as excinfo:
            await BaseController.parse_json_body(mock_request, RequestTestModel)
        
        # Check the error details
        assert "Invalid request data" in str(excinfo.value)
        assert "validation_errors" in excinfo.value.details
    
    @pytest.mark.asyncio
    async def test_parse_json_body_missing_field(self):
        """Test parsing JSON with missing required field"""
        # Create a mock request with missing required field (name)
        mock_request = MagicMock(spec=Request)
        mock_request.json.return_value = {"age": 30}
        
        # Parsing should raise ValidationError
        with pytest.raises(ValidationError) as excinfo:
            await BaseController.parse_json_body(mock_request, RequestTestModel)
        
        # Check the error details
        assert "Invalid request data" in str(excinfo.value)
        assert "validation_errors" in excinfo.value.details
    
    @pytest.mark.asyncio
    async def test_parse_json_body_invalid_json(self):
        """Test parsing invalid JSON format"""
        # Create a mock request that raises an exception when json() is called
        mock_request = MagicMock(spec=Request)
        mock_request.json.side_effect = Exception("Invalid JSON")
        
        # Parsing should raise BadRequestError
        with pytest.raises(BadRequestError) as excinfo:
            await BaseController.parse_json_body(mock_request, RequestTestModel)
        
        # Check the error message
        assert "Error parsing request body" in str(excinfo.value)
        assert "Invalid JSON" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_parse_query_params_valid(self):
        """Test parsing valid query parameters"""
        # Create a mock request with valid query parameters
        mock_request = MagicMock(spec=Request)
        mock_request.query_params = {"search": "test", "limit": "20", "offset": "5"}
        
        # Parse the query params
        result = await BaseController.parse_query_params(mock_request, QueryTestModel)
        
        # Check the result
        assert isinstance(result, QueryTestModel)
        assert result.search == "test"
        assert result.limit == 20
        assert result.offset == 5
    
    @pytest.mark.asyncio
    async def test_parse_query_params_invalid(self):
        """Test parsing invalid query parameters"""
        # Create a mock request with invalid query parameters (negative limit)
        mock_request = MagicMock(spec=Request)
        mock_request.query_params = {"search": "test", "limit": "-20"}
        
        # Parsing should not raise an error (Pydantic will use the default value for limit)
        result = await BaseController.parse_query_params(mock_request, QueryTestModel)
        assert result.limit == -20  # Pydantic model doesn't validate limit
    
    @pytest.mark.asyncio
    async def test_parse_query_params_missing_required(self):
        """Test parsing query parameters with missing required field"""
        # Create a mock request with missing required field (search)
        mock_request = MagicMock(spec=Request)
        mock_request.query_params = {"limit": "20", "offset": "5"}
        
        # Parsing should raise ValidationError
        with pytest.raises(ValidationError) as excinfo:
            await BaseController.parse_query_params(mock_request, QueryTestModel)
        
        # Check the error details
        assert "Invalid query parameters" in str(excinfo.value)
        assert "validation_errors" in excinfo.value.details
    
    def test_create_success_response(self):
        """Test creating a success response"""
        # Create a success response
        response = BaseController.create_success_response(
            data={"id": 1, "name": "Test"},
            message="Operation successful",
            status_code=201
        )
        
        # Check the response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 201
        
        # Check the response content
        content = response.body.decode()
        assert "success" in content
        assert "Operation successful" in content
        assert "Test" in content
    
    def test_create_success_response_defaults(self):
        """Test creating a success response with default values"""
        # Create a success response with defaults
        response = BaseController.create_success_response()
        
        # Check the response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200
        
        # Check the response content
        content = response.body.decode()
        assert "success" in content
        assert "Success" in content
    
    def test_redirect_to_route(self):
        """Test redirecting to a route"""
        # Mock the URL service
        with patch('controllers.url_service.get_url_for_route') as mock_get_url:
            mock_get_url.return_value = "/dashboard"
            
            # Create a redirect response
            response = BaseController.redirect_to_route("dashboard")
            
            # Check the response
            assert isinstance(response, RedirectResponse)
            assert response.status_code == 303  # Default to 303 See Other
            assert response.headers["location"] == "/dashboard"
            
            # Verify URL service was called with correct parameters
            mock_get_url.assert_called_once_with("dashboard", None)
    
    def test_redirect_to_route_with_params(self):
        """Test redirecting to a route with parameters"""
        # Mock the URL service
        with patch('controllers.url_service.get_url_for_route') as mock_get_url:
            mock_get_url.return_value = "/item/123"
            
            # Create a redirect response with parameters
            response = BaseController.redirect_to_route(
                "item_detail", 
                params={"id": 123}
            )
            
            # Check the response
            assert isinstance(response, RedirectResponse)
            assert response.status_code == 303  # Default to 303 See Other
            assert response.headers["location"] == "/item/123"
            
            # Verify URL service was called with correct parameters
            mock_get_url.assert_called_once_with("item_detail", {"id": 123})
    
    def test_redirect_to_route_custom_status_code(self):
        """Test redirecting to a route with a custom status code"""
        # Mock the URL service
        with patch('controllers.url_service.get_url_for_route') as mock_get_url:
            mock_get_url.return_value = "/dashboard"
            
            # Create a redirect response with a custom status code
            response = BaseController.redirect_to_route(
                "dashboard", 
                status_code=status.HTTP_302_FOUND
            )
            
            # Check the response
            assert isinstance(response, RedirectResponse)
            assert response.status_code == status.HTTP_302_FOUND
            assert response.headers["location"] == "/dashboard"
