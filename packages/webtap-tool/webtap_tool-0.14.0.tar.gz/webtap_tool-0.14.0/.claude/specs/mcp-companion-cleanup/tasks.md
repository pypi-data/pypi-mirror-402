# Implementation Tasks: MCP Companion Cleanup

**Status:** Completed
**Spec:** [requirements.md](./requirements.md) | [design.md](./design.md)

## Task Breakdown

### Task 1: Add targets helper to RPC handlers
**Completed:** 2026-01-04

**Files:**
- `src/webtap/rpc/handlers.py` - Added `_get_connected_targets()` helper

**Acceptance:**
- [x] Helper function added
- [x] Returns list of {target, title, url} dicts

---

### Task 2: Embed targets in network() response
**Completed:** 2026-01-04

**Files:**
- `src/webtap/rpc/handlers.py` - Modified `_network()` return

**Acceptance:**
- [x] `targets` field present in network response
- [x] Works with 0, 1, and multiple connected targets

---

### Task 3: Embed targets in console() response
**Completed:** 2026-01-04

**Files:**
- `src/webtap/rpc/handlers.py` - Modified `_console()` return

**Acceptance:**
- [x] `targets` field present in console response
- [x] Works with 0, 1, and multiple connected targets

---

### Task 4: Disable MCP for connection commands
**Completed:** 2026-01-04

**Files:**
- `src/webtap/commands/connection.py`

**Acceptance:**
- [x] connect() not in MCP tools
- [x] disconnect() not in MCP tools
- [x] pages() not in MCP resources
- [x] status() not in MCP resources
- [x] targets() still in MCP resources
- [x] All commands still work in REPL

**Notes:** Also cleaned up unused `_connect_desc` and `_disconnect_desc` variables.

---

### Task 5: Disable MCP for page() command
**Completed:** 2026-01-04

**Files:**
- `src/webtap/commands/navigation.py`

**Acceptance:**
- [x] page() not in MCP resources
- [x] page() still works in REPL

---

### Task 6: Update TIPS.md documentation
**Completed:** 2026-01-04

**Files:**
- `src/webtap/commands/TIPS.md`

**Acceptance:**
- [x] Documentation reflects new response shapes
- [x] Clear guidance on MCP vs REPL commands

**Notes:** Added "REPL-Only Commands" section and "Connected Target Context" section.

---

### Task 7: Verify and test
**Completed:** 2026-01-04

**Verification results:**
```
ruff format src - 55 files left unchanged
ruff check src --fix - All checks passed!
basedpyright src - 0 errors, 0 warnings, 0 notes
```

**Acceptance:**
- [x] All checks pass
- [x] MCP exposure correct (fastmcp={"enabled": False} pattern applied)
- [x] Response shapes correct (targets field added)

---

## Task Dependencies

```
Task 1 (helper)
    ├── Task 2 (network response)
    └── Task 3 (console response)

Task 4 (connection.py) ──┐
Task 5 (navigation.py) ──┼── Task 6 (docs) ── Task 7 (verify)
Tasks 2,3 ───────────────┘
```

## Parallel Tracks

**Track A:** Tasks 1 → 2 → 3 (RPC changes)
**Track B:** Tasks 4, 5 (MCP disable) - can run in parallel with Track A

Both tracks converge at Task 6 (docs) and Task 7 (verify).

## Estimated Scope

- **Total files:** 4
- **Lines changed:** ~30-40
- **Risk:** Low (additive + hiding, no breaking changes)
