# Feature: WebTap Code Consolidation

## Overview

Consolidate duplicated code patterns across the webtap codebase to reduce technical debt, improve maintainability, and establish consistent patterns. Analysis identified ~250-300 lines of duplicated code across commands, services, and infrastructure layers.

## Specification Heritage

This specification formalizes the findings from the comprehensive codebase analysis captured in `~/.claude/plans/immutable-snuggling-zebra.md`. That analysis identified 10 consolidation opportunities across 3 priority levels.

## User Stories

### Story 1: Consistent RPC Error Handling for Command Developers

**As a** developer writing new webtap commands
**I want** a single function for RPC calls with standard error handling
**So that** I don't duplicate try/except blocks in every command

**Acceptance Criteria (EARS notation):**
- WHEN a command makes an RPC call that succeeds, THE SYSTEM SHALL return the result with no error
- WHEN a command makes an RPC call that fails with RPCError, THE SYSTEM SHALL return None and an error_response with the error message
- WHEN a command makes an RPC call that fails with any Exception, THE SYSTEM SHALL return None and an error_response with the exception string
- WHEN using the rpc_call helper, THE SYSTEM SHALL reduce boilerplate from 5 lines to 1 line per call

### Story 2: Unified Query Aggregation for Service Developers

**As a** developer working with multi-target CDP queries
**I want** a single utility for aggregating queries across multiple CDPSessions
**So that** I don't duplicate the aggregation loop in every service method

**Acceptance Criteria (EARS notation):**
- WHEN executing a query across multiple CDPSessions, THE SYSTEM SHALL aggregate results into a single list
- WHEN a query fails on one CDPSession, THE SYSTEM SHALL log a warning and continue with other sessions
- WHEN all queries fail, THE SYSTEM SHALL return an empty list

### Story 3: Shared Field Selection Logic

**As a** developer implementing data retrieval with field selection
**I want** a single implementation of ES-style field selection
**So that** field selection behaves consistently across network and console commands

**Acceptance Criteria (EARS notation):**
- WHEN patterns is None, THE SYSTEM SHALL return minimal default fields
- WHEN patterns is ["*"], THE SYSTEM SHALL return all fields
- WHEN a pattern ends with ".*", THE SYSTEM SHALL return all nested fields
- WHEN a pattern specifies a path, THE SYSTEM SHALL return only that field

### Story 4: Centralized Target Resolution

**As a** developer working with multi-target operations
**I want** a single helper for iterating over target or all connections
**So that** I don't duplicate the target/all branching logic

**Acceptance Criteria (EARS notation):**
- WHEN target is specified, THE SYSTEM SHALL execute callback only on that connection
- WHEN target is None, THE SYSTEM SHALL execute callback on all connections
- WHEN target doesn't exist, THE SYSTEM SHALL return None or empty result

### Story 5: Consistent Truncation Configuration

**As a** command developer
**I want** centralized truncation configs for REPL vs MCP display
**So that** URL and text truncation is consistent across all commands

**Acceptance Criteria (EARS notation):**
- WHEN displaying in REPL mode, THE SYSTEM SHALL use compact truncation (50 chars)
- WHEN displaying in MCP mode, THE SYSTEM SHALL use generous truncation (200 chars)

### Story 6: Shared Code Generation Data Preparation

**As a** developer using to_model or quicktype commands
**I want** shared data preparation logic
**So that** both commands fetch and process HAR data consistently

**Acceptance Criteria (EARS notation):**
- WHEN preparing data for code generation, THE SYSTEM SHALL fetch HAR entry
- WHEN body content is needed, THE SYSTEM SHALL fetch and decode response body
- WHEN expr is provided, THE SYSTEM SHALL evaluate expression on body
- WHEN json_path is provided, THE SYSTEM SHALL extract the specified path

### Story 7: Explicit Module Exports

**As a** developer importing from webtap modules
**I want** explicit `__all__` exports in all public modules
**So that** I know which symbols are part of the public API

**Acceptance Criteria (EARS notation):**
- WHEN a module is imported with `from module import *`, THE SYSTEM SHALL only export `__all__` members
- WHEN `__all__` is defined, THE SYSTEM SHALL include all public functions and classes

### Story 8: Centralized Configuration Constants

**As a** maintainer of the webtap codebase
**I want** magic constants centralized in a config module
**So that** I can find and modify them in one place

**Acceptance Criteria (EARS notation):**
- WHEN network buffer sizes are needed, THE SYSTEM SHALL import from config module
- WHEN timeout values are needed, THE SYSTEM SHALL import from config module
- WHEN event storage limits are needed, THE SYSTEM SHALL import from config module

### Story 9: Specific Exception Handling

**As a** maintainer debugging production issues
**I want** specific exception types caught instead of bare Exception
**So that** I can understand what type of failure occurred

**Acceptance Criteria (EARS notation):**
- WHEN an HTTP request fails, THE SYSTEM SHALL catch httpx.RequestError
- WHEN JSON parsing fails, THE SYSTEM SHALL catch json.JSONDecodeError
- WHEN a timeout occurs, THE SYSTEM SHALL catch TimeoutError
- WHEN a file operation fails, THE SYSTEM SHALL catch OSError

## Non-Functional Requirements

- **Maintainability:** All duplicated patterns should have a single source of truth
- **Backwards Compatibility:** All changes must be internal refactoring with no API changes
- **Testability:** All changes must pass existing type checking (basedpyright) and linting (ruff)
- **Documentation:** All new utilities must include docstrings with usage examples

## Constraints

- Must maintain Python 3.11+ compatibility
- Must pass basedpyright type checking
- Must pass ruff linting
- Cannot break existing ReplKit2 integration
- Cannot change external command signatures or RPC protocol

## Out of Scope

- Splitting handlers.py into domain modules (deferred as too large)
- Adding new features or functionality
- Performance optimizations beyond reducing duplication
- Test coverage additions (webtap tests not currently in scope)

## Assumptions

1. The existing error handling pattern (RPCError then Exception) is the correct approach
2. Field selection patterns follow ES-style notation and this is intentional
3. Truncation differences between REPL and MCP are intentional UX decisions
4. Magic constants have reasonable current values and just need centralization
5. All identified duplication is true duplication (not intentional variation)
