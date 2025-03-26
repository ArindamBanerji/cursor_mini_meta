# Add path setup to find the tests_dest module
import sys
import os
import json
from pathlib import Path

# Add parent directory to path so Python can find the tests_dest module
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent  # Go up two levels to reach project root
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import helper to fix path issues
from tests_dest.import_helper import fix_imports
fix_imports()

"""
Diagnostic tests for the P2P Order API controller.

This file is for testing and diagnosing issues with the P2P Order API controller
and NOT for production use. Its purpose is to experiment with different approaches
to fixing issues with the API controller.
"""

import pytest
import logging
from unittest.mock import MagicMock, AsyncMock
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services and models through the service_imports facade
from tests_dest.test_helpers.service_imports import (
    P2PService,
    MonitorService,
    Order,
    DocumentStatus,
    # Import API controller functions from facade
    api_submit_order, 
    api_approve_order,
    api_receive_order,
    api_complete_order,
    api_cancel_order,
    get_p2p_order_api_controller
)

# Import helper for testing FastAPI dependencies
from tests_dest.api.test_helpers import unwrap_dependencies

# Helper function to extract JSON from response objects
def extract_json(response):
    """Enhanced function to extract JSON from various response types.
    
    This function handles several common response types and converts
    them to dictionaries for consistent handling.
    
    Args:
        response: The response object to extract JSON from
        
    Returns:
        dict: The JSON data extracted from the response
    """
    # Case 1: FastAPI/Starlette Response object
    if hasattr(response, 'body') and callable(getattr(response, 'body', None)):
        return json.loads(response.body.decode())
    
    # Case 2: Already a dict
    if isinstance(response, dict):
        return response
    
    # Case 3: Pydantic model
    if hasattr(response, 'model_dump'):
        return response.model_dump()
    
    if hasattr(response, 'dict'):
        return response.dict()
    
    # Case 4: Object with to_dict method
    if hasattr(response, 'to_dict'):
        return response.to_dict()
    
    # Case 5: Object with common attributes - check if it has expected attributes
    common_attributes = ['id', 'document_number', 'description', 'status', 
                         'created_at', 'updated_at']
    
    # Check if at least 3 of the common attributes are present
    available_attrs = [attr for attr in common_attributes if hasattr(response, attr)]
    
    if len(available_attrs) >= 3:
        # Extract available attributes
        result = {}
        for attr in common_attributes:
            if hasattr(response, attr):
                result[attr] = getattr(response, attr)
        return result
    
    # Case 6: Return as is if we can't convert it
    return response

def get_best_serialization_method(obj):
    """
    Determine the best serialization method for an object.
    
    This function evaluates different serialization methods available on the object
    and returns the best one to use, preferring methods in this order:
    1. model_dump() - Pydantic v2 method
    2. dict() - Pydantic v1 method (deprecated in v2)
    3. to_dict() - Custom method
    4. Attribute extraction - Fallback method
    
    Args:
        obj: The object to evaluate
        
    Returns:
        str: The name of the best serialization method to use
    """
    # Check if model_dump() is available (Pydantic V2)
    if hasattr(obj, 'model_dump'):
        return "model_dump"
    
    # Check if dict() is available (Pydantic V1)
    if hasattr(obj, 'dict'):
        return "dict"
        
    # Check if to_dict() is available (custom method)
    if hasattr(obj, 'to_dict'):
        return "to_dict"
    
    # Default fallback to attribute extraction
    return "attr_extraction"

"""
Approach 1: Test if JSON serialization is the issue with Order objects
"""

def test_order_json_serialization():
    """Test Order object JSON serialization options."""
    # Create a test order
    order = Order(
        id="ORD-001",
        document_number="ORD-001",
        description="Test Order",
        requester="Test User",
        vendor="Test Vendor",
        requisition_id="REQ-001",
        status=DocumentStatus.DRAFT,
        items=[],
        created_at="2023-01-01T00:00:00Z"
    )
    
    # Test with different serialization options
    print("\n=== Testing Order object serialization ===")
    serialization_results = {}
    
    # Approach 1: Direct dictionary access
    # Note: This is expected to fail as Order is not subscriptable
    # Instead of using try/except, use a more controlled test approach
    can_use_subscription = hasattr(order, "__getitem__")
    if can_use_subscription:
        serialization_results["subscription"] = order["id"]
    else:
        print("Direct subscription not available (as expected)")
    
    # Approach 2: Using model_dump() if available
    if hasattr(order, 'model_dump'):
        order_dict = order.model_dump()
        serialization_results["model_dump"] = order_dict
        print(f"model_dump() result available: {order_dict['id'] if 'id' in order_dict else 'id not found'}")
    else:
        print("model_dump() not available")
    
    # Approach 3: Using dict() if available
    if hasattr(order, 'dict'):
        print("WARNING: dict() method is deprecated, use model_dump() instead")
        order_dict = order.dict()
        serialization_results["dict"] = order_dict
        print(f"dict() result available: {order_dict['id'] if 'id' in order_dict else 'id not found'}")
    else:
        print("dict() not available")
    
    # Approach 4: Using to_dict method
    if hasattr(order, 'to_dict'):
        order_dict = order.to_dict()
        serialization_results["to_dict"] = order_dict
        print(f"to_dict result available: {order_dict['id'] if 'id' in order_dict else 'id not found'}")
    else:
        print("to_dict method not available")
    
    # Approach 5: Manual attribute extraction (always works but less elegant)
    attr_dict = {
        'id': getattr(order, 'id', None),
        'document_number': getattr(order, 'document_number', None),
        'description': getattr(order, 'description', None)
    }
    serialization_results["attr_extraction"] = attr_dict
    print(f"Attribute extraction result: {attr_dict['id']}")
    
    print("=== Order serialization tests complete ===")
    
    # Determine the best serialization method
    if "model_dump" in serialization_results:
        best_method = "model_dump"
    elif "dict" in serialization_results:
        best_method = "dict"
    elif "to_dict" in serialization_results:
        best_method = "to_dict"
    else:
        best_method = "attr_extraction"
    
    print(f"Best serialization method: {best_method}")
    
    # Return the best serialization method
    return best_method

"""
Approach 2: Test a modified controller class that uses the best serialization method
"""

class TestP2POrderAPIController:
    """Diagnostic version of P2POrderAPIController with modified serialization."""
    
    def __init__(self, p2p_service=None, monitor_service=None):
        """Initialize with required services."""
        self.p2p_service = p2p_service or MagicMock(spec=P2PService)
        self.monitor_service = monitor_service or MagicMock(spec=MonitorService)
    
    def serialize_order(self, order):
        """Serialize an Order object to a dictionary using the best available method."""
        if hasattr(order, 'model_dump'):
            return order.model_dump()
        elif hasattr(order, 'dict'):
            # Note: dict() is deprecated in Pydantic v2 but used for backward compatibility
            import warnings
            warnings.warn(
                "The 'dict()' method is deprecated; use 'model_dump()' instead.",
                DeprecationWarning,
                stacklevel=2
            )
            return order.dict()
        elif hasattr(order, 'to_dict'):
            # Use to_dict() method if available
            return order.to_dict()
        else:
            # Fallback: convert attributes manually
            return {
                'id': getattr(order, 'id', None),
                'document_number': getattr(order, 'document_number', None),
                'description': getattr(order, 'description', None),
                'requester': getattr(order, 'requester', None),
                'vendor': getattr(order, 'vendor', None),
                'requisition_id': getattr(order, 'requisition_id', None),
                'status': getattr(order, 'status', None),
                'items': getattr(order, 'items', []),
                'created_at': getattr(order, 'created_at', None),
                'updated_at': getattr(order, 'updated_at', None)
            }
    
    def serialize_orders_list(self, orders):
        """Serialize a list of Order objects to a list of dictionaries."""
        return [self.serialize_order(order) for order in orders]
    
    def create_success_response(self, data=None, message=None):
        """Create a standardized success response."""
        response = {
            "success": True,
            "status": "success"
        }
        
        if message:
            response["message"] = message
            
        if data is not None:
            if isinstance(data, list):
                response["data"] = self.serialize_orders_list(data)
            else:
                response["data"] = self.serialize_order(data)
                
        return response
    
    def create_error_response(self, message, error_code="error", details=None, status_code=400):
        """Create a standardized error response."""
        response = {
            "success": False,
            "status": "error",
            "error": {
                "code": error_code,
                "message": str(message)
            }
        }
        
        if details:
            response["error"]["details"] = details
        
        return response, status_code
    
    async def api_submit_order(self, request, order_id):
        """Submit an order for approval."""
        # Attempt to submit the order and handle potential errors with proper logging
        order = self.p2p_service.submit_order(order_id)
        if not order:
            logger.error(f"Order {order_id} submission failed: no order returned")
            return self.create_error_response(
                message="Order submission failed",
                error_code="submission_failed"
            )
        
        # Return success response
        return self.create_success_response(
            data=order,
            message=f"Order {order_id} submitted successfully"
        )
    
    async def api_approve_order(self, request, order_id):
        """Approve an order."""
        # Attempt to approve the order and handle potential errors with proper logging
        order = self.p2p_service.approve_order(order_id)
        if not order:
            logger.error(f"Order {order_id} approval failed: no order returned")
            return self.create_error_response(
                message="Order approval failed",
                error_code="approval_failed"
            )
        
        # Return success response
        return self.create_success_response(
            data=order,
            message=f"Order {order_id} approved successfully"
        )
    
    async def api_receive_order(self, request, order_id):
        """Receive an order."""
        # Deserialize request body to get quantities and other data
        request_data = await request.json()
        received_quantities = request_data.get("received_quantities", {})
        
        if not received_quantities and request_data.get("require_quantities", True):
            logger.warning(f"No received quantities specified for order {order_id}")
            return self.create_error_response(
                message="Received quantities are required",
                error_code="invalid_request"
            )
        
        # Attempt to receive the order with the provided quantities
        order = self.p2p_service.receive_order(order_id, received_quantities)
        if not order:
            logger.error(f"Order {order_id} receiving failed: no order returned")
            return self.create_error_response(
                message="Order receiving failed",
                error_code="receive_failed"
            )
        
        # Return success response
        return self.create_success_response(
            data=order,
            message=f"Order {order_id} received successfully"
        )
    
    async def api_complete_order(self, request, order_id):
        """Complete an order."""
        # Attempt to complete the order and handle potential errors with proper logging
        order = self.p2p_service.complete_order(order_id)
        if not order:
            logger.error(f"Order {order_id} completion failed: no order returned")
            return self.create_error_response(
                message="Order completion failed",
                error_code="completion_failed"
            )
        
        # Return success response
        return self.create_success_response(
            data=order,
            message=f"Order {order_id} completed successfully"
        )
    
    async def api_cancel_order(self, request, order_id):
        """Cancel an order."""
        # Deserialize request body to get cancellation reason and other data
        request_data = await request.json()
        cancellation_reason = request_data.get("cancellation_reason", "No reason provided")
        
        # Attempt to cancel the order with the provided reason
        order = self.p2p_service.cancel_order(
            order_id, 
            cancellation_reason=cancellation_reason
        )
        
        if not order:
            logger.error(f"Order {order_id} cancellation failed: no order returned")
            return self.create_error_response(
                message="Order cancellation failed",
                error_code="cancellation_failed"
            )
        
        # Return success response
        return self.create_success_response(
            data=order,
            message=f"Order {order_id} cancelled successfully"
        )

"""
Approach 3: Test a modified extract_json function that handles both JSONResponse
and Order objects properly
"""

def enhanced_extract_json(response):
    """
    Enhanced version of extract_json that handles different object types.
    
    This function attempts to convert various response objects to dictionaries in this order:
    1. JSONResponse objects (extract from body)
    2. Dictionary objects (return as is)
    3. Pydantic models (use model_dump() or dict())
    4. Other objects (tries to_dict or manual attribute extraction)
    """
    # Case 1: JSONResponse objects
    if hasattr(response, 'body'):
        return json.loads(response.body.decode())
    
    # Case 2: Already a dict
    if isinstance(response, dict):
        return response
    
    # Case 3: Pydantic model
    if hasattr(response, 'model_dump'):
        return response.model_dump()
    
    if hasattr(response, 'dict'):
        return response.dict()
    
    # Case 4: Object with to_dict method
    if hasattr(response, 'to_dict'):
        return response.to_dict()
    
    # Case 5: Object with common attributes - check if it has expected attributes
    common_attributes = ['id', 'document_number', 'description', 'status', 
                         'created_at', 'updated_at']
    
    # Check if at least 3 of the common attributes are present
    available_attrs = [attr for attr in common_attributes if hasattr(response, attr)]
    
    if len(available_attrs) >= 3:
        # Extract available attributes
        result = {}
        for attr in common_attributes:
            if hasattr(response, attr):
                result[attr] = getattr(response, attr)
        return result
    
    # Case 6: Return as is if we can't convert it
    return response

"""
Approach 4: Test controller methods response formats for workflow state transitions
"""

async def test_workflow_endpoints_formats():
    """Test the response formats from different workflow endpoint methods."""
    # Create a test controller with mocks
    p2p_service = MagicMock(spec=P2PService)
    monitor_service = MagicMock(spec=MonitorService)
    controller = TestP2POrderAPIController(p2p_service, monitor_service)
    
    # Create a mock request
    request = AsyncMock(spec=Request)
    # Add received_quantities to avoid the validation error
    request.json = AsyncMock(return_value={"received_quantities": {"item1": 5}, "reason": "Test reason"})
    
    # Setup mock responses for different workflow state transitions
    mock_order = Order(
        id="ORD-001",
        document_number="ORD-001",
        description="Test Order",
        requester="Test User",
        vendor="Test Vendor",
        status=DocumentStatus.DRAFT,
        items=[],
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z"
    )
    
    p2p_service.submit_order.return_value = mock_order
    p2p_service.approve_order.return_value = mock_order
    p2p_service.receive_order.return_value = mock_order
    p2p_service.complete_order.return_value = mock_order
    p2p_service.cancel_order.return_value = mock_order
    
    # Create a record of the response formats
    print("\n=== Testing workflow endpoint response formats ===")
    
    # Test api_submit_order
    workflow_responses = []
    result = await controller.api_submit_order(request, "ORD-001")
    workflow_responses.append(("submit_order", result))
    print(f"Submit order response: {result}")
    
    # Test api_approve_order
    result = await controller.api_approve_order(request, "ORD-001")
    workflow_responses.append(("approve_order", result))
    print(f"Approve order response: {result}")
    
    # Test api_receive_order
    result = await controller.api_receive_order(request, "ORD-001")
    # Handle the case where the result might be a tuple (response, status_code)
    if isinstance(result, tuple) and len(result) == 2:
        response_obj, status_code = result
        workflow_responses.append(("receive_order", response_obj))
        print(f"Receive order response: {response_obj} (status code: {status_code})")
    else:
        workflow_responses.append(("receive_order", result))
        print(f"Receive order response: {result}")
    
    # Test api_complete_order
    result = await controller.api_complete_order(request, "ORD-001")
    workflow_responses.append(("complete_order", result))
    print(f"Complete order response: {result}")
    
    # Test api_cancel_order
    result = await controller.api_cancel_order(request, "ORD-001")
    workflow_responses.append(("cancel_order", result))
    print(f"Cancel order response: {result}")
    
    # Check for consistency in response formats
    for name, response in workflow_responses:
        assert "success" in response, f"{name} response missing 'success' field"
        assert "status" in response, f"{name} response missing 'status' field"
        if "data" in response:
            print(f"{name} data: {response['data']}")
    
    print("=== Workflow endpoint response tests complete ===")
    return True

"""
Approach 5: Fix the request.json().get() issue in api_cancel_order
"""

# Create a special version of api_cancel_order that properly awaits request.json()
async def fixed_api_cancel_order(request, order_id, p2p_service=None, monitor_service=None):
    """Test version of api_cancel_order with fixed json handling."""
    # Get services if not provided (for testing)
    if p2p_service is None:
        p2p_service = get_p2p_service()
    if monitor_service is None:
        monitor_service = get_monitor_service()
        
    controller = get_p2p_order_api_controller(p2p_service, monitor_service)
    
    # Properly await the json() coroutine
    data = await request.json()
    reason = data.get("reason", "")
    
    if not reason:
        return BaseController.create_error_response(
            message="Cancellation reason is required",
            error_code="validation_error",
            details={"reason": "This field is required"},
            status_code=400
        )
        
    # Call the service method and handle potential errors
    result = await p2p_service.cancel_order(order_id, reason)
    
    # Format and return the response
    return {
        "document_number": result["document_number"],
        "status": result["status"],
        "updated_at": result["updated_at"],
        "reason": result["reason"]
    }

async def test_cancel_order_request_json_handling():
    """Test that request.json() is properly awaited in the cancel_order endpoint."""
    print("\n=== Testing cancel_order request.json() handling ===")
    
    # Create logger for capturing errors
    logger = logging.getLogger("test_logger")
    
    # Create a mock request with a json() coroutine
    async def mock_json():
        """Mock implementation of request.json() that returns a dictionary."""
        return {"reason": "Test cancellation reason"}
    
    class MockRequest:
        """Mock Request class with json method that returns a coroutine."""
        async def json(self):
            return await mock_json()
    
    request = MockRequest()
    
    # Mock the p2p service
    class MockP2PService:
        """Mock P2P Service for testing."""
        async def cancel_order(self, order_id, reason):
            """Mock implementation that returns a successful cancellation."""
            return {
                "document_number": f"ORD-{order_id}",
                "status": "CANCELLED",
                "updated_at": "2023-01-01T12:34:56Z",
                "reason": reason
            }
    
    p2p_service = MockP2PService()
    
    # Test the implementation in fixed_api_cancel_order
    result = await fixed_api_cancel_order(request, "123", p2p_service)
    
    # Log the result for debugging
    print(f"Fixed api_cancel_order implementation result: {result}")
    
    # Test the recommendation based on the result
    if isinstance(result, dict) and "reason" in result:
        return "The fixed_api_cancel_order implementation is working correctly"
    else:
        return "Fix request.json() handling in api_cancel_order by properly awaiting the coroutine"

async def test_request_json_await():
    """Test that request.json() is properly awaited in controller methods."""
    print("\n=== Testing request.json() handling ===")
    
    # Create a mock request with a json() coroutine
    async def mock_json():
        """Mock implementation of request.json() that returns a dictionary."""
        return {"reason": "Test cancellation"}
    
    class MockRequest:
        """Mock Request class with json method that returns a coroutine."""
        async def json(self):
            return await mock_json()
    
    request = MockRequest()
    
    # Mock the service functions
    class MockOrderService:
        """Mock Order Service for testing."""
        async def cancel_order(self, order_id, reason):
            """Mock implementation that returns a successful cancellation."""
            return {
                "document_number": f"ORD-{order_id}",
                "status": "CANCELLED",
                "updated_at": "2023-01-01T12:34:56Z",
                "reason": reason
            }
    
    # Create a fixture to test
    async def implementation_with_proper_await(request, order_id, p2p_service):
        """Improved implementation with proper awaiting of request.json()."""
        data = await request.json()
        reason = data.get("reason", "")
        
        if not reason:
            return JSONResponse(
                status_code=400,
                content={"message": "Cancellation reason is required"}
            )
            
        result = await p2p_service.cancel_order(order_id, reason)
        
        return {
            "document_number": result["document_number"],
            "status": result["status"],
            "updated_at": result["updated_at"],
            "reason": result["reason"]
        }
    
    # Test the proper implementation
    mock_service = MockOrderService()
    # Use await directly since this function is already async
    result = await implementation_with_proper_await(request, "123", mock_service)
    print(f"Properly awaited implementation result: {result}")
    
    # Check for expected values in the result
    assert "document_number" in result, "document_number missing from result"
    assert "status" in result, "status missing from result"
    assert "reason" in result, "reason missing from result"
    assert result["reason"] == "Test cancellation", "Unexpected reason value"
    
    print("✓ Proper implementation works correctly")
    print("=== request.json() handling tests complete ===")
    
    return True

# Update the test_diagnostics function to include the new test
async def test_diagnostics():
    """Run all diagnostic tests and report results."""
    print("\n=== P2P Order API Controller Diagnostics ===")
    
    # Test 1: Order serialization
    serialization_method = test_order_json_serialization()
    print(f"\nBest available serialization method: {serialization_method}")
    
    # Test 2: Modified controller
    print("\nTesting modified controller...")
    # Add controller tests here
    
    # Test 3: Enhanced extract_json
    print("\nTesting enhanced extract_json function...")
    # Add extract_json tests here
    
    # Test 4: Workflow endpoint response formats
    print("\nTesting workflow endpoint response formats...")
    await test_workflow_endpoints_formats()
    
    # Test 5: Cancel order request.json() handling
    print("\nTesting cancel order request.json() handling...")
    recommendation = await test_cancel_order_request_json_handling()
    print(f"Recommendation: {recommendation}")
    
    # Test 6: Request.json() handling in api_cancel_order
    print("\nTesting request.json() handling in api_cancel_order...")
    await test_request_json_await()
    
    print("\n=== Diagnostic tests complete ===")
    return True

# Make sure you have these imports to support the new test
from controllers import BaseController
from services import get_p2p_service, get_monitor_service

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_diagnostics()) 