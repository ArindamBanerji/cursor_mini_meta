"""
Route definitions for the Mini Meta Harness application.

This module defines:
1. The RouteDefinition class for structured route specifications
2. ALL_ROUTES collection containing all application routes
"""

from typing import NamedTuple, List, Optional
from routes.http_method import HttpMethod

class RouteDefinition(NamedTuple):
    """
    Definition of a route in the application.
    
    Attributes:
        name: Unique identifier for the route
        path: URL path pattern
        methods: HTTP methods supported by this route
        controller: Path to the controller function (dot notation)
        template: Optional template path for rendered views
    """
    name: str
    path: str
    methods: List[HttpMethod]
    controller: str
    template: Optional[str] = None

# Complete collection of all application routes
ALL_ROUTES: List[RouteDefinition] = [
    # Dashboard routes
    RouteDefinition(
        name="root",
        path="/",
        methods=[HttpMethod.GET],
        controller="controllers.dashboard_controller.redirect_to_dashboard",
        template=None
    ),
    RouteDefinition(
        name="dashboard",
        path="/dashboard",
        methods=[HttpMethod.GET],
        controller="controllers.dashboard_controller.show_dashboard",
        template="dashboard.html"
    ),
    
    # Material UI routes - Note: Specific routes come before parameterized routes
    RouteDefinition(
        name="material_list",
        path="/materials",
        methods=[HttpMethod.GET],
        controller="controllers.material_controller.list_materials",
        template="material/list.html"
    ),
    RouteDefinition(
        name="material_create_form",
        path="/materials/create",
        methods=[HttpMethod.GET],
        controller="controllers.material_controller.create_material_form",
        template="material/create.html"
    ),
    RouteDefinition(
        name="material_create",
        path="/materials/create",
        methods=[HttpMethod.POST],
        controller="controllers.material_controller.create_material",
        template="material/create.html"
    ),
    # Parameterized material routes come after specific routes
    RouteDefinition(
        name="material_detail",
        path="/materials/{material_id}",
        methods=[HttpMethod.GET],
        controller="controllers.material_controller.get_material",
        template="material/detail.html"
    ),
    RouteDefinition(
        name="material_update_form",
        path="/materials/{material_id}/edit",
        methods=[HttpMethod.GET],
        controller="controllers.material_controller.update_material_form",
        template="material/create.html"
    ),
    RouteDefinition(
        name="material_update",
        path="/materials/{material_id}/edit",
        methods=[HttpMethod.POST],
        controller="controllers.material_controller.update_material",
        template="material/create.html"
    ),
    RouteDefinition(
        name="material_deprecate",
        path="/materials/{material_id}/deprecate",
        methods=[HttpMethod.GET],
        controller="controllers.material_controller.deprecate_material",
        template=None
    ),
    
    # Material API routes
    RouteDefinition(
        name="api_material_list",
        path="/api/v1/materials",
        methods=[HttpMethod.GET],
        controller="controllers.material_controller.api_list_materials",
        template=None
    ),
    RouteDefinition(
        name="api_material_detail",
        path="/api/v1/materials/{material_id}",
        methods=[HttpMethod.GET],
        controller="controllers.material_controller.api_get_material",
        template=None
    ),
    RouteDefinition(
        name="api_material_create",
        path="/api/v1/materials",
        methods=[HttpMethod.POST],
        controller="controllers.material_controller.api_create_material",
        template=None
    ),
    RouteDefinition(
        name="api_material_update",
        path="/api/v1/materials/{material_id}",
        methods=[HttpMethod.PUT],
        controller="controllers.material_controller.api_update_material",
        template=None
    ),
    RouteDefinition(
        name="api_material_deprecate",
        path="/api/v1/materials/{material_id}/deprecate",
        methods=[HttpMethod.POST],
        controller="controllers.material_controller.api_deprecate_material",
        template=None
    ),
    
    # P2P Requisition UI Routes
    RouteDefinition(
        name="requisition_list",
        path="/p2p/requisitions",
        methods=[HttpMethod.GET],
        controller="controllers.p2p_controller.list_requisitions",
        template="p2p/requisition/list.html"
    ),
    RouteDefinition(
        name="requisition_create_form",
        path="/p2p/requisitions/create",
        methods=[HttpMethod.GET],
        controller="controllers.p2p_controller.create_requisition_form",
        template="p2p/requisition/create.html"
    ),
    RouteDefinition(
        name="requisition_create",
        path="/p2p/requisitions/create",
        methods=[HttpMethod.POST],
        controller="controllers.p2p_controller.create_requisition",
        template="p2p/requisition/create.html"
    ),
    RouteDefinition(
        name="requisition_detail",
        path="/p2p/requisitions/{document_number}",
        methods=[HttpMethod.GET],
        controller="controllers.p2p_controller.get_requisition",
        template="p2p/requisition/detail.html"
    ),
    RouteDefinition(
        name="requisition_update_form",
        path="/p2p/requisitions/{document_number}/edit",
        methods=[HttpMethod.GET],
        controller="controllers.p2p_controller.update_requisition_form",
        template="p2p/requisition/create.html"
    ),
    RouteDefinition(
        name="requisition_update",
        path="/p2p/requisitions/{document_number}/edit",
        methods=[HttpMethod.POST],
        controller="controllers.p2p_controller.update_requisition",
        template="p2p/requisition/create.html"
    ),
    
    # P2P Order UI Routes
    RouteDefinition(
        name="order_list",
        path="/p2p/orders",
        methods=[HttpMethod.GET],
        controller="controllers.p2p_controller.list_orders",
        template="p2p/order/list.html"
    ),
    RouteDefinition(
        name="order_create_form",
        path="/p2p/orders/create",
        methods=[HttpMethod.GET],
        controller="controllers.p2p_controller.create_order_form",
        template="p2p/order/create.html"
    ),
    RouteDefinition(
        name="order_create",
        path="/p2p/orders/create",
        methods=[HttpMethod.POST],
        controller="controllers.p2p_controller.create_order",
        template="p2p/order/create.html"
    ),
    RouteDefinition(
        name="order_detail",
        path="/p2p/orders/{document_number}",
        methods=[HttpMethod.GET],
        controller="controllers.p2p_controller.get_order",
        template="p2p/order/detail.html"
    ),
    RouteDefinition(
        name="order_update_form",
        path="/p2p/orders/{document_number}/edit",
        methods=[HttpMethod.GET],
        controller="controllers.p2p_controller.update_order_form",
        template="p2p/order/create.html"
    ),
    RouteDefinition(
        name="order_update",
        path="/p2p/orders/{document_number}/edit",
        methods=[HttpMethod.POST],
        controller="controllers.p2p_controller.update_order",
        template="p2p/order/create.html"
    ),
    RouteDefinition(
        name="order_receive_form",
        path="/p2p/orders/{document_number}/receive",
        methods=[HttpMethod.GET],
        controller="controllers.p2p_controller.receive_order_form",
        template="p2p/order/receive.html"
    ),
    
    # P2P Requisition API Routes
    RouteDefinition(
        name="api_requisition_list",
        path="/api/v1/p2p/requisitions",
        methods=[HttpMethod.GET],
        controller="controllers.p2p_controller.api_list_requisitions",
        template=None
    ),
    RouteDefinition(
        name="api_requisition_detail",
        path="/api/v1/p2p/requisitions/{document_number}",
        methods=[HttpMethod.GET],
        controller="controllers.p2p_controller.api_get_requisition",
        template=None
    ),
    RouteDefinition(
        name="api_requisition_create",
        path="/api/v1/p2p/requisitions",
        methods=[HttpMethod.POST],
        controller="controllers.p2p_controller.api_create_requisition",
        template=None
    ),
    RouteDefinition(
        name="api_requisition_update",
        path="/api/v1/p2p/requisitions/{document_number}",
        methods=[HttpMethod.PUT],
        controller="controllers.p2p_controller.api_update_requisition",
        template=None
    ),
    RouteDefinition(
        name="api_requisition_submit",
        path="/api/v1/p2p/requisitions/{document_number}/submit",
        methods=[HttpMethod.POST],
        controller="controllers.p2p_controller.api_submit_requisition",
        template=None
    ),
    RouteDefinition(
        name="api_requisition_approve",
        path="/api/v1/p2p/requisitions/{document_number}/approve",
        methods=[HttpMethod.POST],
        controller="controllers.p2p_controller.api_approve_requisition",
        template=None
    ),
    RouteDefinition(
        name="api_requisition_reject",
        path="/api/v1/p2p/requisitions/{document_number}/reject",
        methods=[HttpMethod.POST],
        controller="controllers.p2p_controller.api_reject_requisition",
        template=None
    ),
    
    # P2P Order API Routes
    RouteDefinition(
        name="api_order_list",
        path="/api/v1/p2p/orders",
        methods=[HttpMethod.GET],
        controller="controllers.p2p_controller.api_list_orders",
        template=None
    ),
    RouteDefinition(
        name="api_order_detail",
        path="/api/v1/p2p/orders/{document_number}",
        methods=[HttpMethod.GET],
        controller="controllers.p2p_controller.api_get_order",
        template=None
    ),
    RouteDefinition(
        name="api_order_create",
        path="/api/v1/p2p/orders",
        methods=[HttpMethod.POST],
        controller="controllers.p2p_controller.api_create_order",
        template=None
    ),
    RouteDefinition(
        name="api_order_from_requisition",
        path="/api/v1/p2p/requisitions/{requisition_number}/create-order",
        methods=[HttpMethod.POST],
        controller="controllers.p2p_controller.api_create_order_from_requisition",
        template=None
    ),
    RouteDefinition(
        name="api_order_update",
        path="/api/v1/p2p/orders/{document_number}",
        methods=[HttpMethod.PUT],
        controller="controllers.p2p_controller.api_update_order",
        template=None
    ),
    RouteDefinition(
        name="api_order_submit",
        path="/api/v1/p2p/orders/{document_number}/submit",
        methods=[HttpMethod.POST],
        controller="controllers.p2p_controller.api_submit_order",
        template=None
    ),
    RouteDefinition(
        name="api_order_approve",
        path="/api/v1/p2p/orders/{document_number}/approve",
        methods=[HttpMethod.POST],
        controller="controllers.p2p_controller.api_approve_order",
        template=None
    ),
    RouteDefinition(
        name="api_order_receive",
        path="/api/v1/p2p/orders/{document_number}/receive",
        methods=[HttpMethod.POST],
        controller="controllers.p2p_controller.api_receive_order",
        template=None
    ),
    RouteDefinition(
        name="api_order_complete",
        path="/api/v1/p2p/orders/{document_number}/complete",
        methods=[HttpMethod.POST],
        controller="controllers.p2p_controller.api_complete_order",
        template=None
    ),
    RouteDefinition(
        name="api_order_cancel",
        path="/api/v1/p2p/orders/{document_number}/cancel",
        methods=[HttpMethod.POST],
        controller="controllers.p2p_controller.api_cancel_order",
        template=None
    ),
    
    # Monitor API routes
    RouteDefinition(
        name="api_monitor_health",
        path="/api/v1/monitor/health",
        methods=[HttpMethod.GET],
        controller="controllers.monitor_controller.api_health_check",
        template=None
    ),
    RouteDefinition(
        name="api_monitor_metrics",
        path="/api/v1/monitor/metrics",
        methods=[HttpMethod.GET],
        controller="controllers.monitor_controller.api_get_metrics",
        template=None
    ),
    RouteDefinition(
        name="api_monitor_errors",
        path="/api/v1/monitor/errors",
        methods=[HttpMethod.GET],
        controller="controllers.monitor_controller.api_get_errors",
        template=None
    ),
    RouteDefinition(
        name="api_monitor_collect_metrics",
        path="/api/v1/monitor/metrics/collect",
        methods=[HttpMethod.POST],
        controller="controllers.monitor_controller.api_collect_metrics",
        template=None
    ),
    
    # Error test routes (for manual testing of error handling)
    RouteDefinition(
        name="test_not_found",
        path="/test/not-found",
        methods=[HttpMethod.GET],
        controller="controllers.error_test_controller.test_not_found",
        template=None
    ),
    RouteDefinition(
        name="test_validation_error",
        path="/test/validation-error",
        methods=[HttpMethod.GET],
        controller="controllers.error_test_controller.test_validation_error",
        template=None
    ),
    RouteDefinition(
        name="test_bad_request",
        path="/test/bad-request",
        methods=[HttpMethod.GET],
        controller="controllers.error_test_controller.test_bad_request",
        template=None
    ),
    RouteDefinition(
        name="test_success_response",
        path="/test/success-response",
        methods=[HttpMethod.GET],
        controller="controllers.error_test_controller.test_success_response",
        template=None
    )
] 