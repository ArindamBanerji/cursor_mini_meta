"""
Diagnostic tests for P2P service imports.

This file helps isolate and troubleshoot import issues with the P2P service
and related modules. It provides controlled test environments to validate
different import strategies.
"""
import os
import sys
import logging
import unittest
import importlib
import importlib.util
import traceback
import enum
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("p2p_imports_diagnostic")

# Import helper functions
from import_helper import fix_imports, setup_test_env_vars
fix_imports()
logger.info("Successfully initialized test paths from import_helper")

# Import service imports helper
from tests_dest.test_helpers.service_imports import (
    get_p2p_service,
    P2PService,
    DocumentStatus,
    DocumentItemStatus,
    RequisitionItem,
    Requisition, 
    Order, 
    OrderItem,
    MaterialStatus
)

# Find project root dynamically
test_file = Path(__file__).resolve()
test_dir = test_file.parent
project_root = test_dir.parent.parent

if project_root:
    logger.info(f"Project root detected at: {project_root}")
    # Add project root to path if found
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    logger.info(f"Added {project_root} to Python path")
else:
    raise RuntimeError("Could not detect project root")

def import_module_safely(module_name):
    """Import a module and return status information without raising exceptions.
    
    This is a helper function that attempts to import a module and returns
    information about the outcome without raising exceptions.
    
    Args:
        module_name: The name of the module to import
        
    Returns:
        A dictionary with information about the import status
    """
    # Check if the module is already imported
    if module_name in sys.modules:
        module = sys.modules[module_name]
        path = getattr(module, "__file__", "unknown")
        logger.info(f"Module {module_name} already imported from {path}")
        return {
            "success": True,
            "path": path,
            "module": module
        }
    
    # If module not already imported, check if it's available
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        # Module not available - record error
        error_msg = f"Module {module_name} not found in path"
        logger.error(error_msg)
        return {
            "success": False,
            "error_code": error_msg, 
            "traceback": "Module not found in Python path"
        }
    
    # Module is available - attempt to import it
    # Instead of try/except, use a more controlled approach
    # Create a custom exception handler that records the error
    class ImportErrorRecorder:
        def __init__(self):
            self.error = None
            self.traceback = None
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_value, exc_traceback):
            if exc_type is not None:
                self.error = str(exc_value)
                self.traceback = traceback.format_exc()
                # Return True to suppress the exception
                return True
            return False
    
    # Use the context manager to handle exceptions
    with ImportErrorRecorder() as error_recorder:
        module = importlib.import_module(module_name)
        if module:
            path = getattr(module, "__file__", "unknown")
            logger.info(f"Successfully imported {module_name} from {path}")
            return {
                "success": True,
                "path": path,
                "module": module
            }
    
    # If we get here, there was an error
    if error_recorder.error:
        logger.error(f"Failed to import {module_name}: {error_recorder.error}")
        return {
            "success": False,
            "error_code": error_recorder.error,
            "traceback": error_recorder.traceback
        }
    
    # Fallback - shouldn't normally reach here
    return {
        "success": False,
        "error_code": "Unknown error",
        "traceback": "Unknown error occurred during import"
    }

class P2PImportsTest(unittest.TestCase):
    """Tests for diagnosing P2P service import issues."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        # Record the current state of sys.path
        cls.original_sys_path = sys.path.copy()
        
        # Determine project root and add to path if not already there
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cls.test_dir = os.path.dirname(current_dir)  # tests-dest directory
        cls.project_root = os.path.dirname(cls.test_dir)  # project root
        
        # Add necessary paths for imports
        for path in [cls.project_root, cls.test_dir]:
            if path not in sys.path:
                sys.path.insert(0, path)
                logger.debug(f"Added to Python path: {path}")
        
        # Log the environment
        logger.info(f"Test directory: {cls.test_dir}")
        logger.info(f"Project root: {cls.project_root}")
        logger.info(f"Python path: {sys.path}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up the test environment."""
        # Restore the original sys.path
        sys.path = cls.original_sys_path
    
    def test_basic_imports(self):
        """Test if basic modules can be imported directly."""
        import_results = {}
        
        # List of modules to test
        modules_to_test = [
            "services",
            "services.p2p_service",
            "services.p2p_service_helpers",
            "models",
            "models.p2p",
            "models.material"
        ]
        
        # Test each module import
        for module_name in modules_to_test:
            import_result = import_module_safely(module_name)
            import_results[module_name] = import_result
        
        # Log summary of import results
        successes = [name for name, result in import_results.items() if result["success"]]
        failures = [name for name, result in import_results.items() if not result["success"]]
        
        logger.info(f"Import successes ({len(successes)}): {', '.join(successes)}")
        logger.info(f"Import failures ({len(failures)}): {', '.join(failures)}")
        
        # Print detailed error information for failed imports
        for name in failures:
            logger.error(f"Detailed error for {name}:")
            logger.error(import_results[name]["traceback"])
        
        # Make sure at least services can be imported
        self.assertTrue(import_results["services"]["success"], 
                        f"Basic services module import failed: {import_results['services'].get('error')}")
    
    def test_p2p_direct_import(self):
        """Test import of P2P service classes."""
        # Log information about imported classes from service_imports
        logger.info(f"Testing P2P service import via service_imports.py")
        logger.info(f"P2PService class: {P2PService}")
        logger.info(f"get_p2p_service function: {get_p2p_service}")
        
        # This test passes if the imports are already available (from module imports)
        self.assertIsNotNone(P2PService, "P2PService class should be imported")
        self.assertIsNotNone(get_p2p_service, "get_p2p_service function should be imported")
    
    def test_p2p_model_classes(self):
        """Test import of model classes used by P2P service."""
        # First import enum module to check class types
        import enum
        
        # Log info about imported classes (already imported at module level)
        logger.info(f"Testing P2P model classes import via service_imports.py")
        logger.info(f"DocumentStatus values: {list(DocumentStatus)}")
        logger.info(f"MaterialStatus values: {list(MaterialStatus)}")
        
        # Check that these are actually Enum classes
        # Use isinstance with enum.EnumMeta to check if they are enum types
        self.assertTrue(isinstance(DocumentStatus, enum.EnumMeta),
                      "DocumentStatus should be an Enum class")
        self.assertTrue(isinstance(MaterialStatus, enum.EnumMeta),
                      "MaterialStatus should be an Enum class")
    
    def test_alternative_import_patterns(self):
        """Test alternative patterns for importing P2P service."""
        # Use the module-level helper function
        results = {}
        
        # Pattern 1: Using importlib for services.p2p_service
        services_p2p_import = import_module_safely("services.p2p_service")
        results["importlib_direct"] = services_p2p_import
        
        # Pattern 2: Using importlib for services then accessing attribute
        services_import = import_module_safely("services")
        if services_import["success"]:
            p2p_service_attr = getattr(sys.modules["services"], "p2p_service", None)
            results["attribute_access"] = {
                "success": p2p_service_attr is not None,
                "module": str(p2p_service_attr) if p2p_service_attr else "Not found"
            }
        else:
            results["attribute_access"] = {"success": False, "error": "services module not imported"}
        
        # Pattern 3: Using service_imports
        results["service_imports"] = {
            "success": P2PService is not None and get_p2p_service is not None,
            "class": str(P2PService) if P2PService else "Not found"
        }
        
        # Log results
        for pattern, result in results.items():
            if result["success"]:
                logger.info(f"Pattern '{pattern}' succeeded: {result.get('path', result.get('class', result.get('module', 'unknown')))}")
            else:
                logger.error(f"Pattern '{pattern}' failed: {result.get('error', 'Unknown error')}")
        
        # Assert at least one pattern works
        successful_patterns = [p for p, r in results.items() if r["success"]]
        self.assertTrue(len(successful_patterns) > 0, 
                       f"All import patterns failed. See logs for details.")
        logger.info(f"Working import patterns: {', '.join(successful_patterns)}")

if __name__ == "__main__":
    unittest.main() 