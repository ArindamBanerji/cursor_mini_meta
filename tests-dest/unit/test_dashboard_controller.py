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

# tests-dest/unit/test_dashboard_controller.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request
from fastapi.responses import RedirectResponse
from controllers.dashboard_controller import show_dashboard, redirect_to_dashboard
from controllers import BaseController
from datetime import datetime

class TestDashboardController:
    def setup_method(self):
        # Create a mock request
        self.mock_request = MagicMock(spec=Request)
    
    @pytest.mark.asyncio
    async def test_show_dashboard(self):
        """Test that show_dashboard returns the expected context with state data"""
        # Mock the state manager
        with patch('controllers.dashboard_controller.state_manager') as mock_state_manager:
            # Configure the mock to return specific values
            mock_state_manager.get.side_effect = lambda key, default=None: {
                "dashboard_visits": 5,
                "last_dashboard_visit": "2023-01-01 12:00:00"
            }.get(key, default)
            
            # Call the controller method
            result = await show_dashboard(self.mock_request)
            
            # Check the result is a dict with expected keys
            assert isinstance(result, dict)
            assert "welcome_message" in result
            assert "visit_count" in result
            assert "last_visit" in result
            assert "current_time" in result
            
            # Check specific values
            assert result["welcome_message"] == "Welcome to the mini-meta harness!"
            assert result["visit_count"] == 6  # 5 + 1
            assert result["last_visit"] == "2023-01-01 12:00:00"
            
            # Verify state was updated
            mock_state_manager.set.assert_any_call("dashboard_visits", 6)
            mock_state_manager.set.assert_any_call("last_dashboard_visit", result["current_time"])
    
    @pytest.mark.asyncio
    async def test_redirect_to_dashboard(self):
        """Test that redirect_to_dashboard returns a RedirectResponse to the dashboard URL"""
        # Mock the BaseController.redirect_to_route method
        with patch('controllers.dashboard_controller.BaseController.redirect_to_route') as mock_redirect:
            # Set up the mock to return a RedirectResponse
            mock_redirect_response = RedirectResponse(url="/dashboard")
            mock_redirect.return_value = mock_redirect_response
            
            # Call the controller method
            result = await redirect_to_dashboard(self.mock_request)
            
            # Verify the redirect method was called correctly
            mock_redirect.assert_called_once_with("dashboard")
            
            # Check the result
            assert result is mock_redirect_response
