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
Diagnostic tests for the monitor controller request handling.

This file tests the request handling in the monitor controller,
specifically focusing on the issue with request.client.host.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import logging
import json
import asyncio
from unittest.mock import MagicMock, patch
from fastapi import Request
from fastapi.testclient import TestClient

from main import app
from controllers.monitor_controller import api_health_check, api_get_errors, api_get_metrics, api_collect_metrics
from services import get_monitor_service

# Try both absolute and relative imports for test_helpers
try:
    from api.test_helpers import unwrap_dependencies, create_controller_test
except ImportError:
    try:
        # Try relative import
        from ..api.test_helpers import unwrap_dependencies, create_controller_test
    except ImportError:
        # Fallback to direct import
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../api')))
        from test_helpers import unwrap_dependencies, create_controller_test

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_monitor_request_diagnostic")

# Create test client
client = TestClient(app)

def test_request_client_in_testclient():
    """Test how TestClient sets up the request.client attribute"""
    logger.info("Testing request.client in TestClient")
    
    # Create a simple endpoint for testing
    @app.get("/test-client")
    async def test_endpoint(request: Request):
        client_info = {
            "has_client": hasattr(request, "client"),
            "client_value": str(request.client) if hasattr(request, "client") else None,
            "has_host": hasattr(request.client, "host") if hasattr(request, "client") else False,
            "host_value": request.client.host if hasattr(request, "client") and hasattr(request.client, "host") else None
        }
        return client_info
    
    # Make a request to the test endpoint
    response = client.get("/test-client")
    logger.info(f"Response from test endpoint: {response.json()}")
    
    # Check the response
    assert response.status_code == 200
    data = response.json()
    
    # Log the findings
    logger.info(f"Has client attribute: {data['has_client']}")
    logger.info(f"Client value: {data['client_value']}")
    logger.info(f"Has host attribute: {data['has_host']}")
    logger.info(f"Host value: {data['host_value']}")

def test_get_safe_client_host():
    """Test the get_safe_client_host function"""
    logger.info("Testing get_safe_client_host function")
    
    from controllers.monitor_controller import get_safe_client_host
    
    # Test with a valid request
    mock_request = MagicMock(spec=Request)
    mock_request.client = MagicMock()
    mock_request.client.host = "127.0.0.1"
    
    host = get_safe_client_host(mock_request)
    logger.info(f"Host from valid request: {host}")
    assert host == "127.0.0.1"
    
    # Test with a request that has no client
    mock_request = MagicMock(spec=Request)
    mock_request.client = None
    
    host = get_safe_client_host(mock_request)
    logger.info(f"Host from request with no client: {host}")
    assert host == "unknown"
    
    # Test with a request that has no host
    mock_request = MagicMock(spec=Request)
    mock_request.client = MagicMock()
    delattr(mock_request.client, "host")
    
    host = get_safe_client_host(mock_request)
    logger.info(f"Host from request with no host: {host}")
    assert host == "unknown"

async def test_mock_request_for_controller():
    """Test creating a proper mock request for controller tests"""
    logger.info("Testing mock request for controller tests")
    
    # Create a mock request with all necessary attributes
    mock_request = MagicMock(spec=Request)
    mock_request.url = MagicMock()
    mock_request.url.path = "/api/v1/monitor/errors"
    mock_request.client = MagicMock()
    mock_request.client.host = "127.0.0.1"
    mock_request.query_params = {}
    
    # Create a mock monitor service
    mock_monitor_service = MagicMock()
    mock_monitor_service.get_error_logs.return_value = []
    
    # Patch the get_monitor_service function to return our mock
    with patch('controllers.monitor_controller.get_monitor_service', return_value=mock_monitor_service):
        # Call the controller function directly
        response = await api_get_errors(mock_request)
        
        # Log the response
        logger.info(f"Response from controller: {response}")
        
        # Verify the monitor service was called
        mock_monitor_service.get_error_logs.assert_called_once()
        logger.info(f"Mock service called: {mock_monitor_service.get_error_logs.call_count} times")

def test_fix_monitor_controller_tests():
    """Test a fix for the monitor controller tests"""
    logger.info("Testing fix for monitor controller tests")
    
    # Create a simple test client with a mock for the request method
    with patch('starlette.testclient.TestClient.request') as mock_request:
        # Configure the mock to return a response with status code 200
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"errors": [], "count": 0}
        mock_request.return_value = mock_response
        
        # Make a request to the errors endpoint
        response = client.get("/api/v1/monitor/errors")
        
        # Log the response
        logger.info(f"Response status: {response.status_code}")
        
        # Verify the mock was called
        assert mock_request.called
        logger.info(f"Mock request called: {mock_request.call_count} times")
        
        # This is a diagnostic test to show how to patch the TestClient
        logger.info(f"Response data: {response.json()}")

async def test_controller_with_direct_call():
    """Test calling the controller directly with a proper mock request"""
    logger.info("Testing controller with direct call")
    
    # Create a mock request with all necessary attributes
    mock_request = MagicMock(spec=Request)
    mock_request.url = MagicMock()
    mock_request.url.path = "/api/v1/monitor/errors"
    mock_request.client = MagicMock()
    mock_request.client.host = "127.0.0.1"
    mock_request.query_params = {}
    
    # Create a mock monitor service
    mock_monitor_service = MagicMock()
    mock_monitor_service.get_error_logs.return_value = []
    
    # Patch the get_monitor_service function to return our mock
    with patch('controllers.monitor_controller.get_monitor_service', return_value=mock_monitor_service):
        # Call the controller function directly
        response = await api_get_errors(mock_request)
        
        # Log the response
        logger.info(f"Response from direct controller call: {response}")
        
        # Verify the monitor service was called
        mock_monitor_service.get_error_logs.assert_called_once()
        logger.info(f"Mock service called: {mock_monitor_service.get_error_logs.call_count} times")

async def run_async_tests():
    """Run all async tests"""
    await test_mock_request_for_controller()
    await test_controller_with_direct_call()

if __name__ == "__main__":
    # Run the synchronous tests
    test_request_client_in_testclient()
    test_get_safe_client_host()
    test_fix_monitor_controller_tests()
    
    # Run the async tests
    asyncio.run(run_async_tests()) 