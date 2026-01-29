# Bug: Disabled Server Override Falls Back to Global Plugin

## Summary

When a user creates a server-specific plugin override and then disables it (`enabled: false`), the plugin falls back to using the global configuration instead of being truly disabled for that server.

## Reproduction Steps

1. Configure a global PII filter plugin (enabled)
2. Create a server-specific override for the PII filter
3. Disable the server-specific override (`enabled: false`)
4. Expected: PII filter is disabled for that server
5. Actual: PII filter continues to work (using global config)

## Root Cause

In `gatekit/plugins/manager.py`, disabled plugins are **skipped entirely during loading**:

```python
# Lines 1464-1469, 1548-1551, 1632-1637
if not plugin_config.get("config", {}).get("enabled", True):
    logger.debug(
        f"Skipping disabled security plugin: {plugin_config.get('handler', 'unknown')}"
    )
    continue  # Plugin never loaded!
```

This means during `_resolve_plugins_for_upstream()`:
1. Global plugins are collected (includes enabled PII filter)
2. Server-specific overrides are checked... but the disabled one was never loaded
3. No override exists, so global plugin is used

## Expected Behavior

A disabled server-specific override should **mask** the global plugin, effectively disabling it for that server.

## Proposed Fix

**Option A: Load disabled overrides, filter at resolution time**
1. Remove the `enabled` check from loading phase (load all configured plugins)
2. In `_resolve_plugins_for_upstream()`, filter out disabled plugins from the final resolved list
3. This ensures disabled overrides still "exist" to mask global plugins

**Option B: Special handling for disabled overrides**
1. During loading, detect if a disabled plugin is an override of a global plugin
2. If so, load it as a "masking" entry that blocks the global
3. Skip truly disabled server-only plugins (no global to mask)

Option A is simpler and more consistent.

## Files to Modify

- `gatekit/plugins/manager.py`:
  - `_load_upstream_scoped_security_plugins()`
  - `_load_upstream_scoped_middleware_plugins()`
  - `_load_upstream_scoped_auditing_plugins()`
  - `_resolve_plugins_for_upstream()`

## Testing

Add test cases:
1. Global plugin enabled, server override disabled → plugin disabled for server
2. Global plugin enabled, no server override → plugin enabled (inheritance)
3. Global plugin disabled, server override enabled → plugin enabled for server
4. Server-only plugin disabled → plugin disabled (no fallback)

## Related TUI Issue: "Use Global" Button Disappears

When the server-specific plugin is disabled, the "Use Global" button also disappears. This prevents users from reverting to the global config without first re-enabling the server-specific plugin.

### Root Cause (TUI)

In `plugin_rendering.py`, `_format_inheritance_status()` returns `""` (empty string) for `"disabled"` status:

```python
display_status_map = {
    ...
    "disabled": "",  # Returns empty string!
    ...
}
```

But in `plugin_table.py` (lines 336-348), the "Use Global" button visibility checks:

```python
if (
    self.show_actions
    and global_enabled
    and inheritance
    in [
        "overrides",
        "overrides (config)",
        "overrides (disables)",
        "disabled",  # Expects "disabled", but gets ""
        "server-only",
    ]
):
```

Since `inheritance` is `""` not `"disabled"`, the condition fails and the button is hidden.

### Proposed TUI Fix

Store both raw and formatted inheritance in `plugin_data`:

1. In `_render_server_plugin_groups()`, add `raw_inheritance` field alongside `inheritance`
2. In `PluginRowWidget.compose()`, use `raw_inheritance` for button visibility logic
3. Keep using formatted `inheritance` (or `scope`) for display text

### Files to Modify (TUI)

- `gatekit/tui/screens/config_editor/plugin_rendering.py`: Add `raw_inheritance` to plugin_data
- `gatekit/tui/widgets/plugin_table.py`: Use `raw_inheritance` for "Use Global" button visibility

## Priority

Medium - Users may be surprised by this behavior, but workaround exists (remove the override entirely and create a new disabled-only entry... though that has the same bug).

## Discovered

During TUI validation testing
