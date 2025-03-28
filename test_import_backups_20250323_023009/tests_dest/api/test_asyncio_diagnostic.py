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
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Optional imports - these might fail but won't break tests
try:
    from services.base_service import BaseService
    from services.monitor_service import MonitorService
    from models.base_model import BaseModel
except ImportError as e:
    logger.warning(f"Optional import failed: {e}")


"""
Diagnostic tests for asyncio functionality.

This file tests our async/await patterns and ensures proper handling
of asynchronous operations in the test environment.
"""

# Critical imports that must be preserved
import asyncio
from typing import Dict, List, Optional, Union, Any
from types import ModuleType
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Add the test helpers
from tests_dest.api.test_helpers import unwrap_dependencies

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up the test environment."""
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "True")
    monkeypatch.setenv("TEST_MODE", "True")
    monkeypatch.setenv("ASYNC_TEST", "True")
    
    # Clear any previous test data
    test_data = {}
    
    # Prepare some test values
    test_data["async_test_value"] = "This is an async test"
    test_data["response_delay"] = 0.1  # 100ms
    
    # Return the test data to the test function
    return test_data

async def async_function():
    """A simple async function for testing."""
    await asyncio.sleep(0.1)  # Simulate some async work
    return "async function result"

@pytest.mark.asyncio
async def test_async_function():
    """Test a simple async function."""
    result = await async_function()
    assert result == "async function result"

@pytest.mark.asyncio
async def test_async_with_mock():
    """Test async operations with a mock."""
    # Create an AsyncMock
    mock_async = AsyncMock()
    mock_async.return_value = "mocked async result"
    
    # Call the mock as an async function
    result = await mock_async()
    
    assert result == "mocked async result"
    mock_async.assert_called_once()

@pytest.fixture
def test_app():
    """Create a test FastAPI app."""
    app = FastAPI()
    
    @app.get("/async-test")
    async def test_endpoint():
        await asyncio.sleep(0.1)  # Simulate async work
        return {"message": "This is an async endpoint"}
    
    return app

@pytest.fixture
def test_client(test_app):
    """Create a test client for the app."""
    return TestClient(test_app)

@pytest.mark.asyncio
async def test_async_endpoint(test_client):
    """Test an async endpoint."""
    response = test_client.get("/async-test")
    assert response.status_code == 200
    assert response.json() == {"message": "This is an async endpoint"}

@pytest.mark.asyncio
async def test_async_request():
    """Test creating an async request."""
    # Create a mock request
    mock_request = AsyncMock(spec=Request)
    mock_request.url = MagicMock()
    mock_request.url.path = "/test-async"
    mock_request.query_params = {"param1": "value1"}
    
    # Use the mock request
    mock_request.json.return_value = {"data": "test data"}
    
    # Test async attribute access
    result = await mock_request.json()
    
    assert result == {"data": "test data"}
    assert mock_request.url.path == "/test-async"
    assert mock_request.query_params["param1"] == "value1"

@pytest.mark.asyncio
async def test_async_response():
    """Test creating an async response."""
    # Create a response
    response = JSONResponse(
        content={"message": "Async test completed"},
        status_code=200
    )
    
    # Verify response
    assert response.status_code == 200
    assert response.body == b'{"message":"Async test completed"}'
    
    # Test with different status code
    error_response = JSONResponse(
        content={"error": "Test error"},
        status_code=400
    )
    
    assert error_response.status_code == 400
    assert b"Test error" in error_response.body

def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Simple diagnostic test ===")
    print("Successfully executed test_asyncio_diagnostic.py")
    print("All imports resolved correctly")
    return True

if __name__ == "__main__":
    run_simple_test()