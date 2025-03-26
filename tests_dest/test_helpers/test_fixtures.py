"""
Test fixtures module.

This module provides pytest fixtures that can be reused across tests.
It provides fixtures for common test dependencies, such as services,
controllers, and models, using direct imports from source modules.
"""
import logging
import pytest
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import FastAPI related components
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# Import from service_imports to use direct imports
from tests_dest.test_helpers.service_imports import (
    # State manager
    StateManager,
    get_state_manager,
    
    # Services
    MaterialService,
    MonitorService,
    P2PService,
    
    # Service getter functions
    get_material_service,
    get_monitor_service,
    get_p2p_service,
    
    # Monitor components
    MonitorHealth,
    MonitorCore,
    MonitorMetrics,
    MonitorErrors,
    create_test_monitor_health,
    
    # Helper functions
    create_test_material,
    
    # Model classes
    Material,
    Requisition, 
    Order,
    
    # Controller functions
    get_material_controller,
    get_p2p_controller,
    get_material_api_controller,
    get_material_ui_controller,
    get_p2p_order_api_controller,
    get_p2p_requisition_api_controller,
    
    # Middleware
    SessionMiddleware
)

# Import helper functions
from tests_dest.test_helpers.service_imports import (
    create_test_material_service,
    create_test_monitor_service,
    create_test_p2p_service,
)

# Import request helpers
from tests_dest.test_helpers.request_helpers import create_test_request

@pytest.fixture
def app():
    """Fixture for a FastAPI app."""
    return FastAPI()

@pytest.fixture
def test_client(app):
    """Fixture for a TestClient."""
    return TestClient(app)

@pytest.fixture
def real_state_manager():
    """Create a real StateManager for testing."""
    return get_state_manager()

@pytest.fixture
def test_state_manager():
    """Fixture for a test state manager."""
    return StateManager()

@pytest.fixture
def real_monitor_service(real_state_manager):
    """Create a real MonitorService for testing."""
    return get_monitor_service(state_manager=real_state_manager)

@pytest.fixture
def test_monitor_service(test_state_manager):
    """Fixture for a test monitor service."""
    return create_test_monitor_service(state_manager=test_state_manager)

@pytest.fixture
def real_monitor_health(real_monitor_service):
    """Create a real MonitorHealth for testing."""
    # Try to create with monitor_service
    try:
        return MonitorHealth(monitor_service=real_monitor_service)
    except TypeError:
        # Try with monitor_core
        monitor_core = MonitorCore()
        return MonitorHealth(monitor_core=monitor_core)

@pytest.fixture
def real_monitor_core(real_monitor_service):
    """Create a real MonitorCore for testing."""
    return MonitorCore(monitor_service=real_monitor_service)

@pytest.fixture
def real_monitor_metrics(real_monitor_service):
    """Create a real MonitorMetrics for testing."""
    return MonitorMetrics(monitor_service=real_monitor_service)

@pytest.fixture
def real_monitor_errors(real_monitor_service):
    """Create a real MonitorErrors for testing."""
    return MonitorErrors(monitor_service=real_monitor_service)

@pytest.fixture
def real_material_service(real_state_manager, real_monitor_service):
    """Create a real MaterialService for testing."""
    return get_material_service(
        state_manager=real_state_manager,
        monitor_service=real_monitor_service
    )

@pytest.fixture
def test_material_service(test_state_manager, test_monitor_service):
    """Fixture for a test material service."""
    return create_test_material_service(
        state_manager=test_state_manager,
        monitor_service=test_monitor_service
    )

@pytest.fixture
def real_p2p_service(real_state_manager, real_material_service, real_monitor_service):
    """Create a real P2PService for testing."""
    return get_p2p_service(
        state_manager=real_state_manager,
        material_service=real_material_service,
        monitor_service=real_monitor_service
    )

@pytest.fixture
def test_p2p_service(test_state_manager, test_material_service, test_monitor_service):
    """Fixture for a test P2P service."""
    return create_test_p2p_service(
        state_manager=test_state_manager,
        material_service=test_material_service,
        monitor_service=test_monitor_service
    )

@pytest.fixture
def test_material(request):
    """Fixture for a test material."""
    return create_test_material(
        id="MAT001",
        name="Test Material",
        description="Material for testing",
        price=10.0
    )

@pytest.fixture
def test_requisition():
    """Fixture for a test requisition."""
    return Requisition(
        id="REQ001",
        title="Test Requisition",
        description="Requisition for testing",
        status="DRAFT",
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00",
        items=[]
    )

@pytest.fixture
def test_order():
    """Fixture for a test order."""
    return Order(
        id="ORD001",
        title="Test Order",
        description="Order for testing",
        status="DRAFT",
        created_at="2023-01-01T00:00:00",
        updated_at="2023-01-01T00:00:00",
        items=[]
    )

@pytest.fixture
def real_request():
    """Create a real request object for testing."""
    return create_test_request(method="GET", url="/test")

@pytest.fixture
def real_material_controller(test_material_service, test_monitor_service):
    """Fixture for a real material controller."""
    return get_material_controller(
        material_service=test_material_service,
        monitor_service=test_monitor_service
    )

@pytest.fixture
def real_material_api_controller(test_material_service, test_monitor_service):
    """Fixture for a real material API controller."""
    return get_material_api_controller(
        material_service=test_material_service,
        monitor_service=test_monitor_service
    )

@pytest.fixture
def real_material_ui_controller(test_material_service, test_monitor_service):
    """Fixture for a real material UI controller."""
    return get_material_ui_controller(
        material_service=test_material_service,
        monitor_service=test_monitor_service
    )

@pytest.fixture
def real_p2p_controller(test_p2p_service, test_monitor_service):
    """Fixture for a real P2P controller."""
    return get_p2p_controller(
        p2p_service=test_p2p_service,
        monitor_service=test_monitor_service
    )

@pytest.fixture
def real_p2p_order_api_controller(test_p2p_service, test_monitor_service):
    """Fixture for a real P2P order API controller."""
    return get_p2p_order_api_controller(
        p2p_service=test_p2p_service,
        monitor_service=test_monitor_service
    )

@pytest.fixture
def real_p2p_requisition_api_controller(test_p2p_service, test_monitor_service):
    """Fixture for a real P2P requisition API controller."""
    return get_p2p_requisition_api_controller(
        p2p_service=test_p2p_service,
        monitor_service=test_monitor_service
    )

@pytest.fixture
def real_session_middleware():
    """Fixture for a real session middleware."""
    return SessionMiddleware() 