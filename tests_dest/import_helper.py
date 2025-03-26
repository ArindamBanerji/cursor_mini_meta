"""
Simplified import helper for test files.

This module ensures proper module resolution in test files by fixing import paths.

Usage:
    from tests_dest.import_helper import fix_imports
    fix_imports()  # Call this at the top of your test file
"""
import os
import sys
import logging
from pathlib import Path

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("import_helper")

def setup_test_env_vars(monkeypatch):
    """Set up test environment variables.
    
    Args:
        monkeypatch: pytest's monkeypatch fixture
    """
    # Get project root
    current_file = Path(__file__).resolve()
    tests_dest_dir = current_file.parent
    project_root = tests_dest_dir.parent
    
    # Set essential environment variables
    env_vars = {
        "PROJECT_ROOT": str(project_root),
        "SAP_HARNESS_HOME": str(project_root),
        "SAP_HARNESS_CONFIG": str(project_root / "config"),
        "TEST_MODE": "true"
    }
    
    # Use monkeypatch to set environment variables
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
        logger.debug(f"Set environment variable: {key}={value}")

def fix_imports():
    """Fix import paths for test modules.
    
    Returns:
        Path to the project root directory
    """
    try:
        # Find project root (parent of tests_dest directory)
        current_file = Path(__file__).resolve()
        tests_dest_dir = current_file.parent
        project_root = tests_dest_dir.parent
        
        # Add essential paths to sys.path
        paths_to_add = [
            str(project_root),      # Project root
            str(tests_dest_dir)     # Test directory
        ]
        
        # Add paths to sys.path if not already there
        for path in paths_to_add:
            if path not in sys.path:
                sys.path.insert(0, path)
                logger.debug(f"Added to Python path: {path}")
        
        # Set environment variables
        os.environ.setdefault("PROJECT_ROOT", str(project_root))
        os.environ.setdefault("TEST_MODE", "true")
        
        logger.debug(f"Project root: {project_root}")
        return project_root
        
    except Exception as e:
        logger.error(f"Error in fix_imports: {e}")
        # Fall back to adding the current directory
        fallback_dir = Path.cwd()
        if str(fallback_dir) not in sys.path:
            sys.path.insert(0, str(fallback_dir))
        return fallback_dir

def verify_imports():
    """Check if critical modules can be imported.
    
    Returns:
        True if all critical imports succeed, False otherwise
    """
    critical_modules = [
        "services.base_service",
        "models.base_model",
        "utils.error_utils"
    ]
    
    success = True
    for module_name in critical_modules:
        try:
            __import__(module_name)
            logger.debug(f"Successfully imported {module_name}")
        except ImportError as e:
            logger.warning(f"Failed to import {module_name}: {e}")
            success = False
    
    return success

if __name__ == "__main__":
    # Test the import helper when run directly
    logger.setLevel(logging.INFO)
    logger.info("Testing import helper...")
    
    project_root = fix_imports()
    logger.info(f"Project root: {project_root}")
    
    if verify_imports():
        logger.info("✅ All critical imports successful!")
        sys.exit(0)
    else:
        logger.error("❌ Some critical imports failed")
        sys.exit(1) 