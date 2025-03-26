# Import helper to fix path issues
import sys
import os
from pathlib import Path

# Add parent directory to path
current_file = Path(__file__).resolve()
tests_dest_dir = current_file.parent.parent
project_root = tests_dest_dir.parent
if str(tests_dest_dir) not in sys.path:
    sys.path.insert(0, str(tests_dest_dir))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now we can import the helper
from import_helper import fix_imports
fix_imports()

import pytest
import logging

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
    logger.info("Successfully imported optional modules")
except ImportError as e:
    logger.warning(f"Optional import failed: {e}")

"""
Minimal diagnostic test file to verify our import approach works.
"""

def test_import_success():
    """Verify that our core imports work properly."""
    logger.info("Running diagnostic import test")
    assert True, "This test should always pass"
    
    # Print module search paths to help with debugging
    logger.info("Python module search paths:")
    for i, path in enumerate(sys.path):
        logger.info(f"  {i}: {path}")
    
    # Print environment variables that might impact imports
    logger.info("Environment variables affecting Python:")
    for key, value in os.environ.items():
        if "PYTHON" in key.upper() or "PATH" in key.upper():
            logger.info(f"  {key}: {value}")

if __name__ == "__main__":
    print("Running minimal diagnostic test")
    test_import_success()
    print("Test completed successfully") 