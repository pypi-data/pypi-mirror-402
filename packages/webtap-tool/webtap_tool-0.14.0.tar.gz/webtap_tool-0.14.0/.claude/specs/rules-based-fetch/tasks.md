# Implementation Tasks: Rules-Based Fetch

**Status:** Completed (2025-12-29)
**Spec:** [requirements.md](./requirements.md) | [design.md](./design.md)

## Completed Summary

All 14 tasks have been completed. The refactor:

1. **Removed manual pause/resume workflow** - All paused requests are now auto-handled
2. **Implemented declarative rules** - `FetchRules` dataclass with `capture`, `block`, `mock`
3. **Added auto-resume callback** - `_on_request_paused()` handles all events automatically
4. **Simplified the API** - Single `fetch(rules)` command replaces 5+ commands
5. **Updated extension** - Changed from dropdown to simple capture toggle
6. **Updated documentation** - TIPS.md and docstrings reflect new API

### Key Changes

**FetchService (`src/webtap/services/fetch.py`):**
- Added `FetchRules` dataclass
- Added `_on_request_paused()` callback for automatic handling
- Added `_capture_and_continue()`, `_fulfill_with_mock()`, `_fail_request()` helpers
- Updated `enable(rules)` to accept rules dict
- Updated `disable()` to clear rules and callbacks
- Removed: `continue_request()`, `fail_request()`, `fulfill_request()`, `_wait_for_next_event()`, `get_paused_event()`, `get_paused_by_network_id()`, `store_body()`, `paused_count` property

**Commands (`src/webtap/commands/fetch.py`):**
- Rewrote to single `fetch(rules)` function
- Supports dict rules, "status" string, or empty dict to disable

**RPC (`src/webtap/rpc/handlers.py`):**
- Updated `_fetch_enable()` to accept rules
- Removed: `_fetch_resume`, `_fetch_fail`, `_fetch_fulfill`

**RPC Framework (`src/webtap/rpc/framework.py`):**
- Removed `requires_paused_request` parameter and lookup logic

**State Snapshot:**
- `StateSnapshot` now has `fetch_rules` and `capture_count` instead of `response_stage` and `paused_count`
- SSE state format updated to broadcast rules and capture count

**Extension:**
- `intercept.js` simplified to toggle capture on/off
- HTML changed from dropdown to simple toggle button

**Documentation:**
- TIPS.md updated with new fetch examples
- Removed references to `resume()`, `fail()`, `fulfill()`, `requests()`

### Verification

- [x] Type check passes (`basedpyright src/webtap`)
- [x] Lint passes (`ruff check`)
- [x] No dead code remaining
- [x] Documentation updated
