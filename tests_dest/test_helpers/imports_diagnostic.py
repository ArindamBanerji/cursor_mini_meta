"""
Diagnostic test for service imports.

This file helps diagnose import issues by attempting to import services directly.
"""

import logging
import sys
from importlib import import_module
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    logger.info(f"Added {project_root} to Python path")

def test_import(module_name, symbols):
    """Test importing specific symbols from a module."""
    logger.info(f"Testing imports from {module_name}: {symbols}")
    
    try:
        module = import_module(module_name)
        logger.info(f"Successfully imported module {module_name}")
        
        for symbol in symbols:
            try:
                attr = getattr(module, symbol, None)
                if attr is not None:
                    logger.info(f"✓ Successfully imported {symbol} from {module_name}")
                else:
                    logger.error(f"✗ Symbol {symbol} exists in {module_name} but is None")
            except AttributeError:
                logger.error(f"✗ Failed to import {symbol} from {module_name}: Symbol not found")
    except ImportError as e:
        logger.error(f"✗ Failed to import module {module_name}: {e}")

def run_diagnostics():
    """Run diagnostics on all service factory imports."""
    logger.info("===== RUNNING IMPORT DIAGNOSTICS =====")
    
    # Test material service factory
    test_import("services.material_service", ["MaterialService", "get_material_service", "material_service"])
    
    # Test P2P service factory 
    test_import("services.p2p_service", ["P2PService", "get_p2p_service", "p2p_service"])
    
    # Test monitor service factory
    test_import("services.monitor_service", ["MonitorService", "get_monitor_service", "monitor_service"])
    
    # Test state manager factory
    test_import("services.state_manager", ["StateManager", "get_state_manager", "state_manager"])
    
    logger.info("===== DIAGNOSTICS COMPLETE =====")

if __name__ == "__main__":
    run_diagnostics() 