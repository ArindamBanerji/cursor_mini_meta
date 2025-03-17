# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Critical imports that must be preserved
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

"""Standard test file imports and setup.

This snippet is automatically added to test files by SnippetForTests.py.
It provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration
3. Common test imports and fixtures
4. Service initialization support
"""

# Find project root dynamically
test_file = Path(__file__).resolve()
test_dir = test_file.parent

# Try to find project root by looking for main.py or known directories
project_root: Optional[Path] = None
for parent in [test_dir] + list(test_dir.parents):
    # Check for main.py as an indicator of project root
    if (parent / "main.py").exists():
        project_root = parent
        break
    # Check for typical project structure indicators
    if all((parent / d).exists() for d in ["services", "models", "controllers"]):
        project_root = parent
        break

# If we still don't have a project root, use parent of the tests-dest directory
if not project_root:
    # Assume we're in a test subdirectory under tests-dest
    for parent in test_dir.parents:
        if parent.name == "tests-dest":
            project_root = parent.parent
            break

# Add project root to path if found
if project_root and str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the test_import_helper
try:
    from test_import_helper import setup_test_paths
    setup_test_paths()
except ImportError:
    # Fall back if test_import_helper is not available
    if str(test_dir.parent) not in sys.path:
        sys.path.insert(0, str(test_dir.parent))
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root) if project_root else "")

# Common test imports
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

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
    from fastapi.testclient import TestClient
except ImportError as e:
    # Log import error but continue - not all tests need all imports
    import logging
    logging.warning(f"Optional import failed: {e}")
    logging.debug("Stack trace:", exc_info=True)
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
