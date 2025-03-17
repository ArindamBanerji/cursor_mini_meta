#!/usr/bin/env python
"""
test_setup.py - Initialize the testing environment

This script sets up the necessary environment for testing the SAP Test Harness:
1. Sets environment variables (SAP_HARNESS_HOME, SAP_HARNESS_CONFIG)
2. Creates test directory structure if needed
3. Generates conftest.py files using GenConfTest
4. Optionally adds or removes code snippets to/from test files

Usage:
    python test_setup.py [--gen-conftest-dir PATH] [--clean] [--add-snippets] [--remove-snippets]
"""
import os
import sys
import json
import shutil
import argparse
import subprocess
from pathlib import Path

def find_project_root():
    """Find the project root directory based on the presence of main.py"""
    # Start with the directory containing this script
    current_dir = Path(__file__).parent.absolute()
    
    # If main.py exists in the current directory, this is the project root
    if (current_dir / "main.py").exists():
        return current_dir
    
    # Otherwise, check each parent directory
    for parent in current_dir.parents:
        if (parent / "main.py").exists():
            return parent
    
    # If not found anywhere, use the current directory as a fallback
    return current_dir

def load_config():
    """Load configuration from environment variable or create default"""
    config_path = os.environ.get("SAP_HARNESS_CONFIG")
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config from {config_path}: {e}")
            print("Using default configuration instead.")
    
    # Create default configuration
    project_root = str(find_project_root())
    return {
        "project_root": project_root,
        "source_dirs": ["services", "models", "controllers", "utils", "api"],
        "test_dirs": ["tests-dest"],
        "test_subdirs": ["api", "unit", "integration", "services", "models", "monitoring"],
        "module_mappings": {
            "tests-dest/models": "model_tests"
        }
    }

def save_config(config, output_path=None):
    """Save configuration to file"""
    if not output_path:
        output_path = "test_structure.json"
    
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)
    
    # Set environment variable to point to this config
    config_path = str(Path(output_path).absolute())
    os.environ["SAP_HARNESS_CONFIG"] = config_path
    print(f"Set SAP_HARNESS_CONFIG={config_path}")

def run_command(cmd, description=None, check=True):
    """Run a command and handle errors"""
    if description:
        print(f"\n{description}...")
    
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                               universal_newlines=True)
        print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print(f"Error output: {e.stderr}")
        return False, e.stderr

def clean_test_environment(config):
    """Clean up the test environment by removing test directories and artifacts"""
    print("\nCleaning test environment...")
    
    # Remove test directories
    for test_dir in config["test_dirs"]:
        test_path = Path(test_dir)
        if test_path.exists():
            print(f"Removing directory: {test_path}")
            try:
                shutil.rmtree(test_path)
            except Exception as e:
                print(f"Error removing {test_path}: {e}")
    
    # Remove conftest.py files
    for pattern in ["conftest.py", "**/conftest.py", "**/__pycache__", "**/*.pyc"]:
        for item in Path('.').glob(pattern):
            if item.exists() and str(item).startswith(tuple(config["test_dirs"])):
                try:
                    if item.is_file():
                        item.unlink()
                    else:
                        shutil.rmtree(item)
                    print(f"Removed: {item}")
                except Exception as e:
                    print(f"Error removing {item}: {e}")
    
    # Remove any backup files
    for backup_file in Path('.').glob("**/*.bak"):
        if backup_file.exists() and str(backup_file).startswith(tuple(config["test_dirs"])):
            try:
                backup_file.unlink()
                print(f"Removed backup file: {backup_file}")
            except Exception as e:
                print(f"Error removing {backup_file}: {e}")
    
    print("Clean operation completed.")

def create_directory_if_needed(target_dir):
    """Create a directory if it doesn't exist."""
    target_path = Path(target_dir)
    
    if not target_path.exists():
        try:
            target_path.mkdir(parents=True)
            return True, f"Created directory: {target_path}"
        except Exception as e:
            return False, f"Error creating directory {target_path}: {e}"
    
    return True, f"Directory {target_path} already exists."

def create_init_files(config):
    """Create test directories and __init__.py files"""
    for test_dir in config["test_dirs"]:
        base_dir = Path(test_dir)
        if not base_dir.exists():
            base_dir.mkdir(parents=True)
            print(f"Created directory {test_dir}")
        
        init_file = base_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Test package init\n")
            print(f"Created {init_file}")
        
        # Create subdirectories and their __init__.py files
        for subdir in config["test_subdirs"]:
            sub_path = base_dir / subdir
            if not sub_path.exists():
                sub_path.mkdir(parents=True)
                print(f"Created directory {sub_path}")
            
            sub_init = sub_path / "__init__.py"
            if not sub_init.exists():
                sub_init.write_text(f"# {subdir} test package init\n")
                print(f"Created {sub_init}")

def find_snippet_file():
    """Find the snippet file by checking common locations and names"""
    # List of possible filenames and locations to check
    possible_files = [
        "code_snippet_for_test_files.py",
        "code_snippet_for_test_files.txt",
        "tests-dest/code_snippet_for_test_files.py",
        "tests-dest/code_snippet_for_test_files.txt"
    ]
    
    for filename in possible_files:
        if Path(filename).exists():
            return str(Path(filename).absolute())
    
    return None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Initialize the testing environment for SAP Test Harness")
    parser.add_argument("--gen-conftest-dir", help="Directory containing GenConfTest.py")
    parser.add_argument("--clean", action="store_true", help="Clean test environment before setup")
    parser.add_argument("--add-snippets", action="store_true", help="Add code snippets to test files")
    parser.add_argument("--remove-snippets", action="store_true", help="Remove code snippets from test files")
    parser.add_argument("--check-snippets", action="store_true", help="Check which test files have snippets")
    args = parser.parse_args()
    
    # Find project root
    project_root = find_project_root()
    print(f"Detected project root: {project_root}")
    
    # Set SAP_HARNESS_HOME environment variable
    os.environ["SAP_HARNESS_HOME"] = str(project_root)
    print(f"Set SAP_HARNESS_HOME={project_root}")
    
    # Load configuration from environment variable or create default
    config = load_config()
    
    # Verify project root from config matches detected root, update if needed
    if config["project_root"] != str(project_root):
        print(f"Updating project_root in config from '{config['project_root']}' to '{project_root}'")
        config["project_root"] = str(project_root)
    
    # Save configuration to file
    save_config(config)
    
    # Clean if requested
    if args.clean:
        clean_test_environment(config)
    
    # Create __init__.py files in test directories
    create_init_files(config)
    
    # Determine GenConfTest path
    gen_conftest_path = "GenConfTest.py"
    if args.gen_conftest_dir:
        gen_conftest_path = os.path.join(args.gen_conftest_dir, "GenConfTest.py")
    
    # Validate GenConfTest.py exists
    if not Path(gen_conftest_path).exists():
        print(f"Error: GenConfTest.py not found at {gen_conftest_path}")
        print("Please specify the correct path with --gen-conftest-dir")
        return 1
    
    # Run GenConfTest to generate conftest files
    test_dir = config['test_dirs'][0]
    subdirs = ",".join(["root"] + config['test_subdirs'])
    genconftest_cmd = f"python {gen_conftest_path} -source {test_dir} -sub-dir-list {subdirs} --overwrite"
    success, _ = run_command(genconftest_cmd, "Generating conftest.py files")
    
    if not success:
        print("Warning: GenConfTest command failed. Continuing with setup...")
    
    # Handle code snippets based on command line args
    # Find snippet file first
    snippet_path = find_snippet_file()
    
    if snippet_path:
        print(f"Found snippet file: {snippet_path}")
        
        # Check if SnippetForTests.py exists
        snippet_script = Path("SnippetForTests.py")
        if args.gen_conftest_dir:
            # Also check in the conftest directory
            conftest_dir = Path(args.gen_conftest_dir)
            if (conftest_dir / "SnippetForTests.py").exists():
                snippet_script = conftest_dir / "SnippetForTests.py"
                
        if not snippet_script.exists():
            print("Warning: SnippetForTests.py not found. Skipping snippet operations.")
        else:
            # Check which test files have snippets
            if args.check_snippets:
                check_cmd = f"python {snippet_script} -source {test_dir} -option ADD --check-only"
                run_command(check_cmd, "Checking test files for snippets", check=False)
            
            # Remove snippets if requested
            if args.remove_snippets:
                remove_cmd = f"python {snippet_script} -source {test_dir} -option REMOVE"
                run_command(remove_cmd, "Removing snippets from test files", check=False)
            
            # Add snippets if requested
            if args.add_snippets:
                add_cmd = f"python {snippet_script} -source {test_dir} -snippet {snippet_path} -option ADD"
                run_command(add_cmd, "Adding import snippets to test files", check=False)
    else:
        print("Warning: No snippet file found. Skipping snippet operations.")
    
    print("\nEnvironment setup complete!")
    return 0

if __name__ == "__main__":
    sys.exit(main())