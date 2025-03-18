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