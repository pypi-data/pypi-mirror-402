# Implementation Tasks: Pipeline Optimization

**Status:** Partially Complete (Scope Reduced)
**Spec:** [requirements.md](./requirements.md) | [design.md](./design.md)

## Summary

Original spec proposed 3 indexed columns (`request_id`, `frame_id`, `timestamp`).
After implementation, `timestamp` and `frame_id` were **reverted** due to:
- `timestamp` mixed wallTime (epoch) with monotonic timestamps, causing type errors in duration calculations
- `frame_id` wasn't used anywhere

**What was kept:**
- `request_id` indexed column - provides real value for GROUP BY
- Extension RPC gating - reduces redundant fetches

---

## Task 1: Add Indexed Column for request_id ✅

**File:** `src/webtap/cdp/session.py`

**Implemented:**
```sql
CREATE TABLE IF NOT EXISTS events (
    event JSON,
    method VARCHAR,
    target VARCHAR,
    request_id VARCHAR
)
CREATE INDEX IF NOT EXISTS idx_events_request_id ON events(request_id)
```

**Reverted:** `frame_id` and `timestamp` columns (over-engineering)

---

## Task 2: Extract request_id on Insert ✅

**File:** `src/webtap/cdp/session.py`

**Implemented:**
```python
def _extract_request_id(self, data: dict) -> str | None:
    return data.get("params", {}).get("requestId")

# INSERT uses request_id column only
```

**Reverted:** `frame_id` and `timestamp` extraction

---

## Task 3: Update har.py Queries (Partial) ✅

**File:** `src/webtap/cdp/har.py`

**Implemented:** Uses `request_id` column for GROUP BY (faster aggregation)

**Reverted:** All `timestamp` column replacements - kept `json_extract_string` for:
- `$.params.wallTime` (display)
- `$.params.timestamp` (duration calculations)

This was necessary because wallTime and timestamp serve different purposes and mixing them caused calculation errors.

---

## Task 4: Update session.py Query ✅

**File:** `src/webtap/cdp/session.py`

**Implemented:** `AND request_id = ?` in fetch_body query

---

## Task 5: Update network.py Queries (Partial) ✅

**File:** `src/webtap/services/network.py`

**Implemented:**
- `AND request_id = ?` for WebSocket frames and redirects

**Reverted:**
- `timestamp` column usage - kept `json_extract_string(event, '$.params.timestamp')`

**Fixed:** Sort fallback `or ""` → `or 0` to avoid float/string comparison error

---

## Task 6: Console.py ❌ Reverted

**File:** `src/webtap/services/console.py`

**Reverted:** Kept original `json_extract_string` for timestamp (no indexed column)

---

## Task 7: Extension RPC Gating ✅

**File:** `extension/main.js`

**Implemented:** Network/console fetch only when `events.total` changes

---

## Lessons Learned

1. **Premature optimization:** Adding `timestamp` column without measuring actual performance impact
2. **Type confusion:** Single column for two different timestamp types (epoch vs monotonic)
3. **Scope creep:** `frame_id` column was never used

**Actual impact:**
- `request_id` index helps GROUP BY performance in har.py
- RPC gating reduces redundant fetches during page load
- Simpler than original spec, fewer bugs
