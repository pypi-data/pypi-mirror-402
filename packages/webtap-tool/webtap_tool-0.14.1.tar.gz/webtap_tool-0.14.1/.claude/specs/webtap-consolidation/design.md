# Design: WebTap Code Consolidation

## Architecture Overview

This refactoring consolidates duplicated code into shared utilities without changing the external API. Changes are internal to the `commands/` and `services/` layers.

```
commands/
  _builders.py      ← Add rpc_call()
  _config.py        ← NEW: truncation configs
  _code_generation.py  ← Existing, add prepare_generation_data()

services/
  _utils.py         ← Add aggregate_query(), select_fields(), trigger_broadcast_mixin()
  main.py           ← Add for_each_connection()

config.py           ← NEW: centralized constants
```

## Component Design

### 1. RPC Call Helper

**File:** `src/webtap/commands/_builders.py`

```python
from webtap.rpc import RPCError

def rpc_call(state, method: str, **params) -> tuple[dict | None, dict | None]:
    """Execute RPC call with standard error handling.

    Args:
        state: Application state with client
        method: RPC method name
        **params: Method parameters

    Returns:
        Tuple of (result, error_response). One will be None.

    Example:
        result, error = rpc_call(state, "network", limit=50)
        if error:
            return error
        # use result
    """
    try:
        return state.client.call(method, **params), None
    except RPCError as e:
        return None, error_response(e.message)
    except Exception as e:
        return None, error_response(str(e))
```

**Usage in commands:**
```python
# Before (5 lines per call):
try:
    result = state.client.call("network", limit=limit)
except RPCError as e:
    return error_response(e.message)
except Exception as e:
    return error_response(str(e))

# After (2 lines per call):
result, error = rpc_call(state, "network", limit=limit)
if error:
    return error
```

### 2. Query Aggregation Utility

**File:** `src/webtap/services/_utils.py`

```python
import logging
from typing import Any

logger = logging.getLogger(__name__)

def aggregate_query(
    cdps: list[Any],
    sql: str,
    params: list | None = None,
    *,
    error_context: str = "query",
) -> list[tuple]:
    """Execute SQL query across multiple CDPSessions, aggregate results.

    Args:
        cdps: List of CDPSession instances
        sql: SQL query to execute
        params: Optional query parameters
        error_context: Context string for error logging

    Returns:
        Aggregated list of result rows from all sessions
    """
    all_rows: list[tuple] = []
    for cdp in cdps:
        try:
            rows = cdp.query(sql, params) if params else cdp.query(sql)
            all_rows.extend(rows)
        except Exception as e:
            logger.warning(f"Failed to {error_context} from {cdp.target}: {e}")
    return all_rows
```

### 3. Field Selection Utility

**File:** `src/webtap/services/_utils.py`

```python
def select_fields(
    entry: dict,
    patterns: list[str] | None,
    *,
    minimal_fields: list[str],
    case_insensitive: bool = False,
) -> dict:
    """Apply ES-style field selection to a dict entry.

    Args:
        entry: Source dictionary
        patterns: Field patterns (None for minimal, ["*"] for all)
        minimal_fields: Default fields when patterns is None
        case_insensitive: Match keys case-insensitively (for HTTP headers)

    Returns:
        Dictionary with only selected fields

    Patterns:
        - None: Returns minimal_fields only
        - ["*"]: Returns entire entry
        - ["path.to.field"]: Specific nested field
        - ["path.*"]: All fields under path
    """
    if patterns is None:
        result: dict = {}
        for pattern in minimal_fields:
            parts = pattern.split(".")
            value = get_nested(entry, parts, case_insensitive=case_insensitive)
            if value is not None:
                set_nested(result, parts, value)
        return result

    if patterns == ["*"] or "*" in patterns:
        return entry

    result = {}
    for pattern in patterns:
        if pattern == "*":
            return entry
        parts = pattern.split(".")
        if pattern.endswith(".*"):
            prefix_parts = pattern[:-2].split(".")
            obj = get_nested(entry, prefix_parts, case_insensitive=case_insensitive)
            if obj is not None:
                set_nested(result, prefix_parts, obj)
        else:
            value = get_nested(entry, parts, case_insensitive=case_insensitive)
            if value is not None:
                set_nested(result, parts, value)
    return result
```

### 4. Target Resolution Helper

**File:** `src/webtap/services/main.py`

```python
from typing import TypeVar, Callable

T = TypeVar("T")

def query_connections(
    self,
    target: str | None,
    callback: Callable[[Any], T | None],
    *,
    collect_errors: bool = False,
) -> T | list[T] | None:
    """Execute callback on target connection or all connections.

    Args:
        target: Specific target ID, or None for all
        callback: Function receiving connection, returning result or None
        collect_errors: If True, collect error strings from failed callbacks

    Returns:
        - If target specified: Single result or None
        - If target is None: List of non-None results
    """
    if target:
        conn = self.connections.get(target)
        if not conn:
            return None
        return callback(conn)

    results = []
    for conn in self.connections.values():
        try:
            result = callback(conn)
            if result is not None:
                results.append(result)
        except Exception:
            pass
    return results
```

### 5. Broadcast Trigger Utility

**File:** `src/webtap/services/_utils.py`

```python
def create_broadcast_trigger(service_ref: Any) -> Callable[[], None]:
    """Create a broadcast trigger function bound to a service.

    Args:
        service_ref: Reference to WebTapService

    Returns:
        Function that triggers broadcast when called
    """
    def trigger() -> None:
        if service_ref:
            try:
                service_ref._trigger_broadcast()
            except Exception as e:
                logger.debug(f"Failed to trigger broadcast: {e}")
    return trigger
```

### 6. Truncation Configuration

**File:** `src/webtap/commands/_config.py` (NEW)

```python
"""Shared configuration for command display formatting.

PUBLIC API:
  - REPL_TRUNCATE: Compact truncation for terminal display
  - MCP_TRUNCATE: Generous truncation for MCP/API responses
  - get_truncate_config: Helper to select based on execution context
"""

from typing import Any

# Compact display for REPL (terminal width constraints)
REPL_TRUNCATE: dict[str, dict[str, Any]] = {
    "URL": {"max": 50, "mode": "middle"},
    "url": {"max": 50, "mode": "middle"},
    "Title": {"max": 40, "mode": "end"},
    "title": {"max": 40, "mode": "end"},
    "Message": {"max": 60, "mode": "end"},
}

# Generous display for MCP (no terminal constraints)
MCP_TRUNCATE: dict[str, dict[str, Any]] = {
    "URL": {"max": 200, "mode": "middle"},
    "url": {"max": 200, "mode": "middle"},
    "Title": {"max": 100, "mode": "end"},
    "title": {"max": 100, "mode": "end"},
    "Message": {"max": 200, "mode": "end"},
}

def get_truncate_config(is_repl: bool) -> dict[str, dict[str, Any]]:
    """Get appropriate truncation config based on execution context."""
    return REPL_TRUNCATE if is_repl else MCP_TRUNCATE

__all__ = ["REPL_TRUNCATE", "MCP_TRUNCATE", "get_truncate_config"]
```

### 7. Code Generation Data Preparation

**File:** `src/webtap/commands/_code_generation.py`

Add to existing file:

```python
def prepare_generation_data(
    state,
    row_id: int,
    field: str = "response.content",
    expr: str | None = None,
    json_path: str | None = None,
) -> tuple[dict | None, dict | None]:
    """Prepare data for code generation commands (to_model, quicktype).

    Args:
        state: Application state
        row_id: HAR row ID to fetch
        field: Field to extract ("response.content" or "request.postData")
        expr: Optional Python expression to transform data
        json_path: Optional JSON path to extract (e.g., "data[0]")

    Returns:
        Tuple of (prepared_data, error_response). One will be None.
    """
    from webtap.commands._utils import evaluate_expression

    # Fetch HAR entry with body
    result, error = rpc_call(state, "request", id=row_id, fields=[field])
    if error:
        return None, error

    # Extract body content
    if field == "response.content":
        content = result.get("response", {}).get("content", {})
        body = content.get("text")
        if not body:
            return None, error_response(
                f"No response body for request {row_id}",
                suggestions=["Ensure the request has completed", "Check if body was captured"]
            )
    else:  # request.postData
        body = result.get("request", {}).get("postData")
        if not body:
            return None, error_response(f"No request body for request {row_id}")

    # Apply expression if provided
    if expr:
        try:
            data = evaluate_expression(expr, {"body": body, "data": result})
        except Exception as e:
            return None, error_response(f"Expression error: {e}")
    else:
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            return None, error_response(f"Invalid JSON: {e}")

    # Extract JSON path if provided
    if json_path:
        try:
            # Simple path extraction: data[0], data.items, etc.
            data = eval(f"data{json_path}" if not json_path.startswith("[") else f"data{json_path}")
        except Exception as e:
            return None, error_response(f"JSON path error: {e}")

    # Validate structure
    if not isinstance(data, (dict, list)):
        return None, error_response(
            "Data must be object or array for type generation",
            suggestions=["Use expr= to transform the data", "Use json_path= to select a subset"]
        )

    return data, None
```

### 8. Centralized Constants

**File:** `src/webtap/config.py` (NEW)

```python
"""Centralized configuration constants.

PUBLIC API:
  - NETWORK_BUFFER_SIZE: CDP Network domain buffer size
  - NETWORK_RESOURCE_SIZE: Per-resource buffer size
  - DOM_TIMEOUT: Timeout for interactive DOM operations
  - MAX_EVENTS: Maximum CDP events to store
  - PRUNE_BATCH_SIZE: Events to prune per batch
  - PRUNE_CHECK_INTERVAL: Events between prune checks
"""

# Network buffer sizes for CDP Network.enable
# Increases body retention from default (~100KB)
NETWORK_BUFFER_SIZE = 50_000_000  # 50MB total buffer
NETWORK_RESOURCE_SIZE = 10_000_000  # 10MB per resource

# DOM service timeouts
DOM_TIMEOUT = 15.0  # Seconds for interactive operations

# Event storage limits (FIFO eviction)
MAX_EVENTS = 50_000
PRUNE_BATCH_SIZE = 5_000
PRUNE_CHECK_INTERVAL = 1_000

__all__ = [
    "NETWORK_BUFFER_SIZE",
    "NETWORK_RESOURCE_SIZE",
    "DOM_TIMEOUT",
    "MAX_EVENTS",
    "PRUNE_BATCH_SIZE",
    "PRUNE_CHECK_INTERVAL",
]
```

## Files to Modify

### Commands Layer
| File | Changes |
|------|---------|
| `commands/_builders.py` | Add `rpc_call()` function |
| `commands/_config.py` | NEW: Truncation configs |
| `commands/_code_generation.py` | Add `prepare_generation_data()` |
| `commands/connection.py` | Use rpc_call, import truncate from _config |
| `commands/network.py` | Use rpc_call, import truncate from _config |
| `commands/console.py` | Use rpc_call, import truncate from _config |
| `commands/navigation.py` | Use rpc_call |
| `commands/fetch.py` | Use rpc_call |
| `commands/javascript.py` | Use rpc_call |
| `commands/to_model.py` | Use prepare_generation_data |
| `commands/quicktype.py` | Use prepare_generation_data |

### Services Layer
| File | Changes |
|------|---------|
| `services/_utils.py` | Add aggregate_query, select_fields |
| `services/main.py` | Add query_connections, import from config |
| `services/network.py` | Use aggregate_query, shared select_fields |
| `services/console.py` | Use aggregate_query, shared select_fields |
| `services/fetch.py` | Use query_connections |
| `services/dom.py` | Import DOM_TIMEOUT from config |

### Infrastructure Layer
| File | Changes |
|------|---------|
| `config.py` | NEW: Centralized constants |
| `cdp/session.py` | Import from config, add `__all__` |
| `cdp/har.py` | Add `__all__` |
| `api/app.py` | Add `__all__` |
| `api/sse.py` | Add `__all__` |
| `api/state.py` | Add `__all__` |

## Error Handling Strategy

No changes to error handling strategy - this refactoring centralizes the existing pattern.

## Security Considerations

No security implications - internal refactoring only.

## Migration Strategy

All changes are atomic internal refactoring:
1. Add new utilities first
2. Update consumers to use utilities
3. Remove duplicated code
4. Verify with basedpyright and ruff after each task
