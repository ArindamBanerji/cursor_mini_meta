# controllers/__init__.py
from typing import Dict, Any, Optional, Type, TypeVar, List, Union, Callable
from fastapi import Request, Response, Body, Query, Path, Form, status, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, ValidationError as PydanticValidationError
from services.url_service import url_service
from utils.error_utils import ValidationError, NotFoundError, BadRequestError
import logging

# Configure logging
logger = logging.getLogger("controllers")

# Type variable for Pydantic models
T = TypeVar('T', bound=BaseModel)

class BaseController:
    """
    Base controller class with common methods for request handling.
    Provides utilities for parsing requests, handling validation,
    and generating consistent responses.
    """
    
    @staticmethod
    async def parse_json_body(request: Request, model_class: Type[T]) -> T:
        """
        Parse and validate request body against a Pydantic model.
        
        Args:
            request: FastAPI request
            model_class: Pydantic model class to validate against
            
        Returns:
            Validated model instance
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Read the request body
            body_bytes = await request.body()
            
            # If the body is empty, provide clear error
            if not body_bytes:
                raise ValidationError(
                    message="Request body cannot be empty",
                    details={"body": "No JSON data provided"}
                )
                
            # Parse the request body as JSON
            json_body = await request.json()
            
            # Validate against the model
            return model_class(**json_body)
            
        except PydanticValidationError as e:
            # Process validation errors into a more usable format
            validation_errors = {}
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                validation_errors[field] = error["msg"]
            
            # Log validation errors
            logger.warning(f"Validation error in request body: {validation_errors}")
            
            # Raise our application-level ValidationError
            raise ValidationError(
                message="Invalid request data",
                details={"validation_errors": validation_errors}
            )
        except ValueError as e:
            # This happens when request.json() fails because of invalid JSON
            logger.warning(f"Invalid JSON in request body: {str(e)}")
            raise BadRequestError(
                message=f"Invalid JSON in request body: {str(e)}"
            )
        except Exception as e:
            # Handle any other errors
            logger.error(f"Error parsing request body: {str(e)}", exc_info=True)
            raise BadRequestError(
                message=f"Error parsing request body: {str(e)}"
            )
    
    @staticmethod
    async def parse_query_params(request: Request, model_class: Type[T]) -> T:
        """
        Parse and validate query parameters against a Pydantic model.
        
        Args:
            request: FastAPI request
            model_class: Pydantic model class to validate against
            
        Returns:
            Validated model instance
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Convert query params to dictionary
            query_params = dict(request.query_params)
            
            # Validate against the model
            return model_class(**query_params)
            
        except PydanticValidationError as e:
            # Process validation errors into a more usable format
            validation_errors = {}
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                validation_errors[field] = error["msg"]
            
            # Log validation errors
            logger.warning(f"Validation error in query params: {validation_errors}")
            
            # Raise our application-level ValidationError
            raise ValidationError(
                message="Invalid query parameters",
                details={"validation_errors": validation_errors}
            )
        except Exception as e:
            # Handle any other errors
            logger.error(f"Error parsing query parameters: {str(e)}", exc_info=True)
            raise BadRequestError(
                message=f"Error parsing query parameters: {str(e)}"
            )
    
    @staticmethod
    async def parse_form_data(request: Request, model_class: Type[T]) -> T:
        """
        Parse and validate form data against a Pydantic model.
        Uses an async approach for form data handling.
        
        Args:
            request: FastAPI request
            model_class: Pydantic model class to validate against
            
        Returns:
            Validated model instance
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Get form data asynchronously
            form_data = await request.form()
            
            # Convert form data to dictionary
            form_dict = {}
            for key, value in form_data.items():
                form_dict[key] = value
                
            # Validate against the model
            return model_class(**form_dict)
            
        except PydanticValidationError as e:
            # Process validation errors into a more usable format
            validation_errors = {}
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"])
                validation_errors[field] = error["msg"]
            
            # Store the form data for later use
            form_dict = {}
            try:
                form_data = await request.form()
                for key, value in form_data.items():
                    form_dict[key] = value
            except Exception as form_error:
                logger.warning(f"Could not retrieve form data for error context: {str(form_error)}")
            
            # Log validation errors
            logger.warning(f"Validation error in form data: {validation_errors}")
            
            # Raise our application-level ValidationError
            raise ValidationError(
                message="Invalid form data",
                details={
                    "validation_errors": validation_errors,
                    "submitted_data": form_dict
                }
            )
        except Exception as e:
            # Handle any other errors
            logger.error(f"Error parsing form data: {str(e)}", exc_info=True)
            raise BadRequestError(
                message=f"Error parsing form data: {str(e)}"
            )
    
    @staticmethod
    def create_success_response(
        data: Any = None, 
        message: str = "Success", 
        status_code: int = 200
    ) -> JSONResponse:
        """
        Create a standardized success response.
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            
        Returns:
            Standardized JSON response
        """
        return JSONResponse(
            status_code=status_code,
            content={
                "success": True,
                "message": message,
                "data": data
            }
        )
    
    @staticmethod
    def create_error_response(
        message: str,
        error_code: str = "error",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400
    ) -> JSONResponse:
        """
        Create a standardized error response.
        
        Args:
            message: Error message
            error_code: Error code identifier
            details: Error details
            status_code: HTTP status code
            
        Returns:
            Standardized JSON response
        """
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error": error_code,
                "message": message,
                "details": details or {}
            }
        )
    
    @staticmethod
    def redirect_to_route(
        route_name: str, 
        params: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        status_code: int = 303  # 303 See Other
    ) -> RedirectResponse:
        """
        Create a redirect response to a named route.
        
        Args:
            route_name: Name of the route to redirect to
            params: Optional route parameters
            query_params: Optional query parameters
            status_code: HTTP status code for the redirect
            
        Returns:
            RedirectResponse to the generated URL
        """
        # Get the base URL for the route
        url = url_service.get_url_for_route(route_name, params)
        
        # Add query parameters if provided
        if query_params:
            query_string = "&".join(f"{key}={value}" for key, value in query_params.items())
            url = f"{url}?{query_string}"
            
        # Create and return the redirect response
        return RedirectResponse(url=url, status_code=status_code)
    
    @staticmethod
    def handle_form_errors(
        request: Request,
        template_name: str,
        context: Dict[str, Any],
        validation_error: ValidationError
    ) -> Dict[str, Any]:
        """
        Handle validation errors for form submissions.
        
        Args:
            request: FastAPI request
            template_name: Template name for rendering
            context: Current template context
            validation_error: The validation error
            
        Returns:
            Updated template context with error information
        """
        # Add error information to the context
        updated_context = context.copy()
        
        # Add validation errors
        updated_context["errors"] = validation_error.details.get("validation_errors", {})
        
        # Add general error message
        updated_context["error_message"] = validation_error.message
        
        # Add submitted form data if available
        form_data = validation_error.details.get("submitted_data")
        if form_data:
            updated_context["form_data"] = form_data
            
        # Log the error
        logger.warning(f"Form validation error in {template_name}: {validation_error.message}")
        
        return updated_context
    
    @classmethod
    def dependency_injection(cls, service_getter: Callable) -> Callable:
        """
        Create a FastAPI dependency for injecting services.
        This improves testability by allowing service mocking.
        
        Args:
            service_getter: Function that returns a service instance
            
        Returns:
            A dependency callable for FastAPI
        """
        def get_service():
            return service_getter()
        
        # Set a name for easier debugging
        get_service.__name__ = f"get_{service_getter.__name__}"
        
        return Depends(get_service)