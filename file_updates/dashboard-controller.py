# controllers/dashboard_controller.py
from fastapi import Request
from fastapi.responses import RedirectResponse
from typing import Dict, Any, List
from services.state_manager import state_manager
from controllers import BaseController
from datetime import datetime, timedelta

async def show_dashboard(request: Request) -> Dict[str, Any]:
    """
    Renders the dashboard with system metrics and statistics
    """
    # Get current visit count from state and increment
    visit_count = state_manager.get("dashboard_visits", 0)
    visit_count += 1
    state_manager.set("dashboard_visits", visit_count)
    
    # Get last visit time
    last_visit = state_manager.get("last_dashboard_visit", "First visit")
    
    # Set current visit time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    state_manager.set("last_dashboard_visit", current_time)
    
    # Get P2P statistics
    p2p_stats = get_p2p_statistics()
    
    # Get system health status
    system_health = get_system_health()
    
    # Get recent activities
    recent_activities = get_recent_activities()
    
    return {
        "welcome_message": "Welcome to the SAP Test Harness!",
        "visit_count": visit_count,
        "last_visit": last_visit,
        "current_time": current_time,
        "p2p_stats": p2p_stats,
        "system_health": system_health,
        "recent_activities": recent_activities
    }

async def redirect_to_dashboard(request: Request) -> RedirectResponse:
    """
    Redirects from root '/' to '/dashboard'
    
    This is a GET redirect, so we use 302 Found status code
    to indicate a temporary redirect without method change.
    """
    # Use BaseController's redirect method with 302 Found for GET redirect
    return BaseController.redirect_to_route(
        "dashboard",
        status_code=302  # Use 302 Found for GET redirects
    )

def get_p2p_statistics() -> Dict[str, Any]:
    """
    Get statistics for the P2P module.
    
    Returns:
        Dictionary with P2P statistics
    """
    try:
        # Import here to avoid circular imports
        from services import get_p2p_service
        p2p_service = get_p2p_service()
        
        # Get requisitions and orders
        requisitions = p2p_service.list_requisitions()
        orders = p2p_service.list_orders()
        
        # Count items by status
        req_status_counts = {}
        for status in ["DRAFT", "SUBMITTED", "APPROVED", "REJECTED", "ORDERED", "CANCELED"]:
            req_status_counts[status] = len([r for r in requisitions if r.status.value == status])
        
        order_status_counts = {}
        for status in ["DRAFT", "SUBMITTED", "APPROVED", "REJECTED", 
                        "RECEIVED", "PARTIALLY_RECEIVED", "COMPLETED", "CANCELED"]:
            order_status_counts[status] = len([o for o in orders if o.status.value == status])
        
        # Calculate total values
        total_requisition_value = sum(r.total_value for r in requisitions)
        total_order_value = sum(o.total_value for o in orders)
        
        # Calculate open value (approved but not ordered)
        open_requisition_value = sum(r.total_value for r in requisitions 
                                    if r.status.value == "APPROVED")
        
        # Calculate pending order value (approved but not received)
        pending_order_value = sum(o.total_value for o in orders 
                                 if o.status.value == "APPROVED")
        
        # Calculate recent activity (last 7 days)
        one_week_ago = datetime.now() - timedelta(days=7)
        recent_requisitions = len([r for r in requisitions 
                                  if r.created_at > one_week_ago])
        recent_orders = len([o for o in orders
                           if o.created_at > one_week_ago])
        
        return {
            "total_requisitions": len(requisitions),
            "total_orders": len(orders),
            "requisition_status_counts": req_status_counts,
            "order_status_counts": order_status_counts,
            "total_requisition_value": round(total_requisition_value, 2),
            "total_order_value": round(total_order_value, 2),
            "open_requisition_value": round(open_requisition_value, 2),
            "pending_order_value": round(pending_order_value, 2),
            "recent_requisitions": recent_requisitions,
            "recent_orders": recent_orders
        }
    except Exception as e:
        # In case of any errors, return empty statistics
        return {
            "total_requisitions": 0,
            "total_orders": 0,
            "requisition_status_counts": {},
            "order_status_counts": {},
            "total_requisition_value": 0,
            "total_order_value": 0,
            "open_requisition_value": 0,
            "pending_order_value": 0,
            "recent_requisitions": 0,
            "recent_orders": 0,
            "error": str(e)
        }

def get_system_health() -> Dict[str, Any]:
    """
    Get system health information.
    
    Returns:
        Dictionary with system health data
    """
    try:
        # Import here to avoid circular imports
        from services import get_monitor_service
        monitor_service = get_monitor_service()
        
        # Get health check results
        health_data = monitor_service.check_system_health()
        
        # Get current metrics
        metrics = monitor_service.collect_current_metrics()
        
        # Combine data
        return {
            "status": health_data.get("status", "unknown"),
            "components": health_data.get("components", {}),
            "metrics": {
                "cpu_percent": round(metrics.cpu_percent, 1),
                "memory_usage": round(metrics.memory_usage, 1),
                "disk_usage": round(metrics.disk_usage, 1),
                "timestamp": metrics.timestamp.isoformat()
            }
        }
    except Exception as e:
        # In case of any errors, return minimal health data
        return {
            "status": "error",
            "error": str(e),
            "metrics": {
                "cpu_percent": 0,
                "memory_usage": 0,
                "disk_usage": 0,
                "timestamp": datetime.now().isoformat()
            }
        }

def get_recent_activities() -> List[Dict[str, Any]]:
    """
    Get recent system activities.
    
    Returns:
        List of recent activity records
    """
    try:
        # Import here to avoid circular imports
        from services import get_monitor_service
        monitor_service = get_monitor_service()
        
        # Get recent error logs (excluding monitoring)
        error_logs = monitor_service.get_error_logs(
            hours=24,
            limit=5
        )
        
        # Format for display
        activities = []
        for log in error_logs:
            # Skip monitoring-related logs
            if log.component == "monitor_service" or log.error_type == "info":
                continue
                
            activities.append({
                "timestamp": log.timestamp,
                "message": log.message,
                "component": log.component,
                "type": log.error_type
            })
        
        # Add some P2P activities if available
        try:
            from services import get_p2p_service
            p2p_service = get_p2p_service()
            
            # Get recent requisitions and orders
            requisitions = p2p_service.list_requisitions()
            orders = p2p_service.list_orders()
            
            # Sort by created_at (newest first)
            recent_requisitions = sorted(
                requisitions, 
                key=lambda r: r.created_at, 
                reverse=True
            )[:3]
            
            recent_orders = sorted(
                orders, 
                key=lambda o: o.created_at, 
                reverse=True
            )[:3]
            
            # Add as activities
            for req in recent_requisitions:
                activities.append({
                    "timestamp": req.created_at,
                    "message": f"Requisition {req.document_number} created: {req.description}",
                    "component": "p2p_service",
                    "type": "requisition_created",
                    "document_number": req.document_number
                })
                
            for order in recent_orders:
                activities.append({
                    "timestamp": order.created_at,
                    "message": f"Order {order.document_number} created: {order.description}",
                    "component": "p2p_service",
                    "type": "order_created",
                    "document_number": order.document_number
                })
        except Exception:
            # Ignore errors from P2P service
            pass
        
        # Sort all activities by timestamp (newest first)
        activities.sort(key=lambda a: a["timestamp"], reverse=True)
        
        # Return top 10
        return activities[:10]
    except Exception as e:
        # In case of any errors, return empty list
        return [
            {
                "timestamp": datetime.now(),
                "message": f"Error retrieving activities: {str(e)}",
                "component": "dashboard_controller",
                "type": "error"
            }
        ]
