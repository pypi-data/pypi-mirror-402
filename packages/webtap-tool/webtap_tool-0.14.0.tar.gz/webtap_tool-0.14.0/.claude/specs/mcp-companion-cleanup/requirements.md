# Feature: MCP Companion Cleanup

## Overview

Simplify MCP tool exposure to complement extension usage rather than duplicate it. The extension handles connection management (connect/disconnect/pages), while MCP tools help LLMs query and act on data. Response shapes should embed target context so LLMs always know what's connected.

## Context

Current workflow:
- User manages connections via Chrome extension (connect, disconnect, browse pages)
- LLM uses MCP tools to query data and perform actions
- Problem: LLM doesn't know what targets are connected without calling separate commands

## User Stories

### Story 1: LLM Queries Network Data
**As a** developer using LLM via MCP
**I want** network() responses to include connected targets
**So that** I know the context without calling a separate command

**Acceptance Criteria (EARS notation):**
- WHEN `network()` is called, THE RESPONSE SHALL include a `targets` field listing all connected target IDs
- WHEN `network(target="9222:abc")` is called, THE RESPONSE SHALL include the filtered target in the response
- WHEN no targets are connected, THE RESPONSE SHALL return an error with clear message

### Story 2: LLM Queries Console Data
**As a** developer using LLM via MCP
**I want** console() responses to include connected targets
**So that** I know which target the logs came from

**Acceptance Criteria (EARS notation):**
- WHEN `console()` is called, THE RESPONSE SHALL include a `targets` field listing all connected target IDs
- WHEN `console(target="9222:abc")` is called, THE RESPONSE SHALL include the filtered target in the response
- WHEN no targets are connected, THE RESPONSE SHALL return an error with clear message

### Story 3: LLM Checks Connected Targets
**As a** developer using LLM via MCP
**I want** a lightweight `targets()` resource
**So that** I can check what's connected when there's no traffic yet

**Acceptance Criteria (EARS notation):**
- WHEN `targets()` is called, THE RESPONSE SHALL list connected targets with their titles and URLs
- WHEN no targets are connected, THE RESPONSE SHALL return an empty list (not an error)

### Story 4: Extension Manages Connections
**As a** developer using the extension
**I want** connection management commands removed from MCP
**So that** MCP tools focus on querying/acting, not duplicating extension UI

**Acceptance Criteria (EARS notation):**
- WHEN reviewing MCP tools, `connect()` SHALL NOT be exposed as MCP tool
- WHEN reviewing MCP tools, `disconnect()` SHALL NOT be exposed as MCP tool
- WHEN reviewing MCP tools, `pages()` SHALL NOT be exposed as MCP resource
- WHEN reviewing MCP tools, `page()` SHALL NOT be exposed as MCP resource
- WHEN reviewing MCP tools, `status()` SHALL NOT be exposed as MCP resource
- THESE commands SHALL remain available in REPL for manual/CLI usage

## Current State (from exploration)

**Already present:**
- `network()` responses include `target` field in each request item
- `console()` responses include `target` field in each message item
- `status()` has `connections` array with full target details

**Missing:**
- Top-level `targets` array in `network()` / `console()` responses showing all connected targets
- This is needed when there's traffic (so LLM sees context) AND when there's no traffic (so LLM knows what's connected)

## Non-Functional Requirements

- **Backward Compatibility (REPL):** All commands remain available in REPL/CLI
- **Response Size:** Target info should be minimal (ID, title, URL only)
- **Performance:** No additional RPC calls to embed target info (use existing connection manager state)

## Constraints

- Must work with existing extension SSE state broadcasts
- Must not break REPL usage of removed MCP commands
- Row IDs (`request()`, `entry()`, etc.) remain unique across targets

## Out of Scope

- Changes to extension UI
- Changes to SSE broadcast format
- New connection management features
- Changes to `js()`, `navigate()`, etc. (already require explicit target)

## Assumptions

1. Extension is the primary way users manage connections
2. LLMs use MCP as a companion, not as primary control
3. `targets()` is sufficient for "what's connected" - no need for `status()` complexity
4. Commands requiring explicit target (`js`, `navigate`, etc.) are fine as-is

## Commands After Cleanup

### MCP Tools (Actions)
| Command | Purpose |
|---------|---------|
| `js()` | Execute JavaScript (requires target) |
| `navigate()` | Go to URL (requires target) |
| `reload()` | Refresh page (requires target) |
| `back()` / `forward()` | History navigation (requires target) |
| `fetch()` | Control body capture |
| `filters()` | Manage noise filters |
| `clear()` | Reset stored data |
| `to_model()` | Generate Pydantic models |
| `quicktype()` | Generate TypeScript/etc types |

### MCP Resources (Data)
| Command | Purpose | Includes Targets |
|---------|---------|------------------|
| `network()` | Query requests | Yes (embedded) |
| `console()` | Query logs | Yes (embedded) |
| `targets()` | List connected targets | N/A (is the list) |
| `request()` | Get request details | No (row ID sufficient) |
| `entry()` | Get console entry | No (row ID sufficient) |
| `selections()` | Element data | No |

### REPL Only (Removed from MCP)
| Command | Reason |
|---------|--------|
| `connect()` | Extension handles |
| `disconnect()` | Extension handles |
| `pages()` | Extension handles |
| `page()` | Extension handles |
| `status()` | Replaced by embedded targets + `targets()` |
| `ports()` | Already REPL-only |
