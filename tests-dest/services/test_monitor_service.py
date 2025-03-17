# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Critical imports that must be preserved
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, ModuleType

"""Standard test file imports and setup.

This snippet is automatically added to test files by SnippetForTests.py.
It provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration
3. Common test imports and fixtures
4. Service initialization support
5. Logging configuration
6. Test environment variable management
"""

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_project_root(test_dir: Path) -> Optional[Path]:
    """Find the project root directory.
    
    Args:
        test_dir: The directory containing the test file
        
    Returns:
        The project root directory or None if not found
    """
    try:
        # Try to find project root by looking for main.py or known directories
        for parent in [test_dir] + list(test_dir.parents):
            # Check for main.py as an indicator of project root
            if (parent / "main.py").exists():
                return parent
            # Check for typical project structure indicators
            if all((parent / d).exists() for d in ["services", "models", "controllers"]):
                return parent
        
        # If we still don't have a project root, use parent of the tests-dest directory
        for parent in test_dir.parents:
            if parent.name == "tests-dest":
                return parent.parent
                
        return None
    except Exception as e:
        logger.error(f"Error finding project root: {e}")
        return None

# Find project root dynamically
test_file = Path(__file__).resolve()
test_dir = test_file.parent
project_root = find_project_root(test_dir)

if project_root:
    logger.info(f"Project root detected at: {project_root}")
    
    # Add project root to path if found
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.info(f"Added {project_root} to Python path")
else:
    logger.warning("Could not detect project root")

# Import the test_import_helper
try:
    from test_import_helper import setup_test_paths
    setup_test_paths()
    logger.info("Successfully initialized test paths from test_import_helper")
except ImportError as e:
    # Fall back if test_import_helper is not available
    if str(test_dir.parent) not in sys.path:
        sys.path.insert(0, str(test_dir.parent))
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root) if project_root else "")
    logger.warning(f"Failed to import test_import_helper: {e}. Using fallback configuration.")

# Set up test environment variables
def setup_test_env() -> None:
    """Set up test environment variables."""
    try:
        os.environ.setdefault("PYTEST_CURRENT_TEST", "True")
        logger.info("Test environment variables initialized")
    except Exception as e:
        logger.error(f"Error setting up test environment: {e}")

def teardown_test_env() -> None:
    """Clean up test environment variables."""
    try:
        if "PYTEST_CURRENT_TEST" in os.environ:
            del os.environ["PYTEST_CURRENT_TEST"]
        logger.info("Test environment variables cleaned up")
    except KeyError:
        logger.warning("PYTEST_CURRENT_TEST was already removed")
    except Exception as e:
        logger.error(f"Error cleaning up test environment: {e}")

# Common test imports
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

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
    logger.info("Successfully imported test fixtures and services")
except ImportError as e:
    # Log import error but continue - not all tests need all imports
    logger.warning(f"Optional import failed: {e}")
    logger.debug("Stack trace:", exc_info=True)

# Register setup/teardown hooks
def setup_module(module: ModuleType) -> None:
    """Set up the test module.
    
    Args:
        module: The test module being set up
    """
    logger.info("Setting up test module")
    setup_test_env()

def teardown_module(module: ModuleType) -> None:
    """Tear down the test module.
    
    Args:
        module: The test module being torn down
    """
    logger.info("Tearing down test module")
    teardown_test_env()
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

# tests-dest/services/test_monitor_service.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import json
from unittest.mock import MagicMock, patch
import time
from datetime import datetime, timedelta

from services.monitor_service import MonitorService
from services.state_manager import StateManager
from services.monitor_errors import ErrorLog


def setup_module(module):
    """Set up the test module by ensuring PYTEST_CURRENT_TEST is set"""
    logger.info("Setting up test module")
    os.environ["PYTEST_CURRENT_TEST"] = "True"
    
def teardown_module(module):
    """Clean up after the test module"""
    logger.info("Tearing down test module")
    if "PYTEST_CURRENT_TEST" in os.environ:
        del os.environ["PYTEST_CURRENT_TEST"]
class TestMonitorService:
    """
    Test suite for the MonitorService class.
    """
    
    @pytest.fixture
    def mock_state_manager(self):
        """Mock state manager for testing."""
        state = StateManager()
        # Initialize with empty state
        state.set("system_metrics", [])
        state.set("error_logs", [])
        state.set("component_status", {})
        return state
    
    @pytest.fixture
    def monitor_service(self, mock_state_manager):
        """Create a monitor service instance with mock state manager."""
        return MonitorService(mock_state_manager)
    
    def test_update_component_status(self, monitor_service, mock_state_manager):
        """Test updating component status."""
        # Update a component's status
        component_name = "test_component"
        status = "healthy"
        details = {"version": "1.0.0"}
        
        monitor_service.update_component_status(component_name, status, details)
        
        # Verify the component status was stored
        component_status = mock_state_manager.get("component_status")
        assert component_name in component_status
        assert component_status[component_name]["status"] == status
        assert component_status[component_name]["details"] == details
        
        # Test getting the status
        status = monitor_service.get_component_status(component_name)
        assert status["status"] == "healthy"
        assert status["details"]["version"] == "1.0.0"
    
    def test_collect_current_metrics(self, monitor_service, mock_state_manager):
        """Test collecting current metrics."""
        # Collect metrics
        metrics = monitor_service.collect_current_metrics()
        
        # Verify metrics were collected and stored
        assert metrics is not None
        assert hasattr(metrics, 'cpu_percent')
        assert hasattr(metrics, 'memory_usage')
        assert hasattr(metrics, 'disk_usage')
        
        # Verify metrics were stored in state manager
        stored_metrics = mock_state_manager.get("system_metrics")
        assert len(stored_metrics) > 0
        assert "cpu_percent" in stored_metrics[0]
        assert "memory_usage" in stored_metrics[0]
        assert "disk_usage" in stored_metrics[0]
    
    def test_get_metrics_with_time_filter(self, monitor_service, mock_state_manager):
        """Test retrieving metrics with time filtering."""
        # Create test metrics at different times
        now = datetime.now()
        
        # Add old metrics (3 hours old)
        old_metrics = {
            "timestamp": (now - timedelta(hours=3)).isoformat(),
            "cpu_percent": 50.0,
            "memory_usage": 60.0,
            "available_memory": 8.0,
            "disk_usage": 70.0
        }
        
        # Add recent metrics (1 hour old)
        recent_metrics = {
            "timestamp": (now - timedelta(hours=1)).isoformat(),
            "cpu_percent": 40.0,
            "memory_usage": 50.0,
            "available_memory": 10.0,
            "disk_usage": 60.0
        }
        
        # Add very recent metrics (10 minutes old)
        very_recent_metrics = {
            "timestamp": (now - timedelta(minutes=10)).isoformat(),
            "cpu_percent": 30.0,
            "memory_usage": 40.0,
            "available_memory": 12.0,
            "disk_usage": 50.0
        }
        
        # Store metrics in state manager
        mock_state_manager.set("system_metrics", [old_metrics, recent_metrics, very_recent_metrics])
        
        # Get metrics for past 2 hours
        metrics = monitor_service.get_metrics(hours=2)
        
        # Should only include the recent and very recent metrics
        assert len(metrics) == 2
        # Metrics should be ordered by timestamp (oldest first)
        assert metrics[0].cpu_percent == 40.0
        assert metrics[1].cpu_percent == 30.0
    
    def test_get_metrics_summary(self, monitor_service, mock_state_manager):
        """Test getting metrics summary."""
        # Create test metrics
        now = datetime.now()
        metrics_list = [
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
        
        # Store metrics in state manager
        mock_state_manager.set("system_metrics", metrics_list)
        
        # Get metrics summary
        summary = monitor_service.get_metrics_summary()
        
        # Verify summary
        assert summary["count"] == 2
        assert "time_range" in summary
        assert "duration_hours" in summary["time_range"]
        assert "averages" in summary
        assert "maximums" in summary
        
        # Verify averages calculation
        assert summary["averages"]["cpu_percent"] == 40.0
        assert summary["averages"]["memory_usage_percent"] == 50.0
        assert summary["averages"]["disk_usage_percent"] == 60.0
        
        # Verify maximums calculation
        assert summary["maximums"]["cpu_percent"] == 50.0
        assert summary["maximums"]["memory_usage_percent"] == 60.0
        assert summary["maximums"]["disk_usage_percent"] == 70.0
    
    def test_log_error(self, monitor_service, mock_state_manager):
        """Test logging an error."""
        # Log an error
        error_type = "test_error"
        message = "This is a test error"
        component = "test_component"
        context = {"key": "value"}
        
        error_log = monitor_service.log_error(error_type, message, component, context)
        
        # Verify error log object
        assert error_log.error_type == error_type
        assert error_log.message == message
        assert error_log.component == component
        assert error_log.context == context
        
        # Verify error was stored in state manager
        stored_logs = mock_state_manager.get("error_logs")
        assert len(stored_logs) == 1
        
        stored_log = stored_logs[0]
        assert stored_log["error_type"] == error_type
        assert stored_log["message"] == message
        assert stored_log["component"] == component
        assert stored_log["context"] == context
    
    def test_get_error_logs_with_filters(self, monitor_service, mock_state_manager):
        """Test getting error logs with filtering."""
        # Create test error logs
        now = datetime.now()
        
        # Create logs with different timestamps, types, and components
        logs = [
            {
                "error_type": "validation_error",
                "message": "Error 1",
                "timestamp": (now - timedelta(hours=3)).isoformat(),
                "component": "component_a",
                "context": {}
            },
            {
                "error_type": "not_found_error",
                "message": "Error 2",
                "timestamp": (now - timedelta(hours=2)).isoformat(),
                "component": "component_b",
                "context": {}
            },
            {
                "error_type": "validation_error",
                "message": "Error 3",
                "timestamp": (now - timedelta(hours=1)).isoformat(),
                "component": "component_a",
                "context": {}
            }
        ]
        
        # Store logs in state manager
        mock_state_manager.set("error_logs", logs)
        
        # Test filtering by time (last 2 hours)
        time_filtered = monitor_service.get_error_logs(hours=2)
        assert len(time_filtered) == 2
        assert time_filtered[0].message == "Error 3"  # Most recent first
        assert time_filtered[1].message == "Error 2"
        
        # Test filtering by error type
        type_filtered = monitor_service.get_error_logs(error_type="validation_error")
        assert len(type_filtered) == 2
        assert type_filtered[0].message == "Error 3"  # Most recent first
        assert type_filtered[1].message == "Error 1"
        
        # Test filtering by component
        component_filtered = monitor_service.get_error_logs(component="component_a")
        assert len(component_filtered) == 2
        assert component_filtered[0].message == "Error 3"  # Most recent first
        assert component_filtered[1].message == "Error 1"
        
        # Test combined filtering (validation errors from component_a in the last 2 hours)
        combined_filtered = monitor_service.get_error_logs(
            error_type="validation_error", 
            component="component_a",
            hours=2
        )
        assert len(combined_filtered) == 1
        assert combined_filtered[0].message == "Error 3"
    
    def test_get_error_summary(self, monitor_service, mock_state_manager):
        """Test getting error summary."""
        # Create test error logs
        now = datetime.now()
        logs = [
            {
                "error_type": "validation_error",
                "message": "Error 1",
                "timestamp": (now - timedelta(hours=2)).isoformat(),
                "component": "component_a",
                "context": {}
            },
            {
                "error_type": "not_found_error",
                "message": "Error 2",
                "timestamp": (now - timedelta(hours=1)).isoformat(),
                "component": "component_b",
                "context": {}
            },
            {
                "error_type": "validation_error",
                "message": "Error 3",
                "timestamp": now.isoformat(),
                "component": "component_a",
                "context": {}
            }
        ]
        
        # Store logs in state manager
        mock_state_manager.set("error_logs", logs)
        
        # Get error summary
        summary = monitor_service.get_error_summary()
        
        # Verify summary
        assert summary["count"] == 3
        assert "time_range" in summary
        assert "by_type" in summary
        assert "by_component" in summary
        assert "recent" in summary
        
        # Verify error counts by type
        assert summary["by_type"]["validation_error"] == 2
        assert summary["by_type"]["not_found_error"] == 1
        
        # Verify error counts by component
        assert summary["by_component"]["component_a"] == 2
        assert summary["by_component"]["component_b"] == 1
        
        # Verify recent errors (should be in reverse chronological order)
        assert len(summary["recent"]) <= 5
        assert summary["recent"][0]["message"] == "Error 3"
        assert summary["recent"][1]["message"] == "Error 2"
        assert summary["recent"][2]["message"] == "Error 1"
    
    def test_clear_error_logs(self, monitor_service, mock_state_manager):
        """Test clearing error logs."""
        # Create test error logs
        logs = [
            {
                "error_type": "test_error",
                "message": "Test error",
                "timestamp": datetime.now().isoformat(),
                "component": "test_component",
                "context": {}
            }
        ]
        
        # Store logs in state manager
        mock_state_manager.set("error_logs", logs)
        
        # Verify logs exist
        assert len(mock_state_manager.get("error_logs")) == 1
        
        # Clear logs
        count = monitor_service.clear_error_logs()
        
        # Verify logs were cleared
        assert count == 1
        assert len(mock_state_manager.get("error_logs")) == 0
    
    def test_check_system_health(self, monitor_service):
        """Test checking system health."""
        # Check health
        health_data = monitor_service.check_system_health()
        
        # Verify health data structure
        assert "status" in health_data
        assert "timestamp" in health_data
        assert "response_time_ms" in health_data
        assert "components" in health_data
        
        # Verify components are included
        components = health_data["components"]
        assert "database" in components
        assert "services" in components
        assert "disk" in components
        assert "memory" in components
        
        # Verify system info is included
        assert "system_info" in health_data
    
    def test_handling_of_invalid_error_logs(self, monitor_service, mock_state_manager):
        """Test handling of invalid error log entries."""
        # Create test error logs with some invalid entries
        now = datetime.now()
        logs = [
            {
                "error_type": "valid_error",
                "message": "Valid error",
                "timestamp": now.isoformat(),
                "component": "test_component",
                "context": {}
            },
            {
                # Missing required fields
                "error_type": "incomplete_error"
            },
            {
                "error_type": "invalid_timestamp",
                "message": "Error with invalid timestamp",
                "timestamp": "not-a-timestamp",
                "component": "test_component",
                "context": {}
            }
        ]
        
        # Store logs in state manager
        mock_state_manager.set("error_logs", logs)
        
        # Get error logs - should handle invalid entries gracefully
        error_logs = monitor_service.get_error_logs()
        
        # Should have at least the valid error
        assert len(error_logs) >= 1
        
        # The valid error should be correctly parsed
        valid_log = next((log for log in error_logs if log.error_type == "valid_error"), None)
        assert valid_log is not None
        assert valid_log.message == "Valid error"
    
    def test_handling_null_state(self, monitor_service, mock_state_manager):
        """Test handling of null state in the state manager."""
        # Set state to None to simulate corrupted state
        mock_state_manager.set("system_metrics", None)
        mock_state_manager.set("error_logs", None)
        mock_state_manager.set("component_status", None)
        
        # These operations should not raise exceptions
        metrics = monitor_service.get_metrics()
        assert isinstance(metrics, list)
        
        error_logs = monitor_service.get_error_logs()
        assert isinstance(error_logs, list)
        
        # Should initialize empty lists
        assert len(metrics) == 0
        assert len(error_logs) == 0
        
        # Should still be able to store new data
        monitor_service.collect_current_metrics()
        monitor_service.log_error("test_error", "Test error")
        
        # Verify data was stored
        assert len(mock_state_manager.get("system_metrics")) > 0
        assert len(mock_state_manager.get("error_logs")) > 0
