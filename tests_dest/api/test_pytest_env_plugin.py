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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test imports - plugin is imported by pytest automatically
def test_env_vars_set():
    """Test that the environment variables are set correctly by the plugin."""
    assert 'TEST_ENV' in os.environ
    assert os.environ['TEST_ENV'] == 'True'
    logger.info("Environment variables correctly set by pytest_env_plugin")

if __name__ == "__main__":
    print("=== Running test_pytest_env_plugin.py ===")
    test_env_vars_set()
    print("All tests passed!") 