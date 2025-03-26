# Facade Pattern Implementation Plan

## Overview
This plan outlines the steps to implement a dedicated testing package facade pattern for the mini-meta-harness project. This approach will consolidate service imports and test fixtures, simplifying test creation and maintenance.

## Implementation Plan

| Step | Description | Files to Create/Modify | Details |
|------|-------------|------------------------|---------|
| 1 | Create test helpers directory structure | `tests_dest/test_helpers/__init__.py` | Create empty `__init__.py` to make it a proper package |
| 2 | Create service imports module | `tests_dest/test_helpers/service_imports.py` | Consolidate all service imports with consistent naming |
| 3 | Create common test fixtures | `tests_dest/test_helpers/test_fixtures.py` | Define reusable pytest fixtures for all tests |
| 4 | Create request/response helpers | `tests_dest/test_helpers/request_helpers.py` | Add helpers for creating request objects and handling responses |
| 5 | Update existing API test files | Various test files | Update imports and use new fixtures (see detailed list below) |
| 6 | Create test documentation | `tests_dest/test_helpers/README.md` | Document the facade pattern and usage guidelines |
| 7 | Add conftest integration | `tests_dest/conftest.py` | Import and expose fixtures from test_helpers |

## Detailed File Contents

### 1. `tests_dest/test_helpers/__init__.py`
```python
"""Test helpers package for mini-meta-harness.

This package provides consolidated imports and utilities for tests.
"""
```

### 2. `tests_dest/test_helpers/service_imports.py`
```python
"""Consolidated service imports for testing.

This module provides a single location for importing all service
classes and functions used in tests. It follows the facade pattern
to simplify imports and provide consistent naming.
"""

# Base service imports
from services.base_service import BaseService, ServiceContext, ServiceConfig

# Material service imports
from services.material_service import MaterialService, get_material_service
from services.material_controller import list_materials, get_material_by_id

# Monitor service imports
from services.monitor_service import MonitorService, get_monitor_service
from services.monitor_health import MonitorHealth
from services.state_manager import StateManager, get_state_manager

# Helper functions for creating properly configured service instances
def create_test_material_service():
    """Create a properly configured MaterialService for testing."""
    return MaterialService()

def create_test_monitor_service():
    """Create a properly configured MonitorService for testing."""
    return MonitorService()

def create_test_state_manager():
    """Create a properly configured StateManager for testing."""
    return StateManager()
```

### 3. `tests_dest/test_helpers/test_fixtures.py`
```python
"""Common pytest fixtures for mini-meta-harness tests.

This module provides reusable fixtures that can be imported 
into any test file or automatically loaded via conftest.py.
"""

import pytest
from fastapi import FastAPI, Request
from starlette.testclient import TestClient as StarletteTestClient

from .service_imports import (
    MaterialService,
    MonitorService,
    StateManager,
    get_material_service,
    get_monitor_service,
    get_state_manager
)

@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    return FastAPI()

@pytest.fixture
def real_request():
    """Create a real request object for testing."""
    scope = {
        "type": "http",
        "path": "/test",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 50000)
    }
    return Request(scope)

@pytest.fixture
def real_material_service():
    """Create a real MaterialService for testing."""
    return MaterialService()

@pytest.fixture
def real_monitor_service():
    """Create a real MonitorService for testing."""
    return MonitorService()

@pytest.fixture
def real_state_manager():
    """Create a real StateManager for testing."""
    return StateManager()
```

### 4. `tests_dest/test_helpers/request_helpers.py`
```python
"""Request and response helpers for API testing.

This module provides utility functions for creating request objects,
parsing responses, and other common API testing operations.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional

def create_test_request(
    path: str = "/test",
    query_params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    client_host: str = "127.0.0.1"
) -> Request:
    """Create a test request with the specified parameters.
    
    Args:
        path: The request path
        query_params: Optional query parameters
        headers: Optional request headers
        client_host: Client IP address
        
    Returns:
        A Request object configured with the provided parameters
    """
    scope = {
        "type": "http",
        "path": path,
        "query_string": b"&".join(
            f"{k}={v}".encode() for k, v in (query_params or {}).items()
        ),
        "headers": [
            (k.lower().encode(), v.encode()) 
            for k, v in (headers or {}).items()
        ],
        "client": (client_host, 50000)
    }
    return Request(scope)

def get_json_data(response: Response) -> Dict[str, Any]:
    """Extract JSON data from a response object.
    
    Args:
        response: The response object
        
    Returns:
        The parsed JSON data as a dictionary
    """
    if isinstance(response, JSONResponse):
        return response.body_dict
    if hasattr(response, "json"):
        return response.json()
    if hasattr(response, "body"):
        import json
        return json.loads(response.body)
    return {}
```

## Changes to Existing Test Files

| Test File | Required Changes |
|-----------|-----------------|
| `test_api_diagnostic.py` | Update imports, use fixtures from test_helpers |
| `test_asyncio_diagnostic.py` | Update imports, use fixtures from test_helpers |
| `test_controller_diagnostic.py` | Update imports, use fixtures from test_helpers |
| `test_dashboard_diagnostic.py` | Update imports, use fixtures from test_helpers |
| `test_datetime_import_diagnostic.py` | Update imports, use fixtures from test_helpers |
| `test_dependency_diagnostic.py` | Update imports, use fixtures from test_helpers |
| `test_dependency_edge_cases.py` | Update imports, use fixtures from test_helpers |
| `test_dependency_unwrap.py` | Update imports, use fixtures from test_helpers |
| `test_diagnostic_summary.py` | Update imports, use fixtures from test_helpers |

## Example Usage in Test Files

```python
# Import consolidated test helpers
from tests_dest.test_helpers.service_imports import (
    MaterialService,
    MonitorService
)
from tests_dest.test_helpers.test_fixtures import (
    real_request,
    real_material_service,
    real_monitor_service
)
from tests_dest.test_helpers.request_helpers import (
    create_test_request,
    get_json_data
)

# Test function using the facade pattern
def test_example(real_request, real_material_service):
    """Example test using the facade pattern."""
    # Test implementation using the imported fixtures and helpers
    ...
```

## Benefits

1. **Simplified Imports**: Single location for all service-related imports
2. **Consistent Fixtures**: Standardized test fixtures across all test files
3. **Reduced Duplication**: Reuse helper functions instead of duplicating code
4. **Better Readability**: Clear separation of test concerns
5. **Easier Maintenance**: Changes to service interfaces only need updates in one place

## Implementation Timeline

1. Create directory structure and initial files: 1 hour
2. Implement service imports and fixtures: 2 hours
3. Create request/response helpers: 1 hour
4. Update one test file as proof of concept: 1 hour
5. Create documentation: 1 hour
6. Update remaining test files: 4 hours

Total estimated time: 10 hours 