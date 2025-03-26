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
"""
Diagnostic test for controller integration with session middleware.

This file provides a diagnostic environment to test how controllers should
interact with the session middleware, particularly for form handling and
flash messages.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import asyncio

from fastapi import FastAPI, Request, Response, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Dynamically determine project root and add to path
file_path = Path(__file__).resolve()
test_dir = file_path.parent.parent
project_root = test_dir.parent
# Import session middleware components
from middleware.session import (
    SessionMiddleware,
    get_session,
    add_flash_message,
    get_flash_messages,
    store_form_data,
    get_form_data,
    clear_form_data
)

# Import controller session utilities
from controllers.session_utils import (
    get_template_context_with_session,
    handle_form_error,
    handle_form_validation_error,
    redirect_with_success,
    redirect_with_error
)

# Import error utilities
from utils.error_utils import ValidationError, NotFoundError

# Define result classes for service operations
class ServiceResult:
    """Base result class for service operations."""
    
    def __init__(self, success=True, data=None, error_message=None):
        self.success = success
        self.data = data
        self.error_message = error_message


class ValidationResult:
    """Result class for validation operations."""
    
    def __init__(self, is_valid=True, details=None, error_message=None):
        self.is_valid = is_valid
        self.details = details or {}
        self.error_message = error_message


class MockService:
    """Mock service for testing."""

    def __init__(self, name="generic"):
        self.name = name
        self.called_methods = []
        self.should_fail = False
        self.should_fail_validation = False
        self.should_fail_not_found = False
    
    async def get_items(self):
        """Get a list of items."""
        self.called_methods.append(("get_items", {}))
        
        if self.should_fail:
            return ServiceResult(success=False, error_message="Service method failed")
            
        items = [{"id": "1", "name": "Item 1"}, {"id": "2", "name": "Item 2"}]
        return ServiceResult(success=True, data=items)
    
    async def create_item(self, data):
        """Create a new item."""
        self.called_methods.append(("create_item", data))
        
        if self.should_fail:
            return ServiceResult(success=False, error_message="Service method failed")
            
        if self.should_fail_validation:
            return ServiceResult(
                success=False, 
                error_message="Validation failed", 
                data={"field": "Invalid value"}
            )
            
        return ServiceResult(
            success=True, 
            data={"id": "123", "status": "created", **data}
        )
    
    async def get_item(self, item_id):
        """Get an item by ID."""
        self.called_methods.append(("get_item", item_id))
        
        if self.should_fail:
            return ServiceResult(success=False, error_message="Service method failed")
            
        if self.should_fail_not_found or item_id == "999":
            return ServiceResult(
                success=False, 
                error_message=f"Item {item_id} not found"
            )
            
        return ServiceResult(
            success=True, 
            data={"id": item_id, "name": f"Test Item {item_id}", "description": "Test description"}
        )


# Form validation function
def validate_form_data(form_data):
    """Validate form data and return result."""
    if not form_data.get("name"):
        return ValidationResult(
            is_valid=False,
            details={"name": "Name is required"},
            error_message="Validation failed: Name is required"
        )
    return ValidationResult(is_valid=True)

# Mock template class definition
class MockTemplate:
    """Mock template service for testing."""

    def __init__(self):
        self.rendered_templates = []
        self.rendered_contexts = []

    async def render_template(self, template_name: str, context: Dict[str, Any]) -> HTMLResponse:
        """Mock render template method."""
        self.rendered_templates.append(template_name)
        self.rendered_contexts.append(context)
        return HTMLResponse(
            content=f"<html><body>Template: {template_name}, Context: {context}</body></html>"
        )

async def test_controller_with_session():
    """Create a test controller with session integration."""
    app = FastAPI()
    
    # Add session middleware
    app.add_middleware(
        SessionMiddleware,
        session_cookie="test_session",
        secure=False
    )
    
    # Create mock services
    mock_service = MockService("item_service")
    mock_template = MockTemplate()
    
    # Create controller routes demonstrating proper session integration
    @app.get("/items")
    async def list_items(request: Request):
        """List items with flash messages from session."""
        # Get items from service (simulated)
        items_result = await mock_service.get_items()
        
        # Check if the service call succeeded
        if not items_result.success:
            # Create error flash message
            await add_flash_message(
                request, 
                f"Error loading items: {items_result.error_message}", 
                message_type="error"
            )
            items = []
        else:
            items = items_result.data
        
        # Prepare template context with session data
        context = get_template_context_with_session(request, {
            "title": "Items List",
            "items": items
        })
        
        # Render template with context
        return await mock_template.render_template("items/list.html", context)
    
    @app.get("/items/create")
    async def create_item_form(request: Request):
        """Display item creation form."""
        # Prepare template context with session data (including any preserved form data)
        context = get_template_context_with_session(request, {
            "title": "Create Item"
        })
        
        # Render template with context
        return await mock_template.render_template("items/create.html", context)
    
    @app.post("/items/create")
    async def process_create_item_form(request: Request):
        """Process item creation form with session integration."""
        # Parse form data (simulated)
        form_data = {"name": "Test Item", "description": "Test Description"}
        
        # Validate form data (simulated)
        validation_result = validate_form_data(form_data)
        if not validation_result.is_valid:
            # Store validation errors in session
            await handle_form_validation_error(request, form_data, validation_result.details)
            return RedirectResponse("/items/create", status_code=303)
        
        # If validation passed, create item (simulated)
        creation_result = await mock_service.create_item(form_data)
        if not creation_result.success:
            # Handle service error
            await handle_form_error(request, form_data, f"Error creating item: {creation_result.error_message}")
            return RedirectResponse("/items/create", status_code=303)
        
        # On success, add success flash message
        await add_flash_message(
            request, 
            "Item created successfully", 
            message_type="success"
        )
        
        # Redirect to items list
        return RedirectResponse("/items", status_code=303)
    
    @app.get("/items/{item_id}")
    async def view_item(request: Request, item_id: str):
        """View item details."""
        # Get item from service
        item_result = await mock_service.get_item(item_id)
        
        # Check if item exists
        if not item_result.success:
            # Add error message to session
            await add_flash_message(
                request, 
                f"Item not found: {item_result.error_message}", 
                message_type="error"
            )
            
            # Redirect to items list
            return RedirectResponse("/items", status_code=303)
        
        # Prepare template context with session data
        context = get_template_context_with_session(request, {
            "title": f"Item: {item_result.data['name']}",
            "item": item_result.data
        })
        
        # Render template with context
        return await mock_template.render_template("items/detail.html", context)
    
    # Client test function
    def test_client_flow():
        """Test client flow for controller with session integration."""
        client = TestClient(app)
        
        print("\n=== Testing success flow ===")
        print("1. Get create form")
        response1 = client.get("/items/create")
        cookies1 = client.cookies
        
        print(f"Create form response status: {response1.status_code}")
        print(f"Rendered template: {mock_template.rendered_templates[-1]}")
        print(f"Context: {mock_template.rendered_contexts[-1]}")
        
        print("\n2. Submit form successfully")
        response2 = client.post("/items/create", cookies=cookies1)
        cookies2 = client.cookies
        
        print(f"Form submission response status: {response2.status_code}")
        print(f"Redirected to: {response2.headers.get('location')}")
        
        print("\n3. View items list with success flash message")
        response3 = client.get("/items", cookies=cookies2)
        
        print(f"List view response status: {response3.status_code}")
        if mock_template.rendered_templates:
            print(f"Rendered template: {mock_template.rendered_templates[-1]}")
            context = mock_template.rendered_contexts[-1]
            print(f"Flash messages: {context.get('flash_messages', [])}")
        
        # Reset for error flow
        mock_template.rendered_templates = []
        mock_template.rendered_contexts = []
        mock_service.should_fail_validation = True
        
        print("\n=== Testing validation error flow ===")
        print("1. Get create form")
        response4 = client.get("/items/create")
        cookies4 = client.cookies
        
        print("\n2. Submit form with validation error")
        response5 = client.post("/items/create", cookies=cookies4)
        cookies5 = client.cookies
        
        print(f"Form submission with error response status: {response5.status_code}")
        print(f"Redirected to: {response5.headers.get('location')}")
        
        print("\n3. View form again with errors and preserved data")
        response6 = client.get("/items/create", cookies=cookies5)
        
        print(f"Form view response status: {response6.status_code}")
        if mock_template.rendered_templates:
            print(f"Rendered template: {mock_template.rendered_templates[-1]}")
            context = mock_template.rendered_contexts[-1]
            print(f"Flash messages: {context.get('flash_messages', [])}")
            print(f"Form data: {context.get('form_data', {})}")
            print(f"Errors: {context.get('errors', {})}")
        
        # Test not found error
        mock_service.should_fail_validation = False
        mock_service.should_fail_not_found = True
        
        print("\n=== Testing not found error flow ===")
        response7 = client.get("/items/999", cookies=cookies5)
        
        print(f"Not found response status: {response7.status_code}")
        print(f"Redirected to: {response7.headers.get('location')}")
        
        # Check service calls
        print("\nService method calls:")
        for method, args in mock_service.called_methods:
            print(f"- {method}: {args}")
    
    # Run the test client flow
    test_client_flow()
    
    return app, mock_service, mock_template

if __name__ == "__main__":
    asyncio.run(test_controller_with_session()) 