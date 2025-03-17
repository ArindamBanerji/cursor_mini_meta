# genconftest_utils.py
"""
Utility module for GenConfTest script.

This module contains validation and file operations used by the GenConfTest script
to validate directories and write conftest.py files.
"""

from pathlib import Path
import os
import sys
import platform
import re

def validate_directory_path(source_dir):
    """
    Validate that the source directory exists and is a directory.
    
    Args:
        source_dir: Path to the test directory
    
    Returns:
        tuple: (source_path, is_valid, message)
    """
    # Convert to Path object for cross-platform compatibility
    source_path = Path(source_dir)
    
    # Validate source directory
    if not source_path.exists():
        return source_path, False, f"Source directory '{source_dir}' does not exist."
    
    if not source_path.is_dir():
        return source_path, False, f"Source path '{source_dir}' is not a directory."
    
    return source_path, True, "Directory path is valid."

def normalize_path(path_str):
    """
    Normalize a path for the current operating system.
    
    Args:
        path_str: Path string to normalize
    
    Returns:
        Normalized path string
    """
    if platform.system() == "Windows":
        return str(Path(path_str))
    return path_str

def create_directory_if_needed(target_dir):
    """
    Create a directory if it doesn't exist.
    
    Args:
        target_dir: Path to the directory to create
    
    Returns:
        tuple: (success, message)
    """
    target_path = Path(target_dir)
    
    if not target_path.exists():
        try:
            target_path.mkdir(parents=True)
            return True, f"Created directory: {target_path}"
        except Exception as e:
            return False, f"Error creating directory {target_path}: {e}"
    
    return True, f"Directory {target_path} already exists."

def write_conftest_file(target_dir, content):
    """
    Write content to a conftest.py file.
    
    Args:
        target_dir: Path to the directory where conftest.py will be created
        content: Content to write to the file
    
    Returns:
        tuple: (success, message)
    """
    conftest_path = Path(target_dir) / "conftest.py"
    
    try:
        with open(conftest_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return True, f"Created conftest.py in {target_dir}"
    except Exception as e:
        return False, f"Error writing conftest.py to {target_dir}: {e}"

def validate_conftest_content(conftest_path):
    """
    Validate that a conftest.py file has the expected content.
    
    Args:
        conftest_path: Path to the conftest.py file
    
    Returns:
        tuple: (is_valid, message)
    """
    try:
        with open(conftest_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Check if the file has content
        if not content:
            return False, "conftest.py is empty"
        
        # Check for basic pytest imports
        if "import pytest" not in content:
            return False, "conftest.py is missing pytest import"
        
        # Check for fixture definitions
        if "@pytest.fixture" not in content:
            return False, "conftest.py has no fixtures defined"
            
        # Determine if this is a root conftest file by its path
        # Root conftest is directly under the tests directory
        is_root = conftest_path.parent.name not in ["api", "integration", "models", "services", "monitoring", "unit"]
        has_plugins = "pytest_plugins" in content
        
        if is_root and not has_plugins:
            return False, "Root conftest.py is missing pytest_plugins definition"
        
        if not is_root and has_plugins:
            return False, "Non-root conftest.py should not define pytest_plugins"
        
        # Check for clear_sync error
        if "clear_sync()" in content:
            return False, "Using clear_sync() instead of clear()"
        
        return True, "conftest.py content is valid"
    
    except Exception as e:
        return False, f"Error validating conftest.py: {e}"

def generate_diagnostics(conftest_path):
    """
    Generate diagnostics for a conftest.py file.
    
    Args:
        conftest_path: Path to the conftest.py file
    
    Returns:
        Dictionary with diagnostics information
    """
    try:
        with open(conftest_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        lines = content.count('\n') + 1
        fixtures = content.count('@pytest.fixture')
        
        # Look for key imports
        has_pytest = "import pytest" in content
        has_state_manager = "state_manager" in content
        has_mock = "Mock" in content or "MagicMock" in content
        has_system_path = "sys.path.insert" in content
        has_asyncio = "async def" in content or "pytest.mark.asyncio" in content
        
        return {
            "path": str(conftest_path),
            "lines": lines,
            "fixtures": fixtures,
            "has_pytest": has_pytest,
            "has_state_manager": has_state_manager,
            "has_mock": has_mock,
            "has_system_path": has_system_path,
            "has_asyncio": has_asyncio
        }
    except Exception as e:
        return {
            "path": str(conftest_path),
            "error": str(e)
        }

def check_for_test_files(directory):
    """
    Check if directory contains test files.
    
    Args:
        directory: Directory path to check
    
    Returns:
        True if test files are found, False otherwise
    """
    directory_path = Path(directory)
    if not directory_path.exists() or not directory_path.is_dir():
        return False
    
    test_files = list(directory_path.glob("test_*.py"))
    return len(test_files) > 0

def verify_imports(conftest_path):
    """
    Verify that imports in conftest.py file will work.
    
    Args:
        conftest_path: Path to the conftest.py file
    
    Returns:
        tuple: (is_valid, issues)
    """
    try:
        with open(conftest_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        issues = []
        
        # Check for common import issues
        if "import service" in content and "from service import" not in content:
            if not Path(os.path.dirname(conftest_path) / "service").exists():
                issues.append("Import 'service' but directory doesn't exist")
        
        if "import models" in content and "from models import" not in content:
            if not Path(os.path.dirname(conftest_path) / "models").exists():
                issues.append("Import 'models' but directory doesn't exist")
        
        # Check relative imports
        if "from .." in content:
            issues.append("Contains relative imports (..) which may cause issues")
        
        # Check for clear_sync usage
        if "state_manager.clear_sync()" in content:
            issues.append("Using 'state_manager.clear_sync()' which doesn't exist, should be 'state_manager.clear()'")
            
        return len(issues) == 0, issues
    
    except Exception as e:
        return False, [f"Error verifying imports: {e}"]

def fix_common_issues(conftest_path):
    """
    Fix common issues in conftest.py files.
    
    Args:
        conftest_path: Path to the conftest.py file
    
    Returns:
        tuple: (fixed, changes)
    """
    try:
        with open(conftest_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        changes = []
        new_content = content
        
        # Fix clear_sync issue
        if "state_manager.clear_sync()" in new_content:
            new_content = new_content.replace("state_manager.clear_sync()", "state_manager.clear()")
            changes.append("Fixed 'clear_sync()' method call to 'clear()'")
        
        # Fix import paths
        if "from .conftest import" in new_content:
            new_content = new_content.replace("from .conftest import", "from conftest import")
            changes.append("Fixed relative import 'from .conftest'")
        
        # Fix relative imports
        relative_imports = re.findall(r"from \.\.([\w\.]+) import", new_content)
        for rel_import in relative_imports:
            new_content = new_content.replace(f"from ..{rel_import} import", f"from {rel_import} import")
            changes.append(f"Fixed relative import 'from ..{rel_import}'")
        
        # Save changes if any
        if changes:
            with open(conftest_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
                
        return len(changes) > 0, changes
            
    except Exception as e:
        return False, [f"Error fixing issues: {e}"]

def create_init_file(target_dir):
    """
    Create an __init__.py file in a directory if it doesn't exist.
    
    Args:
        target_dir: Path to the directory
    
    Returns:
        tuple: (success, message)
    """
    init_path = Path(target_dir) / "__init__.py"
    
    if not init_path.exists():
        try:
            # Create a simple __init__.py file
            with open(init_path, 'w', encoding='utf-8') as file:
                file.write(f"# {Path(target_dir).name} test package init\n")
            return True, f"Created {init_path}"
        except Exception as e:
            return False, f"Error creating {init_path}: {e}"
            
    return True, f"{init_path} already exists"