# Datetime Import Issue in `_get_iso_timestamp` Method

## Problem Description

The test is failing with a `NameError` related to the `datetime` module. This occurs because the `_get_iso_timestamp` method in `monitor_health.py` is trying to use the `datetime` module without importing it within the method scope.

### Error Message
```
NameError: name 'datetime' is not defined
```

### Root Cause
The issue is in the `_get_iso_timestamp` method of the `MonitorHealth` class in `monitor_health.py`. The method attempts to call `datetime.now()` but the `datetime` module is not imported within the method's scope.

This is a common issue when:
1. The module is imported at the file level but not visible in the method's scope
2. The import statement is missing entirely
3. There's a circular import issue preventing the module from being loaded

## Solution

### Option 1: Import within Method Scope (Recommended)
Add the import statement for `datetime` within the method scope:

```python
def _get_iso_timestamp(self) -> str:
    """
    Get current time as ISO 8601 timestamp.
    
    Returns:
        ISO formatted timestamp string
    """
    from datetime import datetime  # Import datetime within function scope
    return datetime.now().isoformat()
```

This approach ensures that the `datetime` module is available when the method is called, regardless of any imports at the file level.

### Option 2: Import at File Level
Ensure the `datetime` module is imported at the file level:

```python
from datetime import datetime

# ... rest of the file ...

def _get_iso_timestamp(self) -> str:
    """
    Get current time as ISO 8601 timestamp.
    
    Returns:
        ISO formatted timestamp string
    """
    return datetime.now().isoformat()
```

## Why This Works

Importing the module within the method scope ensures that:
1. The module is available when the method is called
2. It avoids potential circular import issues
3. It makes the method more self-contained and less dependent on file-level imports

## Testing the Fix

After applying the fix, run the test again:

```
python -m pytest monitoring/test_monitor_controller.py::TestMonitorController::test_health_check_endpoint -v
```

The test should now pass without the `NameError`. 