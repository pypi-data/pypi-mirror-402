# Plugin Display Refactoring: Reuse Working Server Plugin Code for Global Plugins

## Status: TODO

## Problem Statement

The Gatekit TUI has two separate widget systems for displaying plugins:
1. **Global plugins**: `GlobalSecurityWidget` / `GlobalAuditingWidget` in `global_plugins.py` - BROKEN
2. **Server plugins**: `PluginTableWidget` in `plugin_table.py` - WORKS PERFECTLY

After extensive polishing, the server plugin system works flawlessly. Meanwhile, global plugins have critical bugs and use completely different code. This is unnecessary - both display lists of plugins with checkboxes and configure buttons.

## Core Issues

### Bug #1: Global Plugin Config Modal Changes Don't Sync
**Cause**: `_populate_global_plugins()` calls `update_plugins_data(self.config_file_path)` which reloads from disk instead of using the in-memory config.

### Bug #2: Global Plugin Checkbox Changes Don't Refresh UI
**Cause**: `handle_global_plugin_toggled()` never refreshes the global plugin widgets.

### Bug #3: Different Code Paths for Same Functionality
**Cause**: Historical divergence created two systems doing the same thing.

## Solution: Reuse PluginTableWidget Everywhere

The server plugin `PluginTableWidget` already handles:
- Checkbox state management ✅
- Configure button actions ✅
- Enable/disable toggles ✅
- Proper refresh on changes ✅
- Focus restoration ✅
- Column sorting ✅

We should use it for global plugins too, just with different display options.

## Implementation Plan

### Phase 1: Immediate Bug Fixes (1 hour)
**Goal**: Fix critical bugs before refactoring

1. Fix `_populate_global_plugins()` to use in-memory config:
   ```python
   # plugin_rendering.py line ~212
   # Before: await security_widget.update_plugins_data(self.config_file_path)
   # After:  await security_widget.update_plugins_data(config=self.config)
   ```

2. Add refresh in `handle_global_plugin_toggled()`:
   ```python
   # base.py line ~1493
   await self._populate_global_plugins()  # Add this line
   await self._rebuild_runtime_state()   # Keep existing
   await self._populate_server_details() # Keep existing
   ```

3. Test that checkboxes and configure modals now sync properly.

### Phase 2: Adapt PluginTableWidget for Global Display (4-5 hours)
**Goal**: Replace custom global widgets with configured PluginTableWidget

#### Step 1: Add Scope Constants (15 min)

Create shared constants to avoid sentinel string typos:

```python
# gatekit/tui/constants.py (or new file)
GLOBAL_SCOPE = "_global"

# Optional: Create enum for type safety
from enum import Enum

class PluginScope(str, Enum):
    GLOBAL = "_global"
    # Server scopes are dynamic (server names)
```

#### Step 2: Extend Messages with Scope (30 min)

Both messages need scope information to route correctly:

```python
# gatekit/tui/widgets/plugin_table.py

class PluginToggle(Message):
    """Message sent when a plugin checkbox is toggled."""
    bubble = True

    def __init__(self, handler: str, plugin_type: str, enabled: bool, scope: str) -> None:
        self.handler = handler
        self.plugin_type = plugin_type
        self.enabled = enabled
        self.scope = scope  # "_global" or server name
        super().__init__()

class PluginActionClick(Message):
    """Message sent when a plugin action is clicked."""
    bubble = True

    def __init__(self, handler: str, plugin_type: str, action: str, scope: str) -> None:
        self.handler = handler
        self.plugin_type = plugin_type
        self.action = action
        self.scope = scope  # "_global" or server name
        super().__init__()
```

#### Step 3: Update PluginRowWidget to Include Scope (30 min)

Widget needs to know its parent scope to emit correct messages.

**CRITICAL**: ALL message emissions (both PluginToggle and PluginActionClick) must include scope parameter. This includes:
- Checkbox toggles
- Configure button clicks (mouse and keyboard)
- Use Global button clicks (mouse and keyboard)

**Test isolation reminder**: when mocking `Screen.app` in unit tests, always use `with patch.object(type(screen), "app", new_callable=PropertyMock)` so the descriptor is restored after each test run. Never assign to `type(screen).app` directly; that pollutes later tests.

```python
# gatekit/tui/widgets/plugin_table.py

class PluginRowWidget(Horizontal):
    def __init__(
        self,
        plugin_data: Dict[str, Any],
        plugin_type: str,
        scope: str,  # Add this parameter
        show_priority: bool = True,
        show_actions: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.plugin_data = plugin_data
        self.plugin_type = plugin_type
        self.scope = scope  # Store scope
        # ... rest unchanged

    def on_checkbox_value_changed(self, checkbox_widget, new_value: bool) -> None:
        """Handle checkbox value changes."""
        # ... existing code ...

        # Post toggle message with scope
        msg = PluginToggle(
            self.plugin_data["handler"],
            self.plugin_type,
            new_value,
            self.scope  # Include scope
        )
        # ... rest unchanged

    def on_key(self, event) -> None:
        """Handle key events on focusable widgets."""
        # Handle Enter and Space keys on action buttons
        if event.key in ("enter", "space"):
            focused_widget = self.app.focused
            if focused_widget and hasattr(focused_widget, "id") and focused_widget.id:
                if focused_widget.id.startswith("action_configure_"):
                    handler = focused_widget.id.replace("action_configure_", "")
                    msg = PluginActionClick(
                        handler,
                        self.plugin_type,
                        "Configure",
                        self.scope  # Include scope
                    )
                    # Post message...
                elif focused_widget.id.startswith("action_useglobal_"):
                    handler = focused_widget.id.replace("action_useglobal_", "")
                    msg = PluginActionClick(
                        handler,
                        self.plugin_type,
                        "Use Global",
                        self.scope  # Include scope
                    )
                    # Post message...

    def on_click(self, event) -> None:
        """Handle click events on the plugin row."""
        if event.widget.id.startswith("action_configure_"):
            handler = event.widget.id.replace("action_configure_", "")
            msg = PluginActionClick(
                handler,
                self.plugin_type,
                "Configure",
                self.scope  # Include scope
            )
            # Post message...
        elif event.widget.id.startswith("action_useglobal_"):
            handler = event.widget.id.replace("action_useglobal_", "")
            msg = PluginActionClick(
                handler,
                self.plugin_type,
                "Use Global",
                self.scope  # Include scope
            )
            # Post message...
```

#### Step 4: Update PluginTableWidget Constructor and Composition (30 min)

Widget needs to pass scope to child rows and conditionally compose header:

```python
# gatekit/tui/widgets/plugin_table.py

class PluginTableWidget(Container):
    def __init__(
        self,
        plugin_type: str,
        server_name: str,  # "_global" for global plugins, or actual server name
        plugins_data: List[Dict[str, Any]] = None,
        show_priority: bool = True,
        show_header: bool = True,  # NEW: control header visibility
        max_visible_rows: int = DEFAULT_MAX_VISIBLE_ROWS,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.plugin_type = plugin_type
        self.server_name = server_name  # This is the scope
        self.show_header = show_header  # Store for compose
        # ... rest unchanged

    def compose(self) -> ComposeResult:
        """Compose the table structure."""
        # Only render header if show_header is True
        if self.show_header:
            yield PluginTableHeader(
                show_priority=self.show_priority,
                plugin_type=self.plugin_type,
                show_actions=False,
            )

        # Content area (always rendered)
        rows_container = Container(classes="table-scroll")
        rows_container.can_focus = False
        with rows_container:
            for plugin_data in self.plugins_data:
                yield PluginRowWidget(
                    plugin_data,
                    self.plugin_type,
                    scope=self.server_name,  # Pass scope
                    show_priority=self.show_priority,
                    show_actions=True,
                )

    def refresh_table(self) -> None:
        """Refresh the table display."""
        # ... existing code ...

        for plugin_data in sorted_data:
            row = PluginRowWidget(
                plugin_data,
                self.plugin_type,
                scope=self.server_name,  # Pass scope to rows
                show_priority=self.show_priority,
                show_actions=True,
            )
            rows_container.mount(row)
```

#### Step 5: Add CSS for Global Display Mode (30 min)

Global plugins need cleaner, more compact styling:

```python
# gatekit/tui/widgets/plugin_table.py - Add to DEFAULT_CSS

"""
/* Global display mode - cleaner look */
PluginTableWidget.global-mode {
    border: none;
    margin: 0;
}

PluginTableWidget.global-mode PluginRowWidget {
    height: 1;  /* Tighter rows */
}
"""

# In __init__:
if server_name == GLOBAL_SCOPE:
    self.add_class("global-mode")
```

**Note**: Header is controlled via `show_header` flag in composition, not CSS.

**Keep existing coverage**: Adapt, don't delete, the priority-sorting and global widget unit tests. They should assert against the new table configuration (e.g., hidden header in global mode, scope-aware messages) so the Phase 1 regressions stay locked down.

#### Step 6: Update Event Handlers to Branch on Scope (1 hour)

Modify existing handlers to handle both global and server scopes:

```python
# gatekit/tui/screens/config_editor/plugin_actions.py

@on(PluginToggle)
async def on_plugin_toggle(self, event: PluginToggle) -> None:
    """Handle plugin checkbox toggles for both global and server scopes."""
    from ...debug import get_debug_logger
    logger = get_debug_logger()

    if logger:
        logger.log_event(
            "PLUGIN_TOGGLE_EVENT_RECEIVED",
            screen=self,
            context={
                "handler": event.handler,
                "plugin_type": event.plugin_type,
                "scope": event.scope,
                "new_enabled_state": event.enabled,
            },
        )

    if not self.config.plugins:
        self.config.plugins = PluginsConfig()

    plugin_type_dict = getattr(self.config.plugins, event.plugin_type, {})
    if not plugin_type_dict:
        plugin_type_dict = {}

    # Branch based on scope
    if event.scope == GLOBAL_SCOPE:
        # Update global plugins
        global_plugins = plugin_type_dict.get(GLOBAL_SCOPE, [])

        found = False
        for plugin in global_plugins:
            if plugin.handler == event.handler:
                plugin.enabled = event.enabled
                found = True
                break

        if not found:
            # Create new global plugin config
            new_plugin = PluginConfig(
                handler=event.handler,
                config={"enabled": event.enabled, "priority": 50}
            )
            global_plugins.append(new_plugin)

        plugin_type_dict[GLOBAL_SCOPE] = global_plugins

        # Clean up server-specific disabled entries if enabling globally
        if event.enabled:
            for server_name, server_plugins in list(plugin_type_dict.items()):
                if server_name == GLOBAL_SCOPE:
                    continue
                filtered = [p for p in server_plugins if not (p.handler == event.handler and not p.enabled)]
                plugin_type_dict[server_name] = filtered

        # Update config
        setattr(self.config.plugins, event.plugin_type, plugin_type_dict)
        self._mark_dirty()

        # Refresh global plugins display
        await self._populate_global_plugins()
        await self._rebuild_runtime_state()
        await self._populate_server_details()

    else:
        # Update server-specific plugins (existing logic)
        server_plugins = plugin_type_dict.get(event.scope, [])

        found = False
        for plugin in server_plugins:
            if plugin.handler == event.handler:
                plugin.enabled = event.enabled
                found = True
                break

        if not found:
            new_plugin = PluginConfig(
                handler=event.handler,
                config={"enabled": event.enabled, "priority": 50}
            )
            server_plugins.append(new_plugin)

        plugin_type_dict[event.scope] = server_plugins
        setattr(self.config.plugins, event.plugin_type, plugin_type_dict)
        self._mark_dirty()

        # Refresh server plugins display
        await self._render_server_plugin_groups()

    # Focus restoration (scope-aware)
    def _restore_focus():
        try:
            if event.scope == GLOBAL_SCOPE:
                # Derive widget ID from plugin_type: security -> global_security_widget
                widget_id = f"global_{event.plugin_type}_widget"
                container = self.query_one(f"#{widget_id}")
            else:
                # Find server widget
                container = self.query_one("#server_plugins_display")
            checkbox = container.query_one(f"#checkbox_{event.handler}")
            checkbox.focus()
        except Exception:
            pass

    self.set_timer(0.01, _restore_focus)
    event.stop()


@on(PluginActionClick)
async def on_plugin_action_click(self, event: PluginActionClick) -> None:
    """Handle plugin action clicks for both global and server scopes."""
    from ...debug import get_debug_logger
    logger = get_debug_logger()

    if logger:
        logger.log_event(
            "PLUGIN_ACTION_CLICK_RECEIVED",
            screen=self,
            context={
                "handler": event.handler,
                "plugin_type": event.plugin_type,
                "action": event.action,
                "scope": event.scope,
            },
        )

    if event.action == "Configure":
        # Determine inheritance based on scope
        if event.scope == GLOBAL_SCOPE:
            inheritance = None  # Global plugins don't have inheritance
        else:
            # Get inheritance for server plugin
            plugin = None
            if self.plugin_manager:
                upstream_plugins = self.plugin_manager.get_plugins_for_upstream(event.scope)
                for p in upstream_plugins.get(event.plugin_type, []):
                    if getattr(p, "handler", p.__class__.__name__) == event.handler:
                        plugin = p
                        break

            inheritance, _, _ = self.get_plugin_inheritance(
                event.handler, event.plugin_type, event.scope, plugin
            )

        # Open config modal
        self._run_worker(
            self._handle_plugin_config_modal(
                handler_name=event.handler,
                plugin_type=event.plugin_type,
                scope=event.scope,
                inheritance=inheritance,
            )
        )

    elif event.action == "Use Global":
        # Only valid for server scope
        if event.scope != GLOBAL_SCOPE:
            await self._handle_use_global_action(event.handler, event.plugin_type)

    event.stop()
```

#### Step 7: Update Global Plugin Rendering in base.py (30 min)

Replace `GlobalSecurityWidget` and `GlobalAuditingWidget` with `PluginTableWidget`:

```python
# gatekit/tui/screens/config_editor/base.py

from gatekit.tui.constants import GLOBAL_SCOPE
from gatekit.tui.widgets.plugin_table import PluginTableWidget

# In compose() method, replace:
# yield GlobalSecurityWidget(id="global_security_widget")
# with:

yield PluginTableWidget(
    plugin_type="security",
    server_name=GLOBAL_SCOPE,
    plugins_data=[],  # Will be populated later
    show_priority=False,  # Global plugins don't show priority
    show_header=False,    # Cleaner look without header
    id="global_security_widget"
)

# Similarly for auditing:
yield PluginTableWidget(
    plugin_type="auditing",
    server_name=GLOBAL_SCOPE,
    plugins_data=[],
    show_priority=False,
    show_header=False,
    id="global_auditing_widget"
)
```

#### Step 8: Extract and Reuse Plugin Display Data Builder (1 hour)

Create a shared helper that preserves all plugin metadata (status messages, missing-handler warnings). If you intend to reuse it for server rows as well, it must also emit the inheritance fields (`inheritance`, `global_enabled`, blanked `priority` when disabled) so the server table continues to dim inherited checkboxes, gate "Use Global", and show scope labels correctly. Otherwise, make it explicit in the code that the helper is **global-only** and leave the existing server row builder untouched.

**8a. Extract Helper Method**

This reuses the logic from `global_plugins.py::generate_plugin_display_data()` but makes it scope-aware:

```python
# gatekit/tui/screens/config_editor/plugin_rendering.py

def _build_plugin_display_data(
    self,
    plugin_type: str,
    scope: str,  # "_global" or server name
) -> List[Dict[str, Any]]:
    """Build plugin display data for a given type and scope.

    Preserves plugin metadata including:
    - Plugin-specific status via describe_status()
    - Missing handler warnings

    Args:
        plugin_type: "security", "middleware", or "auditing"
        scope: GLOBAL_SCOPE or server name

    Returns:
        List of plugin display data dicts
    """
    from gatekit.tui.constants import GLOBAL_SCOPE

    plugins_data = []

    # Get available handlers for this plugin type
    available_handlers = self.available_handlers.get(plugin_type, {})

    # Get configuration for this scope
    plugins_config = {}
    if self.config.plugins:
        plugin_type_dict = getattr(self.config.plugins, plugin_type, {})
        plugins_config = plugin_type_dict.get(scope, [])

    # Build display data for each available plugin
    for handler_name, handler_class in available_handlers.items():
        # Find config for this handler in the scope
        plugin_config = None
        for p in plugins_config:
            if p.handler == handler_name:
                plugin_config = p
                break

        # Build complete config dict (matching global_plugins.py pattern)
        complete_config = {
            "handler": handler_name,
            "enabled": plugin_config.enabled if plugin_config else False,
            "priority": plugin_config.priority if plugin_config else 50,
            "config": plugin_config.config if plugin_config else {},
        }

        # Extract inner config for plugin methods (they expect config dict, not PluginConfig)
        inner_config = complete_config.get("config", {})
        config_for_plugin_methods = {
            **inner_config,
            "enabled": complete_config.get("enabled", False),
            "priority": complete_config.get("priority", 50),
        }

        try:
            # Get display information from plugin class methods
            display_name = getattr(handler_class, "DISPLAY_NAME", handler_name.title())

            # Call plugin's describe_status() for rich status messages
            status = handler_class.describe_status(config_for_plugin_methods)

            display_data = {
                "handler": handler_name,
                "display_name": display_name,
                "status": status,
                "action": "Configure",  # Primary action
                "enabled": complete_config.get("enabled", False),
                "priority": complete_config.get("priority", 50),
                "is_missing": False,  # Handler found
            }
            plugins_data.append(display_data)

        except Exception as e:
            # Fallback for plugin method failures (preserve existing error handling)
            plugins_data.append({
                "handler": handler_name,
                "display_name": handler_name.title(),
                "status": "Error loading plugin status",
                "action": "Configure",
                "enabled": False,
                "priority": complete_config.get("priority", 50),
                "is_missing": False,
                "error": str(e),
            })

    # Check for configured plugins that are missing from available handlers
    # (This preserves the "⚠ handler (not found)" warnings)
    for plugin_config in plugins_config:
        if plugin_config.handler not in available_handlers:
            plugins_data.append({
                "handler": plugin_config.handler,
                "display_name": plugin_config.handler,
                "status": "Plugin not found",
                "action": "Configure",
                "enabled": plugin_config.enabled,
                "priority": plugin_config.priority,
                "is_missing": True,  # Will show ⚠ in UI
            })

    # Sort: enabled first, then by priority (lower = higher), then alphabetical
    plugins_data.sort(
        key=lambda p: (
            not p["enabled"],
            p.get("priority", 50),
            p["display_name"],
        )
    )

    return plugins_data

# If `get_display_actions()` returns additional buttons, consider storing the action list
# alongside `plugins_data` so the widget can render them in the future. If we are not ready
# to render dynamic actions yet, add an inline TODO explaining the deliberate omission.
```

**8b. Update _populate_global_plugins() to Use Helper**

```python
# gatekit/tui/screens/config_editor/plugin_rendering.py

async def _populate_global_plugins(self) -> None:
    """Populate the global plugins section using PluginTableWidget."""
    from ...debug import get_debug_logger
    from ...widgets.plugin_table import PluginTableWidget
    from gatekit.tui.constants import GLOBAL_SCOPE

    logger = get_debug_logger()

    security_widget = self.query_one("#global_security_widget", PluginTableWidget)
    auditing_widget = self.query_one("#global_auditing_widget", PluginTableWidget)

    # Build plugin data using shared helper
    security_data = self._build_plugin_display_data("security", GLOBAL_SCOPE)
    auditing_data = self._build_plugin_display_data("auditing", GLOBAL_SCOPE)

    # Update widgets with in-memory config data
    security_widget.update_plugins(security_data)
    auditing_widget.update_plugins(auditing_data)

    if logger:
        logger.log_widget_lifecycle(
            "update",
            screen=self,
            component="global_plugins",
            action="populate_plugins_data",
        )

    # Adjust container heights
    self._adjust_global_plugins_section_height(security_widget, auditing_widget)
    self._setup_navigation_containers()
```

**Benefits of This Approach**:
- Preserves plugin-specific status messages via `describe_status()` (e.g., "Filtering SSN, Email")
- Preserves missing-handler warnings ("⚠ handler (not found)")
- Single source of truth for display data building
- Works for global plugins where complexity is manageable

**Note on Server Plugins**: This helper is designed specifically for global plugins. Server plugins have additional complexity (inheritance tracking, scope display, runtime state, priority formatting rules) that cannot be consolidated without breaking functionality. Server plugin rendering should remain unchanged - it's polished and working perfectly.

#### Step 9: Remove Old Handlers and Messages (15 min)

Clean up duplicate code:

```python
# Delete from base.py:
@on(GlobalPluginToggled)
async def handle_global_plugin_toggled(self, message: GlobalPluginToggled) -> None:
    # DELETE THIS ENTIRE HANDLER

@on(PluginActionRequest)
async def handle_plugin_action_request(self, message: PluginActionRequest) -> None:
    # DELETE THIS ENTIRE HANDLER

# Delete from global_plugins.py:
class GlobalPluginToggled(Message):
    # DELETE THIS CLASS

class PluginActionRequest(Message):
    # DELETE THIS CLASS
```

### Phase 3: Cleanup (1 hour)
**Goal**: Remove dead code and update tests

1. Delete `gatekit/tui/widgets/global_plugins.py` entirely
2. Remove imports of `GlobalSecurityWidget`, `GlobalAuditingWidget`, `GlobalPluginToggled`, `PluginActionRequest`
3. Update tests that reference old global widget classes
4. Verify all tests pass

## Technical Details

### Configuration Differences

| Aspect | Global Plugins | Server Plugins |
|--------|---------------|----------------|
| `server_name` | `GLOBAL_SCOPE` (`"_global"`) | Actual server name |
| `show_header` | `False` | `True` |
| `show_priority` | `False` | `True` (except auditing) |
| `show_actions` | `True` | `True` |
| CSS class | `global-mode` | (default) |
| Border | None | Bordered |
| Row height | 1 line | Standard |

### Message Flow (After Refactor)

```
# Both global and server plugins use same messages:
PluginRowWidget → Checkbox → PluginToggle(handler, plugin_type, enabled, scope)
               → Configure → PluginActionClick(handler, plugin_type, "Configure", scope)

ConfigEditorScreen → on_plugin_toggle(scope) → Updates config based on scope
                  → on_plugin_action_click(scope) → Opens modal for scope
                  → Refresh appropriate widget
```

### Data Structure (Unchanged)

Both global and server plugins use the same data dict structure:
```python
{
    "handler": "pii_filter",
    "display_name": "PII Filter",
    "enabled": True,
    "priority": 50,  # Ignored for global display
    "inheritance": "...",  # Only used for server display
    "status": "Active",
    "action": "Configure"
}
```

### Sorting Behavior

- **Server plugins**: Sorting enabled, header clicks change sort order
- **Global plugins**: Header hidden, plugins pre-sorted by enabled → priority → name. No interactive sorting needed.

## Benefits

- **Reuse battle-tested code**: Server plugin code has been extensively debugged and polished
- **Single implementation**: One set of code to maintain
- **Consistent behavior**: Same UX everywhere
- **Less code**: ~500+ lines removed from `global_plugins.py`
- **Fewer bugs**: Single code path is easier to test and debug
- **Type safety**: Scope passed explicitly in messages, not inferred

## Testing Checklist

### After Phase 1 (Bug Fixes)
- [ ] Global plugin checkbox toggles update the checkbox UI
- [ ] Global plugin Configure modal changes update the checkbox
- [ ] No file reloading occurs during UI operations

### After Phase 2 (Refactor)
- [ ] Global plugins display correctly without headers or borders
- [ ] Global plugin checkboxes update `config.plugins.{type}._global`
- [ ] Global plugin Configure modal updates save to `_global` scope
- [ ] Server plugins still work exactly as before
- [ ] All PluginToggle messages include scope field
- [ ] All PluginActionClick messages include scope field (Configure AND Use Global)
- [ ] Focus restoration works for both global and server scopes (using correct widget IDs)
- [ ] CSS styling matches design (compact for global, bordered for server)
- [ ] Header is not rendered for global plugins (composition guard, not CSS)
- [ ] Server plugin checkbox is disabled when the corresponding global plugin is inherited and enabled
- [ ] "Use Global" appears only when a server override exists and clears the override when clicked
- [ ] Server toggle logic reflects actual config state (toggling uses server override when present, otherwise follows global)
- [ ] Inheritance/status labels in the server table still reflect the global/server relationship (Inherited, Overrides, Disabled)
- [ ] Re-enabling a global plugin removes any server-level disabled overrides and refreshes server panels

### After Phase 3 (Cleanup)
- [ ] All tests pass
- [ ] No references to `GlobalSecurityWidget` remain
- [ ] No references to `GlobalPluginToggled` remain
- [ ] No references to `PluginActionRequest` remain
- [ ] Import errors resolved

## Risk Mitigation

**Risk**: Breaking working server plugins
**Mitigation**: Server plugin code paths remain unchanged except for scope parameter addition. All branching happens in handlers, not widget code.

**Risk**: Typos in scope strings
**Mitigation**: Use `GLOBAL_SCOPE` constant throughout. Consider enum for additional type safety.

**Risk**: Visual regression in global plugins
**Mitigation**: CSS `global-mode` class provides cleaner look. Review styling before merge.

**Risk**: Focus restoration breaks
**Mitigation**: Test focus restoration for both scopes explicitly.

## Success Metrics

1. **Bug fixes verified**: Both checkbox and modal sync issues resolved
2. **Code reduction**: ~500+ lines removed
3. **Tests pass**: All existing tests still work
4. **Single code path**: Only one widget system to maintain
5. **Global config updates**: Verify `config.plugins.{type}._global` is correctly updated by new handlers

## Timeline

- **Phase 1**: 1 hour (immediate bug fixes)
- **Phase 2**: 4-5 hours (adapt PluginTableWidget with scope support)
- **Phase 3**: 1 hour (cleanup)

**Total**: 6-7 hours

## Next Steps

1. **Immediate**: Apply Phase 1 fixes to resolve sync bugs
2. **This week**: Complete Phase 2 refactoring with scope support
3. **Follow-up**: Consider if other duplicate TUI code can be similarly consolidated

## Decision Log

- Initial document created after discovering sync bugs
- Pivoted from creating new architecture to reusing existing PluginTableWidget
- Added scope parameter to messages based on QC feedback
- QC review fixes:
  - Ensured ALL PluginActionClick emissions include scope (Configure + Use Global, mouse + keyboard)
  - Fixed focus restoration to derive widget ID from plugin_type (not hardcoded)
  - Specified plugin data building pattern (reuse existing logic from server plugins)
  - Changed header hiding from CSS to composition guard (`if self.show_header`)
  - **Critical**: Removed Step 8c (server plugin consolidation) - would break inheritance tracking, scope display, and priority formatting
- **Design Choice**: Reuse working code over creating "perfect" architecture
- **Design Choice**: Minimize changes to working server plugin code
- **Design Choice**: Use constants (`GLOBAL_SCOPE`) to prevent sentinel string typos
- **Design Choice**: Branch in handlers rather than widget code for cleaner separation
- **Design Choice**: Helper method designed for global plugins only - server plugins have complexity that cannot be consolidated
