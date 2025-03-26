"""
Service imports facade module for tests.

This module provides a centralized location for importing all service classes and functions
used in the mini-meta-harness project tests. It simplifies imports in test files and
provides direct access to source implementations.
"""

# Base service imports
from services.base_service import BaseService

# State manager imports
from services.state_manager import StateManager, get_state_manager, state_manager

# Material service imports - direct imports from source
from services.material_service import MaterialService, get_material_service, material_service

# Monitor service imports - direct imports from source
from services.monitor_service import (
    MonitorService,
    get_monitor_service,
    monitor_service,
    ErrorLog,
    SystemMetrics
)
from services.monitor_health import MonitorHealth
from services.monitor_core import MonitorCore
from services.monitor_metrics import MonitorMetrics
from services.monitor_errors import MonitorErrors

# P2P service imports - direct imports from source
from services.p2p_service import P2PService, get_p2p_service, p2p_service
from services.p2p_service_order import create_test_order
from services.p2p_service_requisition import create_test_requisition

# Template and URL services
from services.template_service import TemplateService
from services.url_service import URLService

# Route imports - direct imports without fallbacks
from routes.meta_routes import RouteDefinition, ALL_ROUTES
from routes.http_method import HttpMethod

# Service registry functions
from services import get_service, get_or_create_service, get_service_status

# Import service registry functionality from services
try:
    from services.service_registry import clear_service_registry, reset_services, register_service
except ImportError:
    # Fallback: define these functions in case they don't exist
    from services import clear_service_registry, reset_services
    
    # Fallback implementation of register_service if needed
    def register_service(name, service):
        """Register a service in the service registry"""
        from services import _service_registry
        _service_registry[name] = service
        return service

# Material model imports
from models.material import (
    Material,
    MaterialCreate, 
    MaterialUpdate, 
    MaterialStatus, 
    MaterialType, 
    UnitOfMeasure,
    MaterialDataLayer
)

# P2P model imports
from models.p2p import (
    ProcurementDocument,
    Requisition,
    Order,
    RequisitionCreate,
    OrderCreate,
    RequisitionUpdate,
    OrderUpdate,
    DocumentStatus,
    ProcurementType,
    DocumentItemStatus,
    DocumentItem,
    RequisitionItem,
    OrderItem,
    P2PDataLayer
)

# Exception imports
from utils.error_utils import (
    NotFoundError,
    ValidationError,
    BadRequestError,
    ConflictError,
    AuthenticationError,
    AuthorizationError
)

# Controller imports
from controllers import BaseController

# Material controllers
from controllers.material_controller import get_material_controller
from controllers.material_api_controller import (
    get_material_api_controller,
    api_get_material,
    api_update_material
)
from controllers.material_ui_controller import (
    get_material_ui_controller,
    create_material,
    get_material
)

# Monitor controller functions
from controllers.monitor_controller import get_safe_client_host

# P2P controller functions
from controllers.p2p_controller import get_p2p_controller
from controllers.p2p_order_api_controller import (
    get_p2p_order_api_controller,
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
from controllers.p2p_requisition_api_controller import (
    get_p2p_requisition_api_controller,
    api_create_requisition,
    api_submit_requisition,
    api_approve_requisition,
    api_reject_requisition
)
from controllers.p2p_requisition_ui_controller import (
    submit_requisition,
    approve_requisition,
    reject_requisition,
    list_requisitions,
    get_requisition,
    create_requisition_form,
    create_requisition,
    update_requisition_form,
    update_requisition
)

# Dashboard controller functions
from controllers.dashboard_controller import get_system_health, get_p2p_statistics, get_recent_activities

# Common controller dependencies
from controllers.material_common import (
    get_material_service_dependency, 
    get_monitor_service_dependency,
    get_material_type_options,
    get_material_status_options,
    get_unit_of_measure_options
)

from controllers.p2p_common import (
    get_p2p_service_dependency,
    get_monitor_service_dependency as get_p2p_monitor_dependency,
    get_material_service_dependency as get_p2p_material_dependency
)

# Session middleware
from middleware.session import (
    SessionMiddleware,
    FlashMessage,
    SessionStore,
    get_session,
    set_session_data,
    get_session_data,
    get_flash_messages,
    add_flash_message,
    store_form_data,
    get_form_data,
    clear_form_data,
    extract_session_from_cookie,
    generate_session_cookie,
    _session_store
)

# Flash message types
class FlashMessageType:
    """Flash message types for user notifications."""
    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"
    WARNING = "warning"

# Async session helper functions
async def get_flash_messages_async(request):
    """Async wrapper for get_flash_messages."""
    return getattr(request.state, "flash_messages", [])

async def add_flash_message_async(request, message, type="info"):
    """Async wrapper for add_flash_message."""
    session = await get_session(request)
    flash_messages = session.get("flash_messages", [])
    flash_messages.append(FlashMessage(message, type).to_dict())
    session["flash_messages"] = flash_messages

async def store_form_data_async(request, form_data):
    """Async wrapper for store_form_data."""
    session = await get_session(request)
    session["form_data"] = form_data

async def get_form_data_async(request):
    """Async wrapper for get_form_data."""
    return getattr(request.state, "form_data", {})

# Replace the original functions with async versions
get_flash_messages = get_flash_messages_async
add_flash_message = add_flash_message_async
store_form_data = store_form_data_async
get_form_data = get_form_data_async

# Model imports
from models.common import BaseDataModel, EntityCollection

# Helper function to create test materials
def create_test_material(
    id="MAT001", 
    name="Test Material", 
    material_type=None,
    description="Test material for testing",
    unit_of_measure=None,
    price=10.0,
    status=None,
    material_number=None
):
    """Create a test material for use in tests."""
    # Set default enum values if not provided
    if material_type is None:
        if hasattr(MaterialType, 'RAW_MATERIAL'):
            material_type = MaterialType.RAW_MATERIAL
        elif hasattr(MaterialType, 'RAW'):
            material_type = MaterialType.RAW
        else:
            # Default to first enum value
            material_type = list(MaterialType)[0]
            
    if unit_of_measure is None:
        if hasattr(UnitOfMeasure, 'EACH'):
            unit_of_measure = UnitOfMeasure.EACH
        elif hasattr(UnitOfMeasure, 'EA'):
            unit_of_measure = UnitOfMeasure.EA
        else:
            # Default to first enum value
            unit_of_measure = list(UnitOfMeasure)[0]
            
    if status is None:
        if hasattr(MaterialStatus, 'ACTIVE'):
            status = MaterialStatus.ACTIVE
        else:
            # Default to first enum value
            status = list(MaterialStatus)[0]
            
    if material_number is None:
        material_number = f"M{id.replace('MAT', '')}" if id.startswith('MAT') else f"M{id}"
    
    return MaterialCreate(
        id=id,
        name=name,
        material_type=material_type,
        description=description,
        unit_of_measure=unit_of_measure,
        price=price,
        status=status,
        material_number=material_number
    )

# Test service creation functions
def create_test_material_service(state_manager=None, monitor_service=None):
    """Create a test material service for use in tests."""
    if state_manager is None:
        state_manager = create_test_state_manager()
    
    # MaterialService takes state_manager as a positional arg, not named parameter
    material_service = MaterialService(state_manager)
    
    if monitor_service:
        material_service.monitor_service = monitor_service
        # Register the material service with the monitor service
        if hasattr(monitor_service, "register_component"):
            monitor_service.register_component("material_service", material_service)
    
    return material_service

def create_test_p2p_service(state_manager=None, material_service=None, monitor_service=None):
    """Create a test P2P service for use in tests."""
    if state_manager is None:
        state_manager = create_test_state_manager()
    
    p2p_service = P2PService(state_manager=state_manager, material_service=material_service)
    
    if monitor_service:
        p2p_service.monitor_service = monitor_service
        # Register the P2P service with the monitor service
        if hasattr(monitor_service, "register_component"):
            monitor_service.register_component("p2p_service", p2p_service)
    
    return p2p_service

def create_test_monitor_service(state_manager=None):
    """Create a test monitor service for use in tests."""
    if state_manager is None:
        state_manager = create_test_state_manager()
    # MonitorService doesn't take state_manager as a named parameter, just as a positional argument
    return MonitorService(state_manager)

def create_test_state_manager():
    """Create a test state manager for use in tests."""
    return StateManager()

def create_test_monitor_health():
    """Create a test monitor health component for use in tests."""
    return MonitorHealth()

def create_test_monitor_metrics():
    """Create a test monitor metrics component for use in tests."""
    return MonitorMetrics()

def create_test_monitor_errors():
    """Create a test monitor errors component for use in tests."""
    return MonitorErrors()

def create_test_template_service():
    """Create a test template service for use in tests."""
    return TemplateService()

def create_test_url_service():
    """Create a test URL service for use in tests."""
    return URLService()

def setup_exception_handlers(app):
    """Set up exception handlers for the FastAPI app."""
    
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request, exc):
        """Handle NotFoundError exceptions."""
        from fastapi.responses import JSONResponse
        from fastapi import status
        
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request, exc):
        """Handle ValidationError exceptions."""
        from fastapi.responses import JSONResponse
        from fastapi import status
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )
    
    @app.exception_handler(BadRequestError)
    async def bad_request_handler(request, exc):
        """Handle BadRequestError exceptions."""
        from fastapi.responses import JSONResponse
        from fastapi import status
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc)},
        )
    
    @app.exception_handler(ConflictError)
    async def conflict_handler(request, exc):
        """Handle ConflictError exceptions."""
        from fastapi.responses import JSONResponse
        from fastapi import status
        
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )
    
    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request, exc):
        """Handle AuthenticationError exceptions."""
        from fastapi.responses import JSONResponse
        from fastapi import status
        
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)},
        )
    
    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(request, exc):
        """Handle AuthorizationError exceptions."""
        from fastapi.responses import JSONResponse
        from fastapi import status
        
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": str(exc)},
        ) 