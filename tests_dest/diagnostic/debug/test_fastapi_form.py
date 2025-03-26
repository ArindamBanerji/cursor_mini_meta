"""
Diagnostic test for FastAPI form data extraction in the controller.
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
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import Request, Form
from fastapi.responses import RedirectResponse

# Configure logging - set to DEBUG for more detailed output
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MockFormData:
    """Mock form data that implements dict methods for testing."""
    
    def __init__(self, data):
        self.data = data
    
    def __getitem__(self, key):
        return self.data.get(key)
    
    def __contains__(self, key):
        return key in self.data
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def items(self):
        return self.data.items()
    
    def keys(self):
        return self.data.keys()
    
    def values(self):
        return self.data.values()
    
    def __iter__(self):
        return iter(self.data)

class TestFastAPIFormExtraction:
    """Tests for FastAPI form data extraction."""
    
    def _create_mock_request(self, form_data=None):
        """Create a mock request with enhanced form data handling."""
        mock_request = MagicMock(spec=Request)
        
        if form_data:
            # Create a mock form method that returns a dict-like object
            mock_form_data = MockFormData(form_data)
            
            async def mock_form():
                logger.debug(f"Mock form() function called, returning: {form_data}")
                return mock_form_data
            
            mock_request.form = mock_form
        
        return mock_request
    
    @pytest.mark.asyncio
    async def test_form_data_with_dict_functionality(self):
        """Test accessing form data with full dict functionality."""
        # Arrange
        form_data = {
            "description": "Test Item",
            "quantity": "10",
            "vendor": "Test Vendor"
        }
        mock_request = self._create_mock_request(form_data=form_data)
        
        # Act - test form data retrieval and dict operations
        try:
            # Get the form data
            form_data_result = await mock_request.form()
            
            # Log the form data and its type
            logger.debug(f"Form data type: {type(form_data_result)}")
            logger.debug(f"Form data content: {form_data_result}")
            
            # Test dictionary access
            assert "description" in form_data_result
            assert form_data_result["description"] == "Test Item"
            assert form_data_result.get("vendor") == "Test Vendor"
            
            # Test dictionary iteration
            keys = list(form_data_result.keys())
            logger.debug(f"Form data keys: {keys}")
            assert "description" in keys
            assert "quantity" in keys
            assert "vendor" in keys
            
            # Test creating a dictionary from the form data
            form_dict = dict(form_data_result)
            logger.debug(f"Dict from form data: {form_dict}")
            assert form_dict["description"] == "Test Item"
            assert form_dict["quantity"] == "10"
            
            # Test a controller-like extraction
            description = form_dict.get("description", "")
            vendor = form_dict.get("vendor", "")
            logger.debug(f"Extracted values: description='{description}', vendor='{vendor}'")
            assert description == "Test Item"
            assert vendor == "Test Vendor"
            
        except Exception as e:
            logger.error(f"Error in form data test: {e}", exc_info=True)
            raise
    
    @pytest.mark.asyncio
    async def test_controller_form_extraction_simulation(self):
        """Simulate the exact form extraction pattern used in the controller."""
        # Arrange
        form_data = {
            "description": "Test Order",
            "requester": "John Doe",
            "vendor": "Test Vendor",
            "payment_terms": "Net 30",
            "procurement_type": "STANDARD",
            "notes": "Test Notes",
            "item_material_0": "MAT001",
            "item_description_0": "Test Material",
            "item_quantity_0": "10"
        }
        mock_request = self._create_mock_request(form_data=form_data)
        
        # Act - simulate the controller's form extraction
        try:
            # This is the exact pattern used in the controller
            form_data_result = await mock_request.form()
            form_dict = dict(form_data_result)
            
            # Log the extraction results
            logger.debug(f"Form data result: {form_data_result}")
            logger.debug(f"Form dict: {form_dict}")
            
            # Extract specific fields as the controller would
            description = form_dict.get("description", "")
            vendor = form_dict.get("vendor", "")
            requester = form_dict.get("requester", "")
            
            # Verify extraction was correct
            assert description == "Test Order"
            assert vendor == "Test Vendor"
            assert requester == "John Doe"
            
            # Check for a value that should not be present
            missing_value = form_dict.get("non_existent_field", "default")
            assert missing_value == "default"
            
            # Simulate extraction of from_requisition check
            from_requisition = form_dict.get("from_requisition")
            assert from_requisition is None  # Should not be present
            
        except Exception as e:
            logger.error(f"Error in controller simulation test: {e}", exc_info=True)
            raise 