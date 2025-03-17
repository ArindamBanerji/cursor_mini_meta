# service_initializer.py
"""
Module for initializing services in a controlled sequence with proper dependency management.
This separates service initialization logic from the main application code.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any

# Configure logging
logger = logging.getLogger("service_initializer")

async def initialize_services():
    """
    Initialize all services in the correct order.
    This ensures dependencies are satisfied before dependent services are initialized.
    
    Returns:
        Dict with initialized services
    """
    logger.info("Starting service initialization sequence")
    
    try:
        # Import service functions here to avoid circular imports
        from services import (
            get_monitor_service, 
            get_material_service, 
            get_p2p_service,
            register_service
        )
        
        # Initialize monitor service first (no dependencies)
        logger.info("Initializing Monitor Service...")
        monitor_service = None
        try:
            monitor_service = get_monitor_service()
            logger.info(f"Monitor service initialized: {monitor_service.__class__.__name__}")
        except Exception as e:
            logger.error(f"Error initializing Monitor Service: {str(e)}", exc_info=True)
            raise
        
        # Initialize material service (depends on monitor)
        logger.info("Initializing Material Service...")
        material_service = None
        try:
            material_service = get_material_service()
            logger.info(f"Material service initialized: {material_service.__class__.__name__}")
        except Exception as e:
            logger.error(f"Error initializing Material Service: {str(e)}", exc_info=True)
            raise
        
        # Initialize P2P service (depends on material)
        logger.info("Initializing P2P Service...")
        p2p_service = None
        try:
            p2p_service = get_p2p_service()
            logger.info(f"P2P service initialized: {p2p_service.__class__.__name__}")
        except Exception as e:
            logger.error(f"Error initializing P2P Service: {str(e)}", exc_info=True)
            raise
        
        # Register services in the service registry for easy access
        logger.info("Registering services in service registry...")
        try:
            register_service("monitor", monitor_service)
            register_service("material", material_service)
            register_service("p2p", p2p_service)
            logger.info("All services registered successfully")
        except Exception as e:
            logger.error(f"Error registering services: {str(e)}", exc_info=True)
            raise
        
        # Return the services for use in the application
        return {
            "monitor_service": monitor_service,
            "material_service": material_service,
            "p2p_service": p2p_service
        }
        
    except Exception as e:
        logger.critical(f"Fatal error during service initialization: {str(e)}", exc_info=True)
        raise

async def collect_initial_metrics(monitor_service):
    """
    Collect initial system metrics using the monitor service.
    
    Args:
        monitor_service: The monitor service instance
    
    Returns:
        The collected metrics
    """
    logger.info("Collecting initial system metrics...")
    try:
        metrics = monitor_service.collect_current_metrics()
        logger.info(f"Initial metrics collected: CPU: {metrics.cpu_percent:.1f}%, Memory: {metrics.memory_usage:.1f}%, Disk: {metrics.disk_usage:.1f}%")
        return metrics
    except Exception as e:
        logger.error(f"Error collecting initial metrics: {str(e)}", exc_info=True)
        return None

async def update_component_status(monitor_service, services: Dict[str, Any]):
    """
    Update component status in the monitor service.
    
    Args:
        monitor_service: The monitor service instance
        services: Dictionary of service instances
    """
    logger.info("Updating component status...")
    try:
        current_time = datetime.now().isoformat()
        
        for service_name, service in services.items():
            if service_name == "monitor_service":
                continue  # Skip monitor service itself
                
            monitor_service.update_component_status(service_name, "healthy", {
                "class": service.__class__.__name__,
                "initialization_time": current_time
            })
            
        # Also update monitor service status
        monitor_service.update_component_status("monitor_service", "healthy", {
            "class": monitor_service.__class__.__name__,
            "initialization_time": current_time
        })
        
        logger.info("Component status updated successfully")
    except Exception as e:
        logger.error(f"Error updating component status: {str(e)}", exc_info=True)

async def perform_startup_tasks():
    """
    Perform all startup tasks in the correct sequence.
    
    This function orchestrates the initialization of all services
    and performs any additional startup tasks.
    """
    logger.info("Performing startup tasks...")
    
    try:
        # Initialize services
        services = await initialize_services()
        
        # Get service instances
        monitor_service = services["monitor_service"]
        
        # Collect initial metrics
        await collect_initial_metrics(monitor_service)
        
        # Update component status
        await update_component_status(monitor_service, services)
        
        # Set environment variable for tests
        os.environ["SAP_TEST_HARNESS_RUNNING"] = "true"
        
        logger.info("Startup tasks completed successfully")
        return services
    except Exception as e:
        logger.critical(f"Fatal error during startup tasks: {str(e)}", exc_info=True)
        raise

async def perform_shutdown_tasks():
    """
    Perform all shutdown tasks in the correct sequence.
    """
    logger.info("Performing shutdown tasks...")
    
    try:
        # Import here to avoid circular imports
        from services import get_monitor_service
        
        # Get monitor service and log shutdown
        monitor_service = get_monitor_service()
        monitor_service.log_error(
            error_type="system",
            message="Application shutdown initiated",
            component="main",
            context={"event": "shutdown"}
        )
        
        # Remove environment variable
        if "SAP_TEST_HARNESS_RUNNING" in os.environ:
            del os.environ["SAP_TEST_HARNESS_RUNNING"]
            
        logger.info("Shutdown tasks completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown tasks: {str(e)}", exc_info=True)
