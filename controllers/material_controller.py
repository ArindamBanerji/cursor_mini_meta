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