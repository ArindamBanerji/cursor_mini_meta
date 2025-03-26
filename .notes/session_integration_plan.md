# Session Integration Implementation Plan

## Root Cause Analysis

Based on the test failures and provided code, there are several key issues:

1. **Error Classes Missing**:
   - `ValidationError` and `NotFoundError` are referenced but not found
   - These classes are needed by controller error handling flows

2. **Controller Implementation Mismatches**:
   - `process_create_requisition_form` function is missing or not correctly defined
   - `list_requisitions` has an incorrect signature (missing `template_service` parameter)

3. **Function Name/Signature Mismatches**:
   - Some tests refer to `set_form_data` when the actual implementation uses `store_form_data`
   - Async/sync function signature inconsistencies

4. **Template Integration**:
   - Flash messages and form data need to be properly integrated into templates
   - Templates need to display validation errors from session data

## Current State Analysis

### Working Components
- Session middleware is fully implemented and working (all unit tests pass)
- Flash message storage and retrieval are working correctly
- Form data preservation and retrieval are working correctly

### Existing Implementation
- `session_utils.py` has proper utility functions for controllers to integrate with session middleware
- Controllers like `p2p_requisition_ui_controller.py` already have some session integration
- `template_integration.md` provides a plan for template updates

## Step-by-Step Implementation Plan

### Phase 1: Setup Diagnostic Environment

1. **Create Diagnostic Test File for Controller Integration**
   - Similar to `session_debug.py` but focusing on controller integration
   - Test how controllers interact with session middleware directly
   - Validate error handling patterns

2. **Create Core Exception Classes**
   - Implement `utils/error_utils.py` or confirm it exists with required exception classes
   - Ensure `ValidationError` and `NotFoundError` are correctly defined
   - Make sure they're properly imported in controllers

### Phase 2: Fix Controller Implementations

1. **Fix Function Signature Issues**
   - Update `list_requisitions` to accept the `template_service` parameter
   - Check if `process_create_requisition_form` exists or needs to be created
   - Verify all function signatures match what tests expect

2. **Apply Session Integration Pattern**
   - Use the utilities from `session_utils.py` consistently
   - Ensure all form handlers correctly handle:
     - Success cases (add flash messages, redirect)
     - Error cases (store form data, add error messages)

3. **Create Missing Controller Functions**
   - Implement any missing controller functions referenced in tests
   - Follow the pattern shown in existing controllers

### Phase 3: Template Integration

1. **Create Base Layout Template**
   - Implement `templates/layout.html` with flash message support
   - Follow the structure from `template_integration.md`

2. **Create Form Input Macros**
   - Implement reusable form components that handle:
     - Form value retention from session data
     - Display of validation errors
     - Correct styling (Bootstrap classes)

3. **Update Existing Templates**
   - Modify form templates to use the new macros
   - Ensure all templates extend the base layout

### Phase 4: Testing and Validation

1. **Run Integration Tests Incrementally**
   - Start with simpler tests that require fewer fixes
   - Fix issues one by one, validating after each fix
   - Document patterns that work for future reference

2. **End-to-End Manual Testing**
   - Test key user flows with session integration
   - Verify flash messages display correctly
   - Verify form data is preserved on validation errors

## Detailed Action Items

### 1. Confirm Error Classes Exist

```python
# Check if utils/error_utils.py exists with required exceptions
class ValidationError(Exception):
    """Exception raised for validation errors in form data."""
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors or {}

class NotFoundError(Exception):
    """Exception raised when a requested resource is not found."""
    pass
```

### 2. Fix Controller Function Signatures

- Update `list_requisitions` signature in all UI controllers to include template_service:
```python
async def list_requisitions(
    request: Request,
    p2p_service=None,
    monitor_service=None,
    template_service=None  # Add this parameter
):
```

### 3. Implement Controller Integration Pattern

For each form processing controller function, implement this pattern:
```python
async def process_form(request, **services):
    try:
        # Parse form data
        form_data = await self.parse_form_data(request)
        
        # Process data with service
        result = await service.process(form_data)
        
        # Add success flash message and redirect
        return await redirect_with_success(
            url=success_url,
            request=request,
            message="Operation completed successfully"
        )
    except ValidationError as e:
        # Handle validation errors
        await handle_form_validation_error(request, form_data, e.errors)
        return RedirectResponse(url=form_url, status_code=303)
    except Exception as e:
        # Handle other errors
        await handle_form_error(request, form_data, str(e))
        return RedirectResponse(url=form_url, status_code=303)
```

### 4. Base Layout Template Implementation

Create a well-structured base template that all other templates can extend, with proper flash message handling according to the pattern in `template_integration.md`. 