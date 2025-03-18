"""
Shared test fixtures and configurations for all test categories.
"""
import pytest
import sys
import os
from datetime import datetime
from fastapi.testclient import TestClient

# Register pytest plugins
pytest_plugins = ['pytest_asyncio']  # For async test support

@pytest.fixture(autouse=True)
def _setup_test_env(monkeypatch):
    """
    Fixture to ensure environment variables are set for each test.
    This runs automatically for all tests.
    """
    monkeypatch.setenv('TEST_ENV', 'True')
    yield
    # monkeypatch automatically restores environment variables

# Get project root from environment variable or use path calculation
project_root = os.environ.get("SAP_HARNESS_HOME")
if not project_root:
    # Add project root to path to ensure imports work correctly
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print(f"SAP_HARNESS_HOME environment variable not set. Using calculated path: {project_root}")

# Add project root to Python path
sys.path.insert(0, project_root)

# Now import application modules
from services.state_manager import StateManager, state_manager
from services.monitor_service import MonitorService
from services.material_service import MaterialService
from services.p2p_service import P2PService
from main import app

# Import or create service factory functions if they don't exist in services/__init__.py
def get_state_manager():
    """Get the singleton state manager."""
    return state_manager

def get_monitor_service():
    """Get or create a monitor service instance."""
    return MonitorService(state_manager)

def get_material_service():
    """Get or create a material service instance."""
    monitor_service = get_monitor_service()
    return MaterialService(state_manager, monitor_service)

def get_p2p_service():
    """Get or create a P2P service instance."""
    material_service = get_material_service()
    return P2PService(state_manager, material_service)

def register_service(name, service):
    """Register a service for discovery."""
    # This function would normally be in services/__init__.py
    # For tests, we'll just return the service
    return service

def clear_service_registry():
    """Clear the service registry."""
    # This function would normally be in services/__init__.py
    # For tests, we'll just do nothing
    pass

@pytest.fixture(autouse=True)
def clean_services():
    """Automatically clean up services before each test."""
    clear_service_registry()
    # Get a fresh state manager and clear it
    state_manager.clear()
    yield
    # Clean up after test
    clear_service_registry()
    state_manager.clear()

@pytest.fixture
def state_manager_fixture():
    """Fixture providing the singleton state manager."""
    return get_state_manager()

@pytest.fixture
def monitor_service_fixture():
    """Fixture providing a monitor service instance."""
    service = get_monitor_service()
    register_service("monitor", service)
    return service

@pytest.fixture
def material_service_fixture():
    """Fixture providing a material service instance."""
    service = get_material_service()
    register_service("material", service)
    return service

@pytest.fixture
def p2p_service_fixture():
    """Fixture providing a P2P service instance."""
    service = get_p2p_service()
    register_service("p2p", service)
    return service

@pytest.fixture
def test_client():
    """Fixture providing a FastAPI test client."""
    return TestClient(app)

@pytest.fixture
def mock_datetime(monkeypatch):
    """Fixture for mocking datetime in tests."""
    class MockDateTime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 1, 12, 0, 0)
    
    monkeypatch.setattr("datetime.datetime", MockDateTime)
    return MockDateTime

# Async fixtures for testing async functions
@pytest.fixture
async def async_state_manager():
    """Async fixture providing the singleton state manager."""
    return get_state_manager()

@pytest.fixture
async def async_monitor_service():
    """Async fixture providing a monitor service instance."""
    service = get_monitor_service()
    register_service("monitor", service)
    return service

@pytest.fixture
async def async_material_service():
    """Async fixture providing a material service instance."""
    service = get_material_service()
    register_service("material", service)
    return service

@pytest.fixture
async def async_p2p_service():
    """Async fixture providing a P2P service instance."""
    service = get_p2p_service()
    register_service("p2p", service)
    return service
