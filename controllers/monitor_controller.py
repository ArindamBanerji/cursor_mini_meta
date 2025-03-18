# controllers/monitor_controller.py
"""
Controller for Monitor API endpoints.

This controller provides handlers for system monitoring operations including:
- Health check
- Metrics collection and retrieval
- Error log access
"""

import logging
from fastapi import Request, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import os

from controllers import BaseController
from services.monitor_service import get_monitor_service, monitor_service

# Configure logging
logger = logging.getLogger("monitor_controller")

def get_safe_client_host(request: Request) -> str:
    """
    Safely get the client host from a request.
    
    Args:
        request: FastAPI request
        
    Returns:
        Client host string or 'unknown' if not available
    """
    try:
        # In test environments, always return a test client host
        if os.environ.get('TEST_MODE') == 'true':
            return 'test-client'
            
        # Check if request has client attribute and it's not None
        if hasattr(request, 'client') and request.client is not None:
            # Check if client has host attribute
            if hasattr(request.client, 'host'):
                return request.client.host
        return 'unknown'
    except Exception:
        return 'unknown'

# Pydantic models for request validation

class MetricsQueryParams(BaseModel):
    """Parameters for metrics queries"""
    hours: Optional[int] = Field(None, ge=1, le=168)  # Max 7 days

class ErrorsQueryParams(BaseModel):
    """Parameters for error log queries"""
    hours: Optional[int] = Field(None, ge=1, le=168)
    error_type: Optional[str] = None
    component: Optional[str] = None
    limit: Optional[int] = Field(None, ge=1, le=1000)

# API Controller methods

async def api_health_check(request: Request, monitor_service_param = None):
    """
    API endpoint for health check.
    
    Args:
        request: FastAPI request
        monitor_service_param: Optional monitor service for dependency injection in tests
        
    Returns:
        JSON response with health check results
    """
    logger.info(f"Health check requested from {get_safe_client_host(request)}")
    
    try:
        # Use provided service or default
        service = monitor_service_param if monitor_service_param is not None else monitor_service
        
        # Perform health check
        health_data = service.check_system_health()
        logger.info(f"Health check completed with status: {health_data['status']}")
        
        # Determine response status code based on health status
        status_code = 200
        if health_data["status"] == "error":
            status_code = 503  # Service Unavailable
            logger.warning(f"Health check returning 503 Service Unavailable (status: error)")
        elif health_data["status"] == "warning":
            status_code = 429  # Too Many Requests (we're using this for warnings)
            logger.warning(f"Health check returning 429 Too Many Requests (status: warning)")
        else:
            logger.info(f"Health check returning 200 OK (status: healthy)")
        
        # Log components contributing to the overall status
        components = health_data.get("components", {})
        for component_name, component_data in components.items():
            logger.debug(f"Component {component_name}: {component_data.get('status', 'unknown')}")
        
        # Return health check results with the appropriate status code
        return JSONResponse(
            status_code=status_code,
            content=health_data
        )
    except Exception as e:
        # Log error
        logger.error(f"Error in api_health_check: {str(e)}", exc_info=True)
        service.log_error(
            error_type="controller_error",
            message=f"Error in api_health_check: {str(e)}",
            component="monitor_controller",
            context={"path": request.url.path}
        )
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to perform health check",
                "error": str(e)
            }
        )

async def api_get_metrics(request: Request, monitor_service_param = None) -> JSONResponse:
    """
    Get system metrics (API endpoint).
    
    Args:
        request: FastAPI request
        monitor_service_param: Optional monitor service for dependency injection in tests
        
    Returns:
        JSON response with metrics data
    """
    logger.info(f"Metrics requested from {get_safe_client_host(request)}")
    
    try:
        # Use provided service or default
        service = monitor_service_param if monitor_service_param is not None else monitor_service
        
        # Parse query parameters
        params = await BaseController.parse_query_params(request, MetricsQueryParams)
        logger.debug(f"Metrics query params: hours={params.hours}")
        
        # Get metrics summary
        metrics_summary = service.get_metrics_summary(hours=params.hours)
        logger.info(f"Metrics retrieved: {metrics_summary.get('count', 0)} data points covering {metrics_summary.get('time_range', {}).get('duration_hours', 0)} hours")
        
        # Return metrics data
        return BaseController.create_success_response(
            data=metrics_summary,
            message="Metrics retrieved successfully"
        )
    except Exception as e:
        # Log error
        logger.error(f"Error in api_get_metrics: {str(e)}", exc_info=True)
        service.log_error(
            error_type="controller_error",
            message=f"Error in api_get_metrics: {str(e)}",
            component="monitor_controller",
            context={"path": str(request.url.path)}
        )
        return BaseController.create_error_response(str(e))

async def api_get_errors(request: Request, monitor_service_param = None) -> JSONResponse:
    """
    Get error logs (API endpoint).
    
    Args:
        request: FastAPI request
        monitor_service_param: Optional monitor service for dependency injection in tests
        
    Returns:
        JSON response with error logs data
    """
    logger.info(f"Error logs requested from {get_safe_client_host(request)}")
    
    try:
        # Use provided service or default
        service = monitor_service_param if monitor_service_param is not None else monitor_service
        
        # Parse query parameters
        params = await BaseController.parse_query_params(request, ErrorsQueryParams)
        logger.debug(f"Errors query params: type={params.error_type}, component={params.component}, hours={params.hours}, limit={params.limit}")
        
        # Get error logs
        errors = service.get_error_logs(error_type=params.error_type, component=params.component, hours=params.hours, limit=params.limit)
        
        # Convert to dict format for response
        error_dicts = [error.to_dict() for error in errors]
        logger.info(f"Retrieved {len(error_dicts)} filtered error logs")
        
        # Get summary statistics
        error_types = {}
        error_components = {}
        for error in errors:
            error_type = error.error_type
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            component = error.component
            error_components[component] = error_components.get(component, 0) + 1
        
        # Prepare response data
        response_data = {
            "errors": error_dicts,
            "count": len(error_dicts),
            "filters": {
                "error_type": params.error_type,
                "component": params.component,
                "hours": params.hours,
                "limit": params.limit
            },
            "by_type": error_types,
            "by_component": error_components,
            "recent": error_dicts[:5]  # Include first 5 as "recent" for convenience
        }
        
        # Return success response with error logs data
        return BaseController.create_success_response(
            data=response_data,
            message="Error logs retrieved successfully"
        )
    except Exception as e:
        # Log error
        logger.error(f"Error in api_get_errors: {str(e)}", exc_info=True)
        service.log_error(
            error_type="controller_error",
            message=f"Error in api_get_errors: {str(e)}",
            component="monitor_controller",
            context={"path": str(request.url.path)}
        )
        return BaseController.create_error_response(str(e))

async def api_collect_metrics(request: Request, monitor_service_param = None) -> JSONResponse:
    """
    Trigger metrics collection (API endpoint).
    
    Args:
        request: FastAPI request
        monitor_service_param: Optional monitor service for dependency injection in tests
        
    Returns:
        JSON response with collection status
    """
    logger.info(f"Metrics collection requested from {get_safe_client_host(request)}")
    
    try:
        # Use provided service or default
        service = monitor_service_param if monitor_service_param is not None else monitor_service
        
        # Collect metrics
        metrics = service.collect_current_metrics()
        logger.info(f"Metrics collected successfully: {metrics.timestamp}")
        
        # Return success response with the collected metrics
        return BaseController.create_success_response(
            data=metrics.to_dict(),
            message="Metrics collected successfully"
        )
    except Exception as e:
        # Log error
        logger.error(f"Error in api_collect_metrics: {str(e)}", exc_info=True)
        service.log_error(
            error_type="controller_error",
            message=f"Error in api_collect_metrics: {str(e)}",
            component="monitor_controller",
            context={"path": str(request.url.path)}
        )
        return BaseController.create_error_response(str(e))
