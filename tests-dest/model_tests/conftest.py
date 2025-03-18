"""
Model test fixtures and configurations.

NOTE: This directory has special mapping to 'model_tests' to avoid namespace conflicts.
"""
import pytest
import sys
import os
from datetime import datetime

# Get project root from environment variable or use path calculation
project_root = os.environ.get("SAP_HARNESS_HOME")
if not project_root:
    # Add project root to path to ensure imports work correctly
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    print(f"SAP_HARNESS_HOME environment variable not set. Using calculated path: {project_root}")

# Add project root to Python path
sys.path.insert(0, project_root)

# Import test_import_helper for proper path setup
test_helper_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, test_helper_path)
from test_import_helper import setup_test_paths, setup_test_env_vars, fix_namespace_conflicts

# Fix namespace conflicts
fix_namespace_conflicts()

# Now that paths are set up, import application modules
from models.common import EntityCollection
from services.state_manager import StateManager

# Import fixtures from root_conftest module to avoid namespace issues
import root_conftest

# Expose fixtures from root conftest
clean_services = root_conftest.clean_services
state_manager_fixture = root_conftest.state_manager_fixture
mock_datetime = root_conftest.mock_datetime
async_state_manager = root_conftest.async_state_manager

@pytest.fixture
def entity_collection():
    """Create an empty entity collection for testing."""
    return EntityCollection(name="test-collection")

@pytest.fixture
def model_state_manager():
    """Create a dedicated state manager for model tests."""
    manager = StateManager()
    manager.clear()
    return manager

@pytest.fixture
async def async_entity_collection():
    """Async fixture creating an empty entity collection for testing."""
    return EntityCollection(name="test-collection")

@pytest.fixture
async def async_model_state_manager():
    """Async fixture creating a dedicated state manager for model tests."""
    manager = StateManager()
    manager.clear()
    return manager
