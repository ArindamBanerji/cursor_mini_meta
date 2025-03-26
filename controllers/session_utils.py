"""
Session utility functions for controllers.

This module provides helper functions for working with session data in controllers,
including flash messages and form data handling.
"""

from typing import Dict, Any, Optional
from fastapi import Request, Response, Form
from fastapi.responses import RedirectResponse

from middleware.session import (
    add_flash_message, 
    store_form_data, 
    get_flash_messages,
    get_form_data
)

async def handle_form_error(
    request: Request, 
    form_data: Dict[str, Any], 
    error_message: str = "An error occurred while processing your request."
) -> None:
    """
    Store form data in session and add error flash message.
    
    Args:
        request: FastAPI request
        form_data: Form data to preserve
        error_message: Error message to display
    """
    # Store form data for re-rendering
    store_form_data(request, form_data)
    
    # Add error flash message
    add_flash_message(request, error_message, "error")

async def handle_form_validation_error(
    request: Request, 
    form_data: Dict[str, Any], 
    error_dict: Dict[str, Any]
) -> None:
    """
    Store form data and validation errors in session.
    
    Args:
        request: FastAPI request
        form_data: Form data to preserve
        error_dict: Dictionary of field-specific errors
    """
    # Store form data for re-rendering
    form_data["_errors"] = error_dict
    store_form_data(request, form_data)
    
    # Add error flash message
    add_flash_message(request, "Please correct the errors in the form.", "error")

async def add_success_message(
    request: Request, 
    message: str
) -> None:
    """
    Add a success flash message.
    
    Args:
        request: FastAPI request
        message: Success message to display
    """
    add_flash_message(request, message, "success")

async def redirect_with_success(
    url: str, 
    request: Request, 
    message: str
) -> RedirectResponse:
    """
    Redirect with a success message.
    
    Args:
        url: Redirect URL
        request: FastAPI request
        message: Success message
        
    Returns:
        Redirect response
    """
    add_flash_message(request, message, "success")
    return RedirectResponse(url, status_code=303)

async def redirect_with_error(
    url: str, 
    request: Request, 
    message: str
) -> RedirectResponse:
    """
    Redirect with an error message.
    
    Args:
        url: Redirect URL
        request: FastAPI request
        message: Error message
        
    Returns:
        Redirect response
    """
    add_flash_message(request, message, "error")
    return RedirectResponse(url, status_code=303)

def get_template_context_with_session(
    request: Request, 
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Add session data to template context.
    
    Args:
        request: FastAPI request
        context: Template context
        
    Returns:
        Template context with session data
    """
    # Add flash messages to context
    flash_messages = get_flash_messages(request)
    context["flash_messages"] = flash_messages
    
    # Add form data to context if available
    form_data = get_form_data(request)
    if form_data:
        context["form_data"] = form_data
        # Extract field-specific errors if present
        if "_errors" in form_data:
            context["errors"] = form_data["_errors"]
    
    return context 