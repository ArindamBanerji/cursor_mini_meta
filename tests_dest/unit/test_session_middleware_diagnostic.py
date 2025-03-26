"""
Diagnostic tests for session middleware.

This file contains tests to diagnose issues with session middleware integration.
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

import pytest
import logging
import json
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from middleware.session import (
    get_session, 
    get_flash_messages, 
    add_flash_message,
    store_form_data,
    get_form_data,
    clear_form_data,
    SessionMiddleware,
    FlashMessage
)

# Setup logging
logger = logging.getLogger(__name__)

class TestSessionMiddlewareDiagnostic:
    """Test session middleware functionality."""
    
    def setup_method(self):
        """Set up test method."""
        # Initialize mock session data
        self.mock_session_data = {}
        
        # Create a test app
        self.app = FastAPI()
        
        # Add session middleware
        self.app.add_middleware(
            SessionMiddleware,
            session_cookie="test_session",
            secure=False
        )
        
        # Create test routes
        @self.app.get("/test-flash")
        async def test_flash(request: Request):
            """Test endpoint to add flash messages."""
            add_flash_message(request, "Test message", "info")
            add_flash_message(request, "Error message", "error")
            return {"status": "messages_added"}
        
        @self.app.get("/test-get-flash")
        async def test_get_flash(request: Request):
            """Test endpoint to retrieve flash messages."""
            flash_messages = get_flash_messages(request)
            messages = [
                {"message": msg.message, "type": msg.type}
                for msg in flash_messages
            ]
            return {"messages": messages}
        
        @self.app.post("/test-form-submit")
        async def test_form_submit(request: Request):
            """Test endpoint to store form data."""
            form_data = {"name": "Test User", "email": "test@example.com"}
            store_form_data(request, form_data)
            return {"status": "form_saved"}
        
        @self.app.get("/test-form-retrieve")
        async def test_form_retrieve(request: Request):
            """Test endpoint to retrieve form data."""
            form_data = get_form_data(request)
            return {"form_data": form_data}
        
        @self.app.get("/test-session-inspect")
        async def test_session_inspect(request: Request):
            """Test endpoint to inspect the session."""
            session = get_session(request)
            return {
                "session": session,
                "has_flash_messages": "flash_messages" in session,
                "has_form_data": "form_data" in session
            }
        
        # Create a test client
        self.client = TestClient(self.app)
    
    def test_flash_message_diagnostic(self):
        """Test the flash message flow to diagnose issues."""
        # Add flash messages
        response1 = self.client.get("/test-flash")
        assert response1.status_code == 200
        
        # Inspect session
        response_inspect = self.client.get("/test-session-inspect")
        assert response_inspect.status_code == 200
        session_data = response_inspect.json()
        print(f"Session after adding flash messages: {json.dumps(session_data, indent=2)}")
        
        # Retrieve flash messages
        response2 = self.client.get("/test-get-flash")
        assert response2.status_code == 200
        messages = response2.json().get("messages", [])
        print(f"Retrieved flash messages: {json.dumps(messages, indent=2)}")
        
        # Inspect session again
        response_inspect2 = self.client.get("/test-session-inspect")
        assert response_inspect2.status_code == 200
        session_data2 = response_inspect2.json()
        print(f"Session after retrieving flash messages: {json.dumps(session_data2, indent=2)}")
    
    def test_form_data_diagnostic(self):
        """Test the form data preservation flow to diagnose issues."""
        # Save form data
        response1 = self.client.post("/test-form-submit")
        assert response1.status_code == 200
        
        # Inspect session
        response_inspect = self.client.get("/test-session-inspect")
        assert response_inspect.status_code == 200
        session_data = response_inspect.json()
        print(f"Session after adding form data: {json.dumps(session_data, indent=2)}")
        
        # Retrieve form data
        response2 = self.client.get("/test-form-retrieve")
        assert response2.status_code == 200
        form_data = response2.json().get("form_data")
        print(f"Retrieved form data: {json.dumps(form_data, indent=2)}")
        
        # Inspect session again
        response_inspect2 = self.client.get("/test-session-inspect")
        assert response_inspect2.status_code == 200
        session_data2 = response_inspect2.json()
        print(f"Session after retrieving form data: {json.dumps(session_data2, indent=2)}") 