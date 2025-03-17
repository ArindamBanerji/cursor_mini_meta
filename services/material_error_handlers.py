# services/material_error_handlers.py
"""
Error handling utilities for the Material Service.

This module contains error logging and handling functions
to separate these concerns from the main service logic.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from services.state_manager import StateManager
import logging

# Configure logging
logger = logging.getLogger("material_error_handlers")

class MaterialErrorHandler:
    """
    Handles error logging and processing for material service operations.
    """
    
    def __init__(self, state_manager: StateManager):
        """
        Initialize the error handler with a state manager instance.
        
        Args:
            state_manager: State manager for accessing shared state
        """
        self.state_manager = state_manager
        self._monitor_service = None
        
        # Initialize monitor service
        try:
            # Import here to avoid circular import issue
            from services.monitor_service import monitor_service
            self._monitor_service = monitor_service
        except ImportError:
            self._monitor_service = None
            logger.warning("Could not import monitor_service during MaterialErrorHandler initialization")
    
    def _ensure_monitor_service(self) -> None:
        """
        Ensure that the monitor service is available.
        If not initialized, try to get it from the service registry.
        """
        if self._monitor_service is None:
            try:
                from services import get_service
                self._monitor_service = get_service("monitor")
            except (ImportError, KeyError):
                try:
                    # Direct import as fallback
                    from services.monitor_service import monitor_service
                    self._monitor_service = monitor_service
                except ImportError:
                    # Still no success, but we tried
                    logger.warning("Unable to get monitor_service reference")
                    pass
    
    def log_error(self, 
                 error_type: str, 
                 message: str, 
                 component: str = "material_service", 
                 context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an error using monitor service if available, with fallback to direct state management.
        
        Args:
            error_type: Type of error (e.g., "validation_error", "not_found_error")
            message: Error message
            component: Component where the error occurred
            context: Additional context information
        """
        try:
            # Ensure monitor service is available
            self._ensure_monitor_service()
            
            # Try to log through monitor service first
            if self._monitor_service:
                self._monitor_service.log_error(
                    error_type=error_type,
                    message=message,
                    component=component,
                    context=context or {}
                )
                
                # Check if log was successful
                error_logs = self.state_manager.get("error_logs", [])
                if not error_logs or len(error_logs) == 0:
                    # If monitor service didn't log correctly, log directly
                    self._direct_log_error(error_type, message, component, context)
            else:
                # No monitor service, log directly
                self._direct_log_error(error_type, message, component, context)
                
        except Exception as e:
            logger.error(f"Error while logging error: {str(e)}")
            # Last resort direct logging
            self._direct_log_error(error_type, message, component, context)
    
    def _direct_log_error(self, 
                         error_type: str, 
                         message: str, 
                         component: str = "material_service", 
                         context: Optional[Dict[str, Any]] = None) -> None:
        """
        Directly log error to state manager without using monitor service.
        
        Args:
            error_type: Type of error
            message: Error message
            component: Component where the error occurred
            context: Additional context information
        """
        try:
            # Get current error logs
            error_logs = self.state_manager.get("error_logs", [])
            if error_logs is None:
                error_logs = []
            
            # Create error log structure
            new_error = {
                "error_type": error_type,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "component": component,
                "context": context or {}
            }
            
            # Add to error logs
            error_logs.append(new_error)
            
            # Save updated logs
            self.state_manager.set("error_logs", error_logs)
            logger.info(f"Direct error logged: [{error_type}] {message}")
            
        except Exception as e:
            logger.error(f"Failed to direct log error: {str(e)}")
            print(f"Critical failure in error logging: {str(e)}")
            print(f"Original error: [{error_type}] {message}")
    
    def log_validation_error(self, 
                           message: str, 
                           validation_errors: Dict[str, str], 
                           entity_type: str = "Material", 
                           operation: str = "validate", 
                           entity_id: Optional[str] = None) -> None:
        """
        Log a validation error with standard format.
        
        Args:
            message: Error message
            validation_errors: Dictionary of field-level validation errors
            entity_type: Type of entity being validated
            operation: Operation that triggered validation
            entity_id: Optional ID of the entity
        """
        context = {
            "validation_errors": validation_errors,
            "entity_type": entity_type,
            "operation": operation
        }
        
        if entity_id:
            context["entity_id"] = entity_id
            
        self.log_error(
            error_type="validation_error",
            message=message,
            component="material_service",
            context=context
        )
    
    def log_not_found_error(self, 
                          entity_id: str, 
                          entity_type: str = "Material", 
                          operation: str = "get") -> None:
        """
        Log a not found error with standard format.
        
        Args:
            entity_id: ID of the entity that wasn't found
            entity_type: Type of entity
            operation: Operation that triggered the error
        """
        error_msg = f"{entity_type} with ID {entity_id} not found"
        context = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "operation": operation
        }
        
        self.log_error(
            error_type="not_found_error",
            message=error_msg,
            component="material_service",
            context=context
        )
    
    def log_conflict_error(self, 
                         entity_id: str, 
                         reason: str, 
                         entity_type: str = "Material", 
                         operation: str = "create") -> None:
        """
        Log a conflict error with standard format.
        
        Args:
            entity_id: ID of the entity in conflict
            reason: Reason for the conflict
            entity_type: Type of entity
            operation: Operation that triggered the error
        """
        error_msg = f"{entity_type} conflict: {reason}"
        context = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "operation": operation,
            "conflict_reason": reason
        }
        
        self.log_error(
            error_type="conflict_error",
            message=error_msg,
            component="material_service",
            context=context
        )
    
    def log_operation_success(self, 
                            operation: str, 
                            entity_id: str, 
                            entity_type: str = "Material", 
                            details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a successful operation.
        
        Args:
            operation: The operation performed
            entity_id: ID of the entity
            entity_type: Type of entity
            details: Additional details about the operation
        """
        message = f"{entity_type} {entity_id} {operation} successfully"
        context = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "operation": operation
        }
        
        if details:
            context.update(details)
            
        self.log_error(
            error_type="info",
            message=message,
            component="material_service",
            context=context
        )
