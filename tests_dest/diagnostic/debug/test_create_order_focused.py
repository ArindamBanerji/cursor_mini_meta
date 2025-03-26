"""
Focused diagnostic test for the create_order function.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so Python can find the tests_dest module
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent  # Go up to project root
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import helper to fix imports
from tests_dest.import_helper import fix_imports
fix_imports()

import pytest
import logging
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import Request
from fastapi.responses import RedirectResponse

# Import from service_imports
from tests_dest.test_helpers.service_imports import (
    P2PService,
    MaterialService,
    MonitorService, 
    OrderCreate
)

# Import the controller function to test
from controllers.p2p_order_ui_controller import create_order

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestCreateOrderFocused:
    """Focused tests for the create_order function."""
    
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
                logger.debug(f"Returning form data: {form_data}")
                return form_data
            mock_request.form = mock_form
        
        return mock_request
    
    @pytest.mark.asyncio
    async def test_create_order_regular(self):
        """Test the standard flow of create_order function."""
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
        
        # Setup request with form data
        mock_request = self._create_mock_request(form_data=form_data)
        
        # Create AsyncMock for session utilities
        redirect_success_mock = AsyncMock(return_value=RedirectResponse(url="/success"))
        handle_error_mock = AsyncMock(return_value=None)
        handle_validation_mock = AsyncMock(return_value=None)
        
        # Configure all the patches we need
        with patch("controllers.p2p_order_ui_controller.redirect_with_success", redirect_success_mock):
            with patch("controllers.p2p_order_ui_controller.handle_form_error", handle_error_mock):
                with patch("controllers.p2p_order_ui_controller.handle_form_validation_error", handle_validation_mock):
                    with patch("controllers.p2p_requisition_common.validate_requisition_items_input") as mock_validate:
                        # Return item data from the validation function
                        mock_validate.return_value = [{
                            "material_number": "MAT001",
                            "description": "Test Material",
                            "quantity": 10.0,
                            "unit": "EA",
                            "price": 100.0
                        }]
                        
                        # Mock URL service for the redirect function
                        with patch("controllers.p2p_order_ui_controller.url_service") as mock_url_service:
                            mock_url_service.get_url_for_route.return_value = "/p2p/orders/PO123456"
                            
                            # Act - Call the controller function
                            try:
                                result = await create_order(
                                    request=mock_request,
                                    p2p_service=self.p2p_service,
                                    material_service=self.material_service,
                                    monitor_service=self.monitor_service
                                )
                                
                                # Verify and log
                                logger.debug(f"Result: {result}")
                                logger.debug(f"p2p_service.create_order called: {self.p2p_service.create_order.called}")
                                if self.p2p_service.create_order.called:
                                    logger.debug(f"Call args: {self.p2p_service.create_order.call_args}")
                                
                                # Assert
                                assert self.p2p_service.create_order.called, "p2p_service.create_order should have been called"
                                assert isinstance(result, RedirectResponse), "Result should be a RedirectResponse"
                                
                            except Exception as e:
                                logger.error(f"Exception during test: {e}", exc_info=True)
                                raise 