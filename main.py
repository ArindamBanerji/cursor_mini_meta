# main.py
"""
Main application module for the SAP Test Harness.
This module initializes the FastAPI application, sets up middleware,
and registers routes and event handlers.
"""

import logging
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError

from services.template_service import TemplateService
from utils.error_utils import setup_exception_handlers
from router_builder import register_routes
from service_initializer import perform_startup_tasks, perform_shutdown_tasks
from middleware.session import SessionMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("sap_test_harness")

# Define lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler that runs on startup and shutdown.
    Replaces the deprecated on_event handlers.
    """
    # Startup logic
    logger.info("SAP Test Harness v1.7 starting...")
    
    try:
        # Perform all startup tasks
        services = await perform_startup_tasks()
        logger.info("SAP Test Harness started successfully")
        
        # Yield control back to FastAPI
        yield
        
        # Shutdown logic
        logger.info("SAP Test Harness shutting down...")
        
        try:
            # Perform all shutdown tasks
            await perform_shutdown_tasks()
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}", exc_info=True)
        
        logger.info("SAP Test Harness shutdown complete")
    except Exception as e:
        logger.critical(f"Fatal error during startup: {str(e)}", exc_info=True)
        # Re-raise the exception to prevent the application from starting with
        # improperly initialized services
        raise

# Create FastAPI app with the lifespan handler
app = FastAPI(
    title="SAP Test Harness",
    description="Test API for SAP Integration",
    version="1.7.0",
    lifespan=lifespan
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    session_cookie="sap_session",
    secure=False,  # Set to True in production with HTTPS
    expiry_minutes=30
)

# Set up error handlers
setup_exception_handlers(app)

# Add specific handler for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"Request validation error: {str(exc)}")
    return await request_validation_exception_handler(request, exc)

# Create template service instance
template_service = TemplateService()
logger.info("Template service initialized")

# Try to mount static files if directory exists
try:
    logger.info("Attempting to mount static files")
    static_dir = "static"
    if os.path.exists(static_dir) and os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        logger.info(f"Static files mounted from '{static_dir}' directory")
    else:
        logger.warning(f"Static directory '{static_dir}' not found")
except Exception as e:
    logger.warning(f"Could not mount static files: {str(e)}")

# Register routes
register_routes(app, template_service)

# These startup and shutdown functions are kept for backward compatibility
# with the existing tests, but they're no longer used directly by FastAPI
async def startup_event():
    """
    Initialize application services on startup.
    This ensures all services are properly initialized
    when the application starts.
    """
    logger.info("SAP Test Harness v1.7 starting...")
    
    try:
        # Perform all startup tasks
        await perform_startup_tasks()
        logger.info("SAP Test Harness started successfully")
    except Exception as e:
        logger.critical(f"Fatal error during startup: {str(e)}", exc_info=True)
        # Re-raise the exception to prevent the application from starting with
        # improperly initialized services
        raise

async def shutdown_event():
    """
    Clean up resources on application shutdown.
    """
    logger.info("SAP Test Harness shutting down...")
    
    try:
        # Perform all shutdown tasks
        await perform_shutdown_tasks()
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)
    
    logger.info("SAP Test Harness shutdown complete")

# For running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)