#!/usr/bin/env python
"""
Template for test files to ensure proper structure and avoid common indentation issues.

This template includes:
1. Standard imports
2. Project path setup
3. Service imports
4. Test fixtures
5. Test methods with proper structure

Note: The indentation in this file is critical. Pay special attention to the
try-except block after the import section.
"""

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
try:
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

# -------------------------------------------------------------------------
# CUSTOM TEST IMPORTS AND FIXTURES
# -------------------------------------------------------------------------
# Add any additional imports specific to this test file here

# Test fixture example
@pytest.fixture
def mock_service():
    """Create a mock service for testing."""
    service = MagicMock(spec=BaseService)
    service.get_data.return_value = {"test": "data"}
    return service

# -------------------------------------------------------------------------
# TEST CLASSES AND METHODS
# -------------------------------------------------------------------------
class TestExample:
    """Example test class demonstrating proper structure."""
    
    def setup_method(self):
        """Set up test environment before each test method."""
        self.app = FastAPI()
        self.client = TestClient(self.app)
        self.test_data = {"key": "value"}
    
    def test_example_functionality(self, mock_service):
        """Test basic functionality with proper assertions."""
        # Arrange
        expected_result = {"test": "data"}
        
        # Act
        result = mock_service.get_data()
        
        # Assert
        assert result == expected_result
        mock_service.get_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality with proper assertions."""
        # Arrange
        mock_async_function = AsyncMock()
        mock_async_function.return_value = {"status": "success"}
        
        # Act
        result = await mock_async_function()
        
        # Assert
        assert result["status"] == "success"
        mock_async_function.assert_called_once()
    
    def test_with_patch(self):
        """Test using patch for mocking."""
        with patch("services.base_service.BaseService.get_data") as mock_get_data:
            mock_get_data.return_value = {"patched": "data"}
            
            # Use the patched function
            from services.base_service import BaseService
            service = BaseService()
            result = service.get_data()
            
            assert result == {"patched": "data"}
            mock_get_data.assert_called_once()

# -------------------------------------------------------------------------
# STANDALONE TEST FUNCTIONS
# -------------------------------------------------------------------------
def test_standalone_function():
    """Example of a standalone test function."""
    assert 1 + 1 == 2
    assert "test".upper() == "TEST"
    
@pytest.mark.parametrize("input_value,expected", [
    (1, 1),
    (2, 4),
    (3, 9),
    (4, 16),
])
def test_parametrized(input_value, expected):
    """Example of a parametrized test."""
    assert input_value * input_value == expected 