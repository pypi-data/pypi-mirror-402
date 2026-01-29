# Implementation Tasks: Always-On Fetch Capture

**Status:** Completed
**Completed:** 2026-01-04
**Mode:** Atomic (breaking changes allowed)
**Spec:** [requirements.md](./requirements.md) | [design.md](./design.md)

## Task Breakdown

### Task 1: Refactor FetchService data model
**Description:** Split global/per-target state, rename FetchRules to TargetRules.

**Files:**
- `src/webtap/services/fetch.py`

**Changes:**
1. Rename `FetchRules` → `TargetRules` (remove `capture` field)
2. Add `capture_enabled: bool = True` to FetchService
3. Add `_target_rules: dict[str, TargetRules] = {}` to FetchService
4. Remove old `self.enabled` and `self.rules`

**Acceptance:**
- [ ] TargetRules has only block/mock fields
- [ ] FetchService has capture_enabled defaulting to True
- [ ] FetchService has _target_rules dict

**Dependencies:** None
**Complexity:** Low

---

### Task 2: Add FetchService lifecycle methods
**Description:** Add enable_on_target(), cleanup_target(), set_capture(), set_rules(), get_status().

**Files:**
- `src/webtap/services/fetch.py`

**Changes:**
1. Add `enable_on_target(target, cdp)` - enables Fetch.enable + registers callback
2. Add `cleanup_target(target, cdp=None)` - removes rules, unregisters callback, Fetch.disable
3. Add `set_capture(enabled)` - toggles global capture on all connections
4. Add `set_rules(target, block, mock)` - sets per-target rules
5. Add `get_status()` - returns capture state + per-target rules
6. Remove old `enable()` and `disable()` methods

**Acceptance:**
- [ ] enable_on_target enables capture on new connection
- [ ] cleanup_target removes rules and callbacks
- [ ] set_capture toggles all connections
- [ ] set_rules stores per-target
- [ ] get_status returns complete state

**Dependencies:** Task 1
**Complexity:** Medium

---

### Task 3: Update _handle_paused_request for per-target rules
**Description:** Modify callback to lookup target-specific rules.

**Files:**
- `src/webtap/services/fetch.py`

**Changes:**
1. Add `target` parameter to callback signature
2. Lookup rules from `_target_rules.get(target)`
3. Apply target-specific mock/block before global capture
4. Use `capture_enabled` instead of `self.rules.capture`

**Acceptance:**
- [ ] Callback receives target parameter
- [ ] Mock rules only apply to matching target
- [ ] Block rules only apply to matching target
- [ ] Capture uses global flag

**Dependencies:** Task 1, Task 2
**Complexity:** Low

---

### Task 4: Hook fetch into connect_to_page()
**Description:** Call fetch.enable_on_target() on new connections.

**Files:**
- `src/webtap/services/main.py`

**Changes:**
1. Replace lines 618-623 (conditional fetch enable) with:
   ```python
   self.fetch.enable_on_target(target_id, cdp)
   ```

**Acceptance:**
- [ ] New connections get Fetch.enable automatically
- [ ] Callback registered with target in closure

**Dependencies:** Task 2
**Complexity:** Low

---

### Task 5: Hook fetch into disconnect_target() and disconnect()
**Description:** Call fetch.cleanup_target() before disconnecting. Remove old fetch.disable() call.

**Files:**
- `src/webtap/services/main.py`

**Changes:**
1. `disconnect_target()`: Get CDP before disconnect, call `fetch.cleanup_target(target, cdp)`
2. `disconnect()` (all): Remove lines 665-666 (`if self.fetch.enabled: self.fetch.disable()`)
   - cleanup_target is called per-target via disconnect_target loop

**Acceptance:**
- [ ] Rules cleared on single disconnect
- [ ] Callbacks removed on single disconnect
- [ ] Old fetch.disable() removed from disconnect() all
- [ ] No orphaned state after full disconnect

**Dependencies:** Task 2
**Complexity:** Low

---

### Task 6: Hook fetch into _handle_unexpected_disconnect()
**Description:** Call fetch.cleanup_target() on crash.

**Files:**
- `src/webtap/services/main.py`

**Changes:**
1. After popping connection, call `self.fetch.cleanup_target(target, cdp=None)`
2. Pass None for cdp since it's already dead

**Acceptance:**
- [ ] Rules cleared on crash
- [ ] No errors when CDP is dead

**Dependencies:** Task 2
**Complexity:** Low

---

### Task 7: Update state snapshot and body capture callback
**Description:** Update references to old fetch properties.

**Files:**
- `src/webtap/services/main.py`

**Changes:**
1. Lines 166-168: Replace `fetch.enabled`/`fetch.rules.to_dict()` with `fetch.get_status()`
2. Line 909: Replace `self.fetch.enabled and self.fetch.rules.capture` with `self.fetch.capture_enabled`

**Acceptance:**
- [ ] State snapshot uses new get_status()
- [ ] Body capture callback uses capture_enabled
- [ ] No references to old fetch.enabled or fetch.rules

**Dependencies:** Task 2
**Complexity:** Low

---

### Task 8: Update RPC handlers
**Description:** Replace _fetch_enable/_fetch_disable with unified _fetch handler.

**Files:**
- `src/webtap/rpc/handlers.py`

**Changes:**
1. Remove `_fetch_enable` and `_fetch_disable` handlers and registrations
2. Add unified `_fetch(ctx, rules=None)` handler
3. Register as `rpc.method("fetch", ...)(_fetch)`
4. Route to set_capture/set_rules/get_status based on input
5. Require target for block/mock rules

**Acceptance:**
- [ ] Old handlers removed
- [ ] `fetch()` returns status
- [ ] `fetch({"capture": False})` disables globally
- [ ] `fetch({"block": [...], "target": "..."})` sets per-target
- [ ] Missing target for block/mock returns error

**Dependencies:** Task 2
**Complexity:** Medium

---

### Task 9: Update fetch command
**Description:** Update command wrapper to match new API.

**Files:**
- `src/webtap/commands/fetch.py`
- `src/webtap/commands/TIPS.md`

**Changes:**
1. Remove old `fetch.enable`/`fetch.disable` RPC calls
2. Use single `fetch` RPC method
3. Update docstring and examples for per-target rules
4. Update TIPS.md fetch section

**Acceptance:**
- [ ] No references to old RPC methods
- [ ] Command reflects new API
- [ ] Examples show per-target usage
- [ ] TIPS.md updated

**Dependencies:** Task 8
**Complexity:** Low

---

### Task 10: Verify and test
**Description:** Run checks and verify changes work correctly.

**Verification:**
```bash
ruff format src
ruff check src --fix
basedpyright src
```

**Manual testing:**
1. Connect to page - verify capture enabled automatically
2. Make requests - verify bodies available via request()
3. Set mock rule for target - verify only that target mocked
4. Disconnect - verify rules cleared
5. Crash tab - verify rules cleared

**Acceptance:**
- [ ] All checks pass
- [ ] Connect enables capture
- [ ] Per-target rules work
- [ ] Disconnect cleans up
- [ ] Crash cleans up

**Dependencies:** Tasks 1-8
**Complexity:** Low

---

## Task Dependencies

```
Task 1 (data model)
    │
    ▼
Task 2 (lifecycle methods)
    │
    ├──► Task 3 (callback update)
    │
    ├──► Task 4 (connect hook)
    │
    ├──► Task 5 (disconnect hooks)
    │
    ├──► Task 6 (crash hook)
    │
    ├──► Task 7 (state snapshot + body capture)
    │
    └──► Task 8 (RPC handlers)
              │
              ▼
         Task 9 (command + TIPS.md)
              │
              ▼
         Task 10 (verify)
```

## Parallel Tracks

**After Task 2 completes, these can run in parallel:**
- Track A: Task 3 (callback)
- Track B: Tasks 4, 5, 6, 7 (main.py changes)
- Track C: Task 8 → Task 9 (RPC + command)

All converge at Task 10.

## Dead Code Verification

After implementation, grep for these - should return zero results:
```bash
grep -r "fetch\.enabled" src/        # Old property
grep -r "fetch\.rules" src/          # Old property
grep -r "fetch\.enable(" src/        # Old method (not enable_on_target)
grep -r "fetch\.disable(" src/       # Old method
grep -r "fetch.enable" src/          # Old RPC method name
grep -r "fetch.disable" src/         # Old RPC method name
grep -r "_fetch_enable" src/         # Old handler
grep -r "_fetch_disable" src/        # Old handler
grep -r "FetchRules" src/            # Old class name
```

## Estimated Scope

- **Total files:** 4
- **Lines changed:** ~200-250
- **Risk:** Medium (touches connection lifecycle)
