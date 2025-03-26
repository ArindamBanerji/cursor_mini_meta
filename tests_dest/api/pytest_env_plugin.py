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
"""
Pytest plugin to handle environment variables for tests.
"""
import os
import pytest

def pytest_configure(config):
    """Set up environment variables at the start of test session."""
    os.environ.setdefault('TEST_ENV', 'True')

def pytest_unconfigure(config):
    """Clean up environment variables at the end of test session."""
    os.environ.pop('TEST_ENV', None)

@pytest.fixture(autouse=True)
def setup_test_env():
    """
    Fixture to ensure environment variables are set for each test.
    This runs automatically for all tests.
    """
    # No need to set anything here as it's handled by pytest_configure
    yield
    # No need to clean up here as it's handled by pytest_unconfigure 
def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Simple diagnostic test ===")
    print("Successfully executed pytest_env_plugin.py")
    print("All imports resolved correctly")
    return True

if __name__ == "__main__":
    run_simple_test()
