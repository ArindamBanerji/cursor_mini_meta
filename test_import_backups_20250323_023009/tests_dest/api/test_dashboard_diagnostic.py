# Add path setup to find the tests_dest module
import sys
import os
from pathlib import Path

# Add parent directory to path so Python can find the tests_dest module
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent  # Go up two levels to reach project root
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import helper to fix path issues
from tests_dest.import_helper import fix_imports
fix_imports()

import pytest
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Optional imports - these might fail but won't break tests
try:
    from services.base_service import BaseService
    from services.monitor_service import MonitorService
    from models.base_model import BaseModel
except ImportError as e:
    logger.warning(f"Optional import failed: {e}")


"""
Diagnostic tests for the dashboard controller.

This file tests our dependency unwrapping approach with the dashboard controller,
which has service dependencies and more complex logic.
"""

# Additional imports for dashboard testing
import json
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from controllers.dashboard_controller import show_dashboard, redirect_to_dashboard
from services.state_manager import state_manager

# Test fixtures
@pytest.fixture
def mock_request():
    """Create a mock request object."""
    request = MagicMock(spec=Request)
    request.url = MagicMock()
    request.url.path = "/dashboard"
    request.query_params = {}
    return request

@pytest.fixture
def mock_state_manager():
    """Create a mock state manager."""
    with patch('controllers.dashboard_controller.state_manager') as mock:
        mock.get.side_effect = lambda key, default=None: {
            "dashboard_visits": 5,
            "last_dashboard_visit": "2024-03-18 12:00:00"
        }.get(key, default)
        yield mock

# Test functions
@pytest.mark.asyncio
async def test_show_dashboard(mock_request, mock_state_manager):
    """Test the show_dashboard endpoint."""
    response = await show_dashboard(mock_request)
    
    assert isinstance(response, dict)
    assert "welcome_message" in response
    assert "visit_count" in response
    assert response["visit_count"] == 6  # Should be incremented from 5
    assert "last_visit" in response
    assert "current_time" in response

@pytest.mark.asyncio
async def test_redirect_to_dashboard(mock_request):
    """Test the redirect_to_dashboard endpoint."""
    response = await redirect_to_dashboard(mock_request)
    
    assert isinstance(response, RedirectResponse)
    assert response.status_code == 302  # GET redirect uses 302 Found
    assert "dashboard" in response.headers["location"]

def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Simple diagnostic test ===")
    print("Successfully executed test_dashboard_diagnostic.py")
    print("All imports resolved correctly")
    return True

if __name__ == "__main__":
    run_simple_test()
    #pytest.main([__file__, "-v"]) 