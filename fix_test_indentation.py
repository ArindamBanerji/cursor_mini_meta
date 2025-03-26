#!/usr/bin/env python
"""
Script to fix indentation errors in test files.

This script scans all test files in a directory for a specific pattern of indentation errors
and fixes them by adding a missing try statement and properly indenting code blocks.
"""

import os
import re
import sys
from pathlib import Path

# The pattern to look for - a line that starts indented (unexpected indent)
INDENTED_LINE_PATTERN = re.compile(r'^(\s+)if str\(project_root\) not in sys\.path:', re.MULTILINE)

# The pattern to find where the try statement should be inserted
TRY_INSERT_PATTERN = re.compile(r'5\. Logging configuration\n"""\n', re.MULTILINE)

# The directories to scan for test files
TEST_DIRECTORIES = [
    'tests_dest/integration',
    'tests_dest/unit',
    'tests_dest/diagnostic',
    'tests_dest/monitoring',
    'tests_dest/models_tests',
    'tests_dest/services_tests',
]

def fix_indentation_in_file(file_path):
    """
    Fix indentation issues in the specified file.
    
    Args:
        file_path: Path to the file to fix
        
    Returns:
        True if the file was fixed, False otherwise
    """
    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for the common indentation problem with the "if str(project_root)" line
        indent_match = INDENTED_LINE_PATTERN.search(content)
        if not indent_match:
            print(f"No indentation issue found in {file_path}")
            return False
        
        # Find where to insert the try statement
        try_match = TRY_INSERT_PATTERN.search(content)
        if not try_match:
            print(f"Could not find insertion point for try statement in {file_path}")
            return False
        
        # Split content at the insertion point
        before_insertion = content[:try_match.end()]
        after_insertion = content[try_match.end():]
        
        # Add the try statement
        fixed_content = before_insertion + "try:\n" + after_insertion
        
        # If no changes were made, return False
        if fixed_content == content:
            print(f"No changes needed for {file_path}")
            return False
            
        # Write the fixed content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"Fixed indentation in {file_path} by adding missing try statement")
        return True
    
    except Exception as e:
        print(f"Error fixing indentation in {file_path}: {e}")
        return False

def scan_directory(directory):
    """
    Scan a directory for Python test files and fix indentation issues.
    
    Args:
        directory: Directory to scan
        
    Returns:
        Tuple of (files_scanned, files_fixed)
    """
    directory_path = Path(directory)
    if not directory_path.exists():
        print(f"Directory {directory} does not exist")
        return 0, 0
    
    files_scanned = 0
    files_fixed = 0
    
    # Find all Python files in the directory
    for file_path in directory_path.glob('test_*.py'):
        files_scanned += 1
        if fix_indentation_in_file(file_path):
            files_fixed += 1
    
    return files_scanned, files_fixed

def main():
    """Main function to execute the script."""
    total_scanned = 0
    total_fixed = 0
    
    for directory in TEST_DIRECTORIES:
        print(f"\nScanning directory: {directory}")
        scanned, fixed = scan_directory(directory)
        total_scanned += scanned
        total_fixed += fixed
        print(f"Files scanned: {scanned}, Files fixed: {fixed}")
    
    print(f"\nSummary: Scanned {total_scanned} files, Fixed {total_fixed} files")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 