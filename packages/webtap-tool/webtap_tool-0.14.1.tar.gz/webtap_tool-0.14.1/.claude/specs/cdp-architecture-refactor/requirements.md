# Feature: CDP Architecture Refactor

## Overview

Simplify WebTap's CDP communication architecture by removing dual state tracking, fixing race conditions, and improving extension robustness. The goal is less code, better reliability, and cleaner separation of concerns.

## Specification Heritage

**Origin:** Architecture review plan at `~/.claude/plans/gleaming-crafting-feather.md`

**Context:** The system works but has accumulated technical debt causing reliability issues:
- State machine errors during multi-target operations
- STALE_EPOCH errors after SSE reconnects
- Race conditions in connect/disconnect operations
- 812-line main.py with 7+ responsibilities

## User Stories

### Story 1: Reliable Multi-Target Connections
**As a** developer debugging multiple browser tabs
**I want** connections to be managed independently per target
**So that** connecting to one tab doesn't affect operations on another

**Acceptance Criteria (EARS notation):**
- WHEN connecting to a new target while another target is connected, THE SYSTEM SHALL handle the connection independently without affecting existing connections
- WHEN disconnecting from one target, THE SYSTEM SHALL not interfere with other active connections
- WHEN two concurrent connect requests arrive for different targets, THE SYSTEM SHALL process both successfully without race conditions
- WHEN two concurrent disconnect requests arrive for the same target, THE SYSTEM SHALL handle the first and ignore the second gracefully

### Story 2: Robust SSE State Synchronization
**As an** extension user
**I want** the extension to automatically recover from daemon disconnections
**So that** I don't have to manually refresh after network hiccups

**Acceptance Criteria (EARS notation):**
- WHEN SSE connection is lost, THE SYSTEM SHALL attempt reconnection with exponential backoff (1s, 2s, 4s, 8s... up to 30s max)
- WHEN SSE reconnection succeeds, THE SYSTEM SHALL reset the epoch counter to prevent STALE_EPOCH errors
- WHEN daemon restarts, THE SYSTEM SHALL automatically rediscover and reconnect
- WHEN SSE broadcasts state, THE SYSTEM SHALL pass state explicitly to controllers (not via shared mutable reference)

### Story 3: Thread-Safe Connection Management
**As a** daemon service
**I want** per-target locking for connection operations
**So that** concurrent operations don't corrupt state

**Acceptance Criteria (EARS notation):**
- WHEN acquiring a lock for target operations, THE SYSTEM SHALL use per-target locks (not a global lock)
- WHEN creating state snapshots, THE SYSTEM SHALL not hold locks during slow CDP queries
- WHEN DOM service mutates browser_data, THE SYSTEM SHALL coordinate with the parent service's state lock
- WHEN snapshot creation fails, THE SYSTEM SHALL not block other operations

### Story 4: Simplified State Architecture
**As a** maintainer
**I want** a single source of truth for connection state
**So that** I can reason about system behavior without tracking dual state machines

**Acceptance Criteria (EARS notation):**
- WHEN validating RPC requests, THE SYSTEM SHALL use only per-target state (no global ConnectionMachine)
- WHEN tracking connection state, THE SYSTEM SHALL use TargetState enum exclusively
- WHEN the RPC framework receives a request, THE SYSTEM SHALL validate against the target's state if target param is present

### Story 5: Transient Error Recovery
**As an** extension user
**I want** transient network errors to be retried automatically
**So that** brief network hiccups don't require manual intervention

**Acceptance Criteria (EARS notation):**
- WHEN an RPC call fails with a transient error, THE SYSTEM SHALL retry up to 3 times with exponential backoff
- WHEN retries are exhausted, THE SYSTEM SHALL display the error to the user
- WHEN an RPC call fails with a permanent error (4xx), THE SYSTEM SHALL not retry and display immediately

### Story 6: Clean Service Separation
**As a** maintainer
**I want** services to be pure query layers
**So that** I can test and reason about them in isolation

**Acceptance Criteria (EARS notation):**
- WHEN NetworkService or ConsoleService queries data, THE SYSTEM SHALL use a shared aggregator utility
- WHEN services need to aggregate multi-target results, THE SYSTEM SHALL use the aggregator with configurable sort key
- WHEN a query fails for one target, THE SYSTEM SHALL log a warning and continue with other targets

### Story 7: Extension-Side Fetch Capture
**As a** developer debugging API responses
**I want** response bodies captured with near-zero latency
**So that** page load is not impacted and bodies are never evicted before capture

**Acceptance Criteria (EARS notation):**
- WHEN `fetch("capture")` is enabled, THE SYSTEM SHALL intercept responses at the extension level using chrome.debugger API
- WHEN Fetch.requestPaused fires with a response, THE SYSTEM SHALL capture the body and continue the request immediately (no round-trip to daemon)
- WHEN a body is captured, THE SYSTEM SHALL push it to the daemon asynchronously via RPC
- WHEN `request(id, ["response.content"])` is called, THE SYSTEM SHALL retrieve the body from daemon's HAR cache
- WHEN `fetch("disable")` is called, THE SYSTEM SHALL stop capture mode

**User Experience:**
```
fetch("capture")  # Enable extension-side capture
# ... browse normally, all XHR/Fetch bodies captured instantly ...
request(11, ["response.content"])  # Always works, body in daemon
fetch("disable")  # Disable when done
```

## Non-Functional Requirements

### Performance
- Snapshot creation SHALL complete within 100ms for up to 10 connected targets
- State lock SHALL never be held for more than 10ms during snapshot swap
- SSE reconnection attempts SHALL not block the UI thread
- Extension-side fetch capture SHALL add < 1ms latency to request completion
- Body push to daemon SHALL be non-blocking (async)

### Reliability
- No race conditions SHALL occur during concurrent connect/disconnect operations
- Double-disconnect on same target SHALL be handled idempotently
- Extension SHALL recover from daemon restart within 30 seconds

### Maintainability
- main.py SHALL be under 400 lines after refactor
- Each service class SHALL have a single responsibility
- Error handling contract SHALL be consistent across all layers

## Constraints

### Technical Constraints
- Must maintain backward compatibility with existing RPC API (method names, params)
- Extension must work with existing Chrome extension manifest
- No changes to CDPSession WebSocket implementation
- Manual testing only (no automated test suite)

### Architectural Constraints
- Big bang atomic refactor - no incremental migration
- Remove global ConnectionMachine entirely (not deprecate)
- Services become pure query layers - state mutations only in main orchestrator

## Out of Scope

- CDPSession reconnection logic (CDP WebSocket layer unchanged)
- Chrome extension UI redesign
- Automated testing infrastructure
- Performance profiling/optimization beyond fixing lock contention
- Field lookup pruning (medium priority, separate task)
- Request body capture (only response bodies via fetch capture)
- Complex extension-side caching/resilience for fetch capture

## Assumptions

1. **Threading model unchanged** - Python threading with locks remains the concurrency model
2. **Single daemon process** - No multi-daemon or distributed scenarios
3. **SSE is reliable once connected** - Focus is on reconnection, not SSE message reliability
4. **Extension controllers are synchronous** - State updates happen in order
5. **No external API consumers** - Only the Chrome extension uses the RPC API
6. **DuckDB queries are fast** - Under 100ms for typical queries; timeouts are exceptional
