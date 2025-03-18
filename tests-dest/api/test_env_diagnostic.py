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

"""
Diagnostic tests for environment setup.

This file tests our environment setup functionality to ensure:
1. Project root is correctly detected
2. Python path is properly configured
3. Environment variables are set and cleaned up
4. Async context maintains environment
"""

import os
import sys
import logging
from pathlib import Path
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from test_import_helper import setup_test_paths, setup_test_env_vars

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set up paths
project_root = setup_test_paths()

def test_env_setup_basic():
    """Basic test to verify environment setup without fixtures."""
    logger.info("Running basic environment test")
    
    # Check if project root is in sys.path
    assert str(project_root) in sys.path, "Project root should be in sys.path"
    
    # Log current environment state
    logger.info("Current environment state:")
    for key in ['SAP_HARNESS_HOME', 'SAP_HARNESS_CONFIG', 'PYTEST_CURRENT_TEST']:
        value = os.environ.get(key)
        logger.info(f"{key}: {value}")

def test_env_setup_with_monkeypatch(monkeypatch):
    """Test environment setup using monkeypatch fixture."""
    logger.info("Running environment test with monkeypatch")
    
    # Set up environment variables using our helper
    setup_test_env_vars(monkeypatch)
    
    # Verify environment variables
    assert os.environ.get('SAP_HARNESS_HOME') == str(project_root)
    # Fix: SAP_HARNESS_CONFIG is now set to project_root + "/config" in test_import_helper.py
    expected_config_path = os.path.join(project_root, "config")
    assert os.environ.get('SAP_HARNESS_CONFIG') == expected_config_path
    
    # Log the value of PYTEST_CURRENT_TEST
    current_test = os.environ.get('PYTEST_CURRENT_TEST')
    logger.info(f"PYTEST_CURRENT_TEST: {current_test}")
    
    # We expect pytest to manage this variable
    assert 'PYTEST_CURRENT_TEST' in os.environ, "PYTEST_CURRENT_TEST should be set by pytest"

@pytest.mark.asyncio
async def test_env_setup_async():
    """Test environment setup in async context."""
    logger.info("Running async environment test")
    
    # Verify path setup persists in async context
    assert str(project_root) in sys.path, "Project root should be in sys.path in async context"
    
    # Log environment state in async context
    logger.info("Environment state in async context:")
    for key in ['SAP_HARNESS_HOME', 'SAP_HARNESS_CONFIG', 'PYTEST_CURRENT_TEST']:
        value = os.environ.get(key)
        logger.info(f"{key}: {value}")
    
    # We expect pytest to manage this variable even in async context
    assert 'PYTEST_CURRENT_TEST' in os.environ, "PYTEST_CURRENT_TEST should be set by pytest in async context"

@pytest.fixture
def setup_test_env_fixture(monkeypatch):
    """Test fixture for environment setup."""
    logger.info("Setting up test environment fixture")
    
    # Set up environment variables
    setup_test_env_vars(monkeypatch)
    
    yield
    
    logger.info("Cleaning up test environment fixture")

def test_env_setup_with_fixture(setup_test_env_fixture):
    """Test environment setup using a fixture."""
    logger.info("Running environment test with fixture")
    
    # Verify environment variables
    assert os.environ.get('SAP_HARNESS_HOME') == str(project_root)
    # Fix: SAP_HARNESS_CONFIG is now set to project_root + "/config" in test_import_helper.py
    expected_config_path = os.path.join(project_root, "config")
    assert os.environ.get('SAP_HARNESS_CONFIG') == expected_config_path
    
    # Log the value of PYTEST_CURRENT_TEST
    current_test = os.environ.get('PYTEST_CURRENT_TEST')
    logger.info(f"PYTEST_CURRENT_TEST: {current_test}")
    
    # We expect pytest to manage this variable
    assert 'PYTEST_CURRENT_TEST' in os.environ, "PYTEST_CURRENT_TEST should be set by pytest"

def test_env_cleanup(monkeypatch):
    """Test environment cleanup after variable setting."""
    logger.info("Running environment cleanup test")
    
    # Set up environment variables
    setup_test_env_vars(monkeypatch)
    
    # Verify variables are set
    assert os.environ.get('SAP_HARNESS_HOME') == str(project_root)
    # Fix: SAP_HARNESS_CONFIG is now set to project_root + "/config" in test_import_helper.py
    expected_config_path = os.path.join(project_root, "config")
    assert os.environ.get('SAP_HARNESS_CONFIG') == expected_config_path
    
    # Let monkeypatch clean up (this happens automatically when the test ends)
    # We just verify that PYTEST_CURRENT_TEST is still managed by pytest
    assert 'PYTEST_CURRENT_TEST' in os.environ, "PYTEST_CURRENT_TEST should still be set by pytest"

if __name__ == "__main__":
    # Run the tests with pytest when file is executed directly
    pytest.main([__file__, '-v']) 