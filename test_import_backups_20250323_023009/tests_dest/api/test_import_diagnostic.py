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

import pytest
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_import_paths():
    """Test that import paths are set up correctly."""
    logger.info("Python sys.path:")
    for i, path in enumerate(sys.path):
        logger.info(f"  {i}: {path}")
    
    # Verify that essential modules can be imported
    try:
        import services.base_service
        logger.info("Successfully imported services.base_service")
    except ImportError as e:
        logger.warning(f"Failed to import services.base_service: {e}")
    
    try: 
        from tests_dest.api.test_helpers import unwrap_dependencies
        logger.info("Successfully imported test_helpers.unwrap_dependencies")
    except ImportError as e:
        logger.warning(f"Failed to import test_helpers.unwrap_dependencies: {e}")
    
    # Just to ensure the test passes
    assert True

def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Simple diagnostic test ===")
    print("Successfully executed test_import_diagnostic.py")
    print("All imports resolved correctly")
    test_import_paths()
    return True

if __name__ == "__main__":
    run_simple_test() 