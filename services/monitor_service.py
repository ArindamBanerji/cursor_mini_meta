# services/monitor_service.py
"""
Monitoring service for the SAP Test Harness.

This service provides functionality for monitoring system health,
collecting performance metrics, and tracking errors.

This is the main entry point that integrates specialized modules:
- MonitorCore: Core data structures and state management
- MonitorMetrics: System metrics collection and analysis
- MonitorHealth: System health checks and reporting
- MonitorErrors: Error logging and retrieval
"""

import logging
from typing import Dict, Any, Optional, List, Union

from services.state_manager import state_manager
from services.monitor_core import MonitorCore
from services.monitor_metrics import MonitorMetrics, SystemMetrics
from services.monitor_health import MonitorHealth
from services.monitor_errors import MonitorErrors, ErrorLog

# Configure logging
logger = logging.getLogger("monitor_service")

class MonitorService:
    """
    Service for monitoring system health and performance.
    Provides health checks, metrics collection, and error logging.
    
    This class integrates the specialized monitoring modules to provide
    a unified interface for all monitoring functionality.
    """
    
    def __init__(self, state_manager_instance=None, metrics_max_age_hours=24, max_error_logs=1000):
        """
        Initialize the monitoring service.
        
        Args:
            state_manager_instance: Optional state manager for dependency injection
            metrics_max_age_hours: How many hours of metrics to keep
            max_error_logs: Maximum number of error logs to store
        """
        # Initialize the core module first
        self.core = MonitorCore(
            state_manager_instance or state_manager, 
            metrics_max_age_hours,
            max_error_logs
        )
        
        # State manager reference for convenience
        self.state_manager = self.core.state_manager
        
        # Initialize specialized modules
        self.metrics = MonitorMetrics(self.core)
        self.health = MonitorHealth(self.core)
        self.errors = MonitorErrors(self.core)
        
        logger.info("MonitorService initialized")
    
    # ==== Core methods for accessing state (delegated to core) ====
    
    def update_component_status(self, component_name: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Update the status of a specific component.
        
        Args:
            component_name: Name of the component
            status: Status string (e.g., "healthy", "warning", "error")
            details: Additional details about the component status
        """
        self.core.update_component_status(component_name, status, details)
    
    def get_component_status(self, component_name: Optional[str] = None):
        """
        Get status information for one or all components.
        
        Args:
            component_name: Optional name of specific component
            
        Returns:
            Component status information
        """
        return self.core.get_component_status(component_name)
    
    # ==== Health check methods (delegated to health) ====
    
    def check_system_health(self) -> Dict[str, Any]:
        """
        Perform a comprehensive system health check.
        
        Returns:
            Dictionary with health check results
        """
        return self.health.check_system_health()
    
    # ==== Metrics methods (delegated to metrics) ====
    
    def collect_current_metrics(self) -> SystemMetrics:
        """
        Collect current system metrics.
        
        Returns:
            SystemMetrics instance with current metrics
        """
        return self.metrics.collect_current_metrics()
    
    def get_metrics(self, hours: Optional[int] = None) -> List[SystemMetrics]:
        """
        Get system metrics for specified time period.
        
        Args:
            hours: Number of hours to look back (None for all available)
            
        Returns:
            List of SystemMetrics objects
        """
        return self.metrics.get_metrics(hours)
    
    def get_metrics_summary(self, hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Get a summary of system metrics.
        
        Args:
            hours: Number of hours to look back (None for all available)
            
        Returns:
            Dictionary with metrics summary
        """
        return self.metrics.get_metrics_summary(hours)
    
    # ==== Error logging methods (delegated to errors) ====
    
    def log_error(self, 
                  error_type: str, 
                  message: str, 
                  component: Optional[str] = None,
                  context: Optional[Dict[str, Any]] = None) -> ErrorLog:
        """
        Log an error in the system.
        
        Args:
            error_type: Type of error (e.g., "validation", "database", "system")
            message: Error message
            component: Component where the error occurred
            context: Additional context information
            
        Returns:
            ErrorLog object that was created
        """
        return self.errors.log_error(error_type, message, component, context)
    
    def get_error_logs(self, 
                       error_type: Optional[str] = None, 
                       component: Optional[str] = None,
                       hours: Optional[int] = None,
                       limit: Optional[int] = None) -> List[ErrorLog]:
        """
        Get error logs with optional filtering.
        
        Args:
            error_type: Optional filter by error type
            component: Optional filter by component
            hours: Optional time limit in hours
            limit: Optional maximum number of logs to return
            
        Returns:
            List of ErrorLog objects
        """
        return self.errors.get_error_logs(error_type, component, hours, limit)
    
    def get_error_summary(self, hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Get a summary of error logs.
        
        Args:
            hours: Number of hours to look back (None for all available)
            
        Returns:
            Dictionary with error summary
        """
        return self.errors.get_error_summary(hours)
    
    def clear_error_logs(self) -> int:
        """
        Clear all error logs.
        
        Returns:
            Number of logs cleared
        """
        return self.errors.clear_error_logs()

# Create a singleton instance
monitor_service = MonitorService()

# Add a log message confirming singleton creation
logger.info(f"Monitor service singleton created with state_manager={id(monitor_service.state_manager)}")

# Add the get_monitor_service function that's missing and causing the import error
def get_monitor_service():
    """
    Get the singleton instance of the monitor service.
    
    Returns:
        The global monitor_service instance
    """
    global monitor_service
    return monitor_service
