#!/usr/bin/env python
"""
Diagnostic script to recreate and demonstrate the datetime import issue.

This script creates a simplified version of the MonitorHealth class with the
_get_iso_timestamp method that has the same issue as in the original code.
"""

import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("datetime_diagnostic")

class MonitorHealth:
    """Simplified MonitorHealth class to demonstrate the datetime import issue."""
    
    def perform_health_check(self):
        """Perform a health check and return the results."""
        logger.info("Performing health check")
        
        try:
            # Get timestamp using the problematic method
            timestamp = self._get_iso_timestamp()
            logger.info(f"Health check timestamp: {timestamp}")
            
            return {
                "status": "healthy",
                "timestamp": timestamp,
                "components": {
                    "example": "ok"
                }
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def _get_iso_timestamp(self):
        """
        Get current time as ISO 8601 timestamp.
        
        Returns:
            ISO formatted timestamp string
        """
        # The issue: datetime is not imported here
        return datetime.now().isoformat()  # This will raise NameError

class FixedMonitorHealth(MonitorHealth):
    """Fixed version of MonitorHealth with proper datetime import."""
    
    def _get_iso_timestamp(self):
        """
        Get current time as ISO 8601 timestamp.
        
        Returns:
            ISO formatted timestamp string
        """
        # The fix: import datetime within the method
        from datetime import datetime
        return datetime.now().isoformat()

def test_original_implementation():
    """Test the original implementation with the datetime issue."""
    logger.info("Testing original implementation (should fail)")
    
    try:
        health = MonitorHealth()
        result = health.perform_health_check()
        logger.info(f"Result: {result}")
        return True
    except Exception as e:
        logger.error(f"Test failed as expected: {str(e)}")
        return False

def test_fixed_implementation():
    """Test the fixed implementation with proper datetime import."""
    logger.info("Testing fixed implementation (should succeed)")
    
    try:
        health = FixedMonitorHealth()
        result = health.perform_health_check()
        logger.info(f"Result: {result}")
        return True
    except Exception as e:
        logger.error(f"Test failed unexpectedly: {str(e)}")
        return False

def main():
    """Main function to run the diagnostic tests."""
    logger.info("Starting datetime import diagnostic")
    
    # Test original implementation (should fail)
    original_success = test_original_implementation()
    
    # Add a separator
    logger.info("-" * 50)
    
    # Test fixed implementation (should succeed)
    fixed_success = test_fixed_implementation()
    
    # Print summary
    logger.info("-" * 50)
    logger.info("Diagnostic Summary:")
    logger.info(f"Original implementation: {'PASSED (unexpected)' if original_success else 'FAILED (expected)'}")
    logger.info(f"Fixed implementation: {'PASSED (expected)' if fixed_success else 'FAILED (unexpected)'}")
    
    # Explain the issue and solution
    logger.info("\nExplanation:")
    logger.info("The original implementation fails because it tries to use 'datetime' without importing it.")
    logger.info("The fixed implementation works because it imports 'datetime' within the method scope.")
    logger.info("\nSolution:")
    logger.info("Add 'from datetime import datetime' inside the _get_iso_timestamp method.")
    
    return 0 if fixed_success else 1

if __name__ == "__main__":
    sys.exit(main()) 