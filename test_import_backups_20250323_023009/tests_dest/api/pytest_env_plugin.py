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
def _setup_test_env():
    """
    Fixture to ensure environment variables are set for each test.
    This runs automatically for all tests.
    """
    # No need to set anything here as it's handled by pytest_configure
    yield
    # No need to clean up here as it's handled by pytest_unconfigure 