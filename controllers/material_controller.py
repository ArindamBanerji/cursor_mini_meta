# controllers/material_controller.py
"""
Main Material Controller Module.

This module serves as the central point for material-related controller functions.
It re-exports all functions from the UI and API controllers to maintain
compatibility with the existing routes configuration.

This structure allows for better separation of concerns while maintaining
backward compatibility with the meta-routes system.
"""

# Re-export UI controller functions
from controllers.material_ui_controller import (
    list_materials,
    get_material,
    create_material_form,
    create_material,
    update_material_form,
    update_material,
    deprecate_material
)

# Re-export API controller functions
from controllers.material_api_controller import (
    api_list_materials,
    api_get_material,
    api_create_material,
    api_update_material,
    api_deprecate_material
)

# Import needed for FastAPI parameter type hints
from fastapi import Request

# Material Controller class for dependency injection
class MaterialController:
    """Material controller class that handles material-related operations."""
    
    def __init__(self, material_service=None, monitor_service=None):
        """Initialize with required services."""
        self.material_service = material_service
        self.monitor_service = monitor_service
    
    async def get_material(self, material_id: str):
        """Get a material by ID."""
        return self.material_service.get_material(material_id)
    
    async def list_materials(self):
        """List all materials."""
        return self.material_service.list_materials()
    
    async def create_material(self, material_data):
        """Create a new material."""
        return self.material_service.create_material(material_data)
    
    async def update_material(self, material_id: str, material_data):
        """Update an existing material."""
        return self.material_service.update_material(material_id, material_data)
    
    async def deprecate_material(self, material_id: str):
        """Deprecate a material."""
        return self.material_service.deprecate_material(material_id)

# Function to create a material controller instance
def get_material_controller(material_service=None, monitor_service=None):
    """Create a material controller instance.
    
    Args:
        material_service: The material service to use
        monitor_service: The monitor service to use
        
    Returns:
        A MaterialController instance
    """
    return MaterialController(
        material_service=material_service,
        monitor_service=monitor_service
    )