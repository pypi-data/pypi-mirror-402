# Feature: WebTap Code Cleanup and Consistency Improvements

## Overview

This specification addresses medium-priority code quality issues identified during a comprehensive architecture review. The goal is to improve maintainability, reduce duplication, and establish consistent patterns across the webtap codebase.

## User Stories

### Story 1: Consistent Error Handling for Command Developers

**As a** developer extending webtap with new commands
**I want** a single, clear error handling pattern
**So that** I can write commands consistently without duplicating error handling logic

**Acceptance Criteria (EARS notation):**
- WHEN a command makes an RPC call that fails with RPCError, THE SYSTEM SHALL return an error response with the error message
- WHEN a command encounters an unexpected exception, THE SYSTEM SHALL return an error response with the exception message
- WHEN a command requires connection, THE SYSTEM SHALL use a standard check_connection pattern before making RPC calls
- WHEN an error occurs, THE SYSTEM SHALL use the existing `error_response()` builder consistently

### Story 2: Encapsulated State Mutations

**As a** maintainer of the webtap services layer
**I want** all browser_data mutations to go through WebTapService methods
**So that** state changes are centralized and broadcasts are triggered consistently

**Acceptance Criteria (EARS notation):**
- WHEN DOMService needs to set browser_data selections, THE SYSTEM SHALL call a WebTapService method instead of direct mutation
- WHEN DOMService needs to set browser_data prompt, THE SYSTEM SHALL call a WebTapService method
- WHEN browser_data is mutated through WebTapService, THE SYSTEM SHALL automatically trigger SSE broadcasts

### Story 3: Consistent Module Organization

**As a** developer navigating the webtap codebase
**I want** related modules to be co-located
**So that** I can find state-related classes in one place

**Acceptance Criteria (EARS notation):**
- WHEN I look for state-related classes, THE SYSTEM SHALL have them in the services/ directory
- WHEN daemon_state.py functionality is needed, THE SYSTEM SHALL import from services/daemon_state.py

### Story 4: Clean API Without Legacy Fields

**As a** consumer of the StateSnapshot API
**I want** only relevant fields exposed
**So that** I don't have to deal with deprecated empty values

**Acceptance Criteria (EARS notation):**
- WHEN StateSnapshot is created, THE SYSTEM SHALL NOT include legacy page_id, page_title, page_url fields
- WHEN multi-target connection info is needed, THE SYSTEM SHALL use the connections tuple

### Story 5: Unified Target Parameter Handling

**As a** developer writing service methods
**I want** a single utility for target/targets parameter normalization
**So that** I don't duplicate the conversion logic in every service

**Acceptance Criteria (EARS notation):**
- WHEN a service receives legacy `target` parameter, THE SYSTEM SHALL convert it to `targets` list using a shared utility
- WHEN `targets` is None and `target` is provided, THE SYSTEM SHALL normalize to list form
- WHEN both are None, THE SYSTEM SHALL pass None to downstream methods

## Non-Functional Requirements

- **Maintainability**: Changes should not alter external behavior; only internal organization
- **Backwards Compatibility**: Existing imports must continue to work during transition
- **Testability**: All patterns should be verifiable through static analysis (type checking, linting)

## Constraints

- Must maintain Python 3.11+ compatibility
- Must pass basedpyright type checking
- Must pass ruff linting
- Cannot break existing ReplKit2 integration

## Out of Scope

- New features or functionality
- Performance optimizations
- Changes to RPC protocol
- Changes to CDP event handling
- Test coverage (tests for webtap are not currently in scope)

## Assumptions

1. The existing `error_response()` builder is the canonical way to return errors
2. Commands that catch both RPCError and Exception are doing so intentionally (RPCError for structured errors, Exception as fallback)
3. The `check_connection()` helper pattern is not widely used due to its recent addition
4. Legacy `page_id`, `page_title`, `page_url` fields are truly unused in the multi-target architecture
5. DOMService is the primary (possibly only) service that directly mutates `browser_data`
