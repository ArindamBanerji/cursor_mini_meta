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
Test helper for setting up import paths for tests.
"""
import os
import sys
import logging
import pytest
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def find_project_root() -> str:
    """Find the project root directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level from tests-dest to find the project root
    return os.path.dirname(current_dir)

def setup_test_paths() -> str:
    """Set up Python path for tests.
    
    Returns:
        The project root path
    """
    project_root = find_project_root()
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Also ensure test dir is in path
    test_dir = os.path.dirname(os.path.abspath(__file__))
    if test_dir not in sys.path:
        sys.path.insert(0, test_dir)
        
    logger.info(f"Set up paths: project_root={project_root}, test_dir={test_dir}")
    return project_root

def setup_test_env_vars(monkeypatch: pytest.MonkeyPatch) -> str:
    """Set up environment variables for tests.
    
    Returns:
        The project root path
    """
    project_root = find_project_root()
    env_vars: Dict[str, str] = {
        "PROJECT_ROOT": project_root,
        "SAP_HARNESS_HOME": project_root,
        "SAP_HARNESS_CONFIG": os.path.join(project_root, "config"),
        "TEST_MODE": "true"
    }
    
    # Set environment variables using monkeypatch
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    # Handle PYTEST_CURRENT_TEST specially
    if "PYTEST_CURRENT_TEST" not in os.environ:
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "test_setup")
    
    logger.info(f"Set environment variables: {env_vars}")
    return project_root

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    """Set up test environment."""
    # Setup paths first
    project_root = setup_test_paths()
    
    # Then setup environment variables
    setup_test_env_vars(monkeypatch)
    
    # Set PYTEST_CURRENT_TEST for the current test
    test_name = request.node.name if request.node else "unknown_test"
    monkeypatch.setenv("PYTEST_CURRENT_TEST", f"{test_name} (setup)")
    
    logger.info(f"Test environment initialized for {test_name}")
    
    # Yield for test execution
    yield
    
    # Update PYTEST_CURRENT_TEST for teardown
    try:
        # At teardown, first check if it exists
        if "PYTEST_CURRENT_TEST" in os.environ:
            monkeypatch.setenv("PYTEST_CURRENT_TEST", f"{test_name} (teardown)")
        else:
            # If it doesn't exist, create it to avoid errors
            monkeypatch.setenv("PYTEST_CURRENT_TEST", "test_teardown")
    except Exception as e:
        logger.warning(f"Error handling PYTEST_CURRENT_TEST: {e}")
    
    logger.info(f"Test environment cleaned up for {test_name}") 