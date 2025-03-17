"""
Unit test fixtures and configurations.
"""
import pytest
import sys
import os
from unittest.mock import MagicMock

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

@pytest.fixture
def mock_request():
    """Mock request object for unit testing controllers."""
    mock_req = MagicMock()
    mock_req.url = MagicMock()
    mock_req.url.path = "/test"
    mock_req.query_params = {}
    return mock_req

@pytest.fixture
async def async_mock_request():
    """Async mock request object for unit testing controllers."""
    mock_req = MagicMock()
    mock_req.url = MagicMock()
    mock_req.url.path = "/test"
    mock_req.query_params = {}
    return mock_req
