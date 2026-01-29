# MSP-3: Plugin Management Actions

## Goal
Enable users to manage plugin configurations through actions: Configure, Override, Disable/Enable, Add, and Remove.

## Prerequisites
- MSP-1 complete (showing all plugins)
- MSP-2 complete (showing inheritance and order)
- Plugins are displayed with context but not yet actionable

## What to Build
1. Configure/Override actions for existing plugins
2. Disable/Enable functionality via `enabled: false` overrides
3. Add Plugin dialog (properly filtered)
4. Remove/Reset for server-specific configurations
5. Post-save refresh to keep UI in sync

## Implementation

### Updated Clarifications & Design Decisions (Prereq for implementation)

This section consolidates the open questions, required helper methods, and design guidance discovered during deeper codebase review so the implementing agent has a single authoritative reference. It intentionally avoids any temporal language.

#### 1. Plugin Configuration Storage Model
Outer wrapper (in YAML / Pydantic schema: `PluginConfigSchema`):
```
handler: str
enabled: bool (authoritative outer flag)
priority: int (0–100; security & middleware ordering)
config: Dict[str, Any]  # plugin-specific inner configuration
```
Some plugin JSON Schemas (e.g. prompt injection) also define `enabled` and `priority` inside the inner schema. For now: treat the OUTER wrapper values as authoritative for enablement and ordering. If a plugin schema returns inner `enabled`/`priority`, they may be mirrored but must not silently override the outer values. (Future cleanup: remove those fields from inner schemas or enforce a sync layer.)

#### 2. Validation Pipeline
Already present:
- JSON Schema validation via `SchemaValidator` (per-handler) inside `PluginConfigModal`.
- Pydantic-level validation occurs when full config is reloaded via `ConfigLoader`.

Recommended save flow for MSP-3:
1. User edits in modal → JSON Schema validation (already done).
2. On success, integrate returned dict as `config` for the plugin while preserving outer wrapper fields (`enabled`, `priority`).
3. (Optional hardening) Instantiate plugin class with candidate config inside a try/except; if instantiation fails, surface error and keep previous config.

#### 3. Action Button Placement (MSP-3 vs. MSP-4)
During MSP-3 we still operate in the existing three-panel layout. Buttons can either:
- A) Appear inline with each plugin entry in the server plugins list, OR
- B) Appear in the right-side details pane when a plugin is selected.

Given pending consolidation to a two-panel layout in MSP-4, choose option **B** to reduce churn: centralize action rendering in the details area. MSP-4 will then collapse middle/right panels, and the same rendering logic can migrate intact.

#### 4. Required Helper Methods (Not Yet Implemented)
The MSP-3 snippets reference methods that do not currently exist in `config_editor.py` and must be added:
- `_get_global_plugin_config(handler_name, plugin_type)` – returns the inner `config` dict from the global wrapper if present, else `{}`.
- `_get_server_plugin_config(handler_name, plugin_type)` – returns server override inner config or `{}`.
- `_create_server_override(handler_name, plugin_type, base_config)` – creates a new server-level `PluginConfigSchema` (clone global then allow editing) and appends to server list, handling duplicate override replacement.
- `_save_plugin_config(handler_name, plugin_type, new_inner_config)` – updates existing wrapper (global or server-specific) preserving outer fields; for inherited/global path this should create an override first.
- `_handle_plugin_reset(handler_name, plugin_type)` – remove server-specific override so global inheritance resumes.
- `_handle_plugin_remove(handler_name, plugin_type)` – remove a server-only plugin entirely.
- `_add_plugin_to_server(handler_name, plugin_type, inner_config)` – create wrapper with default `enabled=True` & default priority (50 unless plugin supplies recommended).
- `_load_config_from_disk()` – thin wrapper around `ConfigLoader().load_from_file()` returning a fresh `ProxyConfig`.
- `_refresh_plugin_display()` – (see Part 5) rebuild plugin manager and re-render server plugin details. (Rename or adapt once MSP-4 merges panels.)

#### 5. Button Metadata / Context Passing
Avoid scattering multiple `data_*` attributes. Introduce a tiny dataclass instead:
```python
from dataclasses import dataclass

@dataclass
class PluginActionContext:
    handler: str
    plugin_type: str  # 'security' | 'middleware' | 'auditing'
    inheritance: str  # 'inherited' | 'overrides' | 'server-only' | 'disabled'
    enabled: bool
    server: str
```
Attach to each action button as `button.data_ctx = PluginActionContext(...)`. The dispatcher then reads `ctx = event.button.data_ctx` instead of several separate attributes.

If you still prefer explicit attributes for consistency with existing code, you must set **all** of: `data_handler`, `data_plugin_type`, `data_inheritance`, and optionally `data_enabled`.

#### 6. Inheritance Status Canonicalization
Normalize inheritance states for UI branching logic:
```
inherited        # global plugin applied to server (no override present)
overrides        # server-specific override exists (enabled or disabled state independent)
server-only      # plugin exists only in server section
disabled         # server override whose sole purpose is disabling a global plugin (enabled=False)
```
Implementation detail: detection uses raw config dictionaries, not the resolved list from `PluginManager` (resolved list loses information about disabled overrides).

#### 7. Disable vs Enable Flow (Global Plugin)
Disable: append server-specific wrapper with `enabled=False` (and optionally copy priority for consistent ordering display). Enable: remove that wrapper entry only if it matches handler **and** `enabled is False`.

#### 8. Debouncing & Async Safety
Standardize on **button disabling only** (drop the `_processing` sentinel used in earlier snippets). Pattern:
```python
if button.disabled:
    return  # Fast re-entry guard
button.disabled = True
try:
    await do_async()
finally:
    try:
        button.disabled = False  # Button may have been replaced during refresh
    except Exception:
        pass
```
Do not reintroduce `_processing` unless future concurrent event races are demonstrated.

#### 9. Atomic Save & Error Recovery
Current plan: use non-atomic save (existing loader) + error modal fallback. If save fails:
1. Show modal / notification.
2. Reload from disk to discard in-memory drift.
3. Re-render.

Future enhancement (not implemented here): write to `config.yaml.tmp`, fsync, atomic rename.

#### 10. Add Plugin Filtering Rules (Authoritative)
When computing available plugins:
1. Gather **configured handlers** from `_global` and current server key (even if disabled).
2. Exclude any handler already configured globally or for the server (prevents duplicates and re-adding disabled ones; user must re-enable instead).
3. Enforce scope rules:
   - In `_global` scope (if ever exposed) forbid `server_aware` and `server_specific`.
   - For `server_specific`, enforce `COMPATIBLE_SERVERS` if declared.
4. Only after filtering present the list. Empty set ⇒ informational modal.

#### 11. Enabled/Priority Duplication Issue
Do **not** overwrite outer `priority` or `enabled` based on inner form values if the plugin schema exposes them. Either:
- Strip those keys before passing config to modal, OR
- After form submit, remove `enabled` / `priority` from returned dict prior to saving.

#### 12. Priority Display for Disabled Plugins
If a disabled server override copies the global priority, display that priority (dimmed execution index if showing order). If not stored, fallback to global plugin priority.

#### 13. Edge Cases to Handle Explicitly
- Handler missing (plugin removed from code): still show row with warning and allow Remove.
- Duplicate server override (user created override then tries again): replace existing rather than append.
- Simultaneous disable + override attempt: if user chooses override path, ensure resulting override has `enabled=True` unless explicitly changed.
- Auditing plugins: ignore priority entirely; never display priority text.

#### 14. Testing Checklist Augmentation
Add these tests beyond existing criteria:
- Re-enable after disable restores prior inherited config (no stale override remains).
- Adding a plugin when a disabled override exists is prevented by filtering.
- Reset on a server-only plugin is disallowed (should offer Remove instead of Reset).
- Global plugin missing handler: disable / enable / reset actions guarded (disable should not appear; enable should not appear if no override).

---
#### 15. Modal Inventory (Current vs Required)
Existing:
- `PluginConfigModal` (rich schema form) – extend with read-only + override action.
- `ConfigErrorModal` – keep for full-config validation errors.

To create for MSP-3:
- `AddPluginModal` – selection + optional inline description, returns `(handler_name, inner_config_dict)`.
- `MessageModal` – simple informational (title, body, OK).
- `ConfirmModal` – yes/no confirmation returning boolean.
- Optional lightweight generic `ErrorModal` for save failures; or repurpose `MessageModal` with severity styling.

#### 16. Default / Recommended Priority Source
There is **no** implemented `DEFAULT_PRIORITY` / `RECOMMENDED_PRIORITY` attribute in current plugins. Always use constant `50` when creating a new plugin wrapper unless user explicitly sets a different value via UI. (Future enhancement could add a class attribute; not part of this milestone.)

#### 17. Save / Refresh Responsibility Refactor
Original snippets intermingle saving and rebuilding (`_save_configuration()` inside `_refresh_plugin_display()`). Adopt this separation:
```python
async def _persist_config(self) -> bool: ...  # save only
async def _rebuild_runtime_state(self) -> None: ...  # rebuild PluginManager + re-render UI
async def _save_and_rebuild(self) -> bool:
    if not await self._persist_config():
        self.config = self._load_config_from_disk()
        await self._rebuild_runtime_state()
        return False
    await self._rebuild_runtime_state()
    return True
```
All mutation handlers should call `_save_and_rebuild()` exactly once. Mark legacy `_refresh_plugin_display()` for deprecation after refactor.

#### 18. Legacy `_populate_server_plugins()` Status
This method exists in `config_editor.py` and currently powers the middle panel list display. For MSP-3 keep it intact to avoid destabilizing navigation. A TODO should mark it for replacement in MSP-4 by a grouped renderer (`_render_server_plugin_groups`) inside the consolidated right panel.

---
The remainder of the original implementation guidance follows, now supplemented by the authoritative clarifications above.

### Part 1: Action Buttons

Update the plugin display to include action buttons:

```python
def _get_plugin_actions(self, handler_name: str, inheritance: str,
                       enabled: bool, plugin_type: str) -> List[Button]:
    """Determine which action buttons to show for a plugin."""
    import re
    # Sanitize handler name for use in button IDs
    safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', handler_name)

    actions = []

    if inheritance == "inherited":
        # Global plugin - can configure (view), override, or disable
        btn = Button("Configure", variant="primary", id=f"config_{safe_id}")
        btn.data_handler = handler_name  # Store original handler name
        actions.append(btn)
        if enabled:
            btn = Button("Disable", variant="warning", id=f"disable_{safe_id}")
            btn.data_handler = handler_name
            actions.append(btn)
    elif inheritance == "disabled":
        # Disabled global plugin - can enable
        btn = Button("Enable", variant="success", id=f"enable_{safe_id}")
        btn.data_handler = handler_name
        actions.append(btn)
    elif inheritance == "overrides":
        # Override - can configure or reset to global
        btn = Button("Configure", variant="primary", id=f"config_{safe_id}")
        btn.data_handler = handler_name
        actions.append(btn)
        btn = Button("Reset", variant="default", id=f"reset_{safe_id}")
        btn.data_handler = handler_name
        actions.append(btn)
    elif inheritance == "server-only":
        # Server-specific - can configure or remove
        btn = Button("Configure", variant="primary", id=f"config_{safe_id}")
        btn.data_handler = handler_name
        actions.append(btn)
        btn = Button("Remove", variant="error", id=f"remove_{safe_id}")
        btn.data_handler = handler_name
        actions.append(btn)

    return actions
```

> NOTE: In the final implementation prefer `PluginActionContext` over multiple `data_*` attributes. The snippet above is left intact for conceptual guidance but should be updated before merge.

### Part 2: Configure/Override Action

Handle the Configure button with override option for global plugins:

```python
async def _handle_plugin_configure(self, handler_name: str, plugin_type: str,
                                  inheritance: str) -> None:
    """Handle plugin configuration action."""

    # Get current configuration
    if inheritance == "inherited":
        # Show global config with override option
        global_config = self._get_global_plugin_config(handler_name, plugin_type)

        # Open modal with read-only global config
        modal = PluginConfigModal(
            handler_name=handler_name,
            plugin_type=plugin_type,
            config=global_config,
            read_only=True,
            show_override_button=True
        )
        result = await self.app.push_screen_wait(modal)

        if result == "override":
            # Create server-specific override
            await self._create_server_override(handler_name, plugin_type, global_config)
    else:
        # Edit server-specific config
        server_config = self._get_server_plugin_config(handler_name, plugin_type)

        modal = PluginConfigModal(
            handler_name=handler_name,
            plugin_type=plugin_type,
            config=server_config,
            read_only=False
        )
        result = await self.app.push_screen_wait(modal)

        if result:
            await self._save_plugin_config(handler_name, plugin_type, result)
```

### Part 3: Disable/Enable Actions

Implement disable via `enabled: false` override:

```python
async def _handle_plugin_disable(self, handler_name: str, plugin_type: str) -> None:
    """Disable a global plugin for this server."""
    # Sanitize handler name for button ID
    import re
    safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', handler_name)
    disable_button = self.query_one(f"#disable_{safe_id}", Button)
    disable_button.disabled = True

    try:
        # Get plugin configuration dict
        # NOTE: config.plugins.security/auditing/middleware are dicts
        plugins_config = self.config.plugins
        plugin_type_dict = getattr(plugins_config, plugin_type, {})
        server_plugins = plugin_type_dict.get(self.selected_server, [])

        # Create PluginConfigSchema object (not dict)
        from gatekit.config.models import PluginConfigSchema
        disable_override = PluginConfigSchema(
            handler=handler_name,
            enabled=False
        )
        server_plugins.append(disable_override)

        # CRITICAL: Must assign back to dict or changes are lost!
        plugin_type_dict[self.selected_server] = server_plugins

        # Save and refresh
        await self._save_configuration()
        await self._refresh_plugin_display()
    finally:
        # Re-enable might fail if button was replaced during refresh
        try:
            disable_button.disabled = False
        except:
            pass  # Button may have been replaced during refresh

async def _handle_plugin_enable(self, handler_name: str, plugin_type: str) -> None:
    """Re-enable a disabled plugin by removing the override."""
    # Sanitize handler name for button ID
    import re
    safe_id = re.sub(r'[^a-zA-Z0-9_-]', '_', handler_name)
    enable_button = self.query_one(f"#enable_{safe_id}", Button)
    enable_button.disabled = True

    try:
        # Get plugin configuration dict
        plugins_config = self.config.plugins
        plugin_type_dict = getattr(plugins_config, plugin_type, {})
        server_plugins = plugin_type_dict.get(self.selected_server, [])

        # Remove the disable override (using attribute access)
        server_plugins = [p for p in server_plugins
                         if not (p.handler == handler_name and not p.enabled)]

        # Update the config (already correct!)
        plugin_type_dict[self.selected_server] = server_plugins

        # Save and refresh
        await self._save_configuration()
        await self._refresh_plugin_display()
    finally:
        # Re-enable might fail if button was replaced during refresh
        try:
            enable_button.disabled = False
        except:
            pass  # Button may have been replaced during refresh
```

### Part 4: Add Plugin Dialog

Create filtered Add Plugin functionality:

```python
def _get_available_plugins_for_add(self, plugin_type: str) -> Dict[str, type]:
    """Get plugins available to add (not already configured)."""

    # Get all available handlers
    all_handlers = self.available_handlers.get(plugin_type, {})

    # IMPORTANT: Check RAW configuration, not resolved list!
    # Disabled plugins might not appear in get_plugins_for_upstream()
    configured_handlers = set()

    if self.config.plugins:
        # Get the plugin type dict (e.g., plugins.security is a dict)
        plugin_type_dict = getattr(self.config.plugins, plugin_type, {})

        # Check global configuration
        for plugin in plugin_type_dict.get("_global", []):
            configured_handlers.add(plugin.handler)

        # Check server-specific configuration
        for plugin in plugin_type_dict.get(self.selected_server, []):
            configured_handlers.add(plugin.handler)

    # Filter to only unconfigured
    available = {}
    for handler_name, handler_class in all_handlers.items():
        if handler_name in configured_handlers:
            continue  # Already configured (even if disabled)

        # Check compatibility
        display_scope = getattr(handler_class, 'DISPLAY_SCOPE', 'global')

        # Server-aware and server-specific plugins cannot be configured globally
        if self.selected_server == '_global' and display_scope in ('server_aware', 'server_specific'):
            continue

        # Server-specific plugins have additional compatibility requirements
        if display_scope == 'server_specific':
            compatible_servers = getattr(handler_class, 'COMPATIBLE_SERVERS', None)
            if compatible_servers and self.selected_server not in compatible_servers:
                continue

        available[handler_name] = handler_class

    return available

async def _handle_add_plugin(self, plugin_type: str) -> None:
    """Show dialog to add new plugin."""

    available = self._get_available_plugins_for_add(plugin_type)

    if not available:
        await self.app.push_screen(MessageModal(
            "No Available Plugins",
            "All compatible plugins are already configured for this server."
        ))
        return

    # Show selection dialog
    modal = AddPluginModal(available_plugins=available, plugin_type=plugin_type)
    result = await self.app.push_screen_wait(modal)

    if result:
        handler_name, config = result
        await self._add_plugin_to_server(handler_name, plugin_type, config)
        await self._refresh_plugin_display()
```

### Part 5: Post-Save Refresh and Error Handling

Critical: Always refresh after configuration changes AND handle save failures:

```python
async def _save_configuration(self) -> bool:
    """Save configuration with proper error handling.

    Returns:
        True if save succeeded, False otherwise
    """
    try:
        # TODO: Consider atomic writes (temp file + rename) in production
        # For now, use existing ConfigLoader save mechanism
        loader = ConfigLoader()
        loader.save_to_file(self.config, self.config_file_path)
        return True
    except Exception as e:
        # Show error banner - don't leave UI in inconsistent state
        await self.app.push_screen(ErrorModal(
            "Save Failed",
            f"Failed to save configuration: {e}"
        ))
        return False

async def _refresh_plugin_display(self) -> None:
    """Refresh the plugin display after configuration changes."""

    # Only refresh if save succeeded
    if not await self._save_configuration():
        # Revert in-memory changes if save failed
        self.config = self._load_config_from_disk()
        return

    # Re-fetch plugins from manager (clears any caches)
    self.plugin_manager = PluginManager(
        self.config.plugins.to_dict() if self.config.plugins else {},
        config_directory=self.config_file_path.parent
    )

    # Reload the plugin display
    await self._populate_server_plugins()

    # Update any other UI elements that might be affected
    self.refresh()
```

**Note on Atomic Persistence**: For production, consider implementing atomic file writes:
1. Write to temp file in same directory
2. fsync() to ensure data is on disk
3. Atomic rename() to replace original file
4. This prevents partial writes from corrupting configuration

### Part 6: Wire Up Event Handlers

Connect button clicks to actions:

```python
@on(Button.Pressed)
async def on_plugin_action_button(self, event: Button.Pressed) -> None:
    """Handle plugin action button presses."""

    button_id = event.button.id
    if not button_id:
        return

    # Prevent duplicate handling during async operations
    if hasattr(event.button, '_processing') and event.button._processing:
        return
    event.button._processing = True

    try:
        # Extract action from ID (config_xxx, disable_xxx, etc.)
        action = button_id.split('_', 1)[0]

        # Get actual handler name from data attribute (not from ID)
        handler_name = event.button.data_handler

        # Get plugin details from button's data attributes
        plugin_type = event.button.data_plugin_type
        inheritance = event.button.data_inheritance

        if action == "config":
            await self._handle_plugin_configure(handler_name, plugin_type, inheritance)
        elif action == "disable":
            await self._handle_plugin_disable(handler_name, plugin_type)
        elif action == "enable":
            await self._handle_plugin_enable(handler_name, plugin_type)
        elif action == "reset":
            await self._handle_plugin_reset(handler_name, plugin_type)
        elif action == "remove":
            await self._handle_plugin_remove(handler_name, plugin_type)
    finally:
        event.button._processing = False
```

## Success Criteria
- [ ] Can view global plugin configurations
- [ ] Can override global plugins for specific servers
- [ ] Can disable global plugins via `enabled: false` override
- [ ] Can re-enable disabled plugins
- [ ] Add Plugin only shows unconfigured, compatible plugins
- [ ] Can remove server-specific plugins
- [ ] Can reset overrides to use global configuration
- [ ] UI refreshes after all changes to show current state

## Testing
1. Test override flow: inherited → override → reset
2. Test disable flow: enabled → disabled → re-enabled
3. Verify Add Plugin filters out already-configured plugins
4. Test that disabled plugins don't appear in Add dialog
5. Confirm UI updates immediately after saves
6. Test with multiple plugin types (security, middleware, auditing)

## Files to Modify
- `gatekit/tui/screens/config_editor.py` - Add all action handlers
- May need to update `PluginConfigModal` to support override button
- May need to create `AddPluginModal` for plugin selection

## Technical Notes
- Always use `get_plugins_for_upstream()` after changes to get fresh data
- The config structure uses handler name as unique key
- Disabled plugins have `enabled: false` in config but still appear in resolved list
- Post-save refresh is CRITICAL to avoid stale UI state

## Next Steps
After plugin management is complete, MSP-4 will add server management (add/remove servers) and polish the two-panel layout.

### Addendum: Interaction with Upcoming Two-Panel Layout (MSP-4)
No functional logic in MSP-3 depends on the number of panels. To reduce refactor effort when MSP-4 merges middle/right panes:
- Centralize all plugin action rendering in a single method that accepts a container node (so the container can change without editing logic).
- Avoid direct references to `#server_plugins_list` inside helper methods (pass container or data list instead).
- Keep `selected_plugin` state optional; actions can infer context directly from button `data_ctx`.

This minimizes code churn during the layout consolidation phase.