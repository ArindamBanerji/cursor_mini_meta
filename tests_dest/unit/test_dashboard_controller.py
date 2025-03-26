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
        # Add project root to path
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        logging.warning("Could not find import_helper.py. Using fallback configuration.")
except Exception as e:
    logging.warning(f"Failed to import import_helper: {{e}}. Using fallback configuration.")
    # Add project root to path
    current_file = Path(__file__).resolve()
    test_dir = current_file.parent.parent
    project_root = test_dir.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

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

# tests-dest/unit/test_dashboard_controller.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request
from fastapi.responses import RedirectResponse
from controllers.dashboard_controller import show_dashboard, redirect_to_dashboard, get_p2p_statistics, get_system_health, get_recent_activities
from controllers import BaseController
from datetime import datetime, timedelta

class TestDashboardController:
    def setup_method(self):
        # Create a mock request
        self.mock_request = MagicMock(spec=Request)
    
    @pytest.mark.asyncio
    async def test_show_dashboard(self):
        """Test that show_dashboard returns the expected context with state data"""
        # Mock the state manager
        with patch('controllers.dashboard_controller.state_manager') as mock_state_manager, \
             patch('controllers.dashboard_controller.get_p2p_statistics') as mock_get_p2p, \
             patch('controllers.dashboard_controller.get_system_health') as mock_get_health, \
             patch('controllers.dashboard_controller.get_recent_activities') as mock_get_activities:
            
            # Configure the mocks to return specific values
            mock_state_manager.get.side_effect = lambda key, default=None: {
                "dashboard_visits": 5,
                "last_dashboard_visit": "2023-01-01 12:00:00"
            }.get(key, default)
            
            mock_get_p2p.return_value = {"total_requisitions": 10}
            mock_get_health.return_value = {"status": "healthy"}
            mock_get_activities.return_value = [{"message": "Test activity"}]
            
            # Call the controller method
            result = await show_dashboard(self.mock_request)
            
            # Check the result is a dict with expected keys
            assert isinstance(result, dict)
            assert "welcome_message" in result
            assert "visit_count" in result
            assert "last_visit" in result
            assert "current_time" in result
            assert "p2p_stats" in result
            assert "system_health" in result
            assert "recent_activities" in result
            
            # Check specific values
            assert result["welcome_message"] == "Welcome to the SAP Test Harness!"
            assert result["visit_count"] == 6  # 5 + 1
            assert result["last_visit"] == "2023-01-01 12:00:00"
            assert result["p2p_stats"] == {"total_requisitions": 10}
            assert result["system_health"] == {"status": "healthy"}
            assert result["recent_activities"] == [{"message": "Test activity"}]
            
            # Verify state was updated
            mock_state_manager.set.assert_any_call("dashboard_visits", 6)
            mock_state_manager.set.assert_any_call("last_dashboard_visit", result["current_time"])
            
            # Verify helper functions were called
            mock_get_p2p.assert_called_once()
            mock_get_health.assert_called_once()
            mock_get_activities.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redirect_to_dashboard(self):
        """Test that redirect_to_dashboard returns a RedirectResponse to the dashboard URL"""
        # Mock the BaseController.redirect_to_route method
        with patch('controllers.dashboard_controller.BaseController.redirect_to_route') as mock_redirect:
            # Set up the mock to return a RedirectResponse with 302 status
            mock_redirect_response = RedirectResponse(url="/dashboard", status_code=302)
            mock_redirect.return_value = mock_redirect_response
            
            # Call the controller method
            result = await redirect_to_dashboard(self.mock_request)
            
            # Verify the redirect method was called correctly with 302 status code
            mock_redirect.assert_called_once_with(
                "dashboard",
                status_code=302  # Verify GET redirect uses 302 Found
            )
            
            # Check the response
            assert result is mock_redirect_response
            assert result.status_code == 302  # Verify status code is 302 Found
            assert result.headers["location"] == "/dashboard"
    
    def test_get_p2p_statistics(self):
        """Test that get_p2p_statistics returns the expected statistics"""
        with patch('services.get_p2p_service') as mock_get_service:
            # Set up mock P2P service
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service
            
            # Create mock requisitions and orders
            mock_req1 = MagicMock()
            mock_req1.status.value = "APPROVED"
            mock_req1.total_value = 100.0
            mock_req1.created_at = datetime.now() - timedelta(days=2)
            
            mock_req2 = MagicMock()
            mock_req2.status.value = "DRAFT"
            mock_req2.total_value = 50.0
            mock_req2.created_at = datetime.now() - timedelta(days=10)
            
            mock_order1 = MagicMock()
            mock_order1.status.value = "APPROVED"
            mock_order1.total_value = 75.0
            mock_order1.created_at = datetime.now() - timedelta(days=3)
            
            # Configure mock service to return our test data
            mock_service.list_requisitions.return_value = [mock_req1, mock_req2]
            mock_service.list_orders.return_value = [mock_order1]
            
            # Call the function
            result = get_p2p_statistics()
            
            # Verify service methods were called
            mock_service.list_requisitions.assert_called_once()
            mock_service.list_orders.assert_called_once()
            
            # Check the result
            assert result["total_requisitions"] == 2
            assert result["total_orders"] == 1
            assert result["total_requisition_value"] == 150.0
            assert result["total_order_value"] == 75.0
            assert result["open_requisition_value"] == 100.0
            assert result["pending_order_value"] == 75.0
            assert result["recent_requisitions"] == 1  # Only one requisition is within the last week
    
    def test_get_p2p_statistics_with_error(self):
        """Test that get_p2p_statistics handles errors gracefully"""
        with patch('services.get_p2p_service', side_effect=Exception("Test error")):
            # Call the function
            result = get_p2p_statistics()
            
            # Verify default values are returned
            assert result["total_requisitions"] == 0
            assert result["total_orders"] == 0
            assert result["requisition_status_counts"] == {}
            assert result["order_status_counts"] == {}
            assert "error" in result
            assert "Test error" in result["error"]
    
    def test_get_system_health(self):
        """Test that get_system_health returns the expected health data"""
        with patch('services.get_monitor_service') as mock_get_service:
            # Set up mock monitor service
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service
            
            # Configure mock service responses
            mock_service.check_system_health.return_value = {
                "status": "healthy", 
                "components": {"api": "up", "database": "up"}
            }
            
            mock_metrics = MagicMock()
            mock_metrics.cpu_percent = 25.5
            mock_metrics.memory_usage = 45.6
            mock_metrics.disk_usage = 60.2
            mock_metrics.timestamp = datetime.now()
            
            mock_service.collect_current_metrics.return_value = mock_metrics
            
            # Call the function
            result = get_system_health()
            
            # Verify service methods were called
            mock_service.check_system_health.assert_called_once()
            mock_service.collect_current_metrics.assert_called_once()
            
            # Check the result
            assert result["status"] == "healthy"
            assert result["components"] == {"api": "up", "database": "up"}
            assert result["metrics"]["cpu_percent"] == 25.5
            assert result["metrics"]["memory_usage"] == 45.6
            assert result["metrics"]["disk_usage"] == 60.2
            assert "timestamp" in result["metrics"]
    
    def test_get_system_health_with_error(self):
        """Test that get_system_health handles errors gracefully"""
        with patch('services.get_monitor_service', side_effect=Exception("Test error")):
            # Call the function
            result = get_system_health()
            
            # Verify default values are returned
            assert result["status"] == "error"
            assert "error" in result
            assert "Test error" in result["error"]
            assert "metrics" in result
            
    def test_get_recent_activities(self):
        """Test that get_recent_activities returns the expected activities"""
        with patch('services.get_monitor_service') as mock_get_monitor, \
             patch('services.get_p2p_service') as mock_get_p2p:
            
            # Set up mock monitor service
            mock_monitor_service = MagicMock()
            mock_get_monitor.return_value = mock_monitor_service
            
            # Create mock error logs
            log1 = MagicMock()
            log1.timestamp = datetime.now() - timedelta(hours=1)
            log1.message = "Error in component A"
            log1.component = "component_a"
            log1.error_type = "error"
            
            log2 = MagicMock()
            log2.timestamp = datetime.now() - timedelta(hours=2)
            log2.message = "Warning in component B"
            log2.component = "component_b"
            log2.error_type = "warning"
            
            log3 = MagicMock()
            log3.timestamp = datetime.now() - timedelta(hours=3)
            log3.message = "Info message"
            log3.component = "monitor_service"
            log3.error_type = "info"
            
            # Configure mock monitor service to return our test logs
            mock_monitor_service.get_error_logs.return_value = [log1, log2, log3]
            
            # Set up mock P2P service
            mock_p2p_service = MagicMock()
            mock_get_p2p.return_value = mock_p2p_service
            
            # Create mock requisitions and orders
            req = MagicMock()
            req.created_at = datetime.now() - timedelta(minutes=30)
            req.document_number = "REQ-001"
            req.description = "Test Requisition"
            
            order = MagicMock()
            order.created_at = datetime.now() - timedelta(minutes=45)
            order.document_number = "PO-001"
            order.description = "Test Order"
            
            # Configure mock P2P service to return our test data
            mock_p2p_service.list_requisitions.return_value = [req]
            mock_p2p_service.list_orders.return_value = [order]
            
            # Call the function
            result = get_recent_activities()
            
            # Verify service methods were called
            mock_monitor_service.get_error_logs.assert_called_once_with(hours=24, limit=5)
            mock_p2p_service.list_requisitions.assert_called_once()
            mock_p2p_service.list_orders.assert_called_once()
            
            # Check the result
            assert len(result) <= 10
            
            # Monitor logs - should not include the "info" log from monitor_service
            monitor_logs = [a for a in result if a["component"] in ["component_a", "component_b"]]
            assert len(monitor_logs) == 2
            
            # P2P activities
            p2p_activities = [a for a in result if a["component"] == "p2p_service"]
            assert len(p2p_activities) == 2
            
            # Verify activities are sorted by timestamp (newest first)
            for i in range(len(result) - 1):
                assert result[i]["timestamp"] >= result[i+1]["timestamp"]
    
    def test_get_recent_activities_with_error(self):
        """Test that get_recent_activities handles errors gracefully"""
        with patch('services.get_monitor_service', side_effect=Exception("Test error")):
            # Call the function
            result = get_recent_activities()
            
            # Verify error activity is returned
            assert len(result) == 1
            assert "Error retrieving activities" in result[0]["message"]
            assert result[0]["component"] == "dashboard_controller"
            assert result[0]["type"] == "error"
