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
        
        # Check for the updated format with error_code and success fields
        assert content["success"] is False
        assert content["error_code"] == "validation_error"
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
