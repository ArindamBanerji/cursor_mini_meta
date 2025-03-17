#!/usr/bin/env python
"""
GenConfTest.py
-------------
A utility script that generates appropriate conftest.py files for
specified test subdirectories.

Usage:
    python GenConfTest.py -source <test_dir> -sub-dir-list <comma_separated_subdirs> [--overwrite] [--fix-issues] [--create-init]

Example:
    python GenConfTest.py -source ./tests-dest -sub-dir-list root,api,models,integration

The script will:
1. Generate appropriate conftest.py files for each specified directory
2. Customize the content based on the subdirectory type
3. Handle Windows paths and spaces in paths
4. Provide diagnostics and final verification
5. Fix common issues if the --fix-issues flag is provided
6. Create __init__.py files if the --create-init flag is provided
"""

import argparse
from pathlib import Path
import sys
import os
import json

# Import helper modules
from genconftest_templates import get_template_for_subdir
from genconftest_utils import (
    validate_directory_path,
    create_directory_if_needed,
    write_conftest_file,
    validate_conftest_content,
    generate_diagnostics,
    check_for_test_files,
    verify_imports,
    fix_common_issues,
    normalize_path,
    create_init_file
)

def load_config():
    """Load configuration from environment variable"""
    config_path = os.environ.get("SAP_HARNESS_CONFIG")
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config from {config_path}: {e}")
            print("Continuing without configuration file")
    
    return None

def create_conftest_file(target_dir, subdir, overwrite=False, fix_issues=False, create_init=False, config=None):
    """
    Create a conftest.py file in the target directory.
    
    Args:
        target_dir: Path to the directory where conftest.py will be created
        subdir: Subdirectory name (determines the template to use)
        overwrite: Whether to overwrite existing files
        fix_issues: Whether to fix common issues in existing files
        create_init: Whether to create __init__.py files
        config: Optional configuration dictionary
        
    Returns:
        tuple: (success, message)
    """
    target_path = Path(target_dir)
    
    # Create directory if it doesn't exist
    dir_created, dir_message = create_directory_if_needed(target_path)
    if not dir_created:
        return False, dir_message
    
    # Create __init__.py file if requested
    if create_init:
        init_created, init_message = create_init_file(target_path)
        print(f"  {init_message}")
    
    # Check if file already exists
    conftest_path = target_path / "conftest.py"
    
    if conftest_path.exists():
        if fix_issues:
            # Try to fix common issues in the existing file
            fixed, changes = fix_common_issues(conftest_path)
            if fixed:
                return True, f"Fixed issues in existing conftest.py in {target_path}: {', '.join(changes)}"
        
        if not overwrite:
            return False, f"conftest.py already exists in {target_path}. Use --overwrite to replace or --fix-issues to repair."
    
    # Get appropriate template for this subdirectory
    content = get_template_for_subdir(subdir)
    
    # If subdir is "models" and we have a module mapping in the config, adjust imports
    if subdir.lower() == "models" and config and "module_mappings" in config:
        mapping = config.get("module_mappings", {}).get("tests-dest/models")
        if mapping:
            # Add a comment explaining the special handling
            content = content.replace("Model test fixtures and configurations.", 
                                     f"Model test fixtures and configurations.\n\nNOTE: This directory has special mapping to '{mapping}' to avoid namespace conflicts.")
    
    # Write the file
    success, message = write_conftest_file(target_path, content)
    return success, message

def verify_conftest_file(target_dir):
    """
    Verify that the conftest.py file was created successfully and has valid content.
    
    Args:
        target_dir: Path to the directory where conftest.py should be
    
    Returns:
        tuple: (exists, is_valid, message, diagnostics)
    """
    conftest_path = Path(target_dir) / "conftest.py"
    
    # Check if file exists
    if not conftest_path.exists():
        return False, False, f"conftest.py does not exist in {target_dir}", None
    
    # Generate diagnostics
    diagnostics = generate_diagnostics(conftest_path)
    
    # Validate file content
    is_valid, message = validate_conftest_content(conftest_path)
    
    # Verify imports
    imports_valid, import_issues = verify_imports(conftest_path)
    if not imports_valid:
        is_valid = False
        message += f" Import issues: {', '.join(import_issues)}"
    
    return True, is_valid, message, diagnostics

def main():
    """Main function to generate conftest.py files."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Generate conftest.py files for specified test subdirectories.'
    )
    parser.add_argument('-source', required=True, help='Source test directory')
    parser.add_argument('-sub-dir-list', dest='subdirs', required=True, 
                        help='Comma-separated list of subdirectories (use "root" for main directory)')
    parser.add_argument('--overwrite', action='store_true', 
                        help='Overwrite existing conftest.py files')
    parser.add_argument('--fix-issues', action='store_true',
                        help='Fix common issues in existing conftest.py files')
    parser.add_argument('--verify-only', action='store_true',
                        help='Only verify existing conftest.py files without creating new ones')
    parser.add_argument('--diagnostic', action='store_true',
                        help='Generate additional diagnostic information')
    parser.add_argument('--create-init', action='store_true',
                        help='Create __init__.py files in test directories')
    parser.add_argument('--set-env', action='store_true',
                        help='Set SAP_HARNESS_HOME environment variable to project root')
    
    args = parser.parse_args()
    
    # Load configuration if available
    config = load_config()
    
    # Validate source path
    source_path, is_valid, message = validate_directory_path(args.source)
    if not is_valid:
        print(f"Error: {message}")
        return 1
    
    # Parse subdirectory list
    subdirs = [s.strip() for s in args.subdirs.split(',')]
    if not subdirs:
        print("Error: No subdirectories specified.")
        return 1
    
    # Set environment variable if requested
    if args.set_env:
        os.environ["SAP_HARNESS_HOME"] = str(source_path.parent.absolute())
        print(f"Set SAP_HARNESS_HOME={os.environ['SAP_HARNESS_HOME']}")
    
    print(f"Source directory: {source_path}")
    print(f"Subdirectories: {', '.join(subdirs)}")
    
    if args.verify_only:
        print("Running in verify-only mode. No files will be created or modified.")
    else:
        print(f"Overwrite existing files: {args.overwrite}")
        print(f"Fix issues in existing files: {args.fix_issues}")
        print(f"Create __init__.py files: {args.create_init}")
    
    # Process each subdirectory
    results = []
    
    for subdir in subdirs:
        if subdir.lower() == "root":
            # For root directory, use the source path
            target_dir = source_path
        else:
            # For subdirectories, append to source path
            target_dir = source_path / subdir
            
            # Check if directory has test files
            has_tests = check_for_test_files(target_dir)
            if not has_tests and not args.verify_only:
                print(f"Warning: Directory '{subdir}' does not contain any test files.")
        
        if args.verify_only:
            # Skip creation, only verify
            exists, is_valid, message, diagnostics = verify_conftest_file(target_dir)
            result_message = message if exists else f"conftest.py does not exist in {target_dir}"
            results.append((subdir, target_dir, exists, is_valid, result_message, diagnostics))
        else:
            # Create or fix the file
            success, message = create_conftest_file(
                target_dir, 
                subdir, 
                args.overwrite, 
                args.fix_issues,
                args.create_init,
                config
            )
            results.append((subdir, target_dir, success, message))
    
    # Verify results
    verification_results = []
    if not args.verify_only:
        for subdir, target_dir, success, _ in results:
            if success:
                exists, is_valid, message, diagnostics = verify_conftest_file(target_dir)
                verification_results.append((subdir, target_dir, exists, is_valid, message, diagnostics))
    
    # Print summary
    if args.verify_only:
        print("\nVerification Summary:")
        print("-" * 80)
        all_valid = True
        for subdir, target_dir, exists, valid, message, diagnostics in results:
            status = "Valid" if valid else "Invalid" if exists else "Missing"
            print(f"{status}: {subdir} -> {target_dir}")
            print(f"  {message}")
            
            if args.diagnostic and diagnostics:
                print("  Diagnostics:")
                for key, value in diagnostics.items():
                    if key != "path":
                        print(f"    {key}: {value}")
                        
            if not valid:
                all_valid = False
    else:
        print("\nGeneration Summary:")
        print("-" * 80)
        for subdir, target_dir, success, message in results:
            status = "Success" if success else "Failed"
            print(f"{status}: {subdir} -> {target_dir}")
            print(f"  {message}")
        
        print("\nVerification Summary:")
        print("-" * 80)
        all_valid = True
        for subdir, target_dir, exists, valid, message, diagnostics in verification_results:
            status = "Valid" if valid else "Invalid"
            print(f"{status}: {subdir} -> {target_dir}")
            print(f"  {message}")
            
            if args.diagnostic and diagnostics:
                print("  Diagnostics:")
                for key, value in diagnostics.items():
                    if key != "path":
                        print(f"    {key}: {value}")
                        
            if not valid:
                all_valid = False
    
    if args.verify_only:
        if all_valid:
            print("\nAll conftest.py files verified successfully!")
            return 0
        else:
            print("\nSome issues were found with the conftest.py files.")
            return 1
    else:
        if all_valid and len(verification_results) == len(results):
            print("\nAll conftest.py files generated and verified successfully!")
            return 0
        else:
            print("\nSome issues were encountered during generation or verification.")
            return 1

if __name__ == "__main__":
    sys.exit(main())