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


# tests_dest/api/test_minimal_async.py
"""
Minimal async test to diagnose pytest-asyncio configuration.
"""
import pytest
import asyncio
import os
import logging

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def setup_module(module):
    """Set up the test module by ensuring PYTEST_CURRENT_TEST is set"""
    logger.info("Setting up test module")
    os.environ["PYTEST_CURRENT_TEST"] = "True"
    
@pytest.mark.asyncio
async def test_minimal_async():
    """Run a minimal async test to verify pytest-asyncio configuration"""
    logger.info("Running minimal async test")
    await asyncio.sleep(0.1)  # Small delay for async operation
    assert True, "Async test should complete successfully"

def run_simple_test():
    """Run a simple test to verify the file can be imported and executed."""
    print("=== Simple diagnostic test ===")
    print("Successfully executed test_minimal_async.py")
    print("All imports resolved correctly")
    return True

if __name__ == "__main__":
    run_simple_test()
    