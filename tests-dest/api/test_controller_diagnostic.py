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

"""
Diagnostic tests for controller functionality.

This file tests our dependency unwrapping approach with a basic controller,
focusing on core functionality like request handling and response formatting.
"""

import os
import sys
import logging
from pathlib import Path
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from test_import_helper import setup_test_paths, setup_test_env_vars

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set up paths
project_root = setup_test_paths()

# Additional imports for controller testing
import json
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from controllers.monitor_controller import (
    api_health_check,
    api_get_metrics,
    get_safe_client_host
)
from services import get_monitor_service

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment for each test."""
    setup_test_env_vars(monkeypatch)
    logger.info("Test environment initialized")
    yield
    logger.info("Test environment cleaned up")

@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "Test endpoint"}
    
    return app

@pytest.fixture
def test_client(test_app):
    """Create a test client."""
    return TestClient(test_app)

@pytest.fixture
def mock_request():
    """Create a mock request object."""
    request = MagicMock(spec=Request)
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    request.query_params = {}
    return request

def test_get_safe_client_host(mock_request):
    """Test the get_safe_client_host function."""
    # Save original TEST_MODE value
    original_test_mode = os.environ.get('TEST_MODE')
    
    try:
        # Test with TEST_MODE=true (default in test environment)
        host = get_safe_client_host(mock_request)
        assert host == 'test-client'  # Should return test-client in test environment
        
        # Test with TEST_MODE unset
        if 'TEST_MODE' in os.environ:
            del os.environ['TEST_MODE']
        
        # With client.host properly set
        mock_request.client.host = "127.0.0.1"
        host = get_safe_client_host(mock_request)
        assert host == '127.0.0.1'  # Should return actual client host
        
        # Test with no client
        mock_request.client = None
        host = get_safe_client_host(mock_request)
        assert host == 'unknown'
    
    finally:
        # Restore original TEST_MODE value
        if original_test_mode is not None:
            os.environ['TEST_MODE'] = original_test_mode
        elif 'TEST_MODE' in os.environ:
            del os.environ['TEST_MODE']

@pytest.mark.asyncio
async def test_health_check_endpoint(mock_request):
    """Test the health check endpoint."""
    # Mock the monitor service with a proper dictionary return value
    mock_monitor = MagicMock()
    health_data = {
        "status": "healthy",
        "components": {
            "database": {
                "status": "healthy",
                "message": "Connected"
            },
            "api": {
                "status": "healthy",
                "message": "Running"
            }
        }
    }
    mock_monitor.check_system_health = MagicMock(return_value=health_data)
    
    # Test the endpoint
    response = await api_health_check(mock_request, mock_monitor)
    
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    data = json.loads(response.body)
    assert data["status"] == "healthy"
    assert "components" in data
    assert data["components"]["database"]["status"] == "healthy"
    assert data["components"]["api"]["status"] == "healthy"

@pytest.mark.asyncio
async def test_metrics_endpoint(mock_request):
    """Test the metrics endpoint."""
    # Test the endpoint
    response = await api_get_metrics(mock_request)
    
    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    data = json.loads(response.body)
    assert "data" in data
    assert "success" in data
    assert data["success"] is True
    assert "message" in data
    assert isinstance(data["data"], dict)
    assert "count" in data["data"]
    assert "time_period_hours" in data["data"]

def test_endpoint_dependency_injection(test_app, test_client):
    """Test dependency injection in endpoints."""
    # Define a test dependency
    async def get_current_user():
        return {"username": "testuser"}
    
    @test_app.get("/protected")
    async def protected_endpoint(current_user: dict = Depends(get_current_user)):
        return current_user
    
    # Test the endpoint
    response = test_client.get("/protected")
    assert response.status_code == 200
    assert response.json() == {"username": "testuser"}

def test_error_handling(test_app, test_client):
    """Test error handling in endpoints."""
    @test_app.get("/error")
    async def error_endpoint():
        raise HTTPException(status_code=400, detail="Test error")
    
    # Test the endpoint
    response = test_client.get("/error")
    assert response.status_code == 400
    assert response.json()["detail"] == "Test error"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 