"""
Updates the API test files to use the simplified import helper.

This script finds all test files in the tests-dest/api directory and
replaces their complex import scaffolding with a simple import from
our simplified import_helper.py.
"""
import os
import re
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fix_api_tests")

# New import header to replace the complex scaffolding
NEW_IMPORT_HEADER = '''# Import helper to fix path issues
from tests-dest.import_helper import fix_imports
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

'''

def find_api_test_files():
    """Find all test files in the tests-dest/api directory."""
    test_dir = Path(__file__).parent / "tests-dest" / "api"
    if not test_dir.exists():
        logger.error(f"API test directory not found: {test_dir}")
        return []
    
    test_files = []
    for file in test_dir.glob("test_*.py"):
        test_files.append(file)
    
    return test_files

def update_test_file(file_path):
    """Update a test file to use the simplified import helper."""
    try:
        # Read the original file
        with open(file_path, "r") as f:
            content = f.read()
        
        # Check if file already has the simplified import
        if "from tests-dest.import_helper import fix_imports" in content:
            logger.info(f"File already has simplified import helper: {file_path}")
            return False
        
        # Define patterns to match
        begin_snippet_pattern = r"# BEGIN_SNIPPET_INSERTION.*?# END_SNIPPET_INSERTION.*?\n"
        sys_path_pattern = r"import sys\nimport os\nsys\.path\.insert.*?\n"
        
        # Check if the standard scaffold pattern exists
        if re.search(begin_snippet_pattern, content, re.DOTALL):
            # Replace the scaffolding with our simplified import
            new_content = re.sub(begin_snippet_pattern, NEW_IMPORT_HEADER, content, flags=re.DOTALL)
        elif re.search(sys_path_pattern, content):
            # Replace simpler sys.path pattern
            new_content = re.sub(sys_path_pattern, NEW_IMPORT_HEADER, content)
        else:
            # If no pattern is found, prepend the import helper
            new_content = NEW_IMPORT_HEADER + content
        
        # Write the updated content back to the file
        with open(file_path, "w") as f:
            f.write(new_content)
        
        logger.info(f"Updated file: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update {file_path}: {e}")
        return False

def main():
    """Main function to update all API test files."""
    # Find API test files
    api_test_files = find_api_test_files()
    if not api_test_files:
        logger.warning("No API test files found")
        return 1
    
    logger.info(f"Found {len(api_test_files)} API test files")
    
    # Update each file
    updated_count = 0
    for file_path in api_test_files:
        if update_test_file(file_path):
            updated_count += 1
    
    logger.info(f"Updated {updated_count} of {len(api_test_files)} files")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 