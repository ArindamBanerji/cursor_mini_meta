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
    from test_import_helper import setup_test_paths, setup_test_env_vars
    setup_test_paths()
    logger.info("Successfully initialized test paths from test_import_helper")
except ImportError as e:
    # Fall back if test_import_helper is not available
    if str(test_dir.parent) not in sys.path:
        sys.path.insert(0, str(test_dir.parent))
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root) if project_root else "")
    logger.warning(f"Failed to import test_import_helper: {e}. Using fallback configuration.")

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

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment for each test."""
    setup_test_env_vars(monkeypatch)
    logger.info("Test environment initialized")
    yield
    logger.info("Test environment cleaned up")
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

# tests-dest/monitoring/test_monitor_controller.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import logging
import os
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main import app
from controllers.monitor_controller import api_health_check, api_get_metrics, api_get_errors, api_collect_metrics
from services.monitor_service import SystemMetrics, ErrorLog, MonitorService
from services import get_monitor_service
from services.state_manager import state_manager

# Import our patched client
from monitoring.test_client_host_solution import PatchedRequestClient

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_monitor_controller")

# Create test client using our patched version
client = PatchedRequestClient(app)

# Set testing environment variable
os.environ["PYTEST_CURRENT_TEST"] = "True"

def reset_test_state():
    """Reset the state manager for tests"""
    logger.info("Resetting state for test")
    state_manager.clear()

class TestMonitorController:
    """
    Tests for the Monitor Controller API endpoints.
    """
    
    def setup_method(self):
        """Reset state before each test"""
        logger.info("Setting up test environment")
        reset_test_state()
        
        # Clear all existing metrics and errors
        monitor_service = get_monitor_service()
        state_manager.set("system_metrics", [])
        state_manager.set("error_logs", [])
        state_manager.set("component_status", {})
        
        # Verify test state is properly set up
        self.verify_test_environment()
    
    def verify_test_environment(self):
        """Verify the test environment is properly set up"""
        logger.info("Verifying test environment")
        
        # Verify state is cleared
        assert len(state_manager.get("system_metrics", [])) == 0, "Metrics state not cleared properly"
        assert len(state_manager.get("error_logs", [])) == 0, "Error logs state not cleared properly"
        assert len(state_manager.get("component_status", {})) == 0, "Component status state not cleared properly"
        
        # Verify test environment variable is set
        assert "PYTEST_CURRENT_TEST" in os.environ, "Test environment variable not set"
        
        # Verify monitor service can be instantiated
        monitor_service = get_monitor_service()
        assert monitor_service is not None, "Failed to get monitor service"
        
        logger.info("Test environment verified successfully")
    
    def test_health_check_endpoint(self):
        """Test the health check API endpoint"""
        logger.info("Testing health check endpoint")
        
        # Force services to have healthy status by adding component statuses directly
        monitor_service = get_monitor_service()
        component_status = {
            "database": {
                "name": "database",
                "status": "healthy",
                "last_check": datetime.now().isoformat(),
                "details": {"test": True}
            },
            "services": {
                "name": "services",
                "status": "healthy",
                "last_check": datetime.now().isoformat(),
                "details": {"test": True}
            },
            "disk": {
                "name": "disk",
                "status": "healthy",
                "last_check": datetime.now().isoformat(),
                "details": {"test": True}
            },
            "memory": {
                "name": "memory",
                "status": "healthy",
                "last_check": datetime.now().isoformat(),
                "details": {"test": True}
            }
        }
        state_manager.set("component_status", component_status)
        
        # Log current system state for debugging
        logger.info(f"Component status: {json.dumps(component_status, indent=2)}")
        
        # Make request to health check endpoint
        response = client.get("/api/v1/monitor/health")
        
        # Log the response for debugging
        logger.info(f"Health check response status: {response.status_code}")
        logger.info(f"Health check response: {json.dumps(response.json(), indent=2)}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert "timestamp" in data
        assert "response_time_ms" in data
        assert "components" in data
        assert "system_info" in data
        
        # Check component status
        assert "database" in data["components"]
        assert "services" in data["components"]
        assert "disk" in data["components"]
        assert "memory" in data["components"]
        
        # Check system info
        assert "platform" in data["system_info"]
        assert "python_version" in data["system_info"]
    
    def test_unhealthy_system_status(self):
        """Test health check with simulated unhealthy system"""
        logger.info("Testing unhealthy system status")
        
        # Mock monitor service to return error status
        monitor_service = get_monitor_service()
        
        # Create a component with error status
        component_status = {
            "database": {
                "name": "database",
                "status": "error",
                "last_check": datetime.now().isoformat(),
                "details": {"error": "Simulated error"}
            }
        }
        state_manager.set("component_status", component_status)
        
        # Log current system state for debugging
        logger.info(f"Component status: {json.dumps(component_status, indent=2)}")
        
        # Make request
        response = client.get("/api/v1/monitor/health")
        
        # Log the response for debugging
        logger.info(f"Unhealthy system response status: {response.status_code}")
        logger.info(f"Unhealthy system response: {json.dumps(response.json(), indent=2)}")
        
        # Verify response indicating error
        assert response.status_code == 503  # Service Unavailable
        data = response.json()
        assert data["status"] == "error"
        
    def test_warning_system_status(self):
        """Test health check with warning system status"""
        logger.info("Testing warning system status")
        
        # Create a component with warning status
        monitor_service = get_monitor_service()
        
        component_status = {
            "disk": {
                "name": "disk",
                "status": "warning",
                "last_check": datetime.now().isoformat(),
                "details": {"percent_free": 8}  # Low disk space
            }
        }
        state_manager.set("component_status", component_status)
        
        # Log current system state for debugging
        logger.info(f"Component status: {json.dumps(component_status, indent=2)}")
        
        # Make request
        response = client.get("/api/v1/monitor/health")
        
        # Log the response for debugging
        logger.info(f"Warning system response status: {response.status_code}")
        logger.info(f"Warning system response: {json.dumps(response.json(), indent=2)}")
        
        # Verify response indicating warning
        assert response.status_code == 429  # Too Many Requests (used for warnings)
        data = response.json()
        assert data["status"] == "warning"
    
    def test_get_metrics_endpoint_with_no_data(self):
        """Test get metrics when no metrics are available"""
        logger.info("Testing get metrics with no data")
        
        # Make request to metrics endpoint
        response = client.get("/api/v1/monitor/metrics")
        
        # Log response for debugging
        logger.info(f"Get metrics response: {json.dumps(response.json(), indent=2)}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert data["success"] is True
        assert "count" in data["data"]
        assert data["data"]["count"] == 0
        assert "message" in data["data"]
    
    def test_get_metrics_endpoint_with_data(self):
        """Test get metrics with some data available"""
        logger.info("Testing get metrics with data")
        
        # Create test metrics
        monitor_service = get_monitor_service()
        
        # Mock collect_current_metrics to return our test data
        with patch.object(monitor_service.metrics, 'collect_current_metrics') as mock_collect:
            # First metrics
            metrics1 = SystemMetrics()
            metrics1.cpu_percent = 10.5
            metrics1.memory_usage = 45.2
            metrics1.available_memory = 4.2
            metrics1.disk_usage = 65.8
            
            # Second metrics
            metrics2 = SystemMetrics()
            metrics2.cpu_percent = 15.3
            metrics2.memory_usage = 52.1
            metrics2.available_memory = 3.8
            metrics2.disk_usage = 66.4
            
            # Configure mock to return our metrics in sequence
            mock_collect.side_effect = [metrics1, metrics2]
            
            # Collect metrics twice using the public interface
            monitor_service.collect_current_metrics()
            monitor_service.collect_current_metrics()
            
            # Verify metrics were stored
            stored_metrics = state_manager.get("system_metrics", [])
            logger.info(f"Stored {len(stored_metrics)} metrics")
            
            # Make request
            response = client.get("/api/v1/monitor/metrics")
            
            # Log response for debugging
            logger.info(f"Get metrics with data response: {json.dumps(response.json(), indent=2)}")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            # Verify structure and content
            assert data["success"] is True
            assert data["data"]["count"] == 2
            assert "averages" in data["data"]
            assert "maximums" in data["data"]
            assert "time_range" in data["data"]
            
            # Check averages
            assert abs(data["data"]["averages"]["cpu_percent"] - 12.9) < 0.1
            assert abs(data["data"]["averages"]["memory_usage_percent"] - 48.65) < 0.1
            
            # Check maximums
            assert abs(data["data"]["maximums"]["cpu_percent"] - 15.3) < 0.1
            assert abs(data["data"]["maximums"]["memory_usage_percent"] - 52.1) < 0.1
    
    def test_get_metrics_with_time_filter(self):
        """Test get metrics with time filter parameter"""
        logger.info("Testing get metrics with time filter")
        
        # Create metrics at different times
        monitor_service = get_monitor_service()
        
        # Mock collect_current_metrics and datetime.now
        with patch.object(monitor_service.metrics, 'collect_current_metrics') as mock_collect, \
             patch('services.monitor_metrics.datetime') as mock_datetime:
            # Set up our mock datetime
            current_time = datetime.now()
            mock_datetime.now.return_value = current_time
            
            # Create old metrics (3 hours ago)
            old_metrics = SystemMetrics()
            old_metrics.timestamp = current_time - timedelta(hours=3)
            old_metrics.cpu_percent = 20.0
            
            # Create recent metrics
            recent_metrics = SystemMetrics()
            recent_metrics.cpu_percent = 10.0
            recent_metrics.timestamp = current_time
            
            # Configure mock to return our metrics in sequence
            mock_collect.side_effect = [old_metrics, recent_metrics]
            
            # First collection (old metrics)
            mock_datetime.now.return_value = current_time - timedelta(hours=3)
            monitor_service.collect_current_metrics()
            
            # Second collection (recent metrics)
            mock_datetime.now.return_value = current_time
            monitor_service.collect_current_metrics()
            
            # Make request with 1 hour filter
            response = client.get("/api/v1/monitor/metrics?hours=1")
            
            # Log response for debugging
            logger.info(f"Get metrics with time filter response: {json.dumps(response.json(), indent=2)}")
            
            # Verify response only includes recent metrics
            assert response.status_code == 200
            data = response.json()
            
            assert data["success"] is True
            assert data["data"]["count"] == 1
            assert abs(data["data"]["averages"]["cpu_percent"] - 10.0) < 0.1
    
    def test_collect_metrics_endpoint(self):
        """Test metrics collection endpoint"""
        logger.info("Testing collect metrics endpoint")
        
        # Make request to collect metrics
        response = client.post("/api/v1/monitor/metrics/collect")
        
        # Log response for debugging
        logger.info(f"Collect metrics response: {json.dumps(response.json(), indent=2)}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert data["success"] is True
        assert "timestamp" in data["data"]
        assert "cpu_percent" in data["data"]
        assert "memory_usage" in data["data"]
        assert "available_memory" in data["data"]
        assert "disk_usage" in data["data"]
        
        # Verify a record was added to the metrics store
        monitor_service = get_monitor_service()
        metrics = state_manager.get("system_metrics", [])
        assert len(metrics) == 1
    
    @patch('services.monitor_service.MonitorService.collect_current_metrics')
    def test_collect_metrics_error_handling(self, mock_collect):
        """Test error handling in metrics collection endpoint"""
        logger.info("Testing collect metrics error handling")
        
        # Mock collection to raise an exception
        mock_collect.side_effect = Exception("Test error")
        
        # Make request
        response = client.post("/api/v1/monitor/metrics/collect")
        
        # Log response for debugging
        logger.info(f"Collect metrics error response: {response.status_code} - {response.text}")
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        
        assert data["success"] is False
        assert "error" in data
        assert data["error"] == "server_error"
        assert "Failed to collect metrics" in data["message"]
    
    def test_get_errors_endpoint_with_no_data(self):
        """Test get errors when no error logs exist"""
        logger.info("Testing get errors with no data")
        
        # Make request
        response = client.get("/api/v1/monitor/errors")
        
        # Log response for debugging
        logger.info(f"Get errors with no data response: {json.dumps(response.json(), indent=2)}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["count"] == 0
    
    def test_get_errors_endpoint_with_data(self):
        """Test get errors with error logs available"""
        logger.info("Testing get errors with data")
        
        # Create some test error logs
        monitor_service = get_monitor_service()
        
        # Add different types of errors
        monitor_service.log_error("validation_error", "Invalid input", "user_controller", {"field": "email"})
        monitor_service.log_error("database_error", "Connection failed", "data_layer", {"table": "users"})
        monitor_service.log_error("validation_error", "Missing field", "material_controller", {"field": "name"})
        
        # Verify errors were stored
        error_logs = state_manager.get("error_logs", [])
        logger.info(f"Stored {len(error_logs)} error logs")
        
        # Make request
        response = client.get("/api/v1/monitor/errors")
        
        # Log response for debugging
        logger.info(f"Get errors with data response: {json.dumps(response.json(), indent=2)}")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check structure and content
        assert data["success"] is True
        assert data["data"]["count"] == 3
        assert "by_type" in data["data"]
        assert "by_component" in data["data"]
        assert "recent" in data["data"]
        
        # Check error type counts
        assert data["data"]["by_type"]["validation_error"] == 2
        assert data["data"]["by_type"]["database_error"] == 1
        
        # Check component counts
        assert data["data"]["by_component"]["user_controller"] == 1
        assert data["data"]["by_component"]["data_layer"] == 1
        assert data["data"]["by_component"]["material_controller"] == 1
        
        # Check recent errors
        assert len(data["data"]["recent"]) <= 5
    
    def test_get_errors_with_filters(self):
        """Test get errors with filtering parameters"""
        logger.info("Testing get errors with filters")
        
        # Create some test error logs
        monitor_service = get_monitor_service()
        
        # Add different types of errors
        monitor_service.log_error("validation_error", "Invalid input", "user_controller", {"field": "email"})
        monitor_service.log_error("database_error", "Connection failed", "data_layer", {"table": "users"})
        monitor_service.log_error("validation_error", "Missing field", "material_controller", {"field": "name"})
        
        # Make request with filter by error_type
        response = client.get("/api/v1/monitor/errors?error_type=validation_error")
        
        # Log response for debugging
        logger.info(f"Get errors with type filter response: {json.dumps(response.json(), indent=2)}")
        
        # Verify filtered response
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "errors" in data["data"]
        assert len(data["data"]["errors"]) == 2
        assert data["data"]["count"] == 2
        
        # Verify all returned errors are validation errors
        for error in data["data"]["errors"]:
            assert error["error_type"] == "validation_error"
        
        # Make request with filter by component
        response = client.get("/api/v1/monitor/errors?component=data_layer")
        
        # Log response for debugging
        logger.info(f"Get errors with component filter response: {json.dumps(response.json(), indent=2)}")
        
        # Verify filtered response
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "errors" in data["data"]
        assert len(data["data"]["errors"]) == 1
        assert data["data"]["count"] == 1
        assert data["data"]["errors"][0]["component"] == "data_layer"
    
    def test_get_errors_with_time_filter(self):
        """Test error logs with time filter"""
        logger.info("Testing get errors with time filter")
        
        # Create error logs at different times
        monitor_service = get_monitor_service()
        
        # Create an old error log
        old_error = monitor_service.log_error(
            error_type="old_error",
            message="Old error message",
            component="test_component",
            context={"timestamp": (datetime.now() - timedelta(hours=5)).isoformat()}
        )
        
        # Create a recent error log
        recent_error = monitor_service.log_error(
            error_type="recent_error",
            message="Recent error message",
            component="test_component"
        )
        
        # Make request with 1 hour filter
        response = client.get("/api/v1/monitor/errors?hours=1")
        
        # Log response for debugging
        logger.info(f"Get errors with time filter response: {json.dumps(response.json(), indent=2)}")
        
        # Verify only recent error is returned
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "errors" in data["data"]
        assert len(data["data"]["errors"]) == 1
        assert data["data"]["errors"][0]["error_type"] == "recent_error"
    
    @patch('services.monitor_service.MonitorService.get_error_logs')
    def test_get_errors_error_handling(self, mock_get_logs):
        """Test error handling in get errors endpoint"""
        logger.info("Testing get errors error handling")
        
        # Mock error logs to raise an exception
        mock_get_logs.side_effect = Exception("Test error")
        
        # Make request
        response = client.get("/api/v1/monitor/errors")
        
        # Log response for debugging
        logger.info(f"Get errors error response: {response.status_code} - {response.text}")
        
        # Verify error response
        assert response.status_code == 500
        data = response.json()
        
        assert data["success"] is False
        assert "error" in data
        assert data["error"] == "server_error"
        assert "Failed to retrieve error logs" in data["message"]
