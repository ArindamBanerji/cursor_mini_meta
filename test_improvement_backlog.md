# Test Improvement Backlog

## A. Diagnostic Tests Creation

### A.1 Sync/Async Boundary Tests
- [x] Create `test_sync_async_boundary.py`
  - Test state manager integration
  - Verify sync/async boundaries
  - Test performance implications
  - Document patterns for state management

### A.2 FastAPI Parameter Extraction Tests
- [x] Create `test_fastapi_parameter_extraction.py`
  - Test parameter validation
  - Test request body handling
  - Test query parameter handling
  - Test path parameter handling

### A.3 Service Layer Cleanliness Tests
- [x] Create `test_service_layer_cleanliness.py`
  - Test service initialization
  - Test service state management
  - Test service error handling
  - Test service lifecycle

## B. Current Issues Fixes

### B.1 API Test Fixes
- [x] Fix syntax error in `test_material_controller.py`
- [x] Verify FastAPI endpoint tests
- [x] Test error handling in API endpoints
- [x] Test API response formats
- [x] Fix `test_dependency_unwrap.py` and `test_real_controller` function
- [x] Fix `test_recommended_approach.py` test functions for proper mocking
- [x] Fix `test_session_integration.py` to ensure proper session state management
- [x] Fix `test_session_diagnostics.py` to allow shared session store for testing
- [x] Fix `test_get_material_mock.py` coroutine handling issue
- [x] Fix `test_main.py` import issues and exception handling

### B.2 Unit Test Completion
- [x] Complete base service test implementation
- [x] Add service initialization tests
- [x] Add service state management tests
- [x] Add service error handling tests

### B.3 Monitoring Test Verification
- [x] Verify datetime issue resolution
- [x] Test health check endpoint
- [x] Test metrics collection
- [x] Test error logging
- [x] Fix time-based filtering in `test_get_error_logs_with_filters`

### B.4 Session Middleware Tests
- [x] Improve `TestSessionMiddleware` class to support shared session store
- [x] Fix `test_flash_message_display_in_template` to properly test flash message rendering
- [x] Fix `test_session_cookie_persistence` to verify cookie-based session persistence
- [ ] Create isolation tests for session-dependent controllers
- [ ] Add comprehensive tests for session expiry and cleanup
- [ ] Ensure session store is properly isolated between test runs

### B.5 Non-API Test Fixes
- [ ] Manually fix indentation errors in high-priority integration tests
  - [ ] Fix `test_p2p_workflow.py` (IndentationError on line 21)
  - [ ] Fix `test_material_p2p_integration.py` (IndentationError on line 21)
  - [ ] Fix `test_monitor_service_integration.py` (IndentationError on line 21)
  - [ ] Fix `test_error_integration.py` (IndentationError on line 21)
  - [ ] Fix `test_integration.py` (IndentationError on line 22)
- [ ] Manually fix indentation errors in high-priority unit tests
  - [ ] Fix `test_base_service.py` (IndentationError on line 21)
  - [ ] Fix `test_state_manager.py` (IndentationError on line 21)
  - [ ] Fix `test_session_middleware.py` (IndentationError on line 21)
  - [ ] Fix `test_error_utils.py` (IndentationError on line 21)
  - [ ] Fix `test_template_service.py` (IndentationError on line 21)
- [ ] Create a standardized snippet with correct indentation for future reference
- [ ] Document the proper format of test file setup blocks
- [ ] Test each fixed file individually after manual correction
- [ ] Verify test helper imports after fixing indentation issues

## C. Additional Test Suites

### C.1 Model Tests
- [x] Test data model validation
- [x] Test model serialization
- [x] Test model relationships
- [x] Test model constraints

### C.2 Service Tests
- [x] Test service dependencies
- [x] Test service communication
- [x] Test service state transitions
- [x] Test service error recovery

### C.3 Integration Tests
- [x] Test end-to-end workflows
- [x] Test system interactions
- [x] Test data flow
- [x] Test error propagation

## D. Test Infrastructure

### D.1 Environment Setup
- [x] Enhance `SetProjEnv.ps1`
- [x] Add environment validation
- [x] Improve error messages
- [x] Add path verification

### D.2 Test Isolation
- [x] Implement virtual environment support
- [x] Add test data isolation
- [x] Add state isolation
- [x] Add dependency isolation
- [ ] Improve session middleware isolation for tests
- [ ] Create standardized approach for mock session data

### D.3 Test Documentation
- [x] Create comprehensive list of application files
- [x] Create comprehensive list of test files
- [x] Update codebase architecture documentation
- [ ] Add detailed test descriptions to architecture documentation
- [ ] Document session-related test patterns and utilities
- [ ] Document correct structure of test file setup blocks to avoid indentation errors

## E. Remaining Challenges

### E.1 Preventing Test Regressions
- [ ] Implement CI/CD pipeline for automated testing
- [ ] Create test coverage reports
- [ ] Set up automatic test execution on commits
- [ ] Create baseline performance metrics
- [ ] Implement linting to catch syntax issues early
- [ ] Create a test file validation step in the CI pipeline

### E.2 Test Refactoring
- [ ] Reduce test duplication
- [ ] Improve test naming consistency
- [ ] Enhance test documentation
- [ ] Standardize assertion patterns
- [ ] Extract common test utilities into dedicated helper modules
- [ ] Create consistent patterns for mock middleware in tests
- [ ] Create a standard template for new test files with correct imports and structure

### E.3 Edge Case Testing
- [ ] Add stress tests for state manager
- [ ] Test race conditions in service initialization
- [ ] Test error recovery in edge cases
- [ ] Test system behavior under load
- [ ] Test session handling under concurrent requests
- [ ] Test flash message behavior in complex redirect scenarios

## F. Session Management Improvements

### F.1 Session Architecture
- [ ] Review global session store implementation
- [ ] Consider more robust session backend options
- [ ] Document session lifecycle and interactions
- [ ] Create diagnostic visualizations for session flows

### F.2 Session Testing Utilities
- [x] Improve `TestSessionMiddleware` implementation
- [ ] Create reusable fixtures for session testing
- [ ] Develop standard patterns for controller tests with sessions
- [ ] Document best practices for session-dependent tests

### F.3 Session Security
- [ ] Audit session cookie settings
- [ ] Test session hijacking prevention
- [ ] Verify CSRF protection
- [ ] Test session expiry functionality

## G. Warning Remediation

### G.1 Deprecation Warnings
- [ ] Fix Pydantic V2 deprecation warnings (`__fields__` to `model_fields`)
- [ ] Fix distutils deprecation warnings (replace with packaging.version)
- [ ] Address deprecated cookie setting in httpx client

### G.2 Runtime Warnings
- [ ] Fix coroutines that are never awaited
  - [ ] Fix `add_flash_message` coroutine not awaited in material controller
  - [ ] Fix coroutine warnings in async/sync boundary tests
  - [ ] Fix setup_module coroutine not awaited in minimal_async test

### G.3 Pytest Warnings
- [ ] Fix PytestReturnNotNoneWarning by using assert instead of return in tests
- [ ] Fix PytestCollectionWarning for classes with __init__ constructors

### G.4 Other Warnings
- [ ] Fix psutil getargs format deprecation warning

## Current Focus
1. ~~Fix syntax error in `test_material_controller.py`~~
2. ~~Complete unit test implementation in `test_base_service.py`~~
3. ~~Verify monitoring test coverage~~
4. ~~Fix time-based filtering in `test_get_error_logs_with_filters`~~
5. ~~Fix recommended approach and dependency unwrap tests~~
6. ~~Fix session integration and diagnostics tests~~
7. ~~Fix remaining API test issues in `test_get_material_mock.py` and `test_main.py`~~
8. Manually fix indentation errors in high-priority integration and unit tests
9. Create a standardized test file template for future use
10. Verify each fixed test file individually
11. Fix coroutine warnings (never awaited coroutines)
12. Fix deprecation warnings (Pydantic, distutils, etc.)
13. Improve session testing utilities and patterns
14. Create detailed test documentation in architecture document
15. Implement strategies to prevent test regressions 

# Test Code Improvement Backlog

## Code Compliance Improvement Plan

This document outlines specific improvements needed to make the test code compliant with the established rules:

1. No mockups or fallback routines within test code
2. Test code should always use tests_dest/test_helpers/service_imports.py
3. Import failures should not be hidden
4. Do not break encapsulation
5. Changes to mainline sources should be preceded by analyses and diagnostics

## Execution Plan Update

**A detailed step-by-step execution plan has been created in [.notes/test_fixes_v1.md](.notes/test_fixes_v1.md)**. 
This plan includes:
- A prioritized list of files to fix
- Specific actions for each file
- Validation steps after each change
- Detailed implementation guidelines for key steps

The execution plan should be followed to ensure all compliance issues are addressed systematically.

### Verification of service_imports.py Completeness

Before proceeding with fixes, we must verify that `tests_dest/test_helpers/service_imports.py` provides all necessary imports:

| Source Module | Required Exports | Current Status | Action Required |
|---------------|------------------|----------------|-----------------|
| services.monitor_service | MonitorService, get_monitor_service, monitor_service | To verify | Check if ErrorLog and SystemMetrics are exported |
| services.material_service | MaterialService, get_material_service, material_service | To verify | Verify all material-related functions are included |
| services.p2p_service | P2PService, get_p2p_service, p2p_service | To verify | Check if all P2P submodules are included |
| models.material | Material, MaterialCreate, MaterialUpdate, MaterialStatus | To verify | Verify UnitOfMeasure and MaterialType are included |
| models.p2p | Requisition, Order, DocumentStatus | To verify | Verify all document types and status enums |
| controllers | BaseController and key controller functions | To verify | Check if all controller helpers are available |

### Integration Test Files With Import Issues

| File Path | Import Issues | Mock Usage | Encapsulation Issues | Specific Actions Required |
|-----------|---------------|------------|----------------------|--------------------------|
| tests_dest/integration/services/test_monitor_service_integration.py | Direct imports from services.monitor_service and others | None | None | Replace direct imports with service_imports; ensure ErrorLog and SystemMetrics are available |
| tests_dest/integration/services/test_service_registry.py | Direct imports from multiple service modules | Multiple MagicMock instances | None | Replace direct imports; refactor tests to use real service instances |
| tests_dest/integration/test_monitor_service_integration.py | Direct imports from models.material and service modules | Mock instances for Material, P2P, Monitor services | None | Replace direct imports; use real service instances from service_imports |
| tests_dest/integration/test_material_p2p_integration.py | Direct imports from models and services | None | Multiple private helper methods with underscore prefix | Replace direct imports; rename helper methods to remove underscore prefix |
| tests_dest/integration/test_p2p_material_integration.py | Indirect imports | Test doubles | Multiple private methods for mock creation | Rename private methods; replace mocks with real service instances |
| tests_dest/integration/test_p2p_service_initialization.py | None | None | Private attribute _state | Refactor to use public interfaces |
| tests_dest/integration/test_integration.py | Potential direct imports | AsyncMock usage for requests | None | Replace mocks with real request objects; use service_imports |
| tests_dest/integration/test_service_factory_integration.py | Direct imports | None | None | Replace with service_imports |

### API Test Files With Import Issues

| File Path | Import Issues | Mock Usage | Encapsulation Issues | Specific Actions Required |
|-----------|---------------|------------|----------------------|--------------------------|
| tests_dest/api/test_monitor_diagnostic.py | Direct imports from services.base_service, services.monitor_service | MagicMock usage for requests | None | Replace direct imports; consider using real request objects |
| tests_dest/api/test_material_controller.py | Potential direct imports | To verify | None | Analyze imports; use service_imports |
| tests_dest/api/test_p2p_order_api.py | Potential direct imports | To verify | None | Check import patterns; update as needed |
| tests_dest/api/test_p2p_requisition_api.py | Potential direct imports | To verify | None | Check import patterns; update as needed |
| tests_dest/api/test_dashboard_controller.py | Potential direct imports | To verify | None | Inspect imports; use service_imports |

### Test Helper Files Needing Verification

| File Path | Issues to Check | Specific Actions Required |
|-----------|-----------------|---------------------------|
| tests_dest/test_helpers/service_imports.py | Completeness of imports | Verify all necessary imports; add missing entries including ErrorLog, SystemMetrics |
| tests_dest/test_helpers/test_fixtures.py | Import patterns | Verify correct import patterns are used and demonstrated |
| tests_dest/test_import_helper.py | Import handling | Ensure import failures are properly handled |

### Diagnostic Actions Required Before Code Changes

1. **Verify service_imports.py completeness**:
   - Compare with source directories to ensure all public classes/functions are included
   - Add missing exports for monitor_errors.ErrorLog, monitor_metrics.SystemMetrics
   - Ensure all material status enums and document types are available

2. **Test import patterns**:
   - Create a small diagnostic test that verifies service_imports can provide all needed imports
   - Document correct import patterns with examples

3. **Mock usage verification**:
   - Document legitimate mock use cases for unit tests
   - Create examples of proper integration tests without mocks
   - Define clear guidelines for when mocks are appropriate

## Implementation Order

1. First fix service_imports.py to ensure it provides all needed imports
2. Update integration test files with direct import issues
3. Address encapsulation issues by renaming private methods
4. Replace mocks in integration tests with real service instances
5. Update API test files with import issues
6. Create documentation on proper test patterns 