# Import helper to fix path issues
from tests-dest.import_helper import fix_imports
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


# tests-dest/api/test_file.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import Request
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

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