#!/usr/bin/env python3
"""
Script to fix hardcoded paths in files to use SAP_HARNESS_HOME.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple
import sys

def find_hardcoded_paths(content: str) -> List[Tuple[str, str]]:
    """
    Find hardcoded paths in content and their replacements.
    
    Args:
        content: File content to search
        
    Returns:
        List of tuples (old_path, new_path)
    """
    # Patterns to match cursor project paths
    patterns = [
        r'C:\\Users\\baner\\CopyFolder\\IOT_thoughts\\python-projects\\kaggle_experiments\\cursor_projects\\mini_meta_harness',
        r'C:\\Users\\baner\\CopyFolder\\IoT_thoughts\\python-projects\\kaggle_experiments\\cursor_projects\\mini_meta_harness'
    ]
    
    # Get SAP_HARNESS_HOME from environment
    sap_harness_home = os.getenv('SAP_HARNESS_HOME')
    if not sap_harness_home:
        raise ValueError("SAP_HARNESS_HOME environment variable not set")
    
    # Normalize path separators
    sap_harness_home = sap_harness_home.replace('/', '\\')
    
    # Verify it points to cursor_projects path
    if 'cursor_projects' not in sap_harness_home.lower():
        raise ValueError(f"SAP_HARNESS_HOME should point to cursor_projects path, but got: {sap_harness_home}")
    
    replacements = []
    for pattern in patterns:
        for match in re.finditer(pattern, content):
            old_path = match.group(0)
            replacements.append((old_path, sap_harness_home))
    
    return replacements

def fix_file_paths(file_path: str) -> bool:
    """
    Fix hardcoded paths in a file.
    
    Args:
        file_path: Path to file to fix
        
    Returns:
        True if file was modified, False otherwise
    """
    print(f"Processing {file_path}")
    
    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find replacements
    replacements = find_hardcoded_paths(content)
    if not replacements:
        print("  No hardcoded paths found")
        return False
    
    # Apply replacements
    new_content = content
    for old_path, new_path in replacements:
        print(f"  Replacing {old_path} with {new_path}")
        new_content = new_content.replace(old_path, new_path)
    
    # Write updated content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("  File updated")
    return True

def main():
    """Main function."""
    try:
        # Get workspace root
        workspace_root = Path.cwd()
        
        # Files to check (md files and Python files)
        files_to_check = []
        for ext in ['.md', '.py']:
            files_to_check.extend(workspace_root.rglob(f'*{ext}'))
        
        # Process each file
        modified_files = []
        for file_path in files_to_check:
            if fix_file_paths(str(file_path)):
                modified_files.append(file_path)
        
        # Print summary
        print("\nSummary:")
        print(f"Processed {len(files_to_check)} files")
        print(f"Modified {len(modified_files)} files")
        if modified_files:
            print("\nModified files:")
            for file in modified_files:
                print(f"  {file}")
    except ValueError as e:
        print(f"\nError: {str(e)}")
        print("Please ensure SAP_HARNESS_HOME is set correctly using:")
        print("  . .\\SetProjEnv.ps1 -proj Cursor")
        sys.exit(1)

if __name__ == '__main__':
    main() 