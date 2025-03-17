"""
Script to fix the _get_iso_timestamp method in monitor_health.py.
"""

import os
import re
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fix_timestamp_method")

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
        content = f.read()
    
    # Make a backup
    backup_path = f"{file_path}.bak"
    with open(backup_path, 'w') as f:
        f.write(content)
    logger.info(f"Created backup at {backup_path}")
    
    # Find the _get_iso_timestamp method
    pattern = r'def _get_iso_timestamp\(self\).*?return datetime\.now\(\)\.isoformat\(\)'
    
    # Count occurrences
    count = len(re.findall(pattern, content, re.DOTALL))
    logger.info(f"Found {count} occurrences of _get_iso_timestamp method")
    
    if count == 0:
        # Try a more general pattern
        pattern = r'def _get_iso_timestamp\(self\).*?return.*?\.isoformat\(\)'
        count = len(re.findall(pattern, content, re.DOTALL))
        logger.info(f"Using more general pattern, found {count} occurrences")
        
        if count == 0:
            logger.warning("Could not find _get_iso_timestamp method")
            
            # Print a portion of the file to help debug
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if '_get_iso_timestamp' in line:
                    start = max(0, i-5)
                    end = min(len(lines), i+15)
                    logger.info(f"Found reference to _get_iso_timestamp at line {i+1}:")
                    for j in range(start, end):
                        logger.info(f"  Line {j+1}: {lines[j]}")
            
            return False
    
    # Replace with fixed method
    fixed_method = """def _get_iso_timestamp(self):
        \"\"\"Return the current time as an ISO 8601 timestamp\"\"\"
        from datetime import datetime  # Import datetime within function scope
        return datetime.now().isoformat()"""
    
    new_content = re.sub(pattern, fixed_method, content, flags=re.DOTALL)
    
    # Write the fixed file
    with open(file_path, 'w') as f:
        f.write(new_content)
    logger.info(f"Fixed _get_iso_timestamp method in {file_path}")
    
    return True

def main():
    """Main function"""
    logger.info("Starting fix_timestamp_method.py")
    
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