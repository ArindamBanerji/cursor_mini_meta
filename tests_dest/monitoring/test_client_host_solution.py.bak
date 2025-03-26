"""
Test script to verify our solution for the request.client.host issue.

This script tests both the patched TestClient and the pytest fixture approach
to ensure they properly handle the request.client.host issue.
"""

import os
import sys
import logging
import pytest
from pathlib import Path

# Add project root and tests-dest to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# FastAPI imports
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_client_host_solution")

# Create a simple FastAPI application for testing
app = FastAPI()

@app.get("/direct-access")
async def direct_access(request: Request):
    """Endpoint that directly accesses request.client.host"""
    try:
        client_host = request.client.host
        return {"client_host": client_host, "method": "direct_access"}
    except Exception as e:
        return {"error": str(e), "method": "direct_access"}

@app.get("/request-info")
async def request_info(request: Request):
    """Endpoint that returns information about the request object"""
    info = {
        "has_client": hasattr(request, "client"),
        "client_type": str(type(request.client)) if hasattr(request, "client") else None,
        "client_is_none": request.client is None if hasattr(request, "client") else None,
        "has_host": hasattr(request.client, "host") if hasattr(request, "client") and request.client is not None else False,
        "client_dict": str(vars(request.client)) if hasattr(request, "client") and request.client is not None else None,
    }
    return info

# Create a custom TestClient that patches Request.client
class PatchedRequestClient(TestClient):
    """
    A TestClient that patches the Request.client property to ensure
    request.client.host is properly set during tests.
    """
    
    def __init__(self, app, client_host="test-client", **kwargs):
        """Initialize the patched test client."""
        super().__init__(app, **kwargs)
        self.client_host = client_host
        self.mock_client = MagicMock()
        self.mock_client.host = self.client_host
        
    def get(self, *args, **kwargs):
        """Override get method to patch Request.client during the request."""
        with patch('fastapi.Request.client', self.mock_client):
            return super().get(*args, **kwargs)
    
    def post(self, *args, **kwargs):
        """Override post method to patch Request.client during the request."""
        with patch('fastapi.Request.client', self.mock_client):
            return super().post(*args, **kwargs)

def test_standard_client_fails():
    """Test that standard TestClient fails when accessing request.client.host"""
    logger.info("Testing standard TestClient")
    
    # Create a standard client
    client = TestClient(app)
    
    # Test direct access - should fail
    response = client.get("/direct-access")
    logger.info(f"Direct access response: {response.json()}")
    
    # Verify that it fails with the expected error
    assert "error" in response.json()
    assert "'NoneType' object has no attribute 'host'" in response.json()["error"]
    
    # Test request info
    response = client.get("/request-info")
    logger.info(f"Request info response: {response.json()}")
    
    # Verify that client is None
    assert response.json()["client_is_none"] is True

def test_patched_client_works():
    """Test that our patched client works when accessing request.client.host"""
    logger.info("Testing patched client")
    
    # Create a patched client
    client = PatchedRequestClient(app)
    
    # Test direct access - should work
    response = client.get("/direct-access")
    logger.info(f"Direct access response: {response.json()}")
    
    # Verify that it works
    assert "error" not in response.json()
    assert response.json()["client_host"] == "test-client"
    
    # Test request info
    response = client.get("/request-info")
    logger.info(f"Request info response: {response.json()}")
    
    # Verify that client is not None and has host attribute
    assert response.json()["client_is_none"] is False
    assert response.json()["has_host"] is True

def test_manual_patch_approach():
    """Test manually patching Request.client"""
    logger.info("Testing manual patch approach")
    
    # Create a mock client with host attribute
    mock_client = MagicMock()
    mock_client.host = "test-client"
    
    # Create a standard client
    client = TestClient(app)
    
    # Patch the Request.client property for specific requests
    with patch('fastapi.Request.client', mock_client):
        # Test direct access - should work
        response = client.get("/direct-access")
        logger.info(f"Direct access response: {response.json()}")
        
        # Verify that it works
        assert "error" not in response.json()
        assert response.json()["client_host"] == "test-client"
        
        # Test request info
        response = client.get("/request-info")
        logger.info(f"Request info response: {response.json()}")
        
        # Verify that client is not None and has host attribute
        assert response.json()["client_is_none"] is False
        assert response.json()["has_host"] is True

if __name__ == "__main__":
    # Run the tests manually
    logger.info("Running tests manually")
    
    # Test standard client
    test_standard_client_fails()
    
    # Test manual patch approach
    test_manual_patch_approach()
    
    # Test patched client
    test_patched_client_works()
    
    # Note: We can't test the fixture approach manually
    # because it requires pytest to run
    logger.info("All manual tests passed!")
    
    # Instruct how to run with pytest
    logger.info("To run with pytest, use: pytest -xvs test_client_host_solution.py") 