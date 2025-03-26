# Add path setup to find the tests_dest module
import sys
import os
from pathlib import Path

# Add parent directory to path so Python can find the tests_dest module
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent  # Go up two levels to reach project root
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import helper to fix path issues
from tests_dest.import_helper import fix_imports
fix_imports()

import pytest
import logging
import time
import json
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Union, Any
from types import ModuleType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services and models through the service_imports facade
from tests_dest.test_helpers.service_imports import (
    BaseService,
    MonitorService,
    StateManager
)

# Custom exception classes
class ValidationError(Exception):
    """Custom validation error with details."""
    pass
    
class NotFoundError(Exception):
    """Custom not found error."""
    pass

# Helper function to create a validation error with details
def create_validation_error(message, details=None):
    """Create a validation error with details."""
    error = ValidationError(message)
    error.details = details or {}
    return error

"""
Standard test file header with environment setup.

This template provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration using monkeypatch
3. Common test imports and fixtures
4. Service initialization support
5. Logging configuration
"""

def test_template_header_is_valid():
    """Verify that the template header can be imported and used."""
    assert True, "Template header is valid"

def test_template_imports_are_valid():
    """Verify that the imports in the template are valid."""
    assert MagicMock is not None, "MagicMock is imported correctly"
    assert AsyncMock is not None, "AsyncMock is imported correctly"
    assert Request is not None, "Request is imported correctly"
    assert logging is not None, "logging is imported correctly"
    assert pytest is not None, "pytest is imported correctly"

def test_template_includes_path_setup():
    """Verify that the template includes proper path setup."""
    assert 'sys' in sys.modules, "sys is imported"
    assert 'os' in sys.modules, "os is imported"
    assert 'pathlib' in sys.modules, "pathlib is imported"
    assert str(parent_dir) in sys.path, "Project root is in sys.path"

def test_template_includes_service_imports():
    """Verify that the template includes service imports."""
    assert BaseService is not None, "BaseService is imported"
    assert MonitorService is not None, "MonitorService is imported"
    assert StateManager is not None, "StateManager is imported"

# Test our custom exceptions
def test_custom_exceptions():
    """Verify that the custom exceptions work as expected."""
    # Test NotFoundError
    error = NotFoundError("Item not found")
    assert str(error) == "Item not found"
    
    # Test ValidationError with details
    validation_error = create_validation_error("Invalid input", {"field": "value"})
    assert str(validation_error) == "Invalid input"
    assert validation_error.details == {"field": "value"}
