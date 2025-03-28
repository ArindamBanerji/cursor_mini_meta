# Add path setup to find the tests_dest module
import sys
import os
from pathlib import Path

# Add parent directory to path so Python can find the tests_dest module
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent  # Go up two levels to reach project root
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import helper to fix path issues
from tests_dest.import_helper import fix_imports
fix_imports()
# Import helper to fix path issues
from tests_dest.import_helper import fix_imports
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
from pathlib import Path
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