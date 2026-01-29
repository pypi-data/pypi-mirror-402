# MSP-4: Server Management and Two-Panel Layout

## Goal
Complete the MCP Servers panel with server management capabilities (add/remove servers) and polish the layout into a clean two-panel design.

## Prerequisites
- MSP-1, MSP-2, MSP-3 complete
- Plugins are fully displayed and manageable
- Need server CRUD operations and layout improvements

## What to Build
1. Simplify server list display
2. Add/Remove server functionality
3. Edit server configuration
4. Two-panel layout (merge middle and right panels)
5. Polish visual presentation

## Implementation

### Pre-Implementation Clarifications & Integration Notes

This phase depends on MSP-3 having introduced plugin action handling and override mechanisms. The migration to a two-panel layout MUST preserve all plugin management capabilities without altering semantics.

#### 1. Rationale for Two-Panel Consolidation
The legacy three-panel layout (servers | server plugins | details) caused:
- Redundant selection state (`selected_plugin`) purely to open configuration.
- Increased keyboard navigation complexity (row/col memory across two adjacent plugin-focused panels).
- Vertical space waste when either middle or right pane sparse.

The two-panel model (servers | combined details + plugins) simplifies navigation, eliminates an entire category of focus bookkeeping, and centralizes contextual actions with their descriptive context.

#### 2. Scope of This Step
Included:
- Layout consolidation.
- Server add/remove (CRUD subset).
- Rendering plugin groups with existing action buttons (from MSP-3).
- Basic server info header.

Explicitly deferred (not part of MSP-4 unless requirements expand):
- Server reorder / priority semantics.
- Bulk enable/disable actions.
- Inline editing of server attributes (only add/remove plus display).
- ~~Atomic file writing enhancement~~ (already implemented in MSP-3 - temp file + fsync + atomic rename).

#### 3. Migration Strategy From MSP-3 Rendering
Refactor approach:
1. Extract MSP-3 plugin section rendering into `_render_server_plugin_groups(container)` where `container` is `#server_plugins_display`.
2. Replace usages of `_populate_server_plugins()` that assumed a `ListView` with new group-based rendering (likely `Container` children with per-group headers).
3. Remove navigation container entries referencing `server_plugins_list` and `config_details`.
4. Purge helper logic that computes row/col focus positions for the now-removed middle panel.
5. Keep `PluginActionContext` approach (recommended in MSP-3 addendum) for action dispatch.

#### 4. Updated Navigation Model
New focusable zones after consolidation:
1. Global security widget.
2. Global auditing widget.
3. Servers list (`#servers_list`).
4. Combined details panel (first focusable plugin action or Add button).
5. Footer / button row (if retained; may be simplified).

You may remove row/col memory for server plugin rows and rely on linear focus order inside the combined panel.

#### 5. Plugin Group Rendering Guidelines
Each group section should:
```
Header line: "═══ Security Plugins ═══" + execution ordering hint.
Per plugin block:
    <execution_index_or_bullet> <checkbox glyph> <Display Name>
    ↳ <inheritance text with priority if applicable>
    [Actions Row: Configure | Disable/Enable | Reset | Remove] (only those relevant for state)
Add button after list: [+ Add Security Plugin]
```
Auditing group omits priority + execution numbering (show bullet markers instead).

#### 6. Inheritance Text Mapping (Reference)
```
inherited           => "inherited (pri: N)"
overrides           => "overrides (pri: N)"
server-only         => "server-only (pri: N)"
disabled            => "disabled (pri: N)"   # derived from override with enabled=False
overrides (disables) => Optional richer variant if both global + disabled override present
```
Keep mapping logic centralized so both MSP-3 and MSP-4 use the same function.

#### 7. Server Removal Side Effects
When removing a server ensure:
- All plugin category dicts remove that server key if present.
- Any selected plugin context referencing that server is discarded.
- UI placeholders render (“Select a server…”).

#### 8. Error Handling & Save Semantics
Reuse `_save_configuration()` from MSP-3 implementation. After add/remove success:
1. Save.
2. Rebuild plugin manager.
3. Re-render server list + combined panel.

If save fails: reload from disk and rebuild both panels.

#### 9. Helper Methods to Add / Adjust
New or changed:
- `_populate_server_details()` (already outlined) – becomes canonical; invokes `_render_server_plugin_groups()`.
- `_render_server_plugin_groups(parent_container)` – loops plugin categories using resolved + raw config to derive inheritance.
- `_clear_server_details()` – mounts placeholder state when no server selected.
- `_get_inheritance_metadata(handler, plugin_type, server)` – returns normalized structure `{status, priority, enabled}` consumed by renderer.

Remove or deprecate:
- `_populate_server_plugins()` (legacy list-based) – replace calls.

Add explicit new helper (migrated from MSP-3 refactor plan):
```python
async def _save_and_rebuild(self) -> bool:
    # Unified persistence + runtime rebuild wrapper used by add/remove server actions
```

Ensure `_persist_config()` / `_rebuild_runtime_state()` split (see MSP-3 §17) is in place before layout migration.

#### 10. Keyboard Navigation Adjustments
Arrow Up/Down inside combined panel should move between plugin action groups linearly. Left should jump back to server list; Right from server list should enter combined panel at first plugin row.

#### 11. Testing Additions for This Phase
- Add server → plugin groups still correct (inheritance preserved).
- Remove server → all overrides for that server removed from each plugin type dict.
- Disabled global plugin for removed server does not remain as dangling override.
- Layout rendering performance with large plugin counts (at least synthetic 25 plugins) remains responsive.

#### 12. Non-Goals (Document Explicitly)
#### 13. Modal Inventory (Reuse vs New)
Reuse from MSP-3:
- `AddPluginModal`, `ConfirmModal`, `MessageModal`, updated `PluginConfigModal`.

Add (server-specific, optional):
- Inline server creation and editing (no modal required).
- Server name and command editing directly in the details panel.

No new specialized error modal needed; reuse existing generic or config error modal for fatal issues.

#### 14. Async Safety Standard (Carryover)
Continue using **only button disabling** for action debouncing (no `_processing` sentinel). Pattern:
```python
if btn.disabled:
    return
btn.disabled = True
try:
    await op()
finally:
    try: btn.disabled = False
    except Exception: pass
```

#### 15. Legacy Method Decommission Plan
Sequence:
1. Introduce `_render_server_plugin_groups()` with identical data semantics (inheritance + priority) used by `_populate_server_plugins()`.
2. Validate visual parity.
3. Remove `_populate_server_plugins()` references; retain function behind feature flag or delete if test suite passes.
4. Update tests to target new renderer IDs (`plugin_row_{type}_{handler}`, etc.).

---
The two-panel redesign does not alter plugin ordering logic or priority resolution; those remain governed exclusively by `PluginManager`.

---

### Part 1: Simplify Server List

Update the server list to be cleaner and more focused:

```python
async def _populate_servers_list(self) -> None:
    """Populate the MCP servers list."""
    servers_list = self.query_one("#servers_list", ListView)
    servers_list.clear()

    # Add header with count
    server_count = len(self.config.upstreams)
    header = ListItem(
        Label(f"MCP Servers ({server_count})", classes="servers-header")
    )
    servers_list.append(header)

    # Add each server (simplified display)
    for upstream in self.config.upstreams:
        # Simple display with selection indicator
        is_selected = upstream.name == self.selected_server
        prefix = "▶ " if is_selected else "  "

        server_item = ListItem(
            Label(f"{prefix}{upstream.name}")
        )
        server_item.data_server_name = upstream.name
        servers_list.append(server_item)

    # Add management buttons at bottom
    button_container = Horizontal(
        Button("+ Add", id="add_server", variant="success"),
        Button("- Remove", id="remove_server", variant="error"),
        classes="server-buttons"
    )
    servers_list.append(ListItem(button_container))
```

### Part 2: Inline Server Creation

#### Server Name Validation Rules
When adding or editing a server, the following validation is enforced:
- **Reserved names**: `_global` is rejected (case-insensitive)
- **Pattern**: `^[A-Za-z0-9][A-Za-z0-9_-]{0,47}$`
- **No leading underscore**: Server names cannot start with `_`
- **Case-insensitive uniqueness**: Names are unique regardless of case
- **Length**: 1-48 characters maximum

Implement server addition with inline draft creation and editing:

```python
async def _handle_add_server(self) -> None:
    """Create a new draft server and switch to edit mode."""
    new_name = self._generate_new_server_name()
    new_upstream = UpstreamConfig.create_draft(name=new_name)
    
    self.config.upstreams.append(new_upstream)
    self.selected_server = new_name
    
    await self._populate_servers_list()
    await self._populate_server_details()
    
    # Focus the command input for immediate editing
            # based on transport selection
            with Container(id="stdio_fields"):  # Shown for stdio
                yield Input(placeholder="Command", id="command")
                yield Input(placeholder="Arguments (space-separated)", id="args")
            with Container(id="http_fields", styles="display: none;"):  # Hidden initially
                yield Input(placeholder="URL", id="url")
            with Horizontal():
                yield Button("Cancel", id="cancel")
                yield Button("Add", id="add", variant="primary")

    @on(Button.Pressed, "#add")
    async def handle_add(self) -> None:
        """Add the new server to configuration."""
        name = self.query_one("#server_name", Input).value.strip()
        transport = self.query_one("#transport", Select).value

        if not name:
            # Show inline error instead of modal from modal
            error_label = self.query_one("#error_label", Label)
            error_label.update("Server name is required.")
            return

        # CRITICAL: Validate server name uniqueness (using passed-in names, NOT self.app.config!)
        if name.lower() in self.existing_names:
            error_label = self.query_one("#error_label", Label)
            error_label.update(f"Server '{name}' already exists (case-insensitive).")
            return

        # Build server config
        new_server = {
            "name": name,
            "transport": transport
        }

        if transport == "stdio":
            command = self.query_one("#command", Input).value
            args = self.query_one("#args", Input).value
            if command:
                new_server["command"] = command.split() if ' ' in command else [command]
                if args:
                    new_server["args"] = args.split()
        else:  # http
            url = self.query_one("#url", Input).value
            new_server["url"] = url

```

Draft servers allow users to create incomplete server configurations that are validated before saving. The server details panel provides inline editing for all server properties including name and command.

Server name and command changes are committed automatically when the input field loses focus or when Enter is pressed. The system provides immediate feedback for validation errors.
```

### Part 3: Remove Server

Implement server removal with confirmation:

```python
async def _handle_remove_server(self) -> None:
    """Remove the selected server."""
    if not self.selected_server:
        await self.app.push_screen(MessageModal(
            "No Server Selected",
            "Please select a server to remove."
        ))
        return

    # Disable buttons during operation to prevent re-entrancy
    self.query_one("#remove_server", Button).disabled = True

    try:
        # Confirm removal
        confirm = await self.app.push_screen_wait(
            ConfirmModal(
                f"Remove server '{self.selected_server}'?",
                "This will also remove all server-specific plugin configurations."
            )
        )

        if confirm:
            # Remove from upstreams
            self.config.upstreams = [
                u for u in self.config.upstreams
                if u.name != self.selected_server
            ]

            # Remove plugin configurations (ensure all categories are cleaned)
            if self.config.plugins:
                for plugin_type in ["security", "middleware", "auditing"]:
                    # Get the plugin type dict (not a model)
                    plugin_type_dict = getattr(self.config.plugins, plugin_type, {})
                    # Only delete if it's actually a dict with this key
                    if isinstance(plugin_type_dict, dict) and self.selected_server in plugin_type_dict:
                        del plugin_type_dict[self.selected_server]

            # Auto-select next/previous server for better UX
            remaining_servers = [u.name for u in self.config.upstreams]
            if remaining_servers:
                # Try to maintain selection position
                self.selected_server = remaining_servers[min(old_index, len(remaining_servers)-1)]
            else:
                self.selected_server = None

            # Save and refresh
            await self._save_configuration()
            await self._populate_servers_list()
            await self._clear_server_details()
    finally:
        self.query_one("#remove_server", Button).disabled = False
```

### Part 4: Two-Panel Layout

Merge the middle and right panels into a comprehensive details panel:

```python
def compose(self) -> ComposeResult:
    """Compose the two-panel layout."""

    # ... header and global sections ...

    # Server management section (two panels)
    with Container(classes="server-management-section"):
        with Horizontal(classes="server-panes-container"):
            # Left pane: Simple server list
            with Vertical(classes="server-list-pane"):
                yield ListView(id="servers_list")

            # Right pane: Combined details and plugins
            with Vertical(classes="server-details-pane"):
                # Server info at top
                yield Container(id="server_info", classes="server-info")

                # Scrollable plugin sections
                with VerticalScroll(classes="server-plugins-scroll"):
                    yield Container(id="server_plugins_display")
```

### Part 5: Combined Details Display

#### Plugin Element IDs
For testability, the following ID patterns are used:
- Plugin group headers: `plugin_group_{type}` (e.g., `plugin_group_security`)
- Plugin row containers: `plugin_row_{type}_{handler}` (e.g., `plugin_row_security_pii_filter`)
- Action buttons: `plugin_action_{type}_{handler}_{action}` (e.g., `plugin_action_security_tool_manager_configure`)

Show server details and plugins in one panel:

```python
async def _populate_server_details(self) -> None:
    """Populate the combined server details panel."""
    if not self.selected_server:
        # Show placeholder
        info_container = self.query_one("#server_info", Container)
        info_container.remove_children()
        info_container.mount(Label("Select a server to view details"))
        return

    # Find upstream config
    upstream = next(
        (u for u in self.config.upstreams if u.name == self.selected_server),
        None
    )

    if not upstream:
        return

    # Update server info section
    info_container = self.query_one("#server_info", Container)
    info_container.remove_children()

    info_container.mount(Label(f"Server: {upstream.name}", classes="server-title"))
    info_container.mount(Label(f"Transport: {upstream.transport}"))

    if upstream.command:
        cmd_display = " ".join(upstream.command[:3])
        if len(upstream.command) > 3:
            cmd_display += " ..."
        info_container.mount(Label(f"Command: {cmd_display}"))

    if upstream.url:
        info_container.mount(Label(f"URL: {upstream.url}"))

    # Update plugins section (reuse from MSP-1/2/3)
    await self._populate_server_plugins_display()
```

### Part 6: Visual Polish

Add CSS for the refined layout:

```css
/* Simplified server list */
.server-list-pane {
    width: 30%;
    border-right: solid $primary;
}

.servers-header {
    font-weight: bold;
    border-bottom: solid $secondary;
}

.server-buttons {
    margin-top: 1;
    align: center middle;
}

/* Combined details panel */
.server-details-pane {
    width: 70%;
    padding: 1;
}

.server-info {
    border-bottom: solid $secondary;
    padding-bottom: 1;
    margin-bottom: 1;
}

.server-title {
    font-size: 1.2em;
    font-weight: bold;
}

.server-plugins-scroll {
    height: 1fr;
}
```

## Success Criteria
- [x] Server list shows clean, simple display with count
- [x] Can add new servers with proper configuration and validation
- [x] Can remove servers with confirmation
- [x] Plugin configs are cleaned up when server is removed
- [x] Two-panel layout with server list (left) and combined details (right)
- [x] Server details and all plugins shown in single scrollable area
- [x] Selection indicator (▶) shows current server
- [x] Add/Remove buttons at bottom of server list
- [x] Auto-selection of next/previous server on removal for better UX
- [x] Inline server creation with draft upstream support
- [x] Centralized inheritance formatting helpers
- [x] Consistent plugin element IDs for testing

## Testing
1. Add a new stdio server and verify it appears
2. Add an http server with URL
3. Remove a server and confirm plugin configs are cleaned
4. Test with many servers to verify scrolling works
5. Verify selection indicator updates correctly
6. Test empty state (no servers)

## Visual Example
```
┌─ MCP Servers (3) ─────┐ ┌─ Server: filesystem ────────┐
│ ▶ filesystem          │ │ Transport: stdio            │
│   github              │ │ Command: npx @mcp/fs ...    │
│   sqlite              │ │                             │
│                       │ │ ═══ Security Plugins ═══    │
│                       │ │     (execution order)       │
│                       │ │ 1. ☑ PII Filter             │
│                       │ │    ↳ inherited (pri: 50)   │
│                       │ │ 2. ☑ Tool Allowlist         │
│                       │ │    ↳ server-only (pri: 90) │
│                       │ │ [+ Add Security Plugin]     │
│                       │ │                             │
│                       │ │ ═══ Auditing Plugins ═══    │
│                       │ │     (runs in listed order)  │
│ [+ Add] [- Remove]    │ │ • ☑ JSON Lines              │
└───────────────────────┘ └─────────────────────────────┘
```

## Files to Modify
- `gatekit/tui/screens/config_editor.py` - Update layout and add server management
- May need to adjust CSS classes for new layout

## Next Steps
This completes the MCP Servers panel implementation. The feature is now fully functional with:
- Complete plugin visibility (MSP-1)
- Inheritance and ordering display (MSP-2)
- Plugin management actions (MSP-3)
- Server management and polished layout (MSP-4)

### Addendum: Forward Compatibility Considerations
To keep future enhancements (e.g., inline server editing, bulk operations) low-risk:
- Keep rendering functions pure (data in → Textual nodes out) so they can be unit tested with mock containers.
- Centralize inheritance + priority formatting in one helper.
- Isolate plugin action button creation so additional actions (e.g., “Test”, “Duplicate Config”) can be appended easily.
- Reserve class names / IDs with predictable prefixes (`plugin_row_{plugin_type}_{handler}`) for test automation.

No further structural changes are required before extending functionality in subsequent milestones.