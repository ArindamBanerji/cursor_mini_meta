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