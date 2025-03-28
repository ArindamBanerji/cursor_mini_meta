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
from fastapi import Request, Response, FastAPI, HTTPException, Depends

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
Diagnostic tests for controller functionality.

This file tests our dependency unwrapping approach with a basic controller,
focusing on core functionality like request handling and response formatting.
"""

# Import from test helpers
from tests_dest.api.test_helpers import unwrap_dependencies, create_controller_test

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
def mock_request():
    """Create a mock request object for testing."""
    request = MagicMock(spec=Request)
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    request.headers = {"X-Forwarded-For": "10.0.0.1"}
    request.url = MagicMock()
    request.url.path = "/test"
    return request

def test_get_safe_client_host(mock_request):
    """Test the util function to get client host safely."""
    from controllers.monitor_controller import get_safe_client_host
    
    # Save original TEST_MODE value
    original_test_mode = os.environ.get('TEST_MODE')
    
    try:
        # Test with TEST_MODE=true
        os.environ['TEST_MODE'] = 'true'
        assert get_safe_client_host(mock_request) == 'test-client'
        
        # Test with TEST_MODE not set to 'true'
        os.environ['TEST_MODE'] = 'False'
        
        # Test with client.host
        mock_request.client.host = "127.0.0.1"
        assert get_safe_client_host(mock_request) == "127.0.0.1"
        
        # Test with client=None
        mock_request.client = None
        assert get_safe_client_host(mock_request) == "unknown"
        
        # Test with client but no host
        mock_request.client = MagicMock()
        delattr(mock_request.client, 'host')
        assert get_safe_client_host(mock_request) == "unknown"
    finally:
        # Restore original TEST_MODE value
        if original_test_mode is not None:
            os.environ['TEST_MODE'] = original_test_mode
        elif 'TEST_MODE' in os.environ:
            del os.environ['TEST_MODE']

@pytest.mark.asyncio
async def test_health_check_endpoint(mock_request):
    """Test the health check endpoint."""
    from controllers.monitor_controller import api_health_check
    
    # Create a mock monitor service that simulates the real implementation
    mock_monitor = MagicMock()
    health_data = {
        "status": "ok",
        "uptime": "10m 30s",
        "start_time": "2023-01-01T00:00:00Z",
        "components": {
            "monitor": {
                "status": "ok",
                "last_update": "2023-01-01T00:10:00Z"
            },
            "api": {
                "status": "ok",
                "version": "1.0.0"
            }
        }
    }
    mock_monitor.check_system_health = MagicMock(return_value=health_data)
    
    # Call the actual controller function from the source code
    response = await api_health_check(mock_request, mock_monitor)
    
    # Verify the response is a JSONResponse
    from fastapi.responses import JSONResponse
    assert isinstance(response, JSONResponse)
    
    # Verify the response content
    assert response.status_code == 200
    content = response.body
    from json import loads
    content_dict = loads(content)
    assert content_dict["status"] == "ok"
    assert "uptime" in content_dict
    assert "start_time" in content_dict
    assert "components" in content_dict
    
    # Verify components
    components = content_dict["components"]
    assert "monitor" in components
    assert "api" in components

@pytest.mark.asyncio
async def test_metrics_endpoint(mock_request):
    """Test the metrics endpoint."""
    from controllers.monitor_controller import api_get_metrics
    from controllers import BaseController
    
    # Setup query parameters
    class MockParamsModel:
        hours = 24
    
    # Patch only the parse_query_params which is not what we're testing
    with patch.object(BaseController, 'parse_query_params', return_value=MockParamsModel()):
        # Create a mock monitor service
        mock_monitor = MagicMock()
        metrics_data = {
            "count": 100,
            "time_period_hours": 24,
            "requests": {
                "total": 1000,
                "per_minute": 10,
                "per_hour": 600
            },
            "errors": {
                "total": 10,
                "rate": 0.01
            },
            "response_time": {
                "avg_ms": 150,
                "p95_ms": 200,
                "p99_ms": 300
            }
        }
        mock_monitor.get_metrics_summary = MagicMock(return_value=metrics_data)
        
        # Call the actual controller function from the source code
        response = await api_get_metrics(mock_request, mock_monitor)
        
        # Verify the response is a JSONResponse
        from fastapi.responses import JSONResponse
        assert isinstance(response, JSONResponse)
        
        # Verify the response status code
        assert response.status_code == 200
        
        # Parse the JSON response
        from json import loads
        content = loads(response.body)
        
        # Check data is present in the response
        assert "success" in content
        assert content["success"] is True
        
        # The controller should pass along the data from the service
        assert "data" in content
        data = content["data"]
        assert data["count"] == 100
        assert data["time_period_hours"] == 24
        assert "requests" in data
        assert "errors" in data
        assert "response_time" in data

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
    
    # Test the endpoint
    response = test_client.get("/error")
    assert response.status_code == 400
    assert response.json() == {"detail": "Test error"}

def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Simple diagnostic test ===")
    print("Successfully executed test_controller_diagnostic.py")
    print("All imports resolved correctly")
    return True

if __name__ == "__main__":
    run_simple_test() 