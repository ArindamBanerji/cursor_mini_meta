# BEGIN_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE
# Critical imports that must be preserved
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

"""Standard test file imports and setup.

This snippet is automatically added to test files by SnippetForTests.py.
It provides:
1. Dynamic project root detection and path setup
2. Environment variable configuration
3. Common test imports and fixtures
4. Service initialization support
"""

# Find project root dynamically
test_file = Path(__file__).resolve()
test_dir = test_file.parent

# Try to find project root by looking for main.py or known directories
project_root: Optional[Path] = None
for parent in [test_dir] + list(test_dir.parents):
    # Check for main.py as an indicator of project root
    if (parent / "main.py").exists():
        project_root = parent
        break
    # Check for typical project structure indicators
    if all((parent / d).exists() for d in ["services", "models", "controllers"]):
        project_root = parent
        break

# If we still don't have a project root, use parent of the tests-dest directory
if not project_root:
    # Assume we're in a test subdirectory under tests-dest
    for parent in test_dir.parents:
        if parent.name == "tests-dest":
            project_root = parent.parent
            break

# Add project root to path if found
if project_root and str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the test_import_helper
try:
    from test_import_helper import setup_test_paths
    setup_test_paths()
except ImportError:
    # Fall back if test_import_helper is not available
    if str(test_dir.parent) not in sys.path:
        sys.path.insert(0, str(test_dir.parent))
    os.environ.setdefault("SAP_HARNESS_HOME", str(project_root) if project_root else "")

# Common test imports
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Import common fixtures and services
try:
    from conftest import test_services
    from services.base_service import BaseService
    from services.monitor_service import MonitorService
    from services.template_service import TemplateService
    from services.p2p_service import P2PService
    from models.base_model import BaseModel
    from models.material import Material
    from models.requisition import Requisition
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
except ImportError as e:
    # Log import error but continue - not all tests need all imports
    import logging
    logging.warning(f"Optional import failed: {e}")
    logging.debug("Stack trace:", exc_info=True)
# END_SNIPPET_INSERTION - DO NOT MODIFY THIS LINE

# tests-dest/api/test_meta_routes.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pytest
from meta_routes import ALL_ROUTES, RouteDefinition, HttpMethod
import re

class TestMetaRoutes:
    """
    Tests for the meta_routes module and the ALL_ROUTES registry.
    Focuses on verifying correct route configuration, especially
    for material and monitor routes.
    """
    
    def test_route_definition_structure(self):
        """Test that the RouteDefinition class has the expected structure"""
        # Create a sample route definition
        route = RouteDefinition(
            name="test_route",
            path="/test",
            methods=[HttpMethod.GET],
            controller="controllers.test_controller.test_action",
            template="test.html"
        )
        
        # Check the fields
        assert route.name == "test_route"
        assert route.path == "/test"
        assert HttpMethod.GET in route.methods
        assert route.controller == "controllers.test_controller.test_action"
        assert route.template == "test.html"
    
    def test_all_routes_not_empty(self):
        """Test that ALL_ROUTES contains routes"""
        assert len(ALL_ROUTES) > 0, "ALL_ROUTES should contain route definitions"
    
    def test_unique_route_names(self):
        """Test that route names are unique"""
        route_names = [route.name for route in ALL_ROUTES]
        assert len(route_names) == len(set(route_names)), "Route names should be unique"
    
    def test_unique_paths(self):
        """Test that route paths are unique for the same HTTP method"""
        # Group routes by HTTP method
        routes_by_method = {}
        for route in ALL_ROUTES:
            for method in route.methods:
                if method not in routes_by_method:
                    routes_by_method[method] = []
                routes_by_method[method].append(route.path)
        
        # Check uniqueness of paths within each HTTP method
        for method, paths in routes_by_method.items():
            # Replace path parameters with a placeholder for comparison
            normalized_paths = [re.sub(r'{[^}]+}', '{param}', path) for path in paths]
            assert len(normalized_paths) == len(set(normalized_paths)), f"Paths should be unique for {method.value}"
    
    def test_valid_http_methods(self):
        """Test that all routes have valid HTTP methods"""
        valid_methods = set(item for item in HttpMethod)
        for route in ALL_ROUTES:
            for method in route.methods:
                assert method in valid_methods, f"Invalid HTTP method {method} in route {route.name}"
    
    def test_path_params_format(self):
        """Test that path parameters are correctly formatted"""
        param_regex = r'{([a-zA-Z0-9_]+)}'
        for route in ALL_ROUTES:
            # Find all parameters in path
            params = re.findall(param_regex, route.path)
            
            # Check that no parameter has invalid characters
            for param in params:
                assert re.match(r'^[a-zA-Z0-9_]+$', param), f"Invalid parameter name '{param}' in route {route.name}"
    
    def test_material_routes_exist(self):
        """Test that the expected material routes exist"""
        required_material_routes = [
            "material_list",
            "material_detail",
            "material_create_form",
            "material_create",
            "material_update_form",
            "material_update",
            "material_deprecate",
            "api_material_list",
            "api_material_detail",
            "api_material_create",
            "api_material_update",
            "api_material_deprecate"
        ]
        
        route_names = [route.name for route in ALL_ROUTES]
        for required_route in required_material_routes:
            assert required_route in route_names, f"Missing required material route: {required_route}"
    
    def test_material_route_params(self):
        """Test material routes with parameters"""
        # Define routes that should have material_id parameter
        material_id_routes = [
            "material_detail",
            "material_update_form",
            "material_update",
            "material_deprecate",
            "api_material_detail",
            "api_material_update",
            "api_material_deprecate"
        ]
        
        # Check each route with material_id parameter
        for route_name in material_id_routes:
            route = next((r for r in ALL_ROUTES if r.name == route_name), None)
            assert route is not None, f"Route {route_name} is missing"
            assert "{material_id}" in route.path, f"Route {route_name} should have material_id parameter"
    
    def test_material_api_routes_prefix(self):
        """Test that material API routes have the correct prefix"""
        api_routes = [r for r in ALL_ROUTES if r.name.startswith("api_material_")]
        assert len(api_routes) > 0, "No material API routes found"
        
        for route in api_routes:
            assert route.path.startswith("/api/v1/materials"), f"API route {route.name} should start with /api/v1/materials"
    
    def test_monitor_api_routes_exist(self):
        """Test that the expected monitor API routes exist"""
        required_monitor_routes = [
            "api_monitor_health",
            "api_monitor_metrics",
            "api_monitor_errors",
            "api_monitor_collect_metrics"
        ]
        
        route_names = [route.name for route in ALL_ROUTES]
        for required_route in required_monitor_routes:
            assert required_route in route_names, f"Missing required monitor route: {required_route}"
    
    def test_monitor_api_routes_prefix(self):
        """Test that monitor API routes have the correct prefix"""
        api_routes = [r for r in ALL_ROUTES if r.name.startswith("api_monitor_")]
        assert len(api_routes) > 0, "No monitor API routes found"
        
        for route in api_routes:
            assert route.path.startswith("/api/v1/monitor"), f"Monitor API route {route.name} should start with /api/v1/monitor"
    
    def test_monitor_routes_controllers(self):
        """Test that monitor routes use the correct controller"""
        monitor_routes = [r for r in ALL_ROUTES if r.name.startswith("api_monitor_")]
        
        for route in monitor_routes:
            assert "controllers.monitor_controller" in route.controller, \
                f"Monitor route {route.name} should use monitor_controller"
    
    def test_monitor_health_route(self):
        """Test the specific health check route configuration"""
        health_route = next((r for r in ALL_ROUTES if r.name == "api_monitor_health"), None)
        assert health_route is not None, "Health check route not found"
        
        assert health_route.path == "/api/v1/monitor/health"
        assert HttpMethod.GET in health_route.methods
        assert health_route.controller == "controllers.monitor_controller.api_health_check"
        assert health_route.template is None  # API routes should not have templates
    
    def test_monitor_metrics_route(self):
        """Test the metrics route configuration"""
        metrics_route = next((r for r in ALL_ROUTES if r.name == "api_monitor_metrics"), None)
        assert metrics_route is not None, "Metrics route not found"
        
        assert metrics_route.path == "/api/v1/monitor/metrics"
        assert HttpMethod.GET in metrics_route.methods
        assert metrics_route.controller == "controllers.monitor_controller.api_get_metrics"
        assert metrics_route.template is None
    
    def test_collect_metrics_route(self):
        """Test the collect metrics route configuration"""
        collect_route = next((r for r in ALL_ROUTES if r.name == "api_monitor_collect_metrics"), None)
        assert collect_route is not None, "Collect metrics route not found"
        
        assert collect_route.path == "/api/v1/monitor/metrics/collect"
        assert HttpMethod.POST in collect_route.methods
        assert collect_route.controller == "controllers.monitor_controller.api_collect_metrics"
        assert collect_route.template is None
    
    def test_error_test_routes_exist(self):
        """Test that error test routes exist for testing error handling"""
        error_test_routes = [
            "test_not_found",
            "test_validation_error",
            "test_bad_request",
            "test_success_response"
        ]
        
        route_names = [route.name for route in ALL_ROUTES]
        for test_route in error_test_routes:
            assert test_route in route_names, f"Missing error test route: {test_route}"
    
    def test_route_naming_conventions(self):
        """Test that routes follow naming conventions"""
        for route in ALL_ROUTES:
            # API routes should start with "api_"
            if route.path.startswith("/api/"):
                assert route.name.startswith("api_"), \
                    f"API route {route.name} should start with 'api_'"
            
            # Test routes should start with "test_"
            if route.path.startswith("/test/"):
                assert route.name.startswith("test_"), \
                    f"Test route {route.name} should start with 'test_'"
    
    def test_dashboard_route(self):
        """Test the dashboard route configuration"""
        dashboard_route = next((r for r in ALL_ROUTES if r.name == "dashboard"), None)
        assert dashboard_route is not None, "Dashboard route not found"
        
        assert dashboard_route.path == "/dashboard"
        assert HttpMethod.GET in dashboard_route.methods
        assert dashboard_route.controller == "controllers.dashboard_controller.show_dashboard"
        assert dashboard_route.template is not None  # Dashboard should have a template
        assert dashboard_route.template == "dashboard.html"
    
    def test_root_route_redirect(self):
        """Test the root route configuration (should redirect to dashboard)"""
        root_route = next((r for r in ALL_ROUTES if r.name == "root"), None)
        assert root_route is not None, "Root route not found"
        
        assert root_route.path == "/"
        assert HttpMethod.GET in root_route.methods
        assert root_route.controller == "controllers.dashboard_controller.redirect_to_dashboard"
        assert root_route.template is None  # Redirect routes shouldn't have templates
