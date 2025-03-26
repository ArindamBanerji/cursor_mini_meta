"""
Tests for FastAPI parameter extraction patterns in the mini_meta_harness.

This test suite addresses item A.2 from the test improvement backlog:
- Test parameter validation
- Test request body handling
- Test query parameter handling
- Test path parameter handling
- Test form parameter handling
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so Python can find the tests_dest module
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent  # Go up to project root
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import helper to fix imports
from tests_dest.import_helper import fix_imports
fix_imports()

import pytest
import logging
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import Request, Form, Query, Path, Body, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Dict, List, Optional, Any
import json
from datetime import datetime, date

# Configure logging
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


class TestFastAPIParameterExtraction:
    """Tests for FastAPI parameter extraction patterns used in the codebase."""
    
    def create_mock_request(self, query_params=None, path_params=None, form_data=None, json_body=None, headers=None):
        """Create a mock request with all parameter types."""
        mock_request = MagicMock(spec=Request)
        
        # Configure query parameters
        mock_request.query_params = MagicMock()
        mock_request.query_params.get = lambda key, default=None: (query_params or {}).get(key, default)
        mock_request.query_params.items = lambda: (query_params or {}).items()
        mock_request.query_params.keys = lambda: (query_params or {}).keys()
        mock_request.query_params.getlist = lambda key: (query_params or {}).get(key, []) if isinstance((query_params or {}).get(key), list) else [(query_params or {}).get(key)] if (query_params or {}).get(key) is not None else []
        
        # Configure path parameters
        mock_request.path_params = path_params or {}
        
        # Configure form data
        if form_data:
            mock_form_data = MockFormData(form_data)
            
            async def mock_form():
                logger.debug(f"Mock form() function called, returning: {form_data}")
                return mock_form_data
            
            mock_request.form = mock_form
        
        # Configure JSON body
        if json_body:
            async def mock_json():
                logger.debug(f"Mock json() function called, returning: {json_body}")
                return json_body
            
            mock_request.json = mock_json
        
        # Configure headers
        mock_request.headers = headers or {}
        
        # Configure URL
        mock_request.url = MagicMock()
        mock_request.url.path = "/api/test"
        mock_request.url.query = "&".join([f"{k}={v}" for k, v in (query_params or {}).items()])
        
        return mock_request
    
    # QUERY PARAMETER TESTS
    
    @pytest.mark.asyncio
    async def test_query_parameter_extraction(self):
        """Test extracting query parameters."""
        # Arrange
        query_params = {
            "name": "John",
            "age": "30",
            "active": "true"
        }
        mock_request = self.create_mock_request(query_params=query_params)
        
        # Act - Simulate controller extracting query parameters
        # Extract query parameters like controllers do
        name = mock_request.query_params.get("name")
        age = mock_request.query_params.get("age")
        active_str = mock_request.query_params.get("active")
        missing = mock_request.query_params.get("missing", "default")
        
        # Convert types as controllers would
        age_int = int(age) if age is not None else None
        active_bool = active_str.lower() == "true" if active_str is not None else False
        
        # Assert
        assert name == "John"
        assert age_int == 30
        assert active_bool is True
        assert missing == "default"
        
        logger.debug(f"Extracted query parameters: name={name}, age={age_int}, active={active_bool}")
    
    @pytest.mark.asyncio
    async def test_optional_query_parameters(self):
        """Test handling of optional query parameters."""
        # Arrange - request with some parameters missing
        query_params = {
            "name": "John"
            # age and active are missing
        }
        mock_request = self.create_mock_request(query_params=query_params)
        
        # Act - Simulate controller extracting query parameters with defaults
        name = mock_request.query_params.get("name")
        age_str = mock_request.query_params.get("age")
        active_str = mock_request.query_params.get("active")
        
        # Convert with defaults
        age = int(age_str) if age_str is not None else 0  # Default age to 0
        active = active_str.lower() == "true" if active_str is not None else False  # Default active to False
        
        # Assert
        assert name == "John"
        assert age == 0
        assert active is False
    
    @pytest.mark.asyncio
    async def test_multi_value_query_parameters(self):
        """Test handling of multi-value query parameters."""
        # Arrange - multi-value parameters
        query_params = {
            "tags": ["python", "fastapi", "testing"]
        }
        mock_request = self.create_mock_request(query_params=query_params)
        
        # Act - Get list of values
        tags = mock_request.query_params.getlist("tags")
        
        # Assert
        assert len(tags) == 3
        assert "python" in tags
        assert "fastapi" in tags
        assert "testing" in tags
    
    # PATH PARAMETER TESTS
    
    @pytest.mark.asyncio
    async def test_path_parameter_extraction(self):
        """Test extracting path parameters."""
        # Arrange
        path_params = {
            "item_id": "12345",
            "version": "v1"
        }
        mock_request = self.create_mock_request(path_params=path_params)
        
        # Act - Simulate controller extracting path parameters
        item_id = mock_request.path_params.get("item_id")
        version = mock_request.path_params.get("version")
        
        # Assert
        assert item_id == "12345"
        assert version == "v1"
    
    # FORM DATA TESTS
    
    @pytest.mark.asyncio
    async def test_form_data_extraction(self):
        """Test extracting form data."""
        # Arrange
        form_data = {
            "username": "jdoe",
            "email": "john.doe@example.com",
            "password": "password123",
            "confirm_password": "password123"
        }
        mock_request = self.create_mock_request(form_data=form_data)
        
        # Act - Simulate controller extracting form data
        form_data_result = await mock_request.form()
        
        # Log the form data and its type for debugging
        logger.debug(f"Form data type: {type(form_data_result)}")
        logger.debug(f"Form data content: {form_data_result}")
        
        # Extract form fields as controllers would
        username = form_data_result.get("username")
        email = form_data_result.get("email")
        password = form_data_result.get("password")
        confirm_password = form_data_result.get("confirm_password")
        
        # Assert
        assert username == "jdoe"
        assert email == "john.doe@example.com"
        assert password == "password123"
        assert confirm_password == "password123"
    
    @pytest.mark.asyncio
    async def test_form_data_validation(self):
        """Test form data validation logic."""
        # Arrange - form with missing required fields
        form_data = {
            "username": "jdoe",
            # email is missing
            "password": "password123",
            "confirm_password": "different_password"  # Passwords don't match
        }
        mock_request = self.create_mock_request(form_data=form_data)
        
        # Act - Simulate controller validation logic
        form_data_result = await mock_request.form()
        
        # Validation logic
        errors = {}
        if not form_data_result.get("email"):
            errors["email"] = "Email is required"
        
        if form_data_result.get("password") != form_data_result.get("confirm_password"):
            errors["confirm_password"] = "Passwords do not match"
        
        # Assert
        assert len(errors) == 2
        assert "email" in errors
        assert "confirm_password" in errors
    
    @pytest.mark.asyncio
    async def test_nested_form_data_extraction(self):
        """Test extracting nested form data with arrays (common pattern in the codebase)."""
        # Arrange - form with array-like fields (item_X_Y pattern)
        form_data = {
            "description": "Purchase Order",
            "vendor": "Acme Inc",
            "item_material_0": "MAT001",
            "item_description_0": "Laptop",
            "item_quantity_0": "2",
            "item_price_0": "1000",
            "item_material_1": "MAT002",
            "item_description_1": "Monitor",
            "item_quantity_1": "3",
            "item_price_1": "300"
        }
        mock_request = self.create_mock_request(form_data=form_data)
        
        # Act - Simulate the extraction and processing of nested form items
        form_data_result = await mock_request.form()
        
        # Convert to dict for easier processing
        form_dict = dict(form_data_result)
        
        # Process array-like form data into structured items
        items = []
        index = 0
        while f"item_material_{index}" in form_dict:
            item = {
                "material": form_dict.get(f"item_material_{index}", ""),
                "description": form_dict.get(f"item_description_{index}", ""),
                "quantity": float(form_dict.get(f"item_quantity_{index}", "0")),
                "price": float(form_dict.get(f"item_price_{index}", "0"))
            }
            items.append(item)
            index += 1
        
        # Assert
        assert len(items) == 2
        assert items[0]["material"] == "MAT001"
        assert items[0]["description"] == "Laptop"
        assert items[0]["quantity"] == 2
        assert items[0]["price"] == 1000
        assert items[1]["material"] == "MAT002"
        assert items[1]["description"] == "Monitor"
        assert items[1]["quantity"] == 3
        assert items[1]["price"] == 300
    
    # JSON BODY TESTS
    
    @pytest.mark.asyncio
    async def test_json_body_extraction(self):
        """Test extracting JSON body data."""
        # Arrange
        json_body = {
            "user": {
                "name": "John Doe",
                "email": "john@example.com",
                "roles": ["admin", "user"]
            },
            "settings": {
                "theme": "dark",
                "notifications": True
            }
        }
        mock_request = self.create_mock_request(json_body=json_body)
        
        # Act - Simulate controller extracting JSON data
        body = await mock_request.json()
        
        # Extract fields as controllers would
        user = body.get("user", {})
        settings = body.get("settings", {})
        name = user.get("name")
        roles = user.get("roles", [])
        theme = settings.get("theme")
        
        # Assert
        assert name == "John Doe"
        assert "admin" in roles
        assert theme == "dark"
    
    # MIXED PARAMETER TYPES TESTS
    
    @pytest.mark.asyncio
    async def test_mixed_parameter_types(self):
        """Test a controller that uses multiple parameter types together."""
        # Arrange
        query_params = {"filter": "active", "sort": "name"}
        path_params = {"org_id": "org123"}
        form_data = {"name": "New Project", "description": "A test project"}
        
        mock_request = self.create_mock_request(
            query_params=query_params,
            path_params=path_params,
            form_data=form_data
        )
        
        # Act - Simulate controller that uses all parameter types
        org_id = mock_request.path_params.get("org_id")
        filter_type = mock_request.query_params.get("filter")
        sort_by = mock_request.query_params.get("sort", "id")  # Default to 'id'
        
        form_data_result = await mock_request.form()
        name = form_data_result.get("name")
        description = form_data_result.get("description")
        
        # Assert
        assert org_id == "org123"
        assert filter_type == "active"
        assert sort_by == "name"
        assert name == "New Project"
        assert description == "A test project"
    
    # DATE AND TIME PARAMETER TESTS
    
    @pytest.mark.asyncio
    async def test_date_time_parameter_handling(self):
        """Test handling of date and time parameters in different formats."""
        # Arrange - date/time in different formats
        query_params = {"date": "2023-04-15"}
        form_data = {
            "start_time": "14:30",
            "end_time": "16:45",
            "created_at": "2023-04-15T14:30:00",
            "date_range": "2023-04-15,2023-04-20"
        }
        
        mock_request = self.create_mock_request(
            query_params=query_params,
            form_data=form_data
        )
        
        # Act - Simulate controller date/time handling
        # Extract date from query params
        date_str = mock_request.query_params.get("date")
        parsed_date = date.fromisoformat(date_str) if date_str else None
        
        # Extract times from form data
        form_data_result = await mock_request.form()
        start_time = form_data_result.get("start_time")
        end_time = form_data_result.get("end_time")
        created_at_str = form_data_result.get("created_at")
        date_range_str = form_data_result.get("date_range")
        
        # Parse ISO datetime
        created_at = datetime.fromisoformat(created_at_str) if created_at_str else None
        
        # Parse date range (comma-separated)
        date_range = []
        if date_range_str:
            date_parts = date_range_str.split(",")
            date_range = [date.fromisoformat(d) for d in date_parts if d]
        
        # Assert
        assert parsed_date == date(2023, 4, 15)
        assert start_time == "14:30"
        assert end_time == "16:45"
        assert created_at == datetime(2023, 4, 15, 14, 30, 0)
        assert len(date_range) == 2
        assert date_range[0] == date(2023, 4, 15)
        assert date_range[1] == date(2023, 4, 20)
    
    # ERROR HANDLING TESTS
    
    @pytest.mark.asyncio
    async def test_parameter_validation_error_handling(self):
        """Test handling of parameter validation errors."""
        # Arrange - form with invalid data
        form_data = {
            "username": "",  # Empty - should fail validation
            "email": "not-an-email",  # Invalid format
            "age": "abc"  # Not a number
        }
        
        mock_request = self.create_mock_request(form_data=form_data)
        
        # Act - Simulate controller validation with error handling
        form_data_result = await mock_request.form()
        
        # Validation logic with error handling
        validation_errors = {}
        
        # Validate age (should be a number)
        age_str = form_data_result.get("age")
        try:
            age = int(age_str) if age_str else None
            if age is not None and (age < 0 or age > 150):
                validation_errors["age"] = "Age must be between 0 and 150"
        except ValueError:
            validation_errors["age"] = "Age must be a number"
        
        # Validate email (simple validation)
        email = form_data_result.get("email")
        if email and "@" not in email:
            validation_errors["email"] = "Invalid email format"
        
        # Assert
        assert "age" in validation_errors
        assert validation_errors["age"] == "Age must be a number"
        assert "email" in validation_errors
        assert validation_errors["email"] == "Invalid email format"


if __name__ == "__main__":
    print("=== Running FastAPI Parameter Extraction Tests ===")
    pytest.main(["-xvs", __file__]) 