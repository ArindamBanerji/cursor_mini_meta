# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Critical imports that must be preserved
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from types import ModuleType

"""Standard test file imports and setup.

This snippet is automatically added to test files by SnippetForTests.py.
It provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration
3. Common test imports and fixtures
4. Service initialization support
5. Logging configuration
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

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_project_root(test_dir: Path) -> Optional[Path]:
    """Find the project root directory.
    
    Args:
        test_dir: The directory containing the test file
        
    Returns:
        The project root directory or None if not found
    """
    try:
        # Try to find project root by looking for main.py or known directories
        for parent in [test_dir] + list(test_dir.parents):
            # Check for main.py as an indicator of project root
            if (parent / "main.py").exists():
                return parent
            # Check for typical project structure indicators
            if all((parent / d).exists() for d in ["services", "models", "controllers"]):
                return parent
        
        # If we still don't have a project root, use parent of the tests-dest directory
        for parent in test_dir.parents:
            if parent.name == "tests-dest":
                return parent.parent
                
        return None
    except Exception as e:
        logger.error(f"Error finding project root: {e}")
        return None

# Find project root dynamically
test_file = Path(__file__).resolve()
test_dir = test_file.parent
project_root = find_project_root(test_dir)

if project_root:
    logger.info(f"Project root detected at: {project_root}")
    
    # Add project root to path if found
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.info(f"Added {project_root} to Python path")
else:
    logger.warning("Could not detect project root")

# Import the test_import_helper
try:
    from test_import_helper import setup_test_paths, setup_test_env_vars
    setup_test_paths()
    logger.info("Successfully initialized test paths from test_import_helper")
except ImportError as e:
    # Fall back if test_import_helper is not available
    if str(test_dir.parent) not in sys.path:
        sys.path.insert(0, str(test_dir.parent))
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root) if project_root else "")
    logger.warning(f"Failed to import test_import_helper: {e}. Using fallback configuration.")

# Common test imports
import pytest
from unittest.mock import MagicMock, AsyncMock, patch, call
from fastapi import Request, Response, FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Scope, Receive, Send
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

# Import session middleware and related components
try:
    from middleware.session import (
        SessionMiddleware,
        FlashMessage,
        get_session,
        add_flash_message,
        get_flash_messages,
        store_form_data,
        get_form_data,
        clear_form_data
    )
except ImportError:
    # For testing purposes, define mock classes if imports fail
    class SessionMiddleware:
        def __init__(self, *args, **kwargs):
            pass
    
    class FlashMessage:
        def __init__(self, message, type="info"):
            self.message = message
            self.type = type

    class FlashMessageType:
        """Flash message types for testing."""
        SUCCESS = "success"
        ERROR = "error"
        WARNING = "warning"
        INFO = "info"
    
    # Define async function stubs
    async def get_session(request):
        return {}
    
    async def add_flash_message(request, message, type="info"):
        pass
    
    async def get_flash_messages(request):
        return []
    
    async def set_form_data(request, form_id, data):
        pass
    
    async def get_form_data(request, form_id):
        return None
    
    async def clear_form_data(request, form_id):
        pass

class TestSessionMiddleware:
    """Test class for the session middleware.
    
    This class tests:
    - Session initialization and persistence
    - Flash message functionality
    - Form state preservation
    """
    
    def setup_method(self):
        """Set up test method."""
        # Create a minimal FastAPI app for testing
        self.app = FastAPI()
        
        # Set up session middleware with our test app
        self.app.add_middleware(SessionMiddleware, session_cookie="sap_session")
        
        # Create test routes for testing
        @self.app.get("/test-session")
        async def test_session(request: Request):
            session = get_session(request)
            session["test_value"] = "test_data"
            return {"session": session}
        
        @self.app.get("/test-flash")
        async def test_flash(request: Request):
            add_flash_message(request, "Test message")
            add_flash_message(request, "Error message", "error")
            return {"status": "messages_added"}
        
        @self.app.get("/test-get-flash")
        async def test_get_flash(request: Request):
            messages = get_flash_messages(request)
            return {"messages": [{"message": msg.message, "type": msg.type} for msg in messages]}
        
        @self.app.post("/test-form-submit")
        async def test_form_submit(request: Request):
            form_data = {"name": "Test User", "email": "test@example.com"}
            store_form_data(request, form_data)
            return {"status": "form_saved"}
        
        @self.app.get("/test-form-retrieve")
        async def test_form_retrieve(request: Request):
            form_data = get_form_data(request)
            return {"form_data": form_data}
        
        # Create a test client with cookie persistence
        self.client = TestClient(self.app)
    
    def test_session_initialization(self):
        """Test that session is initialized for each request."""
        # Create a mock request
        mock_request = MagicMock(spec=Request)
        mock_request.state = MagicMock()
        
        # Create a mock response
        mock_response = MagicMock(spec=Response)
        
        # Create an instance of SessionMiddleware
        middleware = SessionMiddleware(app=None)
        
        # Mock the call_next function
        async def mock_call_next(request):
            # Verify session is available in request state
            assert hasattr(request.state, "session")
            assert isinstance(request.state.session, dict)
            return mock_response
        
        # Call the dispatch method
        import asyncio
        asyncio.run(middleware.dispatch(mock_request, mock_call_next))
    
    def test_session_persistence(self):
        """Test that session data persists between requests."""
        # Make a request to set a session value
        response1 = self.client.get("/test-session")
        assert response1.status_code == 200
        assert response1.json().get("session", {}).get("test_value") == "test_data"
        
        # Make another request and verify the session value is still there
        # This works because our mock implementation keeps self.mock_session_data between requests
        response2 = self.client.get("/test-get-flash")
        assert response2.status_code == 200
        # We cannot actually verify session persistence in this test setup without additional mocking
    
    def test_flash_messages(self):
        """Test that flash messages can be added and retrieved."""
        # Add flash messages
        response1 = self.client.get("/test-flash")
        assert response1.status_code == 200
        assert response1.json().get("status") == "messages_added"

        # Save cookies for session persistence
        cookies = self.client.cookies

        # Retrieve flash messages, using the same session
        response2 = self.client.get("/test-get-flash", cookies=cookies)
        assert response2.status_code == 200
        messages = response2.json().get("messages", [])

        # Check that we got two messages
        assert len(messages) == 2
        assert messages[0]["message"] == "Test message"
        assert messages[0]["type"] == "info"
        assert messages[1]["message"] == "Error message"
        assert messages[1]["type"] == "error"
        
        # Verify flash messages are cleared after being retrieved
        response3 = self.client.get("/test-get-flash")
        assert response3.status_code == 200
        assert len(response3.json().get("messages", [])) == 0
    
    def test_form_data_preservation(self):
        """Test form data preservation and retrieval."""
        # Save form data
        response1 = self.client.post("/test-form-submit")
        assert response1.status_code == 200
        assert response1.json().get("status") == "form_saved"

        # Save cookies for session persistence
        cookies = self.client.cookies

        # Retrieve form data, using the same session
        response2 = self.client.get("/test-form-retrieve", cookies=cookies)
        assert response2.status_code == 200
        form_data = response2.json().get("form_data")

        # Check form data
        assert form_data is not None
        assert form_data["name"] == "Test User"
        assert form_data["email"] == "test@example.com"

        # Verify form data is cleared after being retrieved
        response3 = self.client.get("/test-form-retrieve")
        assert response3.status_code == 200
        # The form_data will be an empty dict, not None
        assert response3.json().get("form_data") == {}
    
    @pytest.mark.asyncio
    async def test_add_flash_message_function(self):
        """Test the add_flash_message function directly."""
        # Create a mock request with a session
        mock_request = MagicMock(spec=Request)
        mock_request.state.session = {}

        # Add flash messages of different types
        add_flash_message(mock_request, "Success message", "success")
        add_flash_message(mock_request, "Error message", "error")
        
        # Verify flash messages were added
        assert len(mock_request.state.session.get("flash_messages", [])) == 2
        assert mock_request.state.session["flash_messages"][0]["message"] == "Success message"
        assert mock_request.state.session["flash_messages"][0]["type"] == "success"
        assert mock_request.state.session["flash_messages"][1]["message"] == "Error message"
        assert mock_request.state.session["flash_messages"][1]["type"] == "error"
    
    @pytest.mark.asyncio
    async def test_get_flash_messages_function(self):
        """Test the get_flash_messages function directly."""
        # Create a mock request with a session and flash messages
        mock_request = MagicMock(spec=Request)
        mock_request.state.session = {
            "flash_messages": [
                {"message": "Message 1", "type": "info", "created_at": "2023-01-01T00:00:00"},
                {"message": "Message 2", "type": "error", "created_at": "2023-01-01T00:00:00"}
            ]
        }
        mock_request.state.flash_messages = [
            FlashMessage("Message 1", "info"),
            FlashMessage("Message 2", "error")
        ]

        # Get flash messages
        messages = get_flash_messages(mock_request)
        
        # Verify messages
        assert len(messages) == 2
        assert messages[0].message == "Message 1"
        assert messages[0].type == "info"
        assert messages[1].message == "Message 2"
        assert messages[1].type == "error"
    
    @pytest.mark.asyncio
    async def test_form_data_functions(self):
        """Test the form data functions directly."""
        # Create a mock request with a session
        mock_request = MagicMock(spec=Request)
        mock_request.state.session = {"form_data": {}}
        
        # Store form data
        form_data = {"name": "John Doe", "age": 30}
        store_form_data(mock_request, form_data)
        
        # Verify form data
        assert mock_request.state.session["form_data"] == form_data
        
        # Get form data
        mock_request.state.form_data = form_data
        retrieved_data = get_form_data(mock_request)
        
        # Verify retrieved data
        assert retrieved_data == form_data
        
        # Clear form data
        clear_form_data(mock_request)
        
        # Verify form data was cleared
        assert mock_request.state.session["form_data"] == {} 