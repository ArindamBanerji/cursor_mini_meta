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
Test to diagnose get_iso_timestamp import path.
"""

import pytest
import sys
import os
from importlib import util
from services.monitor_health import MonitorHealth
from services.monitor_core import MonitorCore

def print_module_info(name):
    """Print information about where a module is loaded from."""
    if name in sys.modules:
        module = sys.modules[name]
        print(f"\nModule {name}:")
        print(f"  Location: {getattr(module, '__file__', 'Unknown')}")
        print(f"  Package: {getattr(module, '__package__', 'Unknown')}")
        print(f"  Path: {getattr(module, '__path__', 'Unknown')}")
        return True
    return False

def test_trace_imports():
    """Trace the import path of get_iso_timestamp."""
    print("\nTracing imports for get_iso_timestamp...")
    
    # Print relevant modules
    modules_to_check = [
        'services',
        'services.monitor_health',
        'services.monitor_health_helpers',
    ]
    
    for module_name in modules_to_check:
        if print_module_info(module_name):
            spec = util.find_spec(module_name)
            if spec:
                print(f"  Spec location: {spec.origin}")
                if spec.submodule_search_locations:
                    print(f"  Search locations: {spec.submodule_search_locations}")
    
    # Try to import and trace get_iso_timestamp
    print("\nAttempting to import get_iso_timestamp...")
    try:
        from services.monitor_health_helpers import get_iso_timestamp
        print("Successfully imported get_iso_timestamp")
        print(f"Function location: {get_iso_timestamp.__module__}")
    except ImportError as e:
        print(f"Import error: {str(e)}")
        
    # Check the actual MonitorHealth class usage
    print("\nChecking MonitorHealth class usage...")
    monitor_core = MonitorCore()
    monitor_health = MonitorHealth(monitor_core)
    
    try:
        timestamp = monitor_health._get_iso_timestamp()
        print(f"Successfully called _get_iso_timestamp: {timestamp}")
    except Exception as e:
        print(f"Error calling _get_iso_timestamp: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Print Python path
    print("\nPython path:")
    for path in sys.path:
        print(f"  {path}") 