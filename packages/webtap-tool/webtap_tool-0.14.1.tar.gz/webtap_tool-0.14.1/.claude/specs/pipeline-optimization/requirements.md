# Feature: WebTap Pipeline Optimization

## Overview

Optimize the daemon↔extension communication pipeline to eliminate redundant work, reduce RPC calls, and improve query performance. These are "quick wins" - high impact optimizations with low implementation effort.

## User Stories

### Story 1: Responsive Extension UI
**As a** developer using the WebTap extension
**I want** the network/console tables to update instantly when new events arrive
**So that** I can monitor traffic without UI lag or freezing

**Acceptance Criteria (EARS notation):**
- WHEN a new network event arrives, THE SYSTEM SHALL update the table within 100ms
- WHEN switching to the network tab, THE SYSTEM SHALL display data within 200ms
- WHEN 1000+ events exist, THE SYSTEM SHALL maintain <200ms query time

### Story 2: Efficient Resource Usage
**As a** developer running WebTap alongside other tools
**I want** WebTap to use minimal CPU/memory during monitoring
**So that** it doesn't slow down my development environment

**Acceptance Criteria (EARS notation):**
- WHEN monitoring an active page, THE SYSTEM SHALL use <5% CPU on average
- WHEN state hasn't changed, THE SYSTEM SHALL NOT make redundant RPC calls
- WHEN coalescing broadcasts, THE SYSTEM SHALL create only ONE snapshot per coalesce window

### Story 3: Fast Event Queries
**As a** developer inspecting network requests
**I want** queries to return quickly even with large event sets
**So that** I can efficiently debug network issues

**Acceptance Criteria (EARS notation):**
- WHEN querying network events, THE SYSTEM SHALL use indexed lookups instead of JSON extraction
- WHEN 50,000 events exist, THE SYSTEM SHALL return filtered results within 50ms

## Non-Functional Requirements

- **Performance**:
  - Network RPC latency: <50ms (current: 50-200ms)
  - SSE broadcast processing: <10ms (current: 10-50ms)
  - Extension re-render: <100ms for 500 rows
- **Resource Usage**:
  - Reduce RPC calls by 90% during active monitoring
  - Eliminate redundant snapshot creation (5-10x reduction)

## Constraints

- Must maintain backward compatibility with existing extension code
- No changes to RPC API signatures
- DuckDB schema changes must be additive (no breaking migrations)

## Out of Scope

- Virtual scrolling for DataTable (Priority 2)
- HAR view materialization (Priority 2)
- Body capture deduplication (Priority 2)
- SSE payload compression (Priority 2)

## Assumptions

- Extension state listener receives previousState for comparison
- DuckDB supports adding columns to existing tables
- Event count is a reliable indicator of data changes
- Selection changes are less frequent than network events

## Priority 1 Optimizations

| # | Issue | Fix | Expected Savings |
|---|-------|-----|------------------|
| 5 | Extension fetches network/console on EVERY state change | Check `events.total` changed before RPC | 90% fewer RPCs |
| 2 | Snapshot created even when coalescing | Move `is_set()` check inside lock | 5-10x less work |
| 10 | No indexes on events JSON fields | Add `request_id`, `status` columns | 50-200ms → <5ms |
| 3 | Deepcopy selections every broadcast | Hash values, skip if unchanged | 10-50ms saved |
