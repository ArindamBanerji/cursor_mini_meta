"""
Standalone test for error handling.

This test doesn't rely on conftest.py and directly tests
whether the API responses use "error_code" or "error".
"""

import os
import sys
import json
from unittest.mock import MagicMock

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import error utilities
from utils.error_utils import (
    NotFoundError, 
    ValidationError,
    create_error_response
)

def test_not_found_error_format():
    """Test not found error response format."""
    # Create a NotFoundError with details
    error = NotFoundError(
        "Resource not found", 
        details={"resource_id": "123", "resource_type": "Test"}
    )
    
    # Call create_error_response directly
    response = create_error_response(error)
    
    # Parse and check response content
    content = json.loads(response.body)
    print(f"Not found error response: {content}")
    
    # Check for error code key
    assert "error_code" in content, "Response should contain 'error_code' field"
    assert "error" not in content, "Response should not contain 'error' field"
    assert content["error_code"] == "not_found"
    
    # Check other fields
    assert content["success"] is False
    assert "details" in content
    assert "resource_id" in content["details"]
    
    print("Not found error test passed!")

def test_validation_error_format():
    """Test validation error response format."""
    # Create a ValidationError with details
    error = ValidationError(
        "Invalid data", 
        details={"field": "name", "reason": "required"}
    )
    
    # Call create_error_response directly
    response = create_error_response(error)
    
    # Parse and check response content
    content = json.loads(response.body)
    print(f"Validation error response: {content}")
    
    # Check for error code key
    assert "error_code" in content, "Response should contain 'error_code' field"
    assert "error" not in content, "Response should not contain 'error' field"
    assert content["error_code"] == "validation_error"
    
    # Check other fields
    assert content["success"] is False
    assert "details" in content
    assert "field" in content["details"]
    
    print("Validation error test passed!")

if __name__ == "__main__":
    print("Running standalone error format tests...")
    test_not_found_error_format()
    test_validation_error_format()
    print("All tests completed successfully!") 