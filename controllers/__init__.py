# controllers/__init__.py
from typing import Dict, Any, Optional, Type, TypeVar, List, Union, Callable
from fastapi import Request, Response, Body, Query, Path, Form, status, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, ValidationError as PydanticValidationError
from services.url_service import url_service
from utils.error_utils import ValidationError, NotFoundError, BadRequestError
import logging

# Import session utilities
from middleware.session import (
    add_flash_message, get_flash_messages, 
    store_form_data, get_form_data,
    get_session_data, set_session_data
)

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
            
            # Store form data in session for redisplay
            try:
                store_form_data(request, form_dict)
            except Exception as session_error:
                logger.warning(f"Could not store form data in session: {str(session_error)}")
            
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
                "message": message,
                "error_code": error_code,
                "details": details
            }
        )
    
    @staticmethod
    def redirect_to_route(
        route_name: str,
        params: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        status_code: int = 303,  # 303 See Other
        flash_message: Optional[str] = None,
        flash_type: str = "success"
    ) -> RedirectResponse:
        """
        Create a redirect response to a named route.
        
        Args:
            route_name: Name of the route to redirect to
            params: Path parameters for the route
            query_params: Query parameters for the route
            status_code: HTTP status code for the redirect
            flash_message: Optional message to flash to the user
            flash_type: Type of flash message (success, error, info, warning)
            
        Returns:
            RedirectResponse to the specified route
        """
        # Generate the URL for the route
        url = url_service.get_url_for_route(route_name, params, query_params)
        
        # Create the redirect response
        response = RedirectResponse(url=url, status_code=status_code)
        
        # Add flash message if provided
        if flash_message:
            # The request is passed as a dependency to the controller function,
            # so we need to access it through the middleware directly
            add_flash_message({"session": {}}, flash_message, flash_type, response)
        
        return response
    
    @staticmethod
    def add_flash_message(request: Request, message: str, type: str = "info") -> None:
        """
        Add a flash message to the session.
        
        Args:
            request: FastAPI request
            message: Message to display
            type: Message type (success, error, info, warning)
        """
        try:
            add_flash_message(request, message, type)
        except Exception as e:
            logger.warning(f"Could not add flash message: {str(e)}")
    
    @staticmethod
    def redirect_with_message(
        route_name: str,
        message: str,
        message_type: str = "success",
        params: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, Any]] = None,
        status_code: int = 303  # 303 See Other
    ) -> RedirectResponse:
        """
        Create a redirect response to a named route with a flash message.
        Convenience method combining redirect_to_route and add_flash_message.
        
        Args:
            route_name: Name of the route to redirect to
            message: Flash message to display
            message_type: Type of flash message (success, error, info, warning)
            params: Path parameters for the route
            query_params: Query parameters for the route
            status_code: HTTP status code for the redirect
            
        Returns:
            RedirectResponse to the specified route with a flash message
        """
        return BaseController.redirect_to_route(
            route_name=route_name,
            params=params,
            query_params=query_params,
            status_code=status_code,
            flash_message=message,
            flash_type=message_type
        )
    
    @staticmethod
    def handle_form_errors(
        request: Request,
        template_name: str,
        context: Dict[str, Any],
        validation_error: ValidationError
    ) -> Dict[str, Any]:
        """
        Handle form validation errors for UI controllers.
        
        Args:
            request: FastAPI request
            template_name: Template to render
            context: Template context
            validation_error: Validation error that occurred
            
        Returns:
            Updated context with error information
            
        This method adds flash messages and populates the context
        with validation errors and previously submitted form data.
        """
        # Extract validation errors
        details = validation_error.details or {}
        validation_errors = details.get("validation_errors", {})
        
        # Add validation errors to the context
        context["validation_errors"] = validation_errors
        
        # Add error message as flash message
        try:
            add_flash_message(request, validation_error.message, "error")
        except Exception as e:
            logger.warning(f"Could not add flash message: {str(e)}")
            # Fall back to adding error to context
            context["error_message"] = validation_error.message
        
        # Get stored form data
        try:
            form_data = get_form_data(request)
            if form_data:
                context["form_data"] = form_data
        except Exception as e:
            logger.warning(f"Could not retrieve form data: {str(e)}")
            # Use submitted data from the validation error if available
            if "submitted_data" in details:
                context["form_data"] = details["submitted_data"]
        
        return context
    
    @staticmethod
    def get_form_data(request: Request) -> Dict[str, Any]:
        """
        Get stored form data from the session.
        
        Args:
            request: FastAPI request
            
        Returns:
            Dictionary of form field values
        """
        try:
            return get_form_data(request) or {}
        except Exception as e:
            logger.warning(f"Could not retrieve form data: {str(e)}")
            return {}
    
    @classmethod
    def dependency_injection(cls, service_getter: Callable) -> Callable:
        """
        Create a dependency injection function for FastAPI.
        
        Args:
            service_getter: Function that returns a service instance
            
        Returns:
            Dependency function for FastAPI
        """
        def get_service():
            try:
                return service_getter()
            except Exception as e:
                logger.error(f"Error getting service: {str(e)}", exc_info=True)
                raise BadRequestError(
                    message=f"Service dependency error: {str(e)}"
                )
        return get_service
    
    @staticmethod
    def handle_api_error(e: Exception) -> JSONResponse:
        """
        Handle API errors for consistent responses.
        
        Args:
            e: Exception that was raised
            
        Returns:
            Standardized error response
        """
        if isinstance(e, ValidationError):
            return BaseController.create_error_response(
                message=e.message,
                error_code="validation_error",
                details=e.details,
                status_code=400
            )
        elif isinstance(e, NotFoundError):
            return BaseController.create_error_response(
                message=e.message,
                error_code="not_found",
                details=e.details,
                status_code=404
            )
        elif isinstance(e, BadRequestError):
            return BaseController.create_error_response(
                message=e.message,
                error_code="bad_request",
                details=e.details,
                status_code=400
            )
        else:
            # For unexpected errors, log them but don't expose details
            logger.error(f"Unexpected API error: {str(e)}", exc_info=True)
            return BaseController.create_error_response(
                message="An unexpected error occurred",
                error_code="server_error",
                status_code=500
            )