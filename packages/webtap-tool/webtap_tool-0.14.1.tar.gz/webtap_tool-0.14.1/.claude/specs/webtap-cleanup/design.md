# Design: WebTap Code Cleanup and Consistency Improvements

## Architecture Overview

These changes improve internal code organization without affecting external APIs. The webtap architecture remains:

```
Entry Points → Commands → RPC → Services → CDP
```

All changes are internal refactoring within the services layer and command helpers.

## Component Analysis

### 1. Error Handling Standardization

**Current State:**
- Commands consistently use `except RPCError` then `except Exception` pattern
- `_builders.py:223` has `check_connection()` helper but it's underutilized
- `_builders.py:250` has `check_fetch_enabled()` helper

**Decision:** Document existing pattern as canonical rather than introducing decorators. The current explicit try/except provides clear control flow and is already consistent.

**Files to Modify:**
- `src/webtap/commands/_builders.py` - Add docstring documenting the canonical error handling pattern

**No structural changes needed** - the pattern is already consistent across all command files.

### 2. State Mutation Encapsulation

**Current State:**
DOMService directly mutates `self.service.state.browser_data` in multiple places:
- `dom.py:281-286` - Initializes and sets selections
- `dom.py:523-526` - Reads selections/prompt for snapshot
- `dom.py:545-546` - Clears selections

**New Components to Create:**
None - add methods to existing WebTapService.

**Files to Modify:**

`src/webtap/services/main.py` - Add browser_data mutation methods:
```python
def set_browser_selection(self, selection_id: str, data: dict) -> None:
    """Set a browser selection, initializing browser_data if needed."""
    if not self.state.browser_data:
        self.state.browser_data = {"selections": {}, "prompt": ""}
    if "selections" not in self.state.browser_data:
        self.state.browser_data["selections"] = {}
    self.state.browser_data["selections"][selection_id] = data
    self._trigger_broadcast()

def clear_browser_selections(self) -> None:
    """Clear all browser selections."""
    if self.state.browser_data:
        self.state.browser_data["selections"] = {}
    self._trigger_broadcast()

def get_browser_data(self) -> tuple[dict[str, Any], str]:
    """Get current browser selections and prompt.

    Returns:
        Tuple of (selections dict, prompt string)
    """
    if not self.state.browser_data:
        return {}, ""
    return (
        dict(self.state.browser_data.get("selections", {})),
        self.state.browser_data.get("prompt", "")
    )
```

`src/webtap/services/dom.py` - Replace direct mutations with service calls:
- Line 281-286: Replace with `self.service.set_browser_selection(selection_id, data)`
- Line 523-526: Replace with `selections, prompt = self.service.get_browser_data()`
- Line 545-546: Replace with `self.service.clear_browser_selections()`

### 3. Module Reorganization

**Current State:**
- `src/webtap/daemon_state.py` - DaemonState class at package root
- `src/webtap/services/state_snapshot.py` - StateSnapshot in services/

**Action:** Move file and update all imports atomically. No re-exports.

**Files to Modify:**

`src/webtap/daemon_state.py` - DELETE (move to services/)

`src/webtap/services/daemon_state.py` - CREATE (moved from package root)

**Import updates required:**
- `src/webtap/daemon.py` - Change `from webtap.daemon_state` to `from webtap.services.daemon_state`
- `src/webtap/api/server.py` - Update import if applicable
- Any other files importing DaemonState

### 4. Legacy Field Removal

**Current State:**
`StateSnapshot` has three legacy fields always set to empty strings:
- `page_id: str`
- `page_title: str`
- `page_url: str`

These are set in `main.py:150-153` with comment "Legacy fields (empty - no primary connection)".

**Files to Modify:**

`src/webtap/services/state_snapshot.py`:
- Remove `page_id`, `page_title`, `page_url` from dataclass fields
- Remove from `create_empty()` method

`src/webtap/services/main.py`:
- Remove lines 150-153 (legacy field assignments)
- Remove lines 197-199 (passing legacy fields to StateSnapshot)

**External Impact Check:**
- `daemon.py:354` - Uses `status.get('page_title')` - needs update to use connections
- `__init__.py:106-107` - Uses `page_title`, `page_url` in status display - needs update

### 5. Target Parameter Utility

**Current State:**
Identical conversion logic in:
- `network.py:86`: `if targets is None and target is not None: targets = [target] if isinstance(target, str) else target`
- `console.py:97`: Same pattern

**New Components to Create:**

`src/webtap/services/_utils.py` - Add to existing file:
```python
def normalize_targets(
    targets: list[str] | None,
    target: str | list[str] | None,
) -> list[str] | None:
    """Normalize target/targets parameters to list form.

    Handles legacy `target` parameter by converting to `targets` list.

    Args:
        targets: Primary parameter - list of target IDs
        target: Legacy parameter - single target or list

    Returns:
        Normalized list of targets, or None if both are None
    """
    if targets is None and target is not None:
        return [target] if isinstance(target, str) else target
    return targets
```

**Files to Modify:**

`src/webtap/services/network.py`:
- Add import: `from webtap.services._utils import normalize_targets`
- Line 86: Replace with `targets = normalize_targets(targets, target)`

`src/webtap/services/console.py`:
- Add import: `from webtap.services._utils import normalize_targets`
- Line 97: Replace with `targets = normalize_targets(targets, target)`

## Data Flow

No changes to data flow - these are internal refactorings.

## Error Handling Strategy

The existing pattern is documented as canonical:

```python
try:
    result = state.client.call("method", **params)
except RPCError as e:
    return error_response(e.message)
except Exception as e:
    return error_response(str(e))
```

For commands requiring connection, optionally use:
```python
if error := check_connection(state):
    return error
```

## Security Considerations

No security implications - internal refactoring only.

## Migration Strategy

All changes are atomic - no phased migration or backwards compatibility stubs.

1. Add new methods/utilities
2. Update all callsites in same commit
3. Delete old code

For `daemon_state.py`: Move file, update all imports, delete original - single atomic change.

## Testing Strategy

Verification through:
1. `basedpyright` - Type checking passes
2. `ruff check` - Linting passes
3. Manual smoke test of REPL commands
