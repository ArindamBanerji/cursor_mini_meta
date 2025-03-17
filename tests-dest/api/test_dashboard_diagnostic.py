"""
Diagnostic tests for the dashboard controller.

This file tests our dependency unwrapping approach with a controller
that has a simpler dependency structure (no explicit Depends objects).
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
import asyncio
import inspect
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request
from fastapi.responses import RedirectResponse

from controllers.dashboard_controller import show_dashboard, redirect_to_dashboard
from api.test_helpers import unwrap_dependencies, create_controller_test
from services.state_manager import state_manager

# Fixtures
@pytest.fixture
def mock_request():
    """Create a mock request object for testing."""
    request = AsyncMock(spec=Request)
    request.url = MagicMock()
    request.url.path = "/dashboard"
    return request

@pytest.fixture
def mock_state_manager():
    """Create a mock state manager for testing."""
    manager = MagicMock()
    manager.get.side_effect = lambda key, default=None: {
        "dashboard_visits": 5,
        "last_dashboard_visit": "2023-03-16 12:00:00"
    }.get(key, default)
    return manager

# Diagnostic tests
@pytest.mark.asyncio
async 
def setup_module(module):
    """Set up the test module by ensuring PYTEST_CURRENT_TEST is set"""
    logger.info("Setting up test module")
    os.environ["PYTEST_CURRENT_TEST"] = "True"
    
def teardown_module(module):
    """Clean up after the test module"""
    logger.info("Tearing down test module")
    if "PYTEST_CURRENT_TEST" in os.environ:
        del os.environ["PYTEST_CURRENT_TEST"]
def test_dashboard_direct(mock_request):
    """Test calling the dashboard controller directly."""
    print("\n--- Testing dashboard controller directly ---")
    
    # Save original state manager
    original_state_manager = state_manager.get
    
    try:
        # Mock the state manager
        state_manager.get = MagicMock(side_effect=lambda key, default=None: {
            "dashboard_visits": 5,
            "last_dashboard_visit": "2023-03-16 12:00:00"
        }.get(key, default))
        state_manager.set = MagicMock()
        
        # Call the function
        result = await show_dashboard(mock_request)
        
        # Verify result
        assert "welcome_message" in result
        assert "visit_count" in result
        assert result["visit_count"] == 6  # Incremented from 5
        assert "last_visit" in result
        assert result["last_visit"] == "2023-03-16 12:00:00"
        
        # Verify state manager was called
        state_manager.get.assert_any_call("dashboard_visits", 0)
        state_manager.set.assert_any_call("dashboard_visits", 6)
        
        print(f"Result: {result}")
    finally:
        # Restore original state manager
        state_manager.get = original_state_manager

@pytest.mark.asyncio
async def test_dashboard_with_unwrap(mock_request):
    """Test the dashboard controller with unwrap_dependencies."""
    print("\n--- Testing dashboard controller with unwrap_dependencies ---")
    
    # Create wrapped controller with no mocks (since there are no Depends)
    wrapped = unwrap_dependencies(show_dashboard)
    
    # Save original state manager
    original_state_manager = state_manager.get
    
    try:
        # Mock the state manager
        state_manager.get = MagicMock(side_effect=lambda key, default=None: {
            "dashboard_visits": 10,
            "last_dashboard_visit": "2023-03-16 14:00:00"
        }.get(key, default))
        state_manager.set = MagicMock()
        
        # Call the function
        result = await wrapped(mock_request)
        
        # Verify result
        assert "welcome_message" in result
        assert "visit_count" in result
        assert result["visit_count"] == 11  # Incremented from 10
        assert "last_visit" in result
        assert result["last_visit"] == "2023-03-16 14:00:00"
        
        # Verify state manager was called
        state_manager.get.assert_any_call("dashboard_visits", 0)
        state_manager.set.assert_any_call("dashboard_visits", 11)
        
        print(f"Result: {result}")
    finally:
        # Restore original state manager
        state_manager.get = original_state_manager

@pytest.mark.asyncio
async def test_redirect_function(mock_request):
    """Test the redirect_to_dashboard function."""
    print("\n--- Testing redirect_to_dashboard function ---")
    
    with patch('controllers.BaseController.redirect_to_route') as mock_redirect:
        # Setup mock
        mock_redirect.return_value = RedirectResponse(url="/dashboard", status_code=302)
        
        # Call the function
        result = await redirect_to_dashboard(mock_request)
        
        # Verify result
        assert isinstance(result, RedirectResponse)
        assert result.status_code == 302
        
        # Verify redirect was called with the correct route
        # The status_code parameter is added in the controller function
        mock_redirect.assert_called_once_with("dashboard")
        
        print(f"Result type: {type(result)}")
        print(f"Status code: {result.status_code}")

# Diagnostic function to inspect controller parameters
def inspect_controller_parameters():
    """Inspect the parameters of the controller functions."""
    print("\n--- Inspecting dashboard controller parameters ---")
    
    # Get the signature of the controller functions
    sig_show = inspect.signature(show_dashboard)
    sig_redirect = inspect.signature(redirect_to_dashboard)
    
    # Print information about each parameter for show_dashboard
    print("show_dashboard parameters:")
    for name, param in sig_show.parameters.items():
        print(f"Parameter: {name}")
        print(f"  Default: {param.default}")
        print(f"  Annotation: {param.annotation}")
        
        # Check if it's a Depends parameter
        if param.default is not inspect.Parameter.empty and hasattr(param.default, "dependency"):
            print(f"  Is Depends: True")
            print(f"  Dependency: {param.default.dependency}")
        else:
            print(f"  Is Depends: False")
        
        print()
    
    # Print information about each parameter for redirect_to_dashboard
    print("redirect_to_dashboard parameters:")
    for name, param in sig_redirect.parameters.items():
        print(f"Parameter: {name}")
        print(f"  Default: {param.default}")
        print(f"  Annotation: {param.annotation}")
        
        # Check if it's a Depends parameter
        if param.default is not inspect.Parameter.empty and hasattr(param.default, "dependency"):
            print(f"  Is Depends: True")
            print(f"  Dependency: {param.default.dependency}")
        else:
            print(f"  Is Depends: False")
        
        print()

# Run the diagnostic function
inspect_controller_parameters()

if __name__ == "__main__":
    # Run the tests directly if this file is executed
    asyncio.run(test_dashboard_direct(AsyncMock()))
    asyncio.run(test_dashboard_with_unwrap(AsyncMock()))
    asyncio.run(test_redirect_function(AsyncMock())) 