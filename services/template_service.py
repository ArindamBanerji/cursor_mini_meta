# services/template_service.py
"""
Template service for rendering HTML templates.

This service provides a consistent interface for rendering Jinja2 templates
and generating URLs for routes.
"""

from fastapi import Request, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from services.url_service import url_service
from typing import Dict, Any, Optional, Union, List

class TemplateService:
    """
    Service for rendering Jinja2 templates and handling URLs.
    """
    
    def __init__(self, templates_dir: str = "templates"):
        """
        Initialize the template service.
        
        Args:
            templates_dir: Directory containing template files
        """
        self.templates = Jinja2Templates(directory=templates_dir)
        
        # Add url_for function to templates
        self.templates.env.globals["url_for"] = self.url_for
    
    def url_for(self, name: str, params: Optional[Dict[str, Any]] = None, query_params: Optional[Dict[str, Any]] = None, **kwargs) -> str:
        """
        Generate URL for a route by name, to be used in templates.
        Supports both dictionary params and keyword arguments.
        
        Args:
            name: Name of the route
            params: Parameters for the route as a dictionary (optional)
            query_params: Query parameters as a dictionary (optional)
            **kwargs: Additional parameters as keyword arguments
            
        Returns:
            Formatted URL string
        """
        path_params = None
        
        # If params is provided as a dictionary, use it
        if isinstance(params, dict):
            path_params = params
        # Otherwise, extract path params from kwargs
        elif kwargs:
            # Extract parameters with a reserved kwarg for query_params
            if 'query_params' in kwargs and path_params is None:
                query_params = kwargs.pop('query_params')
            
            # Use remaining kwargs as path params
            path_params = kwargs if kwargs else None
            
        # Call the url service with the appropriate parameters
        return url_service.get_url_for_route(name, path_params, query_params)

    def render_template(self, request: Request, template_name: str, context: Dict[str, Any]) -> HTMLResponse:
        """
        Render a template with the given context, adding the request object.
        Always returns an HTMLResponse with the rendered template.
        
        Args:
            request: FastAPI request object
            template_name: Name of the template to render
            context: Context data for the template
            
        Returns:
            HTMLResponse with the rendered template
        """
        # Ensure the request is included in the context
        template_context = {"request": request}
        template_context.update(context)
        
        # Render the template and create an HTMLResponse
        response = self.templates.TemplateResponse(
            template_name,
            template_context
        )
        
        # Ensure we're returning an HTMLResponse
        if not isinstance(response, HTMLResponse):
            return HTMLResponse(
                content=response.body,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        return response