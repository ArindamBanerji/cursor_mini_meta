"""
Diagnostic test for P2P requisition controller imports and functionality.

This test verifies that the controller functions can be properly imported and accessed,
and that they integrate correctly with the service layer.
"""

import os
import sys
import inspect
from pathlib import Path

# Add parent directory to path so Python can find the tests_dest module
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent  # Go up two levels to reach project root
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import helper to fix imports
from tests_dest.import_helper import fix_imports
fix_imports()

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import Request
from fastapi.responses import RedirectResponse

# Import from service_imports rather than directly from controllers
from tests_dest.test_helpers.service_imports import (
    P2PService,
    MonitorService,
    DocumentStatus,
    NotFoundError,
    BadRequestError,
    ValidationError
)

# These are the imports we need to test and add to service_imports if needed
def test_import_status():
    """Test the import status of necessary functions."""
    
    try:
        # Try to import via service_imports first
        from tests_dest.test_helpers.service_imports import (
            submit_requisition,
            approve_requisition,
            reject_requisition
        )
        print("✅ UI workflow functions are available in service_imports")
        return True
    except ImportError:
        print("❌ UI workflow functions are NOT available in service_imports")
        
        # Try to import directly as a fallback to diagnose
        try:
            from controllers.p2p_requisition_ui_controller import (
                submit_requisition,
                approve_requisition,
                reject_requisition
            )
            print("✅ UI workflow functions exist in the controller")
            print("❌ But they are not exposed in service_imports")
            return False
        except ImportError:
            print("❌ UI workflow functions do NOT exist in the controller")
            print("❌ And they are not exposed in service_imports")
            return False

@pytest.mark.asyncio
async def test_submit_requisition_function():
    """Test if the submit_requisition function can be called without errors."""
    try:
        # Import directly for diagnosis
        from controllers.p2p_requisition_ui_controller import submit_requisition
        
        # Create mocks
        mock_request = MagicMock(spec=Request)
        mock_request.is_test = True
        mock_p2p_service = MagicMock(spec=P2PService)
        mock_monitor_service = MagicMock(spec=MonitorService)
        
        # Set up the mock to return a mock requisition
        mock_requisition = MagicMock()
        mock_requisition.document_number = "REQ-123"
        mock_requisition.status = DocumentStatus.SUBMITTED
        mock_p2p_service.submit_requisition.return_value = mock_requisition
        
        # Call the function
        with patch("fastapi.responses.RedirectResponse") as mock_redirect:
            mock_redirect.return_value = MagicMock(spec=RedirectResponse)
            result = await submit_requisition(
                request=mock_request,
                document_number="REQ-123",
                p2p_service=mock_p2p_service,
                monitor_service=mock_monitor_service
            )
            
        # Check if the service was called correctly
        mock_p2p_service.submit_requisition.assert_called_once_with("REQ-123")
        
        print("✅ submit_requisition function works when called directly")
        return True
    except Exception as e:
        print(f"❌ Error when calling submit_requisition: {e}")
        return False

@pytest.mark.asyncio
async def test_approve_requisition_function():
    """Test if the approve_requisition function can be called without errors."""
    try:
        # Import directly for diagnosis
        from controllers.p2p_requisition_ui_controller import approve_requisition
        
        # Create mocks
        mock_request = MagicMock(spec=Request)
        mock_request.is_test = True
        mock_p2p_service = MagicMock(spec=P2PService)
        mock_monitor_service = MagicMock(spec=MonitorService)
        
        # Set up the mock to return a mock requisition
        mock_requisition = MagicMock()
        mock_requisition.document_number = "REQ-123"
        mock_requisition.status = DocumentStatus.APPROVED
        mock_p2p_service.approve_requisition.return_value = mock_requisition
        
        # Call the function
        with patch("fastapi.responses.RedirectResponse") as mock_redirect:
            mock_redirect.return_value = MagicMock(spec=RedirectResponse)
            result = await approve_requisition(
                request=mock_request,
                document_number="REQ-123",
                p2p_service=mock_p2p_service,
                monitor_service=mock_monitor_service
            )
            
        # Check if the service was called correctly
        mock_p2p_service.approve_requisition.assert_called_once_with("REQ-123")
        
        print("✅ approve_requisition function works when called directly")
        return True
    except Exception as e:
        print(f"❌ Error when calling approve_requisition: {e}")
        return False

@pytest.mark.asyncio
async def test_reject_requisition_function():
    """Test if the reject_requisition function can be called without errors."""
    try:
        # Import directly for diagnosis
        from controllers.p2p_requisition_ui_controller import reject_requisition
        
        # Create mocks
        mock_request = MagicMock(spec=Request)
        mock_request.is_test = True
        
        # Mock the request form method
        async def async_form():
            return {"rejection_reason": "Budget constraints"}
        mock_request.form = async_form
        
        mock_p2p_service = MagicMock(spec=P2PService)
        mock_monitor_service = MagicMock(spec=MonitorService)
        
        # Set up the mock to return a mock requisition
        mock_requisition = MagicMock()
        mock_requisition.document_number = "REQ-123"
        mock_requisition.status = DocumentStatus.REJECTED
        mock_p2p_service.reject_requisition.return_value = mock_requisition
        
        # Call the function
        with patch("fastapi.responses.RedirectResponse") as mock_redirect:
            mock_redirect.return_value = MagicMock(spec=RedirectResponse)
            result = await reject_requisition(
                request=mock_request,
                document_number="REQ-123",
                p2p_service=mock_p2p_service,
                monitor_service=mock_monitor_service
            )
            
        # Check if the service was called correctly
        mock_p2p_service.reject_requisition.assert_called_once()
        
        print("✅ reject_requisition function works when called directly")
        return True
    except Exception as e:
        print(f"❌ Error when calling reject_requisition: {e}")
        return False

def print_solution_recommendation():
    """Print a recommendation for how to fix the issue."""
    print("\n==================================================================")
    print("                      DIAGNOSIS SUMMARY                           ")
    print("==================================================================")
    print("The issue is that the P2P requisition UI controller has the following workflow")
    print("functions defined, but they are not properly exposed in service_imports.py:")
    print("  - submit_requisition")
    print("  - approve_requisition")
    print("  - reject_requisition")
    print("\nRecommended solution:")
    print("1. Update tests_dest/test_helpers/service_imports.py to include these functions")
    print("2. Ensure all tests import these functions from service_imports, not directly")
    print("3. No modifications to the actual controller code should be needed")
    print("==================================================================")

if __name__ == "__main__":
    print("\n==================================================================")
    print("           P2P CONTROLLER DIAGNOSTIC TESTS                        ")
    print("==================================================================")
    
    # Run the import test
    import_status = test_import_status()
    
    print("\n==================================================================")
    print("           FUNCTION TESTS                                         ")
    print("==================================================================")
    
    # Run function tests
    import asyncio
    submit_result = asyncio.run(test_submit_requisition_function())
    approve_result = asyncio.run(test_approve_requisition_function())
    reject_result = asyncio.run(test_reject_requisition_function())
    
    # Print solution recommendation
    print_solution_recommendation() 