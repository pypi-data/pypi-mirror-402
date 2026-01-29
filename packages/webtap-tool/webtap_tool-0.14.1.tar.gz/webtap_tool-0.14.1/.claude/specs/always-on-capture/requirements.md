# Feature: Always-On Fetch Capture with Per-Target Rules

## Overview

Simplify body capture by enabling it automatically on connect. Block/mock rules are per-target and cleared on crash (clean slate). No state to recreate on reconnect.

## Mental Model

```
CAPTURE (global)     RULES (per-target)
─────────────────    ──────────────────
Always on            Set per target
fetch(capture=False) fetch({..., "target": "..."})
to disable globally  Crash → rules gone
```

## User Stories

### Story 1: Automatic Body Capture
**As a** developer debugging network traffic
**I want** response bodies captured automatically when I connect
**So that** I don't have to remember to enable capture manually

**Acceptance Criteria (EARS notation):**
- WHEN `connect(target)` succeeds, THE SYSTEM SHALL enable Fetch.enable with body capture
- WHEN `network()` shows a request, THE SYSTEM SHALL have body available via `request(id, ["response.content"])`
- WHEN user calls `fetch({"capture": False})`, THE SYSTEM SHALL disable capture globally

### Story 2: Per-Target Rules
**As a** developer reverse engineering an API
**I want** block/mock rules scoped to specific targets
**So that** my test rules don't affect other tabs

**Acceptance Criteria (EARS notation):**
- WHEN `fetch({"mock": {...}, "target": "9222:abc"})` is called, THE SYSTEM SHALL apply mock rules only to that target
- WHEN `fetch({"block": [...], "target": "9222:abc"})` is called, THE SYSTEM SHALL apply block rules only to that target
- WHEN `fetch({"mock": {...}})` is called without target, THE SYSTEM SHALL return error requiring target
- WHEN `fetch()` is called with no args, THE SYSTEM SHALL show capture state and per-target rules

### Story 3: Clean Disconnect
**As a** developer with multiple tabs connected
**I want** fetch state cleaned up when I disconnect a target
**So that** the system state stays consistent

**Acceptance Criteria (EARS notation):**
- WHEN `disconnect(target)` is called, THE SYSTEM SHALL disable Fetch on that CDP session
- WHEN `disconnect(target)` is called, THE SYSTEM SHALL clear rules for that target
- WHEN `disconnect(target)` is called, THE SYSTEM SHALL remove fetch callbacks for that target

### Story 4: Crash Cleanup
**As a** developer whose Chrome tab crashed
**I want** that target's rules cleared automatically
**So that** I have a clean slate on reconnect

**Acceptance Criteria (EARS notation):**
- WHEN a CDP WebSocket closes unexpectedly, THE SYSTEM SHALL clean up fetch callbacks for that target
- WHEN a CDP WebSocket closes unexpectedly, THE SYSTEM SHALL clear rules for that target
- WHEN reconnecting after crash, THE SYSTEM SHALL only enable capture (no rules to restore)

### Story 5: Global Capture Toggle
**As a** developer experiencing overhead issues
**I want** to disable automatic capture globally
**So that** I can reduce CDP traffic if needed

**Acceptance Criteria (EARS notation):**
- WHEN `fetch({"capture": False})` is called, THE SYSTEM SHALL disable Fetch.enable on all targets
- WHEN capture is disabled and `fetch({"capture": True})` is called, THE SYSTEM SHALL re-enable capture on all targets
- WHEN capture is disabled and new target connects, THE SYSTEM SHALL NOT enable capture on new connection

## API Summary

```python
# Always enabled on connect (unless globally disabled)
connect("9222:abc")  # → capture on

# Per-target rules (target required)
fetch({"mock": {"*api*": '{"ok":1}'}, "target": "9222:abc"})
fetch({"block": ["*track*"], "target": "9222:abc"})

# Clear target rules
fetch({"target": "9222:abc"})  # → clears rules for target, keeps capture

# Global capture toggle
fetch({"capture": False})  # → disable capture globally
fetch({"capture": True})   # → re-enable capture globally

# Status
fetch()  # → shows capture state + per-target rules
```

## Non-Functional Requirements

- **Performance:** Capture overhead < 5ms per request
- **Reliability:** No orphaned callbacks after any disconnect scenario
- **Consistency:** Fetch state always matches actual CDP state

## Constraints

- Must work with existing multi-target architecture
- Block/mock rules require explicit target (no implicit "all targets")
- Capture toggle is global (simplicity over per-target control)

## Out of Scope

- Per-target capture toggle
- Rule persistence across full daemon restart
- Automatic retry on connection loss

## Assumptions

1. Capture overhead is acceptable for typical usage
2. Reverse engineering workflow: one target at a time for rules
3. Clean slate on crash is preferred over stale rules
