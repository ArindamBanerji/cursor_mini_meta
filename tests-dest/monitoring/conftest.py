"""
Monitoring test fixtures and configurations.
"""
import pytest
import sys
import os
import logging
import json
from datetime import datetime, timedelta

# Get project root from environment variable or use path calculation
project_root = os.environ.get("SAP_HARNESS_HOME")
if not project_root:
    # Add project root to path to ensure imports work correctly
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    print(f"SAP_HARNESS_HOME environment variable not set. Using calculated path: {project_root}")

# Add project root to Python path
sys.path.insert(0, project_root)

# Import directly from root conftest by getting the path and adding it to sys.path
root_conftest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_conftest_path)

# Now that paths are set up, import application modules
from services.monitor_service import SystemMetrics, ErrorLog, MonitorService
from services.state_manager import state_manager

# Import fixtures from parent conftest.py file
from conftest import (
    clean_services,
    state_manager_fixture,
    monitor_service_fixture,
    test_client,
    mock_datetime,
    async_state_manager,
    async_monitor_service
)

# Configure logging for monitoring tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("monitoring_tests")

@pytest.fixture
def reset_monitoring_state():
    """Reset the monitoring state."""
    logger.info("Resetting monitoring state for test")
    # Clear monitoring-specific state
    state_manager.set("system_metrics", [])
    state_manager.set("error_logs", [])
    state_manager.set("component_status", {})
    return state_manager

@pytest.fixture
def sample_metrics():
    """Create sample metrics for testing."""
    now = datetime.now()
    return [
        {
            "timestamp": (now - timedelta(hours=2)).isoformat(),
            "cpu_percent": 50.0,
            "memory_usage": 60.0,
            "available_memory": 8.0,
            "disk_usage": 70.0
        },
        {
            "timestamp": (now - timedelta(hours=1)).isoformat(),
            "cpu_percent": 30.0,
            "memory_usage": 40.0,
            "available_memory": 12.0,
            "disk_usage": 50.0
        }
    ]

@pytest.fixture
async def async_reset_monitoring_state():
    """Async fixture resetting the monitoring state."""
    logger.info("Resetting monitoring state for async test")
    # Clear monitoring-specific state
    state_manager.set("system_metrics", [])
    state_manager.set("error_logs", [])
    state_manager.set("component_status", {})
    return state_manager

@pytest.fixture
async def async_sample_metrics():
    """Async fixture creating sample metrics for testing."""
    now = datetime.now()
    return [
        {
            "timestamp": (now - timedelta(hours=2)).isoformat(),
            "cpu_percent": 50.0,
            "memory_usage": 60.0,
            "available_memory": 8.0,
            "disk_usage": 70.0
        },
        {
            "timestamp": (now - timedelta(hours=1)).isoformat(),
            "cpu_percent": 30.0,
            "memory_usage": 40.0,
            "available_memory": 12.0,
            "disk_usage": 50.0
        }
    ]
