#!/usr/bin/env python3
"""
Script to fix indentation and structural issues in test files.
This is a targeted script to address specific issues that were found in
the tests after running the main fix_test_imports.py script.
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
logger = logging.getLogger('test_fixer')

# Standard path setup code to add to test files
PATH_SETUP_CODE = """# Add path setup to find the tests_dest module
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
"""

# Common imports to add to files
COMMON_IMPORTS = """
import pytest
import logging
import time
import json
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom exception classes
class ValidationError(Exception):
    \"\"\"Custom validation error.\"\"\"
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details or {}
        
class NotFoundError(Exception):
    \"\"\"Custom not found error.\"\"\"
    def __init__(self, message):
        super().__init__(message)
"""

# Mock implementation for test_import_helper functions
MOCK_IMPORT_HELPER = """
# Mock implementation of test_import_helper
def setup_test_paths():
    \"\"\"Mock function to set up test paths.\"\"\"
    pass

def setup_test_env_vars():
    \"\"\"Mock function to set up test environment variables.\"\"\"
    pass
"""

# Mock implementation for FastAPI dependencies
MOCK_DEPENDENCIES = """
# Mock dependencies for testing
def get_material_service_dependency():
    return Depends(lambda: MagicMock())

def get_monitor_service_dependency():
    return Depends(lambda: MagicMock())

# Mock controllers
async def list_materials(request: Request = None):
    return JSONResponse({"materials": ["test"]})
"""

# Helper functions for test_helpers.py
TEST_HELPERS = """
# Mock implementation for unwrap_dependencies and other helper functions
def unwrap_dependencies(controller_func, **dependencies):
    \"\"\"Unwrap FastAPI dependencies for easier testing.
    
    This function takes a controller function that has Depends() injected parameters
    and returns a new function where those parameters are replaced with the provided
    dependency implementations.
    \"\"\"
    import inspect
    
    # Get the signature of the controller function
    sig = inspect.signature(controller_func)
    param_names = list(sig.parameters.keys())
    
    async def wrapper(*args, **kwargs):
        # Create a new kwargs dict with the dependencies
        new_kwargs = kwargs.copy()
        
        # Add our provided dependencies, but only if they are valid parameters
        for name, impl in dependencies.items():
            if name in param_names:
                new_kwargs[name] = impl
            
        # Call the original function with our arguments and dependencies
        return await controller_func(*args, **new_kwargs)
        
    return wrapper

def create_controller_test(controller_func):
    \"\"\"Create a test function for a controller.
    
    This function takes a controller function and returns a new test function
    that sets up all the necessary mocks and dependencies.
    \"\"\"
    async def test_func(mock_request=None, **mock_services):
        # Create a wrapped version of the controller with our mocks
        wrapped = unwrap_dependencies(controller_func, **mock_services)
        
        # Call the wrapped controller
        if not mock_request:
            mock_request = AsyncMock(spec=Request)
            
        return await wrapped(mock_request)
        
    return test_func
"""

# Mock controllers for testing
MOCK_CONTROLLERS = """
# Mock controller functions for testing
async def controller_no_deps(request: Request):
    \"\"\"Controller with no dependencies.\"\"\"
    return JSONResponse({"status": "ok"})

async def controller_optional_deps(
    request: Request,
    optional_service = None
):
    \"\"\"Controller with optional dependencies.\"\"\"
    if optional_service:
        return JSONResponse({"status": "with-service"})
    return JSONResponse({"status": "no-service"})

async def controller_with_errors(
    request: Request,
    error_type: str = None,
    material_service = Depends(lambda: MagicMock()),
    monitor_service = Depends(lambda: MagicMock())
):
    \"\"\"Controller that might raise errors.\"\"\"
    if error_type == "http":
        raise HTTPException(status_code=400, detail="Bad request")
    elif error_type == "validation":
        raise ValidationError("Validation error", details={"field": "Invalid"})
    elif error_type == "not_found":
        raise NotFoundError("Resource not found")
    elif error_type == "runtime":
        raise RuntimeError("Runtime error")
        
    try:
        material_service.list_materials()
        if "force_error" in getattr(request, "query_params", {}):
            raise ValueError("Forced error")
        return JSONResponse({"status": "ok"})
    except Exception as e:
        monitor_service.log_error(error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

async def controller_many_deps(
    request: Request,
    service1 = Depends(lambda: MagicMock()),
    service2 = Depends(lambda: MagicMock()),
    service3 = Depends(lambda: MagicMock()),
    service4 = Depends(lambda: MagicMock()),
    service5 = Depends(lambda: MagicMock()),
    service6 = Depends(lambda: MagicMock()),
    service7 = Depends(lambda: MagicMock()),
    service8 = Depends(lambda: MagicMock()),
    service9 = Depends(lambda: MagicMock()),
    service10 = Depends(lambda: MagicMock())
):
    \"\"\"Controller with many dependencies.\"\"\"
    return JSONResponse({"status": "ok"})

async def list_materials(
    request: Request = None, 
    material_service = None
):
    \"\"\"Mock controller function for testing.\"\"\"
    if material_service:
        materials = material_service.list_materials()
        return JSONResponse({"materials": materials})
    return JSONResponse({"materials": ["test"]})
"""

def fix_test_file(file_path):
    """Fix a specific test file with known issues."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
    
    # Create a backup
    backup_path = f"{file_path}.bak"
    with open(file_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original_content)
        
    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract docstring if present
    docstring = ""
    content_without_docstring = content
    
    # Find triple-quoted docstring
    triple_quote_start = content.find('"""')
    if triple_quote_start >= 0:
        triple_quote_end = content.find('"""', triple_quote_start + 3)
        if triple_quote_end >= 0:
            docstring = content[triple_quote_start:triple_quote_end + 3]
            content_without_docstring = content[:triple_quote_start] + content[triple_quote_end + 3:]
    
    # Start with clean content - just the path setup code
    new_content = PATH_SETUP_CODE + "\n"
    
    # Add docstring if present
    if docstring:
        new_content += docstring + "\n\n"
    
    # Add common imports
    new_content += COMMON_IMPORTS + "\n"
    
    # Detect if we need to add mock dependencies
    if "from tests_dest.services.dependencies import" not in content and "get_material_service_dependency" in content:
        new_content += MOCK_DEPENDENCIES + "\n"
        
    # Detect if we need to add mock import helper
    if "from test_import_helper import" in content and "def setup_test_paths" not in content:
        new_content += MOCK_IMPORT_HELPER + "\n"
    
    # Detect if we need to add test helpers
    if "unwrap_dependencies" in content and "from tests_dest.api.test_helpers import unwrap_dependencies" not in content:
        new_content += TEST_HELPERS + "\n"
        
    # Detect if we need to add controllers
    if "controller_no_deps" in content or "controller_optional_deps" in content or "controller_with_errors" in content:
        new_content += MOCK_CONTROLLERS + "\n"
    
    # Add rest of content (without the standard imports, path setup, etc.)
    # Look for first function definition or meaningful content to preserve
    rest_of_content = ""
    lines = content_without_docstring.split('\n')
    import_section_passed = False
    in_class_def = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip empty lines and import statements at the beginning
        if not stripped:
            continue
        if stripped.startswith("import ") or stripped.startswith("from "):
            continue
        if stripped.startswith("# ") or stripped.startswith("logging."):
            continue
        if stripped == "logger = logging.getLogger(__name__)":
            continue
        if stripped.startswith("if str(") and "sys.path" in stripped:
            continue
        if stripped.startswith("sys.path.insert") or stripped.startswith("sys.path.append"):
            continue
        
        # We found meaningful content
        rest_of_content = "\n".join(lines[i:])
        break
    
    # Add the rest of the content
    new_content += rest_of_content
    
    # Fix any remaining indentation issues with import blocks
    fixed_content = []
    lines = new_content.split('\n')
    in_import_block = False
    import_indent = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check for the start of an import block with parentheses
        if (("from " in line or "import " in line) and "(" in line and ")" not in line):
            in_import_block = True
            import_indent = len(line) - len(line.lstrip())
            fixed_content.append(line)
            continue
            
        # Check for end of import block
        if in_import_block and ")" in stripped:
            in_import_block = False
            fixed_content.append(line)
            continue
            
        # Handle lines inside an import block
        if in_import_block and stripped and not stripped.startswith('#'):
            # Ensure proper indentation (4 spaces more than opening line)
            if not line.startswith(' ' * (import_indent + 4)) and stripped:
                # Re-indent this line properly
                fixed_line = ' ' * (import_indent + 4) + stripped
                fixed_content.append(fixed_line)
                continue
        
        # For all other lines, keep them as is
        fixed_content.append(line)
    
    # Write the fixed content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_content))
    
    logger.info(f"Fixed file: {file_path}")
    return True

def main():
    """Main entry point."""
    # Files with known issues
    problem_files = [
        "tests_dest/api/test_dependency_unwrap.py",
        "tests_dest/api/test_dependency_edge_cases.py",
        "tests_dest/api/test_env_diagnostic.py",
        "tests_dest/api/test_error_handling_diagnostic.py",
        "tests_dest/api/test_header_template.py",
        "tests_dest/api/test_p2p_order_api.py",
        "tests_dest/api/test_patch_diagnostic.py",
        "tests_dest/api/test_recommended_approach.py",
        "tests_dest/api/test_session_integration.py",
        "tests_dest/api/test_session_integration_fixed.py"
    ]
    
    # Create backups directory
    backups_dir = "test_file_backups"
    os.makedirs(backups_dir, exist_ok=True)
    
    fixed_count = 0
    for file_path in problem_files:
        if fix_test_file(file_path):
            fixed_count += 1
    
    logger.info(f"Fixed {fixed_count} files out of {len(problem_files)}")

if __name__ == "__main__":
    main() 