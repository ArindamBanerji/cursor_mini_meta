#!/usr/bin/env python
"""
SnippetForTests.py
-----------------
A utility script to add or remove code snippets from test files.

Usage:
    python SnippetForTests.py -source "path/to/tests" -snippet "path/to/snippet.txt" -option "ADD" [--backup] [--check-only]
    python SnippetForTests.py -source "path/to/tests" -option "REMOVE" [--backup]
    python SnippetForTests.py -source "path/to/tests" -option "ADD" --check-only

This script will find all "test_*.py" files in the specified directory tree and
either add a code snippet to the beginning of each file or remove a previously added snippet.
The --check-only flag allows checking files without modifying them.
The --backup flag creates .bak files before making changes.

Parameters:
    -source: Directory containing test files (required)
    -snippet: Path to snippet file (required for ADD)
    -option: ADD or REMOVE (required)
    --backup: Create backup files before modifying
    --check-only: Only check files, don't modify them
"""

import argparse
import os
import sys
import re
import shutil
from pathlib import Path
import ast
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    try:
        path_obj = Path(path).resolve()
        if not path_obj.exists():
            raise ValueError(f"Path does not exist: {path}")
        return path_obj
    except Exception as e:
        raise ValueError(f"Invalid path {path}: {str(e)}")

def find_test_files(root_dir):
    """
    Find all test_*.py files in the directory tree.
    
    Args:
        root_dir: Root directory to search
        
    Returns:
        List of Path objects for test files
    """
    try:
        root_path = Path(root_dir)
        test_files = []
        
        for path in root_path.glob('**/test_*.py'):
            if path.is_file():
                test_files.append(path)
        
        if not test_files:
            logger.warning(f"No test files found in {root_dir}")
        else:
            logger.info(f"Found {len(test_files)} test files")
            
        return test_files
    except Exception as e:
        logger.error(f"Error finding test files: {e}")
        raise

def read_file_content(file_path):
    """
    Read content of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        File content as string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def write_file_content(file_path, content, create_backup=False):
    """
    Write content to a file.
    
    Args:
        file_path: Path to file
        content: Content to write
        create_backup: Whether to create a backup before writing
    """
    try:
        if create_backup:
            backup_path = str(file_path) + '.bak'
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup at {backup_path}")
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Error writing to file {file_path}: {e}")
        raise

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
    except SyntaxError as e:
        logger.error(f"Invalid Python syntax: {e}")
        return False
    except Exception as e:
        logger.error(f"Error checking Python syntax: {e}")
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
        logger.warning(f"Syntax error in {file_path}, using raw content")
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
    except Exception as e:
        logger.warning(f"Error removing __main__ block: {e}")
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

def add_snippet(file_path, snippet_content, create_backup=False):
    """
    Add snippet to the beginning of a file.
    
    Args:
        file_path: Path to file
        snippet_content: Snippet to add
        create_backup: Whether to create a backup before modifying
        
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
        write_file_content(file_path, new_content, create_backup)
        return True, f"Snippet added to {file_path}"
    
    except Exception as e:
        return False, f"Error adding snippet to {file_path}: {str(e)}"

def remove_snippet(file_path, create_backup=False):
    """
    Remove snippet from a file.
    
    Args:
        file_path: Path to file
        create_backup: Whether to create a backup before modifying
        
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
        write_file_content(file_path, new_content, create_backup)
        return True, f"Snippet removed from {file_path}"
    
    except Exception as e:
        return False, f"Error removing snippet from {file_path}: {str(e)}"

def process_files(test_files, snippet_path=None, add=True, create_backup=False, check_only=False):
    """
    Process all test files to add or remove snippet.
    
    Args:
        test_files: List of test file paths
        snippet_path: Path to snippet file (required for add)
        add: True to add snippet, False to remove
        create_backup: Whether to create backups before modifying files
        check_only: Only check files, don't modify them
        
    Returns:
        Tuple of (success_count, failure_count, log_messages)
    """
    success_count = 0
    failure_count = 0
    log_messages = []
    
    if add and not check_only:
        try:
            snippet_content = prepare_snippet_content(snippet_path)
            logger.info("Successfully prepared snippet content")
        except Exception as e:
            logger.error(f"Failed to prepare snippet content: {e}")
            return 0, len(test_files), [str(e)]
    
    for file_path in test_files:
        try:
            if check_only:
                # Just check if snippet is present
                content = read_file_content(file_path)
                has_snippet = SNIPPET_START_MARKER in content
                msg = f"Snippet {'present in' if has_snippet else 'missing from'} {file_path}"
                log_messages.append(msg)
                if (add and has_snippet) or (not add and not has_snippet):
                    success_count += 1
                else:
                    failure_count += 1
            else:
                # Actually modify the file
                if add:
                    success, msg = add_snippet(file_path, snippet_content, create_backup)
                else:
                    success, msg = remove_snippet(file_path, create_backup)
                
                log_messages.append(msg)
                if success:
                    success_count += 1
                else:
                    failure_count += 1
        
        except Exception as e:
            msg = f"Error processing {file_path}: {str(e)}"
            log_messages.append(msg)
            failure_count += 1
    
    return success_count, failure_count, log_messages

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-source', required=True, help='Directory containing test files')
    parser.add_argument('-snippet', help='Path to snippet file (required for ADD)')
    parser.add_argument('-option', required=True, choices=['ADD', 'REMOVE'], help='Operation to perform')
    parser.add_argument('--backup', action='store_true', help='Create backup files before modifying')
    parser.add_argument('--check-only', action='store_true', help='Only check files, do not modify them')
    
    args = parser.parse_args()
    
    try:
        # Validate source directory
        source_dir = validate_path(args.source)
        
        # Validate snippet file if adding
        if args.option == 'ADD' and not args.check_only:
            if not args.snippet:
                parser.error("Snippet file is required for ADD operation")
            snippet_path = validate_path(args.snippet)
        else:
            snippet_path = None
        
        # Find test files
        test_files = find_test_files(source_dir)
        if not test_files:
            logger.error("No test files found")
            return 1
        
        # Process files
        success_count, failure_count, messages = process_files(
            test_files,
            snippet_path,
            add=(args.option == 'ADD'),
            create_backup=args.backup,
            check_only=args.check_only
        )
        
        # Print results
        for msg in messages:
            logger.info(msg)
        
        logger.info(f"\nSummary:")
        logger.info(f"Successful operations: {success_count}")
        logger.info(f"Failed operations: {failure_count}")
        
        return 0 if failure_count == 0 else 1
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
