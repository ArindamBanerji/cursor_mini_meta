"""
Diagnostic test to understand the correct import path for RedirectResponse.

This script checks where various controller functions import RedirectResponse from
to help us understand how to correctly patch it in tests.
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

# Import helper to fix imports
from tests_dest.import_helper import fix_imports
fix_imports()

def find_imports_in_function(func):
    """Find imports used in a function."""
    try:
        source = inspect.getsource(func)
        print(f"Source code for {func.__name__}:")
        print(source)
        
        # Check for common patterns
        import re
        fastapi_response = re.search(r'from\s+fastapi\.responses\s+import\s+(\w+)', source, re.MULTILINE)
        redirect_response = re.search(r'(\w+)\s*=\s*RedirectResponse', source, re.MULTILINE)
        
        if fastapi_response:
            print(f"✅ Found direct import from fastapi.responses: {fastapi_response.group(1)}")
        
        if redirect_response:
            print(f"✅ Found RedirectResponse usage: {redirect_response.group(0)}")
            
    except (TypeError, OSError) as e:
        print(f"❌ Cannot get source code for {func.__name__}: {e}")

def check_workflow_function_imports():
    """Check imports in workflow functions."""
    from tests_dest.test_helpers.service_imports import (
        submit_requisition,
        approve_requisition,
        reject_requisition
    )
    
    print("\n==== Checking submit_requisition ====")
    find_imports_in_function(submit_requisition)
    
    print("\n==== Checking approve_requisition ====")
    find_imports_in_function(approve_requisition)
    
    print("\n==== Checking reject_requisition ====")
    find_imports_in_function(reject_requisition)
    
def check_if_imported_from_controller_or_service_imports():
    """Check if functions are imported directly from controller or via service_imports."""
    import tests_dest.api.test_p2p_requisition_ui as test_module
    
    print("\n==== Checking import sources in test file ====")
    
    test_file_source = inspect.getsourcefile(test_module)
    with open(test_file_source, 'r') as f:
        content = f.read()
    
    # Look for direct imports
    direct_import = 'from controllers.p2p_requisition_ui_controller import'
    indirect_import = 'from tests_dest.test_helpers.service_imports import'
    
    if direct_import in content:
        print(f"❌ Test directly imports from controller: {direct_import}")
        
        # Find what's being imported
        import re
        matches = re.search(f"{direct_import}\\s*\\(([^\\)]+)\\)", content, re.DOTALL)
        if matches:
            imports = matches.group(1).strip().split(',')
            imports = [imp.strip() for imp in imports]
            print(f"   Imports: {', '.join(imports)}")
    else:
        print("✅ Test does not directly import from controller")
    
    if indirect_import in content:
        print(f"✅ Test imports from service_imports: {indirect_import}")
        
        # Find what's being imported
        import re
        matches = re.search(f"{indirect_import}\\s*\\(([^\\)]+)\\)", content, re.DOTALL)
        if matches:
            imports = matches.group(1).strip().split(',')
            imports = [imp.strip() for imp in imports]
            print(f"   Imports: {', '.join(imports)}")
    else:
        print(f"❌ Test does not import from service_imports")

def check_patch_usage_in_test():
    """Check how patching is done in the test."""
    import tests_dest.api.test_p2p_requisition_ui as test_module
    
    print("\n==== Checking patch usage in test file ====")
    
    # Look at the test method
    test_class = getattr(test_module, 'TestRequisitionUIEndpoints')
    test_method = getattr(test_class, 'test_submit_requisition')
    
    test_source = inspect.getsource(test_method)
    print("Source code for test_submit_requisition:")
    print(test_source)
    
    # Check what's being patched
    import re
    patch_match = re.search(r'patch\("([^"]+)"', test_source)
    if patch_match:
        patch_path = patch_match.group(1)
        print(f"📌 Test is patching: {patch_path}")
        print(f"   But this may be incorrect if the import is now from service_imports")
    else:
        print("❌ Could not find patch in test")

def print_recommendations():
    """Print recommendations for fixing the tests."""
    print("\n==================================================================")
    print("                      RECOMMENDATIONS                             ")
    print("==================================================================")
    print("Based on the diagnostic results, here's how to fix the tests:")
    print("\n1. Fix the patching in test_submit_requisition:")
    print("   - Current: patch('controllers.p2p_requisition_ui_controller.RedirectResponse')")
    print("   - Should be: patch('fastapi.responses.RedirectResponse')")
    print("\n2. The same change should be applied to test_approve_requisition and test_reject_requisition")
    print("\n3. Ensure all controller functions are imported from service_imports, not directly")
    print("==================================================================")

if __name__ == "__main__":
    print("\n==================================================================")
    print("           REDIRECT RESPONSE PATCHING DIAGNOSTIC                  ")
    print("==================================================================")
    
    # Check imports in workflow functions
    check_workflow_function_imports()
    
    # Check if test imports from controller or service_imports
    check_if_imported_from_controller_or_service_imports()
    
    # Check patch usage in test
    check_patch_usage_in_test()
    
    # Print recommendations
    print_recommendations() 