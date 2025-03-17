# services/monitor_health_helpers.py
"""
Helper functions for the monitor health module.
This module provides utility functions for system health checks and reporting.
"""

import os
import platform
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logger = logging.getLogger("monitor_health_helpers")

def get_iso_timestamp() -> str:
    """
    Get current time as ISO 8601 timestamp.
    
    Returns:
        ISO formatted timestamp string
    """
    return datetime.now().isoformat()

def calculate_disk_percentages(disk_usage):
    """
    Calculate disk usage percentages.
    
    Args:
        disk_usage: psutil disk usage object
        
    Returns:
        Tuple of (percent_used, percent_free)
    """
    percent_used = disk_usage.percent
    percent_free = 100 - percent_used
    return percent_used, percent_free

def calculate_memory_percentages(memory):
    """
    Calculate memory usage percentages.
    
    Args:
        memory: psutil virtual memory object
        
    Returns:
        Tuple of (percent_used, percent_available)
    """
    percent_used = memory.percent
    percent_available = 100 - percent_used
    return percent_used, percent_available

def get_system_info() -> Dict[str, Any]:
    """
    Get basic system information.
    
    Returns:
        Dictionary with system information
    """
    logger.debug("Getting system info")
    try:
        # Get CPU info
        try:
            import psutil
            cpu_count = psutil.cpu_count(logical=True)
            physical_cpu_count = psutil.cpu_count(logical=False)
        except ImportError:
            cpu_count = None
            physical_cpu_count = None
        
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
            "cpu_count": cpu_count,
            "physical_cpu_count": physical_cpu_count
        }
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}", exc_info=True)
        return {
            "error": str(e)
        }

def is_test_environment() -> bool:
    """
    Check if running in a test environment.
    
    Returns:
        True if in test environment, False otherwise
    """
    return 'PYTEST_CURRENT_TEST' in os.environ

def get_disk_usage_details(disk_usage) -> Dict[str, float]:
    """
    Get disk usage details in a standardized format.
    
    Args:
        disk_usage: psutil disk usage object
        
    Returns:
        Dictionary with disk usage details
    """
    percent_used, percent_free = calculate_disk_percentages(disk_usage)
    
    return {
        "total_gb": round(disk_usage.total / (1024**3), 2),
        "used_gb": round(disk_usage.used / (1024**3), 2),
        "free_gb": round(disk_usage.free / (1024**3), 2),
        "percent_used": round(percent_used, 1),
        "percent_free": round(percent_free, 1)
    }

def get_memory_usage_details(memory) -> Dict[str, float]:
    """
    Get memory usage details in a standardized format.
    
    Args:
        memory: psutil virtual memory object
        
    Returns:
        Dictionary with memory usage details
    """
    percent_used, percent_available = calculate_memory_percentages(memory)
    
    return {
        "total_gb": round(memory.total / (1024**3), 2),
        "available_gb": round(memory.available / (1024**3), 2),
        "used_gb": round(memory.used / (1024**3), 2),
        "percent_used": round(percent_used, 1),
        "percent_available": round(percent_available, 1)
    }

def determine_disk_status(percent_free: float) -> str:
    """
    Determine disk status based on free space percentage.
    
    Args:
        percent_free: Percentage of free disk space
        
    Returns:
        Status string: "error", "warning", or "healthy"
    """
    if percent_free < 5:  # Critical
        status = "error"
        logger.warning(f"Critical disk space: only {percent_free:.1f}% free")
    elif percent_free < 10:  # Warning
        status = "warning"
        logger.warning(f"Low disk space: only {percent_free:.1f}% free")
    else:  # Healthy
        status = "healthy"
        logger.debug(f"Healthy disk space: {percent_free:.1f}% free")
    
    return status

def determine_memory_status(percent_available: float) -> str:
    """
    Determine memory status based on available memory percentage.
    
    Args:
        percent_available: Percentage of available memory
        
    Returns:
        Status string: "error", "warning", or "healthy"
    """
    if percent_available < 5:  # Critical
        status = "error"
        logger.warning(f"Critical memory: only {percent_available:.1f}% available")
    elif percent_available < 15:  # Warning
        status = "warning"
        logger.warning(f"Low memory: only {percent_available:.1f}% available")
    else:  # Healthy
        status = "healthy"
        logger.debug(f"Healthy memory: {percent_available:.1f}% available")
    
    return status

def determine_overall_status(components: List[Dict[str, Any]]) -> Tuple[str, List[str], List[str]]:
    """
    Determine the overall status based on component statuses.
    
    Args:
        components: List of component status dictionaries
        
    Returns:
        Tuple of (overall_status, error_names, warning_names)
    """
    error_components = [c for c in components if c["status"] == "error"]
    warning_components = [c for c in components if c["status"] == "warning"]
    
    error_names = [c.get("name", "unknown") for c in error_components]
    warning_names = [c.get("name", "unknown") for c in warning_components]
    
    if error_components:
        overall_status = "error"
        logger.warning(f"Overall status: error - components with errors: {error_names}")
    elif warning_components:
        overall_status = "warning"
        logger.warning(f"Overall status: warning - components with warnings: {warning_names}")
    else:
        overall_status = "healthy"
        logger.info("Overall status: healthy")
    
    return overall_status, error_names, warning_names
