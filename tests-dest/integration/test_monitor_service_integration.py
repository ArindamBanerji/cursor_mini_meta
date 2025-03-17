# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Critical imports that must be preserved
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

"""Standard test file imports and setup.

This snippet is automatically added to test files by SnippetForTests.py.
It provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration
3. Common test imports and fixtures
4. Service initialization support
"""

# Find project root dynamically
test_file = Path(__file__).resolve()
test_dir = test_file.parent

# Try to find project root by looking for main.py or known directories
project_root: Optional[Path] = None
for parent in [test_dir] + list(test_dir.parents):
    # Check for main.py as an indicator of project root
    if (parent / "main.py").exists():
        project_root = parent
        break
    # Check for typical project structure indicators
    if all((parent / d).exists() for d in ["services", "models", "controllers"]):
        project_root = parent
        break

# If we still don't have a project root, use parent of the tests-dest directory
if not project_root:
    # Assume we're in a test subdirectory under tests-dest
    for parent in test_dir.parents:
        if parent.name == "tests-dest":
            project_root = parent.parent
            break

# Add project root to path if found
if project_root and str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the test_import_helper
try:
    from test_import_helper import setup_test_paths
    setup_test_paths()
except ImportError:
    # Fall back if test_import_helper is not available
    if str(test_dir.parent) not in sys.path:
        sys.path.insert(0, str(test_dir.parent))
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root) if project_root else "")

# Common test imports
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Import common fixtures and services
try:
    from conftest import test_services
    from services.base_service import BaseService
    from services.monitor_service import MonitorService
    from services.template_service import TemplateService
    from services.p2p_service import P2PService
    from models.base_model import BaseModel
    from models.material import Material
    from models.requisition import Requisition
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
except ImportError as e:
    # Log import error but continue - not all tests need all imports
    import logging
    logging.warning(f"Optional import failed: {e}")
    logging.debug("Stack trace:", exc_info=True)
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

# tests-dest/integration/test_monitor_service_integration.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from unittest.mock import MagicMock, patch

from models.material import (
    Material, MaterialCreate, MaterialType, MaterialStatus
)
from services.material_service import MaterialService
from services.p2p_service import P2PService
from services.monitor_service import MonitorService
from services.state_manager import StateManager, state_manager
from services import (
    get_material_service, get_p2p_service, get_monitor_service,
    register_service, get_service,
    clear_service_registry, get_or_create_service, create_service_instance,
    reset_services
)
from utils.error_utils import NotFoundError, ValidationError


def setup_module(module):
    """Set up the test module by ensuring PYTEST_CURRENT_TEST is set"""
    logger.info("Setting up test module")
    os.environ["PYTEST_CURRENT_TEST"] = "True"
    
def teardown_module(module):
    """Clean up after the test module"""
    logger.info("Tearing down test module")
    if "PYTEST_CURRENT_TEST" in os.environ:
        del os.environ["PYTEST_CURRENT_TEST"]
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
        
        register_service("material", material_service)
        register_service("p2p", p2p_service)
        register_service("monitor", monitor_service)
        
        # Verify all services share the same state manager
        assert material_service.state_manager is custom_state
        assert p2p_service.state_manager is custom_state
        assert monitor_service.state_manager is custom_state
        
        # Test interaction between services
        try:
            # This should generate a not found error that gets logged
            material_service.get_material("NONEXISTENT")
        except NotFoundError:
            pass  # Expected exception
        
        # Verify the monitor service captured the error
        error_logs = monitor_service.get_error_logs()
        assert len(error_logs) >= 1
    
    def test_get_or_create_service_with_monitor(self):
        """Test the get_or_create_service function with monitor service"""
        # Clear the registry
        clear_service_registry()
        
        # Create a test state manager
        test_state = StateManager()
        
        # Get a service instance
        service1 = get_or_create_service(MonitorService, test_state)
        
        # Verify it's a MonitorService with our state manager
        assert isinstance(service1, MonitorService)
        assert service1.state_manager is test_state
        
        # Get it again
        service2 = get_or_create_service(MonitorService, state_manager)  # Different state manager
        
        # Verify we got the same instance despite different args
        assert service2 is service1
        
        # Verify the state manager wasn't changed
        assert service2.state_manager is test_state
    
    def test_create_service_instance_with_monitor(self):
        """Test the create_service_instance function with monitor service"""
        # Create a test state manager
        test_state = StateManager()
        
        # Create a service instance
        service1 = create_service_instance(MonitorService, test_state)
        
        # Create another instance
        service2 = create_service_instance(MonitorService, test_state)
        
        # Verify they are different instances
        assert service1 is not service2
        
        # Verify they both use our test state manager
        assert service1.state_manager is test_state
        assert service2.state_manager is test_state
    
    def test_reset_services_with_monitor(self):
        """Test the reset_services function including monitor service"""
        # Get the default services
        material_service = get_material_service()
        p2p_service = get_p2p_service()
        monitor_service = get_monitor_service()
        
        # Register the monitor service
        register_service("monitor", monitor_service)
        
        # Add something to the state
        material_service.create_material(
            MaterialCreate(
                material_number="RESET001",
                name="Reset Test Material"
            )
        )
        
        # Log an error
        monitor_service.log_error(
            error_type="reset_test",
            message="Error before reset",
            component="test"
        )
        
        # Verify we can retrieve the material
        material = material_service.get_material("RESET001")
        assert material.name == "Reset Test Material"
        
        # Verify we have the error log
        error_logs = monitor_service.get_error_logs()
        assert any(log.error_type == "reset_test" for log in error_logs)
        
        # Reset the services
        reset_services()
        
        # Get services again
        new_material_service = get_material_service()
        new_p2p_service = get_p2p_service()
        new_monitor_service = get_monitor_service()
        
        # Verify the state was cleared
        with pytest.raises(NotFoundError):
            new_material_service.get_material("RESET001")
        
        # Verify error logs were cleared
        new_error_logs = new_monitor_service.get_error_logs()
        assert not any(log.error_type == "reset_test" for log in new_error_logs)
        
        # The service instances themselves should be different after reset
        with pytest.raises(KeyError):
            get_service("monitor")
    
    def test_cross_service_monitoring_integration(self):
        """Test integration between monitor service and other services through the factory"""
        # Create a clean state
        test_state = StateManager()
        
        # Get services with our test state
        material_service = get_material_service(test_state)
        p2p_service = get_p2p_service(test_state)
        monitor_service = get_monitor_service(test_state)
        
        # Register services
        register_service("material", material_service)
        register_service("p2p", p2p_service)
        register_service("monitor", monitor_service)
        
        # Create a material
        material = material_service.create_material(
            MaterialCreate(
                material_number="MON001",
                name="Monitored Material"
            )
        )
        
        # Collect metrics (this should record the state after material creation)
        metrics = monitor_service.collect_current_metrics()
        
        # Verify metrics were collected
        assert metrics is not None
        
        # Check system health
        health_data = monitor_service.check_system_health()
        
        # Verify health check includes service status
        assert "components" in health_data
        assert "services" in health_data["components"]
        
        # Update component status
        monitor_service.update_component_status(
            "material_service", 
            "healthy", 
            {"count": material_service.data_layer.count()}
        )
        
        # Get component status
        material_status = monitor_service.get_component_status("material_service")
        
        # Verify status is updated
        assert material_status is not None
        assert material_status["status"] == "healthy"
        assert "details" in material_status
        assert "count" in material_status["details"]
        assert material_status["details"]["count"] >= 1
