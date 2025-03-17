from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from services.monitoring.metrics_service import MetricsService
from services.monitoring.error_service import ErrorService
from services.monitoring.component_service import ComponentService
from services.state_manager import StateManager

router = APIRouter()

# Global state manager instance
state_manager = StateManager()

# Service dependencies
async def get_metrics_service() -> MetricsService:
    """Dependency to get metrics service instance"""
    service = MetricsService(state_manager)
    await service.initialize()
    return service

async def get_error_service() -> ErrorService:
    """Dependency to get error service instance"""
    service = ErrorService(state_manager)
    await service.initialize()
    return service

async def get_component_service() -> ComponentService:
    """Dependency to get component service instance"""
    service = ComponentService(state_manager)
    await service.initialize()
    return service

# Metrics routes
@router.get("/metrics")
async def get_metrics(
    name: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    service: MetricsService = Depends(get_metrics_service)
):
    """Get metrics with optional filtering"""
    return await service.get_metrics(
        name=name,
        start_time=start_time,
        end_time=end_time
    )

@router.post("/metrics/{name}")
async def record_metric(
    name: str,
    value: float,
    tags: Optional[Dict[str, str]] = None,
    service: MetricsService = Depends(get_metrics_service)
):
    """Record a new metric"""
    return await service.record_metric(name, value, tags)

@router.delete("/metrics")
async def clear_metrics(
    older_than: Optional[timedelta] = None,
    service: MetricsService = Depends(get_metrics_service)
):
    """Clear metrics data"""
    return await service.clear_metrics(older_than)

# Error routes
@router.get("/errors")
async def get_errors(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    error_type: Optional[str] = None,
    component: Optional[str] = None,
    severity: Optional[str] = None,
    service: ErrorService = Depends(get_error_service)
):
    """Get error logs with optional filtering"""
    return await service.get_error_logs(
        start_time=start_time,
        end_time=end_time,
        error_type=error_type,
        component=component,
        severity=severity
    )

@router.post("/errors")
async def log_error(
    message: str,
    error_type: str,
    component: str,
    context: Optional[Dict] = None,
    severity: str = "error",
    service: ErrorService = Depends(get_error_service)
):
    """Log a new error"""
    return await service.log_error(
        message=message,
        error_type=error_type,
        component=component,
        context=context,
        severity=severity
    )

@router.get("/errors/summary")
async def get_error_summary(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    service: ErrorService = Depends(get_error_service)
):
    """Get error summary"""
    return await service.get_error_summary(start_time, end_time)

@router.delete("/errors")
async def clear_errors(
    older_than: Optional[timedelta] = None,
    error_type: Optional[str] = None,
    component: Optional[str] = None,
    service: ErrorService = Depends(get_error_service)
):
    """Clear error logs"""
    return await service.clear_error_logs(
        older_than=older_than,
        error_type=error_type,
        component=component
    )

# Component routes
@router.get("/components")
async def get_components(
    component_name: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    service: ComponentService = Depends(get_component_service)
):
    """Get component status"""
    return await service.get_component_status(
        component_name=component_name,
        start_time=start_time,
        end_time=end_time
    )

@router.post("/components/{component_name}")
async def update_component(
    component_name: str,
    status: str,
    details: Optional[Dict] = None,
    service: ComponentService = Depends(get_component_service)
):
    """Update component status"""
    return await service.update_component_status(
        component_name=component_name,
        status=status,
        details=details
    )

@router.get("/components/summary")
async def get_components_summary(
    service: ComponentService = Depends(get_component_service)
):
    """Get components summary"""
    return await service.get_components_summary()

@router.delete("/components")
async def clear_components(
    component_name: Optional[str] = None,
    older_than: Optional[timedelta] = None,
    service: ComponentService = Depends(get_component_service)
):
    """Clear component status"""
    return await service.clear_component_status(
        component_name=component_name,
        older_than=older_than
    ) 