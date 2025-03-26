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
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

# Import common fixtures and services
try:
    from conftest import test_services
    from services.base_service import BaseService
    from services.monitor_service import MonitorService
    from services.template_service import TemplateService
    from services.p2p_service import P2PService
    from models.base_model import BaseModel
    from models.material import Material
    from models.requisition import Requisition
    from fastapi import FastAPI, HTTPException
    logger.info("Successfully imported test fixtures and services")
except ImportError as e:
    # Log import error but continue - not all tests need all imports
    logger.warning(f"Optional import failed: {e}")
    logger.debug("Stack trace:", exc_info=True)

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment for each test."""
    setup_test_env_vars(monkeypatch)
    logger.info("Test environment initialized")
    yield
    logger.info("Test environment cleaned up")
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

# tests-dest/unit/test_p2p_common.py
import pytest
from datetime import datetime, date
from unittest.mock import MagicMock, patch
from fastapi import Request
from fastapi.responses import RedirectResponse

from controllers.p2p_common import (
    # Dependencies
    get_p2p_service_dependency,
    get_monitor_service_dependency,
    get_material_service_dependency,
    
    # Error handling functions
    log_controller_error,
    handle_document_not_found,
    
    # Filter parameter models
    DocumentFilterParams,
    RequisitionFilterParams,
    OrderFilterParams,
    
    # Utility functions
    format_timestamp,
    format_date,
    get_status_badge_color,
    
    # Constants
    STATUS_BADGE_COLORS
)
from controllers import BaseController
from models.p2p import DocumentStatus

class TestP2PCommonDependencies:
    """Tests for the dependency functions in p2p_common.py"""
    
    def test_p2p_service_dependency(self):
        """Test that the P2P service dependency function returns a Depends instance"""
        dependency = get_p2p_service_dependency()
        # Check it's a Depends instance with the function inside
        assert hasattr(dependency, "dependency")
        # Get the underlying function
        dependency_func = getattr(dependency, "dependency")
        # Check it matches the expected function
        from services import get_p2p_service
        assert dependency_func == get_p2p_service
    
    def test_monitor_service_dependency(self):
        """Test that the monitor service dependency function returns a Depends instance"""
        dependency = get_monitor_service_dependency()
        # Check it's a Depends instance with the function inside
        assert hasattr(dependency, "dependency")
        # Get the underlying function
        dependency_func = getattr(dependency, "dependency")
        # Check it matches the expected function
        from services import get_monitor_service
        assert dependency_func == get_monitor_service
    
    def test_material_service_dependency(self):
        """Test that the material service dependency function returns a Depends instance"""
        dependency = get_material_service_dependency()
        # Check it's a Depends instance with the function inside
        assert hasattr(dependency, "dependency")
        # Get the underlying function
        dependency_func = getattr(dependency, "dependency")
        # Check it matches the expected function
        from services import get_material_service
        assert dependency_func == get_material_service

class TestP2PCommonErrorHandling:
    """Tests for the error handling functions in p2p_common.py"""
    
    def test_log_controller_error(self):
        """Test that controller errors are logged correctly"""
        # Set up mocks
        mock_monitor_service = MagicMock()
        mock_request = MagicMock()
        mock_request.url = "http://test.com/api/test"
        
        # Create test exception
        exception = ValueError("Test error")
        
        # Call the function
        log_controller_error(
            monitor_service=mock_monitor_service,
            e=exception,
            request=mock_request,
            component="test_component",
            document_number="REQ-123"
        )
        
        # Check the monitor service was called correctly
        mock_monitor_service.log_error.assert_called_once()
        kwargs = mock_monitor_service.log_error.call_args.kwargs
        
        # Verify arguments
        assert kwargs["error_type"] == "controller_error"
        assert "Error in test_component" in kwargs["message"]
        assert "Test error" in kwargs["message"]
        assert kwargs["component"] == "p2p_controller"
        assert kwargs["context"]["path"] == "http://test.com/api/test"
        assert kwargs["context"]["document_number"] == "REQ-123"
    
    def test_log_controller_error_without_document(self):
        """Test that controller errors are logged correctly without document number"""
        # Set up mocks
        mock_monitor_service = MagicMock()
        mock_request = MagicMock()
        mock_request.url = "http://test.com/api/test"
        
        # Create test exception
        exception = ValueError("Test error")
        
        # Call the function
        log_controller_error(
            monitor_service=mock_monitor_service,
            e=exception,
            request=mock_request,
            component="test_component"
        )
        
        # Check the monitor service was called correctly
        mock_monitor_service.log_error.assert_called_once()
        kwargs = mock_monitor_service.log_error.call_args.kwargs
        
        # Verify arguments
        assert kwargs["error_type"] == "controller_error"
        assert "Error in test_component" in kwargs["message"]
        assert "document_number" not in kwargs["context"]
    
    def test_handle_document_not_found_requisition(self):
        """Test that requisition not found errors are handled correctly"""
        # Set up mocks
        mock_request = MagicMock()
        
        # Patch BaseController.redirect_to_route
        with patch('controllers.p2p_common.BaseController.redirect_to_route') as mock_redirect:
            mock_redirect.return_value = "redirect_response"
            
            # Call the function
            result = handle_document_not_found(
                document_number="REQ-123",
                request=mock_request,
                document_type="Requisition"
            )
            
            # Check the redirect was called correctly
            mock_redirect.assert_called_once_with(
                route_name="requisition_list",
                query_params={"error_code": "Requisition REQ-123 not found"},
                status_code=303
            )
            assert result == "redirect_response"
    
    def test_handle_document_not_found_order(self):
        """Test that order not found errors are handled correctly"""
        # Set up mocks
        mock_request = MagicMock()
        
        # Patch BaseController.redirect_to_route
        with patch('controllers.p2p_common.BaseController.redirect_to_route') as mock_redirect:
            mock_redirect.return_value = "redirect_response"
            
            # Call the function
            result = handle_document_not_found(
                document_number="PO-123",
                request=mock_request,
                document_type="Order"
            )
            
            # Check the redirect was called correctly
            mock_redirect.assert_called_once_with(
                route_name="order_list",
                query_params={"error_code": "Order PO-123 not found"},
                status_code=303
            )
            assert result == "redirect_response"

class TestP2PCommonFilterParams:
    """Tests for the filter parameter models in p2p_common.py"""
    
    def test_document_filter_params(self):
        """Test DocumentFilterParams model validation"""
        # Test valid parameters
        params = DocumentFilterParams(
            search="test",
            status=DocumentStatus.APPROVED,
            date_from=date(2023, 1, 1),
            date_to=date(2023, 12, 31),
            limit=50,
            offset=10
        )
        assert params.search == "test"
        assert params.status == DocumentStatus.APPROVED
        assert params.date_from == date(2023, 1, 1)
        assert params.date_to == date(2023, 12, 31)
        assert params.limit == 50
        assert params.offset == 10
        
        # Test optional parameters
        params = DocumentFilterParams()
        assert params.search is None
        assert params.status is None
        assert params.date_from is None
        assert params.date_to is None
        assert params.limit is None
        assert params.offset is None
    
    def test_requisition_filter_params(self):
        """Test RequisitionFilterParams model validation"""
        # Test valid parameters including base and specific fields
        params = RequisitionFilterParams(
            search="test",
            status=DocumentStatus.APPROVED,
            requester="user1",
            department="IT",
            urgent=True
        )
        assert params.search == "test"
        assert params.status == DocumentStatus.APPROVED
        assert params.requester == "user1"
        assert params.department == "IT"
        assert params.urgent is True
        
        # Test optional parameters
        params = RequisitionFilterParams()
        assert params.requester is None
        assert params.department is None
        assert params.urgent is None
    
    def test_order_filter_params(self):
        """Test OrderFilterParams model validation"""
        # Test valid parameters including base and specific fields
        params = OrderFilterParams(
            search="test",
            status=DocumentStatus.APPROVED,
            vendor="Vendor Inc",
            requisition_reference="REQ-123"
        )
        assert params.search == "test"
        assert params.status == DocumentStatus.APPROVED
        assert params.vendor == "Vendor Inc"
        assert params.requisition_reference == "REQ-123"
        
        # Test optional parameters
        params = OrderFilterParams()
        assert params.vendor is None
        assert params.requisition_reference is None

class TestP2PCommonUtilities:
    """Tests for the utility functions in p2p_common.py"""
    
    def test_format_timestamp(self):
        """Test that timestamps are formatted correctly"""
        # Create test timestamp
        timestamp = datetime(2023, 5, 15, 14, 30, 45)
        
        # Check formatting
        assert format_timestamp(timestamp) == "2023-05-15 14:30:45"
    
    def test_format_date(self):
        """Test that dates are formatted correctly"""
        # Create test date
        test_date = date(2023, 5, 15)
        
        # Check formatting
        assert format_date(test_date) == "2023-05-15"
    
    def test_get_status_badge_color(self):
        """Test that status badge colors are returned correctly"""
        # Check existing status colors
        assert get_status_badge_color(DocumentStatus.DRAFT) == "secondary"
        assert get_status_badge_color(DocumentStatus.SUBMITTED) == "info"
        assert get_status_badge_color(DocumentStatus.APPROVED) == "primary"
        assert get_status_badge_color(DocumentStatus.REJECTED) == "danger"
        assert get_status_badge_color(DocumentStatus.ORDERED) == "success"
        assert get_status_badge_color(DocumentStatus.RECEIVED) == "success"
        assert get_status_badge_color(DocumentStatus.PARTIALLY_RECEIVED) == "warning"
        assert get_status_badge_color(DocumentStatus.COMPLETED) == "success"
        assert get_status_badge_color(DocumentStatus.CANCELED) == "dark"
        
        # Check fallback for unknown status
        unknown_status = MagicMock()
        assert get_status_badge_color(unknown_status) == "secondary"
    
    def test_status_badge_colors_constant(self):
        """Test the STATUS_BADGE_COLORS constant"""
        # Check that all statuses have a color
        for status in DocumentStatus:
            assert status in STATUS_BADGE_COLORS
        
        # Check specific color values
        assert STATUS_BADGE_COLORS[DocumentStatus.DRAFT] == "secondary"
        assert STATUS_BADGE_COLORS[DocumentStatus.SUBMITTED] == "info"
        assert STATUS_BADGE_COLORS[DocumentStatus.APPROVED] == "primary"
        assert STATUS_BADGE_COLORS[DocumentStatus.REJECTED] == "danger" 