"""
Patched TestClient for FastAPI tests.

This module provides a patched version of FastAPI's TestClient that ensures
request.client.host is properly set during tests.
"""

from fastapi.testclient import TestClient
from starlette.testclient import TestClient as StarletteTestClient
from starlette.types import Scope
import os
import logging

logger = logging.getLogger("patched_testclient")

class PatchedTestClient(TestClient):
    """
    A patched version of FastAPI's TestClient that ensures request.client.host
    is properly set during tests.
    """
    
    def __init__(self, app, **kwargs):
        """
        Initialize the patched test client.
        
        Args:
            app: The FastAPI application
            **kwargs: Additional arguments to pass to the TestClient
        """
        super().__init__(app, **kwargs)
        logger.info("Initialized PatchedTestClient")
        
    def request(self, method, url, **kwargs):
        """
        Override the request method to ensure client.host is set.
        
        Args:
            method: HTTP method
            url: URL to request
            **kwargs: Additional arguments to pass to the request
            
        Returns:
            Response from the request
        """
        # Set PYTEST_CURRENT_TEST environment variable if not already set
        if "PYTEST_CURRENT_TEST" not in os.environ:
            os.environ["PYTEST_CURRENT_TEST"] = "True"
            logger.debug("Set PYTEST_CURRENT_TEST environment variable")
            
        # Call the original request method
        response = super().request(method, url, **kwargs)
        return response
        
    def _build_scope(self, method, url, params=None):
        """
        Override _build_scope to ensure client is properly set in the scope.
        
        Args:
            method: HTTP method
            url: URL to request
            params: Query parameters
            
        Returns:
            Scope dictionary with client information
        """
        scope = super()._build_scope(method, url, params)
        
        # Ensure client is set in the scope
        if "client" not in scope or scope["client"] is None:
            scope["client"] = ("test-client", 12345)
            logger.debug("Set client in scope")
            
        return scope

# Create a function to get a patched test client
def get_patched_test_client(app, **kwargs):
    """
    Get a patched test client for the given app.
    
    Args:
        app: The FastAPI application
        **kwargs: Additional arguments to pass to the TestClient
        
    Returns:
        PatchedTestClient instance
    """
    return PatchedTestClient(app, **kwargs)

# Usage:
# from patched_testclient import get_patched_test_client
# from main import app
# client = get_patched_test_client(app)
