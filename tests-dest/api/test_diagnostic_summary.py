# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Critical imports that must be preserved
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, ModuleType

"""Standard test file imports and setup.

This snippet is automatically added to test files by SnippetForTests.py.
It provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration
3. Common test imports and fixtures
4. Service initialization support
5. Logging configuration
6. Test environment variable management
"""

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_project_root(test_dir: Path) -> Optional[Path]:
    """Find the project root directory.
    
    Args:
        test_dir: The directory containing the test file
        
    Returns:
        The project root directory or None if not found
    """
    try:
        # Try to find project root by looking for main.py or known directories
        for parent in [test_dir] + list(test_dir.parents):
            # Check for main.py as an indicator of project root
            if (parent / "main.py").exists():
                return parent
            # Check for typical project structure indicators
            if all((parent / d).exists() for d in ["services", "models", "controllers"]):
                return parent
        
        # If we still don't have a project root, use parent of the tests-dest directory
        for parent in test_dir.parents:
            if parent.name == "tests-dest":
                return parent.parent
                
        return None
    except Exception as e:
        logger.error(f"Error finding project root: {e}")
        return None

# Find project root dynamically
test_file = Path(__file__).resolve()
test_dir = test_file.parent
project_root = find_project_root(test_dir)

if project_root:
    logger.info(f"Project root detected at: {project_root}")
    
    # Add project root to path if found
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.info(f"Added {project_root} to Python path")
else:
    logger.warning("Could not detect project root")

# Import the test_import_helper
try:
    from test_import_helper import setup_test_paths
    setup_test_paths()
    logger.info("Successfully initialized test paths from test_import_helper")
except ImportError as e:
    # Fall back if test_import_helper is not available
    if str(test_dir.parent) not in sys.path:
        sys.path.insert(0, str(test_dir.parent))
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root) if project_root else "")
    logger.warning(f"Failed to import test_import_helper: {e}. Using fallback configuration.")

# Set up test environment variables
def setup_test_env() -> None:
    """Set up test environment variables."""
    try:
        os.environ.setdefault("PYTEST_CURRENT_TEST", "True")
        logger.info("Test environment variables initialized")
    except Exception as e:
        logger.error(f"Error setting up test environment: {e}")

def teardown_test_env() -> None:
    """Clean up test environment variables."""
    try:
        if "PYTEST_CURRENT_TEST" in os.environ:
            del os.environ["PYTEST_CURRENT_TEST"]
        logger.info("Test environment variables cleaned up")
    except KeyError:
        logger.warning("PYTEST_CURRENT_TEST was already removed")
    except Exception as e:
        logger.error(f"Error cleaning up test environment: {e}")

# Common test imports
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

# Import common fixtures and services
try:
    from conftest import test_services
    from services.base_service import BaseService
    from services.monitor_service import MonitorService
    from services.template_service import TemplateService
    from services.p2p_service import P2PService
    from models.base_model import BaseModel
    from models.material import Material
    from models.requisition import Requisition
    from fastapi import FastAPI, HTTPException
    logger.info("Successfully imported test fixtures and services")
except ImportError as e:
    # Log import error but continue - not all tests need all imports
    logger.warning(f"Optional import failed: {e}")
    logger.debug("Stack trace:", exc_info=True)

# Register setup/teardown hooks
def setup_module(module: ModuleType) -> None:
    """Set up the test module.
    
    Args:
        module: The test module being set up
    """
    logger.info("Setting up test module")
    setup_test_env()

def teardown_module(module: ModuleType) -> None:
    """Tear down the test module.
    
    Args:
        module: The test module being torn down
    """
    logger.info("Tearing down test module")
    teardown_test_env()
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

"""
Diagnostic Summary for Testing FastAPI Controllers with Dependency Injection

This file summarizes the diagnostic approach, findings, and recommendations
for testing FastAPI controllers that use dependency injection.

Key Findings:
1. FastAPI's Depends objects are created at import time, not at runtime
2. Traditional patching approaches don't work with Depends objects
3. A wrapper function is needed to replace Depends objects with mock services
4. The unwrap_dependencies function provides a clean solution
5. The create_controller_test function simplifies test creation

Recommendations:
1. Use unwrap_dependencies for testing controllers with dependencies
2. Create fixtures for common mock objects
3. Test error handling and edge cases
4. Document the approach for future developers
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import inspect
from fastapi import Depends
from controllers.material_common import get_material_service, get_monitor_service
from controllers.material_ui_controller import list_materials

def print_diagnostic_summary():
    """Print a summary of the diagnostic findings and recommendations."""
    print("\n=== Diagnostic Summary for Testing FastAPI Controllers ===\n")
    
    print("Problem Statement:")
    print("  FastAPI controllers use dependency injection via Depends objects")
    print("  Traditional patching approaches don't work with Depends objects")
    print("  This makes testing controllers with dependencies challenging")
    
    print("\nRoot Cause:")
    print("  Depends objects are created at import time, not at runtime")
    print("  Patching service getter functions doesn't affect already-created Depends objects")
    print("  Controller functions still receive the original Depends objects as default parameter values")
    
    print("\nSolution:")
    print("  Create a wrapper function that replaces Depends objects with mock services at call time")
    print("  The unwrap_dependencies function inspects the controller function's signature")
    print("  It identifies parameters with Depends objects as default values")
    print("  It creates a new function that replaces these with mock objects")
    
    print("\nRecommendations:")
    print("  1. Use unwrap_dependencies for testing controllers with dependencies")
    print("  2. Create fixtures for common mock objects")
    print("  3. Test error handling and edge cases")
    print("  4. Document the approach for future developers")
    
    print("\nExample Usage:")
    print("  # Create wrapped controller with mocks")
    print("  wrapped = unwrap_dependencies(")
    print("      list_materials,")
    print("      material_service=mock_material_service,")
    print("      monitor_service=mock_monitor_service")
    print("  )")
    print("  # Call the function")
    print("  result = await wrapped(mock_request)")
    
    print("\nAlternative Approach:")
    print("  # Create test function with create_controller_test")
    print("  test_func = create_controller_test(list_materials)")
    print("  # Call the test function")
    print("  result = await test_func(")
    print("      mock_request=mock_request,")
    print("      mock_material_service=mock_material_service,")
    print("      mock_monitor_service=mock_monitor_service")
    print("  )")
    
    print("\nDiagnostic Tests Created:")
    print("  1. test_dashboard_diagnostic.py - Simple controllers without dependencies")
    print("  2. test_error_handling_diagnostic.py - Controllers that raise errors")
    print("  3. test_monitor_diagnostic.py - Controllers with service dependencies")
    print("  4. test_dependency_diagnostic.py - Different approaches to mocking dependencies")
    print("  5. test_dependency_unwrap.py - Testing the unwrap_dependencies function")
    print("  6. test_dependency_edge_cases.py - Edge cases for dependency unwrapping")
    print("  7. test_controller_diagnostic.py - Comparing different testing approaches")
    print("  8. test_recommended_approach.py - Demonstrating the recommended approach")
    
    print("\n=== End of Diagnostic Summary ===\n")

def inspect_controller_parameters():
    """Inspect the parameters of a controller function to demonstrate the issue."""
    print("\n--- Inspecting Controller Parameters ---\n")
    
    # Get the signature of the controller function
    sig = inspect.signature(list_materials)
    
    # Print information about each parameter
    for name, param in sig.parameters.items():
        print(f"Parameter: {name}")
        print(f"  Default: {param.default}")
        print(f"  Annotation: {param.annotation}")
        
        # Check if it's a Depends parameter
        if param.default is not inspect.Parameter.empty and hasattr(param.default, "dependency"):
            print(f"  Is Depends: True")
            print(f"  Dependency: {param.default.dependency}")
            
            # Demonstrate why patching doesn't work
            if param.default.dependency == get_material_service:
                print("\n  Demonstration of why patching doesn't work:")
                print("  1. The Depends object is created at import time")
                print("  2. It contains a reference to the original get_material_service function")
                print("  3. Patching get_material_service later doesn't affect this reference")
                print("  4. The controller still calls the original function via the Depends object")
        else:
            print(f"  Is Depends: False")
        
        print()

def demonstrate_solution():
    """Demonstrate the solution to the dependency injection testing problem."""
    print("\n--- Demonstrating the Solution ---\n")
    
    print("The solution is to create a wrapper function that:")
    print("1. Inspects the controller function's signature")
    print("2. Identifies parameters with Depends objects as default values")
    print("3. Creates a new function that replaces these with mock objects")
    print("4. Calls the original function with the new parameters")
    
    print("\nThis is implemented in the unwrap_dependencies function:")
    print("""
def unwrap_dependencies(func, **mocks):
    \"\"\"
    Create a wrapper function that replaces Depends objects with mock objects.
    
    Args:
        func: The controller function to wrap
        **mocks: Mapping of parameter names to mock objects
        
    Returns:
        A wrapper function that calls the original function with mocks
    \"\"\"
    # Get the signature of the function
    sig = inspect.signature(func)
    
    # Create a wrapper function
    async def wrapper(*args, **kwargs):
        # Create a new kwargs dict with mocks for Depends parameters
        new_kwargs = {}
        
        # Process positional arguments
        parameters = list(sig.parameters.items())
        for i, arg in enumerate(args):
            if i < len(parameters):
                param_name, _ = parameters[i]
                new_kwargs[param_name] = arg
        
        # Process keyword arguments
        for param_name, param in sig.parameters.items():
            # Skip parameters already set by positional args
            if param_name in new_kwargs:
                continue
                
            # If the parameter has a Depends default and we have a mock for it
            if (param.default is not inspect.Parameter.empty and 
                hasattr(param.default, "dependency") and
                param_name in mocks):
                new_kwargs[param_name] = mocks[param_name]
            # Otherwise use the provided kwarg or default
            elif param_name in kwargs:
                new_kwargs[param_name] = kwargs[param_name]
        
        # Call the original function with the new kwargs
        return await func(**new_kwargs)
    
    return wrapper
""")
    
    print("\nThis solution allows us to test controllers with dependencies")
    print("without modifying the original controller code.")

if __name__ == "__main__":
    print_diagnostic_summary()
    inspect_controller_parameters()
    demonstrate_solution() 
def setup_module(module):
    """Set up the test module by ensuring PYTEST_CURRENT_TEST is set"""
    logger.info("Setting up test module")
    os.environ["PYTEST_CURRENT_TEST"] = "True"
    
def teardown_module(module):
    """Clean up after the test module"""
    logger.info("Tearing down test module")
    if "PYTEST_CURRENT_TEST" in os.environ:
        del os.environ["PYTEST_CURRENT_TEST"]
