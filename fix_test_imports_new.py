#!/usr/bin/env python
"""
Script to fix imports in test files.

This script scans API test files and fixes imports by:
1. Adding proper path setup
2. Replacing problematic imports with correct ones
3. Ensuring import statements use valid Python syntax
"""
import os
import re
import sys
import glob
import logging
import shutil
import datetime
from pathlib import Path
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import header to add at the beginning of files
# Uses proper Python import syntax (with underscores not hyphens)
IMPORT_HEADER = '''# Import helper to fix path issues
import sys
import os
from pathlib import Path

# Add parent directory to path
current_file = Path(__file__).resolve()
tests_dest_dir = current_file.parent.parent
project_root = tests_dest_dir.parent
if str(tests_dest_dir) not in sys.path:
    sys.path.insert(0, str(tests_dest_dir))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now we can import the helper
from import_helper import fix_imports
fix_imports()
'''

# Patterns to detect existing import approaches
IMPORT_PATTERNS = [
    # Pattern for the broken import (with hyphen)
    re.compile(r'from\s+tests\-dest\.import_helper\s+import\s+fix_imports'),
    # Pattern for import with path manipulation
    re.compile(r'sys\.path\.insert\(.*?os\.path\.join\(.*?\).*?\)'),
    # Pattern for simple import_helper import
    re.compile(r'from\s+import_helper\s+import\s+fix_imports'),
    # Pattern for any import_helper mention
    re.compile(r'import\s+import_helper'),
]

def find_test_files(directory):
    """Find Python test files in the specified directory."""
    logger.info(f"Searching for test files in: {directory}")
    test_files = []
    
    # Find all Python files that start with test_
    for pattern in ['test_*.py']:
        file_pattern = os.path.join(directory, pattern)
        matching_files = glob.glob(file_pattern)
        test_files.extend(matching_files)
    
    logger.info(f"Found {len(test_files)} test files")
    return test_files

def should_update_file(content):
    """Check if the file needs updating based on its content."""
    # Check for broken import pattern
    if any(pattern.search(content) for pattern in IMPORT_PATTERNS):
        return True
    
    # Check if our import header is already present
    if IMPORT_HEADER.strip() in content:
        return False
    
    # If no clear pattern is found, check for fix_imports usage
    if 'fix_imports()' in content:
        # Check if it's already properly set up
        path_setup = "tests_dest_dir = current_file.parent.parent" in content
        if path_setup:
            return False
        return True
    
    # Default to updating if we see it's a test file that might need imports
    return 'import pytest' in content

def backup_file(file_path):
    """Create a backup of the file before modifying it."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.bak_{timestamp}"
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup for {file_path}: {e}")
        return False

def update_file(file_path, preview_mode=False):
    """Update the file with the correct import header."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return False
    
    # Check if the file needs updating
    if not should_update_file(content):
        logger.info(f"No update needed for: {file_path}")
        return False
    
    # Store original content for verification
    original_content = content
    
    # Remove existing problematic import patterns
    for pattern in IMPORT_PATTERNS:
        content = pattern.sub('# Removed problematic import', content)
    
    # Remove fix_imports() call if present
    content = re.sub(r'fix_imports\(\)', '# Removed old fix_imports call', content)
    
    # Add our import header at the top
    new_content = IMPORT_HEADER + '\n' + content
    
    # Preview changes if requested
    if preview_mode:
        logger.info(f"Preview changes for: {file_path}")
        logger.info("First 500 chars of new content would be:")
        logger.info(new_content[:500])
        return True
    
    # Verify the changes don't remove critical code
    if len(new_content) < len(original_content) * 0.8:
        logger.warning(f"Warning: New content is significantly shorter for {file_path}")
        logger.warning(f"Original size: {len(original_content)}, New size: {len(new_content)}")
        return False
    
    # Create a backup before modifying
    if not backup_file(file_path):
        logger.error(f"Skipping update for {file_path} due to backup failure")
        return False
    
    # Write the updated content
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        logger.info(f"Updated: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {e}")
        return False

def main():
    """Main function to fix imports in test files."""
    logger.info("Starting test import fixer")
    
    # Add command-line argument parsing
    parser = argparse.ArgumentParser(description='Fix imports in test files')
    parser.add_argument('--preview', action='store_true', help='Preview changes without applying them')
    parser.add_argument('--single-file', help='Fix a single file instead of scanning directories')
    args = parser.parse_args()
    
    preview_mode = args.preview
    if preview_mode:
        logger.info("Running in preview mode - no changes will be applied")
    
    # Check if we're fixing a single file
    if args.single_file:
        if os.path.exists(args.single_file):
            logger.info(f"Processing single file: {args.single_file}")
            update_file(args.single_file, preview_mode)
        else:
            logger.error(f"File not found: {args.single_file}")
        return
    
    # Path to the tests directory - updated to handle current directory structure
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if we're already in the tests-dest directory
    current_dir_name = os.path.basename(script_dir)
    if current_dir_name == 'tests-dest':
        tests_dir = script_dir
    else:
        # If not, assume it's a subdirectory
        tests_dir = os.path.join(script_dir, 'tests-dest')
    
    logger.info(f"Tests directory: {tests_dir}")
    
    # List of test directories to process
    test_dirs = [
        os.path.join(tests_dir, 'api'),
        os.path.join(tests_dir, 'integration'),
        os.path.join(tests_dir, 'unit')
    ]
    
    total_updated = 0
    
    for test_dir in test_dirs:
        if not os.path.exists(test_dir):
            logger.warning(f"Directory not found: {test_dir}")
            continue
            
        test_files = find_test_files(test_dir)
        
        dir_updated = 0
        for file_path in test_files:
            if update_file(file_path, preview_mode):
                dir_updated += 1
                total_updated += 1
        
        logger.info(f"Updated {dir_updated} files in {test_dir}")
    
    logger.info(f"Total files {'analyzed' if preview_mode else 'updated'}: {total_updated}")

if __name__ == "__main__":
    main() 