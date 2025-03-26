# Correct Import Patterns for Mini Meta Harness Tests

This document outlines the correct patterns for importing modules, classes, and functions in test files for the Mini Meta Harness project. Following these patterns ensures consistent testing practices and compliance with our test code rules.

## Basic Rules

1. **Always use `tests_dest/test_helpers/service_imports.py`** for all imports
2. **Never import directly from source modules** in test files
3. **Do not create fallback/mock implementations** of services or utilities
4. **Make explicit imports** rather than using wildcard `import *` patterns
5. **Handle import errors transparently** without catching or suppressing them

## Import Pattern Examples

### Correct Import Patterns

#### 1. Service Class Imports

```python
# Correct: Import specific services from service_imports
from tests_dest.test_helpers.service_imports import (
    MaterialService,
    P2PService,
    MonitorService,
    StateManager
)
```

#### 2. Model Class Imports

```python
# Correct: Import models from service_imports
from tests_dest.test_helpers.service_imports import (
    Material,
    MaterialCreate,
    MaterialUpdate,
    Requisition,
    Order,
    RequisitionCreate,
    OrderCreate
)
```

#### 3. Enum Imports

```python
# Correct: Import enums from service_imports
from tests_dest.test_helpers.service_imports import (
    MaterialStatus,
    MaterialType,
    UnitOfMeasure,
    DocumentStatus,
    ProcurementType
)
```

#### 4. Error Class Imports

```python
# Correct: Import error types from service_imports
from tests_dest.test_helpers.service_imports import (
    NotFoundError,
    ValidationError,
    BadRequestError,
    ConflictError
)
```

#### 5. Function Imports

```python
# Correct: Import functions from service_imports
from tests_dest.test_helpers.service_imports import (
    create_test_material,
    create_test_material_service,
    create_test_p2p_service,
    get_material_controller
)
```

#### 6. Service Instance Imports

```python
# Correct: Import pre-configured service instances
from tests_dest.test_helpers.service_imports import (
    material_service,
    p2p_service,
    monitor_service,
    state_manager
)
```

#### 7. Middleware and Utility Imports

```python
# Correct: Import middleware components
from tests_dest.test_helpers.service_imports import (
    SessionMiddleware,
    FlashMessage,
    get_session,
    add_flash_message
)
```

### Incorrect Import Patterns (Avoid These)

#### ❌ Direct Imports from Source Modules

```python
# WRONG: Direct imports from source modules
from services.material_service import MaterialService  # Incorrect
from models.material import Material  # Incorrect
from utils.error_utils import NotFoundError  # Incorrect
```

#### ❌ Wildcard Imports

```python
# WRONG: Wildcard imports 
from tests_dest.test_helpers.service_imports import *  # Avoid in production code
```

#### ❌ Try/Except Import Fallbacks

```python
# WRONG: Try/except with fallbacks
try:
    from services.material_service import MaterialService
except ImportError:
    # Creating mock fallback - WRONG APPROACH
    class MaterialService:
        pass
```

#### ❌ Direct Imports Mixed with service_imports

```python
# WRONG: Mixing direct imports with service_imports
from tests_dest.test_helpers.service_imports import MaterialService
from services.p2p_service import P2PService  # Incorrect mixed import
```

## Import Organization Best Practices

1. **Group imports by category**:
   ```python
   # Services
   from tests_dest.test_helpers.service_imports import (
       MaterialService,
       P2PService,
       MonitorService
   )
   
   # Models
   from tests_dest.test_helpers.service_imports import (
       Material,
       MaterialCreate,
       Order,
       RequisitionCreate
   )
   
   # Error types
   from tests_dest.test_helpers.service_imports import (
       NotFoundError,
       ValidationError
   )
   ```

2. **Import what you need**:
   - Import only the specific classes and functions your test needs
   - Avoid importing unused symbols
   - Keep imports minimal and focused

3. **Order of imports**:
   1. Standard library imports (pytest, unittest, etc.)
   2. Third-party library imports
   3. Service imports from service_imports.py
   4. Import test fixtures last

## Managing Test-Specific Dependencies

For test-specific utilities and fixtures:

```python
# First import from service_imports
from tests_dest.test_helpers.service_imports import (
    MaterialService,
    Material,
    MaterialCreate
)

# Then import test fixtures
from tests_dest.test_helpers.test_fixtures import (
    material_fixture,
    p2p_fixture
)

# Lastly import test-specific utilities
from tests_dest.test_helpers.test_utils import (
    assert_material_equal,
    setup_test_data
)
```

## Handling Circular Imports

If you encounter circular import issues:

1. Import the minimum necessary at the module level
2. Consider function-level imports for specific cases
3. Restructure tests to avoid circular dependencies
4. Do NOT create fallback implementations

## Example Test File Structure

```python
"""
Example test file with proper import patterns.
"""
import pytest
from unittest.mock import MagicMock

# Import from service_imports with explicit imports
from tests_dest.test_helpers.service_imports import (
    # Services
    MaterialService,
    P2PService,
    MonitorService,
    
    # Models
    Material,
    MaterialCreate,
    Requisition,
    
    # Enums
    MaterialStatus,
    DocumentStatus,
    
    # Error types
    NotFoundError,
    ValidationError,
    
    # Helper functions
    create_test_material,
    create_test_material_service
)

# Test fixtures last
from conftest import test_services

class TestExample:
    """Example test class with proper setup."""
    
    def setup(self):
        """Set up test services."""
        self.material_service = create_test_material_service()
        self.material = create_test_material(id="MAT001")
    
    def test_example(self):
        """Example test using properly imported classes."""
        # Creates material using imported service and model
        created = self.material_service.create_material(self.material)
        assert created.id == "MAT001"
        assert isinstance(created, Material)
```

By following these patterns consistently across all test files, we ensure that tests are maintainable, consistent, and properly encapsulated. 