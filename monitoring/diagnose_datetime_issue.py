#!/usr/bin/env python
"""
Diagnostic script to identify issues with datetime import in monitor_health.py
"""
import os
import sys
import inspect
import importlib.util
from pathlib import Path

# Add parent directory to path to allow importing from project
parent_dir = str(Path(__file__).parent.parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    print(f"Added {parent_dir} to Python path")

# Try to import the monitor_health module
try:
    from services.monitor_health import MonitorHealth
    print("Successfully imported MonitorHealth class")
except ImportError as e:
    print(f"Error importing MonitorHealth: {e}")
    sys.exit(1)

def inspect_module_imports(module_path):
    """Inspect a module file to check its imports"""
    print(f"\nInspecting module: {module_path}")
    
    if not os.path.exists(module_path):
        print(f"Error: File {module_path} does not exist")
        return
    
    # Read the file content
    with open(module_path, 'r') as f:
        content = f.read()
    
    # Check for datetime imports
    datetime_imports = []
    for i, line in enumerate(content.splitlines(), 1):
        if 'datetime' in line and ('import' in line or 'from' in line):
            datetime_imports.append((i, line.strip()))
    
    if datetime_imports:
        print("Found datetime imports:")
        for line_num, line in datetime_imports:
            print(f"  Line {line_num}: {line}")
    else:
        print("No datetime imports found in the file")
    
    # Check for _get_iso_timestamp function
    if '_get_iso_timestamp' in content:
        print("\nFound _get_iso_timestamp function:")
        lines = content.splitlines()
        in_function = False
        function_lines = []
        
        for i, line in enumerate(lines, 1):
            if 'def _get_iso_timestamp' in line:
                in_function = True
                function_lines.append((i, line.strip()))
            elif in_function:
                if line.strip() and not line.startswith(' '):
                    in_function = False
                elif line.strip():
                    function_lines.append((i, line.strip()))
        
        for line_num, line in function_lines:
            print(f"  Line {line_num}: {line}")
    else:
        print("\nCould not find _get_iso_timestamp function in the file")

def test_get_iso_timestamp():
    """Test the _get_iso_timestamp method"""
    print("\nTesting _get_iso_timestamp method:")
    
    # Create an instance of MonitorHealth
    try:
        health = MonitorHealth()
        print("Created MonitorHealth instance")
    except Exception as e:
        print(f"Error creating MonitorHealth instance: {e}")
        return
    
    # Try to call _get_iso_timestamp
    try:
        timestamp = health._get_iso_timestamp()
        print(f"Successfully called _get_iso_timestamp, result: {timestamp}")
    except Exception as e:
        print(f"Error calling _get_iso_timestamp: {e}")
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception traceback: {e.__traceback__.tb_lineno}")

def create_patched_function():
    """Create a patched version of the _get_iso_timestamp function"""
    print("\nCreating patched version of _get_iso_timestamp:")
    
    patched_code = """
def _get_iso_timestamp(self):
    \"\"\"Return the current time as an ISO 8601 timestamp\"\"\"
    from datetime import datetime  # Import datetime within function scope
    return datetime.now().isoformat()
"""
    
    print(patched_code)
    
    # Try to monkey patch the function
    try:
        from services.monitor_health import MonitorHealth
        exec(patched_code, globals())
        MonitorHealth._get_iso_timestamp = _get_iso_timestamp
        print("Successfully monkey patched _get_iso_timestamp")
        
        # Test the patched function
        health = MonitorHealth()
        timestamp = health._get_iso_timestamp()
        print(f"Patched function result: {timestamp}")
    except Exception as e:
        print(f"Error patching function: {e}")

def main():
    """Main diagnostic function"""
    print("Starting datetime import diagnostic")
    
    # Find the monitor_health.py file
    possible_paths = [
        "../services/monitor_health.py",
        "../../services/monitor_health.py",
        "../../../services/monitor_health.py",
        os.path.join(parent_dir, "services", "monitor_health.py")
    ]
    
    monitor_health_path = None
    for path in possible_paths:
        if os.path.exists(path):
            monitor_health_path = path
            break
    
    if not monitor_health_path:
        print("Error: Could not find monitor_health.py file")
        sys.exit(1)
    
    print(f"Found monitor_health.py at: {monitor_health_path}")
    
    # Inspect the module
    inspect_module_imports(monitor_health_path)
    
    # Test the function
    test_get_iso_timestamp()
    
    # Create patched function
    create_patched_function()
    
    print("\nDiagnostic complete")

if __name__ == "__main__":
    main() 