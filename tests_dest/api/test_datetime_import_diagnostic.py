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
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services from service_imports
from tests_dest.test_helpers.service_imports import (
    BaseService,
    MonitorService, 
    get_monitor_service,
    MonitorHealth,
    MonitorCore
)

"""
Test to diagnose datetime import issues in monitor_health.py
"""

from datetime import datetime

def test_get_timestamp_format():
    """Test that timestamp generation works correctly"""
    monitor_core = MonitorCore()
    monitor_health = MonitorHealth(monitor_core)
    
    # Call a health check which will generate a timestamp internally
    health_data = monitor_health.check_system_health()
    
    # Verify the timestamp format in the health data
    assert isinstance(health_data, dict)
    assert "timestamp" in health_data
    timestamp = health_data["timestamp"]
    assert isinstance(timestamp, str)
    assert "T" in timestamp  # ISO 8601 format contains 'T' between date and time
    assert ":" in timestamp  # Time portion should contain colons
    assert "-" in timestamp  # Date portion should contain hyphens

def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Simple diagnostic test ===")
    print("Successfully executed test_datetime_import_diagnostic.py")
    print("All imports resolved correctly")
    return True

if __name__ == "__main__":
    run_simple_test()
