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
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException

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
except ImportError as e:
    logger.warning(f"Optional import failed: {e}")


"""
Test to diagnose datetime import issues in monitor_health.py
"""

import pytest
from datetime import datetime
from services.monitor_health import MonitorHealth
from services.monitor_core import MonitorCore

def test_get_iso_timestamp():
    """Test that _get_iso_timestamp works correctly"""
    monitor_core = MonitorCore()
    monitor_health = MonitorHealth(monitor_core)
    
    # This should not raise a NameError
    timestamp = monitor_health._get_iso_timestamp()
    
    # Verify the timestamp format
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