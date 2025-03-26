"""
Patched TestClient for FastAPI tests that handles request.client.host issues.

This module provides a TestClient that patches the Request.client property
to ensure that request.client.host is properly set during tests.
"""

import logging
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("patched_request_client")

class PatchedRequestClient(TestClient):
    """
    A TestClient that patches the Request.client property to ensure
    request.client.host is properly set during tests.
    
    This solves the issue where accessing request.client.host directly
    in controllers causes AttributeError during tests.
    """
    
    def __init__(self, app: FastAPI, client_host: str = "test-client", **kwargs):
        """
        Initialize the patched test client.
        
        Args:
            app: The FastAPI application
            client_host: The host value to use for request.client.host
            **kwargs: Additional arguments to pass to TestClient
        """
        super().__init__(app, **kwargs)
        self.client_host = client_host
        
        # Create a mock client with host attribute
        self.mock_client = MagicMock()
        self.mock_client.host = self.client_host
        
        # Start the patcher
        self.patcher = patch('fastapi.Request.client', self.mock_client)
        self.patcher.start()
        
        logger.info(f"Initialized PatchedRequestClient with client_host={client_host}")
    
    def __del__(self):
        """Clean up the patcher when the client is deleted."""
        try:
            self.patcher.stop()
            logger.info("Stopped Request.client patcher")
        except Exception:
            # Ignore errors during cleanup
            pass

def get_patched_client(app: FastAPI, client_host: str = "test-client", **kwargs):
    """
    Get a patched test client for the given app.
    
    Args:
        app: The FastAPI application
        client_host: The host value to use for request.client.host
        **kwargs: Additional arguments to pass to TestClient
        
    Returns:
        PatchedRequestClient instance
    """
    return PatchedRequestClient(app, client_host, **kwargs)

# Usage example:
# from helpers.patched_request_client import get_patched_client
# from main import app
# 
# client = get_patched_client(app)
# response = client.get("/api/endpoint")
# assert response.status_code == 200 