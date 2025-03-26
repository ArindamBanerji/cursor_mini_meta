"""
Test path fixer module to help resolve import issues in tests.

Usage:
    from test_path_fixer import fix_imports
    fix_imports()  # Call this at the top of your test file
"""
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

import os
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_path_fixer")

def fix_imports():
    """Fix imports by setting up the correct Python path.
    
    This handles the special case where imports need to be
    resolved from the project root rather than the tests directory.
    """
    # Find project root
    test_dir = Path(__file__).parent
    project_root = test_dir.parent
    
    # Clear existing module caches that might be problematic
    for module_name in list(sys.modules.keys()):
        if module_name.startswith(('services.', 'models.', 'utils.', 'controllers.')):
            del sys.modules[module_name]
    
    # Add project root to path if not already there
    if str(project_root) not in sys.path:
        # Insert at the beginning to ensure it takes precedence
        sys.path.insert(0, str(project_root))
        logger.info(f"Added project root to sys.path: {project_root}")
    
    # Set environment variables
    os.environ.setdefault("TEST_MODE", "true")
    
    # Try to import a known module to check if paths are working
    try:
        import utils.error_utils
        logger.info("Basic imports are working")
    except ImportError:
        # If we can't import despite adding project root, try more aggressive fixes
        logger.warning("Basic imports still failing after adding project root")
        
        # Add all potential module directories to path
        for dir_name in ["services", "models", "utils", "controllers"]:
            dir_path = project_root / dir_name
            if dir_path.exists():
                # Insert at the beginning for higher precedence
                sys.path.insert(0, str(dir_path))
                logger.info(f"Added {dir_name} directory to sys.path")
    
    # Configure any special environment variables needed for tests
    setup_test_environment()
    
    return project_root

def setup_test_environment():
    """Set up additional environment variables and configurations for tests."""
    # Set environment variables for testing
    os.environ.setdefault("TESTING", "true")
    
    # Other common environment setups
    os.environ.setdefault("LOG_LEVEL", "DEBUG")
    os.environ.setdefault("DATABASE_URL", "memory://test")
    
    # Configure mock state manager if needed
    if "services.state_manager" in sys.modules:
        try:
            from services.state_manager import get_state_manager, StateManager
            # Ensure a clean state manager is available
            state_manager = StateManager()
            
            # Replace the global instance with our test instance
            import types
            original_get_state_manager = get_state_manager
            
            def mock_get_state_manager():
                return state_manager
            
            # Update the module to use our mock function
            sys.modules["services.state_manager"].get_state_manager = mock_get_state_manager
            logger.info("Configured mock StateManager for tests")
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not configure mock StateManager: {e}")

if __name__ == "__main__":
    # If run directly, print diagnostic info
    project_root = fix_imports()
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path}")
    print(f"TEST_MODE: {os.environ.get('TEST_MODE', 'Not set')}")
    
    # Test some imports
    try:
        import services.state_manager
        print("✓ Successfully imported services.state_manager")
    except ImportError as e:
        print(f"✗ Failed to import services.state_manager: {e}")
    
    try:
        import models.material
        print("✓ Successfully imported models.material")
    except ImportError as e:
        print(f"✗ Failed to import models.material: {e}")
    
    try:
        import utils.error_utils
        print("✓ Successfully imported utils.error_utils")
    except ImportError as e:
        print(f"✗ Failed to import utils.error_utils: {e}")
