# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Critical imports that must be preserved
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
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
    logging.warning(f"Failed to import import_helper: {e}. Using fallback configuration.")
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

def find_project_root() -> Path:
    """
    Find the project root directory.
    
    Returns:
        Path to the project root directory.
    """
    # First try environment variable
    project_root = os.environ.get("SAP_HARNESS_HOME")
    if project_root:
        logger.info(f"Project root found in environment: {project_root}")
        return Path(project_root)
    
    # Otherwise, try to detect by traversing up from the current file
    current_file = Path(__file__).resolve()
    parent_dir = current_file.parent
    
    # If we're in tests-dest, the parent is the project root
    if parent_dir.name == 'tests-dest':
        project_root = parent_dir.parent
    else:
        # Otherwise, traverse up until we find a directory that looks like a project root
        potential_root = parent_dir
        while potential_root.name and not (
            (potential_root / 'tests-dest').exists() or
            (potential_root / 'services').exists() or
            (potential_root / 'models').exists()
        ):
            potential_root = potential_root.parent
            if not potential_root.name:  # Reached the root of the filesystem
                break
        
        if potential_root.name:
            project_root = potential_root
        else:
            # If no root found, use current directory's parent as fallback
            project_root = parent_dir
    
    logger.info(f"Project root detected at: {project_root}")
    return project_root

def setup_test_paths() -> Tuple[Path, Path]:
    """
    Set up paths for testing.
    
    This function adds the project root and test directory to sys.path
    to ensure imports work correctly during testing.
    
    Returns:
        Tuple of (project_root, test_dir)
    """
    project_root = find_project_root()
    test_dir = project_root / 'tests-dest'
    
    # Add to sys.path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    if str(test_dir) not in sys.path:
        sys.path.insert(0, str(test_dir))
    
    # Set essential environment variables
    os.environ.setdefault("PROJECT_ROOT", str(project_root))
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root))
    os.environ.setdefault("SAP_HARNESS_CONFIG", str(project_root / "config"))
    os.environ.setdefault("TEST_MODE", "true")
    
    logger.info(f"Set up paths: project_root={project_root}, test_dir={test_dir}")
    return project_root, test_dir

def set_env_variables() -> Dict[str, str]:
    """
    Set environment variables for testing.
    
    Returns:
        Dictionary of environment variables that were set.
    """
    env_vars = {
        "PROJECT_ROOT": os.environ.get("PROJECT_ROOT", ""),
        "SAP_HARNESS_HOME": os.environ.get("SAP_HARNESS_HOME", ""),
        "SAP_HARNESS_CONFIG": os.environ.get("SAP_HARNESS_CONFIG", ""),
        "TEST_MODE": os.environ.get("TEST_MODE", "true")
    }
    
    logger.info(f"Set environment variables: {env_vars}")
    return env_vars

def safe_import(module_name: str) -> Optional[Any]:
    """
    Safely import a module without raising exceptions.
    
    Args:
        module_name: Name of the module to import
        
    Returns:
        Imported module or None if import failed
    """
    try:
        module = __import__(module_name, fromlist=[''])
        return module
    except Exception as e:
        logger.warning(f"Optional import failed: {str(e)}")
        return None

# Set up paths when module is imported
try:
    project_root, test_dir = setup_test_paths()
except Exception as e:
    logger.warning(f"Failed to import test_import_helper: {str(e)}. Using fallback configuration.")
    project_root = Path(os.getcwd())
    test_dir = project_root / 'tests-dest' if (project_root / 'tests-dest').exists() else project_root

# Try to import test fixtures for convenience
try:
    # Use safe import to avoid circular dependencies
    conftest = safe_import('conftest')
    if conftest:
        test_services = getattr(conftest, 'test_services', None)
        state_manager_fixture = getattr(conftest, 'state_manager_fixture', None)
    else:
        test_services = None
        state_manager_fixture = None
except Exception as e:
    logger.warning(f"Failed to import conftest fixtures: {str(e)}")
    test_services = None
    state_manager_fixture = None

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
    
    # Fix the 'models.conftest' namespace issue
    fix_namespace_conflicts()
        
    logger.info(f"Set up paths: project_root={project_root}, test_dir={test_dir}")
    return project_root

def fix_namespace_conflicts() -> None:
    """Fix namespace conflicts in test directories.
    
    This function handles the issue with 'models.conftest' by adding
    the conftest module to sys.modules under a different name.
    """
    try:
        # Check if we're in a subdirectory that might have namespace conflicts
        current_dir = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
        
        # If we're importing from models directory, make sure it doesn't conflict
        if 'models.conftest' in sys.modules:
            # Already registered - nothing to do
            return
            
        conftest_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conftest.py')
        if os.path.exists(conftest_path):
            # Create a module for the root conftest to avoid conflicts
            import importlib.util
            import types
            
            # Load the root conftest module
            spec = importlib.util.spec_from_file_location("root_conftest", conftest_path)
            root_conftest = importlib.util.module_from_spec(spec)
            sys.modules["root_conftest"] = root_conftest
            spec.loader.exec_module(root_conftest)
            
            # If in models directory, create a special module to avoid the models.conftest conflict
            if current_dir == 'models':
                sys.modules['model_tests.conftest'] = root_conftest
                sys.modules['models.conftest'] = types.ModuleType('models.conftest')
                logger.info("Fixed namespace conflict for models.conftest")
    except Exception as e:
        logger.warning(f"Error fixing namespace conflicts: {e}")

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