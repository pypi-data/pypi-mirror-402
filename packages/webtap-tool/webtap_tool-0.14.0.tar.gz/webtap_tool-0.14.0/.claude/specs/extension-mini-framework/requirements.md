# Feature: WebTap Extension Mini-Framework

## Overview

Create a lightweight framework layer (`lib/`) for the WebTap Chrome extension that eliminates ~200 lines of duplicated controller code, standardizes table interaction patterns, and mirrors RPC error codes from Python.

## User Stories

### Story 1: Consistent Table Interactions
**As a** developer maintaining the extension
**I want** standardized table behavior across all controllers
**So that** users have predictable interactions and code is easier to maintain

**Acceptance Criteria (EARS notation):**
- WHEN a user double-clicks any table row, THE SYSTEM SHALL execute the row's primary action (show details, toggle state, or connect)
- WHEN a table displays status information, THE SYSTEM SHALL use the shared `colorBadge` formatter with consistent styling
- WHEN a controller initializes a table, THE SYSTEM SHALL accept preset configurations from `TablePreset`

### Story 2: Reusable Detail Panels
**As a** developer adding new detail views
**I want** a `createDetailPanel` abstraction
**So that** I don't duplicate the show/hide/loading/error pattern

**Acceptance Criteria (EARS notation):**
- WHEN `detailPanel.show(id)` is called with the same ID twice, THE SYSTEM SHALL close the panel (toggle behavior)
- WHEN `detailPanel.show(id)` is called while panel is hidden, THE SYSTEM SHALL show loading state before fetching
- WHEN data fetch fails, THE SYSTEM SHALL display error message in panel
- WHEN close button is clicked, THE SYSTEM SHALL hide the panel and clear selection

### Story 3: Shared Error Codes
**As a** developer handling RPC errors
**I want** error codes defined in `lib/rpc/errors.js`
**So that** JS matches Python error code constants

**Acceptance Criteria (EARS notation):**
- WHEN client receives `STALE_EPOCH` error, THE SYSTEM SHALL identify it via `ErrorCode.STALE_EPOCH`
- WHEN checking if error is retryable, THE SYSTEM SHALL use `isRetryable(code)` helper

### Story 4: Loading State Helpers
**As a** developer implementing async table operations
**I want** `withTableLoading(table, message, asyncFn)` utility
**So that** loading overlay is consistently shown during operations

**Acceptance Criteria (EARS notation):**
- WHEN async operation starts, THE SYSTEM SHALL show loading overlay with message
- WHEN async operation completes (success or error), THE SYSTEM SHALL hide loading overlay
- WHEN async operation throws, THE SYSTEM SHALL propagate error after hiding overlay

## Non-Functional Requirements

- **Bundle Size**: Framework adds < 5KB unminified to extension
- **No Build Step**: Pure ES modules, no transpilation required

## Constraints

- Must work in Chrome extension context (ES modules, no Node.js)
- No external dependencies beyond existing `lib/ui.js`
- Single PR rollout (atomic refactor of all 6 controllers)

## Mode: Atomic

This is an **atomic refactor** - we can change any API, rename, delete, restructure. All callers are in this codebase and will be updated together. Design for cleanliness, not compatibility.

## Out of Scope

- Python client changes (error codes are manually mirrored, no code generation)
- New extension features (pure refactoring)

## Assumptions

- All tables should use double-click for primary action (user-confirmed decision)
- `lib/ui.js` exports `ui` and `icons` objects (verified in codebase)
- Controllers follow existing `init(client, DataTable, callbacks)` pattern
