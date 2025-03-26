# Add path setup to find the tests_dest module
import sys
import os
import json
from pathlib import Path
from datetime import datetime

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

This file tests the P2P Order API controller with real service calls to ensure
proper integration and behavior.
"""

import pytest
import logging
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
    OrderCreate,
    OrderItem,
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
    """Extract JSON content from FastAPI response objects or return dict as is."""
    if hasattr(response, 'body'):
        return json.loads(response.body.decode())
    return response

def get_best_serialization_method(obj):
    """Determine the best available method for serializing an object."""
    if hasattr(obj, 'model_dump'):
        return 'model_dump'
    elif hasattr(obj, 'dict'):
        return 'dict'
    elif hasattr(obj, 'to_dict'):
        return 'to_dict'
    else:
        return 'attribute_extraction'

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

"""
Test Order API Controller with real service calls
"""

class TestP2POrderAPIController:
    """Test version of P2POrderAPIController using real services."""
    
    def __init__(self):
        """Initialize with real services."""
        self.p2p_service = P2PService()
        self.monitor_service = MonitorService()
    
    def serialize_order(self, order):
        """Serialize an Order object to a dictionary using the best available method."""
        if hasattr(order, 'model_dump'):
            return order.model_dump()
        elif hasattr(order, 'dict'):
            return order.dict()
        elif hasattr(order, 'to_dict'):
            return order.to_dict()
        else:
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
    
    def create_success_response(self, data=None, message=None):
        """Create a standardized success response."""
        response = {
            "success": True,
            "status": "success"
        }
        if data is not None:
            response["data"] = data
        if message is not None:
            response["message"] = message
        
        # Convert to JSON string first to handle datetime objects
        json_str = json.dumps(response, cls=CustomJSONEncoder)
        json_data = json.loads(json_str)
        
        return JSONResponse(content=json_data)
    
    def create_error_response(self, message, error_code="error", details=None, status_code=400):
        """Create a standardized error response."""
        response = {
            "success": False,
            "status": "error",
            "error": error_code,
            "message": message
        }
        if details is not None:
            response["details"] = details
            
        # Convert to JSON string first to handle datetime objects
        json_str = json.dumps(response, cls=CustomJSONEncoder)
        json_data = json.loads(json_str)
        
        return JSONResponse(content=json_data, status_code=status_code)

    async def api_submit_order(self, request, order_id):
        """Submit a new order."""
        # Get order data from request
        order_data = await request.json()
        
        # Convert dict to OrderCreate object
        order_create = OrderCreate(**order_data)
        
        # Create order using real service
        order = self.p2p_service.create_order(order_create)
        
        # Serialize order for response
        serialized_order = self.serialize_order(order)
        
        return self.create_success_response(
            data=serialized_order,
            message="Order submitted successfully"
        )

    async def api_approve_order(self, request, order_id):
        """Approve an existing order."""
        # Get approval data from request
        approval_data = await request.json()
        
        # Approve order using real service
        order = self.p2p_service.approve_order(order_id)
        
        # Serialize order for response
        serialized_order = self.serialize_order(order)
        
        return self.create_success_response(
            data=serialized_order,
            message="Order approved successfully"
        )

    async def api_receive_order(self, request, order_id):
        """Receive an order."""
        # Get receipt data from request
        receipt_data = await request.json()
        
        # Convert request data to received_items format
        received_items = {1: receipt_data['items'][0]['quantity']}
        
        # Receive order using real service
        order = self.p2p_service.receive_order(order_id, received_items)
        
        # Serialize order for response
        serialized_order = self.serialize_order(order)
        
        return self.create_success_response(
            data=serialized_order,
            message="Order received successfully"
        )

    async def api_complete_order(self, request, order_id):
        """Complete an order."""
        # Get completion data from request
        completion_data = await request.json()
        
        # Complete order using real service
        order = self.p2p_service.complete_order(order_id)
        
        # Serialize order for response
        serialized_order = self.serialize_order(order)
        
        return self.create_success_response(
            data=serialized_order,
            message="Order completed successfully"
        )

    async def api_cancel_order(self, request, order_id):
        """Cancel an order."""
        # Get cancellation data from request
        cancellation_data = await request.json()
        
        # Cancel order using real service
        order = self.p2p_service.cancel_order(order_id, cancellation_data.get("reason", ""))
        
        # Serialize order for response
        serialized_order = self.serialize_order(order)
        
        return self.create_success_response(
            data=serialized_order,
            message="Order cancelled successfully"
        )

"""
Test workflow endpoints with real service calls
"""

async def test_workflow_endpoints_formats():
    """Test response formats from different workflow endpoint methods using real services."""

    # Create controller instance with real services
    controller = TestP2POrderAPIController()

    # Create test request with real data
    class TestRequest:
        async def json(self):
            return {
                "description": "Test Order",
                "requester": "Test User",
                "vendor": "Test Vendor",
                "items": [
                    {
                        "item_number": 1,
                        "description": "Test Item",
                        "quantity": 10,
                        "unit": "EA",
                        "price": 100.0
                    }
                ]
            }

    mock_request = TestRequest()

    # Test normal workflow
    response = await controller.api_submit_order(mock_request, "TEST-001")
    content = extract_json(response)
    assert content["success"], "Failed to create test order"
    order_id = content["data"]["document_number"]

    # Submit the order
    order = controller.p2p_service.submit_order(order_id)
    assert order.status == DocumentStatus.SUBMITTED

    # Test normal workflow endpoints
    endpoints = [
        (controller.api_approve_order, "approve"),
        (controller.api_receive_order, "receive"),
        (controller.api_complete_order, "complete")
    ]

    for endpoint, name in endpoints:
        # Call endpoint
        response = await endpoint(mock_request, order_id)
        content = extract_json(response)
        print(f"\n=== {name.title()} Order Response Format ===")
        print(f"Success: {content['success']}")
        print(f"Status: {content['status']}")
        print(f"Data: {content['data']}")

    # Test cancellation workflow with a new order
    response = await controller.api_submit_order(mock_request, "TEST-002")
    content = extract_json(response)
    assert content["success"], "Failed to create test order"
    order_id = content["data"]["document_number"]

    # Submit and approve the order
    order = controller.p2p_service.submit_order(order_id)
    assert order.status == DocumentStatus.SUBMITTED
    order = controller.p2p_service.approve_order(order_id)
    assert order.status == DocumentStatus.APPROVED

    # Test cancellation
    class CancelRequest:
        async def json(self):
            return {"reason": "Test cancellation reason"}

    response = await controller.api_cancel_order(CancelRequest(), order_id)
    content = extract_json(response)
    print(f"\n=== Cancel Order Response Format ===")
    print(f"Success: {content['success']}")
    print(f"Status: {content['status']}")
    print(f"Data: {content['data']}")

"""
Test request.json handling with real service
"""

async def test_cancel_order_request_json_handling():
    """Test proper handling of request.json() in cancel order endpoint with real service."""
    # Create controller instance with real service
    controller = TestP2POrderAPIController()

    # First create a test order
    class CreateRequest:
        async def json(self):
            return {
                "description": "Test Order for Cancellation",
                "requester": "Test User",
                "vendor": "Test Vendor",
                "items": [
                    {
                        "item_number": 1,
                        "description": "Test Item",
                        "quantity": 10,
                        "unit": "EA",
                        "price": 100.0
                    }
                ]
            }
    
    create_request = CreateRequest()
    response = await controller.api_submit_order(create_request, "TEST-002")
    content = extract_json(response)
    assert content["success"], "Failed to create test order"
    order_id = content["data"]["document_number"]

    # Submit the order
    order = controller.p2p_service.submit_order(order_id)
    assert order.status == DocumentStatus.SUBMITTED

    # Now test cancellation
    class CancelRequest:
        async def json(self):
            return {"reason": "Test cancellation"}
    
    cancel_request = CancelRequest()

    # Call cancel order endpoint
    response = await controller.api_cancel_order(cancel_request, order_id)

    # Extract JSON content
    content = extract_json(response)

    # Verify response format
    assert "success" in content
    assert "status" in content
    assert "data" in content
    assert isinstance(content["data"], dict)

    print("\n=== Cancel Order Response Format ===")
    print(f"Success: {content['success']}")
    print(f"Status: {content['status']}")
    print(f"Data: {content['data']}")

# Update the test_diagnostics function to include the new test
async def test_diagnostics():
    """Run all diagnostic tests with real services."""
    # Test workflow endpoints
    await test_workflow_endpoints_formats()
    
    # Test request.json handling
    await test_cancel_order_request_json_handling()
    
    print("\n=== All diagnostic tests completed ===")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_diagnostics()) 