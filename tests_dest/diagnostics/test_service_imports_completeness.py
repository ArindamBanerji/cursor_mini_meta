"""
Diagnostic test for service_imports.py completeness.

This test validates that tests_dest/test_helpers/service_imports.py contains
all necessary classes and functions needed for testing the codebase.
"""

import inspect
import pytest
import typing
from enum import Enum

# Test completeness of service_imports by importing everything from it
from tests_dest.test_helpers.service_imports import *

# Define categories and their expected exports for validation
SERVICE_CLASSES = [
    # Base Services
    (BaseService, "BaseService"),
    (StateManager, "StateManager"),
    
    # Core Services
    (MaterialService, "MaterialService"),
    (P2PService, "P2PService"),
    (MonitorService, "MonitorService"),
    
    # Monitor Components
    (MonitorHealth, "MonitorHealth"),
    (MonitorCore, "MonitorCore"),
    (MonitorMetrics, "MonitorMetrics"),
    (MonitorErrors, "MonitorErrors"),
    
    # Template and URL Services
    (TemplateService, "TemplateService"),
    (URLService, "URLService"),
]

MODEL_CLASSES = [
    # Base Models
    (BaseDataModel, "BaseDataModel"),
    (EntityCollection, "EntityCollection"),
    
    # Material Models
    (Material, "Material"),
    (MaterialCreate, "MaterialCreate"),
    (MaterialUpdate, "MaterialUpdate"),
    
    # P2P Models
    (Requisition, "Requisition"),
    (Order, "Order"),
    (RequisitionCreate, "RequisitionCreate"),
    (OrderCreate, "OrderCreate"),
    (RequisitionUpdate, "RequisitionUpdate"),
    (OrderUpdate, "OrderUpdate"),
    (DocumentItem, "DocumentItem"),
    (RequisitionItem, "RequisitionItem"),
    (OrderItem, "OrderItem"),
]

ENUM_CLASSES = [
    # Material Enums
    (MaterialStatus, "MaterialStatus"),
    (MaterialType, "MaterialType"),
    (UnitOfMeasure, "UnitOfMeasure"),
    
    # P2P Enums
    (DocumentStatus, "DocumentStatus"),
    (ProcurementType, "ProcurementType"),
    (DocumentItemStatus, "DocumentItemStatus"),
    
    # Route Enums
    (HttpMethod, "HttpMethod"),
]

ERROR_CLASSES = [
    (NotFoundError, "NotFoundError"),
    (ValidationError, "ValidationError"),
    (BadRequestError, "BadRequestError"),
    (ConflictError, "ConflictError"),
    (AuthenticationError, "AuthenticationError"),
    (AuthorizationError, "AuthorizationError"),
]

KEY_FUNCTIONS = [
    # Service factory functions
    (get_material_service, "get_material_service"),
    (get_p2p_service, "get_p2p_service"),
    (get_monitor_service, "get_monitor_service"),
    (get_state_manager, "get_state_manager"),
    
    # Service registry functions
    (get_service, "get_service"),
    (get_or_create_service, "get_or_create_service"),
    (get_service_status, "get_service_status"),
    (register_service, "register_service"),
    (clear_service_registry, "clear_service_registry"),
    (reset_services, "reset_services"),
    
    # Controller factory functions
    (get_material_controller, "get_material_controller"),
    (get_material_api_controller, "get_material_api_controller"),
    (get_material_ui_controller, "get_material_ui_controller"),
    (get_p2p_controller, "get_p2p_controller"),
    (get_p2p_order_api_controller, "get_p2p_order_api_controller"),
    (get_p2p_requisition_api_controller, "get_p2p_requisition_api_controller"),
    
    # Test helper functions
    (create_test_material, "create_test_material"),
    (create_test_material_service, "create_test_material_service"),
    (create_test_p2p_service, "create_test_p2p_service"),
    (create_test_monitor_service, "create_test_monitor_service"),
    (create_test_state_manager, "create_test_state_manager"),
]

CRITICAL_OBJECTS = [
    # Error logging
    (ErrorLog, "ErrorLog"),
    (SystemMetrics, "SystemMetrics"),
    
    # Session middleware
    (SessionMiddleware, "SessionMiddleware"),
    (FlashMessage, "FlashMessage"),
    (SessionStore, "SessionStore"),
    (FlashMessageType, "FlashMessageType"),
]


class TestServiceImportsCompleteness:
    """Test the completeness of service_imports.py."""
    
    def test_service_classes_exist(self):
        """Test that all service classes are properly exported."""
        for cls, name in SERVICE_CLASSES:
            assert cls is not None, f"{name} should be exported from service_imports.py"
            assert inspect.isclass(cls), f"{name} should be a class"
    
    def test_model_classes_exist(self):
        """Test that all model classes are properly exported."""
        for cls, name in MODEL_CLASSES:
            assert cls is not None, f"{name} should be exported from service_imports.py"
            assert inspect.isclass(cls), f"{name} should be a class"
    
    def test_enum_classes_exist(self):
        """Test that all enum classes are properly exported."""
        for cls, name in ENUM_CLASSES:
            assert cls is not None, f"{name} should be exported from service_imports.py"
            assert inspect.isclass(cls), f"{name} should be a class"
            assert issubclass(cls, Enum), f"{name} should be an Enum subclass"
    
    def test_error_classes_exist(self):
        """Test that all error classes are properly exported."""
        for cls, name in ERROR_CLASSES:
            assert cls is not None, f"{name} should be exported from service_imports.py"
            assert inspect.isclass(cls), f"{name} should be a class"
            assert issubclass(cls, Exception), f"{name} should be an Exception subclass"
    
    def test_functions_exist(self):
        """Test that all key functions are properly exported."""
        for func, name in KEY_FUNCTIONS:
            assert func is not None, f"{name} should be exported from service_imports.py"
            assert callable(func), f"{name} should be callable"
    
    def test_critical_objects_exist(self):
        """Test that critical objects for monitoring and middleware are exported."""
        for obj, name in CRITICAL_OBJECTS:
            assert obj is not None, f"{name} should be exported from service_imports.py"
    
    def test_service_instances_exist(self):
        """Test that pre-created service instances are exported."""
        assert material_service is not None, "material_service instance should be exported"
        assert p2p_service is not None, "p2p_service instance should be exported"
        assert monitor_service is not None, "monitor_service instance should be exported"
        assert state_manager is not None, "state_manager instance should be exported"
    
    def test_controller_functions_available(self):
        """Test that controller functions are properly exported."""
        # Material UI controller functions
        assert callable(create_material), "create_material should be exported"
        assert callable(get_material), "get_material should be exported"
        
        # Material API controller functions
        assert callable(api_get_material), "api_get_material should be exported"
        assert callable(api_update_material), "api_update_material should be exported"
        
        # P2P controller functions
        assert callable(api_list_orders), "api_list_orders should be exported"
        assert callable(api_create_order), "api_create_order should be exported"
        assert callable(api_create_requisition), "api_create_requisition should be exported"
        
        # Dashboard controller functions
        assert callable(get_system_health), "get_system_health should be exported"
        assert callable(get_p2p_statistics), "get_p2p_statistics should be exported"
        assert callable(get_recent_activities), "get_recent_activities should be exported"
    
    def test_session_functions_available(self):
        """Test that session middleware functions are properly exported."""
        assert callable(get_session), "get_session should be exported"
        assert callable(add_flash_message), "add_flash_message should be exported"
        assert callable(get_flash_messages), "get_flash_messages should be exported"
        assert callable(store_form_data), "store_form_data should be exported"
        assert callable(get_form_data), "get_form_data should be exported"
    
    def test_enums_have_expected_values(self):
        """Test that enums have the expected values."""
        # Check a sample of enum values to ensure they're correctly exported
        assert hasattr(MaterialStatus, "ACTIVE"), "MaterialStatus.ACTIVE should exist"
        assert hasattr(DocumentStatus, "DRAFT"), "DocumentStatus.DRAFT should exist"
        assert hasattr(HttpMethod, "GET"), "HttpMethod.GET should exist"
    
    def test_route_definitions_exist(self):
        """Test that route definitions are properly exported."""
        assert RouteDefinition is not None, "RouteDefinition should be exported"
        assert ALL_ROUTES is not None, "ALL_ROUTES should be exported"
    
    def test_data_layer_classes_exist(self):
        """Test that data layer classes are properly exported."""
        assert MaterialDataLayer is not None, "MaterialDataLayer should be exported"
        assert P2PDataLayer is not None, "P2PDataLayer should be exported"

if __name__ == "__main__":
    pytest.main(["-xvs", __file__]) 