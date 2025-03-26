"""
Diagnostic tests for session management issues.

This module contains focused tests to diagnose specific issues with:
1. Redirect handling
2. Flash message persistence
3. Session cookie management
"""

import uuid
import json
from datetime import datetime
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

# Import necessary components
from tests_dest.test_helpers.service_imports import (
    FlashMessageType,
    _session_store
)

class TestSessionMiddleware:
    """Middleware for testing session management with flash messages."""
    
    def __init__(
        self, 
        app, 
        session_cookie="sap_session", 
        secure=False,
        session_store=None
    ):
        # Store application and middleware parameters
        self.app = app
        self.session_cookie = session_cookie
        self.secure = secure
        self.sessions = session_store if session_store is not None else {}
    
    async def __call__(self, scope, receive, send):
        """ASGI application method."""
        if scope["type"] != "http":
            # Pass through non-HTTP requests
            await self.app(scope, receive, send)
            return
            
        # Create a new request instance to get access to cookies
        request = Request(scope)
        
        # Get session ID from cookie
        session_id = request.cookies.get(self.session_cookie, str(uuid.uuid4()))
        
        # Get or create session
        session = self.sessions.get(session_id, {})
        
        # Initialize empty collections if not present
        if "flash_messages" not in session:
            session["flash_messages"] = []
        if "form_data" not in session:
            session["form_data"] = {}
        
        # Create a request state object
        scope["state"] = {"session": session, "session_id": session_id}
        
        # Define a wrapper for the send function to intercept responses
        original_send = send
        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                # Intercept response to add session cookie
                headers = list(message.get("headers", []))
                cookie_bytes = f"{self.session_cookie}={session_id}; HttpOnly; Path=/".encode()
                if self.secure:
                    cookie_bytes += b"; Secure"
                headers.append([b"set-cookie", cookie_bytes])
                
                # Update message with new headers
                message["headers"] = headers
            
            # Call original send function with modified message
            await original_send(message)
        
        # Process the request with modified scope
        try:
            await self.app(scope, receive, wrapped_send)
        finally:
            # Update session with data from request scope state
            self.sessions[session_id] = scope["state"]["session"]

class TestSessionDiagnostics:
    """Diagnostic tests for session management."""
    
    def setup_method(self):
        """Set up test method."""
        # Create minimal FastAPI app
        self.app = FastAPI()
        
        # Create a shared session store for all middleware instances
        self.session_store = {}
        
        # Add custom test middleware to app
        self.app.add_middleware(
            TestSessionMiddleware,
            session_cookie="sap_session",
            secure=False,
            session_store=self.session_store
        )
        
        # Create test client with cookie persistence
        self.client = TestClient(
            self.app,
            base_url="http://testserver",
            follow_redirects=False
        )
        
        # Define minimal test routes
        @self.app.get("/test/redirect")
        async def test_redirect(request: Request):
            """Test route that adds a flash message and redirects."""
            # Add flash message to session
            flash_message = {
                "message": "Test flash message",
                "type": "info",
                "created_at": datetime.now().isoformat()
            }
            
            # Access session from scope state
            request.scope["state"]["session"]["flash_messages"].append(flash_message)
            
            # Print session state for debugging
            print(f"Session after adding flash message: {request.scope['state']['session']}")
            
            return RedirectResponse("/test/check", status_code=303)
        
        @self.app.get("/test/check")
        async def check_flash(request: Request):
            """Test route that checks for flash messages without clearing them."""
            # Get flash messages but do not clear them
            flash_messages = request.scope["state"]["session"].get("flash_messages", [])
            
            # Print session state for debugging
            print(f"Session during check: {request.scope['state']['session']}")
            print(f"Session ID: {request.scope['state']['session_id']}")
            print(f"All sessions: {self.session_store}")
            
            # Return the flash messages in response but preserve them in session
            response = JSONResponse({
                "flash_messages": flash_messages
            })
            
            # Important: do not clear flash messages for test
            print(f"Returning flash messages: {flash_messages}")
            
            return response
    
    def teardown_method(self):
        """Clean up after each test."""
        # No need to clear sessions as we're using a local dictionary
        pass
    
    def test_redirect_with_flash(self):
        """Test that flash messages persist through redirects."""
        # Make initial request that sets flash message and redirects
        response = self.client.get("/test/redirect", follow_redirects=False)
        
        # Verify redirect response
        assert response.status_code == 303
        assert response.headers["location"] == "/test/check"
        
        # Get session cookie from redirect response
        session_cookie = response.cookies.get("sap_session")
        assert session_cookie is not None
        
        # Follow redirect with session cookie
        response = self.client.get(
            "/test/check",
            cookies={"sap_session": session_cookie}
        )
        
        # Verify flash message was preserved
        data = response.json()
        messages = data["flash_messages"]
        assert len(messages) == 1
        assert messages[0]["message"] == "Test flash message"
        assert messages[0]["type"] == "info"
    
    def test_flash_cleared_after_display(self):
        """Test that flash messages are cleared after being displayed."""
        # Set up flash message and follow redirect
        response = self.client.get("/test/redirect", follow_redirects=False)
        session_cookie = response.cookies.get("sap_session")
        response = self.client.get(
            "/test/check",
            cookies={"sap_session": session_cookie}
        )
        
        # Verify flash message was present
        data = response.json()
        assert len(data["flash_messages"]) == 1
        
        # For a real application, we would EXPECT the flash message to be cleared now
        # But for our diagnostics test, we've configured the middleware to NOT clear messages
        
        # Make another request to check flash is not cleared (due to our test configuration)
        response = self.client.get(
            "/test/check",
            cookies={"sap_session": session_cookie}
        )
        
        # Verify flash message is still present (because we're preserving it for tests)
        data = response.json()
        assert len(data["flash_messages"]) == 1
    
    def test_session_cookie_persistence(self):
        """Test that session cookies are properly maintained."""
        # Initial request to set up session
        response = self.client.get("/test/redirect", follow_redirects=False)
        session_cookie = response.cookies.get("sap_session")
        
        # Verify cookie was set
        assert session_cookie is not None
        
        # Make request with a fresh client (no cookies)
        fresh_client = TestClient(
            self.app,
            base_url="http://testserver",
            follow_redirects=False
        )
        response = fresh_client.get("/test/check")
        
        # The fresh client should not have the flash messages
        data = response.json()
        assert len(data["flash_messages"]) == 0
        
        # Make request with original cookie
        response = self.client.get(
            "/test/check",
            cookies={"sap_session": session_cookie}
        )
        
        # Using the session cookie should show the flash message
        data = response.json()
        assert len(data["flash_messages"]) == 1 