#!/usr/bin/env python
"""
Diagnostic script to test import paths and module resolution
"""
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_paths():
    """Set up Python path to include required directories"""
    current_file = Path(__file__).resolve()
    current_dir = current_file.parent
    project_root = current_dir.parent
    
    logger.info(f"Current file path: {current_file}")
    logger.info(f"Current directory: {current_dir}")
    logger.info(f"Project root: {project_root}")
    
    # Add paths
    paths_to_add = [str(current_dir), str(project_root)]
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)
            logger.info(f"Added to sys.path: {path}")

def list_python_path():
    """Display the current Python path"""
    logger.info("Python sys.path:")
    for i, path in enumerate(sys.path):
        logger.info(f"  {i}: {path}")

def list_directory_contents(directory):
    """List files in the specified directory"""
    logger.info(f"Contents of directory: {directory}")
    try:
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isdir(item_path):
                logger.info(f"  DIR: {item}")
            else:
                logger.info(f"  FILE: {item}")
    except Exception as e:
        logger.error(f"Error listing directory {directory}: {e}")

def main():
    """Main diagnostic function"""
    logger.info("Starting import path diagnostic")
    
    # Set up paths
    setup_paths()
    
    # Display Python path
    list_python_path()
    
    # List contents of current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    list_directory_contents(current_dir)
    
    # Try importing some modules
    logger.info("Attempting imports:")
    
    try:
        import import_helper
        logger.info("✓ Successfully imported import_helper")
        # Check if fix_imports function exists
        if hasattr(import_helper, 'fix_imports'):
            logger.info("✓ import_helper.fix_imports function found")
            # Try calling the function
            try:
                import_helper.fix_imports()
                logger.info("✓ Successfully called import_helper.fix_imports()")
            except Exception as e:
                logger.error(f"× Error calling import_helper.fix_imports(): {e}")
        else:
            logger.error("× import_helper.fix_imports function not found")
    except ImportError as e:
        logger.error(f"× Failed to import import_helper: {e}")
    
    # Try importing other modules
    modules_to_test = [
        'services.base_service',
        'services.monitor_service',
        'models.base_model'
    ]
    
    for module_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=['*'])
            logger.info(f"✓ Successfully imported {module_name}")
        except ImportError as e:
            logger.warning(f"× Failed to import {module_name}: {e}")
    
    logger.info("Import diagnostic completed")

if __name__ == "__main__":
    main() 