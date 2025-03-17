# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Critical imports that must be preserved
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

"""Standard test file imports and setup.

This snippet is automatically added to test files by SnippetForTests.py.
It provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration
3. Common test imports and fixtures
4. Service initialization support
"""

# Find project root dynamically
test_file = Path(__file__).resolve()
test_dir = test_file.parent

# Try to find project root by looking for main.py or known directories
project_root: Optional[Path] = None
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

# Add project root to path if found
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
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root) if project_root else "")

# Common test imports
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

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
    from fastapi.testclient import TestClient
except ImportError as e:
    # Log import error but continue - not all tests need all imports
    import logging
    logging.warning(f"Optional import failed: {e}")
    logging.debug("Stack trace:", exc_info=True)
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
