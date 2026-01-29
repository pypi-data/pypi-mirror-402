# Design: Rules-Based Fetch

## Architecture Overview

Replace the manual pause/resume fetch workflow with an automatic rules engine. When rules are active, `Fetch.requestPaused` events are handled automatically based on pattern matching - no user intervention required.

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Commands                            │
│  fetch({"capture": True})   fetch({"block": [...]})   fetch({}) │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │      FetchService         │
                    │  - rules: FetchRules      │
                    │  - _on_request_paused()   │
                    └─────────────┬─────────────┘
                                  │ Callback registered on
                                  │ Fetch.requestPaused
                    ┌─────────────▼─────────────┐
                    │       CDPSession          │
                    │  - Fetch.enable           │
                    │  - Fetch.getResponseBody  │
                    │  - Fetch.continueResponse │
                    │  - Fetch.failRequest      │
                    │  - Fetch.fulfillRequest   │
                    └───────────────────────────┘
```

## Component Analysis

### Existing Components to Modify

#### `src/webtap/services/fetch.py`
**Current:** Manual pause/resume with `continue_request()`, `fail_request()`, `fulfill_request()`
**New:** Rules engine with auto-handling callback

Key changes:
- Add `FetchRules` dataclass
- Add `_on_request_paused(event)` callback
- Add `_matches_pattern(url, pattern)` glob matcher
- Remove `continue_request()`, `fail_request()`, `fulfill_request()`
- Remove `_wait_for_next_event()` polling
- Remove `get_paused_event()`, `get_paused_by_network_id()`

#### `src/webtap/commands/fetch.py`
**Current:** `fetch(action, response)` with separate `resume()`, `fail()`, `fulfill()`, `requests()`
**New:** `fetch(rules)` only

Key changes:
- Change signature to `fetch(rules: dict | str)`
- Remove `resume`, `fail`, `fulfill`, `requests` commands
- Update `__all__` exports

#### `src/webtap/rpc/handlers.py`
**Current:** Handlers for `fetch.enable`, `fetch.disable`, `fetch.resume`, `fetch.fail`, `fetch.fulfill`
**New:** Only `fetch.enable` (with rules) and `fetch.disable`

Key changes:
- Remove `_fetch_resume`, `_fetch_fail`, `_fetch_fulfill` handlers
- Update `_fetch_enable` to accept rules dict
- Remove `requires_paused_request` decorator usage

#### `src/webtap/api/state.py`
**Current:** `fetch: {enabled, response_stage, paused_count}`
**New:** `fetch: {enabled, rules, capture_count}`

Key changes:
- Replace `response_stage` and `paused_count` with `rules` dict
- Add `capture_count` for bodies captured this session

#### `src/webtap/services/state_snapshot.py`
**Current:** `fetch_enabled`, `response_stage`, `paused_count`
**New:** `fetch_enabled`, `fetch_rules`, `capture_count`

#### `extension/controllers/intercept.js`
**Current:** Dropdown with Off/Req/Req+Res modes
**New:** Simple toggle button for capture on/off

#### `extension/sidepanel.html`
**Current:** Dropdown HTML
**New:** Toggle button HTML

### Components to Remove

- `src/webtap/commands/fetch.py`: `resume()`, `fail()`, `fulfill()`, `requests()` functions
- `src/webtap/services/fetch.py`: Manual resume/fail/fulfill methods, polling logic
- `src/webtap/rpc/handlers.py`: `_fetch_resume`, `_fetch_fail`, `_fetch_fulfill`

## Data Models

### FetchRules (Python dataclass)

```python
from dataclasses import dataclass, field

@dataclass
class FetchRules:
    """Declarative rules for fetch interception."""
    capture: bool = False
    block: list[str] = field(default_factory=list)
    mock: dict[str, str | dict] = field(default_factory=dict)

    def is_empty(self) -> bool:
        """Check if no rules are configured."""
        return not self.capture and not self.block and not self.mock

    def to_dict(self) -> dict:
        """Convert to dict for state snapshot."""
        return {
            "capture": self.capture,
            "block": self.block,
            "mock": self.mock,
        }
```

### Mock Value Format

```python
# String: body only, status 200
{"*api*": '{"ok": true}'}

# Dict: body + status
{"*api*": {"body": '{"error": "Not found"}', "status": 404}}
```

## API Design

### New fetch() Command

```python
@app.command(display="markdown", fastmcp={"type": "tool"})
def fetch(state, rules: dict | str = None) -> dict:
    """Control fetch interception with declarative rules.

    Args:
        rules: Dict with rules or "status" string
            - {"capture": True} - Capture all response bodies
            - {"block": ["*pattern*"]} - Block matching URLs
            - {"mock": {"*pattern*": "body"}} - Mock matching URLs
            - {} - Disable all rules
            - "status" - Show current rules

    Examples:
        fetch({"capture": True})                    # Capture bodies
        fetch({"block": ["*tracking*", "*ads*"]})  # Block patterns
        fetch({"mock": {"*api*": '{"ok":1}'}})     # Mock responses
        fetch({"capture": True, "block": ["*ads*"]}) # Combine
        fetch({})                                   # Disable
        fetch("status")                             # Show status
    """
```

### RPC Methods

```python
# fetch.enable - Enable with rules
# Request: {"rules": {"capture": true, "block": [], "mock": {}}}
# Response: {"enabled": true, "rules": {...}}

# fetch.disable - Disable all interception
# Request: {}
# Response: {"enabled": false}
```

## Data Flow

### Enable Capture Mode

```
User: fetch({"capture": True})
  │
  ▼
RPC: fetch.enable(rules={"capture": True})
  │
  ▼
FetchService.enable(rules):
  1. self.rules = FetchRules(capture=True)
  2. For each connection:
     - cdp.execute("Fetch.enable", patterns=[{urlPattern: "*", requestStage: "Response"}])
     - cdp.register_event_callback("Fetch.requestPaused", self._on_request_paused)
  3. self.enabled = True
  4. Trigger SSE broadcast
```

### Request Paused Event Handling

```
Chrome: Fetch.requestPaused event received
  │
  ▼
CDPSession._on_message():
  - Stores event in DuckDB
  - Calls registered callbacks
  │
  ▼
FetchService._on_request_paused(event):
  │
  ├─ Check response stage (responseStatusCode present?)
  │  └─ If Request stage: continueRequest immediately (no body to capture)
  │
  ├─ Extract URL from event.params.request.url
  │
  ├─ Check mock patterns (first match wins)
  │  └─ Match: fulfillRequest with mock body
  │
  ├─ Check block patterns
  │  └─ Match: failRequest with BlockedByClient
  │
  ├─ Capture mode enabled?
  │  └─ Yes: getResponseBody → store → continueResponse
  │
  └─ Default: continueResponse immediately
```

### CDP Calls (aligned with cdp_protocol.json)

```python
# Enable at Response stage only
cdp.execute("Fetch.enable", {
    "patterns": [{"urlPattern": "*", "requestStage": "Response"}]
})

# Get body while paused (Response stage only)
result = cdp.execute("Fetch.getResponseBody", {"requestId": request_id})
# Returns: {"body": "...", "base64Encoded": true/false}

# Continue from Response stage
cdp.execute("Fetch.continueResponse", {"requestId": request_id})

# Block request
cdp.execute("Fetch.failRequest", {
    "requestId": request_id,
    "errorReason": "BlockedByClient"
})

# Mock response (body must be base64)
import base64
cdp.execute("Fetch.fulfillRequest", {
    "requestId": request_id,
    "responseCode": 200,
    "body": base64.b64encode(body.encode()).decode(),
    "responseHeaders": [{"name": "Content-Type", "value": "application/json"}]
})
```

## Pattern Matching

Use Python's `fnmatch` for glob-style patterns:

```python
import fnmatch

def _matches_pattern(url: str, pattern: str) -> bool:
    """Match URL against glob pattern.

    Patterns:
        * - matches any characters
        ? - matches single character

    Examples:
        _matches_pattern("https://api.example.com/users", "*api*") → True
        _matches_pattern("https://tracking.com/pixel", "*tracking*") → True
    """
    return fnmatch.fnmatch(url, pattern)
```

## State Snapshot Changes

### Before (StateSnapshot dataclass)

```python
fetch_enabled: bool
response_stage: bool
paused_count: int
```

### After

```python
fetch_enabled: bool
fetch_rules: dict | None  # {"capture": bool, "block": list, "mock": dict}
capture_count: int  # Bodies captured this session
```

### SSE State Format

```json
{
  "fetch": {
    "enabled": true,
    "rules": {
      "capture": true,
      "block": ["*ads*"],
      "mock": {}
    },
    "capture_count": 42
  }
}
```

## Extension UI Changes

### Before: Dropdown

```html
<div id="interceptDropdown" class="dropdown">
  <button class="dropdown-toggle">Intercept: Off</button>
  <div class="dropdown-menu">
    <button data-value="disabled">Off</button>
    <button data-value="request">Req</button>
    <button data-value="response">Req+Res</button>
  </div>
</div>
```

### After: Toggle Button

```html
<button id="captureToggle" class="toggle-btn">
  Capture: Off
</button>
```

### JavaScript Changes

```javascript
// controllers/intercept.js → controllers/capture.js

export function init(client, callbacks) {
  const btn = document.getElementById("captureToggle");

  btn.onclick = async () => {
    const isEnabled = btn.classList.contains("active");
    if (isEnabled) {
      await client.call("fetch.disable");
    } else {
      await client.call("fetch.enable", { rules: { capture: true } });
    }
  };
}

export function update(state) {
  const btn = document.getElementById("captureToggle");
  const enabled = state.fetch?.enabled && state.fetch?.rules?.capture;

  btn.classList.toggle("active", enabled);
  btn.textContent = `Capture: ${enabled ? "On" : "Off"}`;
}
```

## Error Handling

| Scenario | Action |
|----------|--------|
| `getResponseBody` fails (redirect) | Log debug, continue response |
| `getResponseBody` times out | Log warning, continue response |
| Invalid pattern syntax | Return error from `fetch()` command |
| CDP connection lost | Rules preserved, re-enable on reconnect |
| Mock body encoding fails | Return error, don't fulfill |

## Thread Safety

- `FetchRules` is immutable once set (replaced atomically)
- Callback runs on WebSocket thread (must be synchronous)
- CDP calls are synchronous with timeout
- DuckDB writes use existing thread-safe queue pattern

## Migration Notes

### Removed Commands

Users calling old commands will get errors:
- `resume(id)` → "Unknown command. Use fetch() with rules instead."
- `fail(id)` → "Unknown command. Use fetch({'block': [...]}) instead."
- `fulfill(id)` → "Unknown command. Use fetch({'mock': {...}}) instead."
- `requests()` → "Use network(req_state='paused') instead."

### Extension Compatibility

Extension dropdown will be replaced with toggle. Old extension versions will fail gracefully (RPC method signature changed).
