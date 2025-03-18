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

# tests-dest/services/test_p2p_service_basic.py
"""
Basic tests for the P2P service focusing on service initialization, 
data layer interaction, and core functionality.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from models.p2p import (
    P2PDataLayer, DocumentStatus, ProcurementType,
    Requisition, Order
)
from services.p2p_service import P2PService
from services.state_manager import StateManager
from services.material_service import MaterialService
from utils.error_utils import NotFoundError, ValidationError, ConflictError

class TestP2PServiceBasic:
    """Tests for basic P2P service functionality."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Create a clean state manager
        self.state_manager = StateManager()
        
        # Create a material service instance
        self.material_service = MaterialService(self.state_manager)
        
        # Create the P2P service with the test state manager
        self.p2p_service = P2PService(self.state_manager, self.material_service)
    
    def test_service_initialization(self):
        """Test proper service initialization with dependencies."""
        # Check state manager dependency
        assert self.p2p_service.state_manager is self.state_manager
        
        # Check material service dependency
        assert self.p2p_service.material_service is self.material_service
        
        # Check data layer initialization
        assert isinstance(self.p2p_service.data_layer, P2PDataLayer)
        assert self.p2p_service.data_layer.state_manager is self.state_manager
    
    def test_service_with_default_deps(self):
        """Test service creation with default dependencies."""
        # Create a service with no explicit dependencies
        service = P2PService()
        
        # Should use the default state manager
        from services.state_manager import state_manager
        assert service.state_manager is state_manager
        
        # Should use the default material service
        from services.material_service import material_service
        assert service.material_service is material_service
    
    def test_get_nonexistent_requisition(self):
        """Test getting a requisition that doesn't exist."""
        # Try to get a non-existent requisition
        with pytest.raises(NotFoundError) as excinfo:
            self.p2p_service.get_requisition("NONEXISTENT")
        
        # Check error details
        assert "not found" in str(excinfo.value.message)
        assert "NONEXISTENT" in str(excinfo.value.message)
        assert excinfo.value.details["document_number"] == "NONEXISTENT"
        assert excinfo.value.details["entity_type"] == "Requisition"
    
    def test_get_nonexistent_order(self):
        """Test getting an order that doesn't exist."""
        # Try to get a non-existent order
        with pytest.raises(NotFoundError) as excinfo:
            self.p2p_service.get_order("NONEXISTENT")
        
        # Check error details
        assert "not found" in str(excinfo.value.message)
        assert "NONEXISTENT" in str(excinfo.value.message)
        assert excinfo.value.details["document_number"] == "NONEXISTENT"
        assert excinfo.value.details["entity_type"] == "Order"
    
    def test_list_empty_requisitions(self):
        """Test listing requisitions when none exist."""
        # List requisitions from empty state
        requisitions = self.p2p_service.list_requisitions()
        
        # Should return empty list
        assert isinstance(requisitions, list)
        assert len(requisitions) == 0
    
    def test_list_empty_orders(self):
        """Test listing orders when none exist."""
        # List orders from empty state
        orders = self.p2p_service.list_orders()
        
        # Should return empty list
        assert isinstance(orders, list)
        assert len(orders) == 0
    
    def test_filter_requisitions_empty(self):
        """Test filtering requisitions with various parameters when none exist."""
        # Filter with various parameters
        filtered = self.p2p_service.list_requisitions(
            status=DocumentStatus.DRAFT,
            requester="Test User",
            department="IT",
            search_term="test",
            date_from=datetime(2025, 1, 1),
            date_to=datetime(2025, 12, 31)
        )
        
        # Should still return empty list
        assert isinstance(filtered, list)
        assert len(filtered) == 0
    
    def test_filter_orders_empty(self):
        """Test filtering orders with various parameters when none exist."""
        # Filter with various parameters
        filtered = self.p2p_service.list_orders(
            status=DocumentStatus.DRAFT,
            vendor="Test Vendor",
            requisition_reference="REQ001",
            search_term="test",
            date_from=datetime(2025, 1, 1),
            date_to=datetime(2025, 12, 31)
        )
        
        # Should still return empty list
        assert isinstance(filtered, list)
        assert len(filtered) == 0
    
    def test_data_layer_initialization(self):
        """Test that the data layer is properly initialized."""
        # Instead of patching P2PDataLayer itself, patch the constructor within P2PService.__init__
        with patch('services.p2p_service.P2PDataLayer') as mock_data_layer_class:
            # Create a new service instance
            service = P2PService(self.state_manager, self.material_service)
            
            # Verify data layer was initialized with state manager
            mock_data_layer_class.assert_called_once_with(self.state_manager)
    
    def test_error_propagation(self):
        """Test that errors from the data layer are properly propagated."""
        # Create a mock data layer that raises an exception
        mock_data_layer = MagicMock()
        mock_data_layer.get_requisition.side_effect = Exception("Data layer error")
        
        # Set the mock data layer on the service
        self.p2p_service.data_layer = mock_data_layer
        
        # Try to get a requisition
        with pytest.raises(Exception) as excinfo:
            self.p2p_service.get_requisition("REQ001")
        
        # Check error message
        assert "Data layer error" in str(excinfo.value)
        
        # Verify data layer was called
        mock_data_layer.get_requisition.assert_called_once_with("REQ001")
