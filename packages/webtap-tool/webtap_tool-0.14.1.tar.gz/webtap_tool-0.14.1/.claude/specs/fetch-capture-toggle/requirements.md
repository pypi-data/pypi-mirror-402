# Feature: Fetch Capture Toggle

## Overview

Enable extension-side automatic response body capture as a toggleable feature independent from request interception. The existing `capture.js` module uses `chrome.debugger` API to transparently grab response bodies with near-zero latency before Chrome evicts them from memory. This feature adds the backend state, RPC methods, and UI controls to enable/disable capture.

## Key Design Decision

**Capture is orthogonal to Interception:**
- **Interception** = PAUSE requests at Request/Response stage (requires explicit `resume()`/`fail()`/`fulfill()`)
- **Capture** = RECORD response bodies transparently (no pause, near-zero latency impact)

Users may want either, both, or neither independently. A developer may want to capture all response bodies for later analysis without pausing any requests.

## User Stories

### Story 1: Enable Response Body Capture via REPL/MCP
**As a** developer using WebTap to debug HTTP traffic
**I want** to enable automatic response body capture
**So that** response bodies are available for inspection without manual fetching or request pausing

**Acceptance Criteria (EARS notation):**
- WHEN `capture("enable")` is called AND a connection is active, THE SYSTEM SHALL enable capture mode and return `{"capture_enabled": true}`
- WHEN `capture("enable")` is called AND no connection is active, THE SYSTEM SHALL return an error indicating connection is required
- WHEN `capture("disable")` is called, THE SYSTEM SHALL disable capture mode and return `{"capture_enabled": false}`
- WHEN `capture("status")` is called, THE SYSTEM SHALL return the current capture state
- WHEN capture is enabled, THE SYSTEM SHALL broadcast state update via SSE to all connected clients

### Story 2: Toggle Capture via Extension UI
**As a** developer using the WebTap Chrome extension sidebar
**I want** a Capture button that toggles capture mode
**So that** I can quickly enable/disable body capture without using the REPL

**Acceptance Criteria (EARS notation):**
- WHEN the extension sidebar loads, THE SYSTEM SHALL display a "Capture" button in the header actions
- WHEN the Capture button is clicked AND capture is disabled, THE SYSTEM SHALL call `capture.enable` RPC method
- WHEN the Capture button is clicked AND capture is enabled, THE SYSTEM SHALL call `capture.disable` RPC method
- WHEN capture state changes via SSE, THE SYSTEM SHALL update the button's visual state (active/inactive styling)
- WHEN no connection is active, THE SYSTEM SHALL disable the Capture button (grayed out, non-clickable)

### Story 3: View Capture State in Status
**As a** developer checking WebTap status
**I want** to see whether capture mode is enabled in the state snapshot
**So that** I know if response bodies are being recorded

**Acceptance Criteria (EARS notation):**
- WHEN the state snapshot is requested, THE SYSTEM SHALL include `capture_enabled` in the `fetch` section
- WHEN capture state changes, THE SYSTEM SHALL update `fetch_hash` for frontend change detection
- WHEN capture is enabled AND extension attaches debugger, THE SYSTEM SHALL begin capturing response bodies via `fetch.pushBody`

## Non-Functional Requirements

- **Latency:** Capture mode SHALL NOT add perceptible latency to network requests (< 5ms overhead)
- **State Consistency:** Capture state SHALL be immediately reflected in SSE broadcasts after enable/disable
- **UI Responsiveness:** Button state SHALL update within 100ms of SSE state change

## Constraints

- Requires active Chrome connection to enable (mirrors interception behavior)
- Extension-side capture uses `chrome.debugger` API which requires user permission
- Capture only works for tabs connected via WebTap (cannot capture arbitrary tabs)

## Out of Scope

- Request body capture (only response bodies are captured)
- Capture persistence across daemon restarts (state is ephemeral)
- Capture filtering by URL/type (captures all responses when enabled)
- Multiple capture targets with different settings (single global toggle)
- Body size limits or truncation (handled by existing `store_response_body`)

## Assumptions

1. The `capture.js` extension module is already implemented and working
2. The `fetch.pushBody` RPC method exists and stores bodies correctly
3. Extension can attach `chrome.debugger` to connected tabs
4. Users understand the difference between "Capture" (passive recording) and "Intercept" (active pausing)
5. State snapshot structure follows existing patterns (`fetch_enabled`, `response_stage`)
