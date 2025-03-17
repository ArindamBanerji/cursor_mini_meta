"""
API test fixtures and configurations.
"""
import pytest
import sys
import os
import json
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Get project root from environment variable or use path calculation
project_root = os.environ.get("SAP_HARNESS_HOME")
if not project_root:
    # Add project root to path to ensure imports work correctly
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    print(f"SAP_HARNESS_HOME environment variable not set. Using calculated path: {project_root}")

# Add project root to Python path
sys.path.insert(0, project_root)

# Import directly from root conftest by getting the path and adding it to sys.path
root_conftest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_conftest_path)

# Import fixtures from parent conftest.py file
from conftest import (
    clean_services,
    state_manager_fixture,
    monitor_service_fixture,
    material_service_fixture,
    p2p_service_fixture,
    test_client,
    mock_datetime,
    async_state_manager,
    async_monitor_service,
    async_material_service,
    async_p2p_service
)

# Verify that asyncio plugin is loaded
def test_asyncio_plugin_loaded():
    """Simple test to verify asyncio plugin is loaded."""
    assert 'pytest_asyncio' in sys.modules, "pytest-asyncio is not loaded"

@pytest.fixture
def create_test_app():
    """Create a test FastAPI app with specific routes."""
    def _create_app():
        app = FastAPI()
        # Setup routes for testing
        return app
    return _create_app

@pytest.fixture
async def async_test_app():
    """Async fixture for creating a test FastAPI app."""
    app = FastAPI()
    # Setup routes for testing
    return app

@pytest.fixture
async def async_test_client(async_test_app):
    """Async fixture providing a FastAPI test client."""
    return TestClient(async_test_app)

# Mock implementation of health check for testing
@pytest.fixture
async def mock_health_check():
    """Mock implementation of health check to avoid client.host issues."""
    async def _health_check(request):
        return {"status": "healthy"}
    return _health_check
