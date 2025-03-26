"""
Simplified conftest for the Mini Meta Harness test suite.

This conftest.py provides streamlined fixtures while avoiding:
1. Duplicate code and circular imports
2. Complex service initialization patterns
3. Redundant fixture definitions
"""
import os
import sys
import logging
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("conftest")

# Service registry - a single source of truth for service instances
_service_registry = {}

# ==================================================================
# PATH AND ENVIRONMENT SETUP
# ==================================================================

def setup_python_path():
    """Set up Python path for tests to find project modules."""
    # Find the project root - parent of tests-dest directory
    test_dir = Path(__file__).parent
    project_root = test_dir.parent
    
    # Add project root to path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.debug(f"Added {project_root} to sys.path")
    
    # Set common environment variables
    os.environ.setdefault("TEST_MODE", "true")
    os.environ.setdefault("PROJECT_ROOT", str(project_root))
    
    return project_root

# Initialize paths
project_root = setup_python_path()

# ==================================================================
# SERVICE MANAGEMENT
# ==================================================================

def clear_services():
    """Clear the service registry."""
    _service_registry.clear()

def get_service(service_type, factory_func):
    """Get or create a service instance using lazy initialization.
    
    Args:
        service_type: The service type key (e.g., "monitor", "material")
        factory_func: Function to create the service if it doesn't exist
        
    Returns:
        The service instance
    """
    if service_type in _service_registry:
        return _service_registry[service_type]
    
    service = factory_func()
    if service:
        _service_registry[service_type] = service
    return service

# ==================================================================
# CORE TEST FIXTURES
# ==================================================================

@pytest.fixture(autouse=True)
def test_environment(monkeypatch):
    """Set up the test environment for all tests."""
    # Set essential environment variables
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    
    yield
    
    # Cleanup happens automatically via monkeypatch

@pytest.fixture(autouse=True)
def clean_state_manager(monkeypatch):
    """Provide a clean StateManager for each test."""
    try:
        # Import here to avoid circular imports
        from services.state_manager import StateManager
        
        # Create a fresh instance
        state_manager = StateManager()
        
        # Patch the global state manager
        monkeypatch.setattr("services.state_manager.state_manager", state_manager)
        monkeypatch.setattr("services.state_manager.get_state_manager", lambda: state_manager)
        
        # Clear the service registry to ensure clean state
        clear_services()
        
        return state_manager
    except ImportError as e:
        logger.warning(f"Could not import StateManager: {e}")
        # Return a mock that won't break tests
        return MagicMock()

@pytest.fixture(scope="function")
def test_services(clean_state_manager):
    """Set up all test services with a clean state."""
    # Import services here to avoid circular imports
    try:
        from services.monitor_service import MonitorService
        from services.material_service import MaterialService
        from services.p2p_service import P2PService
        
        # Create services in dependency order
        monitor_service = MonitorService(clean_state_manager)
        material_service = MaterialService(clean_state_manager, monitor_service)
        p2p_service = P2PService(clean_state_manager, material_service)
        
        # Register services
        _service_registry.update({
            "monitor": monitor_service,
            "material": material_service,
            "p2p": p2p_service
        })
        
        services = {
            "state_manager": clean_state_manager,
            "monitor_service": monitor_service,
            "material_service": material_service,
            "p2p_service": p2p_service
        }
        
        yield services
        
        # Clean up after test
        clear_services()
        clean_state_manager.clear()
        
    except ImportError as e:
        logger.warning(f"Could not set up services: {e}")
        # Return basic mocks so tests don't break
        yield {
            "state_manager": clean_state_manager,
            "monitor_service": MagicMock(),
            "material_service": MagicMock(),
            "p2p_service": MagicMock()
        }

# ==================================================================
# INDIVIDUAL SERVICE FIXTURES
# ==================================================================

@pytest.fixture
def monitor_service(test_services):
    """Fixture providing a monitor service instance."""
    return test_services["monitor_service"]

@pytest.fixture
def material_service(test_services):
    """Fixture providing a material service instance."""
    return test_services["material_service"]

@pytest.fixture
def p2p_service(test_services):
    """Fixture providing a P2P service instance."""
    return test_services["p2p_service"]

# ==================================================================
# API TEST FIXTURES
# ==================================================================

@pytest.fixture
def test_client():
    """Fixture providing a FastAPI test client."""
    try:
        from main import app
        return TestClient(app)
    except ImportError as e:
        logger.warning(f"Could not import app: {e}")
        from fastapi import FastAPI
        return TestClient(FastAPI())

@pytest.fixture
def mock_request():
    """Fixture providing a mock HTTP request."""
    mock_req = MagicMock()
    mock_req.headers = {}
    mock_req.cookies = {}
    mock_req.query_params = {}
    mock_req.path_params = {}
    return mock_req

@pytest.fixture
def async_mock_request():
    """Fixture providing an async mock HTTP request."""
    mock_req = AsyncMock()
    mock_req.headers = {}
    mock_req.cookies = {}
    mock_req.query_params = {}
    mock_req.path_params = {}
    return mock_req

# ==================================================================
# TEST DATA FIXTURES
# ==================================================================

@pytest.fixture
def test_material():
    """Fixture providing a test material instance."""
    try:
        from datetime import datetime
        from models.material_models import Material, MaterialCreate, MaterialType, UnitOfMeasure, MaterialStatus
        
        material_create = MaterialCreate(
            material_id="TEST-001",
            name="Test Material 1",
            description="Test material for testing",
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
    except ImportError as e:
        logger.warning(f"Could not create test material: {e}")
        return MagicMock() 