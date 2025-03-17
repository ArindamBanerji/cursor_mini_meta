# router_builder.py
"""
Module for building FastAPI routes from the meta-routes registry.
This separates route-building logic from the main application code.
"""

import importlib
import logging
from typing import List, Callable
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from meta_routes import ALL_ROUTES, HttpMethod, RouteDefinition

# Configure logging
logger = logging.getLogger("router_builder")

def get_controller_func(route: RouteDefinition) -> Callable:
    """
    Dynamically import the controller function from the string reference.
    e.g. "controllers.dashboard_controller.show_dashboard"
    
    Args:
        route: The route definition containing the controller reference
        
    Returns:
        The controller function
        
    Raises:
        ImportError: If the module cannot be imported
        AttributeError: If the function is not found in the module
    """
    logger.debug(f"Importing controller function: {route.controller}")
    try:
        module_name, func_name = route.controller.rsplit(".", 1)
        mod = importlib.import_module(module_name)
        return getattr(mod, func_name)
    except ImportError as e:
        logger.error(f"Failed to import module for controller: {route.controller} - {str(e)}")
        raise
    except AttributeError as e:
        logger.error(f"Controller function not found: {route.controller} - {str(e)}")
        raise

def create_endpoint_handler(handler: Callable, route_def: RouteDefinition, template_service):
    """
    Create an endpoint handler for a specific controller function and route definition.
    This ensures each route gets its own dedicated handler with properly bound values.
    
    Args:
        handler: The controller function to handle the request
        route_def: The route definition containing path, template, etc.
        template_service: Service for rendering templates
    
    Returns:
        An async function that can be used as a FastAPI endpoint handler
    """
    async def endpoint(request: Request):
        try:
            logger.debug(f"Handling request for route: {route_def.path}")
            
            # Extract path parameters from request path
            path_params = extract_path_params(route_def.path, request.url.path)
            
            # Call the handler with the request object and path parameters
            if path_params:
                result = await handler(request, **path_params)
            else:
                result = await handler(request)
            
            # CRITICAL: Check for Response objects and return them directly
            if isinstance(result, Response):
                logger.debug(f"Handler returned a {type(result).__name__}, returning directly")
                return result
                
            # If result is a dict and there's a template, render with TemplateService
            if isinstance(result, dict) and route_def.template:
                logger.debug(f"Rendering template: {route_def.template}")
                return template_service.render_template(request, route_def.template, result)
            
            # Otherwise, just return the result as-is
            return result
        except Exception as e:
            # Log the error but re-raise it to be handled by the global exception handlers
            logger.error(f"Error in endpoint {route_def.path}: {str(e)}", exc_info=True)
            
            # Get monitor service to log the error
            try:
                from services import get_monitor_service
                monitor_service = get_monitor_service()
                monitor_service.log_error(
                    error_type="endpoint_error",
                    message=f"Error in endpoint {route_def.path}: {str(e)}",
                    component="endpoint_handler",
                    context={"route": route_def.path, "method": ",".join([m.value for m in route_def.methods])}
                )
            except Exception as log_error:
                logger.error(f"Failed to log error: {str(log_error)}")
            
            raise
    
    # Set function name and docstring for better debugging
    endpoint.__name__ = f"{route_def.name}_endpoint"
    endpoint.__doc__ = f"Endpoint handler for {route_def.path}"
    
    return endpoint

def extract_path_params(path_template: str, actual_path: str) -> dict:
    """
    Extract path parameters from the actual path based on the template.
    
    Args:
        path_template: The route path template with parameter placeholders
        actual_path: The actual request path
        
    Returns:
        Dictionary of extracted path parameters
    """
    path_params = {}
    
    if '{' in path_template and '}' in path_template:
        # Extract path parameter names from template
        param_names = []
        segments = path_template.split('/')
        for segment in segments:
            if segment.startswith('{') and segment.endswith('}'):
                param_name = segment[1:-1]  # Remove the { and }
                param_names.append(param_name)
        
        # Extract path parameter values from actual path
        actual_segments = actual_path.split('/')
        if len(actual_segments) == len(segments):
            for i, (template_seg, actual_seg) in enumerate(zip(segments, actual_segments)):
                if template_seg.startswith('{') and template_seg.endswith('}'):
                    param_name = template_seg[1:-1]
                    path_params[param_name] = actual_seg
    
    return path_params

def register_routes(app: FastAPI, template_service) -> int:
    """
    Register all routes from meta_routes.py with the FastAPI app.
    
    Args:
        app: The FastAPI application instance
        template_service: Service for rendering templates
        
    Returns:
        The number of routes successfully registered
    """
    logger.info("Registering routes from meta_routes.py")
    route_count = 0
    
    for route_def in ALL_ROUTES:
        try:
            # Get the controller function
            controller_func = get_controller_func(route_def)
            
            # Create endpoint handler with bound values for this specific route
            endpoint_handler = create_endpoint_handler(controller_func, route_def, template_service)
            
            # Register the endpoint with FastAPI based on HTTP method
            methods = register_route_methods(app, route_def, endpoint_handler)
            
            logger.debug(f"Registered route: {route_def.path} [{','.join(methods)}] -> {route_def.controller}")
            route_count += 1
        except Exception as e:
            logger.error(f"Failed to register route {route_def.path}: {str(e)}", exc_info=True)
    
    logger.info(f"Registered {route_count} routes from meta_routes.py")
    return route_count

def register_route_methods(app: FastAPI, route_def: RouteDefinition, endpoint_handler: Callable) -> List[str]:
    """
    Register the endpoint handler with the FastAPI app for all HTTP methods in the route definition.
    
    Args:
        app: The FastAPI application instance
        route_def: The route definition
        endpoint_handler: The endpoint handler function
        
    Returns:
        List of HTTP methods that were registered
    """
    methods = []
    
    if HttpMethod.GET in route_def.methods:
        app.get(
            route_def.path, 
            name=route_def.name, 
            response_class=HTMLResponse if route_def.template else None
        )(endpoint_handler)
        methods.append("GET")
    
    if HttpMethod.POST in route_def.methods:
        app.post(
            route_def.path, 
            name=route_def.name
        )(endpoint_handler)
        methods.append("POST")
    
    if HttpMethod.PUT in route_def.methods:
        app.put(
            route_def.path, 
            name=route_def.name
        )(endpoint_handler)
        methods.append("PUT")
    
    if HttpMethod.DELETE in route_def.methods:
        app.delete(
            route_def.path, 
            name=route_def.name
        )(endpoint_handler)
        methods.append("DELETE")
    
    if HttpMethod.PATCH in route_def.methods:
        app.patch(
            route_def.path,
            name=route_def.name
        )(endpoint_handler)
        methods.append("PATCH")
    
    return methods
