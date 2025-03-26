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
sys.path.insert(0, str(project_root))

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

class MockService:
    """Mock service for testing."""
    
    def __init__(self, name="generic"):
        self.name = name
        self.called_methods = []
        self.should_fail = False
        self.should_raise_validation = False
        self.should_raise_not_found = False
    
    async def create_item(self, data: Dict[str, Any]):
        self.called_methods.append(("create_item", data))
        if self.should_fail:
            raise Exception("Service method failed")
        if self.should_raise_validation:
            raise ValidationError("Validation failed", {"field": "Invalid value"})
        if self.should_raise_not_found:
            raise NotFoundError("Item not found")
        return {"id": "123", "status": "created", **data}
    
    async def get_item(self, item_id: str):
        self.called_methods.append(("get_item", item_id))
        if self.should_fail:
            raise Exception("Service method failed")
        if self.should_raise_not_found:
            raise NotFoundError(f"Item {item_id} not found")
        return {"id": item_id, "name": "Test Item", "status": "active"}

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
        try:
            # Get items from service (simulated)
            items = [{"id": "1", "name": "Item 1"}, {"id": "2", "name": "Item 2"}]
            
            # Prepare template context with session data
            context = get_template_context_with_session(request, {
                "items": items,
                "title": "Items List"
            })
            
            # Render template with context
            return await mock_template.render_template("items/list.html", context)
        except Exception as e:
            # Log error and redirect with error message
            logger.error(f"Error listing items: {str(e)}")
            return await redirect_with_error("/", request, f"Error listing items: {str(e)}")
    
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
        try:
            # Parse form data (simulated)
            form_data = {"name": "Test Item", "description": "Test Description"}
            
            # Validate form data (simulated)
            if not form_data.get("name"):
                errors = {"name": "Name is required"}
                # Handle validation errors - store form data, add flash message
                await handle_form_validation_error(request, form_data, errors)
                return RedirectResponse("/items/create", status_code=303)
            
            # Process data with service
            result = await mock_service.create_item(form_data)
            
            # Handle successful creation - add success message and redirect
            return await redirect_with_success(
                "/items", 
                request, 
                f"Item '{form_data['name']}' created successfully"
            )
        except ValidationError as e:
            # Handle validation errors
            await handle_form_validation_error(request, form_data, e.details)
            return RedirectResponse("/items/create", status_code=303)
        except Exception as e:
            # Handle unexpected errors
            await handle_form_error(request, form_data, f"Error creating item: {str(e)}")
            return RedirectResponse("/items/create", status_code=303)
    
    @app.get("/items/{item_id}")
    async def view_item(request: Request, item_id: str):
        """View item details."""
        try:
            # Get item from service
            item = await mock_service.get_item(item_id)
            
            # Prepare template context with session data
            context = get_template_context_with_session(request, {
                "item": item,
                "title": f"Item - {item['name']}"
            })
            
            # Render template with context
            return await mock_template.render_template("items/detail.html", context)
        except NotFoundError as e:
            # Handle not found error - add flash message and redirect
            return await redirect_with_error("/items", request, str(e))
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Error viewing item: {str(e)}")
            return await redirect_with_error("/items", request, f"Error viewing item: {str(e)}")
    
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
        mock_service.should_raise_validation = True
        
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
        mock_service.should_raise_validation = False
        mock_service.should_raise_not_found = True
        
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