# Add path setup to find the tests_dest module
import sys
import os
from pathlib import Path

# Add parent directory to path so Python can find the tests_dest module
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent.parent  # Go up two levels to reach project root
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import helper to fix path issues
from tests_dest.import_helper import fix_imports
fix_imports()

import pytest
import logging
import inspect
from fastapi.testclient import TestClient
from fastapi import Request, Response, FastAPI, HTTPException, Depends
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services from service_imports
from tests_dest.test_helpers.service_imports import (
    BaseService,
    MonitorService, 
    get_monitor_service,
    MaterialService,
    get_material_service
)


"""
Diagnostic Summary for Testing FastAPI Controllers with Dependency Injection

This file summarizes the diagnostic approach, findings, and recommendations
for testing FastAPI controllers that use dependency injection.

Key Findings:
1. FastAPI's Depends objects are created at import time, not at runtime
2. Traditional patching approaches don't work with Depends objects
3. A wrapper function is needed to replace Depends objects with service instances
4. The unwrap_dependencies function provides a clean solution
5. The create_controller_test function simplifies test creation

Recommendations:
1. Use unwrap_dependencies for testing controllers with dependencies
2. Create fixtures for common objects
3. Test error handling and edge cases
4. Document the approach for future developers
"""

def print_diagnostic_summary():
    """Print a summary of the diagnostic findings and recommendations."""
    print("\n=== Diagnostic Summary for Testing FastAPI Controllers ===\n")
    
    print("Problem Statement:")
    print("  FastAPI controllers use dependency injection via Depends objects")
    print("  Traditional patching approaches don't work with Depends objects")
    print("  This makes testing controllers with dependencies challenging")
    
    print("\nRoot Cause:")
    print("  Depends objects are created at import time, not at runtime")
    print("  Patching service getter functions doesn't affect already-created Depends objects")
    print("  Controller functions still receive the original Depends objects as default parameter values")
    
    print("\nSolution:")
    print("  Create a wrapper function that replaces Depends objects with real service objects at call time")
    print("  The unwrap_dependencies function inspects the controller function's signature")
    print("  It identifies parameters with Depends objects as default values")
    print("  It creates a new function that replaces these with real service objects")
    
    print("\nRecommendations:")
    print("  1. Use unwrap_dependencies for testing controllers with dependencies")
    print("  2. Create fixtures for common objects")
    print("  3. Test error handling and edge cases")
    print("  4. Document the approach for future developers")
    
    print("\nExample Usage:")
    print("  # Create wrapped controller with real services")
    print("  wrapped = unwrap_dependencies(")
    print("      list_materials,")
    print("      material_service=get_material_service(),")
    print("      monitor_service=get_monitor_service()")
    print("  )")
    print("  # Call the function")
    print("  result = await wrapped(real_request)")
    
    print("\nAlternative Approach:")
    print("  # Create test function with create_controller_test")
    print("  test_func = create_controller_test(list_materials)")
    print("  # Call the test function")
    print("  result = await test_func(")
    print("      request=real_request,")
    print("      material_service=get_material_service(),")
    print("      monitor_service=get_monitor_service()")
    print("  )")
    
    print("\nDiagnostic Tests Created:")
    print("  1. test_dashboard_diagnostic.py - Simple controllers without dependencies")
    print("  2. test_error_handling_diagnostic.py - Controllers that raise errors")
    print("  3. test_monitor_diagnostic.py - Controllers with service dependencies")
    print("  4. test_dependency_diagnostic.py - Different approaches to handling dependencies")
    print("  5. test_dependency_unwrap.py - Testing the unwrap_dependencies function")
    print("  6. test_dependency_edge_cases.py - Edge cases for dependency unwrapping")
    print("  7. test_controller_diagnostic.py - Comparing different testing approaches")
    print("  8. test_recommended_approach.py - Demonstrating the recommended approach")
    
    print("\n=== End of Diagnostic Summary ===\n")

# Sample controller for demonstration
async def list_materials(
    request: Request,
    material_service = Depends(get_material_service),
    monitor_service = Depends(get_monitor_service)
):
    """Example controller that lists materials."""
    # Use the correct list_materials method from MaterialService
    return {"materials": material_service.list_materials()}

def inspect_controller_parameters():
    """Inspect the parameters of a controller function to demonstrate the issue."""
    print("\n--- Inspecting Controller Parameters ---\n")
    
    # Get the signature of the controller function
    sig = inspect.signature(list_materials)
    
    # Print information about each parameter
    for name, param in sig.parameters.items():
        print(f"Parameter: {name}")
        print(f"  Default: {param.default}")
        print(f"  Annotation: {param.annotation}")
        
        # Check if it's a Depends parameter
        if param.default is not inspect.Parameter.empty and hasattr(param.default, "dependency"):
            print(f"  Is Depends: True")
            print(f"  Dependency: {param.default.dependency}")
            
            # Demonstrate why patching doesn't work
            if param.default.dependency == get_material_service:
                print("\n  Demonstration of why patching doesn't work:")
                print("  1. The Depends object is created at import time")
                print("  2. It contains a reference to the original get_material_service function")
                print("  3. Patching get_material_service later doesn't affect this reference")
                print("  4. The controller still calls the original function via the Depends object")
        else:
            print(f"  Is Depends: False")
        
        print()

def demonstrate_solution():
    """Demonstrate the solution to the dependency injection testing problem."""
    print("\n--- Demonstrating the Solution ---\n")
    
    print("The solution is to create a wrapper function that:")
    print("1. Inspects the controller function's signature")
    print("2. Identifies parameters with Depends objects as default values")
    print("3. Creates a new function that replaces these with real service objects")
    print("4. Calls the original function with the new parameters")
    
    print("\nThis is implemented in the unwrap_dependencies function:")
    print("""
def unwrap_dependencies(func, **services):
    \"\"\"
    Create a wrapper function that replaces Depends objects with real service objects.
    
    Args:
        func: The controller function to wrap
        **services: Mapping of parameter names to service objects
        
    Returns:
        A wrapper function that calls the original function with services
    \"\"\"
    # Get the signature of the function
    sig = inspect.signature(func)
    
    # Create a wrapper function
    async def wrapper(*args, **kwargs):
        # Create a new kwargs dict with services for Depends parameters
        new_kwargs = {}
        
        # Process positional arguments
        parameters = list(sig.parameters.items())
        for i, arg in enumerate(args):
            if i < len(parameters):
                param_name, _ = parameters[i]
                new_kwargs[param_name] = arg
        
        # Process keyword arguments
        for param_name, param in sig.parameters.items():
            # Skip parameters already set by positional args
            if param_name in new_kwargs:
                continue
                
            # If the parameter has a Depends default and we have a service for it
            if (param.default is not inspect.Parameter.empty and 
                hasattr(param.default, "dependency") and
                param_name in services):
                new_kwargs[param_name] = services[param_name]
            # Otherwise use the provided kwarg or default
            elif param_name in kwargs:
                new_kwargs[param_name] = kwargs[param_name]
        
        # Call the original function with the new kwargs
        return await func(**new_kwargs)
    
    return wrapper
""")
    
    print("\nThis solution allows us to test controllers with real dependencies")
    print("without modifying the original controller code.")

def test_unwrap_dependencies():
    """Test the unwrap_dependencies function with real services."""
    # Define the unwrap_dependencies function
    def unwrap_dependencies(func, **services):
        """
        Create a wrapper function that replaces Depends objects with real service objects.
        
        Args:
            func: The controller function to wrap
            **services: Mapping of parameter names to service objects
            
        Returns:
            A wrapper function that calls the original function with services
        """
        # Get the signature of the function
        sig = inspect.signature(func)
        
        # Create a wrapper function
        async def wrapper(*args, **kwargs):
            # Create a new kwargs dict with services for Depends parameters
            new_kwargs = {}
            
            # Process positional arguments
            parameters = list(sig.parameters.items())
            for i, arg in enumerate(args):
                if i < len(parameters):
                    param_name, _ = parameters[i]
                    new_kwargs[param_name] = arg
            
            # Process keyword arguments
            for param_name, param in sig.parameters.items():
                # Skip parameters already set by positional args
                if param_name in new_kwargs:
                    continue
                    
                # If the parameter has a Depends default and we have a service for it
                if (param.default is not inspect.Parameter.empty and 
                    hasattr(param.default, "dependency") and
                    param_name in services):
                    new_kwargs[param_name] = services[param_name]
                # Otherwise use the provided kwarg or default
                elif param_name in kwargs:
                    new_kwargs[param_name] = kwargs[param_name]
            
            # Call the original function with the new kwargs
            return await func(**new_kwargs)
        
        return wrapper
    
    # Create a test request
    app = FastAPI()
    client = TestClient(app)
    scope = {
        "type": "http",
        "path": "/materials",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 50000)
    }
    test_request = Request(scope)
    
    # Get real services
    material_service = get_material_service()
    monitor_service = get_monitor_service()
    
    # Create wrapped controller with real services
    wrapped = unwrap_dependencies(
        list_materials,
        material_service=material_service,
        monitor_service=monitor_service
    )
    
    # Call the wrapped controller
    import asyncio
    result = asyncio.run(wrapped(test_request))
    
    # Verify the result
    assert "materials" in result
    assert isinstance(result["materials"], list)
    
    return True

if __name__ == "__main__":
    print_diagnostic_summary()
    inspect_controller_parameters()
    demonstrate_solution()
    test_unwrap_dependencies()
