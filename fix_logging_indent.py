#!/usr/bin/env python3
"""
Direct Indentation Fixer for logging.basicConfig blocks

This is a focused script that specifically fixes the indentation of logging.basicConfig 
blocks in all API test files.
"""

import os
import re
import sys
from pathlib import Path
import ast

def check_syntax(file_path):
    """Check if a file has valid Python syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True
    except SyntaxError as e:
        print(f"SyntaxError in {file_path}: {e}")
        return False
    except Exception as e:
        print(f"Error checking {file_path}: {e}")
        return False

def fix_indent_in_file(file_path):
    """Fix indentation in logging.basicConfig blocks."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for the logging.basicConfig block
    if 'logging.basicConfig(' not in content:
        print(f"No logging.basicConfig found in {file_path}")
        return False
    
    # Make backup
    backup_path = f"{file_path}.bak"
    if not os.path.exists(backup_path):
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Created backup at {backup_path}")
    
    # Fix approach 1: Fix with regular expressions
    # This pattern matches logging.basicConfig( followed by newline, some whitespace, and level=logging.INFO,
    pattern = r'logging\.basicConfig\(\n(\s+)level=logging\.INFO,'
    # Make sure the indentation is exactly 4 spaces
    replacement = r'logging.basicConfig(\n    level=logging.INFO,'
    modified_content = re.sub(pattern, replacement, content)
    
    # Fix approach 2: Line by line replacement if regex didn't work
    if modified_content == content:
        lines = content.split('\n')
        in_config_block = False
        for i, line in enumerate(lines):
            if 'logging.basicConfig(' in line:
                in_config_block = True
            elif in_config_block and 'level=' in line:
                # Fix the indentation - use exactly 4 spaces
                fixed_line = '    ' + line.lstrip()
                lines[i] = fixed_line
                in_config_block = False  # We've fixed the level line
        
        modified_content = '\n'.join(lines)
    
    # Only write if content actually changed
    if modified_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print(f"Fixed indentation in {file_path}")
        
        # Verify that the fix worked
        if check_syntax(file_path):
            print(f"✓ Syntax is now valid in {file_path}")
            return True
        else:
            print(f"✗ Syntax is still invalid in {file_path}")
            # Restore backup if fix didn't work
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Restored original content for {file_path}")
            return False
    else:
        print(f"No changes needed for {file_path}")
        return False

def fix_all_api_tests():
    """Fix indentation in all API test files."""
    api_dir = Path('tests_dest/api')
    if not api_dir.exists():
        print(f"Directory {api_dir} does not exist")
        return
    
    python_files = list(api_dir.glob('*.py'))
    print(f"Found {len(python_files)} Python files in {api_dir}")
    
    # First, check which files have syntax errors
    files_with_errors = []
    for file_path in python_files:
        if not check_syntax(file_path):
            files_with_errors.append(file_path)
    
    print(f"{len(files_with_errors)} files have syntax errors")
    
    # Now fix those files
    fixed_files = []
    for file_path in files_with_errors:
        if fix_indent_in_file(file_path):
            fixed_files.append(file_path)
    
    print(f"Fixed {len(fixed_files)} out of {len(files_with_errors)} files with errors")

if __name__ == "__main__":
    print("Starting direct indentation fix for API test files")
    fix_all_api_tests()
    print("Completed indentation fix process") 