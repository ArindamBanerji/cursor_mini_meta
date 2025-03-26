"""
Diagnostic test for order creation process.
This file helps diagnose issues with the order creation process in the controller.
"""

import sys
import os
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
import logging
from unittest.mock import MagicMock, patch
from fastapi import Request
from fastapi.responses import RedirectResponse

# Import from service_imports
from tests_dest.test_helpers.service_imports import (
    P2PService,
    MaterialService,
    MonitorService, 
    OrderCreate,
    OrderItem
)

# Import the controller function to test
from controllers.p2p_order_ui_controller import create_order

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestOrderCreateDiagnostic:
    """Diagnostic tests for order creation."""
    
    def setup_method(self):
        """Set up the test environment."""
        # Create mock services
        self.p2p_service = MagicMock(spec=P2PService)
        self.material_service = MagicMock(spec=MaterialService)
        self.monitor_service = MagicMock(spec=MonitorService)
        
        # Create a mock order result
        mock_order = MagicMock()
        mock_order.document_number = "PO123456"
        self.p2p_service.create_order.return_value = mock_order
    
    def _create_mock_request(self, form_data=None):
        """Create a mock request with the given form data."""
        mock_request = MagicMock(spec=Request)
        
        if form_data:
            async def mock_form():
                logger.debug(f"Mock form function called, returning: {form_data}")
                return form_data
            mock_request.form = mock_form
            # Add direct access to form data for validation functions
            mock_request.form_data = form_data
        else:
            logger.debug("No form data provided")
        
        mock_request.url = MagicMock()
        mock_request.url.path = "/p2p/orders"
        
        return mock_request
    
    @pytest.mark.asyncio
    async def test_create_order_diagnostic(self):
        """Diagnostic test for order creation."""
        # Arrange
        form_data = {
            "description": "Test Order",
            "requester": "John Doe",
            "vendor": "Test Vendor",
            "payment_terms": "Net 30",
            "procurement_type": "STANDARD",
            "notes": "Test Notes",
            "item_material_0": "MAT001",
            "item_description_0": "Test Material",
            "item_quantity_0": "10",
            "item_unit_0": "EA",
            "item_price_0": "100",
            "item_currency_0": "USD",
            "item_delivery_date_0": "2023-05-15"
        }
        mock_request = self._create_mock_request(form_data=form_data)
        
        # Mock session utils that aren't awaitable
        with patch("controllers.session_utils.get_flash_messages", return_value=[]) as mock_flash:
            with patch("controllers.session_utils.get_form_data", return_value={}) as mock_form_data:
                with patch("controllers.session_utils.add_flash_message", return_value=None) as mock_add_flash:
                    with patch("controllers.session_utils.store_form_data", return_value=None) as mock_store_form:
                        with patch("controllers.session_utils.get_template_context_with_session", 
                                  lambda request, context: context) as mock_template:
                
                            # Set breakpoints in test for debugging
                            with patch("controllers.p2p_requisition_common.validate_requisition_items_input") as mock_validate:
                                # Log what happens during validate_requisition_items_input call
                                def log_validate_call(*args, **kwargs):
                                    logger.debug(f"validate_requisition_items_input called with: {args}, {kwargs}")
                                    return [{
                                        "material_number": "MAT001",
                                        "description": "Test Material",
                                        "quantity": 10.0,
                                        "unit": "EA",
                                        "price": 100.0
                                    }]
                                mock_validate.side_effect = log_validate_call
                                
                                # Capture the OrderCreate instance
                                original_create_order = self.p2p_service.create_order
                                def log_create_order_call(*args, **kwargs):
                                    logger.debug(f"p2p_service.create_order called with: {args}, {kwargs}")
                                    return original_create_order(*args, **kwargs)
                                self.p2p_service.create_order.side_effect = log_create_order_call
                                
                                # Mock URL service
                                with patch("controllers.p2p_order_ui_controller.url_service") as mock_url:
                                    def log_url_call(*args, **kwargs):
                                        logger.debug(f"url_service.get_url_for_route called with: {args}, {kwargs}")
                                        return "/p2p/orders/PO123456"
                                    mock_url.get_url_for_route.side_effect = log_url_call
                                    
                                    # Mock redirect_with_success as a normal function, not async
                                    with patch("controllers.p2p_order_ui_controller.redirect_with_success") as mock_redirect:
                                        def log_redirect_call(*args, **kwargs):
                                            logger.debug(f"redirect_with_success called with: {args}, {kwargs}")
                                            return RedirectResponse(url="/p2p/orders/PO123456", status_code=303)
                                        mock_redirect.return_value = RedirectResponse(url="/p2p/orders/PO123456", status_code=303)
                                        
                                        # Mock handle_form_error and handle_form_validation_error
                                        with patch("controllers.p2p_order_ui_controller.handle_form_error") as mock_handle_error:
                                            with patch("controllers.p2p_order_ui_controller.handle_form_validation_error") as mock_handle_validation:
                                                
                                                # Act
                                                try:
                                                    # Debug the form data right before calling create_order
                                                    logger.debug(f"About to call create_order with form data: {await mock_request.form()}")
                                                    
                                                    result = await create_order(
                                                        request=mock_request,
                                                        p2p_service=self.p2p_service,
                                                        material_service=self.material_service,
                                                        monitor_service=self.monitor_service
                                                    )
                                                    
                                                    # Assert
                                                    logger.debug(f"Result: {result}")
                                                    logger.debug(f"p2p_service.create_order called: {self.p2p_service.create_order.called}")
                                                    logger.debug(f"Create order call count: {self.p2p_service.create_order.call_count}")
                                                    logger.debug(f"Create order call args: {self.p2p_service.create_order.call_args_list}")
                                                    
                                                    # Success path
                                                    assert isinstance(result, RedirectResponse)
                                                    assert self.p2p_service.create_order.called
                                                except Exception as e:
                                                    # Error path - log the exception
                                                    logger.debug(f"Exception during create_order: {e}", exc_info=True)
                                                    raise 