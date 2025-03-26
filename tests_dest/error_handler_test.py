"""
Test file for checking API error handling.

This test specifically verifies the error response format
to ensure it includes the "error_code" field.
"""

import os
import sys
import json
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request, Response
from fastapi.responses import JSONResponse

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Use simplified conftest to avoid circular imports
pytest_plugins = ["tests-dest.simple_conftest"]

class TestErrorHandling:
    """Test class for API error handling."""
    
    @pytest.mark.asyncio
    async def test_not_found_error_response_format(self, clean_state_manager):
        """Test that not found errors include error_code in the response."""
        from utils.error_utils import not_found_error_handler
        from utils.error_utils import NotFoundError
        
        # Create a mock request
        request = AsyncMock(spec=Request)
        
        # Create a NotFoundError with context
        error = NotFoundError("Test resource not found", 
                             context={"resource_id": "123", "resource_type": "Test"})
        
        # Call the error handler
        response = await not_found_error_handler(request, error)
        
        # Verify the response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        
        # Check the response content
        content = json.loads(response.body)
        assert content["success"] is False
        assert "error_code" in content
        assert content["error_code"] == "not_found"
        assert "details" in content
        assert "resource_id" in content["details"]
        assert content["details"]["resource_id"] == "123"
    
    @pytest.mark.asyncio
    async def test_validation_error_response_format(self, clean_state_manager):
        """Test that validation errors include error_code in the response."""
        from utils.error_utils import validation_error_handler
        from utils.error_utils import ValidationError
        
        # Create a mock request
        request = AsyncMock(spec=Request)
        
        # Create a ValidationError with context
        error = ValidationError("Invalid data", 
                               context={"field": "name", "reason": "required"})
        
        # Call the error handler
        response = await validation_error_handler(request, error)
        
        # Verify the response
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        
        # Check the response content
        content = json.loads(response.body)
        assert content["success"] is False
        assert "error_code" in content
        assert content["error_code"] == "validation_error"
        assert "details" in content
        assert "field" in content["details"]
        assert content["details"]["field"] == "name"

if __name__ == "__main__":
    # Run the tests directly when this file is executed
    pytest.main(["-xvs", __file__]) 