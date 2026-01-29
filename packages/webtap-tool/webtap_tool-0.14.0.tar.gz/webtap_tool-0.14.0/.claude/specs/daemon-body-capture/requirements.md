# Feature: Daemon-Side Immediate Body Capture

## Overview

Capture HTTP response bodies immediately when requests complete, before page navigation can evict them from Chrome's memory. This ensures bodies are available for later inspection even after redirects.

## Problem Statement

Currently, response bodies are fetched lazily via `Network.getResponseBody` when `request()` is called. If the page has navigated (e.g., after a login XHR triggers a redirect), Chrome evicts the body and the call fails with "No resource found".

## User Stories

### Story 1: Capture Login Response Before Redirect
**As a** developer debugging authentication flows
**I want** XHR response bodies captured before post-login redirects
**So that** I can inspect login responses even after the page navigates

**Acceptance Criteria (EARS notation):**
- WHEN `Network.loadingFinished` event is received, THE SYSTEM SHALL immediately call `Network.getResponseBody` and store the result
- WHEN body is successfully captured, THE SYSTEM SHALL store it as a `Network.responseBodyCaptured` synthetic event in DuckDB
- WHEN `request()` is called for a request with captured body, THE SYSTEM SHALL return the captured body from DuckDB
- WHEN `request()` is called and no captured body exists, THE SYSTEM SHALL fall back to lazy `Network.getResponseBody` CDP call
- WHEN `Network.getResponseBody` fails (body evicted), THE SYSTEM SHALL return error in response

### Story 2: Transparent Integration
**As a** user of the `request()` command
**I want** body capture to work automatically
**So that** I don't need to enable special modes or remember to capture bodies

**Acceptance Criteria (EARS notation):**
- WHEN daemon connects to a page, THE SYSTEM SHALL automatically register for `loadingFinished` events
- WHEN capture is working, THE SYSTEM SHALL NOT require user intervention or mode changes
- WHEN bodies are captured, THE SYSTEM SHALL use the same storage format as extension-pushed bodies

## Non-Functional Requirements

- **Performance:** Body capture callback must complete within 100ms to not block event processing
- **Memory:** Bodies stored in DuckDB (already has 50K event limit with FIFO eviction)
- **Reliability:** Failed captures must not crash the daemon or break event flow

## Constraints

- Must work within existing CDPSession architecture
- Must coexist with existing extension-side capture (if enabled)
- Cannot modify Chrome's body eviction behavior

## Out of Scope

- Redirect-locking via Fetch interception (future enhancement if needed)
- Extension-side Network.loadingFinished handling (daemon-side is sufficient)
- Changing buffer sizes (already set to 50MB)

## Assumptions

1. `Network.loadingFinished` fires before JS callbacks that trigger navigation
2. `Network.getResponseBody` is fast enough to complete before navigation starts
3. Duplicate body captures (from both daemon and extension) are acceptable (first one wins on lookup)
