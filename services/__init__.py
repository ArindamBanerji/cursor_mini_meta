# services/__init__.py
"""
Service factory module for the SAP Test Harness.

This module provides factory functions to obtain service instances with:
1. Explicit service initialization sequence
2. Dependency validation
3. Service status tracking
4. Clean mock injection for testing
"""

import logging
import inspect
from typing import Optional, Dict, Any, Type, TypeVar, List, Callable

from services.state_manager import StateManager, state_manager

# Configure logging
logger = logging.getLogger("services")

# Type variable for services
T = TypeVar('T')

# Service registry to keep track of service instances
_service_instances: Dict[str, Any] = {}

# Service initialization status
_service_status: Dict[str, str] = {
    "material_service": "uninitialized",
    "p2p_service": "uninitialized",
    "monitor_service": "uninitialized"
}

# Service dependency graph
_service_dependencies = {
    "material_service": [],  # No dependencies
    "p2p_service": ["material_service"],  # Depends on material service
    "monitor_service": []  # No dependencies
}

# Service initialization order - dependencies first
_initialization_order = [
    "monitor_service",  # No dependencies, can be first
    "material_service",  # No dependencies, can be second
    "p2p_service"  # Depends on material service, must be after it
]

# Mock registry for testing
_mock_registry: Dict[str, Any] = {}

def register_mock(service_name: str, mock_instance: Any) -> None:
    """
    Register a mock service for testing.
    
    Args:
        service_name: The name of the service to mock
        mock_instance: The mock instance to use
    """
    logger.info(f"Registering mock for '{service_name}'")
    _mock_registry[service_name] = mock_instance

def clear_mocks() -> None:
    """
    Clear all registered mocks.
    """
    logger.info("Clearing all mocks")
    _mock_registry.clear()

def get_material_service(state_manager_instance=None):
    """
    Factory function for Material Service.
    
    Args:
        state_manager_instance: Optional state manager instance for dependency injection
        
    Returns:
        An instance of the MaterialService class
    """
    service_name = "material_service"
    
    # Check for a mock first
    if service_name in _mock_registry:
        logger.debug(f"Using mock for '{service_name}'")
        return _mock_registry[service_name]
    
    # Check if already initialized
    if service_name in _service_instances:
        logger.debug(f"Using existing instance of '{service_name}'")
        return _service_instances[service_name]
    
    # Check if dependencies are satisfied
    _ensure_dependencies_satisfied(service_name)
    
    # Update status to initializing
    _service_status[service_name] = "initializing"
    
    try:
        # Import here to avoid circular imports
        from services.material_service import material_service, MaterialService
        
        if state_manager_instance:
            # Create a new instance with the provided state manager
            logger.info(f"Creating new MaterialService instance with custom state manager")
            instance = MaterialService(state_manager_instance)
            
            # Update service registry and status
            _service_instances[service_name] = instance
            _service_status[service_name] = "initialized"
            
            return instance
        
        # No custom state manager, use the singleton
        _service_instances[service_name] = material_service
        _service_status[service_name] = "initialized"
        
        logger.debug(f"Using singleton MaterialService instance")
        return material_service
    except Exception as e:
        # Update status to failed
        _service_status[service_name] = "failed"
        logger.error(f"Failed to initialize '{service_name}': {str(e)}")
        raise

def get_p2p_service(state_manager_instance=None, material_service_instance=None):
    """
    Factory function for P2P Service.
    
    Args:
        state_manager_instance: Optional state manager instance for dependency injection
        material_service_instance: Optional material service instance for dependency injection
        
    Returns:
        An instance of the P2PService class
    """
    service_name = "p2p_service"
    
    # Check for a mock first
    if service_name in _mock_registry:
        logger.debug(f"Using mock for '{service_name}'")
        return _mock_registry[service_name]
    
    # Check if already initialized
    if service_name in _service_instances:
        logger.debug(f"Using existing instance of '{service_name}'")
        return _service_instances[service_name]
    
    # Check if dependencies are satisfied
    _ensure_dependencies_satisfied(service_name)
    
    # Update status to initializing
    _service_status[service_name] = "initializing"
    
    try:
        # Import here to avoid circular imports
        from services.p2p_service import p2p_service, P2PService
        
        # Get material service if not provided
        if material_service_instance is None:
            material_service_instance = get_material_service()
        
        # Get state manager
        sm = state_manager_instance or state_manager
        
        if state_manager_instance is not None or material_service_instance is not None:
            # Create a new instance with custom dependencies
            logger.info("Creating new P2PService instance with custom dependencies")
            instance = P2PService(sm, material_service_instance)
            
            # Update service registry and status
            _service_instances[service_name] = instance
            _service_status[service_name] = "initialized"
            
            return instance
        
        # No custom dependencies, use the singleton
        _service_instances[service_name] = p2p_service
        _service_status[service_name] = "initialized"
        
        logger.debug("Using singleton P2PService instance")
        return p2p_service
    except Exception as e:
        # Update status to failed
        _service_status[service_name] = "failed"
        logger.error(f"Failed to initialize '{service_name}': {str(e)}")
        raise

def get_monitor_service(state_manager_instance=None):
    """
    Factory function for Monitor Service.
    
    Args:
        state_manager_instance: Optional state manager instance for dependency injection
        
    Returns:
        An instance of the MonitorService class
    """
    service_name = "monitor_service"
    
    # Check for a mock first
    if service_name in _mock_registry:
        logger.debug(f"Using mock for '{service_name}'")
        return _mock_registry[service_name]
    
    # Check if already initialized
    if service_name in _service_instances:
        logger.debug(f"Using existing instance of '{service_name}'")
        return _service_instances[service_name]
    
    # Check if dependencies are satisfied
    _ensure_dependencies_satisfied(service_name)
    
    # Update status to initializing
    _service_status[service_name] = "initializing"
    
    try:
        # Import here to avoid circular imports
        from services.monitor_service import monitor_service, MonitorService
        
        if state_manager_instance:
            # Create a new instance with the provided state manager
            logger.info(f"Creating new MonitorService instance with custom state manager")
            instance = MonitorService(state_manager_instance)
            
            # Update service registry and status
            _service_instances[service_name] = instance
            _service_status[service_name] = "initialized"
            
            return instance
        
        # No custom state manager, use the singleton
        _service_instances[service_name] = monitor_service
        _service_status[service_name] = "initialized"
        
        logger.debug("Using singleton MonitorService instance")
        return monitor_service
    except Exception as e:
        # Update status to failed
        _service_status[service_name] = "failed"
        logger.error(f"Failed to initialize '{service_name}': {str(e)}")
        raise

def _ensure_dependencies_satisfied(service_name: str) -> None:
    """
    Ensure that all dependencies for a service are satisfied.
    
    Args:
        service_name: The name of the service to check dependencies for
        
    Raises:
        RuntimeError: If dependencies are not satisfied
    """
    # Skip if service has no dependencies
    if service_name not in _service_dependencies or not _service_dependencies[service_name]:
        return
    
    # Check each dependency
    for dependency in _service_dependencies[service_name]:
        # Skip if dependency is mocked
        if dependency in _mock_registry:
            continue
            
        # Check if dependency is initialized or in service registry
        if (dependency not in _service_status or 
            _service_status[dependency] != "initialized" or
            dependency not in _service_instances):
            
            # If not, raise an error
            message = f"Service '{service_name}' depends on '{dependency}' which is not initialized"
            logger.error(message)
            raise RuntimeError(message)

def register_service(service_name: str, service_instance: Any) -> None:
    """
    Register a service instance in the registry.
    
    Args:
        service_name: The name of the service (e.g., 'material', 'p2p')
        service_instance: The service instance to register
    """
    logger.info(f"Registering service '{service_name}' in registry: {service_instance.__class__.__name__}")
    _service_instances[service_name] = service_instance
    
    # Update status if this is a tracked service
    if service_name in _service_status:
        _service_status[service_name] = "initialized"

def get_service(service_name: str, default_factory=None):
    """
    Get a service instance from the registry.
    
    Args:
        service_name: The name of the service (e.g., 'material', 'p2p')
        default_factory: Optional function to call if the service is not in the registry
        
    Returns:
        The service instance
        
    Raises:
        KeyError: If the service is not in the registry and no default factory is provided
    """
    # Check for a mock first
    if service_name in _mock_registry:
        logger.debug(f"Using mock for '{service_name}'")
        return _mock_registry[service_name]
    
    if service_name in _service_instances:
        logger.debug(f"Retrieved service '{service_name}' from registry")
        return _service_instances[service_name]
    
    if default_factory:
        logger.info(f"Service '{service_name}' not found in registry, using default factory")
        service = default_factory()
        # Register the service
        register_service(service_name, service)
        return service
    
    logger.error(f"Service '{service_name}' not found in registry and no default factory provided")
    raise KeyError(f"Service '{service_name}' not found in registry")

def get_or_create_service(service_class: Type[T], *args, **kwargs) -> T:
    """
    Get a service instance by class, or create one if it doesn't exist.
    
    Args:
        service_class: The service class to instantiate
        *args: Positional arguments to pass to the service constructor
        **kwargs: Keyword arguments to pass to the service constructor
        
    Returns:
        An instance of the specified service class
    """
    service_name = service_class.__name__
    
    # Check for a mock first
    mock_key = service_name.lower()
    if mock_key in _mock_registry:
        logger.debug(f"Using mock for '{service_name}'")
        return _mock_registry[mock_key]
    
    if service_name in _service_instances:
        logger.debug(f"Retrieved service '{service_name}' from registry by class")
        return _service_instances[service_name]
    
    # Create a new instance
    logger.info(f"Creating new instance of service class: {service_name}")
    instance = service_class(*args, **kwargs)
    
    # Register the instance
    _service_instances[service_name] = instance
    logger.debug(f"Registered new {service_name} instance in registry")
    
    return instance

def create_service_instance(service_class: Type[T], *args, **kwargs) -> T:
    """
    Create a new service instance without registering it.
    
    This is useful for tests where you need a clean instance each time.
    
    Args:
        service_class: The service class to instantiate
        *args: Positional arguments to pass to the service constructor
        **kwargs: Keyword arguments to pass to the service constructor
        
    Returns:
        A new instance of the specified service class
    """
    logger.debug(f"Creating new unregistered instance of {service_class.__name__}")
    return service_class(*args, **kwargs)

def clear_service_registry() -> None:
    """
    Clear the service registry.
    
    This is useful for testing to ensure a clean state between tests.
    """
    global _service_instances
    global _service_status
    
    logger.info(f"Clearing service registry (removing {len(_service_instances)} services)")
    _service_instances.clear()
    
    # Reset service status
    for service_name in _service_status:
        _service_status[service_name] = "uninitialized"

def get_service_status() -> Dict[str, str]:
    """
    Get the initialization status of all services.
    
    Returns:
        Dictionary mapping service names to their status
    """
    return _service_status.copy()

def verify_service_health() -> Dict[str, Any]:
    """
    Verify the health of all initialized services.
    
    Returns:
        Dictionary with health status information
    """
    health = {
        "status": "healthy",
        "services": {}
    }
    
    for service_name, status in _service_status.items():
        health["services"][service_name] = {
            "status": status
        }
        
        if status == "failed":
            health["status"] = "unhealthy"
        elif status == "uninitialized" and health["status"] != "unhealthy":
            health["status"] = "warning"
    
    return health

def reset_services() -> None:
    """
    Reset all service singletons to their initial state.
    This is primarily useful for testing.
    
    Note: This should not be used in production code.
    """
    logger.info("Resetting all services to initial state")
    
    # Reset the state manager
    state_manager.clear()
    
    # Clear the service registry
    clear_service_registry()
    
    # Clear mocks
    clear_mocks()
    
    logger.info("Service reset complete")

def get_service_function_by_name(function_name: str) -> Callable:
    """
    Get a service factory function by name.
    
    This is useful for dynamic service initialization.
    
    Args:
        function_name: The name of the function (e.g., 'get_material_service')
        
    Returns:
        The function
        
    Raises:
        AttributeError: If the function is not found
    """
    current_module = sys.modules[__name__]
    if hasattr(current_module, function_name):
        return getattr(current_module, function_name)
    raise AttributeError(f"Function '{function_name}' not found in services module")

async def initialize_all_services() -> Dict[str, Any]:
    """
    Initialize all services in the correct order.
    
    Returns:
        Dictionary mapping service names to instances
    """
    logger.info("Initializing all services in sequence")
    services = {}
    
    # Initialize services in the defined order
    for service_name in _initialization_order:
        function_name = f"get_{service_name}"
        try:
            # Get the function
            factory_func = get_service_function_by_name(function_name)
            
            # Call the function to get the service
            service = factory_func()
            
            # Store the service
            services[service_name] = service
            
            logger.info(f"Initialized {service_name}: {service.__class__.__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize {service_name}: {str(e)}")
            _service_status[service_name] = "failed"
            raise
    
    logger.info(f"Successfully initialized {len(services)} services")
    return services

# Import needed for get_service_function_by_name
import sys
