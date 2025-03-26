"""
Simplified diagnostic test for P2P requisition workflow functions.

This test demonstrates how to properly import and use the requisition
workflow functions through service_imports rather than directly from controllers.
"""

import os
import sys
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
from unittest.mock import MagicMock, patch
from fastapi import Request
from fastapi.responses import RedirectResponse

# Import proper classes and functions from service_imports
from tests_dest.test_helpers.service_imports import (
    # Service classes
    P2PService,
    MonitorService,
    
    # Models and enums
    DocumentStatus,
    
    # Exceptions
    NotFoundError,
    BadRequestError,
    
    # The workflow functions we need to test
    submit_requisition,
    approve_requisition,
    reject_requisition
)

@pytest.mark.asyncio
async def test_submit_requisition_with_proper_imports():
    """Test using submit_requisition function imported from service_imports."""
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
    
    # Call the function with proper mocking
    with patch("fastapi.responses.RedirectResponse") as mock_redirect:
        mock_redirect.return_value = MagicMock(spec=RedirectResponse)
        result = await submit_requisition(
            request=mock_request,
            document_number="REQ-123",
            p2p_service=mock_p2p_service,
            monitor_service=mock_monitor_service
        )
        
    # Verify service was called correctly
    mock_p2p_service.submit_requisition.assert_called_once_with("REQ-123")
    print("✅ submit_requisition successfully called with service_imports")
    
@pytest.mark.asyncio
async def test_approve_requisition_with_proper_imports():
    """Test using approve_requisition function imported from service_imports."""
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
    
    # Call the function with proper mocking
    with patch("fastapi.responses.RedirectResponse") as mock_redirect:
        mock_redirect.return_value = MagicMock(spec=RedirectResponse)
        result = await approve_requisition(
            request=mock_request,
            document_number="REQ-123",
            p2p_service=mock_p2p_service,
            monitor_service=mock_monitor_service
        )
        
    # Verify service was called correctly
    mock_p2p_service.approve_requisition.assert_called_once_with("REQ-123")
    print("✅ approve_requisition successfully called with service_imports")

@pytest.mark.asyncio
async def test_reject_requisition_with_proper_imports():
    """Test using reject_requisition function imported from service_imports."""
    # Create mocks
    mock_request = MagicMock(spec=Request)
    mock_request.is_test = True
    
    # Mock the form data
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
    
    # Call the function with proper mocking
    with patch("fastapi.responses.RedirectResponse") as mock_redirect:
        mock_redirect.return_value = MagicMock(spec=RedirectResponse)
        result = await reject_requisition(
            request=mock_request,
            document_number="REQ-123",
            p2p_service=mock_p2p_service,
            monitor_service=mock_monitor_service
        )
        
    # Verify service was called correctly
    mock_p2p_service.reject_requisition.assert_called_once()
    print("✅ reject_requisition successfully called with service_imports")

def print_test_summary():
    """Print a summary of the tests."""
    print("\n==================================================================")
    print("                      TEST SUMMARY                                ")
    print("==================================================================")
    print("All workflow functions can be properly imported from service_imports:")
    print("  - submit_requisition")
    print("  - approve_requisition") 
    print("  - reject_requisition")
    print("\nTo fix the original test failure:")
    print("1. Update the tests to import these functions from service_imports")
    print("2. No changes needed to the actual controller code")
    print("==================================================================")

if __name__ == "__main__":
    print("\n==================================================================")
    print("      SIMPLIFIED P2P WORKFLOW FUNCTION TESTS                      ")
    print("==================================================================")
    
    # Run the tests
    import asyncio
    asyncio.run(test_submit_requisition_with_proper_imports())
    asyncio.run(test_approve_requisition_with_proper_imports())
    asyncio.run(test_reject_requisition_with_proper_imports())
    
    # Print test summary
    print_test_summary() 