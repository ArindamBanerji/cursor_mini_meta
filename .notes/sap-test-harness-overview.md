# SAP Test Harness Overview

## Purpose

The SAP Test Harness is a sophisticated testing platform designed as a bridge between SAP business systems and modern AI integration patterns. It serves as a testbed for enabling both direct GUI invocations and LLM (Large Language Model) function calling, allowing developers to simulate SAP system interactions without requiring a full SAP installation.

## Core Design Principles

The harness is built on a meta-architecture that enforces strict separation of concerns and establishes a single source of truth for routing, templates, and controller associations:

1. **Centralized Route Registry**: Acts as a "system call table" where all routes, URL structures, and their corresponding controllers and templates are defined in one place (`meta_routes.py`).

2. **Layered Architecture**:
   - **Controllers**: Thin request handlers that transform HTTP requests and delegate to services
   - **Services**: Pure business logic components with no HTTP concerns
   - **Data Layer**: Models and state management with clear separation from business logic

3. **Dual Interface Support**:
   - **Web UI**: Traditional HTML interface for direct human interaction
   - **API Endpoints**: REST API with consistent `/api/v1` structure for LLM function calling

## Key Functionality

The harness simulates core SAP business processes:

- **Material Management**: Create, retrieve, and manage material master data
- **Procurement (P2P)**: Handle purchase requisitions and purchase orders
- **System Monitoring**: Track system performance and health metrics

Each domain is accessible through both human-friendly web interfaces and structured API endpoints optimized for LLM interaction.

## Technical Implementation

- **Framework**: FastAPI for high-performance asynchronous request handling
- **Data Handling**: Pydantic v2 models for validation and consistent schema definition
- **State Management**: In-memory state with optional persistence 
- **Dynamic Routing**: Routes registered programmatically based on the meta-routes registry
- **Error Handling**: Centralized exception management with consistent response patterns

## Benefits of the Design

1. **Maintainability**: Single definition point for routes reduces inconsistencies and makes changes easier
2. **Testability**: Clear component boundaries enable precise, isolated testing
3. **Extensibility**: Adding new functionality follows a consistent, documented pattern
4. **Documentation**: Self-documenting architecture where related components are clearly connected
5. **LLM Integration**: Structured design enables effective AI-powered automation and testing

## Development Approach

The harness follows strict architectural guidelines and coding rules to ensure the meta-architecture remains consistent during development. These rules enforce separation of concerns, prevent URL hardcoding, ensure business logic stays in services, and maintain proper architectural boundaries.

As an MVP (version 0.15), the harness provides the foundation for more advanced SAP testing scenarios and AI integration patterns to be built in future iterations.
