# Implementation Tasks: WebTap Code Consolidation

**Status:** Not Started
**Spec:** [requirements.md](./requirements.md) | [design.md](./design.md)

## Task Breakdown

### Task 1: Create rpc_call helper
**Description:** Add RPC call wrapper with standard error handling to _builders.py.

**Files:**
- `src/webtap/commands/_builders.py` - Add `rpc_call()` function

**Implementation:**
```python
def rpc_call(state, method: str, **params) -> tuple[dict | None, dict | None]:
    try:
        return state.client.call(method, **params), None
    except RPCError as e:
        return None, error_response(e.message)
    except Exception as e:
        return None, error_response(str(e))
```

**Acceptance:**
- [ ] Function added with type hints and docstring
- [ ] Import RPCError at module level
- [ ] basedpyright passes
- [ ] ruff passes

**Dependencies:** None
**Complexity:** Low

---

### Task 2: Update commands to use rpc_call
**Description:** Replace duplicated try/except blocks with rpc_call in all commands.

**Files:**
- `src/webtap/commands/connection.py` - ~6 occurrences
- `src/webtap/commands/navigation.py` - ~6 occurrences
- `src/webtap/commands/network.py` - ~2 occurrences
- `src/webtap/commands/console.py` - ~2 occurrences
- `src/webtap/commands/fetch.py` - ~5 occurrences
- `src/webtap/commands/javascript.py` - ~1 occurrence
- `src/webtap/commands/filters.py` - ~2 occurrences
- `src/webtap/commands/selections.py` - ~1 occurrence

**Pattern:**
```python
# Before:
try:
    result = state.client.call("method", **params)
except RPCError as e:
    return error_response(e.message)
except Exception as e:
    return error_response(str(e))

# After:
result, error = rpc_call(state, "method", **params)
if error:
    return error
```

**Acceptance:**
- [ ] All try/except blocks for RPC calls replaced
- [ ] No duplicate error handling patterns remain
- [ ] basedpyright passes
- [ ] ruff passes

**Dependencies:** Task 1
**Complexity:** Medium (many files, mechanical changes)

---

### Task 3: Add aggregate_query utility
**Description:** Add query aggregation function to services/_utils.py.

**Files:**
- `src/webtap/services/_utils.py` - Add `aggregate_query()` function

**Acceptance:**
- [ ] Function added with type hints
- [ ] Logger configured
- [ ] basedpyright passes

**Dependencies:** None
**Complexity:** Low

---

### Task 4: Update services to use aggregate_query
**Description:** Replace duplicated aggregation loops with aggregate_query.

**Files:**
- `src/webtap/services/network.py` - `get_requests()` method (~lines 147-157)
- `src/webtap/services/console.py` - `get_recent_messages()` method (~lines 137-148)

**Acceptance:**
- [ ] NetworkService uses aggregate_query
- [ ] ConsoleService uses aggregate_query
- [ ] Inline aggregation loops removed
- [ ] basedpyright passes

**Dependencies:** Task 3
**Complexity:** Low

---

### Task 5: Extract select_fields to shared utility
**Description:** Move field selection logic to _utils.py and update both services.

**Files:**
- `src/webtap/services/_utils.py` - Add `select_fields()` function
- `src/webtap/services/network.py` - Replace NetworkService.select_fields
- `src/webtap/services/console.py` - Replace ConsoleService.select_fields

**Acceptance:**
- [ ] Shared select_fields function in _utils.py
- [ ] NetworkService delegates to shared function
- [ ] ConsoleService delegates to shared function
- [ ] Special cases (response.content, websocket.frames) remain in NetworkService
- [ ] basedpyright passes

**Dependencies:** None
**Complexity:** Medium

---

### Task 6: Add query_connections helper
**Description:** Add target resolution helper to WebTapService.

**Files:**
- `src/webtap/services/main.py` - Add `query_connections()` method

**Acceptance:**
- [ ] Method added with type hints
- [ ] Handles single target case
- [ ] Handles all-connections case
- [ ] basedpyright passes

**Dependencies:** None
**Complexity:** Low

---

### Task 7: Update services to use query_connections
**Description:** Replace duplicated target resolution patterns.

**Files:**
- `src/webtap/services/network.py` - `fetch_body()`, `fetch_websocket_frames()`, `get_har_id_by_request_id()`
- `src/webtap/services/fetch.py` - `get_paused_by_network_id()`

**Acceptance:**
- [ ] NetworkService methods use query_connections
- [ ] FetchService methods use query_connections
- [ ] Inline target branching removed
- [ ] basedpyright passes

**Dependencies:** Task 6
**Complexity:** Medium

---

### Task 8: Create truncation config module
**Description:** Create _config.py with centralized truncation settings.

**Files:**
- `src/webtap/commands/_config.py` - NEW file with REPL_TRUNCATE, MCP_TRUNCATE

**Acceptance:**
- [ ] File created with both configs
- [ ] get_truncate_config() helper added
- [ ] __all__ exports defined
- [ ] basedpyright passes

**Dependencies:** None
**Complexity:** Low

---

### Task 9: Update commands to use truncation config
**Description:** Replace inline truncation definitions with imports from _config.

**Files:**
- `src/webtap/commands/connection.py` - Remove local truncate dicts
- `src/webtap/commands/network.py` - Remove local truncate dicts
- `src/webtap/commands/console.py` - Remove local truncate dicts

**Acceptance:**
- [ ] All local truncation configs removed
- [ ] Commands import from _config
- [ ] basedpyright passes

**Dependencies:** Task 8
**Complexity:** Low

---

### Task 10: Add prepare_generation_data utility
**Description:** Add shared data preparation for code generation commands.

**Files:**
- `src/webtap/commands/_code_generation.py` - Add `prepare_generation_data()` function

**Acceptance:**
- [ ] Function handles HAR fetch, body extraction, expr evaluation, json_path
- [ ] Error responses match existing pattern
- [ ] basedpyright passes

**Dependencies:** Task 1 (uses rpc_call)
**Complexity:** Medium

---

### Task 11: Update code generation commands
**Description:** Replace duplicated data preparation with shared utility.

**Files:**
- `src/webtap/commands/to_model.py` - Use prepare_generation_data
- `src/webtap/commands/quicktype.py` - Use prepare_generation_data

**Acceptance:**
- [ ] to_model uses prepare_generation_data
- [ ] quicktype uses prepare_generation_data
- [ ] ~70 lines of duplication removed per file
- [ ] basedpyright passes

**Dependencies:** Task 10
**Complexity:** Medium

---

### Task 12: Create config.py for constants
**Description:** Create centralized config module for magic constants.

**Files:**
- `src/webtap/config.py` - NEW file with all constants

**Acceptance:**
- [ ] NETWORK_BUFFER_SIZE, NETWORK_RESOURCE_SIZE defined
- [ ] DOM_TIMEOUT defined
- [ ] MAX_EVENTS, PRUNE_BATCH_SIZE, PRUNE_CHECK_INTERVAL defined
- [ ] __all__ exports defined
- [ ] basedpyright passes

**Dependencies:** None
**Complexity:** Low

---

### Task 13: Update modules to use config constants
**Description:** Replace hardcoded constants with imports from config.

**Files:**
- `src/webtap/services/main.py` - Import network buffer sizes
- `src/webtap/services/dom.py` - Import DOM_TIMEOUT
- `src/webtap/cdp/session.py` - Import event storage constants

**Acceptance:**
- [ ] All hardcoded constants replaced
- [ ] Imports from config module
- [ ] basedpyright passes

**Dependencies:** Task 12
**Complexity:** Low

---

### Task 14: Add __all__ exports to modules
**Description:** Add explicit exports to modules missing them.

**Files:**
- `src/webtap/cdp/session.py` - Add __all__
- `src/webtap/cdp/har.py` - Add __all__
- `src/webtap/api/app.py` - Add __all__
- `src/webtap/api/sse.py` - Add __all__
- `src/webtap/api/state.py` - Add __all__

**Acceptance:**
- [ ] All 5 files have __all__ defined
- [ ] Exports match public API
- [ ] basedpyright passes

**Dependencies:** None
**Complexity:** Low

---

### Task 15: Use specific exception types (incremental)
**Description:** Replace bare `except Exception` with specific types where appropriate.

**Files:** Multiple (incremental, non-blocking)
- Focus on: daemon.py, filters.py, cdp/session.py

**Exception mapping:**
- HTTP calls → `httpx.RequestError`
- JSON parsing → `json.JSONDecodeError`
- Timeouts → `TimeoutError`
- File operations → `OSError`

**Acceptance:**
- [ ] High-impact locations updated
- [ ] No functional changes
- [ ] basedpyright passes

**Dependencies:** None
**Complexity:** Low (can be done incrementally)

---

## Task Dependencies

```
Task 1 ──► Task 2
           Task 10 ──► Task 11

Task 3 ──► Task 4

Task 5 (independent)

Task 6 ──► Task 7

Task 8 ──► Task 9

Task 12 ──► Task 13

Task 14 (independent)

Task 15 (independent)
```

## Parallel Tracks

These tracks can run independently:

**Track A:** Tasks 1, 2, 10, 11 (rpc_call + code generation)
**Track B:** Tasks 3, 4 (aggregate_query)
**Track C:** Task 5 (select_fields)
**Track D:** Tasks 6, 7 (query_connections)
**Track E:** Tasks 8, 9 (truncation config)
**Track F:** Tasks 12, 13 (constants config)
**Track G:** Task 14 (__all__ exports)
**Track H:** Task 15 (exception types)

## Verification

After all tasks complete:
```bash
cd packages/webtap
uv run basedpyright src/webtap/
uv run ruff check src/webtap/
```
