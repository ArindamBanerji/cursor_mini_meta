"""
Script to directly fix the _get_iso_timestamp method in monitor_health.py.
This script doesn't rely on regex pattern matching.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("direct_fix")

def fix_timestamp_method():
    """Fix the _get_iso_timestamp method in monitor_health.py"""
    # Get SAP_HARNESS_HOME environment variable
    sap_harness_home = os.environ.get("SAP_HARNESS_HOME")
    if not sap_harness_home:
        logger.error("SAP_HARNESS_HOME environment variable not set")
        return False
    
    logger.info(f"SAP_HARNESS_HOME is set to: {sap_harness_home}")
    
    # Construct the path to monitor_health.py
    file_path = os.path.join(sap_harness_home, "services", "monitor_health.py")
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False
    
    logger.info(f"Found monitor_health.py at: {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Make a backup
    backup_path = f"{file_path}.bak"
    with open(backup_path, 'w') as f:
        f.writelines(lines)
    logger.info(f"Created backup at {backup_path}")
    
    # Find the _get_iso_timestamp method and add the import
    in_method = False
    method_start = -1
    import_added = False
    
    for i, line in enumerate(lines):
        if 'def _get_iso_timestamp' in line:
            in_method = True
            method_start = i
            logger.info(f"Found _get_iso_timestamp method at line {i+1}")
        elif in_method and line.strip() and not line.strip().startswith(' ') and not line.strip().startswith('"'):
            in_method = False
    
    if method_start >= 0:
        # Find the docstring end
        docstring_end = method_start
        for i in range(method_start + 1, len(lines)):
            if '"""' in lines[i] or "'''" in lines[i]:
                docstring_end = i
                break
        
        # Add import after docstring
        import_line = "        from datetime import datetime  # Import datetime within function scope\n"
        
        # Check if import already exists
        for i in range(docstring_end + 1, len(lines)):
            if 'from datetime import datetime' in lines[i]:
                logger.info(f"Import already exists at line {i+1}")
                import_added = True
                break
            if 'return' in lines[i]:
                break
        
        if not import_added:
            lines.insert(docstring_end + 1, import_line)
            logger.info(f"Added import statement after line {docstring_end+1}")
            
            # Write the fixed file
            with open(file_path, 'w') as f:
                f.writelines(lines)
            logger.info(f"Fixed _get_iso_timestamp method in {file_path}")
            return True
        else:
            logger.info("Import statement already exists, no changes needed")
            return True
    else:
        logger.warning("Could not find _get_iso_timestamp method")
        return False

def main():
    """Main function"""
    logger.info("Starting direct_fix.py")
    
    # Fix the timestamp method
    success = fix_timestamp_method()
    if success:
        logger.info("Successfully fixed _get_iso_timestamp method")
    else:
        logger.error("Failed to fix _get_iso_timestamp method")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 