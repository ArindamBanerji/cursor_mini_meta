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
import traceback
import enum

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("p2p_imports_diagnostic")

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
                logger.debug(f"Added {path} to sys.path")
        
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
        
        # List of modules to try importing
        modules_to_test = [
            "services",
            "services.p2p_service",
            "services.p2p_service_helpers",
            "models",
            "models.p2p",
            "models.material"
        ]
        
        for module_name in modules_to_test:
            try:
                module = importlib.import_module(module_name)
                import_results[module_name] = {
                    "success": True,
                    "path": getattr(module, "__file__", "unknown")
                }
                logger.info(f"Successfully imported {module_name} from {import_results[module_name]['path']}")
            except Exception as e:
                import_results[module_name] = {
                    "success": False,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }
                logger.error(f"Failed to import {module_name}: {str(e)}")
        
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
        """Test direct import of P2P service classes."""
        try:
            # Try to import P2PService directly
            from services.p2p_service import P2PService, get_p2p_service
            
            # If successful, log the information
            logger.info(f"Successfully imported P2PService from services.p2p_service")
            logger.info(f"P2PService class: {P2PService}")
            logger.info(f"get_p2p_service function: {get_p2p_service}")
            
            # This test passes if no exception is raised
            self.assertTrue(True)
        except Exception as e:
            logger.error(f"Failed to import P2PService directly: {str(e)}")
            logger.error(traceback.format_exc())
            self.fail(f"Direct P2PService import failed: {str(e)}")
    
    def test_p2p_model_classes(self):
        """Test import of model classes used by P2P service."""
        try:
            # First import enum module to check class types
            import enum
            
            # Try to import model classes
            from models.p2p import (
                Requisition, RequisitionItem, Order, OrderItem,
                DocumentStatus, DocumentItemStatus
            )
            from models.material import MaterialStatus
            
            # If successful, log some info about each class
            logger.info(f"Successfully imported P2P model classes")
            logger.info(f"DocumentStatus values: {list(DocumentStatus)}")
            logger.info(f"MaterialStatus values: {list(MaterialStatus)}")
            
            # Check that these are actually Enum classes
            # Use isinstance with enum.EnumMeta to check if they are enum types
            self.assertTrue(isinstance(DocumentStatus, enum.EnumMeta),
                          "DocumentStatus should be an Enum class")
            self.assertTrue(isinstance(MaterialStatus, enum.EnumMeta),
                          "MaterialStatus should be an Enum class")
        except Exception as e:
            logger.error(f"Failed to import P2P model classes: {str(e)}")
            logger.error(traceback.format_exc())
            self.fail(f"P2P model classes import failed: {str(e)}")
    
    def test_alternative_import_patterns(self):
        """Test alternative patterns for importing P2P service."""
        results = {}
        
        # Pattern 1: Direct import
        try:
            import services.p2p_service
            results["direct_import"] = {
                "success": True,
                "path": services.p2p_service.__file__
            }
        except Exception as e:
            results["direct_import"] = {
                "success": False,
                "error": str(e)
            }
        
        # Pattern 2: Import service from package
        try:
            from services import p2p_service
            results["from_package"] = {
                "success": True,
                "path": p2p_service.__file__
            }
        except Exception as e:
            results["from_package"] = {
                "success": False,
                "error": str(e)
            }
        
        # Pattern 3: Import using importlib
        try:
            p2p_module = importlib.import_module("services.p2p_service")
            results["importlib"] = {
                "success": True,
                "path": p2p_module.__file__
            }
        except Exception as e:
            results["importlib"] = {
                "success": False,
                "error": str(e)
            }
        
        # Pattern 4: Import using exec
        try:
            namespace = {}
            exec("from services.p2p_service import P2PService", namespace)
            results["exec"] = {
                "success": True,
                "class": str(namespace.get("P2PService"))
            }
        except Exception as e:
            results["exec"] = {
                "success": False,
                "error": str(e)
            }
        
        # Log results
        for pattern, result in results.items():
            if result["success"]:
                logger.info(f"Pattern '{pattern}' succeeded: {result.get('path', result.get('class', 'unknown'))}")
            else:
                logger.error(f"Pattern '{pattern}' failed: {result['error']}")
        
        # Assert at least one pattern works
        successful_patterns = [p for p, r in results.items() if r["success"]]
        self.assertTrue(len(successful_patterns) > 0, 
                       f"All import patterns failed. See logs for details.")
        logger.info(f"Working import patterns: {', '.join(successful_patterns)}")

if __name__ == "__main__":
    unittest.main() 