import os
import re
from pathlib import Path

def fix_imports(content):
    """Fix ModuleType import and other imports."""
    # Replace ModuleType import from typing with types
    content = re.sub(
        r'from typing import.*ModuleType.*',
        'from types import ModuleType',
        content
    )
    return content

def fix_async_syntax(content):
    """Fix async syntax issues."""
    # Remove async from setup_module
    content = re.sub(
        r'@pytest\.mark\.asyncio\s*async\s*def\s+setup_module',
        'def setup_module',
        content
    )
    return content

def fix_logger_usage(content):
    """Remove logger.info calls from setup/teardown."""
    # Remove logger.info calls
    content = re.sub(
        r'logger\.info\(".*?"\)',
        '',
        content
    )
    return content

def process_file(file_path):
    """Process a single test file."""
    print(f"Processing {file_path}")
    
    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply fixes
    content = fix_imports(content)
    content = fix_async_syntax(content)
    content = fix_logger_usage(content)
    
    # Write back to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")

def main():
    """Main function to process all test files."""
    # Get all test files
    test_dirs = ['tests-dest/api', 'tests-dest/unit']
    for test_dir in test_dirs:
        for file_path in Path(test_dir).glob('test_*.py'):
            process_file(str(file_path))

if __name__ == '__main__':
    main() 