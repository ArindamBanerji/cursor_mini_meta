#!/usr/bin/env python
"""
Script to fix indentation errors in a single API test file.
"""

import re

def fix_single_file(file_path):
    """Fix indentation errors in a single test file."""
    print(f"Processing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Make a backup of the original file
    with open(f"{file_path}.bak", 'w', encoding='utf-8') as backup:
        backup.write(content)
    
    # Fix the logging.basicConfig() indentation
    fixed_content = re.sub(
        r"logging\.basicConfig\(\)\s+level=logging\.INFO,",
        r"logging.basicConfig(\n    level=logging.INFO,", 
        content
    )
    
    # Fix the closing parenthesis
    fixed_content = re.sub(
        r"format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'(\s+)",
        r"format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'\n)\1", 
        fixed_content
    )
    
    # Write the fixed content back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(fixed_content)
    
    print(f"Fixed indentation in {file_path}")
    print(f"Backup saved to {file_path}.bak")
    
    return True

if __name__ == "__main__":
    # Fix a single file as a test
    target_file = "api/test_import_diagnostic.py"
    fix_single_file(target_file) 