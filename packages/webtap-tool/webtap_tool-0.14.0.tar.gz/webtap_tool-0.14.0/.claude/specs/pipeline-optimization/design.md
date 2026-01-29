# Design: Pipeline Optimization

## Architecture Overview

The WebTap daemon↔extension pipeline has these data flows:

```
CDP Events → DuckDB → SSE Broadcast → Extension → RPC Fetch → DuckDB Query
```

This design optimizes two specific bottlenecks:
1. Extension makes redundant RPC calls on every state change
2. HAR queries use slow JSON extraction instead of indexed columns

## Optimization 1: Extension Event-Based RPC Gating

### Current Behavior (main.js:103-108)
```javascript
if (state.connected && tabs.getActive() === "network") {
  rpcCalls.push(network.fetch());  // Called on EVERY state change
}
```

### Proposed Change
```javascript
if (state.connected && tabs.getActive() === "network"
    && state.events?.total !== previousState?.events?.total) {
  rpcCalls.push(network.fetch());
}
```

### Files to Modify
- `extension/main.js` - Add events.total comparison (lines 103-108)

## Optimization 4: Indexed Columns for Fast Queries

### Current Schema (session.py)
```sql
CREATE TABLE events (event JSON, method VARCHAR, target VARCHAR)
CREATE INDEX idx_events_method ON events(method)
CREATE INDEX idx_events_target ON events(target)
```

### Problem
HAR queries use `json_extract_string(event, '$.params.requestId')` which scans all rows.

### New Schema
```sql
CREATE TABLE events (
    event JSON,
    method VARCHAR,
    target VARCHAR,
    request_id VARCHAR,      -- Extracted on insert
    frame_id VARCHAR,        -- For frame correlation
    timestamp DOUBLE         -- wallTime for ordering
)
CREATE INDEX idx_events_method ON events(method)
CREATE INDEX idx_events_target ON events(target)
CREATE INDEX idx_events_request_id ON events(request_id)
```

### Insert Change (session.py)
```python
def _extract_event_fields(self, method: str, data: dict) -> tuple[str | None, str | None, float | None]:
    """Extract indexable fields from CDP event."""
    params = data.get("params", {})
    request_id = params.get("requestId")
    frame_id = params.get("frameId")
    timestamp = params.get("wallTime") or params.get("timestamp")
    return request_id, frame_id, timestamp

# In event handler:
request_id, frame_id, timestamp = self._extract_event_fields(method, data)
self._db_execute(
    "INSERT INTO events (event, method, target, request_id, frame_id, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
    [json.dumps(data), method, self.target, request_id, frame_id, timestamp],
)
```

### Query Changes (har.py)

**Before:**
```sql
SELECT json_extract_string(event, '$.params.requestId') as request_id, ...
FROM events WHERE method = 'Network.requestWillBeSent'
```

**After:**
```sql
SELECT request_id, ...
FROM events WHERE method = 'Network.requestWillBeSent' AND request_id IS NOT NULL
```

All `json_extract_string(event, '$.params.requestId')` calls in har.py replaced with direct `request_id` column access.

## Files to Modify

| File | Change |
|------|--------|
| `extension/main.js` | Add `events.total` check before network/console RPC |
| `src/webtap/cdp/session.py` | Add columns, extract on insert, create indexes |
| `src/webtap/cdp/har.py` | Replace all json_extract for requestId/frameId/timestamp with columns |

## Error Handling

- **Extension**: If `previousState` is undefined, always fetch (first load)
- **Indexed columns**: NULL values valid (events without requestId)
- **Atomic refactor**: All changes deploy together, no migration needed (in-memory DB)

## Performance Impact

| Metric | Before | After |
|--------|--------|-------|
| RPC calls during page load | ~100 | ~10 |
| Network query (50k events) | 50-200ms | <5ms |
| Insert overhead | ~0.1ms | ~0.2ms (acceptable) |
