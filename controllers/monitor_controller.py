# controllers/monitor_controller.py
"""
Controller for Monitor API endpoints.

This controller provides handlers for system monitoring operations including:
- Health check
- Metrics collection and retrieval
- Error log access
"""

import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from controllers import BaseController
from services import get_monitor_service

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
        if hasattr(request, 'client') and request.client and hasattr(request.client, 'host'):
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

async def api_health_check(request: Request) -> JSONResponse:
    """
    Check system health (API endpoint).
    
    Args:
        request: FastAPI request
        
    Returns:
        JSON response with health check results
    """
    logger.info(f"Health check requested from {get_safe_client_host(request)}")
    monitor_service = get_monitor_service()
    
    try:
        # Perform health check
        health_data = monitor_service.check_system_health()
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
        monitor_service.log_error(
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

async def api_get_metrics(request: Request) -> JSONResponse:
    """
    Get system metrics (API endpoint).
    
    Args:
        request: FastAPI request
        
    Returns:
        JSON response with metrics data
    """
    logger.info(f"Metrics requested from {get_safe_client_host(request)}")
    monitor_service = get_monitor_service()
    
    try:
        # Parse query parameters
        params = await BaseController.parse_query_params(request, MetricsQueryParams)
        logger.debug(f"Metrics query params: hours={params.hours}")
        
        # Get metrics summary
        metrics_summary = monitor_service.get_metrics_summary(hours=params.hours)
        logger.info(f"Metrics retrieved: {metrics_summary.get('count', 0)} data points covering {metrics_summary.get('time_range', {}).get('duration_hours', 0)} hours")
        
        # Return metrics data
        return BaseController.create_success_response(
            data=metrics_summary,
            message="System metrics retrieved successfully"
        )
    except Exception as e:
        # Log error
        logger.error(f"Error in api_get_metrics: {str(e)}", exc_info=True)
        monitor_service.log_error(
            error_type="controller_error",
            message=f"Error in api_get_metrics: {str(e)}",
            component="monitor_controller",
            context={"path": request.url.path, "query_params": str(request.query_params)}
        )
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "server_error",
                "message": f"Failed to retrieve metrics: {str(e)}"
            }
        )

async def api_get_errors(request: Request) -> JSONResponse:
    """
    Get error logs (API endpoint).
    
    Args:
        request: FastAPI request
        
    Returns:
        JSON response with error logs
    """
    logger.info(f"Error logs requested from {get_safe_client_host(request)}")
    monitor_service = get_monitor_service()
    
    try:
        # Parse query parameters
        params = await BaseController.parse_query_params(request, ErrorsQueryParams)
        logger.debug(f"Error query params: type={params.error_type}, component={params.component}, hours={params.hours}, limit={params.limit}")
        
        # Always get detailed error logs with filters
        error_logs = monitor_service.get_error_logs(
            error_type=params.error_type,
            component=params.component,
            hours=params.hours,
            limit=params.limit
        )
        
        # Convert to dictionaries for JSON response
        errors_data = [log.to_dict() for log in error_logs]
        logger.info(f"Retrieved {len(errors_data)} filtered error logs")
        
        # Return error logs with consistent structure
        return BaseController.create_success_response(
            data={
                "errors": errors_data,
                "count": len(errors_data),
                "filters": {
                    "error_type": params.error_type,
                    "component": params.component,
                    "hours": params.hours,
                    "limit": params.limit
                },
                # Include summary data as well
                "by_type": {error_type: sum(1 for log in error_logs if log.error_type == error_type) 
                           for error_type in set(log.error_type for log in error_logs)},
                "by_component": {component: sum(1 for log in error_logs if log.component == component)
                                for component in set(log.component for log in error_logs if log.component)},
                "recent": [log.to_dict() for log in error_logs[:5]]  # First 5 logs (already sorted by timestamp)
            },
            message="Error logs retrieved successfully"
        )
    except Exception as e:
        # Log error (but don't cause an infinite loop if this fails)
        try:
            logger.error(f"Error in api_get_errors: {str(e)}", exc_info=True)
            monitor_service.log_error(
                error_type="controller_error",
                message=f"Error in api_get_errors: {str(e)}",
                component="monitor_controller",
                context={"path": request.url.path, "query_params": str(request.query_params)}
            )
        except Exception as log_error:
            logger.error(f"Failed to log error in api_get_errors: {str(log_error)}")
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "server_error",
                "message": f"Failed to retrieve error logs: {str(e)}"
            }
        )

async def api_collect_metrics(request: Request) -> JSONResponse:
    """
    Collect current system metrics (API endpoint).
    
    Args:
        request: FastAPI request
        
    Returns:
        JSON response with collected metrics
    """
    logger.info(f"Metrics collection requested from {get_safe_client_host(request)}")
    monitor_service = get_monitor_service()
    
    try:
        # Collect current metrics
        metrics = monitor_service.collect_current_metrics()
        logger.info(f"Metrics collected: CPU: {metrics.cpu_percent:.1f}%, Memory: {metrics.memory_usage:.1f}%, Disk: {metrics.disk_usage:.1f}%")
        
        # Return metrics data
        return BaseController.create_success_response(
            data={
                "timestamp": metrics.timestamp.isoformat(),
                "cpu_percent": metrics.cpu_percent,
                "memory_usage": metrics.memory_usage,
                "available_memory": metrics.available_memory,
                "disk_usage": metrics.disk_usage
            },
            message="Metrics collected successfully"
        )
    except Exception as e:
        # Log error
        logger.error(f"Error in api_collect_metrics: {str(e)}", exc_info=True)
        monitor_service.log_error(
            error_type="controller_error",
            message=f"Error in api_collect_metrics: {str(e)}",
            component="monitor_controller",
            context={"path": request.url.path}
        )
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "server_error",
                "message": f"Failed to collect metrics: {str(e)}"
            }
        )
