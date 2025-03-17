"""
Test context manager for FastAPI tests.

This module provides a context manager for setting up the test environment,
including setting the PYTEST_CURRENT_TEST environment variable.
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any

logger = logging.getLogger("test_context")

@contextmanager
def test_client_context(client=None, set_env_vars: Optional[Dict[str, Any]] = None):
    """
    Context manager for tests that ensures the PYTEST_CURRENT_TEST environment
    variable is set during the test and cleaned up afterward.
    
    Args:
        client: Optional test client to use
        set_env_vars: Optional dictionary of environment variables to set
        
    Yields:
        The provided client or None
    """
    # Store original environment variables
    original_env_vars = {}
    env_vars_to_set = {"PYTEST_CURRENT_TEST": "True"}
    
    # Add any additional environment variables
    if set_env_vars:
        env_vars_to_set.update(set_env_vars)
    
    # Set environment variables
    for key, value in env_vars_to_set.items():
        if key in os.environ:
            original_env_vars[key] = os.environ[key]
        os.environ[key] = str(value)
        logger.debug(f"Set environment variable {key}={value}")
    
    try:
        # Yield the client
        yield client
    finally:
        # Restore original environment variables
        for key in env_vars_to_set:
            if key in original_env_vars:
                os.environ[key] = original_env_vars[key]
                logger.debug(f"Restored environment variable {key}={original_env_vars[key]}")
            else:
                if key in os.environ:
                    del os.environ[key]
                    logger.debug(f"Removed environment variable {key}")

# Usage example:
# from helpers.test_context import test_client_context
# from fastapi.testclient import TestClient
# from main import app
#
# client = TestClient(app)
# with test_client_context(client):
#     response = client.get("/api/endpoint")
#     assert response.status_code == 200
