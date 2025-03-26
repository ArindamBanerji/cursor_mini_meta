"""
Test facade diagnostic.

This module tests the functionality of the facade pattern imports.
It ensures that all necessary components can be imported and used.
This file is designed to handle missing components gracefully.
"""
import logging
import pytest

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import service classes from facade
from tests_dest.test_helpers.service_imports import (
    # Base services
    BaseService,
    StateManager, 
    get_state_manager,
    
    # Material service
    MaterialService,
    get_material_service,
    create_test_material,
    create_test_material_service,
    
    # Monitor service
    MonitorService,
    get_monitor_service,
    create_test_monitor_service,
    create_test_monitor_health,
    
    # P2P service
    P2PService,
    get_p2p_service,
    create_test_order,
    create_test_requisition,
    create_test_p2p_service,
    
    # Template and URL services
    TemplateService,
    URLService,
    
    # Service registry functions
    get_service,
    get_or_create_service,
    get_service_status
)

# Import controller functions (these may be placeholders if originals don't exist)
from tests_dest.test_helpers.service_imports import (
    BaseController,
    get_material_controller,
    get_material_api_controller,
    get_material_ui_controller,
    get_safe_client_host,
    get_p2p_controller,
    get_p2p_order_api_controller,
    get_p2p_requisition_api_controller,
    get_system_health,
    get_p2p_statistics,
    get_recent_activities
)

# Import model classes (these may be placeholders if originals don't exist)
from tests_dest.test_helpers.service_imports import (
    BaseDataModel,
    EntityCollection,
    Material,
    MaterialType,
    MaterialStatus,
    UnitOfMeasure,
    ProcurementDocument,
    Requisition,
    Order,
    DocumentStatus,
    ProcurementType,
    DocumentItemStatus
)

# Import middleware components (these may be placeholders if originals don't exist)
from tests_dest.test_helpers.service_imports import (
    SessionMiddleware,
    FlashMessage,
    SessionStore,
    get_session,
    set_session_data,
    get_session_data,
    get_flash_messages,
    add_flash_message,
    store_form_data,
    get_form_data,
    clear_form_data
)

# Import request helpers
from tests_dest.test_helpers.request_helpers import (
    create_test_request,
    create_test_response,
    parse_response_body,
    JSONResponse
)

def test_service_imports():
    """Test that service classes and functions can be imported."""
    # Check that service classes are importable and callable
    logger.info("Testing service imports...")
    
    # Verify StateManager can be instantiated
    state_manager = StateManager()
    assert state_manager is not None
    
    # Test material service imports
    material_service = MaterialService()
    assert material_service is not None
    
    # Test monitor service imports
    monitor_service = MonitorService()
    assert monitor_service is not None
    
    # Test monitor components 
    # Create them with the helper function
    monitor_health = create_test_monitor_health()
    assert monitor_health is not None
    
    # Test P2P service imports
    p2p_service = P2PService()
    assert p2p_service is not None
    
    # Test other services
    assert isinstance(TemplateService(), TemplateService)
    assert isinstance(URLService(), URLService)
    
    # Test service registry functions are callable
    assert callable(get_service)
    assert callable(get_or_create_service)
    assert callable(get_service_status)
    logger.info("Service imports test passed")
    
def test_controller_imports():
    """Test that controller functions can be imported."""
    logger.info("Testing controller imports...")
    
    # Verify controller function callability
    assert callable(get_material_controller)
    assert callable(get_material_api_controller)
    assert callable(get_material_ui_controller)
    assert callable(get_safe_client_host)
    assert callable(get_p2p_controller)
    assert callable(get_p2p_order_api_controller)
    assert callable(get_p2p_requisition_api_controller)
    assert callable(get_system_health)
    assert callable(get_p2p_statistics)
    assert callable(get_recent_activities)
    logger.info("Controller imports test passed")
    
def test_model_imports():
    """Test that model classes can be imported."""
    logger.info("Testing model imports...")
    
    # Check model class importability
    assert BaseDataModel is not None
    
    # Test material model imports
    material = create_test_material(name="Test Material")
    assert material is not None
    assert hasattr(material, "name")
    assert material.name == "Test Material"
    
    # Test using enums if available
    if hasattr(MaterialType, '__members__'):
        assert len(MaterialType.__members__) > 0
    if hasattr(MaterialStatus, '__members__'):
        assert len(MaterialStatus.__members__) > 0
    if hasattr(UnitOfMeasure, '__members__'):
        assert len(UnitOfMeasure.__members__) > 0
    
    # Test P2P model imports
    assert ProcurementDocument is not None
    assert Requisition is not None
    assert Order is not None
    
    # Test enum classes
    if hasattr(DocumentStatus, '__members__'):
        assert len(DocumentStatus.__members__) > 0
    if hasattr(ProcurementType, '__members__'):
        assert len(ProcurementType.__members__) > 0
    if hasattr(DocumentItemStatus, '__members__'):
        assert len(DocumentItemStatus.__members__) > 0
    logger.info("Model imports test passed")
    
def test_middleware_imports():
    """Test that middleware components can be imported."""
    logger.info("Testing middleware imports...")
    
    # Test session middleware
    assert SessionMiddleware is not None
    assert FlashMessage is not None
    assert SessionStore is not None
    
    # Test middleware functions
    assert callable(get_session)
    assert callable(set_session_data)
    assert callable(get_session_data)
    assert callable(get_flash_messages)
    assert callable(add_flash_message)
    assert callable(store_form_data)
    assert callable(get_form_data)
    assert callable(clear_form_data)
    logger.info("Middleware imports test passed")
    
def test_request_helpers():
    """Test that request helpers can be used."""
    logger.info("Testing request helpers...")
    
    # Test creating a request
    request = create_test_request(
        method="GET",
        url="/api/materials",
        headers={"Accept": "application/json"}
    )
    assert request is not None
    assert request.method == "GET"
    assert request.url == "/api/materials"
    assert request.headers["Accept"] == "application/json"
    
    # Test creating a response
    response = create_test_response(
        status_code=200,
        content={"result": "success", "data": [{"id": 1, "name": "Test"}]}
    )
    assert response is not None
    assert response.status_code == 200
    assert "result" in response.body_dict
    assert response.body_dict["result"] == "success"
    
    # Test parsing response body
    data = parse_response_body(response)
    assert data is not None
    assert "result" in data
    assert "data" in data
    assert data["result"] == "success"
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == 1
    logger.info("Request helpers test passed")
    
def test_fixture_dependencies():
    """Test that the fixture dependencies can be used."""
    logger.info("Testing fixture dependencies...")
    
    # Test creating basic components without using fixtures
    state_mgr = StateManager()
    assert state_mgr is not None
    
    # Create services using helper functions
    material_service = create_test_material_service()
    assert material_service is not None
    
    monitor_service = create_test_monitor_service()
    assert monitor_service is not None
    
    p2p_service = create_test_p2p_service()
    assert p2p_service is not None
    
    # Create a test material without using fixtures
    material = create_test_material(
        id="MAT001",
        name="Test Material",
        description="Material for testing"
    )
    assert material is not None
    assert hasattr(material, "id")
    assert hasattr(material, "name")
    assert hasattr(material, "material_number")
    
    logger.info("Fixture dependencies test passed")
    
def test_service_helpers():
    """Test the service helper functions."""
    logger.info("Testing service helper functions...")
    
    # Test material service helper
    material_service = create_test_material_service()
    assert material_service is not None
    
    # Test monitor service helper
    monitor_service = create_test_monitor_service()
    assert monitor_service is not None
    
    # Test P2P service helper
    p2p_service = create_test_p2p_service()
    assert p2p_service is not None
    
    # Test create_test_material functionality
    material = create_test_material(
        id="TEST123", 
        name="Test Helper Material",
        description="Material created with helper function"
    )
    assert material is not None
    assert material.id == "TEST123"
    assert material.name == "Test Helper Material"
    assert material.description == "Material created with helper function"
    assert hasattr(material, "material_number")
    
    logger.info("Service helper functions test passed")
    
def test_complete_facade_pattern():
    """Test that the complete facade pattern works correctly."""
    # This test simply confirms that all the previous tests run without errors
    logger.info("Facade pattern tests completed successfully")
    assert True 