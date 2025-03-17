#!/usr/bin/env python
"""
Script to fix indentation in the _get_iso_timestamp function
"""
import os
import sys
import re
from pathlib import Path

def find_monitor_health_file():
    """Find the monitor_health.py file"""
    possible_paths = [
        "../services/monitor_health.py",
        "../../services/monitor_health.py",
        "../../../services/monitor_health.py",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "services", "monitor_health.py")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    
    return None

def fix_indentation(file_path):
    """Fix indentation in the _get_iso_timestamp function"""
    print(f"Fixing indentation in: {file_path}")
    
    # Read the file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Create a backup of the original file
    backup_path = f"{file_path}.bak2"
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"Created backup at: {backup_path}")
    
    # Split the content into lines
    lines = content.splitlines()
    
    # Find the _get_iso_timestamp function
    function_start = None
    for i, line in enumerate(lines):
        if 'def _get_iso_timestamp' in line:
            function_start = i
            break
    
    if function_start is None:
        print("Could not find _get_iso_timestamp function")
        return False
    
    # Check if the datetime import line needs indentation
    datetime_import_line = None
    for i in range(function_start, len(lines)):
        if 'from datetime import datetime' in lines[i]:
            datetime_import_line = i
            break
    
    if datetime_import_line is None:
        print("Could not find datetime import line")
        return False
    
    # Check if the line is already properly indented
    if lines[datetime_import_line].startswith('        '):
        print("Datetime import line is already properly indented")
        return True
    
    # Fix the indentation
    lines[datetime_import_line] = '        ' + lines[datetime_import_line].lstrip()
    
    # Check the next line (return statement) as well
    if datetime_import_line + 1 < len(lines) and 'return datetime.now()' in lines[datetime_import_line + 1]:
        if not lines[datetime_import_line + 1].startswith('        '):
            lines[datetime_import_line + 1] = '        ' + lines[datetime_import_line + 1].lstrip()
    
    # Write the modified content back to the file
    with open(file_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"Successfully fixed indentation in {file_path}")
    return True

def main():
    """Main function"""
    print("Starting indentation fix script")
    
    # Find the monitor_health.py file
    monitor_health_path = find_monitor_health_file()
    
    if not monitor_health_path:
        print("Error: Could not find monitor_health.py file")
        sys.exit(1)
    
    print(f"Found monitor_health.py at: {monitor_health_path}")
    
    # Fix indentation
    success = fix_indentation(monitor_health_path)
    
    if success:
        print("Indentation fix applied successfully")
    else:
        print("Failed to apply indentation fix")
        sys.exit(1)
    
    print("Indentation fix script completed")

if __name__ == "__main__":
    main() 