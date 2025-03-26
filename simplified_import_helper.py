"""
Simplified import helper for test files.

This module ensures proper module resolution in test files by fixing import paths.

Usage:
    from tests-dest.import_helper import fix_imports
    fix_imports()  # Call this at the top of your test file
"""
import os
import sys
import logging
from pathlib import Path
import importlib

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("import_helper")

def fix_imports():
    """Fix import paths for test modules.
    
    Returns:
        Path to the project root directory
    """
    try:
        # Find project root (parent of tests-dest directory)
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent
        
        # Critical directories that should exist in the root
        critical_dirs = ["services", "models", "utils", "controllers"]
        
        # Verify this is actually the project root
        if not any(Path(project_root / d).exists() for d in critical_dirs):
            logger.warning("Project root validation failed, searching parents...")
            # Try to find project root by looking for critical directories
            for parent in current_file.parents:
                if any(Path(parent / d).exists() for d in critical_dirs):
                    project_root = parent
                    break
        
        # Clean up module cache to prevent stale imports
        _clean_module_cache()
        
        # Add essential paths to sys.path
        _add_paths_to_syspath(project_root)
        
        # Set environment variables
        os.environ.setdefault("PROJECT_ROOT", str(project_root))
        os.environ.setdefault("TEST_MODE", "true")
        os.environ.setdefault("LOG_LEVEL", "DEBUG")
        
        logger.debug(f"Project root: {project_root}")
        return project_root
        
    except Exception as e:
        logger.error(f"Error in fix_imports: {e}")
        # Fall back to adding the current directory
        fallback_dir = Path.cwd()
        if str(fallback_dir) not in sys.path:
            sys.path.insert(0, str(fallback_dir))
        return fallback_dir

def _clean_module_cache():
    """Remove project-related modules from sys.modules to avoid stale imports."""
    project_prefixes = ('services.', 'models.', 'utils.', 'controllers.', 'tests-dest.')
    for module_name in list(sys.modules.keys()):
        if module_name.startswith(project_prefixes):
            sys.modules.pop(module_name, None)

def _add_paths_to_syspath(project_root):
    """Add project paths to sys.path.
    
    Args:
        project_root: Path to the project root
    """
    # Define paths to add
    paths_to_add = [
        project_root,                    # Project root
        project_root / "tests-dest"      # Test directory
    ]
    
    # Add specific module directories
    for module_dir in ["services", "models", "utils", "controllers"]:
        module_path = project_root / module_dir
        if module_path.exists():
            paths_to_add.append(module_path)
    
    # Add paths to sys.path if not already there
    for path in paths_to_add:
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
            logger.debug(f"Added to Python path: {path}")

def verify_imports():
    """Check if critical modules can be imported.
    
    Returns:
        True if all critical imports succeed, False otherwise
    """
    critical_modules = [
        "utils.error_utils",
        "services.state_manager",
        "services.monitor_service"
    ]
    
    success = True
    for module_name in critical_modules:
        try:
            importlib.import_module(module_name)
            logger.debug(f"✓ {module_name}")
        except ImportError as e:
            logger.error(f"✗ {module_name}: {e}")
            success = False
    
    return success

def get_clean_state_manager():
    """Get a fresh StateManager instance for testing.
    
    Returns:
        A clean StateManager instance or None if import fails
    """
    try:
        from services.state_manager import StateManager
        return StateManager()
    except ImportError as e:
        logger.error(f"Cannot create StateManager: {e}")
        return None

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