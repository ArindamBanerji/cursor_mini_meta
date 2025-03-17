# services/material_service.py
"""
Service for material management business logic.

This module provides the MaterialService class which serves as the
business logic layer for material operations, handling validations,
error management, and data persistence.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta

from models.material import (
    Material, MaterialCreate, MaterialUpdate, MaterialDataLayer,
    MaterialType, UnitOfMeasure, MaterialStatus
)
from services.state_manager import state_manager
from utils.error_utils import NotFoundError, ValidationError, ConflictError, BadRequestError

# Configure logging
logger = logging.getLogger("material_service")

class MaterialService:
    """
    Service class for material management business logic.
    Provides a facade over the Material data layer with additional
    validations and business logic.
    """
    
    def __init__(self, state_manager_instance=None, monitor_service=None):
        """
        Initialize the service with a state manager instance.
        
        Args:
            state_manager_instance: Optional state manager for dependency injection
            monitor_service: Optional monitor service for dependency injection
        """
        self.state_manager = state_manager_instance or state_manager
        self.data_layer = MaterialDataLayer(self.state_manager)
        
        # Store monitor service if provided, otherwise it will be loaded on-demand
        self._monitor_service = monitor_service
    
    def _get_monitor_service(self):
        """
        Get the monitor service, loading it if not already available.
        This method provides lazy loading to avoid circular imports.
        
        Returns:
            Monitor service instance
        """
        if self._monitor_service is None:
            # Import here to avoid circular dependency
            from services import get_monitor_service
            self._monitor_service = get_monitor_service()
        return self._monitor_service
    
    def _log_error(self, error_type: str, message: str, component: str = "material_service", 
                 context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an error using the monitor service.
        
        Args:
            error_type: Type of error (e.g., "validation_error")
            message: Error message
            component: Component where the error occurred
            context: Additional context information
        """
        try:
            monitor_service = self._get_monitor_service()
            monitor_service.log_error(
                error_type=error_type,
                message=message,
                component=component,
                context=context or {}
            )
        except Exception as e:
            # If error logging fails, log to standard logger
            logger.error(f"Failed to log error to monitor service: {str(e)}")
            logger.error(f"Original error: [{error_type}] {message}")
    
    def _log_operation_success(self, operation: str, material_id: str, 
                             details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a successful operation.
        
        Args:
            operation: Operation performed (e.g., "create", "update")
            material_id: Material ID
            details: Additional details about the operation
        """
        context = {
            "material_id": material_id,
            "operation": operation
        }
        
        if details:
            context.update(details)
            
        self._log_error(
            error_type="info",
            message=f"Material {material_id} {operation} successfully",
            context=context
        )
    
    # ===== Core CRUD Operations =====
    
    def get_material(self, material_id: str) -> Material:
        """
        Get a material by ID.
        
        Args:
            material_id: The material ID or material number
            
        Returns:
            The material object
            
        Raises:
            NotFoundError: If the material is not found
        """
        logger.debug(f"Getting material: {material_id}")
        material = self.data_layer.get_by_id(material_id)
        if not material:
            error_details = {
                "material_id": material_id,
                "entity_type": "Material",
                "operation": "get"
            }
            
            # Log the error
            self._log_error(
                error_type="not_found_error",
                message=f"Material with ID {material_id} not found",
                context=error_details
            )
            
            raise NotFoundError(
                message=f"Material with ID {material_id} not found",
                details=error_details
            )
        return material
    
    def list_materials(self, 
                       status: Optional[Union[MaterialStatus, List[MaterialStatus]]] = None, 
                       type: Optional[Union[MaterialType, List[MaterialType]]] = None,
                       search_term: Optional[str] = None) -> List[Material]:
        """
        List materials with optional filtering.
        
        Args:
            status: Optional material status(es) to filter by
            type: Optional material type(s) to filter by
            search_term: Optional search term to filter by (looks in name and description)
            
        Returns:
            List of materials matching the criteria
        """
        logger.debug(f"Listing materials with filters: status={status}, type={type}, search={search_term}")
        
        # Get all materials first
        all_materials = self.data_layer.list_all()
        filtered_materials = all_materials
        
        # Filter by status if provided
        if status:
            if isinstance(status, list):
                filtered_materials = [m for m in filtered_materials if m.status in status]
            else:
                filtered_materials = [m for m in filtered_materials if m.status == status]
        
        # Filter by type if provided
        if type:
            if isinstance(type, list):
                filtered_materials = [m for m in filtered_materials if m.type in type]
            else:
                filtered_materials = [m for m in filtered_materials if m.type == type]
        
        # Filter by search term if provided
        if search_term:
            search_term = search_term.lower()
            result = []
            for material in filtered_materials:
                if (
                    search_term in material.name.lower() or 
                    (material.description and search_term in material.description.lower()) or
                    search_term in material.material_number.lower()
                ):
                    result.append(material)
            filtered_materials = result
        
        logger.debug(f"Found {len(filtered_materials)} materials")
        return filtered_materials
    
    def create_material(self, material_data: MaterialCreate) -> Material:
        """
        Create a new material with business logic validations.
        
        Args:
            material_data: The material creation data
            
        Returns:
            The created material
            
        Raises:
            ValidationError: If the material data is invalid
            ConflictError: If a material with the same number already exists
        """
        logger.info(f"Creating new material: {material_data.name}")
        
        try:
            # Validate required fields
            if not material_data.name:
                validation_errors = {"name": "Name cannot be empty"}
                error_details = {
                    "validation_errors": validation_errors,
                    "entity_type": "Material",
                    "operation": "create"
                }
                
                # Log validation error
                self._log_error(
                    error_type="validation_error",
                    message="Invalid material data: Name is required",
                    context=error_details
                )
                
                # Raise ValidationError
                raise ValidationError(
                    message="Invalid material data: Name is required",
                    details=error_details
                )
            
            # Generate material number if not provided
            if not material_data.material_number:
                # Import here to avoid circular import
                from services.material_service_helpers import generate_material_number
                material_data.material_number = generate_material_number(material_data.type)
                logger.debug(f"Generated material number: {material_data.material_number}")
                
            # Check if material with this number already exists
            if material_data.material_number:
                existing = self.data_layer.get_by_material_number(material_data.material_number)
                if existing:
                    error_details = {
                        "material_number": material_data.material_number,
                        "entity_type": "Material",
                        "conflict_reason": "material_number_exists",
                        "operation": "create"
                    }
                    
                    # Log the error
                    self._log_error(
                        error_type="conflict_error",
                        message=f"Material with number {material_data.material_number} already exists",
                        context=error_details
                    )
                    
                    raise ConflictError(
                        message=f"Material with number {material_data.material_number} already exists",
                        details=error_details
                    )
            
            # Create the material
            material = self.data_layer.create(material_data)
            
            # Log successful creation
            self._log_operation_success(
                operation="created",
                material_id=material.material_number,
                details={
                    "material_name": material.name,
                    "material_type": material.type.value
                }
            )
            
            return material
            
        except ValidationError as e:
            # Re-raise validation errors
            logger.warning(f"Validation error creating material: {e.message}")
            raise e
        except ConflictError as e:
            # Re-raise conflict errors
            logger.warning(f"Conflict error creating material: {e.message}")
            raise e
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error creating material: {str(e)}", exc_info=True)
            self._log_error(
                error_type="unexpected_error",
                message=f"Unexpected error creating material: {str(e)}",
                context={
                    "error_type": type(e).__name__,
                    "entity_type": "Material",
                    "operation": "create"
                }
            )
            
            # Re-raise as BadRequestError for consistent handling
            raise BadRequestError(
                message=f"Failed to create material: {str(e)}"
            )
    
    def update_material(self, material_id: str, update_data: MaterialUpdate) -> Material:
        """
        Update a material with business logic validations.
        
        Args:
            material_id: The material ID or material number
            update_data: The material update data
            
        Returns:
            The updated material
            
        Raises:
            NotFoundError: If the material is not found
            ValidationError: If the update data is invalid
        """
        logger.info(f"Updating material {material_id}")
        
        try:
            # Check if material exists
            material = self.get_material(material_id)
            
            # Validate status transition if status is being updated
            if update_data.status is not None and update_data.status != material.status:
                # Import here to avoid circular import
                from services.material_service_helpers import validate_material_status_transition
                
                if not validate_material_status_transition(material.status, update_data.status):
                    error_details = {
                        "material_id": material_id,
                        "current_status": material.status.value,
                        "requested_status": update_data.status.value,
                        "entity_type": "Material",
                        "operation": "update",
                        "reason": "invalid_status_transition"
                    }
                    
                    # Log validation error
                    self._log_error(
                        error_type="validation_error",
                        message=f"Invalid status transition from {material.status} to {update_data.status}",
                        context=error_details
                    )
                    
                    raise ValidationError(
                        message=f"Invalid status transition from {material.status} to {update_data.status}",
                        details=error_details
                    )
            
            # Update the material through the data layer
            updated_material = self.data_layer.update(material_id, update_data)
            if not updated_material:
                error_details = {
                    "material_id": material_id,
                    "entity_type": "Material",
                    "operation": "update"
                }
                
                # Log not found error
                self._log_error(
                    error_type="not_found_error",
                    message=f"Material with ID {material_id} not found",
                    context=error_details
                )
                
                raise NotFoundError(
                    message=f"Material with ID {material_id} not found",
                    details=error_details
                )
            
            # Manual timestamp fix to ensure updated_at is after created_at
            if updated_material.updated_at <= updated_material.created_at:
                updated_material.updated_at = updated_material.created_at + timedelta(milliseconds=1)
                
                # Update the material in the collection to persist the timestamp change
                collection = self.data_layer._get_collection()
                collection.add(updated_material.material_number, updated_material)
                self.state_manager.set_model(self.data_layer.state_key, collection)
            
            # Log successful update
            updated_fields = [k for k, v in update_data.model_dump(exclude_unset=True).items() if v is not None]
            self._log_operation_success(
                operation="updated",
                material_id=material_id,
                details={
                    "material_name": updated_material.name,
                    "updated_fields": updated_fields
                }
            )
            
            return updated_material
            
        except ValidationError as e:
            # Re-raise validation errors
            logger.warning(f"Validation error updating material {material_id}: {e.message}")
            raise e
        except NotFoundError as e:
            # Re-raise not found errors
            logger.warning(f"Material {material_id} not found for update")
            raise e
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error updating material {material_id}: {str(e)}", exc_info=True)
            self._log_error(
                error_type="unexpected_error",
                message=f"Unexpected error updating material {material_id}: {str(e)}",
                context={
                    "material_id": material_id,
                    "error_type": type(e).__name__,
                    "entity_type": "Material",
                    "operation": "update"
                }
            )
            
            # Re-raise as BadRequestError for consistent handling
            raise BadRequestError(
                message=f"Failed to update material {material_id}: {str(e)}"
            )
    
    def delete_material(self, material_id: str) -> bool:
        """
        Delete a material with business logic validations.
        
        Args:
            material_id: The material ID or material number
            
        Returns:
            True if the material was deleted, False otherwise
            
        Raises:
            NotFoundError: If the material is not found
            ValidationError: If the material cannot be deleted
        """
        logger.info(f"Deleting material {material_id}")
        
        try:
            # Check if material exists
            material = self.get_material(material_id)
            
            # Import here to avoid circular import
            from services.material_service_helpers import validate_material_can_be_deleted
            
            # Check if the material can be deleted
            if not validate_material_can_be_deleted(material.status):
                error_details = {
                    "material_id": material_id,
                    "material_number": material.material_number,
                    "current_status": material.status.value,
                    "entity_type": "Material",
                    "operation": "delete",
                    "reason": "active_material_cannot_be_deleted"
                }
                
                # Log validation error
                self._log_error(
                    error_type="validation_error",
                    message=f"Cannot delete material with status {material.status}. Deprecate it first.",
                    context=error_details
                )
                
                raise ValidationError(
                    message=f"Cannot delete material with status {material.status}. Deprecate it first.",
                    details=error_details
                )
            
            # Delete the material
            result = self.data_layer.delete(material_id)
            if not result:
                # Log not found error
                self._log_error(
                    error_type="not_found_error",
                    message=f"Material with ID {material_id} not found",
                    context={
                        "material_id": material_id,
                        "entity_type": "Material",
                        "operation": "delete"
                    }
                )
                
                raise NotFoundError(
                    message=f"Material with ID {material_id} not found",
                    details={
                        "material_id": material_id,
                        "entity_type": "Material",
                        "operation": "delete"
                    }
                )
            
            # Log successful deletion
            self._log_operation_success(
                operation="deleted",
                material_id=material_id,
                details={
                    "material_number": material.material_number,
                    "material_name": material.name
                }
            )
            
            return result
        except ValidationError as e:
            # Re-raise validation errors
            logger.warning(f"Validation error deleting material {material_id}: {e.message}")
            raise e
        except NotFoundError as e:
            # Re-raise not found errors
            logger.warning(f"Material {material_id} not found for deletion")
            raise e
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error deleting material {material_id}: {str(e)}", exc_info=True)
            self._log_error(
                error_type="unexpected_error",
                message=f"Unexpected error deleting material {material_id}: {str(e)}",
                context={
                    "material_id": material_id,
                    "error_type": type(e).__name__,
                    "entity_type": "Material",
                    "operation": "delete"
                }
            )
            
            # Re-raise as BadRequestError for consistent handling
            raise BadRequestError(
                message=f"Failed to delete material {material_id}: {str(e)}"
            )
    
    def count_materials(self, 
                        status: Optional[MaterialStatus] = None,
                        type: Optional[MaterialType] = None) -> int:
        """
        Count materials with optional filtering.
        
        Args:
            status: Optional material status to filter by
            type: Optional material type to filter by
            
        Returns:
            Count of materials matching the criteria
        """
        materials = self.list_materials(status=status, type=type)
        return len(materials)
    
    # ===== Business Operations =====
    
    def deprecate_material(self, material_id: str) -> Material:
        """
        Deprecate a material (mark as DEPRECATED).
        
        Args:
            material_id: The material ID or material number
            
        Returns:
            The updated material
            
        Raises:
            NotFoundError: If the material is not found
            ValidationError: If the material cannot be deprecated
        """
        logger.info(f"Deprecating material {material_id}")
        
        try:
            # Check if material exists
            material = self.get_material(material_id)
            
            # Import here to avoid circular import
            from services.material_service_helpers import validate_material_can_be_deprecated
            
            # Check if the material can be deprecated
            if not validate_material_can_be_deprecated(material.status):
                error_details = {
                    "material_id": material_id,
                    "material_number": material.material_number,
                    "current_status": material.status.value,
                    "entity_type": "Material",
                    "operation": "deprecate",
                    "reason": "already_deprecated"
                }
                
                # Log validation error
                self._log_error(
                    error_type="validation_error",
                    message=f"Material with status {material.status} cannot be deprecated. Material is already deprecated.",
                    context=error_details
                )
                
                raise ValidationError(
                    message=f"Material with status {material.status} cannot be deprecated. Material is already deprecated.",
                    details=error_details
                )
            
            # Update status to DEPRECATED
            update_data = MaterialUpdate(status=MaterialStatus.DEPRECATED)
            updated_material = self.update_material(material_id, update_data)
            
            # Log successful deprecation
            self._log_operation_success(
                operation="deprecated",
                material_id=material_id,
                details={
                    "material_number": material.material_number,
                    "material_name": material.name,
                    "previous_status": material.status.value,
                    "new_status": MaterialStatus.DEPRECATED.value
                }
            )
            
            return updated_material
        except ValidationError as e:
            # Re-raise validation errors with enhanced context if needed
            if "operation" not in getattr(e, "details", {}) or e.details.get("operation") != "deprecate":
                error_details = {
                    "material_id": material_id,
                    "entity_type": "Material",
                    "operation": "deprecate",
                    "validation_errors": e.details if hasattr(e, 'details') else {}
                }
                
                # Log enhanced error
                self._log_error(
                    error_type="validation_error",
                    message=f"Cannot deprecate material {material_id}: {e.message}",
                    context=error_details
                )
                
                raise ValidationError(
                    message=f"Cannot deprecate material {material_id}: {e.message}",
                    details=error_details
                )
            raise e
        except Exception as e:
            # Log unexpected errors
            logger.error(f"Unexpected error deprecating material {material_id}: {str(e)}", exc_info=True)
            self._log_error(
                error_type="unexpected_error",
                message=f"Unexpected error deprecating material {material_id}: {str(e)}",
                context={
                    "material_id": material_id,
                    "error_type": type(e).__name__,
                    "entity_type": "Material",
                    "operation": "deprecate"
                }
            )
            
            # Re-raise as BadRequestError for consistent handling
            raise BadRequestError(
                message=f"Failed to deprecate material {material_id}: {str(e)}"
            )

# Create a singleton instance
material_service = MaterialService()
