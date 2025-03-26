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

# tests-dest/unit/test_p2p_requisition_common.py
import pytest
from datetime import datetime, date
from unittest.mock import MagicMock, patch
from fastapi import Request
from fastapi.responses import RedirectResponse
from typing import Dict, List

from controllers.p2p_requisition_common import (
    # Formatting functions
    format_requisition_for_response,
    format_requisition_item,
    format_requisitions_list,
    
    # Validation functions
    validate_requisition_items_input,
    
    # Error handling
    handle_requisition_not_found,
    log_requisition_error
)
from controllers import BaseController
from models.p2p import Requisition, RequisitionItem, DocumentStatus, ProcurementType
from utils.error_utils import NotFoundError

class TestRequisitionFormatting:
    """Tests for the requisition formatting functions"""
    
    def setup_method(self):
        """Set up test data for each test"""
        # Create a mock requisition item
        self.mock_item = MagicMock(spec=RequisitionItem)
        self.mock_item.item_number = 1
        self.mock_item.material_number = "MAT-001"
        self.mock_item.description = "Test Material"
        self.mock_item.quantity = 10
        self.mock_item.unit = "EA"
        self.mock_item.price = 25.0
        self.mock_item.currency = "USD"
        self.mock_item.delivery_date = date(2023, 6, 1)
        self.mock_item.status = DocumentStatus.APPROVED
        self.mock_item.assigned_to_order = "PO-001"
        
        # Create a mock requisition
        self.mock_requisition = MagicMock(spec=Requisition)
        self.mock_requisition.document_number = "REQ-001"
        self.mock_requisition.description = "Test Requisition"
        self.mock_requisition.requester = "Test User"
        self.mock_requisition.department = "IT"
        self.mock_requisition.type = ProcurementType.STANDARD
        self.mock_requisition.status = DocumentStatus.APPROVED
        self.mock_requisition.notes = "Test notes"
        self.mock_requisition.urgent = True
        self.mock_requisition.items = [self.mock_item]
        self.mock_requisition.total_value = 250.0
        self.mock_requisition.created_at = datetime(2023, 5, 1, 12, 0, 0)
        self.mock_requisition.updated_at = datetime(2023, 5, 2, 14, 30, 0)
    
    def test_format_requisition_item(self):
        """Test that requisition items are formatted correctly"""
        # Format the item
        result = format_requisition_item(self.mock_item)
        
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
        assert result["assigned_to_order"] == "PO-001"
    
    def test_format_requisition_for_response(self):
        """Test that requisitions are formatted correctly for response"""
        # Format the requisition
        result = format_requisition_for_response(self.mock_requisition)
        
        # Verify the result
        assert result["document_number"] == "REQ-001"
        assert result["description"] == "Test Requisition"
        assert result["requester"] == "Test User"
        assert result["department"] == "IT"
        assert result["type"] == "STANDARD"
        assert result["status"] == "APPROVED"
        assert result["status_color"] == "primary"  # From p2p_common.STATUS_BADGE_COLORS
        assert result["notes"] == "Test notes"
        assert result["urgent"] is True
        assert result["total_value"] == 250.0
        assert result["created_at"] == "2023-05-01T12:00:00"
        assert result["updated_at"] == "2023-05-02T14:30:00"
        assert result["created_at_formatted"] == "2023-05-01 12:00:00"
        assert result["updated_at_formatted"] == "2023-05-02 14:30:00"
        
        # Check items are formatted
        assert len(result["items"]) == 1
        item = result["items"][0]
        assert item["item_number"] == 1
        assert item["material_number"] == "MAT-001"
    
    def test_format_requisitions_list(self):
        """Test that a list of requisitions is formatted correctly"""
        # Create a list of requisitions
        requisitions = [self.mock_requisition, self.mock_requisition]
        
        # Add some filters
        filters = {"status": "APPROVED", "department": "IT"}
        
        # Format the list
        result = format_requisitions_list(requisitions, filters)
        
        # Verify the result
        assert len(result["requisitions"]) == 2
        assert result["count"] == 2
        assert result["filters"] == filters
        
        # Check requisition formatting
        req = result["requisitions"][0]
        assert req["document_number"] == "REQ-001"
        assert req["status"] == "APPROVED"
    
    def test_format_requisitions_list_without_filters(self):
        """Test that a list of requisitions is formatted correctly without filters"""
        # Create a list of requisitions
        requisitions = [self.mock_requisition]
        
        # Format the list without filters
        result = format_requisitions_list(requisitions)
        
        # Verify the result
        assert len(result["requisitions"]) == 1
        assert result["count"] == 1
        assert result["filters"] == {}

class TestRequisitionValidation:
    """Tests for the requisition validation functions"""
    
    def test_validate_requisition_items_valid(self):
        """Test validation with valid items"""
        # Create valid items
        items = [
            {
                "item_number": 1,
                "description": "Test Item 1",
                "quantity": "10",
                "price": "25.0",
                "unit": "EA",
                "material_number": "MAT-001"
            },
            {
                "item_number": 2,
                "description": "Test Item 2",
                "quantity": "5",
                "price": "15.0",
                "unit": "EA"
            }
        ]
        
        # Create mock material service
        mock_material_service = MagicMock()
        mock_material = MagicMock()
        mock_material.status = "ACTIVE"
        mock_material_service.get_material.return_value = mock_material
        
        # Validate the items
        errors = validate_requisition_items_input(items, mock_material_service)
        
        # Verify no errors
        assert len(errors) == 0
        # Verify material service was called for the first item
        mock_material_service.get_material.assert_called_once_with("MAT-001")
    
    def test_validate_requisition_items_invalid(self):
        """Test validation with invalid items"""
        # Create invalid items
        items = [
            {
                "item_number": 1,
                "description": "",  # Missing description
                "quantity": "-10",  # Negative quantity
                "price": "abc",  # Invalid price
                "unit": "EA",
                "material_number": "MAT-001"  # Will be not found
            },
            {
                "item_number": 2,
                "description": "Test Item 2",
                "quantity": "0",  # Zero quantity
                "price": "-5.0",  # Negative price
                "unit": "EA",
                "material_number": "MAT-002"  # Will be deprecated
            }
        ]
        
        # Create mock material service
        mock_material_service = MagicMock()
        
        # Configure first material to not be found
        mock_material_service.get_material.side_effect = [
            NotFoundError("Material MAT-001 not found"),
            MagicMock(status="DEPRECATED")  # Second material is deprecated
        ]
        
        # Validate the items
        errors = validate_requisition_items_input(items, mock_material_service)
        
        # Verify errors
        assert len(errors) == 2
        
        # Check first item errors
        assert errors[0]["item_number"] == 1
        assert "description" in errors[0]["errors"]
        assert "quantity" in errors[0]["errors"]
        assert "price" in errors[0]["errors"]
        assert "material_number" in errors[0]["errors"]
        assert "not found" in errors[0]["errors"]["material_number"]
        
        # Check second item errors
        assert errors[1]["item_number"] == 2
        assert "quantity" in errors[1]["errors"]
        assert "price" in errors[1]["errors"]
        assert "material_number" in errors[1]["errors"]
        assert "Deprecated" in errors[1]["errors"]["material_number"]
    
    def test_validate_requisition_items_material_error(self):
        """Test validation when material service throws an error"""
        # Create item with material
        items = [
            {
                "item_number": 1,
                "description": "Test Item",
                "quantity": "10",
                "price": "25.0",
                "unit": "EA",
                "material_number": "MAT-001"
            }
        ]
        
        # Create mock material service
        mock_material_service = MagicMock()
        
        # Configure material service to throw an unexpected error
        mock_material_service.get_material.side_effect = Exception("Unexpected error")
        
        # Validate the items
        errors = validate_requisition_items_input(items, mock_material_service)
        
        # Verify error for material
        assert len(errors) == 1
        assert "material_number" in errors[0]["errors"]
        assert "Error validating material" in errors[0]["errors"]["material_number"]
        assert "Unexpected error" in errors[0]["errors"]["material_number"]

class TestRequisitionErrorHandling:
    """Tests for the requisition error handling functions"""
    
    def test_handle_requisition_not_found(self):
        """Test that requisition not found errors are handled correctly"""
        # Set up mocks
        mock_request = MagicMock()
        
        # Patch BaseController.redirect_to_route
        with patch('controllers.p2p_requisition_common.BaseController.redirect_to_route') as mock_redirect:
            mock_redirect.return_value = "redirect_response"
            
            # Call the function
            result = handle_requisition_not_found("REQ-123", mock_request)
            
            # Check the redirect was called correctly
            mock_redirect.assert_called_once_with(
                route_name="requisition_list",
                query_params={"error_code": "Requisition REQ-123 not found"},
                status_code=303
            )
            assert result == "redirect_response"
    
    def test_log_requisition_error(self):
        """Test that requisition errors are logged correctly"""
        # Set up mocks
        mock_monitor_service = MagicMock()
        mock_request = MagicMock()
        
        # Create test exception
        exception = ValueError("Test error")
        
        # Patch log_controller_error
        with patch('controllers.p2p_requisition_common.log_controller_error') as mock_log_error:
            # Call the function
            log_requisition_error(
                monitor_service=mock_monitor_service,
                e=exception,
                request=mock_request,
                operation="test_operation",
                document_number="REQ-123"
            )
            
            # Check log_controller_error was called correctly
            mock_log_error.assert_called_once_with(
                mock_monitor_service,
                exception,
                mock_request,
                "p2p_requisition_controller.test_operation",
                "REQ-123"
            )
    
    def test_log_requisition_error_without_document(self):
        """Test that requisition errors are logged correctly without document number"""
        # Set up mocks
        mock_monitor_service = MagicMock()
        mock_request = MagicMock()
        
        # Create test exception
        exception = ValueError("Test error")
        
        # Patch log_controller_error
        with patch('controllers.p2p_requisition_common.log_controller_error') as mock_log_error:
            # Call the function
            log_requisition_error(
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
                "p2p_requisition_controller.test_operation",
                None
            ) 