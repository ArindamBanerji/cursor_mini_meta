from enum import Enum

class HttpMethod(str, Enum):
    """HTTP methods supported by the application"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH" 