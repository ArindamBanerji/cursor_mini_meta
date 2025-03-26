"""
Revert import helper changes from test files while preserving error_code fixes.

This script removes the import helper code that was automatically added to test files,
but preserves the error_code fixes that were made.
"""
import os
import sys
import logging
import re
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("revert_fix")

def find_project_root():
    """Find the project root directory."""
    current_file = Path(__file__).resolve()
    potential_root = current_file.parent
    
    # Look for common markers
    for path in [potential_root] + list(potential_root.parents):
        if (path / "tests-dest").exists() and (path / "services").exists():
            return path
    
    # Default to current directory
    return potential_root

def revert_import_helper(file_path):
    """Remove import helper but preserve error_code fixes."""
    try:
        # Read the file
        with open(file_path, "r") as f:
            content = f.read()
        
        # Skip if the helper is not present
        if "import_helper" not in content and "fix_imports" not in content:
            logger.info(f"✓ File doesn't have import helper: {file_path}")
            return True
        
        # Remove the import helper block
        # The import helper block typically starts with "# Import helper to fix path issues"
        # and ends after the try-except block
        
        # Pattern to match the import helper block
        import_helper_pattern = r'# Import helper to fix path issues.*?(?:except.*?\n\s+.*?\n\s*\n|\n\s*\n)'
        
        # Use re.DOTALL to match across multiple lines
        updated_content = re.sub(import_helper_pattern, '', content, flags=re.DOTALL)
        
        # Fix any double newlines that might have been created
        updated_content = re.sub(r'\n\n\n+', '\n\n', updated_content)
        
        # Write the updated content
        with open(file_path, "w") as f:
            f.write(updated_content)
        
        logger.info(f"✓ Removed import helper from: {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to update {file_path}: {str(e)}")
        return False

def find_test_files():
    """Find all Python test files in the tests-dest directory."""
    project_root = find_project_root()
    tests_dir = project_root / "tests-dest"
    
    if not tests_dir.exists():
        logger.error(f"Tests directory not found: {tests_dir}")
        return []
    
    test_files = []
    
    # Recursively find all Python files in tests-dest
    for root, _, files in os.walk(tests_dir):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(Path(root) / file)
    
    return test_files

def main():
    """Main function."""
    logger.info("Finding test files...")
    
    # Find project root
    project_root = find_project_root()
    logger.info(f"Project root: {project_root}")
    
    # Find test files
    test_files = find_test_files()
    logger.info(f"Found {len(test_files)} test files")
    
    # Process each test file
    successful = 0
    for file_path in test_files:
        logger.info(f"Processing: {file_path.relative_to(project_root)}")
        if revert_import_helper(file_path):
            successful += 1
    
    logger.info(f"✅ Reverted {successful} of {len(test_files)} test files")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 