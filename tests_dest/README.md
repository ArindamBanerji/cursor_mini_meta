# Mini Meta Harness Testing

This directory contains tests for the Mini Meta Harness project. The tests are organized into different categories:

- `integration/`: Integration tests that test multiple components together
- `unit/`: Unit tests that test individual components in isolation
- `e2e/`: End-to-end tests that test the entire system

## Handling Import Issues

Many tests may encounter import issues due to Python module resolution. 
We've created an import helper module to resolve these issues.

### Using the Import Helper

To use the import helper, add these lines at the beginning of your test file, 
before any other imports:

```python
from tests-dest.import_helper import fix_imports
fix_imports()  # Configures the Python path for proper imports
```

### What the Import Helper Does

The import helper:

1. Identifies the project root directory
2. Cleans up module cache to avoid stale imports
3. Sets up Python path to find all modules correctly
4. Sets required environment variables for tests

### Example Test File

```python
"""
Example test file using the import helper.
"""

# Import the helper at the very top of your file
from tests-dest.import_helper import fix_imports
fix_imports()

# Now you can import any project module
import pytest
from services.state_manager import StateManager
from services.monitor_service import MonitorService
from utils.error_utils import NotFoundError, create_error_response

# Your test code follows
def test_something():
    # Test implementation
    assert True
```

### Getting a Clean StateManager

If your test needs a clean StateManager instance, you can use:

```python
from tests-dest.import_helper import get_clean_state_manager
state_manager = get_clean_state_manager()
```

### Troubleshooting

If you're still experiencing import issues:

1. Make sure `fix_imports()` is called before any other imports
2. Run import_helper.py directly to check if imports work: `python tests-dest/import_helper.py`
3. Try running your test with PYTHONPATH set to the project root:
   ```
   PYTHONPATH=/path/to/mini_meta_harness python -m pytest tests-dest/your_test.py
   ```
4. Check the conftest.py file for any conflicts with import paths

## Error Response Format

All error responses follow this JSON structure:

```json
{
  "success": false,
  "error_code": "not_found",  // The error type code
  "message": "Resource not found",
  "details": {
    // Additional context-specific details
    "resource_id": "MAT001",
    "resource_type": "Material"
  }
}
```

Key error codes include:
- `not_found`: Resource not found (404)
- `validation_error`: Invalid input data (400)
- `authentication_error`: Authentication failure (401)
- `authorization_error`: Permission denied (403)
- `conflict`: Conflict with existing data (409)
- `internal_error`: Server error (500) 