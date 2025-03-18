# Services package
"""
Services package initialization.
Exposes service factory functions for dependency injection.
"""

# Import singletons and their getter functions
from .state_manager import state_manager, get_state_manager
from .monitor_service import monitor_service, get_monitor_service
from .material_service import material_service, get_material_service
from .p2p_service import p2p_service, get_p2p_service

# Dictionary to store service instances and additional registrations
_service_registry = {
    'monitor_service': monitor_service,
    'material_service': material_service,
    'p2p_service': p2p_service,
    'state_manager': state_manager
}

def register_service(name, service):
    """Register a service for discovery."""
    _service_registry[name] = service
    return service

def get_service(service_name: str, default_factory=None):
    """Get a service instance by name.
    
    Args:
        service_name: The name of the service to retrieve
        default_factory: Optional factory function to create the service if it doesn't exist
        
    Returns:
        The requested service instance
        
    Raises:
        KeyError: If the service doesn't exist and no default factory is provided
    """
    if service_name not in _service_registry:
        if default_factory is not None:
            service = default_factory()
            register_service(service_name, service)
            return service
        raise KeyError(f"Unknown service: {service_name}")
    
    return _service_registry[service_name]

def get_or_create_service(name: str, service_class, *args, **kwargs):
    """Get an existing service instance or create a new one.
    
    Args:
        name: The name of the service to retrieve or create
        service_class: The class to instantiate if the service doesn't exist
        *args: Positional arguments to pass to the service constructor
        **kwargs: Keyword arguments to pass to the service constructor
        
    Returns:
        Either the existing service instance or a newly created one
    """
    try:
        return get_service(name)
    except KeyError:
        service = service_class(*args, **kwargs)
        register_service(name, service)
        return service

def create_service_instance(service_class, *args, **kwargs):
    """Create a new service instance without registering it.
    
    Args:
        service_class: The class to instantiate
        *args: Positional arguments to pass to the service constructor
        **kwargs: Keyword arguments to pass to the service constructor
        
    Returns:
        The newly created service instance
    """
    return service_class(*args, **kwargs)

def clear_service_registry():
    """Clear the service registry."""
    # Don't remove the main services
    main_services = ['monitor_service', 'material_service', 'p2p_service', 'state_manager']
    
    # Clear non-main services
    keys_to_delete = [key for key in _service_registry.keys() if key not in main_services]
    for key in keys_to_delete:
        del _service_registry[key]

def reset_services():
    """Reset all services to initial state."""
    # Clear the state manager
    state_manager.clear()
    
    # Reset service registry
    clear_service_registry()

def get_service_status():
    """Get status of all services."""
    statuses = {}
    
    # Check status of each service in the registry
    for service_name in _service_registry:
        try:
            service = _service_registry[service_name]
            statuses[service_name] = 'initialized' if service else 'not_initialized'
        except Exception:
            statuses[service_name] = 'error'
    
    return statuses

# Export all public functions and instances
__all__ = [
    'get_state_manager', 
    'state_manager',
    'get_monitor_service', 
    'monitor_service',
    'get_material_service', 
    'material_service',
    'get_p2p_service',
    'p2p_service',
    'get_service', 
    'get_service_status',
    'register_service',
    'clear_service_registry',
    'reset_services',
    'get_or_create_service',
    'create_service_instance'
]