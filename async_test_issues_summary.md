# Async Test Issues Diagnostic Summary

## Problem Description

We encountered multiple issues with async test files after adding the standard test snippet. The main problems are:

1. **Syntax Errors with Async Functions**:
   - Multiple files show `SyntaxError: invalid syntax` with `async` keyword
   - This occurs in both test functions and setup/teardown functions
   - Example error: `SyntaxError: 'await' outside async function`

2. **ModuleType Import Issues**:
   - `ImportError: cannot import name 'ModuleType' from 'typing'`
   - This affects all test files that use the standard snippet

3. **Setup/Teardown Function Conflicts**:
   - Some files have their own setup/teardown functions that conflict with the snippet
   - Mixing of async and non-async setup/teardown functions

## Root Cause Analysis

### 1. Async Function Structure
- The standard snippet adds setup/teardown functions that are non-async
- Some test files have async setup/teardown functions
- Mixing async and non-async functions in the same scope causes syntax errors

### 2. Import Structure
- The standard snippet imports `ModuleType` from `typing`
- `ModuleType` should be imported from `types` module
- This affects all files using the snippet

### 3. Test Environment Setup
- Different test files have different setup requirements
- Some files need async setup, others don't
- The standard snippet doesn't account for these variations

## Current State of Test Files

### Files with Async Setup/Teardown
1. `tests-dest/api/test_controller_diagnostic.py`
   - Has async test functions
   - Mixes async and non-async setup
   - Needs careful handling of async context

2. `tests-dest/api/test_dashboard_diagnostic.py`
   - Uses async test functions
   - Has non-async setup/teardown
   - Demonstrates correct async usage

### Files with Standard Setup
1. `tests-dest/unit/test_base_controller.py`
   - Uses standard snippet setup
   - Has non-async test functions
   - Works correctly with standard setup

## Recommended Approach

1. **Separate Async and Non-Async Tests**:
   - Create separate base snippets for async and non-async tests
   - Allow test files to choose the appropriate snippet

2. **Fix Import Structure**:
   - Move `ModuleType` import to `types` module
   - Update all test files to use correct imports

3. **Standardize Setup/Teardown**:
   - Create async-aware setup/teardown functions
   - Allow for both sync and async operations
   - Maintain backward compatibility

## Next Steps

1. **Create Async-Aware Snippet**:
   ```python
   # For async tests
   async def setup_module(module):
       """Async-aware setup"""
       os.environ["PYTEST_CURRENT_TEST"] = "True"
   
   async def teardown_module(module):
       """Async-aware teardown"""
       if "PYTEST_CURRENT_TEST" in os.environ:
           del os.environ["PYTEST_CURRENT_TEST"]
   ```

2. **Update Import Structure**:
   ```python
   from types import ModuleType  # Correct import
   from typing import Dict, List, Optional, Union, Any  # Other typing imports
   ```

3. **Modify Test Files**:
   - Identify which files need async support
   - Apply appropriate snippet version
   - Fix any remaining syntax issues

## Implementation Plan

1. **Phase 1: Import Fixes**
   - Update standard snippet with correct imports
   - Apply to all test files
   - Verify import errors are resolved

2. **Phase 2: Async Support**
   - Create async-aware snippet version
   - Apply to async test files
   - Verify async functionality

3. **Phase 3: Testing and Validation**
   - Run all tests to verify fixes
   - Document any remaining issues
   - Create test suite for async functionality

## Notes
- Keep diagnostic test files separate from standard test files
- Maintain clear documentation of async requirements
- Consider creating a test helper for async setup/teardown
- Add type hints for async functions 