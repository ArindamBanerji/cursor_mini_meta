"""Request and response helpers for API testing.

This module provides utility functions for creating request objects,
parsing responses, and other common API testing operations without fallbacks.
"""

from fastapi import Request, Response, FastAPI
from fastapi.responses import JSONResponse as FastAPIJSONResponse
from starlette.testclient import TestClient
from typing import Dict, List, Any, Optional, Union, Callable
import json
import asyncio
from pydantic import BaseModel
from dataclasses import dataclass

# Define a robust JSONResponse class that works with our tests
@dataclass
class JSONResponse:
    """A class representing a JSON HTTP response."""
    status_code: int = 200
    content: Any = None
    headers: Dict[str, str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.headers is None:
            self.headers = {"Content-Type": "application/json"}
        
        # Make sure content is properly handled
        if isinstance(self.content, (dict, list)):
            self._body_dict = self.content  # Store the original dict/list
            self._content = json.dumps(self.content).encode("utf-8")
        elif isinstance(self.content, str):
            self._content = self.content.encode("utf-8")
            self._body_dict = json.loads(self.content)
        elif isinstance(self.content, bytes):
            self._content = self.content
            self._body_dict = json.loads(self.content.decode("utf-8"))
        else:
            self._content = b""
            self._body_dict = {}
    
    @property
    def body(self) -> bytes:
        """Get the raw body content as bytes."""
        return self._content
    
    @property
    def text(self) -> str:
        """Get the body content as string."""
        if isinstance(self._content, bytes):
            return self._content.decode("utf-8")
        return str(self._content)
    
    @property
    def body_dict(self) -> Dict:
        """Get the body content as a dictionary."""
        return self._body_dict
    
    def json(self) -> Dict:
        """Get the JSON content as a dictionary."""
        return self._body_dict
    
    def raise_for_status(self):
        """Raise an exception if the status code is 4xx or 5xx."""
        if 400 <= self.status_code < 600:
            raise Exception(f"HTTP Error {self.status_code}: {self.text}")

@dataclass
class Request:
    """A class representing an HTTP request."""
    method: str = "GET"
    url: str = "/"
    headers: Dict[str, str] = None
    params: Dict[str, Any] = None
    json_data: Dict[str, Any] = None
    form_data: Dict[str, Any] = None
    files: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.headers is None:
            self.headers = {}
        if self.params is None:
            self.params = {}
        if self.json_data is None:
            self.json_data = {}
        if self.form_data is None:
            self.form_data = {}
        if self.files is None:
            self.files = {}

def create_test_request(
    method: str = "GET",
    url: str = "/",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    form_data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
) -> Request:
    """Create a test request for use in tests."""
    return Request(
        method=method,
        url=url,
        headers=headers or {},
        params=params or {},
        json_data=json_data or {},
        form_data=form_data or {},
        files=files or {},
    )

def create_test_response(
    status_code: int = 200,
    content: Any = None,
    headers: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    """Create a test response for use in tests."""
    if headers is None:
        headers = {"Content-Type": "application/json"}
    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=headers,
    )

def get_json_data(response: Any) -> Dict[str, Any]:
    """Extract JSON data from a response object.
    
    Args:
        response: The response object
        
    Returns:
        The parsed JSON data as a dictionary
    """
    if isinstance(response, JSONResponse):
        return response.body_dict
    if hasattr(response, "json"):
        return response.json()
    if hasattr(response, "body"):
        if isinstance(response.body, bytes):
            return json.loads(response.body.decode("utf-8"))
        elif isinstance(response.body, str):
            return json.loads(response.body)
        elif isinstance(response.body, dict):
            return response.body
    if hasattr(response, "content"):
        if isinstance(response.content, bytes):
            return json.loads(response.content.decode("utf-8"))
        elif isinstance(response.content, str):
            return json.loads(response.content)
        elif isinstance(response.content, dict):
            return response.content
    return {}

def parse_response_body(response: JSONResponse) -> Dict:
    """Parse the response body as JSON."""
    content = response.content
    if isinstance(content, bytes):
        content = content.decode("utf-8")
    if isinstance(content, str):
        return json.loads(content)
    return content

def assert_response_success(response: JSONResponse) -> None:
    """Assert that the response is a success (2xx status code)."""
    assert 200 <= response.status_code < 300, f"Expected success status code, got {response.status_code}"

def assert_response_error(response: JSONResponse, expected_status: int = None) -> None:
    """Assert that the response is an error."""
    assert response.status_code >= 400, f"Expected error status code, got {response.status_code}"
    if expected_status:
        assert response.status_code == expected_status, f"Expected status code {expected_status}, got {response.status_code}"

def assert_json_contains(response: JSONResponse, expected_data: Dict) -> None:
    """Assert that the response JSON contains the expected data."""
    body = parse_response_body(response)
    for key, value in expected_data.items():
        assert key in body, f"Expected key '{key}' not found in response"
        assert body[key] == value, f"Expected value for '{key}' to be {value}, got {body[key]}"

def assert_json_contains_keys(response: JSONResponse, expected_keys: List[str]) -> None:
    """Assert that the response JSON contains the expected keys."""
    body = parse_response_body(response)
    for key in expected_keys:
        assert key in body, f"Expected key '{key}' not found in response"

def assert_json_list_length(response: JSONResponse, expected_length: int) -> None:
    """Assert that the response JSON is a list of the expected length."""
    body = parse_response_body(response)
    assert isinstance(body, list), "Expected response body to be a list"
    assert len(body) == expected_length, f"Expected list length to be {expected_length}, got {len(body)}"

def extract_json_value(response: JSONResponse, key: str) -> Any:
    """Extract a value from the response JSON."""
    body = parse_response_body(response)
    assert key in body, f"Key '{key}' not found in response"
    return body[key]

def create_test_client(app: FastAPI) -> TestClient:
    """Create a test client for the given FastAPI app.
    
    Args:
        app: The FastAPI application
        
    Returns:
        A TestClient instance for the app
    """
    return TestClient(app)

async def call_async_endpoint(endpoint_func: Callable, request: Request, *args, **kwargs) -> JSONResponse:
    """Call an async endpoint function with a request object.
    
    Args:
        endpoint_func: The async endpoint function to call
        request: The request object to pass to the endpoint
        *args: Additional arguments to pass to the endpoint
        **kwargs: Additional keyword arguments to pass to the endpoint
        
    Returns:
        The response from the endpoint
    """
    response = await endpoint_func(request, *args, **kwargs)
    return response

def run_async(coro):
    """Run an async coroutine and return the result.
    
    Args:
        coro: The coroutine to run
        
    Returns:
        The result of the coroutine
    """
    # Get or create an event loop
    loop = asyncio.get_event_loop()
    # Run the coroutine
    return loop.run_until_complete(coro)

def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    """Convert a Pydantic model to a dictionary.
    
    Args:
        model: The Pydantic model to convert
        
    Returns:
        Dictionary representation of the model
    """
    if hasattr(model, "dict"):
        return model.dict()
    elif hasattr(model, "model_dump"):
        return model.model_dump()
    else:
        return dict(model) 