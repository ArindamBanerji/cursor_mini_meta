# genconftest_templates.py
"""
Template module for GenConfTest script.

This module contains all the template content used by the GenConfTest script 
to generate appropriate conftest.py files.
"""

def get_root_conftest_template():
    """Get the template for root directory conftest.py"""
    return '''"""
Shared test fixtures and configurations for all test categories.
"""
import pytest
import sys
import os
from datetime import datetime
from fastapi.testclient import TestClient
from test_import_helper import setup_test_paths, setup_test_env_vars

# Register pytest plugins
pytest_plugins = ['pytest_asyncio']  # For async test support

# Set up paths at module level
project_root = setup_test_paths()

@pytest.fixture(autouse=True)
def _setup_test_env(monkeypatch):
    """
    Fixture to ensure environment variables are set for each test.
    This runs automatically for all tests.
    """
    setup_test_env_vars(monkeypatch, project_root)
    yield
    # monkeypatch automatically restores environment variables

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
'''

def get_unit_conftest_template():
    """Get the template for unit test directory conftest.py"""
    return """\"\"\"
Unit test fixtures and configurations.
\"\"\"
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
"""

def get_api_conftest_template():
    """Get the template for API test directory conftest.py"""
    return """\"\"\"
API test fixtures and configurations.
\"\"\"
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
"""

def get_services_conftest_template():
    """Get the template for services test directory conftest.py"""
    return """\"\"\"
Service test fixtures and configurations.
\"\"\"
import pytest
import sys
import os

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
from models.material import (
    Material, MaterialCreate, MaterialType, MaterialStatus, UnitOfMeasure
)

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
def test_material():
    """Create a test material for testing."""
    return Material(
        material_number="TEST001",
        name="Test Material",
        description="A test material for service testing",
        type=MaterialType.FINISHED,
        base_unit=UnitOfMeasure.EACH,
        status=MaterialStatus.ACTIVE
    )

@pytest.fixture
def setup_test_materials(material_service_fixture):
    """Set up various test materials with different statuses"""
    # Active materials of different types
    material_service_fixture.create_material(
        MaterialCreate(
            material_number="RAW001",
            name="Raw Material",
            type=MaterialType.RAW,
            description="Active raw material"
        )
    )
    
    material_service_fixture.create_material(
        MaterialCreate(
            material_number="FIN001",
            name="Finished Product",
            type=MaterialType.FINISHED,
            description="Active finished product"
        )
    )
    
    return material_service_fixture

@pytest.fixture
async def async_test_material():
    """Async fixture creating a test material for testing."""
    return Material(
        material_number="TEST001",
        name="Test Material",
        description="A test material for service testing",
        type=MaterialType.FINISHED,
        base_unit=UnitOfMeasure.EACH,
        status=MaterialStatus.ACTIVE
    )

@pytest.fixture
async def async_setup_test_materials(async_material_service):
    """Async fixture setting up various test materials with different statuses"""
    # Active materials of different types
    async_material_service.create_material(
        MaterialCreate(
            material_number="RAW001",
            name="Raw Material",
            type=MaterialType.RAW,
            description="Active raw material"
        )
    )
    
    async_material_service.create_material(
        MaterialCreate(
            material_number="FIN001",
            name="Finished Product",
            type=MaterialType.FINISHED,
            description="Active finished product"
        )
    )
    
    return async_material_service
"""

def get_models_conftest_template():
    """Get the template for models test directory conftest.py"""
    return """
Model test fixtures and configurations.

import pytest
import sys
import os
from datetime import datetime

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
from models.common import EntityCollection
from services.state_manager import StateManager

# Import fixtures from parent conftest.py file
# Import directly from the conftest module in the parent directory
from conftest import (
    clean_services,
    state_manager_fixture,
    mock_datetime,
    async_state_manager
)

@pytest.fixture
def entity_collection():
    """Create an empty entity collection for testing."""
    return EntityCollection(name="test-collection")

@pytest.fixture
def model_state_manager():
    """Create a dedicated state manager for model tests."""
    manager = StateManager()
    manager.clear()
    return manager

@pytest.fixture
async def async_entity_collection():
    """Async fixture creating an empty entity collection for testing."""
    return EntityCollection(name="test-collection")

@pytest.fixture
async def async_model_state_manager():
    """Async fixture creating a dedicated state manager for model tests."""
    manager = StateManager()
    manager.clear()
    return manager
"""

def get_monitoring_conftest_template():
    """Get the template for monitoring test directory conftest.py"""
    return """\"\"\"
Monitoring test fixtures and configurations.
\"\"\"
import pytest
import sys
import os
import logging
import json
from datetime import datetime, timedelta

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
from services.monitor_service import SystemMetrics, ErrorLog, MonitorService
from services.state_manager import state_manager

# Import fixtures from parent conftest.py file
from conftest import (
    clean_services,
    state_manager_fixture,
    monitor_service_fixture,
    test_client,
    mock_datetime,
    async_state_manager,
    async_monitor_service
)

# Configure logging for monitoring tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("monitoring_tests")

@pytest.fixture
def reset_monitoring_state():
    """Reset the monitoring state."""
    logger.info("Resetting monitoring state for test")
    # Clear monitoring-specific state
    state_manager.set("system_metrics", [])
    state_manager.set("error_logs", [])
    state_manager.set("component_status", {})
    return state_manager

@pytest.fixture
def sample_metrics():
    """Create sample metrics for testing."""
    now = datetime.now()
    return [
        {
            "timestamp": (now - timedelta(hours=2)).isoformat(),
            "cpu_percent": 50.0,
            "memory_usage": 60.0,
            "available_memory": 8.0,
            "disk_usage": 70.0
        },
        {
            "timestamp": (now - timedelta(hours=1)).isoformat(),
            "cpu_percent": 30.0,
            "memory_usage": 40.0,
            "available_memory": 12.0,
            "disk_usage": 50.0
        }
    ]

@pytest.fixture
async def async_reset_monitoring_state():
    """Async fixture resetting the monitoring state."""
    logger.info("Resetting monitoring state for async test")
    # Clear monitoring-specific state
    state_manager.set("system_metrics", [])
    state_manager.set("error_logs", [])
    state_manager.set("component_status", {})
    return state_manager

@pytest.fixture
async def async_sample_metrics():
    """Async fixture creating sample metrics for testing."""
    now = datetime.now()
    return [
        {
            "timestamp": (now - timedelta(hours=2)).isoformat(),
            "cpu_percent": 50.0,
            "memory_usage": 60.0,
            "available_memory": 8.0,
            "disk_usage": 70.0
        },
        {
            "timestamp": (now - timedelta(hours=1)).isoformat(),
            "cpu_percent": 30.0,
            "memory_usage": 40.0,
            "available_memory": 12.0,
            "disk_usage": 50.0
        }
    ]
"""

def get_integration_conftest_template():
    """Get the template for integration test directory conftest.py"""
    return """\"\"\"
Integration test fixtures and configurations.
\"\"\"
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
"""

def get_generic_conftest_template():
    """Get the template for a generic test directory conftest.py"""
    return """\"\"\"
Test fixtures and configurations for {subdir} tests.
\"\"\"
import pytest
import sys
import os

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

# Add any {subdir}-specific fixtures below
"""

def get_template_for_subdir(subdir):
    """Get the appropriate template for a given subdirectory"""
    subdir = subdir.lower()
    
    if subdir == "root":
        return get_root_conftest_template()
    elif subdir == "unit":
        return get_unit_conftest_template()
    elif subdir == "api":
        return get_api_conftest_template()
    elif subdir == "services":
        return get_services_conftest_template()
    elif subdir == "integration":
        return get_integration_conftest_template()
    elif subdir == "models":
        return get_models_conftest_template()
    elif subdir == "monitoring":
        return get_monitoring_conftest_template()
    else:
        return get_generic_conftest_template().format(subdir=subdir)