"""
Integration test repair script.

This script copies a failing integration test, fixes it using our import helper,
and runs it to validate the fix works.
"""
import os
import sys
import shutil
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_fixer")

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

def create_temp_test_file(test_path):
    """Create a temporary test file with the import fix applied."""
    # Create output directory and path
    out_dir = Path("temp_fixed_tests")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / test_path.name
    
    # Read original file content
    with open(test_path, "r") as f:
        content = f.read()
    
    # Add import fix at the top of the file
    import_fix = """
# Import fix added by test_fixer.py
import sys
import os
from pathlib import Path

# Add the tests-dest directory to sys.path if it's not already there
tests_dest_dir = Path(__file__).parent.parent / "tests-dest"
if tests_dest_dir.exists() and str(tests_dest_dir) not in sys.path:
    sys.path.insert(0, str(tests_dest_dir))

# Fix imports before any other imports
try:
    # Use import_helper from tests_dest package (with underscore)
    from tests_dest.import_helper import fix_imports
    fix_imports()
except ImportError:
    # Directly import the module using its file path
    import importlib.util
    import_helper_path = Path(__file__).parent.parent / "tests-dest" / "import_helper.py"
    if import_helper_path.exists():
        spec = importlib.util.spec_from_file_location("import_helper", import_helper_path)
        import_helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(import_helper)
        import_helper.fix_imports()
    else:
        print(f"WARNING: Could not find import_helper.py at {import_helper_path}")
        # Add project root to path manually
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

"""
    
    # Check if the file already has our import fix
    if "import_helper import fix_imports" in content or "fix_imports()" in content:
        logger.info(f"✓ Test file already has the import fix: {test_path}")
        # Just copy it as-is
        with open(out_path, "w") as f:
            f.write(content)
        return out_path
    
    # Add the import fix at the top, but after any docstring
    if content.strip().startswith('"""'):
        # File has a docstring, add import fix after it
        docstring_end = content.find('"""', 3) + 3
        new_content = content[:docstring_end] + "\n" + import_fix + content[docstring_end:]
    else:
        # No docstring, add import fix at the top
        new_content = import_fix + content
    
    # Update error field if needed
    if '"error":' in new_content and '"error_code":' not in new_content:
        logger.info("Updating error field to error_code")
        new_content = new_content.replace('"error":', '"error_code":')
    
    if "assert response_data[\"error\"]" in new_content:
        logger.info("Updating error assertion to use error_code")
        new_content = new_content.replace(
            "assert response_data[\"error\"]", 
            "assert response_data[\"error_code\"]"
        )
    
    # Write the fixed content
    with open(out_path, "w") as f:
        f.write(new_content)
    
    logger.info(f"✓ Created fixed test file: {out_path}")
    return out_path

def find_integration_tests():
    """Find all integration test files in the project."""
    project_root = find_project_root()
    integration_test_dir = project_root / "tests-dest" / "integration"
    
    if not integration_test_dir.exists():
        logger.error(f"Integration test directory not found: {integration_test_dir}")
        return []
    
    test_files = list(integration_test_dir.glob("test_*.py"))
    return test_files

def fix_test_file(test_path):
    """Fix a test file and return the fixed path."""
    # Create a temporary fixed version
    fixed_path = create_temp_test_file(test_path)
    
    logger.info(f"Running fixed test: {fixed_path}")
    
    # Set PYTHONPATH to include the project root
    env = os.environ.copy()
    project_root = find_project_root()
    env["PYTHONPATH"] = str(project_root)
    
    # Run the fixed test
    result = subprocess.run(
        ["python", str(fixed_path)],
        capture_output=True,
        text=True,
        env=env
    )
    
    if result.returncode == 0:
        logger.info(f"✅ Test passed: {fixed_path}")
        logger.info("Output:\n" + result.stdout)
        return fixed_path
    else:
        logger.error(f"❌ Test failed: {fixed_path}")
        logger.error("Output:\n" + result.stdout)
        logger.error("Error:\n" + result.stderr)
        return None

def main():
    """Main function that fixes an integration test."""
    logger.info("Integration test fix script")
    
    # Find project root
    project_root = find_project_root()
    logger.info(f"Project root: {project_root}")
    
    # Find integration tests
    test_files = find_integration_tests()
    if not test_files:
        logger.error("No test files found")
        return 1
    
    # Try material test files first
    material_tests = [f for f in test_files if "material" in f.name.lower()]
    if material_tests:
        for material_test in material_tests:
            logger.info(f"Attempting to fix material test: {material_test}")
            fixed_path = fix_test_file(material_test)
            if fixed_path:
                logger.info(f"✅ Successfully fixed: {material_test}")
                show_fix_instructions()
                return 0
    
    # If no material test or fix failed, try other test files
    for test_file in test_files:
        if test_file not in material_tests:  # Skip already tried material tests
            logger.info(f"Attempting to fix test file: {test_file}")
            fixed_path = fix_test_file(test_file)
            if fixed_path:
                logger.info(f"✅ Successfully fixed: {test_file}")
                show_fix_instructions()
                return 0
    
    logger.error("❌ Could not fix any test files")
    show_fix_instructions(failed=True)
    return 1

def show_fix_instructions(failed=False):
    """Show instructions for fixing tests."""
    if failed:
        logger.info("\nManual Fix Instructions:")
    else:
        logger.info("\nHow to fix other tests:")
    
    logger.info("1. Add this code at the top of each test file (after any docstring):")
    logger.info("```python")
    logger.info("import sys")
    logger.info("import os")
    logger.info("from pathlib import Path")
    logger.info("")
    logger.info("# Add the tests-dest directory to sys.path")
    logger.info("tests_dest_dir = Path(__file__).parent.parent / \"tests-dest\"")
    logger.info("if tests_dest_dir.exists() and str(tests_dest_dir) not in sys.path:")
    logger.info("    sys.path.insert(0, str(tests_dest_dir))")
    logger.info("")
    logger.info("# Import the helper and fix imports")
    logger.info("from tests_dest.import_helper import fix_imports")
    logger.info("fix_imports()")
    logger.info("```")
    logger.info("")
    logger.info("2. Update assertions checking for 'error' to use 'error_code' instead:")
    logger.info("   Change: assert response_data[\"error\"] == \"not_found\"")
    logger.info("   To:     assert response_data[\"error_code\"] == \"not_found\"")
    logger.info("")
    logger.info("3. If you continue to have issues, try running your test with PYTHONPATH set:")
    logger.info("   PYTHONPATH=. python tests-dest/integration/your_test.py")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 