"""
Diagnostic test for service initialization and module structure.

This script analyzes:
1. What service instances are exposed by each service module
2. How service factories and singletons are defined
3. Import dependencies between services
4. Inconsistencies in module structure

Run this with: python -m tests-dest.service_initialization_diagnostic
"""

import os
import sys
import inspect
import importlib
import logging
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Any, Tuple, Optional, Set

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("service_diagnostic")

# Ensure project root is in sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

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

def analyze_module(module_name: str) -> Dict[str, Any]:
    """
    Analyze a module for service instances, factories, and other attributes.
    
    Args:
        module_name: Full name of the module to analyze
        
    Returns:
        Dictionary with analysis results
    """
    result = {
        "module_name": module_name,
        "can_import": False,
        "error": None,
        "service_instances": [],
        "factory_functions": [],
        "exported_names": [],
        "dependencies": [],
    }
    
    # Try to import the module
    module, error = safe_import(module_name)
    if error:
        result["error"] = str(error)
        return result
    
    result["can_import"] = True
    
    # Get module attributes
    for name, obj in inspect.getmembers(module):
        # Skip private attributes
        if name.startswith('_') and name != '__all__':
            continue
        
        # Special handling for __all__
        if name == '__all__':
            result["exported_names"] = obj
            continue
        
        # Classify objects
        if inspect.isfunction(obj):
            # Check if it's a factory function (returns service instance)
            if name.startswith('get_') and 'service' in name.lower():
                result["factory_functions"].append(name)
        elif not inspect.ismodule(obj) and not inspect.isfunction(obj) and not inspect.isclass(obj):
            # Check if it might be a service instance
            obj_type = type(obj).__name__
            if 'Service' in obj_type:
                result["service_instances"].append(name)
    
    # Get dependencies from imports
    for name, obj in inspect.getmembers(module):
        if inspect.ismodule(obj) and obj.__name__.startswith('services.'):
            result["dependencies"].append(obj.__name__)
    
    return result

def check_services_init() -> Dict[str, Any]:
    """
    Check the services/__init__.py file for proper exports.
    
    Returns:
        Dictionary with analysis results
    """
    module_name = "services"
    result = {
        "module_name": module_name,
        "can_import": False,
        "error": None,
        "exports": {},
        "missing_exports": [],
        "expected_exports": [
            "get_monitor_service", 
            "get_material_service", 
            "get_p2p_service",
            "register_service",
            "clear_service_registry",
            "reset_services"
        ]
    }
    
    # Try to import the module
    module, error = safe_import(module_name)
    if error:
        result["error"] = str(error)
        return result
    
    result["can_import"] = True
    
    # Check what's actually exported
    for name in result["expected_exports"]:
        if hasattr(module, name):
            result["exports"][name] = "available"
        else:
            result["missing_exports"].append(name)
            result["exports"][name] = "missing"
    
    return result

def check_all_services():
    """Check all service modules and print a report."""
    logger.info("=== Service Module Diagnostic Report ===")
    
    # Set environment variables
    set_env_vars()
    
    # Services to check
    services = [
        "services",
        "services.monitor_service",
        "services.material_service",
        "services.p2p_service",
        "services.state_manager"
    ]
    
    # Analyze each service
    results = {}
    for service_name in services:
        logger.info(f"Analyzing {service_name}...")
        if service_name == "services":
            results[service_name] = check_services_init()
        else:
            results[service_name] = analyze_module(service_name)
    
    # Print the results
    print("\n=== DIAGNOSTIC RESULTS ===\n")
    
    # Check services/__init__.py first
    init_result = results["services"]
    print(f"services/__init__.py status: {'OK' if init_result['can_import'] else 'ERROR'}")
    if init_result["error"]:
        print(f"  Error: {init_result['error']}")
    
    print("\nExported functions in services/__init__.py:")
    for name, status in init_result["exports"].items():
        print(f"  {name}: {status}")
    
    if init_result["missing_exports"]:
        print("\nMISSING EXPORTS:")
        for name in init_result["missing_exports"]:
            print(f"  {name}")
    
    # Then check individual service modules
    print("\nIndividual Service Modules:")
    for service_name, result in results.items():
        if service_name == "services":
            continue
            
        status = "OK" if result["can_import"] else "ERROR"
        print(f"\n{service_name}: {status}")
        
        if result["error"]:
            print(f"  Error: {result['error']}")
            continue
        
        if result["service_instances"]:
            print("  Service Instances:")
            for name in result["service_instances"]:
                print(f"    {name}")
        else:
            print("  No service instances found")
            
        if result["factory_functions"]:
            print("  Factory Functions:")
            for name in result["factory_functions"]:
                print(f"    {name}")
        else:
            print("  No factory functions found")
            
        if result["dependencies"]:
            print("  Service Dependencies:")
            for name in result["dependencies"]:
                print(f"    {name}")
    
    # Analyze inconsistencies
    print("\n=== INCONSISTENCIES ===\n")
    
    # Check naming patterns
    service_instances = {}
    factory_functions = {}
    
    for service_name, result in results.items():
        if service_name == "services" or not result["can_import"]:
            continue
            
        for instance in result["service_instances"]:
            service_instances[instance] = service_name
            
        for factory in result["factory_functions"]:
            factory_functions[factory] = service_name
    
    # Check expected patterns
    for service_name, result in results.items():
        if service_name == "services" or not result["can_import"]:
            continue
            
        base_name = service_name.split(".")[-1]
        expected_instance = base_name
        expected_factory = f"get_{base_name}"
        
        # Special case for state_manager
        if base_name == "state_manager":
            expected_instance = "state_manager"
            expected_factory = "get_state_manager"
        
        if expected_instance not in result["service_instances"]:
            print(f"MISSING: {service_name} should expose a '{expected_instance}' instance")
            
        if expected_factory not in result["factory_functions"]:
            print(f"MISSING: {service_name} should provide a '{expected_factory}' factory function")
    
    print("\n=== RECOMMENDATIONS ===\n")
    
    if init_result["missing_exports"]:
        print("1. Update services/__init__.py to export the following missing functions:")
        for name in init_result["missing_exports"]:
            print(f"   - {name}")
    
    inconsistent_modules = []
    for service_name, result in results.items():
        if service_name == "services" or not result["can_import"]:
            continue
            
        base_name = service_name.split(".")[-1]
        expected_instance = base_name
        expected_factory = f"get_{base_name}"
        
        # Special case for state_manager
        if base_name == "state_manager":
            expected_instance = "state_manager"
            expected_factory = "get_state_manager"
        
        if (expected_instance not in result["service_instances"] or 
            expected_factory not in result["factory_functions"]):
            inconsistent_modules.append(service_name)
    
    if inconsistent_modules:
        print("\n2. Standardize these service modules:")
        for module in inconsistent_modules:
            base_name = module.split(".")[-1]
            print(f"   - {module}: Should expose '{base_name}' instance and 'get_{base_name}' factory")
    
    print("\n3. Ensure all service modules follow the same pattern:")
    print("   - Create a singleton instance: service_name = ServiceClass(...)")
    print("   - Provide a getter function: get_service_name() that returns the singleton")
    print("   - Export both in __all__ list")
    
    print("\n4. Update services/__init__.py to re-export all service getters and utilities")

if __name__ == "__main__":
    check_all_services() 