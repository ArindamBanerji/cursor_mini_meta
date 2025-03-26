#!/usr/bin/env python
"""
FileList - List Python test files in a directory with optional range filtering

Usage:
    python file_list.py -source "directory_path" [-range "start-end"]

Examples:
    python file_list.py -source "tests_dest/api"
    python file_list.py -source "tests_dest/api" -range "5-10"
"""

import os
import sys
import argparse
from pathlib import Path

def list_test_files(directory, range_spec=None):
    """
    List Python files with 'test' in their name from the given directory
    
    Args:
        directory (str): Directory path to search
        range_spec (str, optional): Range specification in format "start-end"
    
    Returns:
        List of filenames in alphabetical order, optionally filtered by range
    """
    try:
        # Convert to Path object to handle Windows paths properly
        dir_path = Path(directory)
        
        # Verify directory exists
        if not dir_path.exists():
            print(f"Error: Directory '{directory}' doesn't exist")
            return []
            
        if not dir_path.is_dir():
            print(f"Error: '{directory}' is not a directory")
            return []
        
        # List all Python files with 'test' in the name
        test_files = [f.name for f in dir_path.iterdir() 
                     if f.is_file() and f.suffix == '.py' and 'test' in f.name.lower()]
        
        # Sort alphabetically
        test_files.sort()
        
        # No files found
        if not test_files:
            print(f"No Python test files found in '{directory}'")
            return []
        
        # If range is specified, filter the list
        if range_spec:
            try:
                start, end = map(int, range_spec.split('-'))
                
                # Adjust for 0-based indexing
                if start < 1:
                    start = 1
                    
                # Check if indices are valid
                if start > len(test_files) or end < start:
                    print(f"Error: Invalid range '{range_spec}' for {len(test_files)} files")
                    return test_files
                
                # Slice the list (adjusting for 0-based indexing)
                return test_files[start-1:end]
            except ValueError:
                print(f"Error: Invalid range format '{range_spec}', expected 'start-end'")
                return test_files
        
        return test_files
        
    except Exception as e:
        print(f"Error listing files: {str(e)}")
        return []

def main():
    """Parse arguments and display results"""
    parser = argparse.ArgumentParser(description="List Python test files in a directory")
    parser.add_argument("-source", required=True, help="Directory to search for test files")
    parser.add_argument("-range", help="Optional range specification (e.g., '5-10')")
    
    # Handle argument errors gracefully
    try:
        args = parser.parse_args()
    except SystemExit:
        print("\nUsage example: python file_list.py -source \"tests_dest/api\" -range \"5-10\"")
        sys.exit(1)
    
    # Get the files
    files = list_test_files(args.source, args.range)
    
    # Display results
    if files:
        print(f"\nFound {len(files)} test file(s):")
        for i, file in enumerate(files, 1):
            print(f"{i}. {file}")
    else:
        print("No matching files found or an error occurred.")

if __name__ == "__main__":
    main() 