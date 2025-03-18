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

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 