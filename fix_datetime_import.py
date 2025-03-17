#!/usr/bin/env python
"""
Script to fix the datetime import issue in monitor_health.py.

This script:
1. Locates the monitor_health.py file using the SAP_HARNESS_HOME environment variable
2. Finds the _get_iso_timestamp method
3. Adds the datetime import statement within the method
4. Saves the modified file
"""

import os
import re
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fix_datetime_import")

def find_monitor_health_file():
    """Find the monitor_health.py file using SAP_HARNESS_HOME."""
    sap_harness_home = os.environ.get("SAP_HARNESS_HOME")
    if not sap_harness_home:
        logger.error("SAP_HARNESS_HOME environment variable not set")
        return None
    
    logger.info(f"SAP_HARNESS_HOME is set to: {sap_harness_home}")
    
    # Construct the path to monitor_health.py
    file_path = os.path.join(sap_harness_home, "services", "monitor_health.py")
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None
    
    logger.info(f"Found monitor_health.py at: {file_path}")
    return file_path

def fix_datetime_import(file_path):
    """Fix the datetime import in the _get_iso_timestamp method."""
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Create a backup
    backup_path = f"{file_path}.bak"
    with open(backup_path, 'w') as f:
        f.write(content)
    logger.info(f"Created backup at: {backup_path}")
    
    # Find the _get_iso_timestamp method
    method_pattern = r'(def _get_iso_timestamp\(self\)[^\n]*:(?:\s*"""(?:.|\n)*?""")?)(?:\s*)(return datetime\.now\(\)\.isoformat\(\))'
    
    # Check if the method exists
    if not re.search(method_pattern, content, re.DOTALL):
        logger.error("Could not find _get_iso_timestamp method")
        return False
    
    # Check if the import already exists
    if "from datetime import datetime" in content and "def _get_iso_timestamp" in content:
        # Check if the import is within the method
        method_content = re.search(r'def _get_iso_timestamp\(self\)[^\n]*:(?:\s*"""(?:.|\n)*?""")?(?:\s*)(.+?)return', content, re.DOTALL)
        if method_content and "from datetime import datetime" in method_content.group(1):
            logger.info("Import already exists within the method")
            return True
    
    # Add the import statement
    fixed_content = re.sub(
        method_pattern,
        r'\1\n        from datetime import datetime  # Import datetime within function scope\n        \2',
        content,
        flags=re.DOTALL
    )
    
    # Write the fixed content
    with open(file_path, 'w') as f:
        f.write(fixed_content)
    
    logger.info("Added datetime import to _get_iso_timestamp method")
    return True

def main():
    """Main function."""
    logger.info("Starting fix_datetime_import.py")
    
    # Find the monitor_health.py file
    file_path = find_monitor_health_file()
    if not file_path:
        return 1
    
    # Fix the datetime import
    success = fix_datetime_import(file_path)
    if not success:
        logger.error("Failed to fix datetime import")
        return 1
    
    logger.info("Successfully fixed datetime import")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 