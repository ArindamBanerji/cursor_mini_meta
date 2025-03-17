# services/monitor_core.py
"""
Core functionality for the monitor service.
This module provides the base MonitorService class and common utilities.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from services.state_manager import state_manager

# Configure logging
logger = logging.getLogger("monitor_core")

class MonitorCore:
    """
    Core functionality for monitoring system health and performance.
    This class provides the foundation for the monitoring system.
    """
    
    def __init__(self, state_manager_instance=None, metrics_max_age_hours=24, max_error_logs=1000):
        """
        Initialize the core monitoring functionality.
        
        Args:
            state_manager_instance: Optional state manager for dependency injection
            metrics_max_age_hours: How many hours of metrics to keep (default: 24)
            max_error_logs: Maximum number of error logs to store (default: 1000)
        """
        self.state_manager = state_manager_instance or state_manager
        self.metrics_max_age_hours = metrics_max_age_hours
        self.max_error_logs = max_error_logs
        
        # Define state keys for different types of data
        self.metrics_key = "system_metrics"
        self.error_logs_key = "error_logs"
        self.component_status_key = "component_status"
        
        # Initialize state if needed
        self._initialize_state()
        logger.info("MonitorCore initialized")
    
    def _initialize_state(self) -> None:
        """
        Initialize state for metrics, error logs, and component status if not already present.
        """
        # Initialize metrics list if not present
        if not self.state_manager.get(self.metrics_key):
            logger.info("Initializing metrics state")
            self.state_manager.set(self.metrics_key, [])
        
        # Initialize error logs list if not present
        if not self.state_manager.get(self.error_logs_key):
            logger.info("Initializing error logs state")
            self.state_manager.set(self.error_logs_key, [])
            
        # Initialize component status dict if not present
        if not self.state_manager.get(self.component_status_key):
            logger.info("Initializing component status state")
            self.state_manager.set(self.component_status_key, {})
    
    def update_component_status(self, component_name: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Update the status of a specific component.
        
        Args:
            component_name: Name of the component
            status: Status string (e.g., "healthy", "warning", "error")
            details: Additional details about the component status
        """
        logger.info(f"Updating component status: {component_name} -> {status}")
        # Get current component status
        component_status = self.state_manager.get(self.component_status_key, {})
        
        # Create component status entry
        component = {
            "name": component_name,
            "status": status,
            "last_check": datetime.now().isoformat(),
            "details": details or {}
        }
        
        # Store in component status dict
        component_status[component_name] = component
        
        # Update state
        self.state_manager.set(self.component_status_key, component_status)
        logger.debug(f"Component status updated: {component_name}")
    
    def get_component_status(self, component_name: Optional[str] = None) -> Any:
        """
        Get status information for one or all components.
        
        Args:
            component_name: Optional name of specific component
            
        Returns:
            Component status information or list of all component statuses
        """
        component_status = self.state_manager.get(self.component_status_key, {})
        
        if component_name:
            status = component_status.get(component_name, {})
            logger.debug(f"Retrieved status for component: {component_name}")
            return status
        
        statuses = list(component_status.values())
        logger.debug(f"Retrieved status for {len(statuses)} components")
        return statuses
    
    def verify_component_health(self, component_name: str) -> Dict[str, Any]:
        """
        Verify the health of a specific component.
        
        Args:
            component_name: The name of the component to check
            
        Returns:
            Health status information for the component
        """
        status = self.get_component_status(component_name)
        
        if not status:
            return {
                "name": component_name,
                "status": "unknown",
                "message": f"Component {component_name} has not reported status"
            }
        
        return {
            "name": component_name,
            "status": status.get("status", "unknown"),
            "last_check": status.get("last_check", "unknown"),
            "details": status.get("details", {})
        }
    
    def ensure_state_initialized(self) -> None:
        """
        Ensure all state is properly initialized.
        This is useful to call before operations to guarantee state exists.
        """
        self._initialize_state()
        
        # Verify each state key is accessible
        metrics = self.state_manager.get(self.metrics_key)
        error_logs = self.state_manager.get(self.error_logs_key)
        component_status = self.state_manager.get(self.component_status_key)
        
        if metrics is None:
            logger.warning("Metrics state was None, reinitializing")
            self.state_manager.set(self.metrics_key, [])
            
        if error_logs is None:
            logger.warning("Error logs state was None, reinitializing")
            self.state_manager.set(self.error_logs_key, [])
            
        if component_status is None:
            logger.warning("Component status state was None, reinitializing")
            self.state_manager.set(self.component_status_key, {})
