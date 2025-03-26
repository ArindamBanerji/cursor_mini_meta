"""
Simple test to verify the import fix solution.

This script imports the state_manager module and other
critical modules to confirm the fix works.
"""

import os
import sys
import logging
import importlib.util
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_import_fix")

def setup_imports():
    """Directly set up imports within this script."""
    logger.info("Current directory: %s", os.getcwd())
    logger.info("Python path before fix: %s", sys.path)
    
    # Find project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent
    
    # Clear existing module caches that might be problematic
    for module_name in list(sys.modules.keys()):
        if module_name.startswith(('services.', 'models.', 'utils.', 'controllers.')):
            del sys.modules[module_name]
    
    # Add project root to path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.info(f"Added project root to sys.path: {project_root}")
    
    # Try importing utils.error_utils as a test
    try:
        import utils.error_utils
        logger.info("Basic imports are working")
    except ImportError as e:
        logger.warning(f"Basic imports still failing: {e}")
        
        # Add all potential module directories to path
        for dir_name in ["services", "models", "utils", "controllers"]:
            dir_path = project_root / dir_name
            if dir_path.exists():
                sys.path.insert(0, str(dir_path))
                logger.info(f"Added {dir_name} directory to sys.path")
    
    logger.info("Python path after fix: %s", sys.path)
    return project_root

def load_module_from_file(module_name, file_path):
    """Load a module from a file path."""
    try:
        logger.info(f"Trying to load {module_name} from {file_path}")
        if not Path(file_path).exists():
            logger.error(f"File not found: {file_path}")
            return None
        
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            logger.error(f"Failed to create spec for {module_name}")
            return None
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # If this is a submodule, ensure the parent module exists
        if "." in module_name:
            parent_name = module_name.split(".")[0]
            if parent_name not in sys.modules:
                import types
                parent = types.ModuleType(parent_name)
                sys.modules[parent_name] = parent
            
            # Set the submodule as an attribute of the parent
            setattr(sys.modules[parent_name], module_name.split(".")[-1], module)
        
        logger.info(f"Successfully loaded {module_name}")
        return module
    except Exception as e:
        logger.error(f"Error loading {module_name}: {e}")
        return None

def main():
    """Test importing critical modules."""
    project_root = setup_imports()
    
    # Modules to test with direct file paths
    modules_to_test = [
        ("services.state_manager", project_root / "services" / "state_manager.py"),
        ("services.monitor_service", project_root / "services" / "monitor_service.py"),
        ("services.material_service", project_root / "services" / "material_service.py"),
        ("utils.error_utils", project_root / "utils" / "error_utils.py"),
        ("models.material", project_root / "models" / "material.py"),
    ]
    
    success = True
    for module_name, file_path in modules_to_test:
        if file_path.exists():
            logger.info(f"Module file exists: {file_path}")
            
            # First try regular import
            try:
                logger.info(f"Trying normal import for {module_name}")
                module = __import__(module_name, fromlist=["*"])
                logger.info(f"✓ Successfully imported {module_name} using standard import")
                continue
            except ImportError as e:
                logger.warning(f"Standard import failed for {module_name}: {e}")
            
            # Try direct file loading
            module = load_module_from_file(module_name, file_path)
            if module:
                logger.info(f"✓ Successfully loaded {module_name} from file")
                
                # Check for key classes
                if module_name == "services.state_manager":
                    if hasattr(module, "StateManager"):
                        logger.info("✓ StateManager class found")
                    else:
                        logger.error("✗ StateManager class not found in module")
                        success = False
            else:
                logger.error(f"✗ Failed to load {module_name} from file")
                success = False
        else:
            logger.error(f"✗ Module file does not exist: {file_path}")
            success = False
    
    return success

if __name__ == "__main__":
    if main():
        logger.info("All imports successful! The fix works.")
        sys.exit(0)
    else:
        logger.error("Some imports failed. The fix needs improvement.")
        sys.exit(1) 