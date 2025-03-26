#!/usr/bin/env python3
"""
Systematic Indentation Fixer for API Test Files

This script:
1. Identifies all Python files in the tests_dest/api directory
2. Finds and fixes common indentation errors
3. Verifies code correctness after each fix
4. Logs all changes and errors
"""

import os
import re
import sys
import logging
import subprocess
from pathlib import Path
import ast
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("indentation_fix.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("fix_indentation")

def check_syntax(file_content):
    """
    Check if the Python file has valid syntax.
    
    Args:
        file_content (str): Content of the Python file
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        ast.parse(file_content)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}, column {e.offset}: {e.msg}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def fix_logging_indentation(content):
    """
    Fix common indentation issues in logging configuration.
    
    Args:
        content (str): File content
        
    Returns:
        str: Fixed content
    """
    # Find and fix indentation in logging.basicConfig blocks
    pattern = r'(logging\.basicConfig\(\n)(\s+)(level=logging\.INFO,)'
    fixed_content = re.sub(pattern, r'\1\2\3', content)
    
    # Fix indentation of parameters in logging.basicConfig
    lines = fixed_content.split('\n')
    in_basicconfig = False
    fixed_lines = []
    
    for i, line in enumerate(lines):
        if 'logging.basicConfig(' in line:
            in_basicconfig = True
            fixed_lines.append(line)
        elif in_basicconfig and ')' in line and not re.search(r'^\s+\w', line):
            # End of basicConfig block
            in_basicconfig = False
            fixed_lines.append(line)
        elif in_basicconfig and re.search(r'^\s+\w+=', line):
            # This is a parameter line, ensure correct indentation
            # Extract the current indentation
            if i > 0 and 'logging.basicConfig(' in lines[i-1]:
                leading_whitespace = re.match(r'^(\s+)', line)
                if leading_whitespace:
                    current_indent = len(leading_whitespace.group(1))
                    # If the indentation looks wrong, fix it
                    if current_indent % 4 != 0 or current_indent < 4:
                        # Adjust to 4 spaces (standard indentation)
                        adjusted_line = ' ' * 4 + line.lstrip()
                        fixed_lines.append(adjusted_line)
                        continue
            fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def fix_file_indentation(file_path):
    """
    Fix indentation issues in a single file.
    
    Args:
        file_path (Path): Path to the file
        
    Returns:
        bool: True if file was fixed, False otherwise
    """
    logger.info(f"Processing {file_path}")
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check syntax before fixing
        is_valid, error_msg = check_syntax(content)
        if is_valid:
            logger.info(f"✓ {file_path} already has valid syntax")
            return False
        else:
            logger.warning(f"✗ {file_path} has syntax error: {error_msg}")
        
        # Create a backup
        backup_path = f"{file_path}.bak"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Created backup at {backup_path}")
        
        # Fix indentation issues
        fixed_content = fix_logging_indentation(content)
        
        # Verify the fixed content has valid syntax
        is_valid, error_msg = check_syntax(fixed_content)
        if not is_valid:
            logger.error(f"✗ Fixed content still has syntax error: {error_msg}")
            return False
        
        # Write the fixed content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        logger.info(f"✓ Fixed indentation in {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error processing {file_path}: {str(e)}")
        return False

def verify_importability(file_path):
    """
    Verify that the fixed file can be imported without errors.
    
    Args:
        file_path (Path): Path to the file
        
    Returns:
        bool: True if file can be imported, False otherwise
    """
    try:
        # Create a temporary file that imports the module
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
            module_path = os.path.relpath(file_path, Path.cwd())
            module_name = module_path.replace('/', '.').replace('\\', '.').replace('.py', '')
            temp.write(f"import {module_name}\n".encode('utf-8'))
            temp_name = temp.name
        
        # Try to import the module
        result = subprocess.run(
            [sys.executable, temp_name],
            capture_output=True,
            text=True
        )
        
        # Cleanup the temporary file
        os.unlink(temp_name)
        
        if result.returncode == 0:
            logger.info(f"✓ {file_path} can be imported successfully")
            return True
        else:
            logger.error(f"✗ {file_path} cannot be imported: {result.stderr.strip()}")
            return False
    
    except Exception as e:
        logger.error(f"Error verifying importability of {file_path}: {str(e)}")
        return False

def fix_all_api_tests():
    """
    Fix indentation in all API test files.
    """
    # Find all Python files in the tests_dest/api directory
    api_dir = Path('tests_dest/api')
    if not api_dir.exists():
        logger.error(f"Directory {api_dir} does not exist")
        return
    
    python_files = list(api_dir.glob('*.py'))
    logger.info(f"Found {len(python_files)} Python files in {api_dir}")
    
    # Process each file
    fixed_files = []
    for file_path in python_files:
        if fix_file_indentation(file_path):
            fixed_files.append(file_path)
    
    # Summary
    logger.info(f"Fixed indentation in {len(fixed_files)} out of {len(python_files)} files")
    logger.info("Fixed files:")
    for file_path in fixed_files:
        logger.info(f"  - {file_path}")

def run_tests(test_file=None):
    """
    Run pytest on the specified test file or all API tests.
    
    Args:
        test_file (Path, optional): Path to specific test file
        
    Returns:
        bool: True if tests pass, False otherwise
    """
    try:
        cmd = [sys.executable, '-m', 'pytest']
        if test_file:
            cmd.append(str(test_file))
        else:
            cmd.append('tests_dest/api/')
        
        logger.info(f"Running tests: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✓ Tests passed")
            return True
        else:
            logger.error(f"✗ Tests failed: {result.stderr.strip()}")
            logger.info(f"Test output: {result.stdout.strip()}")
            return False
    
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting systematic indentation fix for API test files")
    fix_all_api_tests()
    logger.info("Running tests to verify fixes")
    run_tests()
    logger.info("Completed indentation fix process") 