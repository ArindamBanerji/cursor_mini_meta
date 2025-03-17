# services/monitor_helpers.py
"""
Helper module for the Monitor Service.

Contains shared data structures and utility functions used by all monitor modules.
This module has been updated to align with the refactored monitor service architecture.
"""

import os
import platform
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union

# Configure logging
logger = logging.getLogger("monitor_helpers")

def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format a datetime object as ISO 8601 string.
    
    Args:
        dt: Datetime object to format (default: current time)
        
    Returns:
        ISO 8601 formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()

def parse_timestamp(timestamp_str: Optional[str]) -> Optional[datetime]:
    """
    Parse an ISO 8601 timestamp string to datetime.
    Handles parsing errors gracefully.
    
    Args:
        timestamp_str: ISO 8601 timestamp string
        
    Returns:
        Datetime object or None if parsing fails
    """
    if not timestamp_str:
        return None
        
    try:
        return datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse timestamp '{timestamp_str}': {str(e)}")
        return None

def filter_by_time(items: List[Dict[str, Any]], 
                  hours: Optional[int], 
                  timestamp_key: str = "timestamp") -> List[Dict[str, Any]]:
    """
    Filter a list of items by timestamp.
    
    Args:
        items: List of dictionaries containing timestamp values
        hours: Number of hours to look back (None for all items)
        timestamp_key: Key for the timestamp value in the dictionaries
        
    Returns:
        Filtered list of items
    """
    if hours is None:
        return items
        
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        filtered_items = []
        
        for item in items:
            timestamp_str = item.get(timestamp_key)
            timestamp = parse_timestamp(timestamp_str)
            
            if timestamp and timestamp > cutoff_time:
                filtered_items.append(item)
            
        return filtered_items
    except Exception as e:
        logger.error(f"Error filtering items by time: {str(e)}")
        return items  # Return original items on error

def standardize_error_context(context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Standardize error context dictionaries to ensure they're JSON-serializable.
    
    Args:
        context: Original context dictionary or None
        
    Returns:
        Standardized context dictionary
    """
    if context is None:
        return {}
    
    # Create a new dictionary to avoid modifying the original
    result = {}
    
    for key, value in context.items():
        # Convert non-serializable types to strings
        if isinstance(value, datetime):
            result[key] = format_timestamp(value)
        elif isinstance(value, (set, frozenset)):
            result[key] = list(value)
        elif hasattr(value, '__dict__'):
            # Handle custom objects
            result[key] = str(value)
        else:
            result[key] = value
    
    return result

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
        logger.error(f"Error getting system info: {str(e)}")
        return {
            "error": str(e)
        }

def get_test_environment_values() -> Dict[str, Any]:
    """
    Get values to use in test environments.
    
    Returns:
        Dictionary of test values
    """
    return {
        "metrics": {
            "cpu_percent": 40.0,
            "memory_usage": 40.0,
            "available_memory": 12.0,
            "disk_usage": 40.0
        },
        "disk": {
            "total_gb": 100.0,
            "used_gb": 50.0,
            "free_gb": 50.0,
            "percent_used": 50.0,
            "percent_free": 50.0
        },
        "memory": {
            "total_gb": 16.0,
            "available_gb": 8.0,
            "used_gb": 8.0,
            "percent_used": 50.0,
            "percent_available": 50.0
        }
    }

def is_test_environment() -> bool:
    """
    Check if we're running in a test environment.
    
    Returns:
        True if we're in a test environment, False otherwise
    """
    return 'PYTEST_CURRENT_TEST' in os.environ

def safe_dict_get(d: Optional[Dict[str, Any]], key: str, default: Any = None) -> Any:
    """
    Safely get a value from a dictionary that might be None.
    
    Args:
        d: Dictionary to get value from (or None)
        key: Key to get value for
        default: Default value if dictionary is None or key is missing
        
    Returns:
        Value from dictionary or default
    """
    if d is None:
        return default
    return d.get(key, default)

def calculate_averages(metrics_list: List[Dict[str, Any]], 
                      keys: List[str]) -> Dict[str, float]:
    """
    Calculate averages for specific keys in a list of metrics dictionaries.
    
    Args:
        metrics_list: List of metrics dictionaries
        keys: Keys to calculate averages for
        
    Returns:
        Dictionary mapping keys to their average values
    """
    if not metrics_list:
        return {key: 0 for key in keys}
    
    averages = {}
    for key in keys:
        values = []
        for metrics in metrics_list:
            value = safe_dict_get(metrics, key)
            if value is not None and isinstance(value, (int, float)):
                values.append(value)
        
        if values:
            averages[key] = sum(values) / len(values)
        else:
            averages[key] = 0
    
    return averages

def calculate_max_values(metrics_list: List[Dict[str, Any]], 
                        keys: List[str]) -> Dict[str, float]:
    """
    Calculate maximum values for specific keys in a list of metrics dictionaries.
    
    Args:
        metrics_list: List of metrics dictionaries
        keys: Keys to calculate maximums for
        
    Returns:
        Dictionary mapping keys to their maximum values
    """
    if not metrics_list:
        return {key: 0 for key in keys}
    
    maximums = {}
    for key in keys:
        values = []
        for metrics in metrics_list:
            value = safe_dict_get(metrics, key)
            if value is not None and isinstance(value, (int, float)):
                values.append(value)
        
        if values:
            maximums[key] = max(values)
        else:
            maximums[key] = 0
    
    return maximums