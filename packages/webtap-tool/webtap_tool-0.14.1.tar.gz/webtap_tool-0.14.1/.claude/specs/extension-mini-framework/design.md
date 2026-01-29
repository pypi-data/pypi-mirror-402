# Design: WebTap Extension Mini-Framework

## Architecture Overview

The extension currently has 6 controllers that each configure DataTable with similar patterns, leading to ~200 lines of duplication. The solution is a `lib/` layer that provides:

1. **RPC utilities** - Error codes mirrored from Python
2. **Table utilities** - Formatters, presets, detail panel abstraction
3. **General utilities** - Loading state helpers

```
extension/
├── lib/
│   ├── rpc/
│   │   └── errors.js       # ErrorCode constants, isRetryable()
│   ├── table/
│   │   ├── formatters.js   # colorBadge, httpStatus, timestamp, actionButton
│   │   ├── presets.js      # RowClass, Width, TablePreset
│   │   ├── detail-panel.js # createDetailPanel()
│   │   └── index.js        # Barrel export
│   └── utils.js            # withTableLoading, createButtonLock
├── datatable.js            # Core component (cleanup only)
├── client.js               # Import ErrorCode (no API change)
├── bind.js                 # Unchanged
└── controllers/            # Refactored to use lib/
```

## Component Design

### 1. `lib/rpc/errors.js`

Mirror Python's `ErrorCode` class for consistent error handling.

```javascript
// Matches webtap/rpc/errors.py
export const ErrorCode = {
  METHOD_NOT_FOUND: "METHOD_NOT_FOUND",
  INVALID_STATE: "INVALID_STATE",
  STALE_EPOCH: "STALE_EPOCH",
  INVALID_PARAMS: "INVALID_PARAMS",
  INTERNAL_ERROR: "INTERNAL_ERROR",
  NOT_CONNECTED: "NOT_CONNECTED",
};

export function isRetryable(code) {
  return code === ErrorCode.STALE_EPOCH;
}
```

### 2. `lib/table/formatters.js`

Reusable formatter factories that return DataTable-compatible formatters.

```javascript
// Factory for colored status badges
export function colorBadge(statusMap) {
  return (value, row) => {
    const type = statusMap[value] || statusMap.default || "muted";
    const el = document.createElement("span");
    el.className = `status-badge status-badge--${type}`;
    el.textContent = value ?? "";
    return el;
  };
}

// HTTP status codes (dynamic: 2xx=success, 3xx=warning, 4xx+=error)
export function httpStatus(value, row) {
  if (row.state === "paused") {
    return pauseBadge(row.pause_stage);
  }
  if (!value) return "-";
  const type = value >= 400 ? "error" : value >= 300 ? "warning" : "success";
  const el = document.createElement("span");
  el.className = `status-badge status-badge--${type}`;
  el.textContent = value;
  return el;
}

// Console log levels
export const consoleLevel = colorBadge({
  error: "error",
  warning: "warning",
  info: "info",
  default: "muted",
});

// Timestamp HH:MM:SS
export function timestamp(value) {
  if (!value) return "-";
  return new Date(value).toLocaleTimeString("en-US", {
    hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

// Action button column
export function actionButton({ label, onClick, disabled, className }) {
  return (value, row) => {
    const btn = document.createElement("button");
    btn.className = className || "action-btn";
    btn.textContent = typeof label === "function" ? label(row) : label;
    btn.disabled = typeof disabled === "function" ? disabled(row) : !!disabled;
    btn.onclick = (e) => { e.stopPropagation(); onClick(row, e); };
    return btn;
  };
}
```

### 3. `lib/table/presets.js`

Constants and preset configurations for consistent table setup.

```javascript
// Semantic CSS class names (replaces overloaded --tracked)
export const RowClass = {
  SELECTED: "data-table-row--selected",
  ERROR: "data-table-row--error",
  CONNECTED: "data-table-row--connected",
  ACTIVE: "data-table-row--active",
  ENABLED: "data-table-row--enabled",
};

// Column width constants
export const Width = {
  BADGE: "35px",
  STATUS: "50px",
  METHOD: "55px",
  SOURCE: "70px",
  TIME: "65px",
  AUTO: "auto",
};

// Table configuration presets
export const TablePreset = {
  // Network/Console: scrolling event log with detail panel
  eventLog: {
    selectable: true,
    autoScroll: true,
    emptyText: "No items captured",
  },
  // Pages/Targets/Filters: compact toggle lists
  compactList: {
    compact: true,
    emptyText: "No items",
  },
};

// Helper: conditional row class
export const rowClassIf = (condition, className) =>
  (row) => condition(row) ? className : "";
```

### 4. `lib/table/detail-panel.js`

Abstraction for network/console detail panels (~50 lines each, nearly identical).

```javascript
import { ui, icons } from "../lib/ui.js";

export function createDetailPanel({ elementId, fetchData, renderHeader, renderContent }) {
  const el = document.getElementById(elementId);
  let selectedId = null;

  function close() {
    selectedId = null;
    el.classList.add("hidden");
  }

  async function show(id, row) {
    // Toggle off if same ID
    if (selectedId === id) { close(); return; }

    const wasHidden = el.classList.contains("hidden");
    selectedId = id;
    el.classList.remove("hidden");

    if (wasHidden) ui.loading(el);

    try {
      const data = await fetchData(id, row);
      ui.empty(el);

      el.appendChild(ui.row("details-header flex-row", [
        ui.el("span", { text: renderHeader(data) }),
        ui.el("button", { class: "icon-btn", text: icons.close, onclick: close }),
      ]));

      renderContent(data, el);
    } catch (err) {
      ui.empty(el, `Error: ${err.message}`);
    }
  }

  return { show, close, getSelectedId: () => selectedId };
}
```

### 5. `lib/utils.js`

General utilities for async operations.

```javascript
// Wrap async operation with table loading state
export async function withTableLoading(table, message, asyncFn) {
  table.setLoading(message);
  try {
    return await asyncFn();
  } finally {
    table.clearLoading();
  }
}

// Create a button lock to prevent concurrent operations
export function createButtonLock() {
  let locked = false;
  return async function withLock(buttonId, asyncFn) {
    if (locked) return;
    const btn = document.getElementById(buttonId);
    const wasDisabled = btn?.disabled;
    if (btn) btn.disabled = true;
    locked = true;
    try {
      return await asyncFn();
    } finally {
      if (btn) btn.disabled = wasDisabled;
      locked = false;
    }
  };
}
```

## DataTable Changes

**Cleanup only** - DataTable core is solid, no API changes needed.

Remove unused exports from `datatable.js`:
```javascript
// DELETE these (never used)
const formatters = {
  dot: ...,    // 0 usages
  badge: ...,  // 0 usages
  truncate: ..., // 0 usages
};
export { DataTable, formatters }; // → export { DataTable };
```

## Controller Refactoring Pattern

### Before (network.js ~155 lines)
```javascript
function formatStatus(value, row) {
  if (row.state === "paused") { /* ... */ }
  if (!value) return "-";
  const type = value >= 400 ? "error" : /* ... */;
  const badge = document.createElement("span");
  // ...
}

export function init(c, DT, fmt, callbacks) {
  networkTable = new DataTable("#networkTable", {
    columns: [
      { key: "method", header: "Method", width: "55px" },
      { key: "status", header: "Status", width: "50px", formatter: formatStatus },
      { key: "url", header: "URL", truncate: true },
    ],
    selectable: true,
    onRowClick: (row) => showDetails(row.id, row.target),
    autoScroll: true,
    // ...
  });
}

export async function showDetails(id, target) {
  // 50 lines of show/hide/loading/error logic
}
```

### After (network.js ~80 lines)
```javascript
import { httpStatus, Width, TablePreset, createDetailPanel } from "../lib/table/index.js";

let detailPanel;

export function init(c, DataTable, callbacks) {
  client = c;
  onError = callbacks.onError;

  networkTable = new DataTable("#networkTable", {
    ...TablePreset.eventLog,
    columns: [
      { key: "method", header: "Method", width: Width.METHOD },
      { key: "status", header: "Status", width: Width.STATUS, formatter: httpStatus },
      { key: "url", header: "URL", truncate: true },
    ],
    onRowDoubleClick: (row) => detailPanel.show(row.id, row),
    getKey: (row) => row.id,
  });

  detailPanel = createDetailPanel({
    elementId: "requestDetails",
    fetchData: (id, row) => client.call("request", { id, target: row.target }),
    renderHeader: (data) => `${data.entry.request?.method} ${data.entry.response?.status}`,
    renderContent: renderRequestDetails,
  });
}

function renderRequestDetails(data, el) {
  // Domain-specific rendering (stays in controller)
}
```

## CSS Changes

Add new semantic row classes to `sidepanel.css`:

```css
/* Semantic row states (replace overloaded --tracked) */
.data-table-row--active { background: var(--row-active-bg); }
.data-table-row--enabled { background: var(--row-enabled-bg); }
```

## Import Graph

```
main.js
├── client.js ──────────────── lib/rpc/errors.js
├── datatable.js (no change)
├── bind.js (no change)
└── controllers/
    ├── network.js ─────────── lib/table/index.js
    │                          lib/utils.js
    ├── console.js ─────────── lib/table/index.js
    │                          lib/utils.js
    ├── pages.js ───────────── lib/table/index.js
    │                          lib/utils.js
    ├── targets.js ─────────── lib/table/index.js
    │                          lib/utils.js
    ├── filters.js ─────────── lib/table/index.js
    │                          lib/utils.js
    └── selections.js ──────── lib/table/index.js
```

## Migration Notes

1. All controllers switch from `onRowClick` to `onRowDoubleClick` for primary actions
2. `formatters` param removed from controller `init()` signatures (was unused in some)
3. CSS class `data-table-row--tracked` split into `--active` and `--enabled`
