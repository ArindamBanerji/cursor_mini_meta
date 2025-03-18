# Test Improvement Backlog

## A. Diagnostic Tests Creation

### A.1 Sync/Async Boundary Tests
- [ ] Create `test_sync_async_boundary.py`
  - Test state manager integration
  - Verify sync/async boundaries
  - Test performance implications
  - Document patterns for state management

### A.2 FastAPI Parameter Extraction Tests
- [ ] Create `test_fastapi_parameter_extraction.py`
  - Test parameter validation
  - Test request body handling
  - Test query parameter handling
  - Test path parameter handling

### A.3 Service Layer Cleanliness Tests
- [ ] Create `test_service_layer_cleanliness.py`
  - Test service initialization
  - Test service state management
  - Test service error handling
  - Test service lifecycle

## B. Current Issues Fixes

### B.1 API Test Fixes
- [x] Fix syntax error in `test_material_controller.py`
- [ ] Verify FastAPI endpoint tests
- [ ] Test error handling in API endpoints
- [ ] Test API response formats

### B.2 Unit Test Completion
- [ ] Complete base service test implementation
- [ ] Add service initialization tests
- [ ] Add service state management tests
- [ ] Add service error handling tests

### B.3 Monitoring Test Verification
- [ ] Verify datetime issue resolution
- [ ] Test health check endpoint
- [ ] Test metrics collection
- [ ] Test error logging

## C. Additional Test Suites

### C.1 Model Tests
- [ ] Test data model validation
- [ ] Test model serialization
- [ ] Test model relationships
- [ ] Test model constraints

### C.2 Service Tests
- [ ] Test service dependencies
- [ ] Test service communication
- [ ] Test service state transitions
- [ ] Test service error recovery

### C.3 Integration Tests
- [ ] Test end-to-end workflows
- [ ] Test system interactions
- [ ] Test data flow
- [ ] Test error propagation

## D. Test Infrastructure

### D.1 Environment Setup
- [ ] Enhance `SetProjEnv.ps1`
- [ ] Add environment validation
- [ ] Improve error messages
- [ ] Add path verification

### D.2 Test Isolation
- [ ] Implement virtual environment support
- [ ] Add test data isolation
- [ ] Add state isolation
- [ ] Add dependency isolation

## Current Focus
1. Fix syntax error in `test_material_controller.py`
2. Complete unit test implementation in `test_base_service.py`
3. Verify monitoring test coverage

## High Priority

1. **Python Path Management in GenConfTest**
   - Issue: Unit tests require proper Python path setup to resolve imports correctly
   - Current Fix: Added path setup in unit/conftest.py
   - Required Change: Move this logic into GenConfTest to generate proper conftest files
   - Implementation Details:
     ```python
     # Template for conftest path setup
     import sys
     import os
     
     # Get project root from environment variable or use path calculation
     project_root = os.environ.get("SAP_HARNESS_HOME")
     if not project_root:
         project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
         print(f"SAP_HARNESS_HOME environment variable not set. Using calculated path: {project_root}")
     
     # Add project root to Python path
     sys.path.insert(0, project_root)
     
     @pytest.fixture(autouse=True)
     def setup_test_env():
         '''Set up test environment.'''
         original_path = sys.path[:]
         yield
         sys.path[:] = original_path
     ```
   - Benefits:
     - Consistent import resolution across all test files
     - Proper handling of environment variables
     - Clean path restoration after tests
   - Dependencies:
     - Update GenConfTest to include path setup logic
     - Ensure compatibility with existing fixtures
     - Test with both environment variable present and absent

2. **Timestamp Testing Pattern**
   - Issue: Tests comparing timestamps in quick succession may fail due to identical timestamps
   - Current Fix: Added small sleep delay in test_base_service.py
   - Required Change: Create a reusable pattern for timestamp testing
   - Implementation Details:
     ```python
     def test_timestamp_updates():
         """Test that timestamps are properly updated."""
         # Add small delay between operations that update timestamps
         time.sleep(0.001)  # 1ms delay is usually sufficient
         
         # Alternative: Use freezegun to control time explicitly
         with freeze_time() as frozen_time:
             first_time = datetime.now()
             frozen_time.tick(delta=timedelta(microseconds=1))
             second_time = datetime.now()
             assert second_time > first_time
     ```
   - Benefits:
     - More reliable timestamp comparison tests
     - Prevents flaky tests due to timing issues
     - Provides two approaches: real time with delay or controlled time with freezegun
   - Dependencies:
     - Consider adding freezegun as a test dependency
     - Document both patterns in test guidelines
     - Update existing timestamp tests to use the new pattern

3. **Async Test Standardization**
   - Issue: Inconsistent async/sync patterns in test files causing warnings and potential issues
   - Current Fix: Standardized async setup/teardown in test_minimal_async.py
   - Required Change: Update GenConfTest to handle async test patterns correctly
   - Implementation Details:
     ```python
     # Template for async test setup
     @pytest.mark.asyncio
     async def setup_module(module: ModuleType) -> None:
         """Set up the test module."""
         setup_test_env()
     
     @pytest.mark.asyncio
     async def teardown_module(module: ModuleType) -> None:
         """Tear down the test module."""
         teardown_test_env()
     
     @pytest.mark.asyncio
     async def test_async_function():
         """Async test function."""
         await asyncio.sleep(0.01)
         assert True
     ```
   - Benefits:
     - Consistent async/sync patterns across test files
     - Proper handling of async setup/teardown
     - Clear separation between async and sync tests
   - Dependencies:
     - Update GenConfTest to detect async test files
     - Add async-specific imports and fixtures
     - Handle pytest-asyncio configuration 