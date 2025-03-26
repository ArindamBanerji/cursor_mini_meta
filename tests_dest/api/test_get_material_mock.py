"""
Test for demonstrating how to properly mock async session utils.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import Request
from fastapi.responses import RedirectResponse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

from tests_dest.api.test_helpers import unwrap_dependencies

# Import services and models
from tests_dest.test_helpers.service_imports import (
    MaterialService,
    MonitorService,
    Material,
    MaterialType,
    UnitOfMeasure,
    MaterialStatus
)

# Import the controller to test
from controllers.material_ui_controller import get_material

# Create test material data
TEST_MATERIAL = Material(
    id="MAT001",
    name="Steel Sheet",
    material_number="STEEL-001",
    description="Sheet of industrial steel",
    type=MaterialType.RAW,
    base_unit=UnitOfMeasure.KILOGRAM,
    price=15.50,
    created_at="2023-01-01T00:00:00",
    updated_at="2023-01-01T00:00:00",
    status=MaterialStatus.ACTIVE
)

@pytest.fixture
def mock_request():
    """Create a mock request for testing."""
    request = AsyncMock(spec=Request)
    request.url = MagicMock()
    request.url.path = "/materials/MAT12345"
    request.state = MagicMock()
    request.state.flash_messages = []
    request.state.form_data = {}
    return request

@pytest.fixture
def mock_material_service():
    """Create a mock material service for testing."""
    service = MagicMock(spec=MaterialService)
    service.get_material.return_value = TEST_MATERIAL
    return service

@pytest.fixture
def mock_monitor_service():
    """Create a mock monitor service for testing."""
    service = MagicMock(spec=MonitorService)
    service.log_error = MagicMock()
    return service

@pytest.mark.asyncio
async def test_get_material_mock(mock_request, mock_material_service, mock_monitor_service):
    """Test the get_material controller function with proper mocking."""
    # Create wrapped controller with mocks
    wrapped = unwrap_dependencies(
        get_material,
        material_service=mock_material_service,
        monitor_service=mock_monitor_service
    )
    
    # Create a simple context to be returned by our mocked function
    mock_context = {
        "material": TEST_MATERIAL,
        "related_documents": {"requisitions": [], "orders": []},
        "title": f"Material: {TEST_MATERIAL.name}",
        "flash_messages": [],
        "form_data": {}
    }
    
    # Mock get_template_context_with_session to return our prepared context
    with patch('controllers.material_ui_controller.get_template_context_with_session') as mock_get_context:
        # Set up mock to return our prepared context
        mock_get_context.return_value = mock_context
        
        # Call the function
        result = await wrapped(mock_request, "MAT12345")
    
    # Verify result
    assert result == mock_context
    assert "material" in result
    assert result["material"] == TEST_MATERIAL
    mock_material_service.get_material.assert_called_once_with("MAT12345") 