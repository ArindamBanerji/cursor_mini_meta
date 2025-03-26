# middleware/session.py
"""
Session middleware for the SAP Test Harness.

This module provides session management functionality for the FastAPI application,
including:
- Session storage and retrieval
- Flash messages for user feedback
- Form data preservation for error handling
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Union

from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send, Message

# Configure logging
logger = logging.getLogger("middleware.session")

class FlashMessage:
    """
    Flash message model for temporary user notifications.
    
    Flash messages are designed to be displayed once after a redirect
    and then cleared automatically.
    """
    
    # Message types with Bootstrap color classes
    TYPES = {
        "success": "success",
        "error": "danger",
        "warning": "warning",
        "info": "info"
    }
    
    def __init__(self, message: str, type: str = "info"):
        """
        Initialize a flash message.
        
        Args:
            message: The message text to display
            type: Message type (success, error, warning, info)
        """
        self.message = message
        self.type = type if type in self.TYPES else "info"
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "message": self.message,
            "type": self.type,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FlashMessage':
        """Create from dictionary"""
        msg = cls(
            message=data.get("message", ""),
            type=data.get("type", "info")
        )
        # Set created_at if provided
        if "created_at" in data:
            try:
                msg.created_at = datetime.fromisoformat(data["created_at"])
            except (ValueError, TypeError):
                pass  # Use default creation time
        return msg
    
    @property
    def bootstrap_class(self) -> str:
        """Get the Bootstrap alert class for this message type"""
        return f"alert-{self.TYPES.get(self.type, 'info')}"

class SessionStore:
    """
    In-memory session storage.
    
    This is a simple implementation for the MVP. In a production environment,
    this would be replaced with a more robust solution like Redis.
    """
    
    def __init__(self, expiry_minutes: int = 30):
        """
        Initialize the session store.
        
        Args:
            expiry_minutes: Session expiry time in minutes
        """
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._expiry_minutes = expiry_minutes
        self._expiry_times: Dict[str, datetime] = {}
        logger.info(f"Initialized session store with {expiry_minutes} minute expiry")
    
    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session data or None if not found or expired
        """
        # Check if session exists
        if session_id not in self._sessions:
            return None
        
        # Check if session has expired
        if self._is_expired(session_id):
            self.delete(session_id)
            return None
        
        # Update expiry time
        self._refresh_expiry(session_id)
        
        return self._sessions[session_id]
    
    def set(self, session_id: str, data: Dict[str, Any]) -> None:
        """
        Set session data.
        
        Args:
            session_id: Session identifier
            data: Session data to store
        """
        self._sessions[session_id] = data
        self._refresh_expiry(session_id)
    
    def delete(self, session_id: str) -> None:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
        
        if session_id in self._expiry_times:
            del self._expiry_times[session_id]
    
    def create(self) -> str:
        """
        Create a new session.
        
        Returns:
            New session identifier
        """
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {}
        self._refresh_expiry(session_id)
        return session_id
    
    def _refresh_expiry(self, session_id: str) -> None:
        """
        Refresh session expiry time.
        
        Args:
            session_id: Session identifier
        """
        self._expiry_times[session_id] = datetime.now() + timedelta(minutes=self._expiry_minutes)
    
    def _is_expired(self, session_id: str) -> bool:
        """
        Check if session has expired.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if expired, False otherwise
        """
        if session_id not in self._expiry_times:
            return True
        
        return datetime.now() > self._expiry_times[session_id]
    
    def cleanup(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions removed
        """
        expired_sessions = [
            session_id for session_id in self._sessions.keys()
            if self._is_expired(session_id)
        ]
        
        for session_id in expired_sessions:
            self.delete(session_id)
        
        return len(expired_sessions)

# Global session store
_session_store = SessionStore()

class SessionMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for session management.
    
    This middleware handles:
    - Creating and retrieving sessions
    - Managing session cookies
    - Updating request and response objects with session data
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        session_cookie: str = "sap_session", 
        secure: bool = False,
        expiry_minutes: int = 30
    ):
        """
        Initialize session middleware.
        
        Args:
            app: FastAPI application
            session_cookie: Name of the session cookie
            secure: Whether to use secure cookies (HTTPS)
            expiry_minutes: Session expiry time in minutes
        """
        super().__init__(app)
        self.session_cookie = session_cookie
        self.secure = secure
        self.expiry_minutes = expiry_minutes
        
        # Use the global session store
        self._session_store = _session_store
        
        logger.info(f"Initialized SessionMiddleware with cookie name '{session_cookie}'")
    
    def _get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID."""
        return self._session_store.get(session_id)
    
    def _set_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Set session data."""
        self._session_store.set(session_id, data)
    
    def _delete_session(self, session_id: str) -> None:
        """Delete a session."""
        self._session_store.delete(session_id)
    
    def _create_session(self) -> str:
        """Create a new session."""
        return self._session_store.create()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process a request and handle session management.
        
        This method:
        1. Gets or creates a session
        2. Adds session data to request state
        3. Processes the request
        4. Updates the session cookie
        5. Cleans up flash messages and form data
        
        Args:
            request: FastAPI request
            call_next: ASGI application callable
            
        Returns:
            Response with session cookie
        """
        # Get session ID from cookie
        session_id = request.cookies.get(self.session_cookie)
        
        # Get or create session
        if session_id:
            session_data = self._get_session(session_id)
            if not session_data:
                session_id = self._create_session()
                session_data = {}
        else:
            session_id = self._create_session()
            session_data = {}
        
        # Add session data to request state
        request.state.session = session_data
        request.state.session_id = session_id
        
        # Get flash messages and form data
        flash_messages = await self._get_flash_messages(session_data)
        form_data = await self._get_form_data(session_data)
        
        # Add to request state
        request.state.flash_messages = flash_messages
        request.state.form_data = form_data
        
        # Process request
        response = await call_next(request)
        
        # Update session data from request state
        session_data = request.state.session
        self._set_session(session_id, session_data)
        
        # Set session cookie
        await self._set_session_cookie(response, session_id)
        
        # Only clear flash messages and form data if not a redirect
        if not isinstance(response, RedirectResponse):
            await self._clear_flash_messages(session_data)
            await self._clear_form_data(session_data)
            self._set_session(session_id, session_data)
        
        return response
    
    async def _set_session_cookie(self, response: Response, session_id: str) -> None:
        """Set session cookie on response."""
        response.set_cookie(
            key=self.session_cookie,
            value=session_id,
            httponly=True,
            secure=self.secure,
            max_age=self.expiry_minutes * 60,  # Convert to seconds
            samesite="lax"
        )
    
    async def _get_flash_messages(self, session_data: Dict[str, Any]) -> List[FlashMessage]:
        """Get flash messages from session data."""
        flash_messages = []
        if "flash_messages" in session_data:
            for msg_data in session_data["flash_messages"]:
                if isinstance(msg_data, dict):
                    flash_messages.append(FlashMessage.from_dict(msg_data))
        return flash_messages
    
    async def _clear_flash_messages(self, session_data: Dict[str, Any]) -> None:
        """Clear flash messages from session data."""
        if "flash_messages" in session_data:
            del session_data["flash_messages"]
    
    async def _get_form_data(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get stored form data from session."""
        return session_data.get("form_data", {})
    
    async def _clear_form_data(self, session_data: Dict[str, Any]) -> None:
        """Clear form data from session."""
        session_data["form_data"] = {}

# Session management functions
async def get_session(request: Request) -> Dict[str, Any]:
    """Get the session data for the current request."""
    return getattr(request.state, "session", {})

async def set_session_data(request: Request, key: str, value: Any) -> None:
    """Set a value in the session."""
    session = await get_session(request)
    session[key] = value

async def get_session_data(request: Request, key: str, default: Any = None) -> Any:
    """Get a value from the session."""
    session = await get_session(request)
    return session.get(key, default)

async def get_flash_messages(request: Request) -> List[FlashMessage]:
    """Get flash messages for the current request."""
    return getattr(request.state, "flash_messages", [])

async def add_flash_message(request: Request, message: str, type: str = "info") -> None:
    """
    Add a flash message to the session.
    
    Args:
        request: FastAPI request
        message: Message text
        type: Message type (success, error, warning, info)
    """
    session = request.state.session
    flash_messages = session.get("flash_messages", [])
    flash_messages.append(FlashMessage(message, type).to_dict())
    session["flash_messages"] = flash_messages
    
    # Update session store directly
    session_id = request.state.session_id
    _session_store.set(session_id, session)

async def store_form_data(request: Request, form_data: Dict[str, Any]) -> None:
    """Store form data in the session."""
    session = await get_session(request)
    session["form_data"] = form_data

async def get_form_data(request: Request) -> Dict[str, Any]:
    """Get stored form data from the session."""
    return getattr(request.state, "form_data", {})

async def clear_form_data(request: Request) -> None:
    """Clear stored form data from the session."""
    session = await get_session(request)
    session["form_data"] = {}

# Add these functions to make the middleware compatible with tests
def extract_session_from_cookie(cookies: Dict[str, str]) -> Dict[str, Any]:
    """
    Extract session data from cookies (for test compatibility).
    
    Args:
        cookies: Cookies dictionary
        
    Returns:
        Session data
    """
    if "sap_session" in cookies:
        session_id = cookies["sap_session"]
        session = _session_store.get(session_id)
        if session:
            return session
    return {}

def generate_session_cookie(session_data: Dict[str, Any], response: Response) -> Response:
    """
    Generate session cookie (for test compatibility).
    
    Args:
        session_data: Session data
        response: Response to add cookie to
        
    Returns:
        Response with cookie
    """
    session_id = str(uuid.uuid4())
    _session_store.set(session_id, session_data)
    response.set_cookie(
        key="sap_session",
        value=session_id,
        httponly=True,
        secure=False,
        max_age=30 * 60,  # 30 minutes
        samesite="lax"
    )
    return response
