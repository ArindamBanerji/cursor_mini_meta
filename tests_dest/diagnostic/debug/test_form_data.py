"""
Simple diagnostic test for form data handling in the controller.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so Python can find the tests_dest module
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent  # Go up to project root
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import helper to fix imports
from tests_dest.import_helper import fix_imports
fix_imports()

import pytest
import logging
from unittest.mock import MagicMock, patch
from fastapi import Request
from fastapi.responses import RedirectResponse

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestFormDataHandling:
    """Tests for form data handling."""
    
    def _create_mock_request(self, form_data=None):
        """Create a mock request with form data for testing."""
        mock_request = MagicMock(spec=Request)
        if form_data:
            async def mock_form():
                logger.debug(f"Mock form() function called, returning: {form_data}")
                return form_data
            mock_request.form = mock_form
        
        return mock_request
    
    @pytest.mark.asyncio
    async def test_form_data_access(self):
        """Test accessing form data from a request."""
        # Arrange
        form_data = {
            "description": "Test Item",
            "quantity": "10"
        }
        mock_request = self._create_mock_request(form_data=form_data)
        
        # Act - simply test accessing the form data
        try:
            actual_form_data = await mock_request.form()
            
            # Assert
            logger.debug(f"Form data retrieved: {actual_form_data}")
            assert actual_form_data == form_data
            assert "description" in actual_form_data
            assert actual_form_data["description"] == "Test Item"
            
            # Additional check - can we convert to dict and access?
            form_dict = dict(actual_form_data)
            logger.debug(f"Form dict: {form_dict}")
            assert "description" in form_dict
            assert form_dict["description"] == "Test Item"
            
        except Exception as e:
            logger.error(f"Error accessing form data: {e}", exc_info=True)
            raise 