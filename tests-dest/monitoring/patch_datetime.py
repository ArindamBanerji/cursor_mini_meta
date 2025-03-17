#!/usr/bin/env python
"""
Script to patch the _get_iso_timestamp function in monitor_health.py
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

def patch_get_iso_timestamp(file_path):
    """Patch the _get_iso_timestamp function to import datetime within the function"""
    print(f"Patching file: {file_path}")
    
    # Read the file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Create a backup of the original file
    backup_path = f"{file_path}.bak"
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"Created backup at: {backup_path}")
    
    # Define the pattern to match the _get_iso_timestamp function
    pattern = r'def _get_iso_timestamp\(self\)[^:]*:.*?return datetime\.now\(\)\.isoformat\(\)'
    
    # Define the replacement with the datetime import
    replacement = """def _get_iso_timestamp(self) -> str:
    """
    replacement += '"""'
    replacement += """
    Get current time as ISO 8601 timestamp.
    
    Returns:
        ISO formatted timestamp string
    """
    replacement += '"""'
    replacement += """
    from datetime import datetime  # Import datetime here to ensure it's available
    return datetime.now().isoformat()"""
    
    # Use regex to find and replace the function
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Check if any changes were made
    if new_content == content:
        print("Warning: No changes were made to the file. Function pattern not found.")
        
        # Try a more specific approach - find the function and replace it line by line
        lines = content.splitlines()
        function_start = None
        function_end = None
        
        for i, line in enumerate(lines):
            if 'def _get_iso_timestamp' in line:
                function_start = i
            elif function_start is not None and 'return datetime.now().isoformat()' in line:
                function_end = i
                break
        
        if function_start is not None and function_end is not None:
            print(f"Found function from line {function_start+1} to {function_end+1}")
            
            # Replace the function
            new_lines = lines[:function_start]
            new_lines.append('    def _get_iso_timestamp(self) -> str:')
            new_lines.append('        """')
            new_lines.append('        Get current time as ISO 8601 timestamp.')
            new_lines.append('        ')
            new_lines.append('        Returns:')
            new_lines.append('            ISO formatted timestamp string')
            new_lines.append('        """')
            new_lines.append('        from datetime import datetime  # Import datetime here to ensure it\'s available')
            new_lines.append('        return datetime.now().isoformat()')
            new_lines.extend(lines[function_end+1:])
            
            new_content = '\n'.join(new_lines)
            print("Successfully replaced function using line-by-line approach")
        else:
            print("Could not find function start and end lines")
            return False
    
    # Write the modified content back to the file
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print(f"Successfully patched {file_path}")
    return True

def main():
    """Main function"""
    print("Starting patch script")
    
    # Find the monitor_health.py file
    monitor_health_path = find_monitor_health_file()
    
    if not monitor_health_path:
        print("Error: Could not find monitor_health.py file")
        sys.exit(1)
    
    print(f"Found monitor_health.py at: {monitor_health_path}")
    
    # Patch the file
    success = patch_get_iso_timestamp(monitor_health_path)
    
    if success:
        print("Patch applied successfully")
    else:
        print("Failed to apply patch")
        sys.exit(1)
    
    print("Patch script completed")

if __name__ == "__main__":
    main()
