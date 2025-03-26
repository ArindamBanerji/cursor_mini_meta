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

class TestRequisitionUIEndpoints:
    """Test the UI controller endpoints for requisition management."""
    
    def setup_method(self):
        """Set up test method."""
        # Create mock services
        self.p2p_service = MagicMock(spec=P2PService)
        self.material_service = MagicMock(spec=MaterialService)
        self.monitor_service = MagicMock(spec=MonitorService)
        
        # Create mock requisition and list
        self.mock_requisition = self._create_mock_requisition()
        self.mock_requisitions_list = [self._create_mock_requisition() for _ in range(3)]
        
        # Configure service responses
        self.p2p_service.get_requisition.return_value = self.mock_requisition
        self.p2p_service.list_requisitions.return_value = self.mock_requisitions_list
        self.p2p_service.create_requisition.return_value = self.mock_requisition
        self.p2p_service.update_requisition.return_value = self.mock_requisition
        
        # Configure material service
        self.mock_materials = [self._create_mock_material() for _ in range(5)]
        self.material_service.list_materials.return_value = self.mock_materials
        
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
            document_number="REQ123456",
            description="Test Requisition",
            created_at="2023-01-15T10:00:00",
            updated_at="2023-01-15T10:30:00",
            requester="John Doe",
            department="IT Department",
            status=DocumentStatus.DRAFT,
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
        mock_request.url.path = "/p2p/requisitions"
        
        return mock_request
        
    @pytest.mark.asyncio
    async def test_list_requisitions(self):
        """Test listing requisitions."""
        # Arrange
        mock_request = self._create_mock_request(query_params={"status": "DRAFT"})
        
        # Act
        result = await list_requisitions(
            request=mock_request,
            p2p_service=self.p2p_service,
            monitor_service=self.monitor_service
        )
        
        # Assert
        assert result is not None
        assert "requisitions" in result
        assert "count" in result
        assert "filters" in result
        assert "filter_options" in result
        assert result["count"] == len(self.mock_requisitions_list)
        
        # Verify service calls
        self.p2p_service.list_requisitions.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_list_requisitions_with_error(self):
        """Test listing requisitions when an error occurs."""
        # Arrange
        mock_request = self._create_mock_request()
        self.p2p_service.list_requisitions.side_effect = Exception("Test error")
        
        # Act & Assert
        with pytest.raises(Exception):
            await list_requisitions(
                request=mock_request,
                p2p_service=self.p2p_service,
                monitor_service=self.monitor_service
            )
            
        # Verify error logging
        self.monitor_service.log_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_requisition(self):
        """Test getting requisition details."""
        # Arrange
        mock_request = self._create_mock_request()
        document_number = "REQ123456"
        
        # Act
        result = await get_requisition(
            request=mock_request,
            document_number=document_number,
            p2p_service=self.p2p_service,
            monitor_service=self.monitor_service
        )
        
        # Assert
        assert result is not None
        assert "requisition" in result
        assert "formatted_requisition" in result
        assert "can_edit" in result
        assert "can_submit" in result
        assert "title" in result
        assert result["title"] == f"Requisition: {document_number}"
        
        # Verify service calls
        self.p2p_service.get_requisition.assert_called_once_with(document_number)
    
    @pytest.mark.asyncio
    async def test_get_requisition_not_found(self):
        """Test getting a requisition when it doesn't exist."""
        # Arrange
        mock_request = self._create_mock_request()
        document_number = "INVALID123"
        self.p2p_service.get_requisition.side_effect = NotFoundError(f"Requisition {document_number} not found")
        
        # Act
        result = await get_requisition(
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
    async def test_create_requisition_form(self):
        """Test displaying the requisition creation form."""
        # Arrange
        mock_request = self._create_mock_request()
        
        # Act
        result = await create_requisition_form(
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
        assert result["title"] == "Create Requisition"
        
        # Verify service calls
        self.material_service.list_materials.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_requisition(self):
        """Test creating a new requisition."""
        # Arrange
        form_data = {
            "description": "Test Requisition",
            "requester": "John Doe",
            "department": "IT Department",
            "type": "STANDARD",
            "notes": "Test Notes",
            "urgent": "on",
            "item_0_material_number": "MAT001",
            "item_0_description": "Test Material",
            "item_0_quantity": "10",
            "item_0_unit_price": "100",
            "item_0_unit": "EA"
        }
        mock_request = self._create_mock_request(form_data=form_data)
        
        # Mock the redirect response creation
        with patch("controllers.p2p_requisition_ui_controller.RedirectResponse") as mock_redirect:
            mock_redirect.return_value = MagicMock(spec=RedirectResponse)
            
            # Act
            result = await create_requisition(
                request=mock_request,
                p2p_service=self.p2p_service,
                material_service=self.material_service,
                monitor_service=self.monitor_service
            )
            
            # Assert
            assert result is not None
            assert mock_redirect.called
            
            # Verify service calls
            self.p2p_service.create_requisition.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_requisition_with_validation_error(self):
        """Test creating a requisition with invalid data."""
        # Arrange
        form_data = {
            "description": "",  # Missing required field
            "requester": "John Doe",
            "department": "IT Department"
        }
        mock_request = self._create_mock_request(form_data=form_data)
        self.p2p_service.create_requisition.side_effect = ValidationError("Missing required fields")
        
        # Mock the handle_requisition_form_errors function
        with patch("controllers.p2p_requisition_ui_controller.handle_requisition_form_errors") as mock_handle_errors:
            mock_handle_errors.return_value = {"error_code": "Test error"}
            
            # Act
            result = await create_requisition(
                request=mock_request,
                p2p_service=self.p2p_service,
                material_service=self.material_service,
                monitor_service=self.monitor_service
            )
            
            # Assert
            assert result is not None
            assert mock_handle_errors.called
    
    @pytest.mark.asyncio
    async def test_update_requisition_form(self):
        """Test displaying the requisition update form."""
        # Arrange
        mock_request = self._create_mock_request()
        document_number = "REQ123456"
        
        # Act
        result = await update_requisition_form(
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
        assert "requisition" in result
        assert "materials" in result
        
        # Verify service calls
        self.p2p_service.get_requisition.assert_called_once_with(document_number)
        self.material_service.list_materials.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_requisition_form_not_found(self):
        """Test displaying update form for non-existent requisition."""
        # Arrange
        mock_request = self._create_mock_request()
        document_number = "INVALID123"
        self.p2p_service.get_requisition.side_effect = NotFoundError(f"Requisition {document_number} not found")
        
        # Act
        result = await update_requisition_form(
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
    async def test_update_requisition(self):
        """Test updating an existing requisition."""
        # Arrange
        form_data = {
            "description": "Updated Requisition",
            "requester": "John Doe",
            "department": "IT Department",
            "type": "STANDARD",
            "notes": "Updated Notes",
            "urgent": "on",
            "item_0_material_number": "MAT001",
            "item_0_description": "Test Material",
            "item_0_quantity": "20",  # Updated quantity
            "item_0_unit_price": "100",
            "item_0_unit": "EA"
        }
        mock_request = self._create_mock_request(form_data=form_data)
        document_number = "REQ123456"
        
        # Mock the redirect response creation
        with patch("controllers.p2p_requisition_ui_controller.RedirectResponse") as mock_redirect:
            mock_redirect.return_value = MagicMock(spec=RedirectResponse)
            
            # Act
            result = await update_requisition(
                request=mock_request,
                document_number=document_number,
                p2p_service=self.p2p_service,
                material_service=self.material_service,
                monitor_service=self.monitor_service
            )
            
            # Assert
            assert result is not None
            assert mock_redirect.called
            
            # Verify service calls
            self.p2p_service.update_requisition.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_requisition_not_draft(self):
        """Test updating a requisition that is not in draft state."""
        # Arrange
        form_data = {
            "description": "Updated Requisition",
            "requester": "John Doe",
            "department": "IT Department"
        }
        mock_request = self._create_mock_request(form_data=form_data)
        document_number = "REQ123456"
        
        # Configure requisition to be in non-draft state
        self.mock_requisition.status = DocumentStatus.SUBMITTED
        
        # Mock the redirect response creation
        with patch("controllers.p2p_requisition_ui_controller.RedirectResponse") as mock_redirect:
            mock_redirect.return_value = MagicMock(spec=RedirectResponse)
            
            # Act
            result = await update_requisition(
                request=mock_request,
                document_number=document_number,
                p2p_service=self.p2p_service,
                material_service=self.material_service,
                monitor_service=self.monitor_service
            )
            
            # Assert
            assert result is not None
            assert mock_redirect.called
            
            # Verify service calls - should not update
            self.p2p_service.update_requisition.assert_not_called() 