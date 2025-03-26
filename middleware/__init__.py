# middleware/__init__.py
"""
Middleware package for the SAP Test Harness.

This package contains middleware components that are integrated into the FastAPI
application pipeline to provide cross-cutting functionality like session management,
flash messages, and request/response interception.
"""

from typing import Dict, Any, List, Optional, Callable
import logging

# Configure logging
logger = logging.getLogger("middleware")

# Export session middleware
from .session import SessionMiddleware, FlashMessage, get_flash_messages, get_session

__all__ = [
    'SessionMiddleware', 
    'FlashMessage',
    'get_flash_messages',
    'get_session'
]
