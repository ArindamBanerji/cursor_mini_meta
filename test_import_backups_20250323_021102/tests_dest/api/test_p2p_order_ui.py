# Import helper to fix path issues
from tests-dest.import_helper import fix_imports
fix_imports()

import pytest
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Optional imports - these might fail but won't break tests
try:
    from services.base_service import BaseService
    from services.monitor_service import MonitorService
    from models.base_model import BaseModel
except ImportError as e:
    logger.warning(f"Optional import failed: {e}")


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment for all tests."""
    # Configure test environment
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("TEMPLATE_DIR", "templates")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    
    # Create a clean state for each test
    from services.state_manager import StateManager
    state_manager = StateManager()
    monkeypatch.setattr("services.state_manager.state_manager", state_manager)
    
    # Ensure test isolation
    if hasattr(BaseController, "_instance"):
        BaseController._instance = None

class TestOrderUIEndpoints:
    """Test the UI controller endpoints for order management."""
    
    def setup_method(self):
        """Set up test method."""
        # Create mock services
        self.p2p_service = MagicMock(spec=P2PService)
        self.material_service = MagicMock(spec=MaterialService)
        self.monitor_service = MagicMock(spec=MonitorService)
        
        # Create mock order and list
        self.mock_order = self._create_mock_order()
        self.mock_orders_list = [self._create_mock_order() for _ in range(3)]
        
        # Create mock requisition for testing
        self.mock_requisition = self._create_mock_requisition()
        
        # Configure service responses
        self.p2p_service.get_order.return_value = self.mock_order
        self.p2p_service.list_orders.return_value = self.mock_orders_list
        self.p2p_service.create_order.return_value = self.mock_order
        self.p2p_service.update_order.return_value = self.mock_order
        self.p2p_service.get_requisition.return_value = self.mock_requisition
        self.p2p_service.create_order_from_requisition.return_value = self.mock_order
        
        # Configure material service
        self.mock_materials = [self._create_mock_material() for _ in range(5)]
        self.material_service.list_materials.return_value = self.mock_materials
        
    def _create_mock_order(self):
        """Create a mock order for testing."""
        items = [
            MagicMock(
                item_number=1,
                material_number="MAT001",
                description="Test Material 1",
                quantity=10,
                unit_price=100.0,
                unit="EA",
                total_price=1000.0,
                received_quantity=0,
                currency="USD",
                delivery_date="2023-05-15"
            )
        ]
        
        order = MagicMock(
            document_number="PO123456",
            description="Test Order",
            created_at="2023-01-15T10:00:00",
            updated_at="2023-01-15T10:30:00",
            requester="John Doe",
            vendor="Test Vendor",
            payment_terms="Net 30",
            status=DocumentStatus.DRAFT,
            items=items,
            type=ProcurementType.STANDARD,
            notes="Test Notes",
            urgent=False,
            created_by="user1",
            updated_by="user1",
            requisition_reference="REQ789012"
        )
        
        return order
    
    def _create_mock_requisition(self):
        """Create a mock requisition for testing."""
        items = [
            MagicMock(
                item_number=1,
                material_number="MAT001",
                description="Test Material 1",
                quantity=10,
                unit_price=100.0,
                unit="EA",
                total_price=1000.0
            )
        ]
        
        requisition = MagicMock(
            document_number="REQ789012",
            description="Test Requisition",
            created_at="2023-01-10T10:00:00",
            updated_at="2023-01-10T10:30:00",
            requester="John Doe",
            department="IT Department",
            status=DocumentStatus.APPROVED,
            items=items,
            type=ProcurementType.STANDARD,
            notes="Test Notes",
            urgent=False,
            created_by="user1",
            updated_by="user1"
        )
        
        return requisition
    
    def _create_mock_material(self):
        """Create a mock material for testing."""
        return MagicMock(
            material_number="MAT001",
            description="Test Material",
            type="STANDARD",
            status="ACTIVE",
            unit="EA",
            price=100.0
        )
        
    def _create_mock_request(self, query_params=None, form_data=None, path_params=None):
        """Create a mock request object for testing."""
        mock_request = MagicMock(spec=Request)
        mock_request.query_params = MagicMock()
        mock_request.query_params.get = lambda key, default=None: (query_params or {}).get(key, default)
        mock_request.query_params.items = lambda: (query_params or {}).items()
        
        if form_data:
            async def mock_form():
                return form_data
            mock_request.form = mock_form
        
        mock_request.path_params = path_params or {}
        mock_request.url = MagicMock()
        mock_request.url.path = "/p2p/orders"
        
        return mock_request
        
    @pytest.mark.asyncio
    async def test_list_orders(self):
        """Test listing orders."""
        # Arrange
        mock_request = self._create_mock_request(query_params={"status": "DRAFT", "vendor": "Test Vendor"})
        
        # Act
        result = await list_orders(
            request=mock_request,
            p2p_service=self.p2p_service,
            monitor_service=self.monitor_service
        )
        
        # Assert
        assert result is not None
        assert "orders" in result
        assert "count" in result
        assert "filters" in result
        assert "filter_options" in result
        assert result["count"] == len(self.mock_orders_list)
        
        # Verify service calls
        self.p2p_service.list_orders.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_list_orders_with_error(self):
        """Test listing orders when an error occurs."""
        # Arrange
        mock_request = self._create_mock_request()
        self.p2p_service.list_orders.side_effect = Exception("Test error")
        
        # Act & Assert
        with pytest.raises(Exception):
            await list_orders(
                request=mock_request,
                p2p_service=self.p2p_service,
                monitor_service=self.monitor_service
            )
            
        # Verify error logging
        self.monitor_service.log_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_order(self):
        """Test getting order details."""
        # Arrange
        mock_request = self._create_mock_request()
        document_number = "PO123456"
        
        # Act
        result = await get_order(
            request=mock_request,
            document_number=document_number,
            p2p_service=self.p2p_service,
            monitor_service=self.monitor_service
        )
        
        # Assert
        assert result is not None
        assert "order" in result
        assert "formatted_order" in result
        assert "can_edit" in result
        assert "can_submit" in result
        assert "title" in result
        assert result["title"] == f"Purchase Order: {document_number}"
        
        # Verify service calls
        self.p2p_service.get_order.assert_called_once_with(document_number)
        
        # Check if it tried to get related requisition
        self.p2p_service.get_requisition.assert_called_once_with("REQ789012")
    
    @pytest.mark.asyncio
    async def test_get_order_not_found(self):
        """Test getting an order when it doesn't exist."""
        # Arrange
        mock_request = self._create_mock_request()
        document_number = "INVALID123"
        self.p2p_service.get_order.side_effect = NotFoundError(f"Order {document_number} not found")
        
        # Act
        result = await get_order(
            request=mock_request,
            document_number=document_number,
            p2p_service=self.p2p_service,
            monitor_service=self.monitor_service
        )
        
        # Assert - should handle not found and return a redirect response
        assert isinstance(result, RedirectResponse)
        
        # Verify error logging
        self.monitor_service.log_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_order_form(self):
        """Test displaying the order creation form."""
        # Arrange
        mock_request = self._create_mock_request()
        
        # Act
        result = await create_order_form(
            request=mock_request,
            material_service=self.material_service,
            monitor_service=self.monitor_service
        )
        
        # Assert
        assert result is not None
        assert "title" in result
        assert "form_action" in result
        assert "materials" in result
        assert "procurement_types" in result
        assert result["title"] == "Create Purchase Order"
        
        # Verify service calls
        self.material_service.list_materials.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_order_form_from_requisition(self):
        """Test displaying the order creation form with requisition reference."""
        # Arrange
        mock_request = self._create_mock_request(query_params={"from_requisition": "REQ789012"})
        
        # Act
        result = await create_order_form(
            request=mock_request,
            material_service=self.material_service,
            monitor_service=self.monitor_service
        )
        
        # Assert
        assert result is not None
        assert "title" in result
        assert "requisition" in result
        assert result["requisition"] == self.mock_requisition
        
        # Verify service calls
        self.material_service.list_materials.assert_called_once()
        self.p2p_service.get_requisition.assert_called_once_with("REQ789012")
    
    @pytest.mark.asyncio
    async def test_create_order_form_from_non_approved_requisition(self):
        """Test redirect when requisition is not approved."""
        # Arrange
        mock_request = self._create_mock_request(query_params={"from_requisition": "REQ789012"})
        self.mock_requisition.status = DocumentStatus.DRAFT  # Not approved
        
        # Act
        result = await create_order_form(
            request=mock_request,
            material_service=self.material_service,
            monitor_service=self.monitor_service
        )
        
        # Assert - should redirect with error
        assert isinstance(result, RedirectResponse)
    
    @pytest.mark.asyncio
    async def test_create_order(self):
        """Test creating a new order."""
        # Arrange
        form_data = {
            "description": "Test Order",
            "requester": "John Doe",
            "vendor": "Test Vendor",
            "payment_terms": "Net 30",
            "type": "STANDARD",
            "notes": "Test Notes",
            "urgent": "on",
            "item_material_0": "MAT001",
            "item_description_0": "Test Material",
            "item_quantity_0": "10",
            "item_unit_0": "EA",
            "item_price_0": "100",
            "item_currency_0": "USD",
            "item_delivery_date_0": "2023-05-15"
        }
        mock_request = self._create_mock_request(form_data=form_data)
        
        # Mock the redirect response creation
        with patch("controllers.p2p_order_ui_controller.RedirectResponse") as mock_redirect:
            mock_redirect.return_value = MagicMock(spec=RedirectResponse)
            
            # Act
            result = await create_order(
                request=mock_request,
                p2p_service=self.p2p_service,
                material_service=self.material_service,
                monitor_service=self.monitor_service
            )
            
            # Assert
            assert result is not None
            assert mock_redirect.called
            
            # Verify service calls
            self.p2p_service.create_order.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_order_from_requisition(self):
        """Test creating an order from a requisition."""
        # Arrange
        form_data = {
            "from_requisition": "REQ789012",
            "vendor": "Test Vendor",
            "payment_terms": "Net 30"
        }
        mock_request = self._create_mock_request(form_data=form_data)
        
        # Mock the redirect response creation
        with patch("controllers.p2p_order_ui_controller.RedirectResponse") as mock_redirect:
            mock_redirect.return_value = MagicMock(spec=RedirectResponse)
            
            # Act
            result = await create_order(
                request=mock_request,
                p2p_service=self.p2p_service,
                material_service=self.material_service,
                monitor_service=self.monitor_service
            )
            
            # Assert
            assert result is not None
            assert mock_redirect.called
            
            # Verify service calls
            self.p2p_service.create_order_from_requisition.assert_called_once_with(
                "REQ789012", "Test Vendor", "Net 30"
            )
    
    @pytest.mark.asyncio
    async def test_create_order_with_validation_error(self):
        """Test creating an order with invalid data."""
        # Arrange
        form_data = {
            "description": "Test Order",
            "requester": "John Doe",
            "vendor": "",  # Missing required field
            "payment_terms": "Net 30"
        }
        mock_request = self._create_mock_request(form_data=form_data)
        self.p2p_service.create_order.side_effect = ValidationError("Missing required fields")
        
        # Mock the handle_order_form_errors function
        with patch("controllers.p2p_order_ui_controller.handle_order_form_errors") as mock_handle_errors:
            mock_handle_errors.return_value = {"error_code": "Test error"}
            
            # Act
            result = await create_order(
                request=mock_request,
                p2p_service=self.p2p_service,
                material_service=self.material_service,
                monitor_service=self.monitor_service
            )
            
            # Assert
            assert result is not None
            assert mock_handle_errors.called
    
    @pytest.mark.asyncio
    async def test_update_order_form(self):
        """Test displaying the order update form."""
        # Arrange
        mock_request = self._create_mock_request()
        document_number = "PO123456"
        
        # Act
        result = await update_order_form(
            request=mock_request,
            document_number=document_number,
            p2p_service=self.p2p_service,
            material_service=self.material_service,
            monitor_service=self.monitor_service
        )
        
        # Assert
        assert result is not None
        assert "title" in result
        assert "form_action" in result
        assert "order" in result
        assert "materials" in result
        
        # Verify service calls
        self.p2p_service.get_order.assert_called_once_with(document_number)
        self.material_service.list_materials.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_order_form_not_found(self):
        """Test displaying update form for non-existent order."""
        # Arrange
        mock_request = self._create_mock_request()
        document_number = "INVALID123"
        self.p2p_service.get_order.side_effect = NotFoundError(f"Order {document_number} not found")
        
        # Act
        result = await update_order_form(
            request=mock_request,
            document_number=document_number,
            p2p_service=self.p2p_service,
            material_service=self.material_service,
            monitor_service=self.monitor_service
        )
        
        # Assert - should handle not found and return a redirect response
        assert isinstance(result, RedirectResponse)
        
        # Verify error logging
        self.monitor_service.log_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_receive_order_form(self):
        """Test displaying the order receiving form."""
        # Arrange
        mock_request = self._create_mock_request()
        document_number = "PO123456"
        
        # Configure order to be in APPROVED state
        self.mock_order.status = DocumentStatus.APPROVED
        
        # Act
        result = await receive_order_form(
            request=mock_request,
            document_number=document_number,
            p2p_service=self.p2p_service,
            monitor_service=self.monitor_service
        )
        
        # Assert
        assert result is not None
        assert "title" in result
        assert "form_action" in result
        assert "order" in result
        assert "items" in result
        
        # Verify service calls
        self.p2p_service.get_order.assert_called_once_with(document_number)
    
    @pytest.mark.asyncio
    async def test_receive_order_form_not_approved(self):
        """Test receiving form for non-approved order."""
        # Arrange
        mock_request = self._create_mock_request()
        document_number = "PO123456"
        
        # Configure order to be in DRAFT state (not APPROVED)
        self.mock_order.status = DocumentStatus.DRAFT
        
        # Act
        result = await receive_order_form(
            request=mock_request,
            document_number=document_number,
            p2p_service=self.p2p_service,
            monitor_service=self.monitor_service
        )
        
        # Assert - should redirect with error
        assert isinstance(result, RedirectResponse)
    
    @pytest.mark.asyncio
    async def test_receive_order_form_not_found(self):
        """Test receiving form for non-existent order."""
        # Arrange
        mock_request = self._create_mock_request()
        document_number = "INVALID123"
        self.p2p_service.get_order.side_effect = NotFoundError(f"Order {document_number} not found")
        
        # Act
        result = await receive_order_form(
            request=mock_request,
            document_number=document_number,
            p2p_service=self.p2p_service,
            monitor_service=self.monitor_service
        )
        
        # Assert - should handle not found and return a redirect response
        assert isinstance(result, RedirectResponse)
        
        # Verify error logging
        self.monitor_service.log_error.assert_called_once() 