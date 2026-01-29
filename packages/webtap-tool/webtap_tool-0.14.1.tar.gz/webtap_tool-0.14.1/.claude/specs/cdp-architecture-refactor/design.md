# Design: CDP Architecture Refactor

## Architecture Overview

This refactor simplifies WebTap's state management by removing the global ConnectionMachine and extracting connection lifecycle into a dedicated ConnectionManager. Additionally, it moves fetch capture to the extension side for near-zero latency body capture.

### Current Architecture (Complex)
```
Chrome CDP ←→ CDPSession ←→ WebTapService ←→ RPCFramework ←→ FastAPI
                  │              │                  │
              WebSocket     7+ domains         Global Machine
              + DB Thread   (812 lines)       + Per-Target State
```

### Target Architecture (Simplified)
```
Chrome CDP ←→ CDPSession ←→ ConnectionManager ←→ WebTapService ←→ FastAPI
                  │               │                    │
              WebSocket      Per-Target           Domain Services
              + DB Thread    State Only           (pure queries)
                                  │
                            ┌─────┴─────┐
                            │ Extension │
                            │ Capture   │
                            └───────────┘
```

---

## Component Analysis

### Existing Components to Modify

#### `src/webtap/rpc/machine.py` - DELETE
Global state machine with 5 states and 8 transitions. Will be removed entirely.

#### `src/webtap/rpc/framework.py` - MAJOR
- Remove `ConnectionMachine` import and instantiation (line 65)
- Remove epoch validation against machine (lines 227-235)
- Keep epoch in responses but source from service
- Simplify `_validate_request()` to use per-target state only

#### `src/webtap/rpc/handlers.py` - MAJOR
- Remove all `ctx.machine.*` calls
- Remove first-connection guards (`is_first_connection` pattern)
- Move inspection state to per-target in DOMService
- Handlers affected:
  - `connect()` (lines 103-135)
  - `disconnect()` (lines 138-169)
  - `browser_start_inspect()` (lines 220-235)
  - `browser_stop_inspect()` (lines 238-242)

#### `src/webtap/services/main.py` - MAJOR (~400 lines reduction)
- Extract connection lifecycle to `ConnectionManager`
- Delegate: `connect_to_page()`, `disconnect_target()`, `disconnect()`
- Keep: snapshot creation, broadcast triggering, service coordination
- Fix `_trigger_broadcast()` - create snapshot outside lock

#### `src/webtap/services/dom.py` - MINOR
- Add per-target inspection state tracking
- Coordinate state mutations with service lock
- Replace global `inspecting` state with target-specific flag

#### `src/webtap/services/fetch.py` - MAJOR
- Add RPC handler for receiving captured bodies from extension
- Store bodies in HAR cache (existing structure)
- Add `fetch.pushBody` RPC method

#### `extension/client.js` - MAJOR
- Add exponential backoff for SSE reconnection
- Reset epoch on successful reconnect
- Add retry logic for transient errors (3x with backoff)
- Add `chrome.debugger` integration for fetch capture

#### `extension/main.js` - MINOR
- Pass state explicitly to all controller update() calls
- Add fetch capture initialization

#### `extension/controllers/*.js` - MINOR
- Use passed state parameter instead of `client.state`
- Affected: targets.js, pages.js, network.js, console.js, filters.js, intercept.js

#### `extension/manifest.json` - MINOR
- Add `"debugger"` permission for fetch capture

### New Components to Create

#### `src/webtap/services/connection.py` - NEW
ConnectionManager with per-target locking and lifecycle.

#### `extension/capture.js` - NEW
Extension-side fetch capture using chrome.debugger API.

---

## Data Models

### TargetState Enum (existing, unchanged)
```python
class TargetState(str, Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
```

### ActiveConnection (existing, add inspection flag)
```python
@dataclass
class ActiveConnection:
    target: str                      # Target ID "{port}:{short-id}"
    cdp: CDPSession                  # CDP session instance
    page_info: dict                  # Page metadata
    connected_at: float              # Connection timestamp
    state: TargetState = TargetState.CONNECTED
    inspecting: bool = False         # NEW: Per-target inspection state
```

### ConnectionManager (new)
```python
class ConnectionManager:
    """Thread-safe connection lifecycle management."""

    def __init__(self):
        self.connections: dict[str, ActiveConnection] = {}
        self._locks: dict[str, threading.Lock] = {}  # Per-target locks
        self._global_lock: threading.Lock = threading.Lock()  # For connections dict
        self._epoch: int = 0  # Global epoch, increments on any state change

    @property
    def epoch(self) -> int:
        return self._epoch

    def _get_target_lock(self, target: str) -> threading.Lock:
        with self._global_lock:
            if target not in self._locks:
                self._locks[target] = threading.Lock()
            return self._locks[target]

    def connect(self, target: str, cdp: CDPSession, page_info: dict) -> ActiveConnection:
        """Thread-safe connection registration."""
        lock = self._get_target_lock(target)
        with lock:
            if target in self.connections:
                return self.connections[target]  # Idempotent
            conn = ActiveConnection(
                target=target,
                cdp=cdp,
                page_info=page_info,
                connected_at=time.time(),
                state=TargetState.CONNECTED
            )
            with self._global_lock:
                self.connections[target] = conn
                self._epoch += 1
            return conn

    def disconnect(self, target: str) -> bool:
        """Thread-safe disconnection with double-disconnect prevention."""
        lock = self._get_target_lock(target)
        with lock:
            conn = self.connections.get(target)
            if not conn or conn.state == TargetState.DISCONNECTING:
                return False  # Already disconnecting or not found

            conn.state = TargetState.DISCONNECTING
            # Disconnect CDP outside lock (network I/O)

        conn.cdp.disconnect()
        conn.cdp.cleanup()

        with self._global_lock:
            self.connections.pop(target, None)
            self._locks.pop(target, None)
            self._epoch += 1
        return True

    def get(self, target: str) -> ActiveConnection | None:
        return self.connections.get(target)

    def get_all(self) -> list[ActiveConnection]:
        return list(self.connections.values())

    def set_inspecting(self, target: str, inspecting: bool) -> bool:
        conn = self.connections.get(target)
        if conn and conn.state == TargetState.CONNECTED:
            conn.inspecting = inspecting
            with self._global_lock:
                self._epoch += 1
            return True
        return False
```

### CapturedBody (for extension-to-daemon sync)
```python
@dataclass
class CapturedBody:
    request_id: str      # CDP request ID
    target: str          # Target ID
    body: str            # Base64 encoded body
    base64_encoded: bool # Whether body is base64
    timestamp: float     # Capture timestamp
```

---

## API Changes

### New RPC Method: `fetch.pushBody`
Receives captured bodies from extension.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "fetch.pushBody",
  "params": {
    "request_id": "123.456",
    "target": "9222:abc",
    "body": "eyJkYXRhIjogWzEsMiwzXX0=",
    "base64_encoded": true
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {"stored": true},
  "id": 1,
  "epoch": 43
}
```

### Modified State Snapshot
```python
# Add to StateSnapshot
fetch: FetchState = field(default_factory=lambda: FetchState(
    enabled=False,
    paused_count=0,
    response_stage=False,
    capture_enabled=False,  # NEW
    capture_mode="off"      # NEW: "off" | "capture"
))
```

---

## Data Flow

### Connection Lifecycle (Simplified)
```
┌─────────────────────────────────────────────────────────────────┐
│                        RPC: connect                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ConnectionManager.connect(target, cdp, page_info)              │
│  ├─ Acquire per-target lock                                     │
│  ├─ Check if already connected (idempotent)                     │
│  ├─ Create ActiveConnection                                     │
│  ├─ Register in connections dict                                │
│  ├─ Increment epoch                                             │
│  └─ Return connection                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  WebTapService                                                   │
│  ├─ Wire disconnect callback                                    │
│  ├─ Enable CDP domains                                          │
│  ├─ Trigger broadcast                                           │
│  └─ Return connection info                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Extension-Side Fetch Capture
```
┌─────────────────────────────────────────────────────────────────┐
│  User: fetch("capture")                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  RPC: fetch.enable + capture mode                               │
│  → FetchService enables Fetch domain at response stage          │
│  → State broadcast: capture_enabled=true                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Extension: capture.js receives state update                    │
│  → Attaches chrome.debugger to connected tabs                   │
│  → Subscribes to Fetch.requestPaused events                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Chrome: Fetch.requestPaused (response stage)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Extension: capture.js handler                                  │
│  1. chrome.debugger.sendCommand("Fetch.getResponseBody")        │
│  2. chrome.debugger.sendCommand("Fetch.continueRequest")        │
│  3. client.call("fetch.pushBody", {body, request_id, target})   │
│     (async, non-blocking)                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Daemon: fetch.pushBody handler                                 │
│  → Store body in CDPSession's body cache                        │
│  → Body available for request() queries                         │
└─────────────────────────────────────────────────────────────────┘
```

### SSE Reconnection Flow
```
┌─────────────────────────────────────────────────────────────────┐
│  SSE connection lost                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  client.js: _reconnectSSE()                                     │
│  ├─ Attempt 1: wait 1s, try connect                            │
│  ├─ Attempt 2: wait 2s, try connect                            │
│  ├─ Attempt 3: wait 4s, try connect                            │
│  ├─ ...                                                         │
│  └─ Max: wait 30s between attempts                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  On successful reconnect:                                       │
│  ├─ this._reconnectAttempts = 0                                 │
│  ├─ this.state.epoch = 0  // Reset to prevent STALE_EPOCH      │
│  └─ First SSE message syncs correct epoch                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Error Handling Strategy

### Error Types by Layer

| Layer | Error Type | Handling |
|-------|------------|----------|
| CDPSession | `CDPError`, `TimeoutError` | Raise to caller |
| ConnectionManager | Returns `None`/`False` | Caller checks |
| Services | `ServiceError` | Convert to RPCError |
| RPC Handlers | `RPCError` | JSON-RPC error response |
| Extension | Retry transient, display permanent | 3x backoff retry |

### Transient vs Permanent Errors (Extension)

```javascript
_isTransientError(err) {
  // Retry these
  return (
    err.code === 'NETWORK_ERROR' ||
    err.code === 'TIMEOUT' ||
    err.code === 'STALE_EPOCH' ||
    err.message?.includes('fetch failed')
  );
  // Don't retry: NOT_CONNECTED, INVALID_PARAMS, etc.
}
```

---

## Security Considerations

### chrome.debugger API
- Requires explicit user permission in manifest
- Only attaches to tabs with active WebTap connection
- Detaches on connection close or extension disable

### Body Data
- Bodies stored in memory only (not persisted)
- Cleared on disconnect or explicit clear
- No sensitive data logging

---

## File Changes Summary

| File | Action | Lines Changed (Est.) |
|------|--------|---------------------|
| `rpc/machine.py` | DELETE | -180 |
| `rpc/framework.py` | MODIFY | ~50 |
| `rpc/handlers.py` | MODIFY | ~80 |
| `rpc/__init__.py` | MODIFY | ~5 |
| `services/connection.py` | CREATE | ~150 |
| `services/main.py` | MAJOR | -400 |
| `services/dom.py` | MODIFY | ~30 |
| `services/fetch.py` | MODIFY | ~50 |
| `extension/client.js` | MAJOR | ~100 |
| `extension/main.js` | MODIFY | ~30 |
| `extension/capture.js` | CREATE | ~80 |
| `extension/manifest.json` | MODIFY | ~5 |
| `extension/controllers/*.js` | MODIFY | ~60 total |

**Net effect:** ~400 lines removed, ~300 lines added = ~100 line reduction with better architecture.
