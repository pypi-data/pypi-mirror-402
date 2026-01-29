# Design: Always-On Fetch Capture with Per-Target Rules

## Architecture Overview

Split fetch state into global capture flag and per-target rules. Hook into connection lifecycle for proper cleanup.

```
┌─────────────────────────────────────────────────────────────┐
│                      FetchService                           │
├─────────────────────────────────────────────────────────────┤
│  Global State                                               │
│  ├─ capture_enabled: bool = True (default on)               │
│  └─ _capture_count: int                                     │
├─────────────────────────────────────────────────────────────┤
│  Per-Target State                                           │
│  └─ _target_rules: dict[str, TargetRules]                   │
│       └─ TargetRules(block: list[str], mock: dict)          │
└─────────────────────────────────────────────────────────────┘
```

## Component Analysis

### Files to Modify

#### 1. `src/webtap/services/fetch.py`

**Changes:**
- Rename `FetchRules` → `TargetRules` (no capture field, just block/mock)
- Add `_target_rules: dict[str, TargetRules]` for per-target storage
- Add `capture_enabled: bool = True` as global default-on flag
- Add `cleanup_target(target: str)` method for disconnect/crash cleanup
- Add `enable_on_target(target: str, cdp)` for new connections
- Modify `_handle_paused_request()` to lookup target-specific rules

**New data model:**
```python
@dataclass
class TargetRules:
    """Per-target block/mock rules."""
    block: list[str] = field(default_factory=list)
    mock: dict[str, str | dict] = field(default_factory=dict)

    def is_empty(self) -> bool:
        return not self.block and not self.mock

class FetchService:
    def __init__(self):
        self._lock = threading.Lock()
        self.capture_enabled = True  # Global, default ON
        self._capture_count = 0
        self._target_rules: dict[str, TargetRules] = {}  # Per-target
        self.service: Any = None
```

**New/modified methods:**
```python
def enable_on_target(self, target: str, cdp: Any) -> None:
    """Enable fetch capture on a newly connected target.

    Called from connect_to_page(). Only enables if capture_enabled.
    """
    if not self.capture_enabled:
        return

    patterns = [{"urlPattern": "*", "requestStage": "Response"}]
    cdp.execute("Fetch.enable", {"patterns": patterns})
    cdp.register_event_callback(
        "Fetch.requestPaused",
        lambda event, cdp=cdp, target=target: self._on_request_paused(event, cdp, target)
    )

def cleanup_target(self, target: str, cdp: Any | None = None) -> None:
    """Clean up fetch state for a disconnected target.

    Called from disconnect_target() and _handle_unexpected_disconnect().
    """
    with self._lock:
        self._target_rules.pop(target, None)

    if cdp:
        try:
            cdp._event_callbacks.pop("Fetch.requestPaused", None)
            cdp._paused_count = 0
            cdp.execute("Fetch.disable")
        except Exception:
            pass  # CDP may already be dead

def set_capture(self, enabled: bool) -> dict:
    """Toggle global capture on/off."""
    with self._lock:
        if enabled == self.capture_enabled:
            return self.get_status()

        self.capture_enabled = enabled

        # Enable/disable on all current connections
        for conn in self.service.connections.values():
            try:
                if enabled:
                    self.enable_on_target(conn.target, conn.cdp)
                else:
                    conn.cdp._event_callbacks.pop("Fetch.requestPaused", None)
                    conn.cdp.execute("Fetch.disable")
            except Exception:
                pass

        self._trigger_broadcast()
        return self.get_status()

def set_rules(self, target: str, block: list[str] = None, mock: dict = None) -> dict:
    """Set block/mock rules for a specific target."""
    with self._lock:
        if block is None and mock is None:
            # Clear rules for target
            self._target_rules.pop(target, None)
        else:
            self._target_rules[target] = TargetRules(
                block=block or [],
                mock=mock or {}
            )
        self._trigger_broadcast()
        return self.get_status()

def get_status(self) -> dict:
    """Get current fetch status."""
    return {
        "capture": self.capture_enabled,
        "capture_count": self._capture_count,
        "rules": {
            target: {"block": r.block, "mock": r.mock}
            for target, r in self._target_rules.items()
        }
    }
```

**Modified `_handle_paused_request()`:**
```python
def _handle_paused_request(self, event: dict, cdp: Any, target: str) -> None:
    """Process paused request - lookup target-specific rules."""
    # ... existing request/response stage handling ...

    # Get rules for this target (if any)
    rules = self._target_rules.get(target)

    # Check mock patterns (target-specific)
    if rules:
        for pattern, mock_value in rules.mock.items():
            if _matches_pattern(url, pattern):
                self._fulfill_with_mock(cdp, request_id, mock_value, params)
                return

        # Check block patterns (target-specific)
        for pattern in rules.block:
            if _matches_pattern(url, pattern):
                self._fail_request(cdp, request_id)
                return

    # Capture body (global)
    if self.capture_enabled:
        self._capture_and_continue(cdp, request_id, params)
    else:
        cdp.execute("Fetch.continueResponse", {"requestId": request_id})
        cdp.decrement_paused_count()
```

#### 2. `src/webtap/services/main.py`

**Changes to `connect_to_page()`:**
```python
# Replace lines 618-623:
# Old:
# if self.fetch.enabled:
#     try:
#         cdp.execute("Fetch.enable", {"patterns": [{"urlPattern": "*"}]})
#     except Exception:
#         pass

# New:
self.fetch.enable_on_target(target_id, cdp)
```

**Changes to `disconnect_target()`:**
```python
def disconnect_target(self, target: str) -> None:
    """Disconnect specific target."""
    # Get CDP before disconnect (for cleanup)
    conn = self.conn_mgr.get(target)
    cdp = conn.cdp if conn else None

    # Clean up fetch state BEFORE disconnect
    self.fetch.cleanup_target(target, cdp)

    # Delegate to ConnectionManager
    disconnected = self.conn_mgr.disconnect(target)
    if not disconnected:
        return

    self.conn_mgr.remove_from_tracked(target, self.tracked_targets)
    self._trigger_broadcast()
```

**Changes to `_handle_unexpected_disconnect()`:**
```python
def _handle_unexpected_disconnect(self, target: str, code: int, reason: str) -> None:
    # ... existing code ...

    try:
        with self.conn_mgr._global_lock:
            conn = self.conn_mgr.connections.pop(target, None)
            # ...

        if not conn:
            return

        # Clean up fetch state (CDP already dead, pass None)
        self.fetch.cleanup_target(target, cdp=None)

        # ... rest of existing code ...
```

#### 3. `src/webtap/rpc/handlers.py`

**Changes to `_fetch_enable()` and `_fetch_disable()`:**

Replace with unified handler that routes to appropriate method:

```python
def _fetch(ctx: RPCContext, rules: dict | None = None) -> dict:
    """Handle fetch configuration."""
    if rules is None:
        # No args - return status
        return ctx.service.fetch.get_status()

    # Check for global capture toggle
    if "capture" in rules and len(rules) == 1:
        return ctx.service.fetch.set_capture(rules["capture"])

    # Check for target-specific rules
    if "target" in rules:
        target = rules["target"]
        if target not in ctx.service.connections:
            raise RPCError(ErrorCode.INVALID_PARAMS, f"Target '{target}' not connected")
        return ctx.service.fetch.set_rules(
            target=target,
            block=rules.get("block"),
            mock=rules.get("mock")
        )

    # Block/mock without target is error
    if "block" in rules or "mock" in rules:
        raise RPCError(ErrorCode.INVALID_PARAMS, "block/mock rules require 'target' parameter")

    return ctx.service.fetch.get_status()
```

#### 4. `src/webtap/commands/fetch.py`

**Update command to match new API:**
- Remove separate enable/disable logic
- Route to unified `_fetch` RPC handler
- Update help text and examples

## Data Flow

### Connect Flow (New)
```
connect("9222:abc")
    → connect_to_page()
        → CDPSession.connect()
        → enable domains
        → conn_mgr.connect()
        → fetch.enable_on_target(target, cdp)  # NEW: always enable capture
            → Fetch.enable with Response stage pattern
            → register callback with target in closure
        → broadcast
```

### Disconnect Flow (Fixed)
```
disconnect("9222:abc")
    → disconnect_target()
        → fetch.cleanup_target(target, cdp)  # NEW: cleanup before disconnect
            → remove target rules
            → unregister callback
            → Fetch.disable
        → conn_mgr.disconnect()
        → broadcast
```

### Crash Flow (Fixed)
```
WebSocket closes unexpectedly
    → CDPSession._on_close()
        → _handle_unexpected_disconnect()
            → pop from connections
            → fetch.cleanup_target(target, None)  # NEW: cleanup rules (CDP dead)
            → set_error()
            → broadcast
```

### Set Rules Flow (New)
```
fetch({"mock": {...}, "target": "9222:abc"})
    → _fetch RPC handler
        → validate target connected
        → fetch.set_rules(target, mock={...})
            → store in _target_rules[target]
            → broadcast
```

## Error Handling

| Scenario | Handling |
|----------|----------|
| `fetch({"mock": ...})` without target | RPCError: "block/mock rules require 'target' parameter" |
| `fetch({"target": "unknown"})` | RPCError: "Target 'unknown' not connected" |
| CDP dead during cleanup | Silently ignore (already disconnected) |
| Callback on dead target | Check target in connections before processing |

## Breaking Changes (Atomic Mode)

- `fetch({"capture": True})` no longer needed - capture is default on
- `fetch({})` now returns status (was: disable all)
- `fetch({"block": ...})` now requires `"target"` key
- `fetch({"mock": ...})` now requires `"target"` key
- Old global block/mock patterns no longer work
