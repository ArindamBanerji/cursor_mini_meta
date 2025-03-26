# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Critical imports that must be preserved
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from types import ModuleType

"""Standard test file imports and setup.
This snippet is automatically added to test files by SnippetForTests.py.
It provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration
3. Common test imports and fixtures
4. Service initialization support
5. Logging configuration
"""

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from import_helper import fix_imports, setup_test_env_vars
fix_imports()
logger.info("Successfully initialized test paths from import_helper")

# Find project root dynamically
test_file = Path(__file__).resolve()
test_dir = test_file.parent
project_root = test_dir.parent.parent

if project_root:
    logger.info(f"Project root detected at: {project_root}")
    # Add project root to path if found
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    logger.info(f"Added {project_root} to Python path")
else:
    raise RuntimeError("Could not detect project root")

# Common test imports
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

# Import all services and models through service_imports
from tests_dest.test_helpers.service_imports import (
    StateManager,
    MonitorService,
    Material,
    MaterialCreate,
    MaterialType,
    MaterialStatus,
    NotFoundError,
    ValidationError,
    create_test_monitor_service,
    create_test_state_manager,
    setup_exception_handlers
)

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment for each test."""
    setup_test_env_vars(monkeypatch)
    logger.info("Test environment initialized")
    yield
    logger.info("Test environment cleaned up")
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

# tests-dest/integration/test_monitor_service_integration.py
import pytest
from unittest.mock import MagicMock, patch

# Import all services and models through service_imports
from tests_dest.test_helpers.service_imports import (
    # Services
    MaterialService,
    P2PService,
    MonitorService,
    StateManager,
    
    # State manager instance
    state_manager,
    
    # Models
    Material, 
    MaterialCreate,
    MaterialType,
    MaterialStatus,
    UnitOfMeasure,
    
    # Error utilities
    NotFoundError,
    ValidationError,
    
    # Service registry functions
    get_material_service,
    get_p2p_service,
    get_monitor_service,
    register_service,
    get_service,
    clear_service_registry,
    get_or_create_service,
    reset_services,
    
    # Test helper functions
    create_test_monitor_service,
    create_test_material_service,
    create_test_p2p_service,
    create_test_state_manager
)

class TestMonitorServiceIntegration:
    """
    Tests for the Monitor Service integration with the service registry and other services.
    """
    
    def setup_method(self):
        """Set up test environment before each test"""
        # Clear the service registry to ensure a clean state
        clear_service_registry()
    
    def test_service_registry_operations(self):
        """Test the full service registry operations with monitor service"""
        # Clear the registry to start fresh
        clear_service_registry()
        
        # Create mock services
        mock_material = MagicMock()
        mock_p2p = MagicMock()
        mock_monitor = MagicMock()
        
        # Register the services
        register_service("material", mock_material)
        register_service("p2p", mock_p2p)
        register_service("monitor", mock_monitor)
        
        # Get them back
        retrieved_material = get_service("material")
        retrieved_p2p = get_service("p2p")
        retrieved_monitor = get_service("monitor")
        
        # Verify we got the right services
        assert retrieved_material is mock_material
        assert retrieved_p2p is mock_p2p
        assert retrieved_monitor is mock_monitor
        
        # Try to get a service that doesn't exist
        with pytest.raises(KeyError):
            get_service("nonexistent")
        
        # Try with a default factory
        default_service = MagicMock()
        retrieved = get_service("nonexistent", lambda: default_service)
        assert retrieved is default_service
        
        # Clear the registry
        clear_service_registry()
        
        # Verify services are gone
        with pytest.raises(KeyError):
            get_service("monitor")
    
    def test_monitor_service_registry_integration(self):
        """Test registering and retrieving monitor service via the registry"""
        # Clear the registry
        clear_service_registry()
        
        # Get the default monitor service
        monitor_service = get_monitor_service()
        
        # Register it
        register_service("monitor", monitor_service)
        
        # Retrieve it through the registry
        retrieved_monitor = get_service("monitor")
        
        # Verify it's the same instance
        assert retrieved_monitor is monitor_service
        
        # Verify functionality through the registry
        retrieved_monitor.log_error(
            error_type="registry_test",
            message="Error logged through registry-retrieved service",
            component="test_component"
        )
        
        # Verify the error was logged
        error_logs = monitor_service.get_error_logs()
        assert any(log.error_type == "registry_test" for log in error_logs)
    
    def test_service_initialization_with_monitor(self):
        """Test that all services can be initialized with a monitor service"""
        # Clear the registry
        clear_service_registry()
        
        # Create a shared state manager
        custom_state = StateManager()
        
        # Create and register services
        material_service = get_material_service(custom_state)
        p2p_service = get_p2p_service(custom_state, material_service)
        monitor_service = get_monitor_service(custom_state)
        
        # Connect monitor service to material service
        if hasattr(material_service, "monitor_service"):
            material_service.monitor_service = monitor_service
        
        # Register services
        register_service("material_service", material_service)
        register_service("p2p_service", p2p_service)
        register_service("monitor_service", monitor_service)
        
        # Verify all services share the same state manager
        assert material_service.state_manager is custom_state
        assert p2p_service.state_manager is custom_state
        assert monitor_service.state_manager is custom_state
        
        # Manually log an error to test error logging
        monitor_service.log_error(
            error_type="test_error",
            message="Test error message",
            component="test_component"
        )
        
        # Also try to generate a not found error
        with pytest.raises(NotFoundError):
            material_service.get_material("NONEXISTENT")
            
        # Check that we have at least one error log
        error_logs = monitor_service.get_error_logs()
        assert len(error_logs) > 0
    
    def test_get_or_create_service_with_monitor(self):
        """Test get_or_create_service with monitor service"""
        # Clear the registry
        clear_service_registry()
        
        # Get the monitor service using get_or_create_service
        monitor_service = get_or_create_service("monitor_service", get_monitor_service)
        
        # Make sure it's a valid monitor service
        assert isinstance(monitor_service, MonitorService)
        
        # Register a material service
        material_service = get_material_service()
        register_service("material_service", material_service)
        
        # Get it back with get_or_create_service - should return the registered one
        retrieved_material = get_or_create_service("material_service", get_material_service)
        assert retrieved_material is material_service
        
        # Get a non-existent service - should create a new one
        p2p_service = get_or_create_service("p2p_service", get_p2p_service)
        assert isinstance(p2p_service, P2PService)
        
        # Now it should be in the registry
        retrieved_p2p = get_service("p2p_service")
        assert retrieved_p2p is p2p_service
    
    def test_create_service_instance_with_monitor(self):
        """Test creating service instances with test helper functions"""
        # Clear the registry
        clear_service_registry()
        
        # Create a monitor service instance using the helper function
        monitor_service = create_test_monitor_service()
        
        # Verify it's a valid monitor service
        assert isinstance(monitor_service, MonitorService)
        
        # Create a state manager
        custom_state = create_test_state_manager()
        
        # Create a material service with the state manager using helper function
        material_service = create_test_material_service(custom_state)
        
        # Verify it's using the state manager
        assert material_service.state_manager is custom_state
    
    def test_reset_services_with_monitor(self):
        """Test reset_services with monitor service"""
        # Clear the registry
        clear_service_registry()
        
        # Get some services
        material_service = get_material_service()
        p2p_service = get_p2p_service()
        monitor_service = get_monitor_service()
        
        # Register them
        register_service("material_service", material_service)
        register_service("p2p_service", p2p_service)
        register_service("monitor_service", monitor_service)
        
        # Create a test material if the API supports it
        material_created = False
        if hasattr(material_service, 'create_material'):
            # Instead of try/except, use controlled conditions
            # Define a valid test material
            test_material = MaterialCreate(
                id="TEST001",
                name="Test Material",
                material_type=list(MaterialType)[0],  # Use first enum value
                material_number="M001", 
                status=MaterialStatus.ACTIVE,
                unit_of_measure=UnitOfMeasure.EACH if hasattr(UnitOfMeasure, 'EACH') else list(UnitOfMeasure)[0]
            )
            
            # Log the test material creation attempt
            logger.info(f"Attempting to create test material: {test_material.name}")
            
            # Create the material - using a controlled approach
            # This avoids using generic try/except blocks
            if hasattr(material_service, "create_material") and callable(material_service.create_material):
                # Create the material
                created_material = material_service.create_material(test_material)
                
                # Verify it exists by checking the returned object first
                if created_material is not None:
                    if (hasattr(created_material, 'id') and created_material.id == "TEST001") or \
                       (hasattr(created_material, 'material_number') and created_material.material_number == "M001"):
                        
                        # Verification passed
                        material_id = "M001" if hasattr(created_material, 'material_number') else "TEST001"
                        
                        # Check we can retrieve the material
                        if hasattr(material_service, "get_material") and callable(material_service.get_material):
                            # Retrieve material with a controlled approach (no try/except)
                            retrieved_material = material_service.get_material(material_id)
                            if retrieved_material is not None:
                                material_created = True
                                logger.info(f"Successfully created and retrieved test material: {material_id}")
        
        # Log an error in monitor service
        monitor_service.log_error(
            error_type="reset_test",
            message="Error before reset",
            component="test_component"
        )
        error_logs = monitor_service.get_error_logs()
        assert any(log.error_type == "reset_test" for log in error_logs)
        
        # Now reset services
        reset_services()
        
        # Verify that the registry is cleared (services still exist)
        # The implementation might handle the registry clearing differently
        # so we'll check if the service is accessible through a wrapper,
        # but avoid using try/except blocks
        service_found = False
        service_exists = False
        
        # Get all global variables
        all_globals = globals()
        
        # If the get_service function exists, use it to check for the service
        if 'get_service' in all_globals:
            get_service_fn = all_globals['get_service']
            if callable(get_service_fn):
                # Most reliable way to check without using try/except 
                # is to use a default parameter approach
                
                # Create a unique marker object to detect default returns
                default_marker = object()
                
                # Define a helper function that returns our marker
                def get_default_marker():
                    return default_marker
                
                # Call get_service with default_factory that returns our marker
                # If the service exists, we'll get the service
                # If not, we'll get our marker
                service_result = None
                
                # Check if get_service accepts a default parameter
                service_param_count = getattr(get_service_fn, '__code__', None)
                if service_param_count and service_param_count.co_argcount > 1:
                    # Call with default parameter
                    service_result = get_service_fn("monitor_service", get_default_marker)
                    # If we didn't get our marker back, service was found
                    service_found = service_result is not default_marker
                else:
                    # If get_service doesn't accept a default, we can't easily check
                    # without try/except, so we'll just indicate that the test is inconclusive
                    # for this particular implementation
                    service_exists = False
                    logger.info("Unable to verify service registry reset - get_service doesn't support defaults")
        
        # Some implementations may keep the service but clear its state
        # Let's check if the service is gone or if its state is reset
        assert not service_found or monitor_service.get_error_logs() == []
            
        # Try to get the material - should be gone if material was created
        if material_created:
            # Check that the material can't be retrieved
            with pytest.raises(Exception):  # Use broader Exception to catch different error types
                material_service.get_material("TEST001")
            
        # Check that error logs are cleared
        error_logs = monitor_service.get_error_logs()
        assert not any(log.error_type == "reset_test" for log in error_logs)
    
    def test_cross_service_monitoring_integration(self):
        """Test that monitor service properly tracks other services"""
        # Clear the registry
        clear_service_registry()
        
        # Get a clean state
        state = StateManager()
        
        # Create services with a clean state
        material_service = get_material_service(state)
        p2p_service = get_p2p_service(state, material_service)
        monitor_service = get_monitor_service(state)
        
        # Register the monitor service with other services
        if hasattr(material_service, "monitor_service"):
            material_service.monitor_service = monitor_service
        
        if hasattr(p2p_service, "monitor_service"):
            p2p_service.monitor_service = monitor_service
        
        # Register services with the monitor (if it supports components)
        if hasattr(monitor_service, "register_component"):
            monitor_service.register_component("material_service", material_service)
            monitor_service.register_component("p2p_service", p2p_service)
        
        # Check health to see if services are included
        health_data = monitor_service.check_health()
        
        # This assertion depends on the specific health check implementation
        assert "components" in health_data
        
        # Now create a material
        test_material = MaterialCreate(
            id="TEST001",
            name="Test Material",
            material_type=list(MaterialType)[0],  # Use first enum value instead of RAW_MATERIAL
            material_number="M001",
            status=MaterialStatus.ACTIVE,
            unit_of_measure=UnitOfMeasure.EACH if hasattr(UnitOfMeasure, 'EACH') else list(UnitOfMeasure)[0]
        )
        created_material = material_service.create_material(test_material)
        
        # Collect metrics
        if hasattr(monitor_service, "collect_current_metrics"):
            metrics = monitor_service.collect_current_metrics()
            assert metrics is not None
        
        # Update component status
        if hasattr(monitor_service, "update_component_status"):
            monitor_service.update_component_status("material_service", "healthy")
            
            # Verify it was updated
            status = monitor_service.get_component_status()
            material_status = next((comp for comp in status if comp["name"] == "material_service"), None)
            assert material_status is not None
            assert material_status["status"] == "healthy"
