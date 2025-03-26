"""
Creates a symbolic link from tests_dest to tests-dest to help with Python imports.

Python can't import from directories with hyphens, so we create a symlink with underscores.
"""
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("symlink_creator")

def find_project_root():
    """Find the project root directory."""
    current_file = Path(__file__).resolve()
    project_root = current_file.parent
    
    # Look for common markers
    for path in [project_root] + list(project_root.parents):
        if (path / "tests-dest").exists() and (path / "services").exists():
            return path
    
    # Default to current directory
    return project_root

def create_symlink():
    """Create a symbolic link from tests_dest to tests-dest."""
    project_root = find_project_root()
    source_dir = project_root / "tests-dest"
    target_dir = project_root / "tests_dest"
    
    if not source_dir.exists():
        logger.error(f"Source directory does not exist: {source_dir}")
        return False
    
    if target_dir.exists():
        logger.info(f"Target directory already exists: {target_dir}")
        # Check if it's already a symlink to our source
        if target_dir.is_symlink() and target_dir.resolve() == source_dir.resolve():
            logger.info("Symbolic link is already correctly configured.")
            return True
        else:
            logger.warning(f"Target exists but is not a symlink to {source_dir}")
            return False
    
    try:
        # Create symbolic link - use os.symlink as pathlib may have issues on Windows
        os.symlink(str(source_dir), str(target_dir), target_is_directory=True)
        logger.info(f"✅ Created symbolic link: {target_dir} -> {source_dir}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create symbolic link: {e}")
        logger.info("On Windows, you might need to run this script as administrator")
        logger.info("or enable Developer Mode to create symbolic links.")
        return False

def create_init_files():
    """Create __init__.py files to make directories importable as packages."""
    project_root = find_project_root()
    source_dir = project_root / "tests-dest"
    
    if not source_dir.exists():
        logger.error(f"Source directory does not exist: {source_dir}")
        return False
    
    # Create __init__.py files in tests-dest and its subdirectories
    for directory in [source_dir] + list(source_dir.glob("*/")):
        init_file = directory / "__init__.py"
        if not init_file.exists():
            try:
                init_file.touch()
                logger.info(f"Created {init_file}")
            except Exception as e:
                logger.error(f"Failed to create {init_file}: {e}")
    
    return True

def show_alternative_instructions():
    """Show alternative instructions if symlink creation fails."""
    logger.info("\nAlternative solution if symbolic links don't work:")
    logger.info("1. Create a copy of the tests-dest directory named tests_dest:")
    logger.info("   ```")
    logger.info("   cp -r tests-dest tests_dest")  # Unix
    logger.info("   # or on Windows:")
    logger.info("   xcopy /E /I tests-dest tests_dest")
    logger.info("   ```")
    logger.info("")
    logger.info("2. Make sure both directories have __init__.py files:")
    logger.info("   ```")
    logger.info("   touch tests_dest/__init__.py")
    logger.info("   touch tests_dest/integration/__init__.py")
    logger.info("   touch tests_dest/unit/__init__.py")
    logger.info("   # same for other subdirectories")
    logger.info("   ```")
    logger.info("")
    logger.info("3. In your tests, import from tests_dest instead of tests-dest")

def main():
    """Main function."""
    logger.info("Creating symbolic link for tests-dest directory")
    
    # Create __init__.py files first
    create_init_files()
    
    # Create symlink
    success = create_symlink()
    if not success:
        show_alternative_instructions()
        return 1
    
    logger.info("\nNow you can import from tests_dest in your Python code:")
    logger.info("from tests_dest.import_helper import fix_imports")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 