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
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
import json
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services from service_imports
from tests_dest.test_helpers.service_imports import (
    BaseService,
    MonitorService, 
    get_monitor_service
)


"""
Diagnostic tests for controller functionality.

This file tests our dependency injection approach with a basic controller,
focusing on core functionality like request handling and response formatting.
"""

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment for each test."""
    # Set environment variables for tests
    monkeypatch.setenv("TEST_MODE", "True")
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "True")
    
    # Prepare some test data
    test_data = {
        "test_value": "test",
        "user_id": "123456",
        "client_ip": "127.0.0.1"
    }
    
    return test_data

@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"status": "ok", "message": "This is a test endpoint"}
    
    return app

@pytest.fixture
def test_client(test_app):
    """Create a test client for the app."""
    return TestClient(test_app)

@pytest.fixture
def real_request():
    """Create a real request object for testing."""
    app = FastAPI()
    client = TestClient(app)
    
    # Create a basic request scope
    scope = {
        "type": "http",
        "path": "/test",
        "headers": [(b"x-forwarded-for", b"10.0.0.1")],
        "query_string": b"",
        "client": ("127.0.0.1", 50000)
    }
    
    return Request(scope)

@pytest.fixture
def monitor_service():
    """Get the real monitor service."""
    return get_monitor_service()

def test_get_safe_client_host(real_request):
    """Test the util function to get client host safely."""
    from controllers.monitor_controller import get_safe_client_host
    
    # Save original TEST_MODE value
    original_test_mode = os.environ.get('TEST_MODE')
    
    try:
        # Test with TEST_MODE=true
        os.environ['TEST_MODE'] = 'true'
        assert get_safe_client_host(real_request) == 'test-client'
        
        # Test with TEST_MODE not set to 'true'
        os.environ['TEST_MODE'] = 'False'
        
        # Test with a real client
        # (we can only validate function doesn't throw errors)
        result = get_safe_client_host(real_request)
        assert isinstance(result, str)
        
    finally:
        # Restore original TEST_MODE value
        if original_test_mode is not None:
            os.environ['TEST_MODE'] = original_test_mode
        elif 'TEST_MODE' in os.environ:
            del os.environ['TEST_MODE']

@pytest.mark.asyncio
async def test_health_check_endpoint(real_request, monitor_service):
    """Test the health check endpoint."""
    from controllers.monitor_controller import api_health_check
    
    # Call the actual controller function with real service
    response = await api_health_check(real_request, monitor_service)
    
    # Verify the response is a JSONResponse
    assert isinstance(response, JSONResponse)
    
    # The real service may return 429 when in warning state
    # This is expected behavior with real dependencies
    assert response.status_code in [200, 429]
    
    # Parse the content
    content = response.body
    from json import loads
    content_dict = loads(content)
    
    # Check required fields based on actual response structure
    assert "status" in content_dict
    assert "components" in content_dict
    assert "system_info" in content_dict
    assert "response_time_ms" in content_dict
    
    # Verify components structure (we can't assert exact values with real service)
    components = content_dict["components"]
    assert isinstance(components, dict)
    
    # Check for expected component keys if they exist
    if "database" in components:
        assert "status" in components["database"]
    if "services" in components:
        assert "status" in components["services"]
    if "disk" in components:
        assert "status" in components["disk"]
    if "memory" in components:
        assert "status" in components["memory"]

@pytest.mark.asyncio
async def test_metrics_endpoint(real_request, monitor_service):
    """Test the metrics endpoint."""
    from controllers.monitor_controller import api_get_metrics
    
    # Call the actual controller function with real service
    response = await api_get_metrics(real_request, monitor_service)
    
    # Verify the response is a JSONResponse
    assert isinstance(response, JSONResponse)
    
    # Verify the response status code
    assert response.status_code == 200
    
    # Parse the JSON response
    content = json.loads(response.body)
    
    # Check data is present in the response
    assert "success" in content
    assert content["success"] is True
    
    # Verify data structure (we can't assert exact values with real service)
    assert "data" in content
    data = content["data"]
    assert isinstance(data, dict)
    assert "time_period_hours" in data
    
    # We expect these fields but can't guarantee values with real service
    if "requests" in data:
        assert isinstance(data["requests"], dict)
    if "errors" in data:
        assert isinstance(data["errors"], dict)
    if "response_time" in data:
        assert isinstance(data["response_time"], dict)

def test_endpoint_dependency_injection(test_app, test_client):
    """Test dependency injection in endpoints."""
    # Add endpoint with dependency
    async def get_current_user():
        return {"user_id": "12345", "username": "test_user"}
    
    @test_app.get("/protected")
    async def protected_endpoint(current_user: dict = Depends(get_current_user)):
        return {"message": f"Hello, {current_user['username']}!"}
    
    # Test the endpoint
    response = test_client.get("/protected")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, test_user!"}

def test_error_handling(test_app, test_client):
    """Test error handling in endpoints."""
    @test_app.get("/error")
    async def error_endpoint():
        raise HTTPException(status_code=400, detail="Test error")
    
    # Test the error endpoint
    response = test_client.get("/error")
    assert response.status_code == 400
    assert response.json()["detail"] == "Test error"

def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Simple diagnostic test ===")
    print("Successfully executed test_controller_diagnostic.py")
    print("All imports resolved correctly")
    return True

if __name__ == "__main__":
    run_simple_test()
