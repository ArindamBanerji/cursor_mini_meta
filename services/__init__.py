# Services package
"""
Services package initialization.
Exposes service factory functions for dependency injection.
"""

from .monitor_service import get_monitor_service
from .material_service import get_material_service
from .p2p_service import p2p_service

# Dictionary to store service instances
_services = {
    'monitor_service': None,
    'material_service': None,
    'p2p_service': p2p_service
}

def get_service(service_name: str):
    """Get a service instance by name."""
    if service_name not in _services:
        raise ValueError(f"Unknown service: {service_name}")
        
    if service_name == 'monitor_service':
        if not _services[service_name]:
            _services[service_name] = get_monitor_service()
        return _services[service_name]
    elif service_name == 'material_service':
        if not _services[service_name]:
            _services[service_name] = get_material_service()
        return _services[service_name]
    else:
        return _services[service_name]

def get_service_status():
    """Get status of all services."""
    statuses = {}
    
    # Monitor service
    try:
        monitor = get_service('monitor_service')
        statuses['monitor_service'] = 'initialized' if monitor else 'not_initialized'
    except Exception:
        statuses['monitor_service'] = 'error'
    
    # Material service
    try:
        material = get_service('material_service')
        statuses['material_service'] = 'initialized' if material else 'not_initialized'
    except Exception:
        statuses['material_service'] = 'error'
    
    # P2P service
    try:
        statuses['p2p_service'] = 'initialized' if p2p_service else 'not_initialized'
    except Exception:
        statuses['p2p_service'] = 'error'
    
    return statuses

__all__ = ['get_monitor_service', 'get_material_service', 'get_service', 'get_service_status']