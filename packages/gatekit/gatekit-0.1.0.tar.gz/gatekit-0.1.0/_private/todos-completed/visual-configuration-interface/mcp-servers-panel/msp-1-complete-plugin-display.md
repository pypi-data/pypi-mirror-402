# MSP-1: Complete Plugin Display

## Goal
Replace the minimal server plugins panel implementation with one that shows ALL plugins affecting each server, not just server-specific configurations.

## Current State
The `_populate_server_plugins()` method in `gatekit/tui/screens/config_editor.py` (around line 978) only displays server-specific plugins by reading directly from the config:

```python
# Current implementation (incomplete):
security_plugins = self.config.plugins.security.get(self.selected_server, [])
```

This misses all global plugins that also apply to the server.

## What to Build
Update the server plugins panel to show the complete set of plugins affecting each server by using the plugin manager's resolution system.

## Implementation

### Step 1: Use Plugin Manager Resolution
Replace the current implementation with:

```python
async def _populate_server_plugins(self) -> None:
    """Populate plugins list for the selected server."""
    if not self.selected_server:
        return

    plugins_list = self.query_one("#server_plugins_list", ListView)
    plugins_list.clear()

    # Get ALL plugins for this server (global + server-specific with overrides)
    upstream_plugins = self.plugin_manager.get_plugins_for_upstream(self.selected_server)

    # Process each plugin category
    for plugin_type in ["security", "middleware", "auditing"]:
        plugins = upstream_plugins.get(plugin_type, [])

        if plugins:
            # Add category header
            header = ListItem(Label(f"═══ {plugin_type.title()} Plugins ═══"))
            plugins_list.append(header)

            # CRITICAL: Do NOT re-sort these plugins!
            # Display in EXACT order from PluginManager (already sorted by priority)
            for plugin in plugins:
                handler_name = getattr(plugin, 'handler', plugin.__class__.__name__)
                enabled = getattr(plugin, 'enabled', True)
                status = "✅" if enabled else "❌"

                plugin_item = ListItem(
                    Label(f"• {self._format_handler_name(handler_name)} {status}")
                )
                plugin_item.data_handler = handler_name
                plugin_item.data_type = plugin_type
                plugins_list.append(plugin_item)
```

### Step 2: Test the Display
Create a test configuration with both global and server-specific plugins:

```yaml
plugins:
  security:
    _global:
      - handler: pii_filter
        enabled: true
      - handler: secrets_filter
        enabled: true
    filesystem:
      - handler: tool_allowlist
        enabled: true
```

Verify that the filesystem server now shows:
- PII Filter (from global)
- Secrets Filter (from global)
- Tool Allowlist (server-specific)

### Step 3: Handle All Plugin Types
Ensure the display works for all three plugin categories:
- Security plugins
- Middleware plugins
- Auditing plugins

## Success Criteria
- [ ] ALL plugins affecting a server are visible (not just server-specific)
- [ ] Global plugins inherited by servers are displayed
- [ ] Server-specific plugins continue to appear
- [ ] Plugin overrides are shown (server config replacing global)
- [ ] All three plugin categories are displayed (security, middleware, auditing)

## Testing
1. Create a config with `_global` plugins and server-specific plugins
2. Select a server in the TUI
3. Verify all plugins appear in the server plugins panel
4. Test with a server that has NO server-specific config (should still show global plugins)
5. Test with a server that overrides a global plugin

## Technical Notes

### Config Model Structure
**IMPORTANT**: The configuration uses a hybrid model:
- `self.config.plugins` is a Pydantic model (use attribute access)
- `self.config.plugins.security`, `.auditing`, `.middleware` are Python dicts: `Dict[str, List[PluginConfigSchema]]`

Example:
```python
# Get the plugin type dict (attribute access on model)
security_dict = self.config.plugins.security  # Returns a dict

# Use dict operations on the dict
server_plugins = security_dict.get(self.selected_server, [])  # Dict operation
```

### Plugin Resolution
- `get_plugins_for_upstream()` returns the complete, resolved plugin list
- It handles override logic automatically (server configs replace global configs with same handler name)
- The returned plugins are already in the correct state (enabled/disabled resolved)

## Files to Modify
- `gatekit/tui/screens/config_editor.py` - Update `_populate_server_plugins()` method

## Dependencies
- Requires functional `PluginManager` with `get_plugins_for_upstream()` method
- Assumes config is properly loaded with plugins section

## Next Steps
After this foundation is working, the next phase (MSP-2) will add inheritance indicators and execution order display to make the information more understandable.