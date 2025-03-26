# Test Helpers Package

This package implements a facade pattern for the mini-meta-harness test infrastructure, providing a simplified, consistent interface for working with services, controllers, middleware components, and models in tests.

## Components

### Service Imports (`service_imports.py`)

This module centralizes all service imports in one place, making it easy to access all classes and functions related to services.

```python
# Import from the facade instead of directly from service modules
from tests_dest.test_helpers.service_imports import (
    MaterialService, 
    get_material_service, 
    MonitorService
)
```

#### Available Imports:

- **Base Service**: `BaseService`
- **State Management**: `StateManager`, `get_state_manager`
- **Material Services**: `MaterialService`, `get_material_service`, `create_test_material`
- **Monitor Services**: `MonitorService`, `get_monitor_service`, `MonitorHealth`, `MonitorCore`, `MonitorMetrics`, `MonitorErrors`
- **P2P Services**: `P2PService`, `get_p2p_service`, `create_test_order`, `create_test_requisition`
- **Utility Services**: `TemplateService`, `URLService`
- **Controller Classes**: `BaseController` and all controller getter functions
- **Middleware Components**: `SessionMiddleware`, `FlashMessage`, `SessionStore` and session utility functions
- **Models**: `BaseDataModel`, `Material`, `Requisition`, `Order` and all related models and enums

### Test Fixtures (`test_fixtures.py`)

This module provides common pytest fixtures that can be reused across test files.

```python
# Fixtures are automatically available via conftest.py
def test_with_services(real_material_service, real_monitor_service):
    # Test code using real services
    assert real_material_service is not None
    assert real_monitor_service is not None
```

#### Available Fixtures:

- **App Fixtures**: `app`, `real_request`, `test_client`
- **Service Fixtures**: `real_state_manager`, `real_material_service`, `real_monitor_service`, `real_p2p_service`
- **Monitor Component Fixtures**: `real_monitor_health`, `real_monitor_core`, `real_monitor_metrics`, `real_monitor_errors`
- **Utility Service Fixtures**: `real_template_service`, `real_url_service`
- **Controller Fixtures**: `real_material_controller`, `real_material_api_controller`, `real_p2p_controller` and other controllers
- **Session Fixtures**: `real_session_store`, `real_session_middleware`, `test_flash_message`
- **Model Fixtures**: `test_material`, `test_requisition`, `test_order`

### Request Helpers (`request_helpers.py`)

This module provides utilities for creating request objects and handling responses in tests.

```python
from tests_dest.test_helpers.request_helpers import create_test_request, get_json_data

# Create a test request with custom parameters
request = create_test_request(
    path="/api/materials",
    method="POST",
    json_body={"name": "Test Material"}
)

# Extract JSON data from a response
response = await some_endpoint(request)
data = get_json_data(response)
```

#### Available Helper Functions:

- **Request Creation**: `create_test_request` - Creates a FastAPI request with customizable parameters
- **Response Handling**: `get_json_data` - Extracts JSON data from various response types
- **Client Creation**: `create_test_client` - Creates a test client for a FastAPI app
- **Async Testing**: `call_async_endpoint`, `run_async` - Utilities for testing async endpoints
- **Model Conversion**: `model_to_dict` - Converts Pydantic models to dictionaries

## Basic Usage

### Importing Services

```python
# Import from the facade
from tests_dest.test_helpers.service_imports import (
    MaterialService, 
    get_material_service,
    create_test_material_service
)

# Create a service instance
material_service = create_test_material_service()
```

### Using Fixtures

```python
# Fixtures are automatically available through conftest.py
def test_material_creation(real_material_service, test_material):
    # Test using the fixtures
    result = real_material_service.create_material(test_material)
    assert result.id == test_material.id
```

### Creating Test Requests

```python
from tests_dest.test_helpers.request_helpers import create_test_request

# Create a test request
request = create_test_request(
    path="/api/materials",
    query_params={"type": "raw"},
    headers={"Authorization": "Bearer token"},
    method="GET"
)
```

### Testing Controllers

```python
def test_controller(real_material_controller, test_material):
    # Test the controller with the fixture
    result = real_material_controller.get_material(test_material.id)
    assert result.id == test_material.id
```

### Testing with Middleware

```python
def test_with_session(real_session_middleware, app, test_client):
    # Test code using session middleware
    response = test_client.get("/api/session-test")
    assert response.status_code == 200
```

## Benefits

1. **Simplified Imports**: Reduces the complexity of import statements in test files
2. **Consistent Fixtures**: Standardized fixtures for all components of the application
3. **Reduced Duplication**: Eliminates duplicate test setup code across files
4. **Better Readability**: Makes test files cleaner and more focused on test logic
5. **Easier Maintenance**: Changes to service interfaces only need to be updated in one place
6. **Enhanced Async Testing**: Tools for working with asynchronous code in tests
7. **Comprehensive Coverage**: All application components are available through the facade
8. **Proper Dependency Injection**: Service fixtures are created with proper dependencies

## Best Practices

1. **Use Facade Pattern Imports**: Always import services through the facade instead of directly from service modules
2. **Leverage Provided Fixtures**: Use the fixtures provided by the facade pattern whenever possible
3. **Follow Dependency Chains**: When creating custom fixtures, follow the same dependency patterns as in the facade
4. **Organize Imports Logically**: Group imports by component type (services, controllers, etc.)
5. **Delegate Setup to Fixtures**: Use fixtures for setup rather than duplicating setup code in tests
6. **Keep Tests Focused**: Tests should focus on specific functionality, not environment setup
7. **Use Async Helpers**: Leverage the async helpers for testing async endpoints 