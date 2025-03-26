#!/usr/bin/env python
"""
Script to fix indentation errors in API test files.
"""

import os
import re
import glob

def fix_logging_indentation(file_path):
    """Fix indentation errors in logging.basicConfig() calls."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Pattern to match incorrectly indented logging.basicConfig() calls
    pattern = r"logging\.basicConfig\(\)\s+level=logging\.INFO,\s+format='([^']+)'"
    replacement = r"logging.basicConfig(\n    level=logging.INFO,\n    format='\1'"
    
    # Fix indentation
    fixed_content = re.sub(pattern, replacement, content)
    
    # Add missing closing parenthesis if needed
    if "logging.basicConfig(" in fixed_content and not re.search(r"logging\.basicConfig\([^)]+\)", fixed_content):
        fixed_content = fixed_content.replace("format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'", 
                                             "format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'\n)")
    
    # Fix other common syntax errors
    # 1. Fix import statements with empty parentheses followed by items on new lines
    pattern = r"from\s+([a-zA-Z0-9_.]+)\s+import\s+\(\)\s+([a-zA-Z0-9_]+)"
    replacement = r"from \1 import (\n    \2"
    fixed_content = re.sub(pattern, replacement, fixed_content)
    
    # 2. Fix TEST_MATERIAL initialization
    pattern = r"TEST_MATERIAL\s+=\s+Material\(\)\s+([a-zA-Z0-9_]+)="
    replacement = r"TEST_MATERIAL = Material(\n    \1="
    fixed_content = re.sub(pattern, replacement, fixed_content)
    
    # 3. Fix unwrap_dependencies() calls
    pattern = r"wrapped\s+=\s+unwrap_dependencies\(\)\s+([a-zA-Z0-9_]+),"
    replacement = r"wrapped = unwrap_dependencies(\n        \1,"
    fixed_content = re.sub(pattern, replacement, fixed_content)
    
    # Write fixed content back to file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(fixed_content)
    
    return True

def main():
    """Fix indentation errors in all API test files."""
    api_test_files = glob.glob('api/test_*.py')
    fixed_count = 0
    
    for file_path in api_test_files:
        print(f"Processing {file_path}...")
        if fix_logging_indentation(file_path):
            print(f"Fixed indentation in {file_path}")
            fixed_count += 1
    
    print(f"Fixed indentation in {fixed_count} files")

if __name__ == "__main__":
    main() 