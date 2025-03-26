"""
Direct test script to validate the error_code fix in error_utils.py
Running this file directly will test the error response format.
"""

import json
import sys
from fastapi.responses import JSONResponse

# Import directly from project
from utils.error_utils import AppError, NotFoundError, ValidationError, create_error_response

def test_error_response_format():
    """Test that error responses use error_code instead of error."""
    print("Testing error response format...")
    
    # Create test errors
    not_found_error = NotFoundError(
        "Resource not found", 
        details={"resource_id": "TEST001", "resource_type": "Material"}
    )
    
    validation_error = ValidationError(
        "Invalid input data",
        details={"field": "quantity", "reason": "Must be positive"}
    )
    
    # Generate responses
    not_found_response = create_error_response(not_found_error)
    validation_response = create_error_response(validation_error)
    
    # Parse response bodies
    not_found_data = json.loads(not_found_response.body)
    validation_data = json.loads(validation_response.body)
    
    # Check for error_code field
    assert "error_code" in not_found_data, "Not found response should have error_code"
    assert "error" not in not_found_data, "Not found response should not have error field"
    
    assert "error_code" in validation_data, "Validation response should have error_code"
    assert "error" not in validation_data, "Validation response should not have error field"
    
    # Print the response formats
    print(f"Not found error response: {not_found_data}")
    print(f"Validation error response: {validation_data}")
    
    print("All tests passed!")
    return True

if __name__ == "__main__":
    # Run the test
    success = test_error_response_format()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1) 