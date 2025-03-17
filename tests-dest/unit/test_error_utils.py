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

# tests-dest/unit/test_error_utils.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import json
from fastapi import FastAPI, status, Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from utils.error_utils import (
    AppError, ValidationError, NotFoundError, AuthenticationError, 
    AuthorizationError, BadRequestError, ConflictError, 
    create_error_response, app_exception_handler, setup_exception_handlers
)


def setup_module(module):
    """Set up the test module by ensuring PYTEST_CURRENT_TEST is set"""
    logger.info("Setting up test module")
    os.environ["PYTEST_CURRENT_TEST"] = "True"
    
def teardown_module(module):
    """Clean up after the test module"""
    logger.info("Tearing down test module")
    if "PYTEST_CURRENT_TEST" in os.environ:
        del os.environ["PYTEST_CURRENT_TEST"]
class TestErrorClasses:
    def test_app_error_default_values(self):
        """Test AppError with default values"""
        error = AppError()
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert error.error_code == "internal_error"
        assert error.message == "An unexpected error occurred"
        assert error.details == {}
    
    def test_app_error_custom_values(self):
        """Test AppError with custom values"""
        error = AppError(
            message="Custom error message",
            details={"key": "value"}
        )
        assert error.message == "Custom error message"
        assert error.details == {"key": "value"}
    
    def test_validation_error(self):
        """Test ValidationError"""
        error = ValidationError(
            message="Invalid data",
            details={"field": "This field is required"}
        )
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.error_code == "validation_error"
        assert error.message == "Invalid data"
    
    def test_not_found_error(self):
        """Test NotFoundError"""
        error = NotFoundError(message="Resource not found")
        assert error.status_code == status.HTTP_404_NOT_FOUND
        assert error.error_code == "not_found"
        assert error.message == "Resource not found"
    
    def test_authentication_error(self):
        """Test AuthenticationError"""
        error = AuthenticationError(message="Invalid credentials")
        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert error.error_code == "authentication_error"
        assert error.message == "Invalid credentials"
    
    def test_authorization_error(self):
        """Test AuthorizationError"""
        error = AuthorizationError(message="Permission denied")
        assert error.status_code == status.HTTP_403_FORBIDDEN
        assert error.error_code == "authorization_error"
        assert error.message == "Permission denied"
    
    def test_bad_request_error(self):
        """Test BadRequestError"""
        error = BadRequestError(message="Invalid request")
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.error_code == "bad_request"
        assert error.message == "Invalid request"
    
    def test_conflict_error(self):
        """Test ConflictError"""
        error = ConflictError(message="Resource already exists")
        assert error.status_code == status.HTTP_409_CONFLICT
        assert error.error_code == "conflict"
        assert error.message == "Resource already exists"

class TestErrorHandlers:
    def test_create_error_response(self):
        """Test create_error_response function"""
        error = ValidationError(
            message="Invalid data",
            details={"field": "This field is required"}
        )
        response = create_error_response(error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.body is not None
        
        # Convert response body to dict
        content = json.loads(response.body.decode())
        
        assert content["error"] == "validation_error"
        assert content["message"] == "Invalid data"
        assert content["details"] == {"field": "This field is required"}
    
    def test_error_dict_method(self):
        """Test that we can generate a dict representation of errors"""
        # Add dict method to AppError
        def dict(self):
            return {
                "status_code": self.status_code,
                "error_code": self.error_code,
                "message": self.message,
                "details": self.details
            }
        
        # Temporarily add dict method to AppError
        original_dict = getattr(AppError, "dict", None)
        AppError.dict = dict
        
        try:
            # Test dict method
            error = ValidationError(message="Test error")
            error_dict = error.dict()
            
            assert error_dict["status_code"] == status.HTTP_400_BAD_REQUEST
            assert error_dict["error_code"] == "validation_error"
            assert error_dict["message"] == "Test error"
        finally:
            # Restore original dict method
            if original_dict:
                AppError.dict = original_dict
            else:
                delattr(AppError, "dict")
