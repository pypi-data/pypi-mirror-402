# Design: MCP Companion Cleanup

## Architecture Overview

This cleanup simplifies MCP tool exposure to complement extension usage. The extension handles connection management while MCP tools focus on querying data and performing actions.

## Component Analysis

### Files to Modify

#### 1. `src/webtap/rpc/handlers.py`
Add `targets` field to `_network()` and `_console()` responses.

**Current `_network()` return:**
```python
return {"requests": requests}
```

**New return:**
```python
return {
    "targets": _get_connected_targets(ctx),  # NEW
    "requests": requests
}
```

#### 2. `src/webtap/commands/connection.py`
Disable MCP exposure for connection management commands.

**Changes:**
- `connect()` - Add `fastmcp={"enabled": False}`
- `disconnect()` - Add `fastmcp={"enabled": False}`
- `pages()` - Add `fastmcp={"enabled": False}`
- `status()` - Add `fastmcp={"enabled": False}`
- `targets()` - Keep as MCP resource (already correct)

#### 3. `src/webtap/commands/navigation.py`
Disable MCP exposure for `page()`.

**Changes:**
- `page()` - Add `fastmcp={"enabled": False}`

#### 4. `src/webtap/commands/TIPS.md`
Update documentation to reflect MCP-available commands.

## Data Flow

### Current Flow
```
LLM → network() → RPC → {requests: [...]}
LLM → targets() → RPC → {connections: [...]}  # Separate call needed
```

### New Flow
```
LLM → network() → RPC → {targets: [...], requests: [...]}  # Context embedded
LLM → targets() → RPC → {targets: [...]}  # Still available for no-traffic case
```

## Implementation Details

### Helper Function for Targets
Add to `handlers.py`:

```python
def _get_connected_targets(ctx: RPCContext) -> list[dict]:
    """Get minimal target info for response embedding."""
    return [
        {
            "target": conn.target,
            "title": conn.page_info.get("title", ""),
            "url": conn.page_info.get("url", "")
        }
        for conn in ctx.service.conn_mgr.get_all()
    ]
```

### Response Shapes After Change

#### `network()` Response
```python
{
    "targets": [
        {"target": "9222:abc123", "title": "My Page", "url": "https://..."},
        {"target": "9222:def456", "title": "Other Page", "url": "https://..."}
    ],
    "requests": [
        {"id": 1, "method": "GET", "url": "...", "target": "9222:abc123", ...},
        ...
    ]
}
```

#### `console()` Response
```python
{
    "targets": [
        {"target": "9222:abc123", "title": "My Page", "url": "https://..."}
    ],
    "messages": [
        {"id": 1, "level": "error", "message": "...", "target": "9222:abc123", ...},
        ...
    ]
}
```

#### `targets()` Response (unchanged)
```python
{
    "targets": [
        {"target": "9222:abc123", "title": "My Page", "url": "https://...", "tracked": true}
    ]
}
```

### Disabling MCP Exposure

Use `fastmcp={"enabled": False}` pattern (already used by `ports()`):

```python
# Before
@app.command(display="markdown", fastmcp={"type": "tool"})
def connect(state, target: str = "") -> dict:

# After
@app.command(display="markdown", fastmcp={"enabled": False})
def connect(state, target: str = "") -> dict:
```

This keeps REPL/CLI functionality intact while hiding from MCP.

## Error Handling

### No Targets Connected
When `network()` or `console()` called with no connections:

```python
{
    "targets": [],  # Empty but present
    "requests": []  # or "messages": []
}
```

No error - just empty data. LLM sees `targets: []` and knows nothing is connected.

## Security Considerations

None - this is a simplification, not adding new capabilities.

## Migration Strategy

No migration needed - this is additive (new field) and subtractive (hiding from MCP).
Existing REPL usage unaffected.

## Testing Verification

1. **MCP exposure:** Verify removed commands don't appear in MCP tool list
2. **Response shape:** Verify `targets` field present in network/console responses
3. **REPL:** Verify all commands still work in REPL
4. **Empty state:** Verify responses when no targets connected
