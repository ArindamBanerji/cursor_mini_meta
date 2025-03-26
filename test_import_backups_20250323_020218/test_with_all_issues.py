import sys
import os
import sys  # duplicate import
from pathlib import Path

# Partial path setup - this should be removed and replaced with our complete version
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

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
    from tests_dest.services.base_service import BaseService  # uses hyphen instead of underscore
    from tests_dest.services.monitor_service import MonitorService
    from tests_dest.models.base_model import BaseModel
except ImportError as e:
    logger.warning(f"Optional import failed: {e}")

# Import helper to fix path issues - this should be kept
from tests_dest.import_helper import fix_imports  # uses hyphen
fix_imports()

# Duplicate import helper - this should be removed
from tests_dest.import_helper import fix_imports
fix_imports()

# tests-dest/api/test_file.py - comment with hyphen
import sys  # Another duplicate import
import os   # Another duplicate import
logger = logging.getLogger(__name__)

# Wrong import from test_helpers
from api.test_helpers import unwrap_dependencies

@pytest.fixture
def mock_request():
    """Create a mock request object for testing."""
    request = MagicMock(spec=Request)
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    request.headers = {"X-Forwarded-For": "10.0.0.1"}
    request.url = MagicMock()
    request.url.path = "/test"
    return request

@pytest.mark.asyncio
async def test_simple_function(mock_request):
    """Test a simple function."""
    # Create a mock
    mock_service = MagicMock()
    mock_service.get_data.return_value = {"test": "value"}
    
    # Call the function
    result = await mock_service.get_data()
    
    # Verify the result
    assert result == {"test": "value"}
    mock_service.get_data.assert_called_once() 