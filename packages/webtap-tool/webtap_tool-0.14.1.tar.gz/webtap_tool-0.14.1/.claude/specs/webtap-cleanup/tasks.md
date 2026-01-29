# Implementation Tasks: WebTap Code Cleanup

**Status:** Completed (2025-12-28)
**Spec:** [requirements.md](./requirements.md) | [design.md](./design.md)

**Note:** Tasks 1-2 (normalize_targets) were skipped as per user decision - this was identified as a breaking change.

## Task Breakdown

### Task 1: Add normalize_targets utility

**Description:** Add target parameter normalization to shared utilities.

**Files:**
- `src/webtap/services/_utils.py` - Add `normalize_targets()` function

**Implementation:**
```python
def normalize_targets(
    targets: list[str] | None,
    target: str | list[str] | None,
) -> list[str] | None:
    """Normalize target/targets parameters to list form."""
    if targets is None and target is not None:
        return [target] if isinstance(target, str) else target
    return targets
```

**Acceptance:**
- [ ] Function added with type hints
- [ ] basedpyright passes
- [ ] ruff passes

**Dependencies:** None
**Complexity:** Low

---

### Task 2: Update services to use normalize_targets

**Description:** Replace inline target normalization with shared utility.

**Files:**
- `src/webtap/services/network.py` - Line ~86: Use `normalize_targets()`
- `src/webtap/services/console.py` - Line ~97: Use `normalize_targets()`

**Acceptance:**
- [ ] NetworkService uses normalize_targets
- [ ] ConsoleService uses normalize_targets
- [ ] Inline conversion logic removed
- [ ] basedpyright passes

**Dependencies:** Task 1
**Complexity:** Low

---

### Task 3: Add browser_data mutation methods to WebTapService

**Description:** Add centralized methods for browser_data state changes.

**Files:**
- `src/webtap/services/main.py` - Add three methods:
  - `set_browser_selection(selection_id: str, data: dict)`
  - `clear_browser_selections()`
  - `get_browser_data() -> tuple[dict, str]`

**Acceptance:**
- [ ] Methods added with proper type hints
- [ ] Methods trigger `_trigger_broadcast()` where appropriate
- [ ] basedpyright passes

**Dependencies:** None
**Complexity:** Low

---

### Task 4: Update DOMService to use WebTapService methods

**Description:** Replace direct browser_data mutations with service method calls.

**Files:**
- `src/webtap/services/dom.py`:
  - Line ~281-286: Replace with `self.service.set_browser_selection()`
  - Line ~523-526: Replace with `self.service.get_browser_data()`
  - Line ~545-546: Replace with `self.service.clear_browser_selections()`

**Acceptance:**
- [ ] No direct `self.service.state.browser_data` mutations remain
- [ ] All mutations go through WebTapService
- [ ] basedpyright passes

**Dependencies:** Task 3
**Complexity:** Medium

---

### Task 5: Move daemon_state.py to services/

**Description:** Relocate DaemonState to services directory and update imports.

**Files:**
- `src/webtap/daemon_state.py` - DELETE
- `src/webtap/services/daemon_state.py` - CREATE (move content)
- `src/webtap/api/server.py` - Update import to `from webtap.services.daemon_state`

**Acceptance:**
- [ ] File moved to services/
- [ ] Original file deleted
- [ ] All imports updated
- [ ] basedpyright passes

**Dependencies:** None
**Complexity:** Low

---

### Task 6: Remove legacy StateSnapshot fields

**Description:** Remove unused page_id, page_title, page_url fields.

**Files:**
- `src/webtap/services/state_snapshot.py`:
  - Remove `page_id`, `page_title`, `page_url` fields
  - Update `create_empty()` method
- `src/webtap/services/main.py`:
  - Remove legacy field assignments (~lines 150-153)
  - Remove from StateSnapshot constructor call (~lines 197-199)

**Acceptance:**
- [ ] Legacy fields removed from StateSnapshot
- [ ] main.py no longer sets legacy fields
- [ ] basedpyright passes

**Dependencies:** None
**Complexity:** Low

---

### Task 7: Update status displays to use connections

**Description:** Update CLI status output to derive title/URL from connections tuple.

**Files:**
- `src/webtap/__init__.py` - Lines 106-107: Get title/URL from first connection
- `src/webtap/daemon.py` - Line 354: Get title from first connection

**Implementation pattern:**
```python
connections = status.get("connections", [])
if connections:
    first = connections[0]
    title = first.get("title", "Unknown")
    url = first.get("url", "Unknown")
```

**Acceptance:**
- [ ] Status displays work without page_title/page_url
- [ ] Multi-target display unchanged
- [ ] basedpyright passes

**Dependencies:** Task 6
**Complexity:** Low

---

### Task 8: Document error handling pattern

**Description:** Add documentation for canonical error handling pattern in commands.

**Files:**
- `src/webtap/commands/_builders.py` - Add module-level docstring section

**Content:**
```python
"""
Error Handling Pattern
---------------------
Commands should use this pattern for RPC calls:

    try:
        result = state.client.call("method", **params)
    except RPCError as e:
        return error_response(e.message)
    except Exception as e:
        return error_response(str(e))

For commands requiring connection, optionally use:
    if error := check_connection(state):
        return error
"""
```

**Acceptance:**
- [ ] Pattern documented
- [ ] Existing helpers documented

**Dependencies:** None
**Complexity:** Low

---

## Task Dependencies

```
Task 1 ──► Task 2
Task 3 ──► Task 4
Task 6 ──► Task 7
Task 5 (independent)
Task 8 (independent)
```

## Parallel Tracks

**Track A:** Tasks 1, 2 (target normalization)
**Track B:** Tasks 3, 4 (state mutations)
**Track C:** Task 5 (module move)
**Track D:** Tasks 6, 7 (legacy field removal)
**Track E:** Task 8 (documentation)

All tracks can run in parallel. Within each track, tasks are sequential.

## Verification

After all tasks complete:
```bash
cd packages/webtap
uv run basedpyright src/webtap/
uv run ruff check src/webtap/
```
