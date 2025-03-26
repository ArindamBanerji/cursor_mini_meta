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

# tests-dest/unit/test_p2p_order_common.py
import pytest
from datetime import datetime, date
from unittest.mock import MagicMock, patch
from fastapi import Request
from fastapi.responses import RedirectResponse
from typing import Dict, List

from controllers.p2p_order_common import (
    # Formatting functions
    format_order_for_response,
    format_order_item,
    format_orders_list,
    
    # Error handling
    handle_order_not_found,
    log_order_error
)
from controllers import BaseController
from models.p2p import Order, OrderItem, DocumentStatus, ProcurementType

class TestOrderFormatting:
    """Tests for the order formatting functions"""
    
    def setup_method(self):
        """Set up test data for each test"""
        # Create a mock order item
        self.mock_item = MagicMock(spec=OrderItem)
        self.mock_item.item_number = 1
        self.mock_item.material_number = "MAT-001"
        self.mock_item.description = "Test Material"
        self.mock_item.quantity = 10
        self.mock_item.unit = "EA"
        self.mock_item.price = 25.0
        self.mock_item.currency = "USD"
        self.mock_item.delivery_date = date(2023, 6, 1)
        self.mock_item.status = DocumentStatus.APPROVED
        self.mock_item.received_quantity = 5
        self.mock_item.requisition_reference = "REQ-001"
        self.mock_item.requisition_item = 1
        
        # Create a mock order
        self.mock_order = MagicMock(spec=Order)
        self.mock_order.document_number = "PO-001"
        self.mock_order.description = "Test Order"
        self.mock_order.requester = "Test User"
        self.mock_order.vendor = "Test Vendor"
        self.mock_order.payment_terms = "Net 30"
        self.mock_order.type = ProcurementType.STANDARD
        self.mock_order.status = DocumentStatus.APPROVED
        self.mock_order.notes = "Test notes"
        self.mock_order.urgent = True
        self.mock_order.items = [self.mock_item]
        self.mock_order.total_value = 250.0
        self.mock_order.requisition_reference = "REQ-001"
        self.mock_order.created_at = datetime(2023, 5, 1, 12, 0, 0)
        self.mock_order.updated_at = datetime(2023, 5, 2, 14, 30, 0)
    
    def test_format_order_item(self):
        """Test that order items are formatted correctly"""
        # Format the item
        result = format_order_item(self.mock_item)
        
        # Verify the result
        assert result["item_number"] == 1
        assert result["material_number"] == "MAT-001"
        assert result["description"] == "Test Material"
        assert result["quantity"] == 10
        assert result["unit"] == "EA"
        assert result["price"] == 25.0
        assert result["currency"] == "USD"
        assert result["delivery_date"] == "2023-06-01"
        assert result["status"] == "APPROVED"
        assert result["value"] == 250.0  # quantity * price
        assert result["received_quantity"] == 5
        assert result["remaining_quantity"] == 5  # quantity - received_quantity
        assert result["requisition_reference"] == "REQ-001"
        assert result["requisition_item"] == 1
    
    def test_format_order_for_response(self):
        """Test that orders are formatted correctly for response"""
        # Format the order
        result = format_order_for_response(self.mock_order)
        
        # Verify the result
        assert result["document_number"] == "PO-001"
        assert result["description"] == "Test Order"
        assert result["requester"] == "Test User"
        assert result["vendor"] == "Test Vendor"
        assert result["payment_terms"] == "Net 30"
        assert result["type"] == "STANDARD"
        assert result["status"] == "APPROVED"
        assert result["status_color"] == "primary"  # From p2p_common.STATUS_BADGE_COLORS
        assert result["notes"] == "Test notes"
        assert result["urgent"] is True
        assert result["total_value"] == 250.0
        assert result["requisition_reference"] == "REQ-001"
        assert result["created_at"] == "2023-05-01T12:00:00"
        assert result["updated_at"] == "2023-05-02T14:30:00"
        assert result["created_at_formatted"] == "2023-05-01 12:00:00"
        assert result["updated_at_formatted"] == "2023-05-02 14:30:00"
        
        # Check items are formatted
        assert len(result["items"]) == 1
        item = result["items"][0]
        assert item["item_number"] == 1
        assert item["material_number"] == "MAT-001"
    
    def test_format_orders_list(self):
        """Test that a list of orders is formatted correctly"""
        # Create a list of orders
        orders = [self.mock_order, self.mock_order]
        
        # Add some filters
        filters = {"status": "APPROVED", "vendor": "Test Vendor"}
        
        # Format the list
        result = format_orders_list(orders, filters)
        
        # Verify the result
        assert len(result["orders"]) == 2
        assert result["count"] == 2
        assert result["filters"] == filters
        
        # Check order formatting
        order = result["orders"][0]
        assert order["document_number"] == "PO-001"
        assert order["status"] == "APPROVED"
    
    def test_format_orders_list_without_filters(self):
        """Test that a list of orders is formatted correctly without filters"""
        # Create a list of orders
        orders = [self.mock_order]
        
        # Format the list without filters
        result = format_orders_list(orders)
        
        # Verify the result
        assert len(result["orders"]) == 1
        assert result["count"] == 1
        assert result["filters"] == {}
    
    def test_format_order_item_without_delivery_date(self):
        """Test that order items without delivery dates are formatted correctly"""
        # Modify the mock item to have no delivery date
        self.mock_item.delivery_date = None
        
        # Format the item
        result = format_order_item(self.mock_item)
        
        # Verify delivery_date is None
        assert result["delivery_date"] is None
        
class TestOrderErrorHandling:
    """Tests for the order error handling functions"""
    
    def test_handle_order_not_found(self):
        """Test that order not found errors are handled correctly"""
        # Set up mocks
        mock_request = MagicMock()
        
        # Patch BaseController.redirect_to_route
        with patch('controllers.p2p_order_common.BaseController.redirect_to_route') as mock_redirect:
            mock_redirect.return_value = "redirect_response"
            
            # Call the function
            result = handle_order_not_found("PO-123", mock_request)
            
            # Check the redirect was called correctly
            mock_redirect.assert_called_once_with(
                route_name="order_list",
                query_params={"error_code": "Order PO-123 not found"},
                status_code=303
            )
            assert result == "redirect_response"
    
    def test_log_order_error(self):
        """Test that order errors are logged correctly"""
        # Set up mocks
        mock_monitor_service = MagicMock()
        mock_request = MagicMock()
        
        # Create test exception
        exception = ValueError("Test error")
        
        # Patch log_controller_error
        with patch('controllers.p2p_order_common.log_controller_error') as mock_log_error:
            # Call the function
            log_order_error(
                monitor_service=mock_monitor_service,
                e=exception,
                request=mock_request,
                operation="test_operation",
                document_number="PO-123"
            )
            
            # Check log_controller_error was called correctly
            mock_log_error.assert_called_once_with(
                mock_monitor_service,
                exception,
                mock_request,
                "p2p_order_controller.test_operation",
                "PO-123"
            )
    
    def test_log_order_error_without_document(self):
        """Test that order errors are logged correctly without document number"""
        # Set up mocks
        mock_monitor_service = MagicMock()
        mock_request = MagicMock()
        
        # Create test exception
        exception = ValueError("Test error")
        
        # Patch log_controller_error
        with patch('controllers.p2p_order_common.log_controller_error') as mock_log_error:
            # Call the function
            log_order_error(
                monitor_service=mock_monitor_service,
                e=exception,
                request=mock_request,
                operation="test_operation"
            )
            
            # Check log_controller_error was called correctly
            mock_log_error.assert_called_once_with(
                mock_monitor_service,
                exception,
                mock_request,
                "p2p_order_controller.test_operation",
                None
            ) 