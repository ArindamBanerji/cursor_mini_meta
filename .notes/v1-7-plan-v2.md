# SAP Test Harness v1.7 Implementation Plan

## Overview

Based on the analysis of the current v1.6 codebase and the progression outlined in the mini-meta-tracker, this document outlines the minimal set of features to be implemented in v1.7 of the SAP Test Harness. The plan maintains a focused approach to ensure testability while incrementally expanding functionality.

## Key Priorities for v1.7

According to the mini-meta-tracker, the recommended next steps for v1.7 were:

1. **P2P Controller** (Feature #22, Step #21)
   - Create `controllers/p2p_controller.py` for procurement UI and API
   - Implement requisition and order management endpoints
   - Add templates for procurement views
   - Create tests for controller methods

2. **Session Middleware** (Feature #24, Step #23)
   - Implement session handling with flash messages
   - Add form re-fill on validation errors
   - Create comprehensive tests for session functionality

After analyzing the codebase, we'll focus primarily on the P2P Controller implementation as the main objective for v1.7, with some foundation work for session middleware. This approach ensures we maintain the incremental development pattern while addressing the most critical missing feature (P2P Controller) identified in the tracker.

## Implementation Plan 

### 1. P2P Controller Implementation

Following the guidance on file size, encapsulation, and dependency management, we'll break down the controller implementation into more focused, smaller files:

| File | Changes | Details |
|------|---------|---------|
| `controllers/p2p_common.py` | New file | Define common functionality shared by all P2P controllers: <br>- Base dependency functions <br>- Error handling utilities <br>- Common data structures and type annotations <br>- Filter parameter models (max 100-150 lines) | Done
| `controllers/p2p_requisition_common.py` | New file | Common utilities specific to requisition handling: <br>- Format functions for requisition responses <br>- Validation helpers <br>- Requisition-specific error formatting (max 100 lines) | Done
| `controllers/p2p_order_common.py` | New file | Common utilities specific to order handling: <br>- Format functions for order responses <br>- Validation helpers <br>- Order-specific error formatting (max 100 lines) | Done
| `controllers/p2p_requisition_ui_controller.py` | New file | UI controller functions for requisition management only: <br>- List requisitions <br>- View requisition details <br>- Create/edit forms <br>- Submit/approve/reject actions (max 250 lines) | Done
| `controllers/p2p_order_ui_controller.py` | New file | UI controller functions for order management only: <br>- List orders <br>- View order details <br>- Create/edit forms <br>- Submit/approve/receive actions (max 250 lines) | Done
| `controllers/p2p_requisition_api_controller.py` | New file | API controller functions for requisition endpoints: <br>- CRUD operations <br>- Workflow state transitions <br>- Response formatting (max 200 lines) | Done
| `controllers/p2p_order_api_controller.py` | New file | API controller functions for order endpoints: <br>- CRUD operations <br>- Workflow state transitions <br>- Response formatting (max 200 lines) | Done
| `controllers/p2p_controller.py` | New file | Main controller module that re-exports all functions: <br>- Import and re-export UI and API functions <br>- No direct implementation, just exports (max 50 lines) | Done
| `meta_routes.py` | Modify | Add routes for P2P UI and API endpoints, carefully structured to separate requisition and order paths | Done (but check) 

### 2. P2P Templates

| File | Changes | Details |
|------|---------|---------|
| `templates/p2p/requisition/list.html` | New file | Template for listing requisitions with filtering and navigation | Done
| `templates/p2p/requisition/detail.html` | New file | Template for viewing requisition details and performing actions | Done
| `templates/p2p/requisition/create.html` | New file | Form template for creating/editing requisitions | Done
| `templates/p2p/order/list.html` | New file | Template for listing purchase orders with filtering and navigation | Done
| `templates/p2p/order/detail.html` | New file | Template for viewing order details and performing actions | Done
| `templates/p2p/order/create.html` | New file | Form template for creating/editing purchase orders |
| `templates/base.html` | Modify | Uncomment P2P navigation section and update links | (Pending Update)

### 3. Session Middleware Foundation

| File | Changes | Details |
|------|---------|---------|
| `middleware/__init__.py` | New file | Initialize the middleware package | (Done) 
| `middleware/session.py` | New file | Implement session handling middleware with flash message support | (Done)
| `main.py` | Modify | Add middleware registration in the FastAPI application | (Pending Update)
| `controllers/__init__.py` | Modify | Enhance BaseController to support flash messages and form state preservation | (Pending Update)

### 4. Cross-component Integration

| File | Changes | Details |
|------|---------|---------|
| `templates/material/detail.html` | Modify | Update related_documents section to use real P2P data |(Pending Update)
| `controllers/dashboard_controller.py` | Modify | Enhance dashboard to include P2P metrics/statistics | (Pending update)
| `templates/dashboard.html` | Modify | Update to display P2P information | (Pending) 

### 5. Testing Implementation  (Pending - TBD)

Following the guidance on testing and the revised controller structure, we'll create a more comprehensive testing plan that mirrors the controller organization:

| File | Changes | Details |
|------|---------|---------|
| `tests-dest/unit/test_p2p_common.py` | New file | Test common P2P utilities and shared functionality (max 150 lines) |
| `tests-dest/unit/test_p2p_requisition_common.py` | New file | Test requisition-specific utilities and helper functions (max 100 lines) |
| `tests-dest/unit/test_p2p_order_common.py` | New file | Test order-specific utilities and helper functions (max 100 lines) |
| `tests-dest/api/test_p2p_requisition_api.py` | New file | Test the requisition API endpoints: <br>- CRUD operations <br>- Workflow transitions <br>- Error handling <br>- Input validation (max 200 lines) |
| `tests-dest/api/test_p2p_order_api.py` | New file | Test the order API endpoints: <br>- CRUD operations <br>- Workflow transitions <br>- Error handling <br>- Input validation (max 200 lines) |
| `tests-dest/api/test_p2p_requisition_ui.py` | New file | Test the requisition UI controller: <br>- Page rendering <br>- Form submission <br>- Response handling <br>- Error displays (max 200 lines) |
| `tests-dest/api/test_p2p_order_ui.py` | New file | Test the order UI controller: <br>- Page rendering <br>- Form submission <br>- Response handling <br>- Error displays (max 200 lines) |
| `tests-dest/integration/test_p2p_material_integration.py` | New file | Test integration between P2P and Material modules: <br>- Material references in requisitions/orders <br>- Material availability checks <br>- Cross-module workflows (max 200 lines) |
| `tests-dest/integration/test_p2p_workflow.py` | New file | Test complete P2P workflows from end-to-end: <br>- Requisition to order conversion <br>- Full lifecycle testing <br>- State transitions (max 200 lines) |
| `tests-dest/unit/test_session_middleware.py` | New file | Test session middleware functionality (max 150 lines) |
| `tests-dest/api/test_session_integration.py` | New file | Test integration of session middleware with P2P controllers (max 150 lines) |

## Detailed Component Specifications

### P2P Controller Structure

#### 1. Requisition Management Functions

* **List Requisitions**: 
  - UI: Display list with filtering by status, date range, and search terms
  - API: Return filtered list with pagination support

* **View Requisition Details**:
  - UI: Show detailed view with items, status, and available actions
  - API: Return complete requisition data

* **Create Requisition**:
  - UI: Form for creating new requisition with material selection
  - API: Accept JSON payload for requisition creation

* **Edit Requisition**:
  - UI: Form for editing draft requisition
  - API: Accept JSON payload for requisition updates

* **Submit Requisition**:
  - UI: Action button in detail view
  - API: Endpoint to transition requisition to submitted status

* **Approve/Reject Requisition**:
  - UI: Action buttons with confirmation
  - API: Endpoints for approval/rejection with reason

* **Convert to Order**:
  - UI: Action button with vendor selection
  - API: Endpoint to create order from requisition

#### 2. Order Management Functions

* **List Orders**:
  - UI: Display list with filtering by status, vendor, date range
  - API: Return filtered list with pagination support

* **View Order Details**:
  - UI: Show detailed view with items, status, and available actions
  - API: Return complete order data

* **Create Order**:
  - UI: Form for creating new order with material selection and vendor
  - API: Accept JSON payload for order creation

* **Edit Order**:
  - UI: Form for editing draft order
  - API: Accept JSON payload for order updates

* **Submit Order**:
  - UI: Action button in detail view
  - API: Endpoint to transition order to submitted status

* **Approve/Reject Order**:
  - UI: Action buttons with confirmation
  - API: Endpoints for approval/rejection with reason

* **Receive Items**:
  - UI: Form for recording received quantities
  - API: Endpoint to update received quantities

* **Complete Order**:
  - UI: Action button with confirmation
  - API: Endpoint to mark order as completed

### Session Middleware Functionality

* **Flash Messages**:
  - Store temporary messages between requests
  - Support message types (success, error, info, warning)
  - Automatically clear messages after being displayed

* **Form State Preservation**:
  - Store form data on validation failure
  - Restore form data when rendering form again
  - Clear form data after successful submission

* **User Preferences**:
  - Store and retrieve user preferences
  - Support for theme, display options, etc.

## Testing Strategy

### Approach

1. **Unit Tests**: Focus on testing individual controller functions and middleware components in isolation.
2. **API Tests**: Test the API endpoints for correct responses, error handling, and data validation.
3. **Integration Tests**: Test the interaction between P2P and existing components (especially Material).
4. **UI Tests**: Verify that UI controllers correctly render templates and process form submissions.

### Priority Test Cases

1. **P2P Workflow Testing**: Test complete procurement workflow from requisition creation to order completion.
2. **Error Handling**: Verify appropriate error responses for invalid inputs and unauthorized actions.
3. **Session Persistence**: Ensure session data is correctly stored and retrieved across requests.
4. **Cross-module Integration**: Test that P2P operations correctly interact with Material data.

## Implementation Sequence

Following the guidance for maintainable and focused code development:

1. Implement common functionality files first:
   - `controllers/p2p_common.py`
   - `controllers/p2p_requisition_common.py`
   - `controllers/p2p_order_common.py`

2. Implement API controllers before UI controllers:
   - `controllers/p2p_requisition_api_controller.py`
   - `controllers/p2p_order_api_controller.py`

3. Implement UI controllers with template rendering:
   - `controllers/p2p_requisition_ui_controller.py`
   - `controllers/p2p_order_ui_controller.py`

4. Create the main controller file that re-exports functions:
   - `controllers/p2p_controller.py`

5. Update route definitions in `meta_routes.py`

6. Create essential UI templates for requisition and order management

7. Implement session middleware foundation

8. Create test files following the same structure as controller files:
   - Write tests for common functionality first
   - Test API controllers
   - Test UI controllers
   - Test integration between modules

9. Update cross-component integration in existing files

This carefully sequenced approach ensures that dependencies are properly managed, with foundation components built first, followed by implementation files that depend on them.

This focused implementation plan for v1.7 will significantly enhance the SAP Test Harness while maintaining a manageable scope for testing and validation.
