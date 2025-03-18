"""
Diagnostic test for conftest and test integration issues.

This script analyzes:
1. How test files import from services
2. What fixtures are defined in conftest.py
3. How tests use these fixtures
4. Import patterns that may cause conflicts
5. Dependencies between test modules and conftest

Run this with: python -m tests-dest.conftest_test_integration_diagnostic
"""

import os
import sys
import ast
import inspect
import importlib
import logging
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Any, Tuple, Optional, Set

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("conftest_diagnostic")

# Ensure project root is in sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Ensure tests directory is in sys.path
tests_dir = Path(__file__).parent
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))

def set_env_vars():
    """Set necessary environment variables."""
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root))
    os.environ.setdefault("PROJECT_ROOT", str(project_root))
    os.environ.setdefault("TEST_MODE", "true")

def safe_import(module_name: str) -> Tuple[Optional[ModuleType], Optional[Exception]]:
    """
    Safely import a module and return it along with any exception.
    
    Args:
        module_name: Name of the module to import
        
    Returns:
        Tuple of (module or None, exception or None)
    """
    try:
        module = importlib.import_module(module_name)
        return module, None
    except Exception as e:
        return None, e

def analyze_conftest():
    """
    Analyze the conftest.py file for fixtures and imported modules.
    
    Returns:
        Dictionary with analysis results
    """
    result = {
        "can_import": False,
        "error": None,
        "fixtures": [],
        "imported_modules": [],
        "service_imports": []
    }
    
    # Try to import the conftest module
    module, error = safe_import("conftest")
    if error:
        result["error"] = str(error)
        return result
    
    result["can_import"] = True
    
    # Find fixtures
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and hasattr(obj, "__pytest_wrapped__"):
            fixture_name = name
            result["fixtures"].append(fixture_name)
    
    # Analyze imports by parsing the file
    try:
        conftest_path = tests_dir / "conftest.py"
        with open(conftest_path, "r") as f:
            conftest_code = f.read()
            
        tree = ast.parse(conftest_code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    result["imported_modules"].append(name.name)
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module
                result["imported_modules"].append(module_name)
                
                # Check if it's a service import
                if module_name and module_name.startswith("services"):
                    for name in node.names:
                        result["service_imports"].append(f"{module_name}.{name.name}")
    except Exception as e:
        result["error"] = f"Error parsing conftest.py: {str(e)}"
    
    return result

def analyze_test_files() -> Dict[str, Any]:
    """
    Analyze test files for service imports and fixture usage.
    
    Returns:
        Dictionary with analysis results
    """
    result = {
        "test_files": [],
        "service_imports": {},
        "fixture_usage": {},
        "import_patterns": {},
        "errors": {}
    }
    
    # Find all test files
    test_categories = ["api", "unit", "integration", "model_tests", "monitoring"]
    test_files = []
    
    for category in test_categories:
        category_dir = tests_dir / category
        if category_dir.exists():
            for file in category_dir.glob("test_*.py"):
                test_files.append(file)
    
    # Analyze each test file
    for file in test_files:
        relative_path = file.relative_to(tests_dir)
        file_result = {
            "service_imports": [],
            "direct_imports": [],
            "from_conftest": [],
            "from_imports": [],
            "fixture_usage": []
        }
        
        try:
            with open(file, "r") as f:
                code = f.read()
                
            tree = ast.parse(code)
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        import_name = name.name
                        file_result["direct_imports"].append(import_name)
                        
                        if import_name == "services":
                            file_result["service_imports"].append(import_name)
                        elif import_name == "conftest":
                            file_result["from_conftest"].append(import_name)
                            
                elif isinstance(node, ast.ImportFrom):
                    module_name = node.module
                    if not module_name:
                        continue
                        
                    file_result["from_imports"].append(module_name)
                    
                    if module_name == "services":
                        for name in node.names:
                            file_result["service_imports"].append(f"services.{name.name}")
                    elif module_name == "conftest":
                        for name in node.names:
                            file_result["from_conftest"].append(name.name)
            
            # Extract fixture usage
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for arg in node.args.args:
                        arg_name = arg.arg
                        if arg_name not in ['self', 'cls'] and not arg_name.startswith('_'):
                            file_result["fixture_usage"].append(arg_name)
            
            # Record results
            result["test_files"].append(str(relative_path))
            result["service_imports"][str(relative_path)] = file_result["service_imports"]
            result["fixture_usage"][str(relative_path)] = file_result["fixture_usage"]
            
            # Categorize import patterns
            if file_result["service_imports"]:
                pattern = "direct_service_import"
            elif file_result["from_conftest"]:
                pattern = "from_conftest"
            else:
                pattern = "other"
                
            result["import_patterns"][str(relative_path)] = pattern
            
        except Exception as e:
            result["errors"][str(relative_path)] = str(e)
    
    return result

def analyze_test_imports():
    """Check conftest.py and test files for import patterns and inconsistencies."""
    logger.info("=== Conftest and Test Integration Diagnostic ===")
    
    # Set environment variables
    set_env_vars()
    
    # Analyze conftest
    logger.info("Analyzing conftest.py...")
    conftest_result = analyze_conftest()
    
    # Analyze test files
    logger.info("Analyzing test files...")
    test_files_result = analyze_test_files()
    
    # Print results
    print("\n=== DIAGNOSTIC RESULTS ===\n")
    
    # Conftest results
    print("conftest.py status:", "OK" if conftest_result["can_import"] else "ERROR")
    if conftest_result["error"]:
        print(f"  Error: {conftest_result['error']}")
    
    print(f"\nFixtures defined in conftest.py: {len(conftest_result['fixtures'])}")
    for fixture in sorted(conftest_result["fixtures"]):
        print(f"  {fixture}")
    
    print(f"\nService imports in conftest.py: {len(conftest_result['service_imports'])}")
    for imp in sorted(conftest_result["service_imports"]):
        print(f"  {imp}")
    
    # Test file results
    print(f"\nAnalyzed {len(test_files_result['test_files'])} test files")
    
    # Import patterns
    patterns = {}
    for file, pattern in test_files_result["import_patterns"].items():
        patterns.setdefault(pattern, []).append(file)
    
    print("\nImport patterns:")
    for pattern, files in patterns.items():
        print(f"  {pattern}: {len(files)} files")
    
    # Service import conflicts
    print("\nFiles with direct service imports:")
    direct_imports = []
    for file, imports in test_files_result["service_imports"].items():
        if imports:
            direct_imports.append((file, imports))
    
    for file, imports in sorted(direct_imports):
        print(f"  {file}:")
        for imp in imports:
            print(f"    {imp}")
    
    # Fixture usage
    fixture_usage = {}
    for file, fixtures in test_files_result["fixture_usage"].items():
        for fixture in fixtures:
            fixture_usage.setdefault(fixture, []).append(file)
    
    print("\nTop used fixtures:")
    for fixture, files in sorted(fixture_usage.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
        print(f"  {fixture}: {len(files)} files")
    
    # Errors
    if test_files_result["errors"]:
        print("\nErrors during analysis:")
        for file, error in test_files_result["errors"].items():
            print(f"  {file}: {error}")
    
    # Consistency analysis
    print("\n=== CONSISTENCY ANALYSIS ===\n")
    
    # Check if test files import services directly vs using conftest
    direct_service_importers = patterns.get("direct_service_import", [])
    conftest_importers = patterns.get("from_conftest", [])
    
    if direct_service_importers and conftest_importers:
        print("INCONSISTENCY: Tests use different service import patterns")
        print(f"  {len(direct_service_importers)} files import services directly")
        print(f"  {len(conftest_importers)} files import from conftest")
    
    # Check for fixtures defined in conftest but not used
    unused_fixtures = []
    for fixture in conftest_result["fixtures"]:
        if fixture not in fixture_usage:
            unused_fixtures.append(fixture)
    
    if unused_fixtures:
        print("\nUnused fixtures defined in conftest.py:")
        for fixture in unused_fixtures:
            print(f"  {fixture}")
    
    # Check for fixtures used but not defined in conftest
    undefined_fixtures = []
    for fixture in fixture_usage:
        if fixture not in conftest_result["fixtures"]:
            undefined_fixtures.append(fixture)
    
    if undefined_fixtures:
        print("\nFixtures used but not defined in conftest.py:")
        for fixture in undefined_fixtures:
            print(f"  {fixture} (used in {len(fixture_usage[fixture])} files)")
    
    # Recommendations
    print("\n=== RECOMMENDATIONS ===\n")
    
    if direct_service_importers:
        print("1. Standardize service imports:")
        print("   - Update test files to use fixtures from conftest.py instead of direct imports")
        print("   - Or ensure services/__init__.py exports all necessary functions consistently")
    
    if unused_fixtures:
        print("\n2. Consider removing unused fixtures from conftest.py")
    
    if undefined_fixtures:
        print("\n3. Define commonly used fixtures in conftest.py:")
        for fixture in sorted(undefined_fixtures, key=lambda x: len(fixture_usage[x]), reverse=True)[:5]:
            print(f"   - {fixture} (used in {len(fixture_usage[fixture])} files)")
    
    print("\n4. General recommendations:")
    print("   - Use a single conftest.py to avoid import conflicts")
    print("   - Ensure conftest.py fixtures use consistent naming")
    print("   - Document fixture purposes with clear docstrings")
    print("   - Group related fixtures together")

if __name__ == "__main__":
    analyze_test_imports() 