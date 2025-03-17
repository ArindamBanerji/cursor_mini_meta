#!/usr/bin/env python
"""
SnippetForTests.py
-----------------
A utility script to add or remove code snippets from test files.

Usage:
    python SnippetForTests.py -source "path/to/tests" -snippet "path/to/snippet.txt" -option "ADD"
    python SnippetForTests.py -source "path/to/tests" -option "REMOVE"
    python SnippetForTests.py -source "path/to/tests" -option "ADD" --check-only

This script will find all "test_*.py" files in the specified directory tree and
either add a code snippet to the beginning of each file or remove a previously added snippet.
The --check-only flag allows checking files without modifying them.
"""

import argparse
import os
import sys
import re
from pathlib import Path
import ast

# Marker comments to identify the snippet
SNIPPET_START_MARKER = "# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE"
SNIPPET_END_MARKER = "# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE"

def validate_path(path):
    """
    Validate that a path exists.
    
    Args:
        path: Path to validate
    
    Returns:
        Path object if valid
        
    Raises:
        ValueError: If path doesn't exist
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise ValueError(f"Path does not exist: {path}")
    return path_obj

def find_test_files(root_dir):
    """
    Find all test_*.py files in the directory tree.
    
    Args:
        root_dir: Root directory to search
        
    Returns:
        List of Path objects for test files
    """
    root_path = Path(root_dir)
    test_files = []
    
    for path in root_path.glob('**/test_*.py'):
        test_files.append(path)
    
    return test_files

def read_file_content(file_path):
    """
    Read content of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        File content as string
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file_content(file_path, content):
    """
    Write content to a file.
    
    Args:
        file_path: Path to file
        content: Content to write
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def is_valid_python(code):
    """
    Check if the code is valid Python syntax.
    
    Args:
        code: Python code to check
        
    Returns:
        True if valid, False otherwise
    """
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False

def extract_useful_code_from_py_file(file_path):
    """
    Extract useful code from a Python file, ignoring boilerplate.
    
    Args:
        file_path: Path to Python file
        
    Returns:
        Extracted code as string
    """
    content = read_file_content(file_path)
    
    # Skip any module docstring
    try:
        parsed = ast.parse(content)
        if parsed.body and isinstance(parsed.body[0], ast.Expr) and isinstance(parsed.body[0].value, ast.Str):
            docstring_lines = len(parsed.body[0].value.s.split('\n')) + 2  # +2 for quotes
            content_lines = content.split('\n')
            # Find where actual code starts after docstring
            for i in range(docstring_lines, len(content_lines)):
                if content_lines[i].strip() and not content_lines[i].strip().startswith('#'):
                    content = '\n'.join(content_lines[i:])
                    break
    except SyntaxError:
        # If we can't parse it, use it as-is
        pass
    
    # Remove any if __name__ == "__main__" block
    try:
        lines = content.split('\n')
        main_block_start = None
        for i, line in enumerate(lines):
            if re.match(r'^\s*if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:', line):
                main_block_start = i
                break
        
        if main_block_start is not None:
            content = '\n'.join(lines[:main_block_start])
    except Exception:
        # If something goes wrong, use it as-is
        pass
    
    return content.strip()

def prepare_snippet_content(snippet_path):
    """
    Prepare snippet content based on file type.
    
    Args:
        snippet_path: Path to snippet file
        
    Returns:
        Prepared snippet content as string
    """
    snippet_path = Path(snippet_path)
    
    if snippet_path.suffix.lower() == '.py':
        # For .py files, extract the useful code
        return extract_useful_code_from_py_file(snippet_path)
    else:
        # For other files, just read the content
        return read_file_content(snippet_path)

def add_snippet(file_path, snippet_content):
    """
    Add snippet to the beginning of a file.
    
    Args:
        file_path: Path to file
        snippet_content: Snippet to add
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Read current file content
        original_content = read_file_content(file_path)
        
        # Check if snippet is already present
        if SNIPPET_START_MARKER in original_content:
            return False, f"Snippet already present in {file_path}"
        
        # Prepare new content with snippet
        wrapped_snippet = f"{SNIPPET_START_MARKER}\n{snippet_content}\n{SNIPPET_END_MARKER}\n\n"
        new_content = wrapped_snippet + original_content
        
        # Validate the combined content is valid Python
        if not is_valid_python(new_content):
            return False, f"Adding snippet would create invalid Python syntax in {file_path}"
        
        # Write new content
        write_file_content(file_path, new_content)
        return True, f"Snippet added to {file_path}"
    
    except Exception as e:
        return False, f"Error adding snippet to {file_path}: {str(e)}"

def remove_snippet(file_path):
    """
    Remove snippet from a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Read current file content
        original_content = read_file_content(file_path)
        
        # Check if snippet is present
        if SNIPPET_START_MARKER not in original_content or SNIPPET_END_MARKER not in original_content:
            return False, f"No snippet found in {file_path}"
        
        # Extract content after the snippet
        pattern = re.compile(f"{re.escape(SNIPPET_START_MARKER)}.*?{re.escape(SNIPPET_END_MARKER)}\n+", re.DOTALL)
        new_content = pattern.sub('', original_content)
        
        # Validate the content is valid Python
        if not is_valid_python(new_content):
            return False, f"Removing snippet would create invalid Python syntax in {file_path}"
        
        # Write new content
        write_file_content(file_path, new_content)
        return True, f"Snippet removed from {file_path}"
    
    except Exception as e:
        return False, f"Error removing snippet from {file_path}: {str(e)}"

def process_files(test_files, snippet_path=None, add=True):
    """
    Process all test files to add or remove snippet.
    
    Args:
        test_files: List of test file paths
        snippet_path: Path to snippet file (required for add)
        add: True to add snippet, False to remove
        
    Returns:
        Tuple of (success_count, failure_count, log_messages)
    """
    success_count = 0
    failure_count = 0
    log_messages = []
    
    # Read snippet content if adding
    snippet_content = None
    if add and snippet_path:
        try:
            snippet_content = prepare_snippet_content(snippet_path)
        except Exception as e:
            return 0, len(test_files), [f"Error preparing snippet content: {str(e)}"]
    
    # Process each test file
    for file_path in test_files:
        if add:
            success, message = add_snippet(file_path, snippet_content)
        else:
            success, message = remove_snippet(file_path)
        
        log_messages.append(message)
        
        if success:
            success_count += 1
        else:
            failure_count += 1
    
    return success_count, failure_count, log_messages

def backup_file(file_path):
    """
    Create a backup of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Path to backup file
    """
    backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")
    file_path.rename(backup_path)
    return backup_path

def main():
    """Main function to execute the script."""
    parser = argparse.ArgumentParser(
        description='Add or remove code snippets from test files.'
    )
    parser.add_argument('-source', required=True, 
                        help='Source directory containing test files')
    parser.add_argument('-snippet', 
                        help='Path to snippet file to add (only required for ADD without --check-only)')
    parser.add_argument('-option', required=True, choices=['ADD', 'REMOVE'],
                        help='Operation to perform: ADD or REMOVE')
    parser.add_argument('--backup', action='store_true',
                        help='Create backups of modified files')
    parser.add_argument('--check-only', action='store_true',
                        help='Only check for impact without modifying files')
    
    args = parser.parse_args()
    
    # Validate inputs
    try:
        source_dir = validate_path(args.source)
        
        # Only require snippet file if actually adding (not in check-only mode)
        if args.option == 'ADD' and not args.snippet and not args.check_only:
            parser.error("Snippet file path (-snippet) is required for ADD operation without --check-only")
        
        if args.option == 'ADD' and args.snippet:
            snippet_path = validate_path(args.snippet)
    except ValueError as e:
        print(f"Error: {str(e)}")
        return 1
    
    # Find test files
    try:
        test_files = find_test_files(source_dir)
        if not test_files:
            print(f"No test files found in {source_dir}")
            return 0
        
        print(f"Found {len(test_files)} test files in {source_dir}")
    except Exception as e:
        print(f"Error finding test files: {str(e)}")
        return 1
    
    # Check-only mode
    if args.check_only:
        print("Check-only mode: No files will be modified")
        for file_path in test_files:
            content = read_file_content(file_path)
            has_snippet = SNIPPET_START_MARKER in content
            print(f"{file_path}: {'Has snippet' if has_snippet else 'No snippet'}")
        return 0
    
    # Create backups if requested
    if args.backup:
        print("Creating backups of files...")
        backup_files = []
        for file_path in test_files:
            # Create a backup with a new filename instead of renaming
            backup_path = Path(str(file_path) + ".bak")
            with open(file_path, 'r', encoding='utf-8') as src, open(backup_path, 'w', encoding='utf-8') as dest:
                dest.write(src.read())
            backup_files.append(backup_path)
            print(f"Backup created: {backup_path}")
    
    # Process files
    add_operation = args.option == 'ADD'
    snippet_path = args.snippet if add_operation else None
    
    success_count, failure_count, log_messages = process_files(
        test_files, snippet_path, add_operation
    )
    
    # Print results
    print(f"\nOperation: {args.option}")
    print(f"Files processed: {len(test_files)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")
    
    if failure_count > 0:
        print("\nDetails:")
        for msg in log_messages:
            if "Error" in msg or "invalid" in msg:
                print(f"  - {msg}")
    
    return 0 if failure_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
