"""
Simplified conftest.py for testing. 
This version avoids circular imports and provides clean StateManager instances.
"""

import os
import sys
import logging
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Find project root
test_dir = Path(__file__).parent
project_root = None

for parent in [test_dir] + list(test_dir.parents):
    if (parent / "main.py").exists():
        project_root = parent
        break
    if all((parent / d).exists() for d in ["services", "models", "controllers"]):
        project_root = parent
        break

if project_root:
    logger.info(f"Project root detected at: {project_root}")
    
    # Add project root to path 
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.info(f"Added {project_root} to Python path")
else:
    logger.warning("Could not detect project root")

# Service registry - populated lazily by service getters
_service_registry = {}

# Set up test environment variables
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment for all tests."""
    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("TEMPLATE_DIR", "templates")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

@pytest.fixture(autouse=True)
def clean_state_manager(monkeypatch):
    """Create a clean state manager for each test."""
    # Import here to avoid circular imports
    from services.state_manager import StateManager
    
    # Create a fresh instance
    test_state_manager = StateManager()
    
    # Patch both the state_manager singleton and get_state_manager function
    monkeypatch.setattr("services.state_manager.state_manager", test_state_manager)
    monkeypatch.setattr("services.state_manager.get_state_manager", lambda: test_state_manager)
    
    # Clear services registry to ensure clean state
    _service_registry.clear()
    
    return test_state_manager

@pytest.fixture
def test_services(clean_state_manager):
    """Set up test services with clean state."""
    # Import services here to avoid circular imports
    from services.monitor_service import MonitorService
    from services.material_service import MaterialService
    
    # Create and register services
    monitor_service = MonitorService(clean_state_manager)
    material_service = MaterialService(clean_state_manager, monitor_service)
    
    # Register services for discovery
    _service_registry["monitor"] = monitor_service
    _service_registry["material"] = material_service
    
    return {
        "state_manager": clean_state_manager,
        "monitor_service": monitor_service,
        "material_service": material_service
    } 