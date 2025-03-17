"""
Integration test fixtures and configurations.
"""
import pytest
import sys
import os
import asyncio

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

# Now that paths are set up, import application modules
from services.state_manager import StateManager
from services.material_service import MaterialService
from services.p2p_service import P2PService
from services.monitor_service import MonitorService

# Import fixtures from parent conftest.py file
from conftest import (
    clean_services,
    state_manager_fixture,
    monitor_service_fixture,
    material_service_fixture,
    p2p_service_fixture,
    test_client,
    mock_datetime,
    register_service,
    clear_service_registry,
    async_state_manager,
    async_monitor_service,
    async_material_service,
    async_p2p_service
)

@pytest.fixture
def test_services(state_manager_fixture):
    """Set up test services with clean state."""
    # Reset all services to ensure clean state
    clear_service_registry()
    
    # Create test services with the clean state manager
    monitor_service = MonitorService(state_manager_fixture)
    material_service = MaterialService(state_manager_fixture, monitor_service)
    p2p_service = P2PService(state_manager_fixture, material_service)
    
    # Register services for discovery
    register_service("monitor", monitor_service)
    register_service("material", material_service)
    register_service("p2p", p2p_service)
    
    yield {
        "state_manager": state_manager_fixture,
        "monitor_service": monitor_service,
        "material_service": material_service,
        "p2p_service": p2p_service
    }
    
    # Clean up
    clear_service_registry()
    
@pytest.fixture
async def async_test_services(async_state_manager):
    """Async fixture setting up test services with clean state."""
    # Reset all services to ensure clean state
    clear_service_registry()
    
    # Create test services with the clean state manager
    monitor_service = MonitorService(async_state_manager)
    material_service = MaterialService(async_state_manager, monitor_service)
    p2p_service = P2PService(async_state_manager, material_service)
    
    # Register services for discovery
    register_service("monitor", monitor_service)
    register_service("material", material_service)
    register_service("p2p", p2p_service)
    
    yield {
        "state_manager": async_state_manager,
        "monitor_service": monitor_service,
        "material_service": material_service,
        "p2p_service": p2p_service
    }
    
    # Clean up
    clear_service_registry()
