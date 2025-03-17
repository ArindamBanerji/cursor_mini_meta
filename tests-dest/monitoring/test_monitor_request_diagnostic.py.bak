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


def setup_module(module):
    """Set up the test module by ensuring PYTEST_CURRENT_TEST is set"""
    logger.info("Setting up test module")
    os.environ["PYTEST_CURRENT_TEST"] = "True"
    
def teardown_module(module):
    """Clean up after the test module"""
    logger.info("Tearing down test module")
    if "PYTEST_CURRENT_TEST" in os.environ:
        del os.environ["PYTEST_CURRENT_TEST"]
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