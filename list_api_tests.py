#!/usr/bin/env python3
"""
List API Test Files

This script simply lists all API test files in the tests_dest/api directory.
"""

import os
from pathlib import Path

def main():
    """List all API test files."""
    api_dir = Path('tests_dest/api')
    
    if not api_dir.exists():
        print(f"Directory {api_dir} does not exist")
        return
    
    # List all Python test files
    test_files = list(api_dir.glob('test_*.py'))
    
    print(f"Found {len(test_files)} API test files:")
    for i, file_path in enumerate(test_files, 1):
        print(f"{i}. {file_path}")

if __name__ == "__main__":
    main() 