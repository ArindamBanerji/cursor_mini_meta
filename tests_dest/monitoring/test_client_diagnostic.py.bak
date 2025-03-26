"""
Diagnostic test for TestClient behavior with request.client.host

This file contains tests to diagnose issues with the TestClient and request.client.host
attribute that's causing failures in the monitor controller tests.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import logging
import json
from unittest.mock import MagicMock, patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.testclient import TestClient as StarletteTestClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_client_diagnostic")

# Create a simple test app
app = FastAPI()

@app.get("/client-info")
async def client_info(request: Request):
    """Return information about the request.client attribute"""
    client_data = {
        "has_client": hasattr(request, "client"),
        "client_type": str(type(request.client)) if hasattr(request, "client") else None,
        "client_value": str(request.client) if hasattr(request, "client") else None,
        "has_host": hasattr(request.client, "host") if hasattr(request, "client") else False,
        "host_value": request.client.host if hasattr(request, "client") and hasattr(request.client, "host") else None,
        "client_attrs": str(dir(request.client)) if hasattr(request, "client") else None,
    }
    return client_data

@app.get("/safe-client-info")
async def safe_client_info(request: Request):
    """Return information about the request.client attribute using safe access"""
    client_host = "unknown"
    try:
        if hasattr(request, "client") and request.client is not None:
            if hasattr(request.client, "host"):
                client_host = request.client.host
    except Exception as e:
        client_host = f"Error: {str(e)}"
    
    return {"client_host": client_host}

def test_standard_testclient():
    """Test the standard TestClient behavior with request.client"""
    logger.info("Testing standard TestClient behavior")
    
    # Create a test client
    client = TestClient(app)
    
    # Make a request to get client info
    response = client.get("/client-info")
    assert response.status_code == 200
    
    # Log the response
    client_data = response.json()
    logger.info(f"Client data: {json.dumps(client_data, indent=2)}")
    
    # Check if client and host attributes are present
    logger.info(f"Has client attribute: {client_data['has_client']}")
    logger.info(f"Client type: {client_data['client_type']}")
    logger.info(f"Client value: {client_data['client_value']}")
    logger.info(f"Has host attribute: {client_data['has_host']}")
    logger.info(f"Host value: {client_data['host_value']}")
    logger.info(f"Client attrs: {client_data['client_attrs']}")
    
    # Test the safe access endpoint
    response = client.get("/safe-client-info")
    assert response.status_code == 200
    logger.info(f"Safe client host: {response.json()['client_host']}")

def test_starlette_testclient():
    """Test the Starlette TestClient behavior with request.client"""
    logger.info("Testing Starlette TestClient behavior")
    
    # Create a test client
    client = StarletteTestClient(app)
    
    # Make a request to get client info
    response = client.get("/client-info")
    assert response.status_code == 200
    
    # Log the response
    client_data = response.json()
    logger.info(f"Client data: {json.dumps(client_data, indent=2)}")
    
    # Test the safe access endpoint
    response = client.get("/safe-client-info")
    assert response.status_code == 200
    logger.info(f"Safe client host: {response.json()['client_host']}")

def test_testclient_with_custom_client():
    """Test the TestClient behavior with a custom client address"""
    logger.info("Testing TestClient with custom client address")
    
    # Create a test client with base_url parameter
    client = TestClient(app, base_url="http://localhost:8000")
    
    # Make a request to get client info
    response = client.get("/client-info")
    assert response.status_code == 200
    
    # Log the response
    client_data = response.json()
    logger.info(f"Client data with custom address: {json.dumps(client_data, indent=2)}")
    
    # Test the safe access endpoint
    response = client.get("/safe-client-info")
    assert response.status_code == 200
    logger.info(f"Safe client host with custom address: {response.json()['client_host']}")

def test_testclient_with_patched_scope():
    """Test the TestClient behavior with a patched scope to include client info"""
    logger.info("Testing TestClient with patched scope")
    
    # Create a test client
    client = TestClient(app)
    
    # Define a patch for the TestClient's request method
    original_request = client.request
    
    def patched_request(method, url, **kwargs):
        # Call the original request method
        response = original_request(method, url, **kwargs)
        return response
    
    # Apply the patch
    with patch.object(client, 'request', side_effect=patched_request):
        # Make a request to get client info
        response = client.get("/client-info")
        assert response.status_code == 200
        
        # Log the response
        client_data = response.json()
        logger.info(f"Client data with patched scope: {json.dumps(client_data, indent=2)}")

def test_with_environment_variable():
    """Test behavior with PYTEST_CURRENT_TEST environment variable set"""
    logger.info("Testing with PYTEST_CURRENT_TEST environment variable")
    
    # Set the environment variable
    os.environ["PYTEST_CURRENT_TEST"] = "test_with_environment_variable"
    
    try:
        # Create a test client
        client = TestClient(app)
        
        # Make a request to get client info
        response = client.get("/client-info")
        assert response.status_code == 200
        
        # Log the response
        client_data = response.json()
        logger.info(f"Client data with env var: {json.dumps(client_data, indent=2)}")
        
        # Test the safe access endpoint
        response = client.get("/safe-client-info")
        assert response.status_code == 200
        logger.info(f"Safe client host with env var: {response.json()['client_host']}")
    finally:
        # Clean up the environment variable
        if "PYTEST_CURRENT_TEST" in os.environ:
            del os.environ["PYTEST_CURRENT_TEST"]

def test_with_mocked_request():
    """Test behavior with a mocked Request object"""
    logger.info("Testing with a mocked Request object")
    
    # Create a mock request
    mock_request = MagicMock(spec=Request)
    mock_request.client = MagicMock()
    mock_request.client.host = "127.0.0.1"
    
    # Check the mock request attributes
    logger.info(f"Mock request has client: {hasattr(mock_request, 'client')}")
    logger.info(f"Mock request client has host: {hasattr(mock_request.client, 'host')}")
    logger.info(f"Mock request client host value: {mock_request.client.host}")
    
    # Test with None client
    mock_request.client = None
    logger.info(f"Mock request with None client has client: {hasattr(mock_request, 'client')}")
    try:
        logger.info(f"Accessing host on None client: {mock_request.client.host}")
    except AttributeError as e:
        logger.info(f"Expected error accessing host on None client: {str(e)}")

if __name__ == "__main__":
    print("\n=== Running TestClient Diagnostic Tests ===\n")
    test_standard_testclient()
    print("\n---\n")
    test_starlette_testclient()
    print("\n---\n")
    test_testclient_with_custom_client()
    print("\n---\n")
    test_testclient_with_patched_scope()
    print("\n---\n")
    test_with_environment_variable()
    print("\n---\n")
    test_with_mocked_request()
    print("\n=== Diagnostic Tests Complete ===\n") 