"""
P2P Controller Import Diagnostic

This script is designed to diagnose issues with the p2p_controller imports and functions.
It checks for missing functions in the controller files that are expected by the tests.
"""

import os
import sys
import inspect
from pathlib import Path

# Add parent directory to path so Python can find the tests_dest module
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent  # Go up two levels to reach project root
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import helper to fix path issues
from tests_dest.import_helper import fix_imports
fix_imports()

def print_separator(text):
    """Print a separator line with text."""
    print("\n" + "=" * 80)
    print(f" {text} ".center(80, "="))
    print("=" * 80 + "\n")

def inspect_module(module_name, print_functions=True):
    """
    Inspect a module and print its functions.
    
    Args:
        module_name: Name of the module to inspect
        print_functions: Whether to print the list of functions
        
    Returns:
        Dictionary of function names to functions
    """
    print(f"Inspecting module: {module_name}")
    
    try:
        # Try to import the module
        module = __import__(module_name, fromlist=["*"])
        
        # Get all functions in the module
        functions = {}
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj):
                # Only include functions defined in this module (not imports)
                if inspect.getmodule(obj).__name__ == module_name:
                    functions[name] = obj
        
        if print_functions:
            print(f"Found {len(functions)} functions defined in {module_name}:")
            for name in sorted(functions.keys()):
                print(f"  - {name}")
        
        # Get all imported functions (re-exports)
        reexports = {}
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj):
                # Only include functions not defined in this module (imports)
                module_of_obj = inspect.getmodule(obj)
                if module_of_obj and module_of_obj.__name__ != module_name:
                    reexports[name] = (obj, module_of_obj.__name__)
        
        if print_functions and reexports:
            print(f"\nFound {len(reexports)} re-exported functions in {module_name}:")
            for name, (obj, origin_module) in sorted(reexports.items()):
                print(f"  - {name} (from {origin_module})")
        
        # Return all functions (both defined and imported)
        all_functions = {**functions, **{name: obj for name, (obj, _) in reexports.items()}}
        
        return all_functions, reexports
        
    except ImportError as e:
        print(f"Error importing module {module_name}: {e}")
        return {}, {}
    except Exception as e:
        print(f"Error inspecting module {module_name}: {e}")
        return {}, {}

def check_test_imports():
    """Check imports in the p2p_requisition_ui.py test file."""
    print_separator("TEST FILE IMPORTS")
    try:
        from tests_dest.api.test_p2p_requisition_ui import TestRequisitionUIEndpoints
        
        # Check what imports the test expects
        import inspect
        test_source = inspect.getsource(TestRequisitionUIEndpoints)
        
        # Look for imports at the top of the file
        import re
        # Extract the import section
        imports_match = re.search(r'from controllers\.p2p_requisition_ui_controller import \((.*?)\)', test_source, re.DOTALL)
        if imports_match:
            imports_text = imports_match.group(1)
            imports = [imp.strip() for imp in imports_text.split(',')]
            print("Test file imports from p2p_requisition_ui_controller:")
            for imp in imports:
                if imp and not imp.isspace():
                    print(f"  - {imp}")
        
        # Look for function calls in the test methods
        function_calls = re.findall(r'result = await (\w+)\(', test_source)
        unique_function_calls = set(function_calls)
        print("\nController functions called in test methods:")
        for func in sorted(unique_function_calls):
            print(f"  - {func}")
            
        # Check if functions exist in various controller files
        print("\nChecking if functions exist in controller files:")
        for func in sorted(unique_function_calls):
            found = False
            
            # Check in p2p_requisition_ui_controller.py
            try:
                import controllers.p2p_requisition_ui_controller
                if hasattr(controllers.p2p_requisition_ui_controller, func):
                    found = True
                    print(f"  - {func}: Found in p2p_requisition_ui_controller.py")
                    continue
            except ImportError:
                pass
            
            # Check in p2p_controller.py
            try:
                import controllers.p2p_controller
                if hasattr(controllers.p2p_controller, func):
                    found = True
                    print(f"  - {func}: Found in p2p_controller.py")
                    continue
            except ImportError:
                pass
            
            # Check in p2p_requisition_api_controller.py
            try:
                import controllers.p2p_requisition_api_controller
                if hasattr(controllers.p2p_requisition_api_controller, func):
                    found = True
                    print(f"  - {func}: Found in p2p_requisition_api_controller.py")
                    continue
            except ImportError:
                pass
                
            if not found:
                print(f"  - {func}: NOT FOUND in any controller file")
        
        return unique_function_calls
    except Exception as e:
        print(f"Error checking test imports: {e}")
        return set()

def analyze_p2p_controller_structure():
    """Analyze the structure of the p2p controller files."""
    print_separator("P2P CONTROLLER STRUCTURE")
    
    # Check the p2p_controller.py file
    _, reexports = inspect_module("controllers.p2p_controller")
    
    # Check what UI functions related to requisitions are re-exported
    req_ui_functions = []
    for name, (_, origin) in reexports.items():
        if origin == "controllers.p2p_requisition_ui_controller":
            req_ui_functions.append(name)
    
    if req_ui_functions:
        print("\nRequisition UI functions re-exported in p2p_controller.py:")
        for func in sorted(req_ui_functions):
            print(f"  - {func}")
    
    # Check the p2p_requisition_ui_controller.py file
    ui_functions, _ = inspect_module("controllers.p2p_requisition_ui_controller")
    
    if ui_functions:
        print("\nFunctions defined in p2p_requisition_ui_controller.py:")
        for name in sorted(ui_functions.keys()):
            print(f"  - {name}")
    
    # Check if any API functions could be used for UI
    api_functions, _ = inspect_module("controllers.p2p_requisition_api_controller", print_functions=False)
    
    if api_functions:
        print("\nRelevant API functions in p2p_requisition_api_controller.py that might be adapted for UI:")
        api_patterns = ['api_submit', 'api_approve', 'api_reject']
        for pattern in api_patterns:
            for name in sorted(api_functions.keys()):
                if pattern in name:
                    print(f"  - {name}")
    
    # Return all the function information
    return {
        "ui_functions": ui_functions,
        "api_functions": api_functions,
        "reexports": reexports
    }

def identify_missing_functions(test_function_calls, controller_info):
    """Identify which functions are missing from the controllers."""
    print_separator("MISSING FUNCTIONS ANALYSIS")
    
    missing_functions = []
    ui_functions = controller_info.get("ui_functions", {})
    api_functions = controller_info.get("api_functions", {})
    
    for func in test_function_calls:
        if func not in ui_functions:
            missing_functions.append(func)
    
    if missing_functions:
        print(f"Found {len(missing_functions)} missing functions:")
        for func in sorted(missing_functions):
            print(f"  - {func}")
            
            # Try to find similar functions in API controller
            similar_api_funcs = []
            for api_func in api_functions.keys():
                if func.replace('submit', 'api_submit') == api_func or \
                   func.replace('approve', 'api_approve') == api_func or \
                   func.replace('reject', 'api_reject') == api_func:
                    similar_api_funcs.append(api_func)
            
            if similar_api_funcs:
                print(f"    Similar API functions: {', '.join(similar_api_funcs)}")
                
    else:
        print("No missing functions found.")
        
    return missing_functions

def check_service_test_helpers():
    """Check what's exposed in the service_imports.py file."""
    print_separator("SERVICE IMPORTS ANALYSIS")
    
    try:
        from tests_dest.test_helpers.service_imports import P2PService
        
        # Check if the p2p_controller is properly imported
        try:
            from tests_dest.test_helpers.service_imports import get_p2p_controller
            print("✅ get_p2p_controller is properly imported")
        except ImportError:
            print("❌ get_p2p_controller is NOT properly imported")
            
        # Check if related API functions are imported
        try:
            from tests_dest.test_helpers.service_imports import api_submit_requisition, api_approve_requisition, api_reject_requisition
            print("✅ API requisition workflow functions are properly imported")
        except ImportError:
            print("❌ API requisition workflow functions are NOT properly imported")
        
        # Check p2p service methods
        import inspect
        p2p_methods = [name for name, _ in inspect.getmembers(P2PService, predicate=inspect.isfunction) 
                      if not name.startswith('_')]
        
        if p2p_methods:
            print("\nP2P Service methods available through service_imports.py:")
            workflow_methods = []
            for method in sorted(p2p_methods):
                if 'submit' in method or 'approve' in method or 'reject' in method:
                    workflow_methods.append(method)
                    print(f"  - {method} ✅")  # Mark workflow-related methods
                else:
                    print(f"  - {method}")
            
            if workflow_methods:
                print("\nP2P Service has the necessary workflow methods that controller should use")
        
    except Exception as e:
        print(f"Error checking service imports: {e}")

def recommend_solution(missing_functions, controller_info):
    """Recommend a solution based on the analysis."""
    print_separator("RECOMMENDED SOLUTION")
    
    if not missing_functions:
        print("No missing functions identified.")
        return
    
    print("Based on the analysis, the following UI controller functions need to be implemented:")
    for func in sorted(missing_functions):
        print(f"  - {func}")
    
    print("\nRecommended approach:")
    print("1. Implement the missing UI controller functions in controllers/p2p_requisition_ui_controller.py")
    print("2. Use the service methods already available in P2PService:")
    
    for func in sorted(missing_functions):
        if 'submit' in func:
            print(f"   - For {func}: Use p2p_service.submit_requisition()")
        elif 'approve' in func:
            print(f"   - For {func}: Use p2p_service.approve_requisition()")
        elif 'reject' in func:
            print(f"   - For {func}: Use p2p_service.reject_requisition()")
    
    print("\n3. Follow the existing patterns in the UI controller for error handling and redirects")
    print("4. Update the imports in p2p_controller.py to re-export the new functions")
    print("\nNote: Do not implement these functions directly in test files or using mocks")

def main():
    """Main function to run the diagnostic."""
    print_separator("P2P CONTROLLER IMPORT DIAGNOSTIC")
    
    # Check what functions the test is trying to import and use
    test_function_calls = check_test_imports()
    
    # Analyze the structure of the p2p controller files
    controller_info = analyze_p2p_controller_structure()
    
    # Check what's exposed in service_imports.py
    check_service_test_helpers()
    
    # Identify which functions are missing
    missing_functions = identify_missing_functions(test_function_calls, controller_info)
    
    # Recommend a solution
    recommend_solution(missing_functions, controller_info)

if __name__ == "__main__":
    main() 