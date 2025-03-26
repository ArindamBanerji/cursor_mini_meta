"""
Minimal reproduction script for request.client.host issue in FastAPI tests.

This script creates a simple FastAPI application with endpoints that access
request.client.host in different ways, then tests various approaches to fix
the issue in test environments.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# FastAPI imports
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.testclient import TestClient as StarletteTestClient
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("reproduce_client_host")

# Create a simple FastAPI application
app = FastAPI()

# Helper function similar to the one in monitor_controller.py
def get_safe_client_host(request: Request) -> str:
    """
    Safely get the client host from a request.
    
    Args:
        request: FastAPI request
        
    Returns:
        Client host string or 'unknown' if not available
    """
    try:
        # Check if request has client attribute and it's not None
        if hasattr(request, 'client') and request.client is not None:
            # Check if client has host attribute
            if hasattr(request.client, 'host'):
                return request.client.host
        return 'unknown'
    except Exception:
        return 'unknown'

# Enhanced version with environment variable check
def get_safe_client_host_enhanced(request: Request) -> str:
    """
    Enhanced version that checks for PYTEST_CURRENT_TEST environment variable.
    
    Args:
        request: FastAPI request
        
    Returns:
        Client host string, 'test-client' in test environments, or 'unknown' if not available
    """
    try:
        # In test environments, always return a test client host
        if 'PYTEST_CURRENT_TEST' in os.environ:
            return 'test-client'
            
        # Check if request has client attribute and it's not None
        if hasattr(request, 'client') and request.client is not None:
            # Check if client has host attribute
            if hasattr(request.client, 'host'):
                return request.client.host
        return 'unknown'
    except Exception:
        return 'unknown'

# Create endpoints that access request.client.host in different ways

@app.get("/direct-access")
async def direct_access(request: Request):
    """Endpoint that directly accesses request.client.host"""
    try:
        client_host = request.client.host
        return {"client_host": client_host, "method": "direct_access"}
    except Exception as e:
        return {"error": str(e), "method": "direct_access"}

@app.get("/safe-access")
async def safe_access(request: Request):
    """Endpoint that uses get_safe_client_host"""
    client_host = get_safe_client_host(request)
    return {"client_host": client_host, "method": "safe_access"}

@app.get("/enhanced-safe-access")
async def enhanced_safe_access(request: Request):
    """Endpoint that uses get_safe_client_host_enhanced"""
    client_host = get_safe_client_host_enhanced(request)
    return {"client_host": client_host, "method": "enhanced_safe_access"}

@app.get("/conditional-access")
async def conditional_access(request: Request):
    """Endpoint that uses conditional access"""
    if hasattr(request, 'client') and request.client is not None and hasattr(request.client, 'host'):
        client_host = request.client.host
    else:
        client_host = 'unknown'
    return {"client_host": client_host, "method": "conditional_access"}

@app.get("/request-info")
async def request_info(request: Request):
    """Endpoint that returns information about the request object"""
    info = {
        "has_client": hasattr(request, "client"),
        "client_type": str(type(request.client)) if hasattr(request, "client") else None,
        "client_is_none": request.client is None if hasattr(request, "client") else None,
        "has_host": hasattr(request.client, "host") if hasattr(request, "client") and request.client is not None else False,
        "client_dict": str(vars(request.client)) if hasattr(request, "client") and request.client is not None else None,
        "request_dict": str({k: str(v) for k, v in vars(request).items() if not k.startswith("_")})
    }
    return info

# Test different approaches to fix the issue

def test_standard_client():
    """Test with standard TestClient"""
    logger.info("Testing with standard TestClient")
    
    client = TestClient(app)
    
    # Test direct access
    response = client.get("/direct-access")
    logger.info(f"Direct access response: {response.json()}")
    
    # Test safe access
    response = client.get("/safe-access")
    logger.info(f"Safe access response: {response.json()}")
    
    # Test enhanced safe access
    response = client.get("/enhanced-safe-access")
    logger.info(f"Enhanced safe access response: {response.json()}")
    
    # Test conditional access
    response = client.get("/conditional-access")
    logger.info(f"Conditional access response: {response.json()}")
    
    # Test request info
    response = client.get("/request-info")
    logger.info(f"Request info response: {response.json()}")

def test_with_env_var():
    """Test with PYTEST_CURRENT_TEST environment variable set"""
    logger.info("Testing with PYTEST_CURRENT_TEST environment variable")
    
    # Set environment variable
    os.environ["PYTEST_CURRENT_TEST"] = "True"
    
    try:
        client = TestClient(app)
        
        # Test direct access
        response = client.get("/direct-access")
        logger.info(f"Direct access response: {response.json()}")
        
        # Test safe access
        response = client.get("/safe-access")
        logger.info(f"Safe access response: {response.json()}")
        
        # Test enhanced safe access
        response = client.get("/enhanced-safe-access")
        logger.info(f"Enhanced safe access response: {response.json()}")
        
        # Test conditional access
        response = client.get("/conditional-access")
        logger.info(f"Conditional access response: {response.json()}")
        
        # Test request info
        response = client.get("/request-info")
        logger.info(f"Request info response: {response.json()}")
    finally:
        # Clean up environment variable
        if "PYTEST_CURRENT_TEST" in os.environ:
            del os.environ["PYTEST_CURRENT_TEST"]

class PatchedTestClient(TestClient):
    """A patched version of TestClient that ensures client.host is set"""
    
    def request(self, *args, **kwargs):
        """Override request method to set client.host"""
        response = super().request(*args, **kwargs)
        return response
    
    def _build_scope(self, method, url, params=None):
        """Override _build_scope to ensure client is properly set in the scope"""
        scope = super()._build_scope(method, url, params)
        
        # Ensure client is set in the scope
        if "client" not in scope or scope["client"] is None:
            scope["client"] = ("test-client", 12345)
            logger.debug("Set client in scope")
            
        return scope

def test_patched_client():
    """Test with patched TestClient"""
    logger.info("Testing with patched TestClient")
    
    client = PatchedTestClient(app)
    
    # Test direct access
    response = client.get("/direct-access")
    logger.info(f"Direct access response: {response.json()}")
    
    # Test safe access
    response = client.get("/safe-access")
    logger.info(f"Safe access response: {response.json()}")
    
    # Test enhanced safe access
    response = client.get("/enhanced-safe-access")
    logger.info(f"Enhanced safe access response: {response.json()}")
    
    # Test conditional access
    response = client.get("/conditional-access")
    logger.info(f"Conditional access response: {response.json()}")
    
    # Test request info
    response = client.get("/request-info")
    logger.info(f"Request info response: {response.json()}")

def test_patched_function():
    """Test with patched get_safe_client_host function"""
    logger.info("Testing with patched get_safe_client_host function")
    
    # Define a patched version of get_safe_client_host
    def patched_get_safe_client_host(request):
        """Always return 'test-client'"""
        return 'test-client'
    
    # Patch the function
    with patch('__main__.get_safe_client_host', side_effect=patched_get_safe_client_host):
        client = TestClient(app)
        
        # Test direct access
        response = client.get("/direct-access")
        logger.info(f"Direct access response: {response.json()}")
        
        # Test safe access
        response = client.get("/safe-access")
        logger.info(f"Safe access response: {response.json()}")
        
        # Test enhanced safe access
        response = client.get("/enhanced-safe-access")
        logger.info(f"Enhanced safe access response: {response.json()}")
        
        # Test conditional access
        response = client.get("/conditional-access")
        logger.info(f"Conditional access response: {response.json()}")
        
        # Test request info
        response = client.get("/request-info")
        logger.info(f"Request info response: {response.json()}")

def test_patched_request():
    """Test with patched Request object"""
    logger.info("Testing with patched Request object")
    
    # Create a mock client with host attribute
    mock_client = MagicMock()
    mock_client.host = "test-client"
    
    # Patch the Request.client property
    with patch('fastapi.Request.client', mock_client):
        client = TestClient(app)
        
        # Test direct access
        response = client.get("/direct-access")
        logger.info(f"Direct access response: {response.json()}")
        
        # Test safe access
        response = client.get("/safe-access")
        logger.info(f"Safe access response: {response.json()}")
        
        # Test enhanced safe access
        response = client.get("/enhanced-safe-access")
        logger.info(f"Enhanced safe access response: {response.json()}")
        
        # Test conditional access
        response = client.get("/conditional-access")
        logger.info(f"Conditional access response: {response.json()}")
        
        # Test request info
        response = client.get("/request-info")
        logger.info(f"Request info response: {response.json()}")

def run_all_tests():
    """Run all tests and summarize results"""
    logger.info("Running all tests")
    
    # Run each test and catch any exceptions
    tests = [
        test_standard_client,
        test_with_env_var,
        test_patched_client,
        test_patched_function,
        test_patched_request
    ]
    
    results = {}
    
    for test_func in tests:
        test_name = test_func.__name__
        logger.info(f"\n{'=' * 50}\nRunning {test_name}\n{'=' * 50}")
        
        try:
            test_func()
            results[test_name] = "Success"
        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}")
            results[test_name] = f"Failed: {str(e)}"
    
    # Print summary
    logger.info("\n\n" + "=" * 50)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 50)
    
    for test_name, result in results.items():
        logger.info(f"{test_name}: {result}")
    
    logger.info("=" * 50)

if __name__ == "__main__":
    run_all_tests() 