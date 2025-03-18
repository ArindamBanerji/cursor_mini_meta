"""Script to remove setup_module and teardown_module functions from test files."""

import os
import re
from pathlib import Path

def remove_setup_teardown(file_path):
    """Remove setup_module and teardown_module functions from a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match setup_module and teardown_module functions
    # This handles both the function definition and its body until the next def or class
    pattern = r'\ndef setup_module\(module\):.*?(?=\n(?:def|class)|$)|\ndef teardown_module\(module\):.*?(?=\n(?:def|class)|$)'
    
    # Remove the functions
    new_content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # Remove any resulting multiple blank lines
    new_content = re.sub(r'\n{3,}', '\n\n', new_content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def process_directory(directory):
    """Process all Python files in a directory recursively."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') and 'test_' in file:
                file_path = os.path.join(root, file)
                print(f"Processing {file_path}")
                try:
                    remove_setup_teardown(file_path)
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

if __name__ == '__main__':
    tests_dir = Path('tests-dest')
    if tests_dir.exists():
        process_directory(tests_dir)
        print("Completed processing all test files")
    else:
        print("tests-dest directory not found") 