# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Add this at the top of every test file
import os
import sys
from pathlib import Path

# Find project root dynamically
test_file = Path(__file__).resolve()
test_dir = test_file.parent

# Try to find project root by looking for main.py or known directories
project_root = None
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

# Add project root to path
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
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root))

# Now regular imports
import pytest
# Rest of imports follow
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

# tests-dest/integration/test_service_factory_integration.py
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
        
        # Get a P2P service with just the custom state
        p2p_service = get_p2p_service(custom_state)
        
        # Verify it's using our custom state manager
        assert p2p_service.state_manager is custom_state
        
        # Verify it's NOT using the default material service
        assert p2p_service.material_service is not get_material_service()
        
        # Verify the material service is using the same custom state
        assert p2p_service.material_service.state_manager is custom_state
    
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
