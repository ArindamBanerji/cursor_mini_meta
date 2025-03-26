"""
Debug test for session middleware.

This is a minimal test to debug issues with session middleware.
"""

import sys
import os
import logging
from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Dynamically determine project root and add to path
file_path = Path(__file__).resolve()
test_dir = file_path.parent.parent
project_root = test_dir.parent
sys.path.insert(0, str(project_root))

# Now we can import from the middleware package
from middleware.session import (
    SessionMiddleware,
    get_session,
    add_flash_message,
    get_flash_messages,
    store_form_data,
    get_form_data
)

def debug_session_middleware():
    """Debug function for session middleware."""
    print("Debugging session middleware")
    
    # Create a test app
    app = FastAPI()
    
    # Add session middleware
    app.add_middleware(
        SessionMiddleware,
        session_cookie="debug_session",
        secure=False
    )
    
    # Create test routes
    @app.get("/add-flash")
    async def add_flash(request: Request):
        """Add flash messages to session."""
        add_flash_message(request, "Debug message", "info")
        add_flash_message(request, "Error debug", "error")
        session = get_session(request)
        logger.debug(f"Session after adding flash: {session}")
        return {"status": "ok", "session": session}
    
    @app.get("/get-flash")
    async def get_flash(request: Request):
        """Get flash messages from session."""
        messages = get_flash_messages(request)
        session = get_session(request)
        logger.debug(f"Session after getting flash: {session}")
        return {
            "status": "ok",
            "messages": [{"message": m.message, "type": m.type} for m in messages],
            "session": session
        }
    
    @app.post("/add-form")
    async def add_form(request: Request):
        """Add form data to session."""
        form_data = {"name": "Debug User", "email": "debug@example.com"}
        store_form_data(request, form_data)
        session = get_session(request)
        logger.debug(f"Session after adding form: {session}")
        return {"status": "ok", "session": session}
    
    @app.get("/get-form")
    async def get_form(request: Request):
        """Get form data from session."""
        form_data = get_form_data(request)
        session = get_session(request)
        logger.debug(f"Session after getting form: {session}")
        return {"status": "ok", "form_data": form_data, "session": session}
    
    # Create a test client that preserves cookies
    client = TestClient(app, cookies={})
    
    # Test flash messages
    print("Testing flash messages...")
    resp1 = client.get("/add-flash")
    print(f"Add flash response: {resp1.json()}")
    
    # Get cookies and ensure they're passed in next request
    cookies = client.cookies
    print(f"Cookies after add-flash: {cookies}")
    
    resp2 = client.get("/get-flash", cookies=cookies)
    print(f"Get flash response: {resp2.json()}")
    
    # Test form data
    print("Testing form data...")
    resp3 = client.post("/add-form")
    print(f"Add form response: {resp3.json()}")
    
    # Get cookies and ensure they're passed in next request
    cookies = client.cookies
    print(f"Cookies after add-form: {cookies}")
    
    resp4 = client.get("/get-form", cookies=cookies)
    print(f"Get form response: {resp4.json()}")
    
    print("Debug complete")

if __name__ == "__main__":
    debug_session_middleware() 