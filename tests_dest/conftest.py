"""
Shared test fixtures and configurations for all test categories.

This is the main conftest.py file for the entire test suite.
It provides fixtures for all test categories including:
- API tests
- Integration tests
- Model tests
- Monitoring tests
- Service tests
- Unit tests
"""
import os
import sys
import logging
import pytest
import random
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

# Import the simplified import helper to handle path setup
from tests_dest.import_helper import fix_imports
project_root = fix_imports()

# Import test helpers fixtures to make them globally available
# This exposes all fixtures from test_helpers to all test files
try:
    from tests_dest.test_helpers.test_fixtures import (
        # App and request fixtures
        app,
        real_request,
        test_client,
        
        # Core service fixtures
        real_state_manager,
        real_material_service,
        real_monitor_service,
        real_p2p_service,
        
        # Monitor component fixtures
        real_monitor_health,
        real_monitor_core,
        real_monitor_metrics,
        real_monitor_errors,
        
        # Utility service fixtures
        real_template_service,
        real_url_service,
        
        # Controller fixtures
        real_material_controller,
        real_material_api_controller,
        real_p2p_controller,
        real_p2p_order_api_controller,
        real_p2p_requisition_api_controller,
        
        # Session and middleware fixtures
        real_session_store,
        real_session_middleware,
        test_flash_message,
        
        # Model instance fixtures
        test_material,
        test_requisition,
        test_order
    )
except ImportError as e:
    logging.warning(f"Could not import test_helpers fixtures: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("conftest")

# Register pytest plugins
pytest_plugins = ['pytest_asyncio']  # For async test support

# Service registry for tests - populated lazily
_service_registry = {}

# Setup environment variables for tests
def setup_test_env_vars(monkeypatch):
    """Set up environment variables for tests."""
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("TEMPLATE_DIR", "templates")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

@pytest.fixture(autouse=True)
def clean_state_manager(monkeypatch):
    """Create a clean state manager for each test."""
    # Import here to avoid circular dependency
    try:
        from services.state_manager import StateManager
        
        # Create a fresh instance
        test_state_manager = StateManager()
        
        # Patch both the state_manager singleton and get_state_manager function
        try:
            monkeypatch.setattr("services.state_manager.state_manager", test_state_manager)
        except AttributeError as e:
            logger.warning(f"Could not patch state_manager singleton: {e}")
            
        try:
            monkeypatch.setattr("services.state_manager.get_state_manager", lambda: test_state_manager)
        except AttributeError as e:
            logger.warning(f"Could not patch get_state_manager function: {e}")
        
        # Clear services registry to ensure clean state
        _service_registry.clear()
        
        return test_state_manager
    except ImportError as e:
        logger.warning(f"StateManager not available, creating mock: {e}")
        # Return a mock state manager if we can't import the real one
        mock_state_manager = MagicMock()
        mock_state_manager.get.return_value = None
        mock_state_manager.set.return_value = None
        return mock_state_manager

def get_state_manager():
    """Get a fresh state manager for tests."""
    # Import locally to avoid circular imports
    try:
        from services.state_manager import StateManager
        return StateManager()
    except ImportError as e:
        logger.warning(f"StateManager not available, creating mock: {e}")
        # Return a mock state manager if we can't import the real one
        mock_state_manager = MagicMock()
        mock_state_manager.get.return_value = None
        mock_state_manager.set.return_value = None
        return mock_state_manager

def get_monitor_service():
    """Get or create a monitor service instance."""
    if "monitor" in _service_registry:
        return _service_registry["monitor"]
    
    try:
        from services.monitor_service import MonitorService
        from services.state_manager import state_manager
        
        service = MonitorService(state_manager)
        _service_registry["monitor"] = service
        return service
    except ImportError as e:
        logger.error(f"Could not import MonitorService: {e}")
        return None

def get_material_service():
    """Get or create a material service instance."""
    if "material" in _service_registry:
        return _service_registry["material"]
    
    try:
        from services.material_service import MaterialService
        from services.state_manager import state_manager
        
        monitor_service = get_monitor_service()
        service = MaterialService(state_manager, monitor_service)
        _service_registry["material"] = service
        return service
    except ImportError as e:
        logger.error(f"Could not import MaterialService: {e}")
        return None

def get_p2p_service():
    """Get or create a P2P service instance."""
    if "p2p" in _service_registry:
        return _service_registry["p2p"]
    
    try:
        from services.p2p_service import P2PService
        from services.state_manager import state_manager
        
        material_service = get_material_service()
        service = P2PService(state_manager, material_service)
        _service_registry["p2p"] = service
        return service
    except ImportError as e:
        logger.error(f"Could not import P2PService: {e}")
        return None

def register_service(name, service):
    """Register a service for discovery."""
    _service_registry[name] = service
    return service

def clear_service_registry():
    """Clear the service registry."""
    _service_registry.clear()

#
# GENERAL TEST FIXTURES
#

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """
    Set up the test environment.
    This runs automatically for each test.
    """
    # Set environment variables
    monkeypatch.setenv('TEST_ENV', 'True')
    
    yield
    
    # No cleanup required, monkeypatch handles restoration automatically

@pytest.fixture(autouse=True)
def clean_services():
    """Automatically clean up services before each test."""
    clear_service_registry()
    # Get a fresh state manager and clear it
    try:
        from services.state_manager import get_state_manager
        state_mgr = get_state_manager()
        if state_mgr:
            state_mgr.clear()
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not clear state manager: {e}")
    yield
    # Clean up after test
    clear_service_registry()
    try:
        from services.state_manager import get_state_manager
        state_mgr = get_state_manager()
        if state_mgr:
            state_mgr.clear()
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not clear state manager: {e}")

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
    try:
        from main import app
        return TestClient(app)
    except ImportError as e:
        logger.error(f"Could not import app: {e}")
        from fastapi import FastAPI
        return TestClient(FastAPI())

@pytest.fixture
def mock_datetime(monkeypatch):
    """Fixture for mocking datetime in tests."""
    class MockDateTime:
        @classmethod
        def now(cls):
            return datetime(2024, 1, 1, 12, 0, 0)
    
    monkeypatch.setattr("datetime.datetime", MockDateTime)
    return MockDateTime

#
# ASYNC FIXTURES
#

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

#
# INTEGRATION TEST FIXTURES
#

@pytest.fixture
def test_services(state_manager_fixture):
    """Set up test services with clean state."""
    # Reset all services to ensure clean state
    clear_service_registry()

    # Import directly from service_imports
    from tests_dest.test_helpers.service_imports import (
        MonitorService,
        MaterialService,
        P2PService
    )
    
    # Create test services with the clean state manager
    monitor_service = MonitorService(state_manager_fixture)
    material_service = MaterialService(state_manager_fixture, monitor_service)
    p2p_service = P2PService(state_manager_fixture, material_service)
    
    # Register services
    register_service("monitor", monitor_service)
    register_service("material", material_service)
    register_service("p2p", p2p_service)
    
    yield {
        "monitor_service": monitor_service,
        "material_service": material_service,
        "p2p_service": p2p_service,
        "state_manager": state_manager_fixture
    }
    
    # Clean up
    clear_service_registry()
    if hasattr(state_manager_fixture, 'clear'):
        state_manager_fixture.clear()

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

#
# MODEL TEST FIXTURES
#

@pytest.fixture
def entity_collection():
    """Fixture providing an entity collection for tests."""
    state_manager = get_state_manager()
    return EntityCollection(state_manager.get_state("test_entity"))

@pytest.fixture
def model_state_manager():
    """Fixture providing a state manager for model tests."""
    state_manager = get_state_manager()
    return state_manager

@pytest.fixture
async def async_entity_collection():
    """Async fixture providing an entity collection for tests."""
    state_manager = get_state_manager()
    return EntityCollection(state_manager.get_state("test_entity"))

@pytest.fixture
async def async_model_state_manager():
    """Async fixture providing a state manager for model tests."""
    state_manager = get_state_manager()
    return state_manager

#
# SERVICE TEST FIXTURES
#

@pytest.fixture
def test_material():
    """Fixture providing a test material instance."""
    material_create = MaterialCreate(
        material_id="TEST-001",
        name="Test Material 1",
        description="Test material for services testing",
        material_type=MaterialType.RAW,
        unit_of_measure=UnitOfMeasure.KG,
        quantity=100.0,
        location="Warehouse A",
        status=MaterialStatus.AVAILABLE
    )
    
    material = Material(
        **material_create.dict(),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    return material

@pytest.fixture
def setup_test_materials(material_service_fixture):
    """Fixture setting up test materials for services testing."""
    materials = []
    
    # Create test materials
    for i in range(1, 5):
        material_create = MaterialCreate(
            material_id=f"TEST-{i:03d}",
            name=f"Test Material {i}",
            description=f"Test material {i} for services testing",
            material_type=MaterialType.RAW if i % 2 == 0 else MaterialType.FINISHED,
            unit_of_measure=UnitOfMeasure.KG if i % 2 == 0 else UnitOfMeasure.PIECE,
            quantity=100.0 * i,
            location=f"Warehouse {chr(64 + i)}",
            status=MaterialStatus.AVAILABLE if i % 2 == 0 else MaterialStatus.IN_TRANSIT
        )
        
        material = material_service_fixture.create_material(material_create)
        materials.append(material)
    
    return materials

@pytest.fixture
async def async_test_material():
    """Async fixture providing a test material instance."""
    material_create = MaterialCreate(
        material_id="TEST-001",
        name="Test Material 1",
        description="Test material for services testing",
        material_type=MaterialType.RAW,
        unit_of_measure=UnitOfMeasure.KG,
        quantity=100.0,
        location="Warehouse A",
        status=MaterialStatus.AVAILABLE
    )
    
    material = Material(
        **material_create.dict(),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    return material

@pytest.fixture
async def async_setup_test_materials(async_material_service):
    """Async fixture setting up test materials for services testing."""
    materials = []
    
    # Create test materials
    for i in range(1, 5):
        material_create = MaterialCreate(
            material_id=f"TEST-{i:03d}",
            name=f"Test Material {i}",
            description=f"Test material {i} for services testing",
            material_type=MaterialType.RAW if i % 2 == 0 else MaterialType.FINISHED,
            unit_of_measure=UnitOfMeasure.KG if i % 2 == 0 else UnitOfMeasure.PIECE,
            quantity=100.0 * i,
            location=f"Warehouse {chr(64 + i)}",
            status=MaterialStatus.AVAILABLE if i % 2 == 0 else MaterialStatus.IN_TRANSIT
        )
        
        material = async_material_service.create_material(material_create)
        materials.append(material)
    
    return materials

#
# MONITORING TEST FIXTURES
#

@pytest.fixture
def reset_monitoring_state(monitor_service_fixture):
    """Reset the monitoring state before each test."""
    monitor_service_fixture.clear()
    return monitor_service_fixture

@pytest.fixture
def sample_metrics():
    """Generate sample metrics for testing."""
    now = datetime.now()
    metrics = []
    
    # Generate metrics for the last hour with 5-minute intervals
    for i in range(12):
        timestamp = now - timedelta(minutes=i * 5)
        metrics.append(
            SystemMetrics(
                timestamp=timestamp,
                cpu_usage=random.uniform(10, 90),
                memory_usage=random.uniform(20, 80),
                disk_usage=random.uniform(30, 70),
                network_in=random.uniform(1, 100),
                network_out=random.uniform(1, 100)
            )
        )
    
    return metrics

@pytest.fixture
async def async_reset_monitoring_state(async_monitor_service):
    """Async fixture to reset the monitoring state before each test."""
    async_monitor_service.clear()
    return async_monitor_service

@pytest.fixture
async def async_sample_metrics():
    """Async fixture to generate sample metrics for testing."""
    now = datetime.now()
    metrics = []
    
    # Generate metrics for the last hour with 5-minute intervals
    for i in range(12):
        timestamp = now - timedelta(minutes=i * 5)
        metrics.append(
            SystemMetrics(
                timestamp=timestamp,
                cpu_usage=random.uniform(10, 90),
                memory_usage=random.uniform(20, 80),
                disk_usage=random.uniform(30, 70),
                network_in=random.uniform(1, 100),
                network_out=random.uniform(1, 100)
            )
        )
    
    return metrics

#
# API TEST FIXTURES
#

@pytest.fixture
def api_client():
    """Fixture providing a FastAPI test client for API tests."""
    try:
        from main import app
        return TestClient(app)
    except ImportError as e:
        logger.error(f"Could not import app: {e}")
        from fastapi import FastAPI
        return TestClient(FastAPI())

@pytest.fixture
def setup_api_services():
    """Fixture setting up services for API tests."""
    # Clear the service registry
    clear_service_registry()
    
    # Get service instances
    state_manager = get_state_manager()
    monitor_service = get_monitor_service()
    material_service = get_material_service()
    p2p_service = get_p2p_service()
    
    # Register services
    register_service("state_manager", state_manager)
    register_service("monitor", monitor_service)
    register_service("material", material_service)
    register_service("p2p", p2p_service)
    
    # Clear states
    state_manager.clear()
    
    return {
        "state_manager": state_manager,
        "monitor_service": monitor_service,
        "material_service": material_service,
        "p2p_service": p2p_service
    }

#
# UNIT TEST FIXTURES
#

@pytest.fixture
def unit_test_env():
    """Set up clean environment for unit tests."""
    # Clear the service registry
    clear_service_registry()
    
    # Get a fresh state manager and clear it
    state_manager = get_state_manager()
    state_manager.clear()
    
    return {
        "state_manager": state_manager
    }

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
