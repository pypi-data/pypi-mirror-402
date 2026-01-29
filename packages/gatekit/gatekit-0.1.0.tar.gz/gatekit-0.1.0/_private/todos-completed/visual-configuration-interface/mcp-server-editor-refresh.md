# MCP Server Editor Refresh

## Summary
Add editing controls for each MCP server and relocate destructive actions so the configuration editor follows familiar master-detail patterns. The list pane keeps collection-level actions such as creating servers, while the detail pane presents per-server edits and the removal flow. Inline edits respect existing auto-save-to-memory behavior while signaling dirty state and still require the global `Save Configuration` action to write changes to disk.

## Context
- Current UI shows `+ Add` and `- Remove` buttons underneath the MCP server list regardless of selection.
- The detail pane already presents server metadata and scoped plugin tables but offers no way to edit identity fields.
- Users have to act on a server without its context visible (remove) or cannot edit its name/command at all.

## Goals
- Support editing of a server's display name and command from the detail pane.
- Clarify which actions affect the server list versus the selected server.
- Reduce the chance of accidental deletions by presenting the destructive control with rich context.

## Non-Goals
- Bulk operations on multiple servers.
- Reordering the list (can be handled later from the same toolbar once designed).
- Changing transport type selection or advanced validation logic.

## User Experience Requirements
- **List Pane Toolbar**
  - Retain an always-available `Add Server` button associated with the list pane header/footer.
  - Optional overflow menu (`⋯`) can host future list-level actions (duplicate, reorder) but is not required for the first iteration.
- **Detail Pane — Identity Section**
  - Display editable fields for `Name` and `Command` directly beneath the server heading.
  - Edits update the in-memory configuration immediately (matching checkbox behavior) and surface through the global "Save Configuration" button for persistence.
  - Reflect name edits immediately in the MCP server list so the selector stays in sync.
  - Show a dirty-state indicator (badge or status chip) near the server heading tied to the existing global dirty flag (not per-server state).
  - Show transport value (read-only) so the user understands which command field they are editing.
- **Detail Pane — Plugins**
  - Preserve existing plugin tables; ensure they expand beneath the identity section with updated layout spacing.
- **Danger Zone**
  - Move the `Remove Server` control to the bottom of the detail pane inside a visually distinct danger section.
  - Require confirmation before removal; confirmation copy must mention the server name and note that scoped plugins/config will be removed from the configuration only.

## Implementation Outline
1. **Layout Updates**
   - Adjust the left pane container (`#servers_list` & `#server_buttons_row`) so the add button sits in a toolbar; remove the existing inline remove button.
   - Introduce an identity container at the top of `#server_info` containing name & command input widgets plus the dirty indicator.
   - Append a `DangerZone` container (new CSS class) at the bottom of the server detail column with the destructive button.
2. **Widgets and State**
   - Replace static `Label` widgets for name/command with `Input` or `TextArea` components bound to the selected server state.
   - Update the underlying configuration model as edits occur, reusing the existing dirty-tracking mechanism that powers the global "Save Configuration" button.
   - Ensure rename events propagate to downstream consumers (e.g., auditing/log labeling) the same way current configuration changes do.
3. **Remove Flow**
   - Swap list-level removal for a detail-only `Remove Server…` button styled with `error` theme.
   - Show a confirmation dialog using existing modal infrastructure; include server name, command summary, and an explicit note that only the configuration entry is removed (nothing from the filesystem).
   - Upon confirmation, remove the server from the model and return focus to the list pane, selecting the next available server.
4. **Styling & Accessibility**
   - Add CSS rules for the identity form, dirty indicator, and danger section (padding, focus states, color alignment with existing palette).
   - Ensure button labels are descriptive (`Remove Server…`).
   - Maintain logical focus order: after selecting a server, tab should move from name input to command input to the remove control if focus moves that far.
5. **Validation & Messaging**
   - Basic validation: name must be non-empty and unique; enforce allowed identifier characters (letters, numbers, `-`, `_`).
   - When a name conflicts with an existing server, show the inline error as soon as the field blurs; allow re-editing to dismiss it.
   - Require command (current stdio-only transport); trim leading/trailing whitespace before validation and leave room for other transports to make the field optional later.
   - Surface validation errors inline beneath inputs using existing Textual error styling.
   - Run name validation on blur; run command validation with a debounced on-input check so feedback stays timely without flicker.
   - Clear validation errors as soon as the user resumes editing a field.
6. **Testing**
   - Update or add unit tests for the TUI controller/state layer to cover rename, command edit, validation (including duplicate-name handling), dirty indicators, and remove flows.
   - Add integration test ensuring the removal confirmation fires and removing a server updates the config model.
   - Include regression coverage that a rename updates list display and downstream observers (e.g., mock audit logger labels).

## Acceptance Criteria
- Selecting a server shows editable fields populated with current name/command.
- Inline edits update the in-memory configuration and surface through existing watchers; dirty indicator reflects unsaved global state.
- Renaming updates the MCP server list immediately while enforcing uniqueness/character rules with errors shown on blur.
- Command edits validate (current stdio transport) with debounced feedback while typing; leading/trailing whitespace is trimmed before validation.
- Rename propagates to any downstream references that consume the in-memory configuration (auditing/log labeling).
- `Add Server` button lives exclusively in the list pane; `Remove Server…` exists only within the detail pane danger section.
- Remove action requires confirmation and focuses the list afterwards without leaving the UI in an inconsistent state.
- Automated tests cover name edit, command edit, and remove confirmation flows.

## Open Questions
- None currently.
