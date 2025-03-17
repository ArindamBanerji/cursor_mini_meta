# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Critical imports that must be preserved
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, ModuleType

"""Standard test file imports and setup.

This snippet is automatically added to test files by SnippetForTests.py.
It provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration
3. Common test imports and fixtures
4. Service initialization support
5. Logging configuration
6. Test environment variable management
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
    from test_import_helper import setup_test_paths
    setup_test_paths()
    logger.info("Successfully initialized test paths from test_import_helper")
except ImportError as e:
    # Fall back if test_import_helper is not available
    if str(test_dir.parent) not in sys.path:
        sys.path.insert(0, str(test_dir.parent))
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root) if project_root else "")
    logger.warning(f"Failed to import test_import_helper: {e}. Using fallback configuration.")

# Set up test environment variables
def setup_test_env() -> None:
    """Set up test environment variables."""
    try:
        os.environ.setdefault("PYTEST_CURRENT_TEST", "True")
        logger.info("Test environment variables initialized")
    except Exception as e:
        logger.error(f"Error setting up test environment: {e}")

def teardown_test_env() -> None:
    """Clean up test environment variables."""
    try:
        if "PYTEST_CURRENT_TEST" in os.environ:
            del os.environ["PYTEST_CURRENT_TEST"]
        logger.info("Test environment variables cleaned up")
    except KeyError:
        logger.warning("PYTEST_CURRENT_TEST was already removed")
    except Exception as e:
        logger.error(f"Error cleaning up test environment: {e}")

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

# Register setup/teardown hooks
def setup_module(module: ModuleType) -> None:
    """Set up the test module.
    
    Args:
        module: The test module being set up
    """
    logger.info("Setting up test module")
    setup_test_env()

def teardown_module(module: ModuleType) -> None:
    """Tear down the test module.
    
    Args:
        module: The test module being torn down
    """
    logger.info("Tearing down test module")
    teardown_test_env()
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

# test_import_helper.py
"""
Helper module for managing imports in tests.

This module sets up the correct Python paths for tests to ensure
that test modules can import application modules correctly without
namespace conflicts.
"""
import os
import sys
import json
from pathlib import Path

def setup_test_paths():
    """
    Set up Python path for tests.
    
    This function:
    1. Loads config from SAP_HARNESS_CONFIG environment variable
    2. Adds project root to sys.path
    3. Sets up import paths to avoid module conflicts
    
    Returns:
        dict: The loaded configuration
    """
    # Try to load from environment variable
    config_path = os.environ.get("SAP_HARNESS_CONFIG")
    structure = None
    
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, "r") as f:
                structure = json.load(f)
                print(f"Loaded config from {config_path}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading config from {config_path}: {e}")
    
    # Fall back to environment variable or calculation if config not loaded
    if not structure:
        project_root = os.environ.get("SAP_HARNESS_HOME")
        if not project_root:
            # Calculate project root by going up from current file
            current_file = Path(__file__).resolve()
            
            # Search for main.py to identify project root
            for parent in [current_file.parent] + list(current_file.parents):
                if (parent / "main.py").exists():
                    project_root = str(parent)
                    break
            
            # If we couldn't find main.py, use the parent directory of tests-dest
            if not project_root:
                for parent in [current_file.parent] + list(current_file.parents):
                    if (parent / "tests-dest").exists():
                        project_root = str(parent)
                        break
            
            # Last resort: use two directories up from current file
            if not project_root:
                project_root = str(Path(__file__).resolve().parents[1])
        
        structure = {
            "project_root": project_root,
            "test_dirs": ["tests-dest"],
            "module_mappings": {}
        }
    
    # Ensure project_root is in sys.path
    project_root = structure["project_root"]
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"Added {project_root} to Python path")
    
    # Set environment variable if not already set
    if not os.environ.get("SAP_HARNESS_HOME"):
        os.environ["SAP_HARNESS_HOME"] = project_root
        print(f"Set SAP_HARNESS_HOME={project_root}")
    
    # Add test directories to prevent import conflicts
    for test_dir in structure.get("test_dirs", ["tests-dest"]):
        test_path = os.path.join(project_root, test_dir)
        if os.path.exists(test_path) and test_path not in sys.path:
            # Add test directory to path to enable imports from test modules
            sys.path.insert(0, test_path)
            print(f"Added {test_path} to Python path")
    
    # Handle module mappings to prevent conflicts
    for test_path, module_name in structure.get("module_mappings", {}).items():
        full_path = os.path.join(project_root, test_path)
        if os.path.exists(full_path) and full_path not in sys.path:
            sys.path.insert(0, full_path)
            print(f"Added module mapping: {test_path} -> {module_name}")
    
    # Return the structure for reference
    return structure

# Snippet for test files - execute when imported
structure = setup_test_paths()
def setup_module(module):
    """Set up the test module by ensuring PYTEST_CURRENT_TEST is set"""
    logger.info("Setting up test module")
    os.environ["PYTEST_CURRENT_TEST"] = "True"
    
def teardown_module(module):
    """Clean up after the test module"""
    logger.info("Tearing down test module")
    if "PYTEST_CURRENT_TEST" in os.environ:
        del os.environ["PYTEST_CURRENT_TEST"]
