"""
Diagnostic test for import path issues in test files.

This script helps identify and fix the common import path issues
that are causing test failures across the test suite.
"""

import os
import sys
import logging
import importlib
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("import_diagnostic")

def find_project_root():
    """Find the project root directory based on common markers."""
    # Start from the current directory
    current_dir = Path(__file__).resolve().parent
    
    # List of potential project root markers
    markers = [
        # Main application file
        lambda p: (p / "main.py").exists(),
        # Common directory structure
        lambda p: all((p / d).exists() for d in ["services", "models", "controllers"]),
        # Package configuration
        lambda p: (p / "pyproject.toml").exists() or (p / "setup.py").exists(),
    ]
    
    # Check the current directory and parents
    for path in [current_dir] + list(current_dir.parents):
        if any(marker(path) for marker in markers):
            return path
            
    # If we reached here, we couldn't find a definitive project root
    logger.warning("Could not identify project root using markers, using current directory")
    return current_dir

def test_import_resolution(module_path, project_root):
    """Test importing a module with different path configurations."""
    original_path = sys.path.copy()
    results = {}
    
    try:
        # Test 1: Default import (no path changes)
        sys.path = original_path.copy()
        results["default"] = try_import(module_path)
        
        # Test 2: With project root added to path
        sys.path = original_path.copy()
        sys.path.insert(0, str(project_root))
        results["with_project_root"] = try_import(module_path)
        
        # Test 3: With both project root and tests directory added
        sys.path = original_path.copy()
        sys.path.insert(0, str(project_root))
        sys.path.insert(0, str(project_root / "tests-dest"))
        results["with_tests_dir"] = try_import(module_path)
        
        # Test 4: Special handling for 'services' package
        if module_path.startswith("services."):
            module_name = module_path.split(".", 1)[1]
            sys.path = original_path.copy()
            sys.path.insert(0, str(project_root / "services"))
            results["services_direct"] = try_import(module_name)
    except Exception as e:
        logger.error(f"Error during import tests: {e}")
    finally:
        # Restore original sys.path
        sys.path = original_path
        
    return results

def try_import(module_path):
    """Try to import a module and return the result."""
    try:
        module = importlib.import_module(module_path)
        return {
            "success": True,
            "module": module.__name__,
            "file": getattr(module, "__file__", "unknown"),
            "path": sys.path.copy()
        }
    except ImportError as e:
        return {
            "success": False,
            "error": str(e),
            "path": sys.path.copy()
        }

def check_module_exists(directory, module_name):
    """Check if a module file exists in the given directory."""
    module_path = Path(directory) / f"{module_name}.py"
    return module_path.exists()

def print_system_info():
    """Print system path and environment information."""
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Python path: {sys.path}")
    logger.info(f"PYTHONPATH env: {os.environ.get('PYTHONPATH', 'Not set')}")
    logger.info(f"Module search paths:")
    for i, path in enumerate(sys.path):
        logger.info(f"  {i}: {path}")

def suggest_fixes(problematic_modules, project_root):
    """Suggest fixes for import issues."""
    fix_strategies = []
    
    fix_strategies.append(
        f"1. Add this code at the start of problematic test files:\n"
        f"```python\n"
        f"import sys\n"
        f"import os\n"
        f"# Add project root to Python path\n"
        f"sys.path.insert(0, os.path.abspath('{project_root}'))\n"
        f"```"
    )
    
    fix_strategies.append(
        f"2. Create a conftest.py file in tests-dest that sets up paths correctly:\n"
        f"```python\n"
        f"import pytest\n"
        f"import sys\n"
        f"import os\n"
        f"from pathlib import Path\n\n"
        f"# Add project root to path in pytest session\n"
        f"@pytest.fixture(scope='session', autouse=True)\n"
        f"def setup_path():\n"
        f"    project_root = Path(__file__).parent.parent\n"
        f"    sys.path.insert(0, str(project_root))\n"
        f"```"
    )
    
    fix_strategies.append(
        f"3. Use PYTHONPATH environment variable when running tests:\n"
        f"```\n"
        f"PYTHONPATH={project_root} python -m pytest tests-dest/\n"
        f"```"
    )
    
    fix_strategies.append(
        f"4. Create symbolic links to key modules in the tests-dest directory:\n"
        f"```bash\n"
        f"ln -s {project_root}/services {project_root}/tests-dest/services\n"
        f"ln -s {project_root}/models {project_root}/tests-dest/models\n"
        f"ln -s {project_root}/controllers {project_root}/tests-dest/controllers\n"
        f"```"
    )
    
    return fix_strategies

def main():
    """Main diagnostic function."""
    logger.info("Running import path diagnostic")
    
    # Print system information
    print_system_info()
    
    # Find project root
    project_root = find_project_root()
    logger.info(f"Detected project root: {project_root}")
    
    # Check if key modules exist in expected locations
    modules_to_check = {
        "services/state_manager.py": "services.state_manager",
        "services/monitor_service.py": "services.monitor_service",
        "services/material_service.py": "services.material_service",
        "utils/error_utils.py": "utils.error_utils",
        "models/material.py": "models.material",
    }
    
    # Test key imports
    problematic_modules = []
    
    logger.info("\n--- Module Location Checks ---")
    for file_path, module_path in modules_to_check.items():
        full_path = project_root / file_path
        exists = full_path.exists()
        logger.info(f"Module {module_path} ({file_path}): {'✓ Exists' if exists else '✗ Missing'}")
        
        if not exists:
            problematic_modules.append(module_path)
            continue
            
        # Try different import strategies
        logger.info(f"\n--- Import Tests for {module_path} ---")
        results = test_import_resolution(module_path, project_root)
        
        for strategy, result in results.items():
            success = result.get("success", False)
            status = "✓ Success" if success else "✗ Failed"
            details = result.get("file", result.get("error", ""))
            logger.info(f"  {strategy}: {status} - {details}")
            
        if not any(result.get("success", False) for result in results.values()):
            problematic_modules.append(module_path)
    
    # Suggest fixes
    if problematic_modules:
        logger.info("\n--- Import Problems Detected ---")
        logger.info(f"Problematic modules: {', '.join(problematic_modules)}")
        
        logger.info("\n--- Suggested Fixes ---")
        fixes = suggest_fixes(problematic_modules, project_root)
        for i, fix in enumerate(fixes, 1):
            logger.info(f"\nFix Strategy {i}:")
            logger.info(fix)
    else:
        logger.info("\n--- No Import Problems Detected ---")
        logger.info("All key modules can be imported with the right path configuration.")
    
    # Create a helper script that can be used to fix tests
    create_test_helper_script(project_root)
    
    logger.info("\nDiagnostic complete!")

def create_test_helper_script(project_root):
    """Create a test helper script for use in tests."""
    helper_path = project_root / "tests-dest" / "test_path_fixer.py"
    
    script_content = f'''"""
Test path fixer module to help resolve import issues in tests.

Usage:
    from test_path_fixer import fix_imports
    fix_imports()  # Call this at the top of your test file
"""

import os
import sys
from pathlib import Path

def fix_imports():
    """Fix imports by setting up the correct Python path."""
    # Find project root
    test_dir = Path(__file__).parent
    project_root = test_dir.parent
    
    # Add project root to path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        
    # Set environment variables
    os.environ.setdefault("TEST_MODE", "true")
    
    return project_root

if __name__ == "__main__":
    # If run directly, print diagnostic info
    project_root = fix_imports()
    print(f"Project root: {{project_root}}")
    print(f"Python path: {{sys.path}}")
    print(f"TEST_MODE: {{os.environ.get('TEST_MODE', 'Not set')}}")
'''
    
    # Write the helper script
    with open(helper_path, 'w') as f:
        f.write(script_content)
        
    logger.info(f"\nCreated test helper script at {helper_path}")
    logger.info("You can use this in test files by adding:")
    logger.info("```python")
    logger.info("from test_path_fixer import fix_imports")
    logger.info("fix_imports()  # Call at the top of your test file")
    logger.info("```")

if __name__ == "__main__":
    main() 