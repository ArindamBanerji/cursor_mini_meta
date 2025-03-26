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

"""
Diagnostic tests for environment setup.

This file tests our environment setup functionality to ensure:
1. Project root is correctly detected
2. Python path is properly configured
3. Environment variables are set and cleaned up
4. Async context maintains environment
"""

import pytest
import logging
import time
import json
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse

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
    BaseDataModel
)

# Custom exception classes
class ValidationError(Exception):
    """Custom validation error."""
    pass
        
class NotFoundError(Exception):
    """Custom not found error."""
    pass

# Helper to create a validation error with details
def create_validation_error(message, details=None):
    error = ValidationError(message)
    error.details = details or {}
    return error

# Test environment setup functions
def setup_test_paths():
    """Set up test paths for diagnostics."""
    current_dir = Path(__file__).resolve().parent
    test_dir = current_dir.parent  # tests_dest directory
    project_dir = test_dir.parent   # project root
    
    return {
        "current": str(current_dir),
        "test_dir": str(test_dir),
        "project_dir": str(project_dir),
        "in_path": str(project_dir) in sys.path
    }

def setup_test_env_vars(monkeypatch=None):
    """Set up test environment variables."""
    env_vars = {
        "TEST_MODE": "diagnostic",
        "TEST_SETUP": "true",
        "TEST_TIME": str(time.time())
    }
    
    # Set environment variables
    if monkeypatch:
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)
    else:
        for key, value in env_vars.items():
            os.environ[key] = value
    
    # Return the variables we set
    return env_vars

def test_env_setup_basic():
    """Test basic environment setup."""
    # Check paths
    paths = setup_test_paths()
    assert paths["in_path"], "Project root should be in sys.path"
    
    # Check environment variables
    env_vars = setup_test_env_vars()
    for key, value in env_vars.items():
        assert os.environ.get(key) == value, f"Environment variable {key} not set correctly"
    
    logger.info("Basic environment setup test passed")

def test_env_setup_with_monkeypatch(monkeypatch):
    """Test environment setup with pytest's monkeypatch."""
    # Use monkeypatch to set environment variables
    env_vars = setup_test_env_vars(monkeypatch)
    
    # Check that variables were set
    for key, value in env_vars.items():
        assert os.environ.get(key) == value, f"Environment variable {key} not set correctly with monkeypatch"
    
    # Check that monkeypatch will clean up automatically
    logger.info("Environment setup with monkeypatch test passed")

@pytest.mark.asyncio
async def test_env_setup_async():
    """Test environment setup in async context."""
    # Set up environment
    env_vars = setup_test_env_vars()
    
    # Define an async function that checks environment
    async def check_env():
        for key, value in env_vars.items():
            assert os.environ.get(key) == value, f"Environment variable {key} not preserved in async context"
        return True
    
    # Run the check
    result = await check_env()
    assert result, "Async environment check failed"
    
    logger.info("Async environment setup test passed")

@pytest.fixture
def setup_test_env_fixture(monkeypatch):
    """Fixture that sets up test environment variables."""
    # Set up paths and environment variables
    paths = setup_test_paths()
    env_vars = setup_test_env_vars(monkeypatch)
    
    # Return a dictionary with the setup information
    return {
        "paths": paths,
        "env_vars": env_vars
    }

def test_env_setup_with_fixture(setup_test_env_fixture):
    """Test environment setup using a pytest fixture."""
    # Check paths
    paths = setup_test_env_fixture["paths"]
    assert paths["in_path"], "Project root should be in sys.path"
    
    # Check environment variables
    env_vars = setup_test_env_fixture["env_vars"]
    for key, value in env_vars.items():
        assert os.environ.get(key) == value, f"Environment variable {key} not set correctly with fixture"
    
    logger.info("Environment setup with fixture test passed")

def test_env_cleanup(monkeypatch):
    """Test that environment variables are cleaned up properly."""
    # Generate a unique key that's unlikely to be in the environment
    import uuid
    test_key = f"TEST_CLEANUP_{uuid.uuid4().hex}"
    test_value = "test_value"
    
    # Set the environment variable with monkeypatch
    monkeypatch.setenv(test_key, test_value)
    
    # Verify it was set
    assert os.environ.get(test_key) == test_value, f"Environment variable {test_key} not set correctly"
    
    # Note: When this test function exits, monkeypatch should clean up the variable
    # We can't verify this cleanup here since it happens after the test completes
    
    logger.info(f"Set test environment variable {test_key} that should be cleaned up")

# Use BaseDataModel from service_imports instead of defining our own
def test_service_model_imports():
    """Test that service and model imports work correctly."""
    # Test BaseService
    assert BaseService is not None, "BaseService import failed"
    
    # Test MonitorService
    assert MonitorService is not None, "MonitorService import failed"
    
    # Test BaseDataModel
    assert BaseDataModel is not None, "BaseDataModel import failed"
    
    # Create a test model and check basic functionality
    model = BaseDataModel()
    
    # Verify we can get a dictionary representation
    model_dict = model.dict()
    assert isinstance(model_dict, dict), "Model dict() method should return a dictionary"
    
    # Check that we have expected fields like id, created_at, updated_at
    assert "id" in model_dict, "Model dict should contain id field"
    assert "created_at" in model_dict, "Model dict should contain created_at field"
    assert "updated_at" in model_dict, "Model dict should contain updated_at field"
    
    logger.info("Service and model imports test passed")
    return model_dict

def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Running test_env_diagnostic.py ===")
    test_env_setup_basic()
    test_service_model_imports()
    print("All tests passed!")

if __name__ == "__main__":
    run_simple_test()
