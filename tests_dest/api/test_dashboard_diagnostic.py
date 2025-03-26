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
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services from service_imports
from tests_dest.test_helpers.service_imports import (
    BaseService,
    MonitorService, 
    get_monitor_service,
    state_manager
)

"""
Diagnostic tests for the dashboard controller.

This file tests the dashboard controller with real dependencies, 
which has service dependencies and more complex logic.
"""

# Additional imports for dashboard testing
import json
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from controllers.dashboard_controller import show_dashboard, redirect_to_dashboard

# Test fixtures
@pytest.fixture
def real_request():
    """Create a real request object."""
    app = FastAPI()
    client = TestClient(app)
    
    # Create a basic request scope
    scope = {
        "type": "http",
        "path": "/dashboard",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 50000)
    }
    
    return Request(scope)

# Test functions
@pytest.mark.asyncio
async def test_show_dashboard(real_request):
    """Test the show_dashboard endpoint with real dependencies."""
    # Get the initial visit count for validation
    initial_visit_count = state_manager.get("dashboard_visits", 0)
    
    # Call the actual function with real request and state_manager
    response = await show_dashboard(real_request)
    
    assert isinstance(response, dict)
    assert "welcome_message" in response
    assert "visit_count" in response
    assert response["visit_count"] > initial_visit_count  # Should be incremented
    assert "last_visit" in response
    assert "current_time" in response

@pytest.mark.asyncio
async def test_redirect_to_dashboard(real_request):
    """Test the redirect_to_dashboard endpoint with real dependencies."""
    response = await redirect_to_dashboard(real_request)
    
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
