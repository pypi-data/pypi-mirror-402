# Implementation Tasks: CDP Architecture Refactor

**Status:** Completed
**Completed:** 2025-12-28
**Spec:** [requirements.md](./requirements.md) | [design.md](./design.md)

## Task Breakdown

### Task 1: Create ConnectionManager
**Description:** Extract connection lifecycle from main.py into new ConnectionManager class with per-target locking.

**Files:**
- `src/webtap/services/connection.py` - CREATE: ConnectionManager class
- `src/webtap/services/__init__.py` - Export ConnectionManager

**Implementation:**
```python
class ConnectionManager:
    connections: dict[str, ActiveConnection]
    _locks: dict[str, threading.Lock]  # Per-target
    _global_lock: threading.Lock        # For dict operations
    _epoch: int                          # Global counter

    def connect(target, cdp, page_info) -> ActiveConnection
    def disconnect(target) -> bool
    def get(target) -> ActiveConnection | None
    def get_all() -> list[ActiveConnection]
    def set_inspecting(target, inspecting) -> bool
```

**Acceptance:**
- [x] Per-target locks prevent concurrent operations on same target
- [x] Epoch increments on connect/disconnect/inspect changes
- [x] Double-disconnect returns False (idempotent)
- [x] Thread-safe connection lookup

**Dependencies:** None
**Complexity:** Medium
**Completed:** 2025-12-28

---

### Task 2: Remove ConnectionMachine
**Description:** Delete global state machine and remove all references.

**Files:**
- `src/webtap/rpc/machine.py` - DELETE entirely
- `src/webtap/rpc/__init__.py` - Remove machine exports
- `src/webtap/rpc/framework.py` - Remove machine instantiation, keep epoch from service
- `src/webtap/api/state.py` - Get epoch from service instead of machine

**Acceptance:**
- [x] machine.py deleted
- [x] No imports of ConnectionMachine remain
- [x] RPCFramework no longer creates machine
- [x] Epoch sourced from ConnectionManager

**Dependencies:** Task 1
**Complexity:** Low
**Completed:** 2025-12-28

---

### Task 3: Update RPC Handlers for Per-Target State
**Description:** Remove global machine checks, use per-target validation only.

**Files:**
- `src/webtap/rpc/handlers.py` - Remove ctx.machine.* calls, use per-target state

**Changes:**
- `connect()`: Remove first-connection guard, just connect
- `disconnect()`: Remove machine transitions, use ConnectionManager
- `browser_start_inspect()`: Use ConnectionManager.set_inspecting()
- `browser_stop_inspect()`: Use ConnectionManager.set_inspecting()

**Acceptance:**
- [x] No ctx.machine references remain
- [x] Concurrent connects to different targets work
- [x] Inspection state per-target
- [x] All RPC methods still functional

**Dependencies:** Task 1, Task 2
**Complexity:** Medium
**Completed:** 2025-12-28

---

### Task 4: Integrate ConnectionManager into WebTapService
**Description:** Delegate connection operations to ConnectionManager, reduce main.py size.

**Files:**
- `src/webtap/services/main.py` - Use ConnectionManager, remove extracted code

**Changes:**
- Add `self.conn_mgr = ConnectionManager()`
- Delegate `connect_to_page()` → create CDP then `conn_mgr.connect()`
- Delegate `disconnect_target()` → `conn_mgr.disconnect()`
- Delegate `disconnect()` → iterate and disconnect all
- Update `get_connection()` → `conn_mgr.get()`
- Update `_create_snapshot()` → get epoch from conn_mgr

**Acceptance:**
- [x] main.py under 400 lines
- [x] All connection tests pass manually
- [x] Epoch in snapshots works correctly

**Dependencies:** Task 1, Task 2, Task 3
**Complexity:** High
**Completed:** 2025-12-28

---

### Task 5: Fix Snapshot Lock Contention
**Description:** Create snapshot outside lock, swap atomically.

**Files:**
- `src/webtap/services/main.py` - Fix `_trigger_broadcast()`

**Current (problematic):**
```python
with self._state_lock:
    self._state_snapshot = self._create_snapshot()  # Slow!
```

**Fixed:**
```python
snapshot = self._create_snapshot()  # Outside lock
with self._state_lock:
    self._state_snapshot = snapshot  # Fast atomic swap
```

**Acceptance:**
- [x] Snapshot creation doesn't hold lock
- [x] No race conditions in snapshot swap
- [x] Broadcast still coalesces correctly

**Dependencies:** Task 4
**Complexity:** Low
**Completed:** 2025-12-28

---

### Task 6: Extension SSE Reconnection
**Description:** Add exponential backoff for SSE reconnection with epoch reset.

**Files:**
- `extension/client.js` - Add reconnection logic

**Implementation:**
```javascript
_reconnectSSE() {
    const backoff = Math.min(30000, 1000 * Math.pow(2, this._reconnectAttempts));
    setTimeout(() => {
        this._reconnectAttempts++;
        this.connect();
    }, backoff);
}

connect() {
    // ... existing ...
    this._eventSource.onopen = () => {
        this._reconnectAttempts = 0;
        this.state.epoch = 0;  // Reset to sync with server
    };
    this._eventSource.onerror = () => {
        this._reconnectSSE();
    };
}
```

**Acceptance:**
- [x] SSE reconnects automatically on disconnect
- [x] Backoff: 1s, 2s, 4s, 8s... up to 30s
- [x] Epoch resets on reconnect (no STALE_EPOCH)
- [x] Reconnect counter resets on success

**Dependencies:** None
**Complexity:** Low
**Completed:** 2025-12-28

---

### Task 7: Extension Error Retry Logic
**Description:** Add automatic retry for transient RPC errors.

**Files:**
- `extension/client.js` - Add retry wrapper

**Implementation:**
```javascript
async call(method, params, options = {}) {
    const maxRetries = options.maxRetries ?? 3;
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            return await this._doCall(method, params, options);
        } catch (err) {
            if (this._isTransientError(err) && attempt < maxRetries) {
                await this._delay(1000 * Math.pow(2, attempt));
                continue;
            }
            throw err;
        }
    }
}

_isTransientError(err) {
    return err.code === 'NETWORK_ERROR' ||
           err.code === 'TIMEOUT' ||
           err.message?.includes('fetch failed');
}
```

**Acceptance:**
- [x] Transient errors retry up to 3 times
- [x] Exponential backoff between retries
- [x] Permanent errors fail immediately
- [x] STALE_EPOCH handled by existing logic (not retried here)

**Dependencies:** None
**Complexity:** Low
**Completed:** 2025-12-28

---

### Task 8: Extension State Passing
**Description:** Pass state explicitly to controllers instead of reading client.state.

**Files:**
- `extension/main.js` - Pass state to update() calls
- `extension/controllers/targets.js` - Use passed state
- `extension/controllers/pages.js` - Use passed state
- `extension/controllers/network.js` - Use passed state
- `extension/controllers/console.js` - Use passed state
- `extension/controllers/intercept.js` - Use passed state

**Changes:**
```javascript
// main.js
client.on("state", (state, prevState) => {
    targets.update(state);  // Pass state
    // ...
});

// controllers - use parameter
export function update(state) {
    const connections = state.connections || [];  // Not client.state
}
```

**Acceptance:**
- [x] Controllers use passed state parameter
- [x] No direct client.state reads in update()
- [x] UI updates correctly with passed state

**Dependencies:** None
**Complexity:** Low
**Completed:** 2025-12-28

---

### Task 9: Add Manifest Debugger Permission
**Description:** Add chrome.debugger permission for fetch capture.

**Files:**
- `extension/manifest.json` - Add permission

**Change:**
```json
{
  "permissions": [
    "activeTab",
    "tabs",
    "sidePanel",
    "contextMenus",
    "storage",
    "debugger"  // ADD
  ]
}
```

**Acceptance:**
- [x] Extension loads without errors
- [x] chrome.debugger API available

**Dependencies:** None
**Complexity:** Low
**Completed:** 2025-12-28

---

### Task 10: Extension Fetch Capture Module
**Description:** Create capture.js for extension-side response body capture.

**Files:**
- `extension/capture.js` - CREATE: Fetch capture logic

**Implementation:**
```javascript
// capture.js
let client = null;
let activeTargets = new Map();  // tabId -> debugger attached

export function init(c) {
    client = c;
}

export function update(state) {
    if (state.fetch?.capture_enabled) {
        attachToConnectedTabs(state.connections);
    } else {
        detachAll();
    }
}

function attachToConnectedTabs(connections) {
    for (const conn of connections) {
        const tabId = extractTabId(conn.target);
        if (!activeTargets.has(tabId)) {
            chrome.debugger.attach({tabId}, "1.3", () => {
                chrome.debugger.sendCommand({tabId}, "Fetch.enable", {
                    patterns: [{requestStage: "Response"}]
                });
                activeTargets.set(tabId, conn.target);
            });
        }
    }
}

// Listen for paused requests
chrome.debugger.onEvent.addListener((source, method, params) => {
    if (method === "Fetch.requestPaused" && params.responseStatusCode) {
        handlePausedResponse(source.tabId, params);
    }
});

async function handlePausedResponse(tabId, params) {
    const target = activeTargets.get(tabId);

    // Get body
    chrome.debugger.sendCommand({tabId}, "Fetch.getResponseBody",
        {requestId: params.requestId}, (result) => {
            // Continue immediately
            chrome.debugger.sendCommand({tabId}, "Fetch.continueRequest",
                {requestId: params.requestId});

            // Push to daemon async
            if (result?.body) {
                client.call("fetch.pushBody", {
                    request_id: params.requestId,
                    target: target,
                    body: result.body,
                    base64_encoded: result.base64Encoded
                }).catch(console.error);
            }
        });
}
```

**Acceptance:**
- [x] Attaches debugger to connected tabs when capture enabled
- [x] Captures response bodies on Fetch.requestPaused
- [x] Continues requests immediately (no latency)
- [x] Pushes bodies to daemon async
- [x] Detaches on disable

**Dependencies:** Task 9
**Complexity:** High
**Completed:** 2025-12-28

---

### Task 11: Daemon Fetch PushBody Handler
**Description:** Add RPC handler to receive and store captured bodies.

**Files:**
- `src/webtap/rpc/handlers.py` - Add fetch_push_body handler
- `src/webtap/services/fetch.py` - Add body storage method

**Implementation:**
```python
# handlers.py
@rpc.method("fetch.pushBody")
def fetch_push_body(ctx: RPCContext, request_id: str, target: str,
                    body: str, base64_encoded: bool) -> dict:
    ctx.service.fetch.store_body(request_id, target, body, base64_encoded)
    return {"stored": True}

# fetch.py
def store_body(self, request_id: str, target: str, body: str, base64_encoded: bool):
    conn = self.service.get_connection(target)
    if conn:
        conn.cdp.store_response_body(request_id, body, base64_encoded)
```

**Acceptance:**
- [x] RPC method registered and callable
- [x] Bodies stored in CDP session cache
- [x] request() queries find stored bodies

**Dependencies:** Task 10
**Complexity:** Medium
**Completed:** 2025-12-28

---

### Task 12: Wire Capture to Main.js
**Description:** Initialize and wire capture module in extension.

**Files:**
- `extension/main.js` - Import and init capture module
- `extension/sidepanel.html` - Add capture.js script (if needed)

**Changes:**
```javascript
// main.js
import * as capture from './capture.js';

// In init
capture.init(client);

// In state listener
client.on("state", (state) => {
    capture.update(state);
    // ... other controllers
});
```

**Acceptance:**
- [x] Capture module initialized on load
- [x] Capture updates on state changes
- [x] fetch("capture") enables extension-side capture

**Dependencies:** Task 10, Task 11
**Complexity:** Low
**Completed:** 2025-12-28

---

## Task Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│  Task 1: ConnectionManager                                       │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Task 2: Remove ConnectionMachine                               │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Task 3: Update RPC Handlers                                    │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Task 4: Integrate into WebTapService                           │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Task 5: Fix Snapshot Lock                                      │
└─────────────────────────────────────────────────────────────────┘

Independent tracks (can run in parallel):

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Task 6: SSE      │  │ Task 7: Retry    │  │ Task 8: State    │
│ Reconnect        │  │ Logic            │  │ Passing          │
└──────────────────┘  └──────────────────┘  └──────────────────┘

┌──────────────────┐
│ Task 9: Manifest │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ Task 10: Capture │
│ Module           │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ Task 11: PushBody│
│ Handler          │
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ Task 12: Wire    │
│ Capture          │
└──────────────────┘
```

## Parallel Tracks

**Track A: Backend State Machine Refactor** (sequential)
- Task 1 → Task 2 → Task 3 → Task 4 → Task 5

**Track B: Extension Robustness** (parallel, independent)
- Task 6: SSE Reconnection
- Task 7: Error Retry
- Task 8: State Passing

**Track C: Fetch Capture** (sequential)
- Task 9 → Task 10 → Task 11 → Task 12

Tracks B and C can run in parallel with Track A after Task 1 is complete.
