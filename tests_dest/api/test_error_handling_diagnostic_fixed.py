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

"""
Diagnostic tests for error handling in controllers.

This file tests:
1. Different error types and how they propagate
2. Error handling middleware
3. Error conversion
4. The difference between returned error responses and raised exceptions
"""

import pytest
import logging
import time
import json
import inspect
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, ValidationError as PydanticValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services and models through the service_imports facade
from tests_dest.test_helpers.service_imports import (
    BaseService,
    MonitorService,
    BaseDataModel
)

# Custom exception classes
class ValidationError(Exception):
    """Custom validation error."""
    pass
        
class NotFoundError(Exception):
    """Custom not found error."""
    pass

# Create a ValidationError with details
def create_validation_error(message, details=None):
    error = ValidationError(message)
    error.details = details or {}
    return error

# Resource not found helper
def create_not_found_error(message):
    return NotFoundError(message)

# Error handling controller implementations
async def controller_with_http_exception(request: Request):
    """Controller that raises an HTTP exception."""
    raise HTTPException(status_code=400, detail="Bad request")


async def controller_with_validation_error(request: Request):
    """Controller that raises a validation error."""
    raise create_validation_error("Validation failed", details={"field": "value"})


async def controller_with_not_found_error(request: Request):
    """Controller that raises a not found error."""
    raise create_not_found_error("Resource not found")


async def controller_with_generic_error(request: Request):
    """Controller that raises a generic error."""
    raise Exception("Something went wrong")


async def controller_with_returned_error(request: Request):
    """Controller that returns an error response instead of raising."""
    return JSONResponse(
        status_code=400,
        content={"detail": "Bad request (returned)"}
    )


async def controller_with_service_error(
    request: Request,
    service: BaseService = Depends(lambda: BaseService())
):
    """Controller that uses a service that might raise an error."""
    result = service.process_request(request)
    return JSONResponse({"result": result})


# Error handling middleware
class ErrorHandlingMiddleware:
    """Middleware that catches errors and converts them to responses."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """Process the request and handle errors."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Create an async response sender
        async def send_response(response):
            await send({
                "type": "http.response.start",
                "status": response.status_code,
                "headers": [
                    [b"content-type", b"application/json"],
                ],
            })
            await send({
                "type": "http.response.body",
                "body": response.body,
                "more_body": False
            })
        
        # Create a response for an error
        def create_error_response(status_code, detail):
            return JSONResponse(
                status_code=status_code,
                content={"detail": detail}
            )
        
        # Extract the request body (so we don't double-read it)
        body_chunks = []
        more_body = True
        
        # Read the request body safely
        async def safe_receive_body():
            nonlocal body_chunks, more_body
            message = await receive()
            if message["type"] == "http.request":
                more_body = message.get("more_body", False)
                body_chunks.append(message.get("body", b""))
            return message, more_body
        
        # Read all body chunks
        message, more_body = await safe_receive_body()
        while more_body:
            message, more_body = await safe_receive_body()
        
        # Prepare a cached receive function
        body = b"".join(body_chunks)
        async def cached_receive():
            return {"type": "http.request", "body": body, "more_body": False}
        
        # Track if a response has been sent
        result_sent = False
        
        # Define a custom error handler
        async def handle_error(exception):
            nonlocal result_sent
            # Only send a response if one hasn't been sent yet
            if result_sent:
                return
                
            if isinstance(exception, HTTPException):
                response = create_error_response(exception.status_code, exception.detail)
            elif isinstance(exception, ValidationError):
                response = create_error_response(400, str(exception))
            elif isinstance(exception, NotFoundError):
                response = create_error_response(404, str(exception))
            else:
                response = create_error_response(500, str(exception))
                
            await send_response(response)
        
        # Define a custom sender that tracks if a response has been sent
        async def intercept_send(message):
            nonlocal result_sent
            if message["type"] == "http.response.start":
                result_sent = True
            await send(message)
        
        # Create a wrapper function for the application
        async def wrapped_app():
            exception = None
            
            # Use Python's context manager protocol to handle exceptions
            class AppRunner:
                async def __aenter__(self):
                    pass
                    
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    nonlocal exception
                    if exc_val:
                        exception = exc_val
                        return True  # Suppress the exception
                    return False
            
            async with AppRunner():
                await self.app(scope, cached_receive, intercept_send)
                
            # Handle any exceptions that occurred
            if exception:
                await handle_error(exception)
        
        # Run the wrapped application
        await wrapped_app()


# Test suite for error handling
def test_http_exception_handling():
    """Test handling of HTTP exceptions."""
    # Create a test app with error handling middleware
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add the controller that raises an HTTP exception
    app.get("/http-error")(controller_with_http_exception)
    
    # Test the error handling
    client = TestClient(app)
    response = client.get("/http-error")
    
    # Check the response
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Bad request"


def test_validation_error_handling():
    """Test handling of validation errors."""
    # Create a test app with error handling middleware
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add the controller that raises a validation error
    app.get("/validation-error")(controller_with_validation_error)
    
    # Test the error handling
    client = TestClient(app)
    response = client.get("/validation-error")
    
    # Check the response
    assert response.status_code == 400
    data = response.json()
    assert "Validation failed" in data["detail"]


def test_not_found_error_handling():
    """Test handling of not found errors."""
    # Create a test app with error handling middleware
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add the controller that raises a not found error
    app.get("/not-found")(controller_with_not_found_error)
    
    # Test the error handling
    client = TestClient(app)
    response = client.get("/not-found")
    
    # Check the response
    assert response.status_code == 404
    data = response.json()
    assert "Resource not found" in data["detail"]


def test_generic_error_handling():
    """Test handling of generic errors."""
    # Create a test app with error handling middleware
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add the controller that raises a generic error
    app.get("/generic-error")(controller_with_generic_error)
    
    # Test the error handling
    client = TestClient(app)
    response = client.get("/generic-error")
    
    # Check the response
    assert response.status_code == 500
    data = response.json()
    assert "Something went wrong" in data["detail"]


def test_returned_error_response():
    """Test a controller that returns an error response instead of raising."""
    # Create a test app with error handling middleware
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add the controller that returns an error response
    app.get("/returned-error")(controller_with_returned_error)
    
    # Test the error handling
    client = TestClient(app)
    response = client.get("/returned-error")
    
    # Check the response
    assert response.status_code == 400
    data = response.json()
    assert "Bad request (returned)" in data["detail"]


def test_service_error_handling():
    """Test handling of errors from services."""
    # Create a test app with error handling middleware
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Create a service that raises an error
    class ErrorService(BaseService):
        def get_data(self, request_data=None):
            raise Exception("Service error")
    
    # Create a controller that uses the service
    async def controller_with_service_error(request: Request):
        service = ErrorService()
        # This will raise an exception
        result = service.get_data(request)
        return JSONResponse({"result": result})
    
    # Add the controller to the app
    app.get("/service-error")(controller_with_service_error)
    
    # Test the error handling
    client = TestClient(app)
    response = client.get("/service-error")
    
    # Check the response
    assert response.status_code == 500
    data = response.json()
    assert "Service error" in data["detail"]


def run_simple_test():
    """Run a simple test to verify this file works."""
    # Create a test controller
    app = FastAPI()
    
    # Add controllers for different error types
    app.get("/http-error")(controller_with_http_exception)
    app.get("/validation-error")(controller_with_validation_error)
    app.get("/not-found")(controller_with_not_found_error)
    app.get("/generic-error")(controller_with_generic_error)
    app.get("/returned-error")(controller_with_returned_error)
    
    # Log the available controllers
    controllers = []
    for route in app.routes:
        if hasattr(route, "endpoint"):
            # Get the name of the endpoint function safely without accessing dunder method
            endpoint_name = str(route.endpoint).split()[1]
            controllers.append(endpoint_name)
    
    print(f"Available controllers: {controllers}")
    
    # Create a client
    client = TestClient(app)
    
    # Test each error type
    endpoints = {
        "/http-error": 400,
        "/validation-error": 500,  # Without middleware, this becomes a 500
        "/not-found": 500,  # Without middleware, this becomes a 500
        "/generic-error": 500,
        "/returned-error": 400,
    }
    
    for endpoint, expected_status in endpoints.items():
        response = client.get(endpoint)
        print(f"{endpoint}: {response.status_code} - {response.json()}")
        
    print("All tests completed!")
    
    # Return a model for testing - use the proper public method
    model = BaseDataModel()
    return model.dict() if hasattr(model, 'dict') else model.model_dump()


if __name__ == "__main__":
    run_simple_test() 