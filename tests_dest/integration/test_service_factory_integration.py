# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Critical imports that must be preserved
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from types import ModuleType
from datetime import datetime

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
    MaterialService,
    MonitorService,
    P2PService,
    TemplateService,
    Material,
    MaterialCreate,
    MaterialType,
    MaterialStatus,
    Requisition,
    NotFoundError,
    ValidationError,
    create_test_monitor_service,
    create_test_state_manager,
    setup_exception_handlers,
    register_service,
    clear_service_registry,
    get_material_service,
    get_p2p_service,
    get_monitor_service,
    state_manager
)

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment for each test."""
    setup_test_env_vars(monkeypatch)
    logger.info("Test environment initialized")
    yield
    logger.info("Test environment cleaned up")
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

class TestServiceFactoryIntegration:
    """
    Tests for the service factory and registry mechanisms.
    """
    
    def setup_method(self):
        """Set up test environment before each test"""
        # Clear the service registry to ensure a clean state
        clear_service_registry()
    
    def test_get_material_service_default(self):
        """Test getting the default material service singleton"""
        # Get the material service
        material_service = get_material_service()
        
        # Get it again
        material_service2 = get_material_service()
        
        # Verify we got the same instance both times
        assert material_service is material_service2
        
        # Verify it's using the default state manager
        assert material_service.state_manager is state_manager
    
    def test_get_material_service_with_custom_state(self):
        """Test getting a material service with a custom state manager"""
        # Create a custom state manager
        custom_state = StateManager()
        
        # Get a material service with the custom state manager
        material_service = get_material_service(custom_state)
        
        # Verify it's using our custom state manager
        assert material_service.state_manager is custom_state
        
        # Verify it's NOT the same as the default service
        assert material_service is not get_material_service()
    
    def test_get_p2p_service_default(self):
        """Test getting the default P2P service singleton"""
        # Get the P2P service
        p2p_service = get_p2p_service()
        
        # Get it again
        p2p_service2 = get_p2p_service()
        
        # Verify we got the same instance both times
        assert p2p_service is p2p_service2
        
        # Verify it's using the default state manager
        assert p2p_service.state_manager is state_manager
        
        # Verify it's using the default material service
        assert p2p_service.material_service is get_material_service()
    
    def test_get_p2p_service_with_deps(self):
        """Test getting a P2P service with custom dependencies"""
        # Create a custom state manager
        custom_state = StateManager()
        
        # Create a mock material service
        mock_material_service = MagicMock()
        
        # Get a P2P service with custom dependencies
        p2p_service = get_p2p_service(custom_state, mock_material_service)
        
        # Verify it's using our custom dependencies
        assert p2p_service.state_manager is custom_state
        assert p2p_service.material_service is mock_material_service
        
        # Verify it's NOT the same as the default service
        assert p2p_service is not get_p2p_service()
    
    def test_get_p2p_service_with_state_only(self):
        """Test getting a P2P service with just a custom state manager"""
        # Create a custom state manager
        custom_state = StateManager()
        
        # Set a test value in the custom state
        test_key = "test_p2p_with_state"
        test_value = {"initialized": True, "timestamp": datetime.now().isoformat()}
        custom_state.set(test_key, test_value)
        
        # Create a material service with the same state
        custom_material_service = get_material_service(custom_state)
        
        # Get a P2P service with the custom state and material service
        p2p_service = get_p2p_service(custom_state, custom_material_service)
        
        # Verify it's using our custom state manager by checking if it can access our test value
        assert p2p_service.state_manager.get(test_key) == test_value
        
        # Verify the material service can access the same state
        assert p2p_service.material_service.state_manager.get(test_key) == test_value
        
        # Verify the material service is our custom instance
        assert p2p_service.material_service is custom_material_service
        
        # Add another test value through the P2P service's state manager
        p2p_key = "test_p2p_set" 
        p2p_value = {"service": "p2p", "test": True}
        p2p_service.state_manager.set(p2p_key, p2p_value)
        
        # Verify we can access it through the material service's state manager too
        assert custom_material_service.state_manager.get(p2p_key) == p2p_value
    
    def test_get_p2p_service_with_material_only(self):
        """Test getting a P2P service with just a custom material service"""
        # Create a mock material service
        mock_material_service = MagicMock()
        
        # Get a P2P service with just the custom material service
        p2p_service = get_p2p_service(material_service_instance=mock_material_service)
        
        # Verify it's using our mock material service
        assert p2p_service.material_service is mock_material_service
        
        # Verify it's using the default state manager
        assert p2p_service.state_manager is state_manager
    
    # New tests for Monitor Service factory function
    
    def test_get_monitor_service_default(self):
        """Test getting the default monitor service singleton"""
        # Get the monitor service
        monitor_service = get_monitor_service()
        
        # Get it again
        monitor_service2 = get_monitor_service()
        
        # Verify we got the same instance both times
        assert monitor_service is monitor_service2
        
        # Verify it's using the default state manager
        assert monitor_service.state_manager is state_manager
    
    def test_get_monitor_service_with_custom_state(self):
        """Test getting a monitor service with a custom state manager"""
        # Create a custom state manager
        custom_state = StateManager()
        
        # Get a monitor service with the custom state manager
        monitor_service = get_monitor_service(custom_state)
        
        # Verify it's using our custom state manager
        assert monitor_service.state_manager is custom_state
        
        # Verify it's NOT the same as the default service
        assert monitor_service is not get_monitor_service()
        
        # Verify it initialized correctly by collecting metrics
        metrics = monitor_service.collect_current_metrics()
        assert metrics is not None
        assert hasattr(metrics, 'cpu_percent')
        assert hasattr(metrics, 'memory_usage')
    
    def test_monitor_service_preserves_state(self):
        """Test that the monitor service correctly preserves state between instances"""
        # Create a custom state manager
        custom_state = StateManager()
        
        # Get a monitor service with the custom state manager
        monitor_service1 = get_monitor_service(custom_state)
        
        # Log an error
        test_error = monitor_service1.log_error(
            error_type="test_error",
            message="Test error for state preservation",
            component="test_component"
        )
        
        # Get another monitor service with the same state manager
        monitor_service2 = get_monitor_service(custom_state)
        
        # Verify the error is accessible from the second instance
        error_logs = monitor_service2.get_error_logs()
        assert len(error_logs) >= 1
        
        found_test_error = False
        for error in error_logs:
            if (error.error_type == "test_error" and 
                "Test error for state preservation" in error.message):
                found_test_error = True
                break
        
        assert found_test_error, "Test error not found in error logs from second instance"
