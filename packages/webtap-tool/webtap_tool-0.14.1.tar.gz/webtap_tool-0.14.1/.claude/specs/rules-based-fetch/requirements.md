# Feature: Rules-Based Fetch

## Overview

Replace the manual pause/resume fetch API with declarative rules for reliable HTTP response body capture, request blocking, and response mocking. The key innovation is intercepting ALL requests at Response stage when capture is enabled, guaranteeing body availability via `Fetch.getResponseBody` before Chrome evicts them.

## Specification Heritage

Evolves from: `daemon-body-capture` (completed 2025-12-29)

**What worked:** Daemon-side body capture via `Network.loadingFinished` callback with ThreadPoolExecutor.

**What didn't solve:** Pre-navigation XHR bodies (login responses before redirect) are evicted by Chrome before capture runs. The `loadingFinished` → `getResponseBody` approach races against Chrome's memory eviction.

**This spec adds:** Response-stage interception to guarantee body availability while paused.

## User Stories

### Story 1: Reliable Body Capture
**As a** reverse engineer
**I want** HTTP response bodies captured before Chrome evicts them
**So that** login flows with redirects are fully inspectable

**Acceptance Criteria (EARS notation):**
- WHEN `fetch({"capture": True})` is called, THE SYSTEM SHALL call `Fetch.enable` with pattern `{urlPattern: "*", requestStage: "Response"}`
- WHEN a `Fetch.requestPaused` event has `responseStatusCode` present, THE SYSTEM SHALL call `Fetch.getResponseBody` with the event's `requestId`
- WHEN body capture succeeds, THE SYSTEM SHALL store it as a `Network.responseBodyCaptured` synthetic event in DuckDB
- WHEN body capture succeeds, THE SYSTEM SHALL call `Fetch.continueResponse` with the event's `requestId`
- WHEN body capture fails (e.g., redirects have no body), THE SYSTEM SHALL log the error and call `Fetch.continueResponse`

### Story 2: Request Blocking
**As a** reverse engineer
**I want** to block requests matching URL patterns
**So that** I can observe API behavior without side effects (payments, bookings)

**Acceptance Criteria:**
- WHEN `fetch({"block": ["*tracking*", "*analytics*"]})` is called, THE SYSTEM SHALL intercept requests at Response stage
- WHEN a paused request URL matches a block pattern, THE SYSTEM SHALL call `Fetch.failRequest` with `errorReason: "BlockedByClient"`
- WHEN a request is blocked, THE SYSTEM SHALL preserve the `Network.requestWillBeSent` event (headers visible in `network()`)

### Story 3: Response Mocking
**As a** developer
**I want** to mock API responses
**So that** I can test error handling and edge cases

**Acceptance Criteria:**
- WHEN `fetch({"mock": {"*api/users*": '{"error": "Not found"}'}})` is called, THE SYSTEM SHALL intercept requests at Response stage
- WHEN a paused request URL matches a mock pattern with string value, THE SYSTEM SHALL call `Fetch.fulfillRequest` with `responseCode: 200` and body as base64-encoded content
- WHEN a mock pattern has dict value `{"body": "...", "status": 404}`, THE SYSTEM SHALL use the specified status code
- WHEN a request is mocked, THE SYSTEM SHALL store the mock response as `Network.responseBodyCaptured` for `request()` inspection

### Story 4: Combined Rules
**As a** user
**I want** to combine capture, block, and mock in one call
**So that** I can configure complex interception scenarios

**Acceptance Criteria:**
- WHEN `fetch({"capture": True, "block": ["*ads*"], "mock": {"*api*": "{}"}})` is called, THE SYSTEM SHALL apply all rules
- WHEN a URL matches multiple rules, THE SYSTEM SHALL apply priority: mock (highest) → block → capture (lowest)
- WHEN `fetch({})` is called, THE SYSTEM SHALL call `Fetch.disable` on all connections

### Story 5: Status Display
**As a** user
**I want** to see current fetch rules
**So that** I know what interception is active

**Acceptance Criteria:**
- WHEN `fetch("status")` is called, THE SYSTEM SHALL return current rules as dict or "disabled"
- WHEN rules are active, THE SYSTEM SHALL include the rules in SSE state broadcast

## Non-Functional Requirements

- **Latency**: ~20-50ms per request when capture enabled (acceptable for debugging use case)
- **Memory**: Bodies stored in DuckDB as synthetic events (existing pattern, no new storage)
- **Compatibility**: Works with existing `network()`, `request()` commands unchanged
- **Thread Safety**: Rule evaluation and CDP calls must be thread-safe

## Constraints

### CDP Protocol Constraints (from cdp_protocol.json)
- `Fetch.getResponseBody` may ONLY be called when paused in Response stage
- `Fetch.fulfillRequest.body` parameter must be base64-encoded binary
- `Fetch.continueResponse` is experimental but required for response-stage continuation
- Response stage detection: `responseStatusCode` OR `responseErrorReason` present in `requestPaused` event
- Redirect responses (301/302/303/307/308) have no body available

### Technical Constraints
- WebSocket message handling runs on dedicated thread (callbacks must be synchronous)
- DuckDB operations use thread-safe queue pattern (existing)
- Extension communicates via RPC over HTTP (existing)

## Out of Scope

- Manual `resume()`, `fail()`, `fulfill()` commands (removed - replaced by rules)
- Request-stage interception (only Response stage needed for body capture)
- Conditional rules based on headers/cookies/request body
- Per-request rule configuration (rules apply to all matching URLs)
- Body modification (capture stores original, mock replaces entirely)

## Assumptions

1. Users accept ~20-50ms latency per request when capture is enabled (debugging tool, not production proxy)
2. Glob patterns (`*`, `?`) are sufficient for URL matching (no regex needed)
3. Mock responses use same Content-Type as matched response (no explicit header override)
4. Body capture failures on redirects are acceptable (redirects have no body per CDP spec)
5. Extension only needs simple on/off toggle (no rule configuration in UI)
6. Lazy body fetch remains as fallback when capture is off (`request()` tries DuckDB first, then `Network.getResponseBody`)
