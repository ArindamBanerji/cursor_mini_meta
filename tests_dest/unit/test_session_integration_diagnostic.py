"""
Diagnostic test for session integration with controllers.

This test focuses on determining how session middleware interacts with controllers,
particularly looking at flash messages and form data preservation.
"""
        # Add project root to path
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        logging.warning("Could not find import_helper.py. Using fallback configuration.")
except Exception as e:
    logging.warning(f"Failed to import import_helper: {{e}}. Using fallback configuration.")
    # Add project root to path
    current_file = Path(__file__).resolve()
    test_dir = current_file.parent.parent
    project_root = test_dir.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any, List, Optional

# Try to add the project root to the path
test_dir = Path(__file__).parent.parent
project_root = test_dir.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request, Response, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

# Import session middleware components if available
try:
    from middleware.session import (
        SessionMiddleware, FlashMessage, FlashMessageType,
        add_flash_message, get_flash_messages, set_form_data, get_form_data
    )
except ImportError:
    # Define minimums if not available
    class FlashMessageType:
        SUCCESS = "success"
        ERROR = "error"
        INFO = "info"
        WARNING = "warning"
    
    class FlashMessage:
        def __init__(self, message: str, type: str = FlashMessageType.INFO):
            self.message = message
            self.type = type
    
    class SessionMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, session_cookie: str = "test_session"):
            super().__init__(app)
            self.session_cookie = session_cookie
            self.session_store = {}
        
        async def dispatch(self, request: Request, call_next) -> Response:
            # Initialize empty session
            request.state.session = {}
            
            # Get session from cookie
            session_id = request.cookies.get(self.session_cookie)
            if session_id and session_id in self.session_store:
                request.state.session = self.session_store[session_id]
            
            # Call next middleware
            response = await call_next(request)
            
            # Store session
            session_id = session_id or "test_session_id"
            self.session_store[session_id] = request.state.session
            
            # Set cookie
            response.set_cookie(
                key=self.session_cookie,
                value=session_id,
                httponly=True,
                max_age=1800
            )
            
            return response
    
    async def add_flash_message(request: Request, message: str, type: str = "info") -> None:
        """Add a flash message to the session."""
        session = getattr(request.state, "session", {})
        if "flash_messages" not in session:
            session["flash_messages"] = []
        session["flash_messages"].append({"message": message, "type": type})
    
    async def get_flash_messages(request: Request) -> List[dict]:
        """Get flash messages from the session."""
        session = getattr(request.state, "session", {})
        return session.get("flash_messages", [])
    
    async def set_form_data(request: Request, form_id: str, data: Dict[str, Any]) -> None:
        """Store form data in the session."""
        session = getattr(request.state, "session", {})
        if "form_data" not in session:
            session["form_data"] = {}
        session["form_data"][form_id] = data
    
    async def get_form_data(request: Request, form_id: str) -> Optional[Dict[str, Any]]:
        """Get form data from the session."""
        session = getattr(request.state, "session", {})
        if "form_data" not in session:
            return None
        return session["form_data"].get(form_id)

# Define error classes for testing
class ValidationError(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.message = message
        self.errors = errors or {}

class NotFoundError(Exception):
    pass

class TestSessionIntegrationDiagnostic:
    """Diagnostic test for session integration with controllers."""
    
    def setup_method(self):
        """Set up test environment."""
        self.app = FastAPI()
        
        # Add session middleware
        self.middleware = SessionMiddleware(self.app, session_cookie="test_session")
        self.app.add_middleware(SessionMiddleware, session_cookie="test_session")
        
        # Define mock service for testing
        class MockService:
            def create_item(self, data):
                if not data.get("name"):
                    raise ValidationError("Name is required")
                return {"id": 1, "name": data.get("name")}
            
            def get_item(self, item_id):
                if item_id == 999:
                    raise NotFoundError("Item not found")
                return {"id": item_id, "name": f"Item {item_id}"}
        
        self.service = MockService()
        
        # Define controller routes
        @self.app.get("/items/create")
        async def create_form(request: Request):
            """Display create form."""
            # Check for form data from previous submission
            form_data = await get_form_data(request, "item_form")
            
            return {
                "template": "items/create.html",
                "context": {
                    "form_data": form_data,
                    "flash_messages": await get_flash_messages(request)
                }
            }
        
        @self.app.post("/items/create")
        async def create_item(request: Request):
            """Process create form."""
            # Get form data from request
            form_data = {"name": "Test Item"}
            
            try:
                # Try to create item
                item = self.service.create_item(form_data)
                
                # Add success message
                await add_flash_message(
                    request, 
                    f"Item created successfully: {item['name']}",
                    FlashMessageType.SUCCESS
                )
                
                # Redirect to view
                return RedirectResponse(url="/items", status_code=303)
            except ValidationError as e:
                # Store form data for redisplay
                await set_form_data(request, "item_form", form_data)
                
                # Add error message
                await add_flash_message(
                    request,
                    f"Validation error: {e.message}",
                    FlashMessageType.ERROR
                )
                
                # Redirect back to form
                return RedirectResponse(url="/items/create", status_code=303)
            except Exception as e:
                # Log and handle unexpected errors
                print(f"Unexpected error in create_item: {str(e)}")
                await add_flash_message(
                    request,
                    f"An unexpected error occurred: {str(e)}",
                    FlashMessageType.ERROR
                )
                return RedirectResponse(url="/items/create", status_code=303)
        
        @self.app.get("/items")
        async def list_items(request: Request):
            """List items with flash messages."""
            return {
                "template": "items/list.html",
                "context": {
                    "items": [{"id": 1, "name": "Item 1"}],
                    "flash_messages": await get_flash_messages(request)
                }
            }
        
        @self.app.get("/items/{item_id}")
        async def view_item(request: Request, item_id: int):
            """View item details."""
            try:
                item = self.service.get_item(item_id)
                return {
                    "template": "items/view.html",
                    "context": {
                        "item": item,
                        "flash_messages": await get_flash_messages(request)
                    }
                }
            except NotFoundError as e:
                await add_flash_message(
                    request,
                    f"Error: {str(e)}",
                    FlashMessageType.ERROR
                )
                return RedirectResponse(url="/items", status_code=303)
        
        # Create test client
        self.client = TestClient(self.app)
    
    def test_flash_message_flow(self):
        """Test flash messages flow between requests."""
        # Visit create form
        response1 = self.client.get("/items/create")
        assert response1.status_code == 200
        data1 = response1.json()
        print(f"Response 1: {data1}")
        assert data1["template"] == "items/create.html"
        assert "flash_messages" in data1["context"]
        
        # Submit form successfully - don't follow redirects
        response2 = self.client.post("/items/create", follow_redirects=False)
        print(f"Response 2 status: {response2.status_code}")
        print(f"Response 2 headers: {response2.headers}")
        
        # Manually check for redirect
        assert response2.status_code in (302, 303)
        assert "location" in response2.headers
        redirect_url = response2.headers["location"]
        assert redirect_url == "/items"
        
        # Follow redirect to list view
        response3 = self.client.get(redirect_url)
        assert response3.status_code == 200
        data3 = response3.json()
        print(f"Response 3: {data3}")
        
        # Check flash message was displayed
        assert data3["template"] == "items/list.html"
        assert "flash_messages" in data3["context"]
        messages = data3["context"]["flash_messages"]
        print(f"Flash messages in response: {messages}")
        assert len(messages) > 0
        assert "Item created successfully" in str(messages)
    
    def test_form_data_preservation(self):
        """Test form data is preserved on validation error."""
        # Replace the create_item method with one that raises an error
        original_create = self.service.create_item
        
        def create_with_error(data):
            raise ValidationError("Name is required")
        
        self.service.create_item = create_with_error
        
        try:
            # Visit create form
            response1 = self.client.get("/items/create")
            assert response1.status_code == 200
            
            # Submit form with error - don't follow redirects
            response2 = self.client.post("/items/create", follow_redirects=False)
            print(f"Error response status: {response2.status_code}")
            print(f"Error response headers: {response2.headers}")
            
            # Manually check for redirect
            assert response2.status_code in (302, 303)
            assert "location" in response2.headers
            redirect_url = response2.headers["location"]
            assert redirect_url == "/items/create"
            
            # Follow redirect back to form
            response3 = self.client.get(redirect_url)
            assert response3.status_code == 200
            data3 = response3.json()
            print(f"Form data preservation response: {data3}")
            
            # Check form data was preserved
            assert "form_data" in data3["context"]
            form_data = data3["context"]["form_data"]
            print(f"Form data retrieved: {form_data}")
            assert form_data is not None
            assert "name" in form_data
            
            # Check error message was displayed
            assert "flash_messages" in data3["context"]
            messages = data3["context"]["flash_messages"]
            print(f"Flash messages: {messages}")
            assert len(messages) > 0
            assert "Validation error" in str(messages)
        finally:
            # Restore original method
            self.service.create_item = original_create
    
    def test_not_found_error_handling(self):
        """Test handling of not found errors with redirect and flash message."""
        # Try to view non-existent item - don't follow redirects
        response1 = self.client.get("/items/999", follow_redirects=False)
        print(f"Not found response status: {response1.status_code}")
        print(f"Not found response headers: {response1.headers}")
        
        # Manually check for redirect
        assert response1.status_code in (302, 303)
        assert "location" in response1.headers
        redirect_url = response1.headers["location"]
        assert redirect_url == "/items"
        
        # Follow redirect to list view
        response2 = self.client.get(redirect_url)
        assert response2.status_code == 200
        data2 = response2.json()
        print(f"Redirect response data: {data2}")
        
        # Check error message was displayed
        assert "flash_messages" in data2["context"]
        messages = data2["context"]["flash_messages"]
        print(f"Flash messages: {messages}")
        assert len(messages) > 0
        assert "Error:" in str(messages)
        assert "not found" in str(messages).lower()

if __name__ == "__main__":
    # Run the diagnostic test directly
    test = TestSessionIntegrationDiagnostic()
    try:
        test.setup_method()
        print("\n=== Testing Flash Message Flow ===")
        test.test_flash_message_flow()
        print("\n=== Testing Form Data Preservation ===")
        test.test_form_data_preservation()
        print("\n=== Testing Not Found Error Handling ===")
        test.test_not_found_error_handling()
        print("\n=== All diagnostic tests passed! ===")
    except Exception as e:
        import traceback
        print(f"\n=== Test failed with error: ===\n{str(e)}")
        traceback.print_exc()
    finally:
        print("\n=== Diagnostic test complete ===\n") 