"""
Test file to validate our import fix works for integration tests.

This is a sample integration test that uses our import_helper to resolve
the import path issues.
"""

import os
import sys
import logging
import importlib
from pathlib import Path
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("integration_test_fix")

# Directly include the fix_imports code
def fix_imports():
    """Fix import path issues for test modules."""
    # Find project root (parent of tests-dest)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent
    
    # Find tests-dest directory
    test_dir = project_root / "tests-dest"
    if not test_dir.exists():
        # We might be in a different location
        test_dir = None
        for path in [project_root] + list(project_root.parents):
            if (path / "tests-dest").exists():
                test_dir = path / "tests-dest"
                project_root = path
                break
    
    # If we couldn't find tests-dest, use best guess
    if test_dir is None:
        logger.warning("Could not find tests-dest directory")
        test_dir = project_root / "tests-dest"
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Test directory: {test_dir}")
    
    # Clear any previously cached imports
    for module_name in list(sys.modules.keys()):
        if module_name.startswith(('services.', 'models.', 'utils.', 'controllers.')):
            sys.modules.pop(module_name, None)
    
    # Add project root to path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.info(f"Added project root to Python path: {project_root}")
    
    # Add test directory to path if not already there
    if str(test_dir) not in sys.path:
        sys.path.insert(1, str(test_dir))  # 1 = after project root
        logger.info(f"Added test directory to Python path: {test_dir}")
    
    # Add individual module directories directly to path
    for module_dir in ['services', 'utils', 'models', 'controllers']:
        module_path = project_root / module_dir
        if module_path.exists() and str(module_path) not in sys.path:
            sys.path.insert(0, str(module_path))
            logger.info(f"Added {module_dir} directory to Python path")
    
    # Set environment variables
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root))
    os.environ.setdefault("PROJECT_ROOT", str(project_root))
    os.environ.setdefault("TEST_MODE", "true")
    
    return project_root

# Run our import fix
project_root = fix_imports()

# Now we can import modules that would otherwise fail
import pytest
from fastapi.testclient import TestClient
from fastapi import status, APIRouter
from fastapi.responses import JSONResponse

def test_error_util_directly():
    """Test error_utils directly which should be synchronous."""
    try:
        # Import the error utils classes
        from utils.error_utils import create_error_response, NotFoundError, ValidationError
        
        # Create a NotFoundError
        error = NotFoundError(
            message="Resource not found",
            details={"resource_id": "TEST001", "resource_type": "Material"}
        )
        
        # Create a response using the error
        error_response = create_error_response(error)
        
        # Verify the response structure
        assert error_response.status_code == status.HTTP_404_NOT_FOUND
        body = error_response.body.decode("utf-8")
        import json
        data = json.loads(body)
        
        logger.info(f"Error response data: {data}")
        
        # Check that it has the right structure
        assert data["success"] == False
        assert "error_code" in data
        assert data["error_code"] == "not_found"
        assert "message" in data
        assert "details" in data
        
        # Test a validation error too
        validation_error = ValidationError(
            message="Invalid input data",
            details={"field": "quantity", "reason": "Must be positive"}
        )
        validation_response = create_error_response(validation_error)
        
        # Verify validation error response
        assert validation_response.status_code == status.HTTP_400_BAD_REQUEST
        validation_data = json.loads(validation_response.body.decode("utf-8"))
        assert validation_data["error_code"] == "validation_error"
        
        logger.info("✅ Error utils test passed")
        return True
    except ImportError as e:
        logger.error(f"❌ Error utils test failed due to import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error utils test failed with unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def verify_critical_imports():
    """Verify that critical modules can be imported and log results."""
    critical_modules = [
        "utils.error_utils",
        "services.state_manager",
        "services.monitor_service",
        "services.material_service",
        "models.material",
        "controllers.material_controller"
    ]
    
    success = True
    for module_name in critical_modules:
        try:
            module = importlib.import_module(module_name)
            logger.info(f"✓ Successfully imported {module_name}")
        except ImportError as e:
            logger.error(f"✗ Failed to import {module_name}: {e}")
            success = False
    
    return success

def main():
    """Run all tests."""
    logger.info("Starting import fix validation")
    
    # First verify all imports work
    logger.info("Verifying critical imports...")
    if not verify_critical_imports():
        logger.error("❌ Critical imports failed. Fix needed!")
        return 1
    
    # Test the error utils directly which should be synchronous
    if not test_error_util_directly():
        logger.error("❌ Error utils test failed")
        return 1
    
    logger.info("✅ All tests passed!")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 