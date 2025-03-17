"""
Script to patch the monitor_controller.py file.

This script replaces all instances of direct access to request.client.host
with get_safe_client_host(request).
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
logger = logging.getLogger("patch_controller")

def find_controller_file():
    """Find the monitor_controller.py file"""
    # Get SAP_HARNESS_HOME environment variable
    sap_harness_home = os.environ.get("SAP_HARNESS_HOME")
    if not sap_harness_home:
        logger.warning("SAP_HARNESS_HOME environment variable not set")
    else:
        logger.info(f"SAP_HARNESS_HOME is set to: {sap_harness_home}")
    
    # Try different paths
    possible_paths = [
        "../controllers/monitor_controller.py",
        "../../controllers/monitor_controller.py",
        "../../../controllers/monitor_controller.py",
        "../../../../controllers/monitor_controller.py",
    ]
    
    # Add path using SAP_HARNESS_HOME if available
    if sap_harness_home:
        sap_path = os.path.join(sap_harness_home, "controllers", "monitor_controller.py")
        possible_paths.insert(0, sap_path)  # Add as first priority
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found controller file at {path}")
            return path
    
    logger.error("Could not find controller file")
    return None

def patch_controller_file(file_path):
    """Patch the controller file"""
    logger.info(f"Patching controller file at {file_path}")
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Make a backup
    backup_path = f"{file_path}.bak"
    with open(backup_path, 'w') as f:
        f.write(content)
    logger.info(f"Created backup at {backup_path}")
    
    # Replace direct access to request.client.host with get_safe_client_host(request)
    # Pattern 1: request.client.host
    pattern1 = r'request\.client\.host'
    replacement1 = 'get_safe_client_host(request)'
    
    # Pattern 2: request.client.host if hasattr(request, 'client') else 'unknown'
    pattern2 = r"request\.client\.host if hasattr\(request, 'client'\) else 'unknown'"
    replacement2 = 'get_safe_client_host(request)'
    
    # Count occurrences
    count1 = len(re.findall(pattern1, content))
    count2 = len(re.findall(pattern2, content))
    logger.info(f"Found {count1} occurrences of {pattern1}")
    logger.info(f"Found {count2} occurrences of {pattern2}")
    
    # Replace pattern 2 first (more specific)
    content = re.sub(pattern2, replacement2, content)
    
    # Then replace pattern 1 (more general)
    content = re.sub(pattern1, replacement1, content)
    
    # Write the patched file
    with open(file_path, 'w') as f:
        f.write(content)
    logger.info(f"Patched {count1 + count2} occurrences in {file_path}")
    
    return count1 + count2

def main():
    """Main function"""
    logger.info("Starting patch_controller.py")
    
    # Find the controller file
    controller_path = find_controller_file()
    if not controller_path:
        logger.error("Could not find controller file")
        return 1
    
    # Patch the controller file
    count = patch_controller_file(controller_path)
    if count == 0:
        logger.warning("No occurrences found to patch")
    else:
        logger.info(f"Successfully patched {count} occurrences")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 