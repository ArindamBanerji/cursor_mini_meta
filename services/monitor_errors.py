# services/monitor_errors.py
"""
Error logging functionality for the monitor service.
This module provides functions for logging and retrieving error information.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union

# Configure logging
logger = logging.getLogger("monitor_errors")

class ErrorLog:
    """
    Error log entry data structure.
    """
    def __init__(self, 
                 error_type: str, 
                 message: str, 
                 timestamp: Optional[datetime] = None,
                 component: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
        self.error_type: str = error_type
        self.message: str = message
        self.timestamp: datetime = timestamp or datetime.now()
        self.component: Optional[str] = component
        self.context: Dict[str, Any] = context or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert error log to dictionary for storage"""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "component": self.component,
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorLog':
        """Create error log from dictionary"""
        try:
            # Handle timestamp conversion safely
            timestamp = data.get("timestamp")
            if timestamp:
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except (ValueError, TypeError):
                    timestamp = datetime.now()
            else:
                timestamp = datetime.now()
                
            return cls(
                error_type=data.get("error_type", "unknown"),
                message=data.get("message", "No message provided"),
                timestamp=timestamp,
                component=data.get("component"),
                context=data.get("context", {})
            )
        except Exception as e:
            logger.error(f"Error converting log from dictionary: {str(e)}")
            # Return a placeholder error log
            return cls(
                error_type="parse_error",
                message=f"Failed to parse error log: {str(e)}",
                component="monitor_errors"
            )

class MonitorErrors:
    """
    Error logging and retrieval for the monitoring system.
    """
    
    def __init__(self, monitor_core):
        """
        Initialize the error logging functionality.
        
        Args:
            monitor_core: The MonitorCore instance
        """
        self.core = monitor_core
        self.state_manager = monitor_core.state_manager
        self.error_logs_key = monitor_core.error_logs_key
        self.max_error_logs = monitor_core.max_error_logs
        logger.info("MonitorErrors initialized")
    
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
        logger.error(f"Error logged: [{error_type}] {message} (component: {component})")
        
        # Ensure state is initialized before logging
        self.core.ensure_state_initialized()
        
        # Create error log
        error_log = ErrorLog(
            error_type=error_type,
            message=message,
            component=component,
            context=context or {}
        )
        
        # Store error log with reliable storage
        try:
            self._store_error_log(error_log)
        except Exception as e:
            # If storage fails, try one more time after re-initialization
            logger.warning(f"Error storing log, attempting recovery: {str(e)}")
            self.core.ensure_state_initialized()
            self._store_error_log(error_log)
        
        return error_log
    
    def _store_error_log(self, error_log: ErrorLog) -> None:
        """
        Store error log in state manager with improved reliability.
        
        Args:
            error_log: ErrorLog to store
        """
        # Get current error logs directly from state manager
        current_logs = self.state_manager.get(self.error_logs_key, [])
        if current_logs is None:
            logger.warning("Error logs state was None, initializing empty list")
            current_logs = []
        
        # Create a copy of the list to avoid modifying the original reference
        updated_logs = current_logs.copy() if isinstance(current_logs, list) else []
        
        # Convert error log to dict for storage
        error_log_dict = error_log.to_dict()
        
        # Add new log to the beginning for easier access to recent logs
        updated_logs.insert(0, error_log_dict)
        
        # Limit size of log history
        if len(updated_logs) > self.max_error_logs:
            updated_logs = updated_logs[:self.max_error_logs]
        
        # Save updated logs in state
        self.state_manager.set(self.error_logs_key, updated_logs)
        
        # Verify storage succeeded
        stored_logs = self.state_manager.get(self.error_logs_key, [])
        log_count = len(stored_logs) if stored_logs else 0
        logger.debug(f"Stored error log, now have {log_count} records")
    
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
        logger.info(f"Retrieving error logs (type: {error_type}, component: {component}, hours: {hours}, limit: {limit})")
        
        # Ensure state is initialized before retrieving logs
        self.core.ensure_state_initialized()
        
        # Get stored logs directly from state manager
        stored_logs = self.state_manager.get(self.error_logs_key, [])
        if stored_logs is None:
            logger.warning("Error logs state was None, returning empty list")
            return []
            
        # Force stored_logs to be a list
        if not isinstance(stored_logs, list):
            logger.warning(f"Error logs not a list (type: {type(stored_logs)}), returning empty list")
            return []
        
        logger.debug(f"Found {len(stored_logs)} raw error logs")
        
        # Filter by time if requested
        filtered_logs = stored_logs
        if hours is not None:
            try:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                filtered_logs = []
                
                for log in stored_logs:
                    # Handle invalid timestamps gracefully
                    try:
                        timestamp = datetime.fromisoformat(log.get("timestamp", ""))
                        if timestamp > cutoff_time:
                            filtered_logs.append(log)
                    except (ValueError, TypeError):
                        # Skip logs with invalid timestamps
                        logger.warning(f"Invalid timestamp in log: {log.get('timestamp')}")
                        continue
            except Exception as e:
                logger.error(f"Error filtering logs by time: {str(e)}")
                # Fall back to unfiltered logs
                filtered_logs = stored_logs
        
        # Filter by error type if requested
        if error_type is not None:
            filtered_logs = [log for log in filtered_logs if log.get("error_type") == error_type]
        
        # Filter by component if requested
        if component is not None:
            filtered_logs = [log for log in filtered_logs if log.get("component") == component]
        
        # Convert to ErrorLog objects
        error_logs = []
        for log in filtered_logs:
            try:
                error_logs.append(ErrorLog.from_dict(log))
            except Exception as e:
                logger.warning(f"Failed to convert log to ErrorLog: {str(e)}")
                # Skip invalid logs instead of breaking the entire request
                continue
        
        # Sort by timestamp (newest first) - ensures consistent ordering
        error_logs.sort(key=lambda log: log.timestamp, reverse=True)
        
        # Apply limit if requested
        if limit is not None and limit > 0:
            error_logs = error_logs[:limit]
        
        logger.debug(f"Retrieved {len(error_logs)} error logs after filtering")
        return error_logs
    
    def get_error_summary(self, hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Get a summary of error logs.
        
        Args:
            hours: Optional time limit in hours
            
        Returns:
            Dictionary with error summary
        """
        logger.info(f"Generating error summary for past {hours or 'all'} hours")
        logs = self.get_error_logs(hours=hours)
        
        if not logs:
            logger.warning("No errors available for summary")
            return {
                "count": 0,
                "time_period_hours": hours,
                "message": "No errors logged"
            }
        
        try:
            # Count errors by type
            error_types = {}
            for log in logs:
                if log.error_type:
                    error_types[log.error_type] = error_types.get(log.error_type, 0) + 1
            
            # Count errors by component
            components = {}
            for log in logs:
                if log.component:
                    components[log.component] = components.get(log.component, 0) + 1
            
            # Get time range if logs exist
            time_range = {}
            if logs:
                try:
                    # Handle potential errors in timestamp data
                    timestamps = [log.timestamp for log in logs if isinstance(log.timestamp, datetime)]
                    if timestamps:
                        oldest = min(timestamps)
                        newest = max(timestamps)
                        time_range = {
                            "oldest": oldest.isoformat(),
                            "newest": newest.isoformat(),
                            "duration_hours": round((newest - oldest).total_seconds() / 3600, 2)
                        }
                except Exception as e:
                    logger.error(f"Error calculating time range: {str(e)}")
                    time_range = {"error": str(e)}
            
            return {
                "count": len(logs),
                "time_range": time_range,
                "by_type": error_types,
                "by_component": components,
                "recent": [log.to_dict() for log in logs[:5]]  # 5 most recent errors
            }
        except Exception as e:
            logger.error(f"Error generating error summary: {str(e)}")
            return {
                "count": len(logs),
                "error": str(e),
                "message": "Error generating error summary"
            }
    
    def clear_error_logs(self) -> int:
        """
        Clear all error logs.
        
        Returns:
            Number of logs cleared
        """
        logs = self.state_manager.get(self.error_logs_key, [])
        if logs is None:
            logs = []
            
        count = len(logs)
        logger.info(f"Clearing {count} error logs")
        
        # Clear logs by setting an empty list
        self.state_manager.set(self.error_logs_key, [])
        
        # Verify logs were cleared
        current_logs = self.state_manager.get(self.error_logs_key, [])
        if current_logs and len(current_logs) > 0:
            logger.warning(f"Logs were not cleared properly. Still have {len(current_logs)} logs.")
            # Force clear again
            self.state_manager.set(self.error_logs_key, [])
        
        return count