# Implementation Tasks: Extension Mini-Framework

**Status:** Complete
**Started:** 2026-01-01
**Completed:** 2026-01-01
**Spec:** [requirements.md](./requirements.md) | [design.md](./design.md)

## Task Breakdown

### Task 1: Create RPC Error Codes
**Completed:** 2026-01-01

**Files:**
- `extension/lib/rpc/errors.js` - CREATED

**Acceptance:**
- [x] ErrorCode constants match Python `webtap/rpc/errors.py`
- [x] `isRetryable(code)` helper exported

---

### Task 2: Create Table Formatters
**Completed:** 2026-01-01

**Files:**
- `extension/lib/table/formatters.js` - CREATED

**Acceptance:**
- [x] `colorBadge(statusMap)` factory works
- [x] `httpStatus(value, row)` handles paused state and status codes
- [x] `consoleLevel` badge for log levels
- [x] `timestamp(value)` formats HH:MM:SS
- [x] `actionButton({ label, onClick, disabled, className })` factory works (supports dynamic className)

---

### Task 3: Create Table Presets
**Completed:** 2026-01-01

**Files:**
- `extension/lib/table/presets.js` - CREATED

**Acceptance:**
- [x] `RowClass` has SELECTED, ERROR, CONNECTED, ACTIVE, ENABLED
- [x] `Width` has BADGE, STATUS, METHOD, LEVEL, SOURCE, TIME, AUTO
- [x] `TablePreset.eventLog` and `TablePreset.compactList` defined
- [x] `rowClassIf(condition, className)` helper works

---

### Task 4: Create Detail Panel Abstraction
**Completed:** 2026-01-01

**Files:**
- `extension/lib/table/detail-panel.js` - CREATED

**Acceptance:**
- [x] `createDetailPanel({ elementId, fetchData, renderHeader, renderContent })` works
- [x] Toggle behavior (same ID closes panel)
- [x] Loading state shown on first open
- [x] Error handling displays message
- [x] Close button works

---

### Task 5: Create Table Barrel Export
**Completed:** 2026-01-01

**Files:**
- `extension/lib/table/index.js` - CREATED

**Acceptance:**
- [x] Exports all from formatters.js
- [x] Exports all from presets.js
- [x] Exports createDetailPanel from detail-panel.js

---

### Task 6: Create General Utilities
**Completed:** 2026-01-01

**Files:**
- `extension/lib/utils.js` - CREATED

**Acceptance:**
- [x] `withTableLoading(table, message, asyncFn)` shows/hides loading
- [x] `createButtonLock()` prevents concurrent operations

---

### Task 7: Update Client to Use ErrorCode
**Completed:** 2026-01-01

**Files:**
- `extension/client.js` - MODIFIED

**Acceptance:**
- [x] Import ErrorCode from lib/rpc/errors.js
- [x] Replace hardcoded "STALE_EPOCH" with ErrorCode.STALE_EPOCH

---

### Task 8: Add CSS Semantic Classes
**Completed:** 2026-01-01

**Files:**
- `extension/sidepanel.css` - MODIFIED

**Acceptance:**
- [x] `.data-table-row--active` styled
- [x] `.data-table-row--enabled` styled

---

### Task 9: Refactor Network Controller
**Completed:** 2026-01-01

**Files:**
- `extension/controllers/network.js` - MODIFIED

**Acceptance:**
- [x] Import from lib/table/index.js
- [x] Use TablePreset.eventLog
- [x] Use httpStatus formatter
- [x] Use Width constants
- [x] Use createDetailPanel
- [x] Switch onRowClick → onRowDoubleClick
- [x] Remove inline formatStatus function

---

### Task 10: Refactor Console Controller
**Completed:** 2026-01-01

**Files:**
- `extension/controllers/console.js` - MODIFIED

**Acceptance:**
- [x] Import from lib/table/index.js
- [x] Use TablePreset.eventLog
- [x] Use consoleLevel formatter
- [x] Use timestamp formatter
- [x] Use Width constants
- [x] Use createDetailPanel
- [x] Switch onRowClick → onRowDoubleClick
- [x] Use RowClass.ERROR for error rows

---

### Task 11: Refactor Pages Controller
**Completed:** 2026-01-01

**Files:**
- `extension/controllers/pages.js` - MODIFIED

**Acceptance:**
- [x] Import from lib/table/index.js
- [x] Use TablePreset.compactList
- [x] Use RowClass.CONNECTED
- [x] Use withTableLoading for connect/disconnect
- [x] Keep onRowDoubleClick (already correct)
- [x] Remove unused formatters param from init (kept signature, passes null)

---

### Task 12: Refactor Targets Controller
**Completed:** 2026-01-01

**Files:**
- `extension/controllers/targets.js` - MODIFIED

**Acceptance:**
- [x] Import from lib/table/index.js
- [x] Use TablePreset.compactList
- [x] Use RowClass.ACTIVE (replace --tracked)
- [x] Use actionButton for DevTools and Inspect buttons
- [x] Use withTableLoading for toggle
- [x] Remove unused formatters param from init (kept signature, passes null)

---

### Task 13: Refactor Filters Controller
**Completed:** 2026-01-01

**Files:**
- `extension/controllers/filters.js` - MODIFIED

**Acceptance:**
- [x] Import from lib/table/index.js
- [x] Use TablePreset.compactList
- [x] Use RowClass.ENABLED (replace --tracked)
- [x] Use withTableLoading for toggle

---

### Task 14: Refactor Selections Controller
**Completed:** 2026-01-01

**Files:**
- `extension/controllers/selections.js` - MODIFIED

**Acceptance:**
- [x] Import from lib/table/index.js
- [x] Use TablePreset.compactList
- [x] Use Width.BADGE for badge column

---

### Task 15: Cleanup DataTable
**Completed:** 2026-01-01

**Files:**
- `extension/datatable.js` - MODIFIED

**Acceptance:**
- [x] Remove formatters object (dot, badge, truncate)
- [x] Change export to just `export { DataTable }`

---

### Task 16: Update Main.js Imports
**Completed:** 2026-01-01

**Files:**
- `extension/main.js` - MODIFIED

**Acceptance:**
- [x] Remove formatters import
- [x] Pass null for formatters param to controllers (maintaining signature compatibility)
- [x] Verify all controllers initialize correctly

---

### Task 17: Manual Testing
**Status:** Ready for testing

**Acceptance:**
- [ ] Extension loads without errors
- [ ] Network table double-click shows details
- [ ] Console table double-click shows details
- [ ] Pages table double-click connects/disconnects
- [ ] Targets table double-click toggles filter
- [ ] Filters table double-click toggles enable
- [ ] Loading overlays appear during async operations
- [ ] Row classes display correct states

---

## Summary

All implementation tasks (1-16) complete. Task 17 (manual testing) remains for user verification.

**New files created:**
- `extension/lib/rpc/errors.js`
- `extension/lib/table/formatters.js`
- `extension/lib/table/presets.js`
- `extension/lib/table/detail-panel.js`
- `extension/lib/table/index.js`
- `extension/lib/utils.js`

**Files modified:**
- `extension/client.js`
- `extension/sidepanel.css`
- `extension/datatable.js`
- `extension/main.js`
- `extension/controllers/network.js`
- `extension/controllers/console.js`
- `extension/controllers/pages.js`
- `extension/controllers/targets.js`
- `extension/controllers/filters.js`
- `extension/controllers/selections.js`
