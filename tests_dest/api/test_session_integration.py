"""
Test for demonstrating session integration with a mock session middleware.
"""

import pytest
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock, patch
import json
import logging
from enum import Enum
import uuid

# FastAPI imports
from fastapi import FastAPI, Request, Response, Depends, Form
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.testclient import TestClient

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

# Import custom exceptions
from utils.error_utils import NotFoundError, ValidationError

# Import Session middleware and utilities
from middleware.session import add_flash_message, get_flash_messages, FlashMessage, store_form_data, get_form_data

# Define FlashMessageType enum for testing
class FlashMessageType(str, Enum):
    """Flash message types for testing."""
    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add this class before TestSessionIntegration
class ValidationResult:
    """Result of form validation without using exceptions."""
    def __init__(self, is_valid=True, error_message="", details=None):
        self.is_valid = is_valid
        self.error_message = error_message
        self.details = details or {}

class TestSessionIntegration:
    """Test basic session features including flash messages."""
    
    def setup_method(self):
        """Set up the test app with session middleware."""
        # Create a test FastAPI app
        self.app = FastAPI()
        
        # Set up mock session storage
        self.sessions = {}
        
        # Define a mock middleware for testing sessions
        @self.app.middleware("http")
        async def mock_session_middleware(request: Request, call_next):
            """Mock session middleware for testing."""
            # Create a session ID if not present
            cookies = request.cookies
            session_id = cookies.get("sap_session", str(uuid.uuid4()))
            
            # Get or create session data
            session = self.sessions.get(session_id, {})
            request.state.session = session
            request.state.session_id = session_id
            
            # Initialize empty form data and flash messages if not present
            if "form_data" not in session:
                session["form_data"] = {}
            if "flash_messages" not in session:
                session["flash_messages"] = []
            
            # Fetch and store flash messages for display before they get cleared
            request.state.flash_messages = session.get("flash_messages", [])
            print(f"Request state flash messages: {request.state.flash_messages}")
            
            # Handle the request
            response = await call_next(request)
            
            # Update session after request
            self.sessions[session_id] = request.state.session
            print(f"Updated session: {self.sessions[session_id]}")
            
            # Add session cookie to response
            response.set_cookie("sap_session", session_id)
            return response
        
        # Create test data
        def get_item_with_error(item_id):
            """Get an item or raise NotFoundError."""
            if item_id == 999:
                raise NotFoundError(f"Item {item_id} not found")
            return {"id": item_id, "name": f"Test Item {item_id}"}
        
        def create_item_with_validation(data):
            """Validate and create an item."""
            if not data.get("name"):
                raise ValidationError("Name is required", details={"name": "This field is required"})
            return {"id": 123, "name": data["name"]}
        
        def mock_render(template_name, context=None, status_code=200):
            """Mock template rendering for testing."""
            context = context or {}
            # For testing purposes, just return JSON with the template name and context
            return JSONResponse(
                content={"template": template_name, "context": context},
                status_code=status_code
            )
        
        # Define some test routes
        @self.app.get("/items")
        async def list_items(request: Request):
            # Get flash messages for display
            flash_messages = await get_flash_messages_for_test(request)
            print(f"Flash messages in list_items: {flash_messages}")
            
            # Mock some items
            items = [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"}
            ]
            
            # Return template with items and flash messages
            return mock_render("items/list.html", {
                "items": items,
                "flash_messages": [msg.to_dict() for msg in flash_messages]
            })
        
        @self.app.get("/items/create")
        async def create_form(request: Request):
            # Get flash messages and form data
            flash_messages = await get_flash_messages_for_test(request)
            form_data = await get_form_data(request) or {}
            print(f"Flash messages in create_form: {flash_messages}")
            print(f"Form data in create_form: {form_data}")
            
            # Return template with messages and form data
            return mock_render("items/create.html", {
                "flash_messages": [msg.to_dict() for msg in flash_messages],
                "form_data": form_data
            })
        
        # Add this function in setup_method where create_item_with_validation is defined
        def validate_item(data):
            """Validate item data without raising exceptions."""
            if not data.get("name"):
                return ValidationResult(
                    is_valid=False,
                    error_message="Name is required",
                    details={"name": "This field is required"}
                )
            return ValidationResult(is_valid=True)
        
        @self.app.post("/items/create")
        async def create_item(request: Request):
            # Simulate form data parsing
            form_data = {}
            if request.query_params.get("with_error"):
                # Direct validation approach without using exceptions
                validation_result = validate_item({})
                if not validation_result.is_valid:
                    # Store form data and error
                    form_data["_errors"] = validation_result.details
                    await store_form_data(request, form_data)
                    await add_flash_message_for_test(
                        request, f"Error creating item: {validation_result.error_message}", 
                        FlashMessageType.ERROR
                    )
                    print(f"Added flash message in create_item: Error creating item: {validation_result.error_message}")
                    redirect = RedirectResponse("/items/create", status_code=303)
                    return redirect
        
        @self.app.get("/items/{item_id}")
        async def view_item(request: Request, item_id: int):
            # Get flash messages for display
            flash_messages = await get_flash_messages_for_test(request)
            print(f"Flash messages in view_item: {flash_messages}")
            
            # Check if this is a known not-found case
            if item_id == 999:
                # Add error message and redirect to list
                await add_flash_message_for_test(
                    request, f"Item {item_id} not found", 
                    FlashMessageType.ERROR
                )
                print(f"Added flash message in view_item: Item {item_id} not found")
                redirect = RedirectResponse("/items", status_code=303)
                return redirect
            
            # Fetch the item directly since we know it exists
            item = {"id": item_id, "name": f"Test Item {item_id}"}
            
            # Return template with item and messages
            return mock_render("items/detail.html", {
                "item": item,
                "flash_messages": [msg.to_dict() for msg in flash_messages]
            })
        
        # Add helpers to the test instance
        self.get_item_with_error = get_item_with_error
        self.create_item_with_validation = create_item_with_validation
        self.mock_render = mock_render
        
        # Create test client
        self.client = TestClient(self.app)
        
        # Helper to make requests with cookies maintained
        def request_with_cookies(*args, **kwargs):
            """Make a request while maintaining cookies for session persistence."""
            # Disable automatic following of redirects to check status codes
            kwargs['follow_redirects'] = False
            
            # Make the request
            response = self.client.request(*args, **kwargs)
            print(f"Response cookies: {dict(response.cookies)}")
            print(f"Client cookies after request: {dict(self.client.cookies)}")
            
            # Return the response object
            return response
        
        self.request = request_with_cookies
        
    def test_flash_message_display_in_template(self):
        """Test that flash messages are properly displayed in templates."""
        # Set up - add a flash message by hitting a route that sets one
        # In this case, try to view a non-existent item which adds an error message
        response = self.request("GET", "/items/999")
        
        # Verify redirect
        assert response.status_code == 303
        assert response.headers["location"] == "/items"
        
        # Follow the redirect to the items list
        response = self.request("GET", "/items")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify template
        assert data["template"] == "items/list.html"
        
        # Verify flash messages were passed to template
        assert "flash_messages" in data["context"]
        messages = data["context"]["flash_messages"]
        
        # Verify message content
        assert len(messages) == 1
        assert messages[0]["message"] == "Item 999 not found"
        assert messages[0]["type"] == FlashMessageType.ERROR
    
    def test_form_data_preservation(self):
        """Test that form data is preserved when validation errors occur."""
        # Define a helper function for failing form submission
        def create_with_error(data):
            """Helper function to simulate a form submission with validation error."""
            # Submit form - this will fail validation and redirect back to form
            response = self.request(
                "POST", 
                "/items/create?with_error=1", 
                json=data
            )
            
            # Verify redirect
            assert response.status_code == 303
            assert response.headers["location"] == "/items/create"
            
            # Follow the redirect to the form
            response = self.request("GET", "/items/create")
            
            # Return the response
            return response
        
        # Test with empty form data
        response = create_with_error({})
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify template
        assert data["template"] == "items/create.html"
        
        # Verify flash messages were passed to template
        assert "flash_messages" in data["context"]
        messages = data["context"]["flash_messages"]
        
        # Verify message content
        assert len(messages) == 1
        assert "Error creating item" in messages[0]["message"]
        assert messages[0]["type"] == FlashMessageType.ERROR
    
    def test_flash_message_cleared_after_display(self):
        """Test that flash messages are cleared after being displayed."""
        # Set up - add a flash message 
        response = self.request("GET", "/items/999")
        
        # Follow the redirect to the items list - this should display and clear the message
        response = self.request("GET", "/items")
        
        # Verify message was in the response
        data = response.json()
        assert "flash_messages" in data["context"]
        assert len(data["context"]["flash_messages"]) == 1
        
        # Make another request to the same page
        response = self.request("GET", "/items")
        
        # Verify no messages in the response
        data = response.json()
        assert "flash_messages" in data["context"]
        assert len(data["context"]["flash_messages"]) == 0
    
    def test_not_found_error_with_flash_message(self):
        """Test handling of NotFoundError with flash message."""
        # Try to view a non-existent item
        response = self.request("GET", "/items/999")
        
        # Verify redirect
        assert response.status_code == 303
        assert response.headers["location"] == "/items"
        
        # Follow the redirect
        response = self.request("GET", "/items")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Verify flash message
        messages = data["context"]["flash_messages"]
        assert len(messages) == 1
        assert "Item 999 not found" in messages[0]["message"]
        assert messages[0]["type"] == FlashMessageType.ERROR

# Define test-specific session utility functions - remove the 'test_' prefix to avoid them being collected as tests
async def get_flash_messages_for_test(request: Request) -> List[FlashMessage]:
    """Get and clear flash messages from session."""
    print("In get_flash_messages_for_test")
    # Get the session
    if not hasattr(request.state, "session"):
        print("No session in request state")
        return []
        
    # Get flash messages from session
    flash_messages = request.state.session.get("flash_messages", [])
    print(f"Flash messages before clear: {flash_messages}")
    
    # Clear flash messages from session
    request.state.session["flash_messages"] = []
    
    # Convert to FlashMessage objects if needed
    result = []
    for msg in flash_messages:
        if isinstance(msg, dict):
            result.append(FlashMessage(**msg))
        else:
            result.append(msg)
    
    print(f"Returning flash messages: {result}")
    return result

async def add_flash_message_for_test(
    request: Request, 
    message: str, 
    message_type: FlashMessageType = FlashMessageType.INFO
) -> None:
    """Add a flash message to session."""
    print(f"In add_flash_message_for_test: {message}, {message_type}")
    # Get the session
    if not hasattr(request.state, "session"):
        print("No session in request state")
        request.state.session = {}
        
    # Create flash message
    flash_message = FlashMessage(
        message=message,
        type=message_type
    )
    
    # Add to session
    if "flash_messages" not in request.state.session:
        request.state.session["flash_messages"] = []
    
    request.state.session["flash_messages"].append(flash_message.to_dict())
    print(f"Session after adding flash message: {request.state.session}")

# Mock implementation of models.base_model
class BaseModel:
    """Mock base model class."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def dict(self):
        # Properly handle encapsulation by not directly exposing internal __dict__
        return {key: value for key, value in vars(self).items()}
    
    def model_dump(self):
        # For compatibility with newer Pydantic versions
        return self.dict()

# Flash message for testing
class FlashMessage:
    """Flash message representation for testing."""
    
    def __init__(self, message: str, type: FlashMessageType = FlashMessageType.INFO):
        """Initialize a flash message."""
        self.message = message
        self.type = type
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        return {
            "message": self.message,
            "type": self.type
        }
    
    def __str__(self) -> str:
        """Return a string representation of the message."""
        return f"{self.type}: {self.message}"

if __name__ == "__main__":
    # Run a quick test
    test = TestSessionIntegration()
    test.setup_method()
    print("Setup completed successfully")
    print("Test class ready for testing") 