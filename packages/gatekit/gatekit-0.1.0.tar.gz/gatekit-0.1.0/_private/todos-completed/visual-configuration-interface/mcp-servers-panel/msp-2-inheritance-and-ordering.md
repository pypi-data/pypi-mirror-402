# MSP-2: Inheritance and Execution Order Display

## Goal
Enhance the plugin display to show WHERE each plugin configuration comes from (inheritance) and the execution order for security/middleware plugins.

## Prerequisites
- MSP-1 must be complete (showing all plugins)
- Plugins are displayed but without context about their source or order

## What to Build
1. Add inheritance indicators showing if a plugin is inherited, server-specific, or an override
2. Display execution order with priority numbers for security/middleware plugins
3. Add "runs in listed order" hint for auditing plugins

## Implementation

### Part 1: Inheritance Detection

Create a helper function to determine plugin inheritance:

```python
def get_plugin_inheritance(self, handler_name: str, plugin_type: str, server_name: str,
                           effective_plugin) -> tuple[str, Optional[int]]:
    """Determine how a plugin is configured for a server.

    Returns:
        Tuple of (inheritance_status, priority)
    """
    # Get raw configuration
    # NOTE: config.plugins is a Pydantic model, but its attributes (security, auditing, etc.)
    # are Python dicts: Dict[str, List[PluginConfigSchema]]
    plugins_config = self.config.plugins
    if not plugins_config:
        return ("unknown", None)

    # Get the plugin type dict (e.g., plugins_config.security returns a dict)
    plugin_type_dict = getattr(plugins_config, plugin_type, {})

    # Now use dict operations on the dict
    global_plugins = plugin_type_dict.get("_global", [])
    server_plugins = plugin_type_dict.get(server_name, [])

    # Find matching plugins in raw config (using attribute access)
    global_plugin = next((p for p in global_plugins if p.handler == handler_name), None)
    server_plugin = next((p for p in server_plugins if p.handler == handler_name), None)

    # Get priority (not for auditing plugins)
    priority = getattr(effective_plugin, 'priority', None) if plugin_type != 'auditing' else None

    if server_plugin:
        if global_plugin:
            # Check if it's disabled override
            if not server_plugin.enabled and global_plugin.enabled:
                return ("disabled", priority)
            else:
                return ("overrides", priority)
        else:
            return ("server-only", priority)
    elif global_plugin:
        return ("inherited", priority)
    else:
        return ("unknown", priority)
```

### Part 2: Display with Execution Order

Update the display to show inheritance and order:

```python
async def _populate_server_plugins(self) -> None:
    """Populate plugins list for the selected server."""
    if not self.selected_server:
        return

    plugins_list = self.query_one("#server_plugins_list", ListView)
    plugins_list.clear()

    # Get ALL plugins for this server
    upstream_plugins = self.plugin_manager.get_plugins_for_upstream(self.selected_server)

    for plugin_type in ["security", "middleware", "auditing"]:
        plugins = upstream_plugins.get(plugin_type, [])

        if plugins:
            # Add category header with ordering hint
            if plugin_type == "auditing":
                header_text = f"═══ {plugin_type.title()} Plugins ═══\n    (runs in listed order)"
            else:
                header_text = f"═══ {plugin_type.title()} Plugins ═══\n    (execution order)"

            header = ListItem(Label(header_text))
            plugins_list.append(header)

            # CRITICAL: Plugins are ALREADY SORTED by PluginManager
            # DO NOT re-sort! Display in EXACT order received.
            # For security/middleware, just add numbering to show execution order
            for idx, plugin in enumerate(plugins):
                handler_name = getattr(plugin, 'handler', plugin.__class__.__name__)
                enabled = getattr(plugin, 'enabled', True)

                # Get inheritance status
                inheritance, priority = self.get_plugin_inheritance(
                    handler_name, plugin_type, self.selected_server, plugin
                )

                # Format based on type
                if plugin_type == "auditing":
                    # No numbering for auditing
                    prefix = "• "
                else:
                    # Number for execution order
                    prefix = f"{idx + 1}. "

                # Format status
                if not enabled or inheritance == "disabled":
                    checkbox = "☐"
                else:
                    checkbox = "☑"

                # Build display
                line1 = f"{prefix}{checkbox} {self._format_handler_name(handler_name)}"

                # Add inheritance indicator
                if priority is not None:
                    line2 = f"   ↳ {inheritance} (pri: {priority})"
                else:
                    line2 = f"   ↳ {inheritance}"

                plugin_item = ListItem(
                    Vertical(
                        Label(line1),
                        Label(line2, classes="plugin-inheritance")
                    )
                )
                plugin_item.data_handler = handler_name
                plugin_item.data_type = plugin_type
                plugins_list.append(plugin_item)
```

### Part 3: Deterministic Ordering

**SINGLE SOURCE OF TRUTH**: The PluginManager is the ONLY place that sorts plugins. The UI must display plugins in the EXACT order received from `get_plugins_for_upstream()`.

```python
# The PluginManager sorts with these rules:
# 1. Priority (lower number = higher priority = runs first)
# 2. Server-specific before global (on tie)
# 3. Config definition order (on tie)
# 4. Handler name alphabetically (final tie-breaker)

# CRITICAL: DO NOT re-sort in the UI! Display in the order received.
# Any re-sorting in the UI would cause the displayed order to differ
# from actual execution order, confusing users about security posture.
```

### Part 4: Visual Styling

Add CSS for the inheritance indicators:

```css
.plugin-inheritance {
    color: $text-muted;
    font-size: 0.9em;
    padding-left: 2;
}
```

## Success Criteria
- [ ] Each plugin shows its inheritance status (inherited, server-only, overrides, disabled)
- [ ] Security/middleware plugins are numbered by execution order (1, 2, 3...)
- [ ] Priority values are displayed with inheritance
- [ ] Auditing plugins show "runs in listed order" without numbering
- [ ] Disabled plugins show with ☐ checkbox
- [ ] The displayed order EXACTLY matches execution order

## Testing
1. Create config with various scenarios:
   - Global plugin inherited by server
   - Server-specific plugin (no global)
   - Server override of global plugin
   - Disabled global plugin (enabled: false override)
2. Verify inheritance indicators are correct
3. Test plugins with same priority to verify deterministic ordering
4. Confirm execution order numbering is sequential and correct

## Visual Example
```
═══ Security Plugins ═══
    (execution order)
1. ☑ Rate Limiter
   ↳ inherited (pri: 10)
2. ☑ PII Filter
   ↳ overrides (pri: 50)
3. ☐ Secrets Filter
   ↳ disabled (pri: 60)
4. ☑ Tool Allowlist
   ↳ server-only (pri: 90)

═══ Auditing Plugins ═══
    (runs in listed order)
• ☑ JSON Lines
   ↳ inherited
```

## Files to Modify
- `gatekit/tui/screens/config_editor.py` - Add `get_plugin_inheritance()` method and update display

## Next Steps
After inheritance and ordering are clear, MSP-3 will add management actions (configure, override, disable, add).