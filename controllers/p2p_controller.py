# controllers/p2p_controller.py
"""
Main P2P Controller Module.

This module serves as the central point for P2P-related controller functions.
It re-exports all functions from the UI and API controllers to maintain
compatibility with the existing routes configuration.

This structure allows for better separation of concerns while maintaining
backward compatibility with the meta-routes system.
"""

# Re-export UI controller functions for requisitions
from controllers.p2p_requisition_ui_controller import (
    list_requisitions,
    get_requisition,
    create_requisition_form,
    create_requisition,
    update_requisition_form,
    update_requisition
)

# Re-export UI controller functions for orders
from controllers.p2p_order_ui_controller import (
    list_orders,
    get_order,
    create_order_form,
    create_order,
    update_order_form,
    update_order,
    receive_order_form
)

# Re-export API controller functions for requisitions
from controllers.p2p_requisition_api_controller import (
    api_list_requisitions,
    api_get_requisition,
    api_create_requisition,
    api_update_requisition,
    api_submit_requisition,
    api_approve_requisition,
    api_reject_requisition
)

# Re-export API controller functions for orders
from controllers.p2p_order_api_controller import (
    api_list_orders,
    api_get_order,
    api_create_order,
    api_create_order_from_requisition,
    api_update_order,
    api_submit_order,
    api_approve_order,
    api_receive_order,
    api_complete_order,
    api_cancel_order
)

# Import needed for FastAPI parameter type hints
from fastapi import Request, Response, HTTPException, status
import logging
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# P2P Controller class for dependency injection
class P2PController:
    """P2P controller class that handles P2P-related operations."""
    
    def __init__(self, p2p_service=None, monitor_service=None):
        """Initialize with required services."""
        self.p2p_service = p2p_service
        self.monitor_service = monitor_service
    
    # Requisition methods
    async def get_requisition(self, requisition_id: str):
        """Get a requisition by ID."""
        return self.p2p_service.get_requisition(requisition_id)
    
    async def list_requisitions(self):
        """List all requisitions."""
        return self.p2p_service.list_requisitions()
    
    async def create_requisition(self, requisition_data):
        """Create a new requisition."""
        return self.p2p_service.create_requisition(requisition_data)
    
    async def update_requisition(self, requisition_id: str, requisition_data):
        """Update an existing requisition."""
        return self.p2p_service.update_requisition(requisition_id, requisition_data)
    
    async def submit_requisition(self, requisition_id: str):
        """Submit a requisition for approval."""
        return self.p2p_service.submit_requisition(requisition_id)
    
    # Order methods
    async def get_order(self, order_id: str):
        """Get an order by ID."""
        return self.p2p_service.get_order(order_id)
    
    async def list_orders(self):
        """List all orders."""
        return self.p2p_service.list_orders()
    
    async def create_order(self, order_data):
        """Create a new order."""
        return self.p2p_service.create_order(order_data)
    
    async def update_order(self, order_id: str, order_data):
        """Update an existing order."""
        return self.p2p_service.update_order(order_id, order_data)
    
    async def submit_order(self, order_id: str):
        """Submit an order for approval."""
        return self.p2p_service.submit_order(order_id)

# Function to create a P2P controller instance
def get_p2p_controller(p2p_service=None, monitor_service=None):
    """Create a P2P controller instance.
    
    Args:
        p2p_service: The P2P service to use
        monitor_service: The monitor service to use
        
    Returns:
        A P2PController instance
    """
    return P2PController(
        p2p_service=p2p_service,
        monitor_service=monitor_service
    )
