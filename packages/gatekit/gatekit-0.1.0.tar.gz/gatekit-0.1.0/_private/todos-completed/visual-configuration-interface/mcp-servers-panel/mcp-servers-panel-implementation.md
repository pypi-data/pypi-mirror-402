# MCP Servers Panel Implementation

## Executive Summary

The MCP Servers panel currently exists as a minimal placeholder that only displays server-specific plugin configurations. This document outlines building it into a complete server management interface that shows the full security posture, enables plugin configuration, and provides server management capabilities.

## Current State

The existing implementation in `_populate_server_plugins()` is a basic stub that only reads server-specific configurations directly from the config file. This was likely a quick initial implementation that needs to be built out into a proper feature.

### What's Missing
1. **Complete plugin visibility** - Need to show ALL plugins affecting each server (global + server-specific)
2. **Inheritance display** - No indication of where plugin configurations come from
3. **Override mechanism** - Can't override global plugins at the server level
4. **Management actions** - Can't add/remove servers or configure plugins properly
5. **Execution order** - No visibility into plugin execution sequence
6. **Two-panel layout** - Current three-panel design wastes space

## Design Decision: Two-Panel Layout with Complete Plugin View

### Visual Design
```
├─────────────────────────────────────────────────────────┤
│ ┌─ MCP Servers (3) ─────┐ ┌─ Server: filesystem ──────┐ │
│ │ ▶ filesystem          │ │ Command: npx @mcp/fs...   │ │
│ │   github              │ │ Args: ["/home"]           │ │
│ │   sqlite              │ │                           │ │
│ │                       │ │ ═══ Security Plugins ═══  │ │
│ │                       │ │     (execution order)     │ │
│ │                       │ │ 1. ☑ Rate Limiter  [Config]│ │
│ │                       │ │    ↳ inherited (pri: 10) │ │
│ │                       │ │ 2. ☑ PII Filter    [Config]│ │
│ │                       │ │    ↳ overrides (pri: 50) │ │
│ │                       │ │ 3. ☐ Secrets Filter[Disable]│ │
│ │                       │ │    ↳ disabled (pri: 60)  │ │
│ │                       │ │ 4. ☑ Tool Allowlist[Config]│ │
│ │                       │ │    ↳ server-only (pri: 90)│ │
│ │                       │ │ [+ Add Security Plugin]    │ │
│ │                       │ │                           │ │
│ │                       │ │ ═══ Middleware Plugins ═══│ │
│ │                       │ │     (execution order)     │ │
│ │                       │ │ 1. ☑ Tool Manager  [Config]│ │
│ │                       │ │    ↳ server-only (pri: 30)│ │
│ │                       │ │ [+ Add Middleware Plugin]  │ │
│ │                       │ │                           │ │
│ │                       │ │ ═══ Auditing Plugins ═══  │ │
│ │                       │ │  (runs in listed order)   │ │
│ │                       │ │ • ☑ JSON Lines     [View] │ │
│ │                       │ │   ↳ inherited from global │ │
│ │ [+ Add] [- Remove]    │ │                           │ │
│ └───────────────────────┘ └───────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
```

### Key Design Elements

#### 1. Simplified Server List (Left Panel)
- Just server names for clean scanning
- Selection indicator (▶)
- Count in header "MCP Servers (3)"
- Add/Remove buttons at bottom
- No clutter (status, tools, commands moved to detail panel)

#### 2. Comprehensive Server Details (Right Panel)
- Server configuration at top (command, args, transport)
- ALL plugins affecting the server grouped by category
- Clear inheritance indicators for each plugin
- Action buttons appropriate to plugin type

#### 3. Inheritance Indicators with Priority
Each plugin shows its configuration source and execution priority:
- **"inherited (pri: N)"** - Using global configuration with priority N
- **"server-only (pri: N)"** - Only configured for this server
- **"overrides (pri: N)"** - Server config overrides global config
- **"disabled (pri: N)"** - Server explicitly disables a global plugin via `enabled: false`

Note: Security and middleware plugins execute in priority order (lower number = higher priority = runs first). Auditing plugins execute in definition order (no priority).

## Technical Implementation

### Core Change: Use Complete Plugin Resolution
The main technical change is to use the already-implemented plugin resolution system instead of reading raw config:

```python
# Current approach (incomplete):
security_plugins = self.config.plugins.security.get(self.selected_server, [])

# Complete approach:
upstream_plugins = self.plugin_manager.get_plugins_for_upstream(self.selected_server)
all_security = upstream_plugins["security"]  # Includes global + server with overrides handled
```

### Plugin Ordering Display
The execution order is critical for users to understand the security posture:
```python
def format_plugins_with_order(plugins, plugin_type, raw_config):
    """Format plugins with deterministic execution order.

    CRITICAL: This must match EXACTLY the ordering used by PluginManager.
    Do NOT re-implement sorting here - use the already-sorted list from
    get_plugins_for_upstream() which has the authoritative ordering.
    """
    if plugin_type == 'auditing':
        # Auditing plugins execute in definition order, no numbering
        # Display hint: "(runs in listed order)"
        return [(p, None) for p in plugins]
    else:
        # Security and middleware plugins are ALREADY SORTED by PluginManager
        # with deterministic tie-breaking. Just add numbering.
        return [(p, idx+1) for idx, p in enumerate(plugins)]
```

### Deterministic Plugin Ordering (CRITICAL)
Plugin execution order must be consistent and predictable. The PluginManager uses this algorithm:

```python
def get_deterministic_sort_key(plugin, raw_config, server_name):
    """Generate sort key for deterministic plugin ordering.

    Sort order (for security/middleware only):
    1. Priority (lower number = higher priority = runs first)
    2. Tie-breaker 1: Server-specific before global (on same priority)
    3. Tie-breaker 2: Original config definition order
    4. Tie-breaker 3: Handler name (alphabetical)
    """
    priority = getattr(plugin, 'priority', 50)

    # Determine if this is server-specific or inherited from global
    handler_name = getattr(plugin, 'handler', plugin.__class__.__name__)
    is_server_specific = any(
        p.handler == handler_name
        for p in raw_config[plugin_type].get(server_name, [])
    )

    # Get original config index for stable ordering
    config_index = get_config_definition_index(plugin, raw_config, server_name)

    return (
        priority,                           # Primary: priority value
        0 if is_server_specific else 1,    # Tie-breaker 1: server-specific first
        config_index,                       # Tie-breaker 2: definition order
        handler_name                        # Tie-breaker 3: alphabetical
    )

# The UI must display the EXACT order from get_plugins_for_upstream(),
# not re-sort or reorder plugins independently.
```

### Building the Complete Feature

The implementation involves several interconnected components:

1. **Plugin Resolution**: Use `get_plugins_for_upstream()` to get the complete, resolved plugin list
2. **Inheritance Detection**: Compare resolved plugins with raw config to determine source
3. **Visual Display**: Show plugins with execution order, priority, and inheritance
4. **Management Actions**: Enable configuration, override, disable, and add operations
5. **Server Management**: Add/remove servers from the configuration

### Determining Plugin Inheritance Status
```python
def get_plugin_inheritance(handler_name, plugin_type, server_name, effective_plugin):
    """Determine how a plugin is configured for a server.

    Args:
        handler_name: The plugin handler identifier
        plugin_type: 'security', 'middleware', or 'auditing'
        server_name: The server to check
        effective_plugin: The actual plugin instance from get_plugins_for_upstream()
    """

    # Check raw configuration
    global_plugins = config.plugins[plugin_type].get("_global", [])
    server_plugins = config.plugins[plugin_type].get(server_name, [])

    global_plugin = next((p for p in global_plugins if p.handler == handler_name), None)
    server_plugin = next((p for p in server_plugins if p.handler == handler_name), None)

    # Get priority for display (except auditing which has no priority)
    priority = getattr(effective_plugin, 'priority', None) if plugin_type != 'auditing' else None

    if server_plugin:
        if global_plugin:
            # Server overrides global - check if it's just disabling
            if not server_plugin.enabled and global_plugin.enabled:
                return ("disabled", priority)  # Explicitly disabled via override
            elif server_plugin.config != global_plugin.config or \
                 server_plugin.enabled != global_plugin.enabled:
                return ("overrides", priority)  # Configuration override
            else:
                return ("overrides", priority)  # Any server-level config is an override
        else:
            return ("server-only", priority)  # Server-specific, no global
    elif global_plugin:
        return ("inherited", priority)  # Using global configuration
    else:
        # This shouldn't happen if plugin is in effective list
        return ("unknown", priority)
```

### Action Handlers

#### 1. Configure Action
- **For inherited plugins**: Opens modal with option to override or disable for this server
- **For overrides**: Edits server-specific configuration with option to reset to global
- **For server-specific**: Edits configuration directly
- **For disabled plugins**: Shows as "Enable" button that removes the disable override

#### 2. Add Plugin Action
Opens modal showing only plugins that:
- Are NOT already configured (even if disabled) - check both global and server-specific
- Are compatible with the server (check DISPLAY_SCOPE)
- Support the server type (check COMPATIBLE_SERVERS if present)

```python
def get_available_plugins_for_add(server_name, plugin_type):
    """Get plugins available to add (not already configured)."""
    all_handlers = discover_all_handlers(plugin_type)

    # Get ALL configured plugins (enabled or disabled)
    configured = set()

    # Check global plugins
    for p in config.plugins[plugin_type].get("_global", []):
        configured.add(p.handler)

    # Check server-specific plugins
    for p in config.plugins[plugin_type].get(server_name, []):
        configured.add(p.handler)

    # Filter to only unconfigured plugins
    available = {}
    for handler_name, handler_class in all_handlers.items():
        if handler_name in configured:
            continue  # Already configured (even if disabled)

        # Check compatibility
        display_scope = getattr(handler_class, 'DISPLAY_SCOPE', 'global')
        if display_scope == 'server_specific' and server_name == '_global':
            continue  # Can't add server-specific plugins globally

        compatible_servers = getattr(handler_class, 'COMPATIBLE_SERVERS', None)
        if compatible_servers and server_name not in compatible_servers:
            continue  # Not compatible with this server

        available[handler_name] = handler_class

    return available
```

**Important**: If a plugin is disabled via override, the user should use [Enable] on the existing entry, NOT add it again through the Add dialog.

#### 3. Remove/Reset/Disable Actions
- **Server-specific plugins**: [Remove] button removes from configuration
- **Override plugins**: [Reset] button removes override, reverts to global
- **Disabled plugins**: [Enable] button removes the `enabled: false` override
- **Inherited global plugins**: [Disable] button adds `enabled: false` override for this server

#### 4. Disable-via-Override Mechanism
When a user wants to disable a global plugin for a specific server:
1. Click [Disable] on an inherited global plugin
2. System adds server-specific config with `handler: plugin_name, enabled: false`
3. Plugin shows as disabled with "☐" checkbox and "disabled (pri: N)" status
4. [Enable] button appears to remove the disable override

## Implementation Phases

The implementation has been broken down into four manageable, testable sections. Each builds on the previous and can be completed independently:

### Implementation Documents

📁 **Location**: `docs/todos/visual-configuration-interface/mcp-servers-panel/`

1. **[msp-1-complete-plugin-display.md](mcp-servers-panel/msp-1-complete-plugin-display.md)**
   - Foundation: Show ALL plugins (global + server-specific)
   - Replace stub with plugin manager resolution
   - Estimated time: 1.5 hours

2. **[msp-2-inheritance-and-ordering.md](mcp-servers-panel/msp-2-inheritance-and-ordering.md)**
   - Add inheritance indicators and execution order
   - Show where configs come from and priority
   - Estimated time: 2 hours

3. **[msp-3-plugin-management-actions.md](mcp-servers-panel/msp-3-plugin-management-actions.md)**
   - Enable all management actions
   - Configure, override, disable, add, remove
   - Estimated time: 3 hours

4. **[msp-4-server-management.md](mcp-servers-panel/msp-4-server-management.md)**
   - Add/remove servers and two-panel layout
   - Polish and complete the feature
   - Estimated time: 3 hours

### Implementation Order

These documents MUST be implemented in sequence as each builds on the previous:
- **MSP-1** provides the foundation (complete plugin visibility)
- **MSP-2** makes the information understandable
- **MSP-3** makes it actionable
- **MSP-4** completes the feature with server management

Each document includes:
- Clear goals and success criteria
- Code examples and implementation details
- Testing requirements
- Estimated completion time

## Configuration Structure (Already Implemented)

The backend already fully supports this via the dictionary-based configuration:

```yaml
plugins:
  security:
    _global:
      - handler: pii_filter
        enabled: true
        config: {action: redact}
      
    filesystem:
      - handler: pii_filter  # Override with different config
        enabled: true
        config: {action: block}
      - handler: tool_allowlist  # Additional server-specific
        enabled: true
        config: {allowed_tools: ["read_file"]}
```

The `PluginManager._resolve_plugins_for_upstream()` method correctly:
1. Starts with `_global` plugins
2. Adds server-specific plugins
3. Removes global plugins that are overridden by server-specific with same handler name
4. Returns the merged, effective plugin list

## User Interaction Flows

### Flow 1: Override Global Plugin
1. User sees "PII Filter ↳ inherited (pri: 50)"
2. Clicks [Configure]
3. Modal shows current global config (read-only)
4. Modal has [Override for This Server] and [Disable for This Server] buttons
5. Clicking override switches to edit mode with server-specific config
6. Save creates server-specific override

### Flow 1b: Disable Global Plugin for Server
1. User sees "PII Filter ↳ inherited (pri: 50)"
2. Clicks [Disable] button (or [Configure] → [Disable for This Server])
3. System adds `{handler: "pii_filter", enabled: false}` to server config
4. Plugin now shows as "☐ PII Filter ↳ disabled (pri: 50)" with [Enable] button
5. Clicking [Enable] removes the disable override

### Flow 2: Add Server-Specific Plugin
1. User clicks [+ Add Security Plugin]
2. Modal shows ONLY unconfigured plugins (excluding already configured, even if disabled)
3. User selects plugin and configures
4. Save adds to server-specific configuration
5. **UI refreshes** to show new plugin with correct ordering and inheritance

Note: If user wants to enable a disabled plugin, they must use [Enable] on the existing entry, not Add.

### Flow 3: Remove Override
1. User sees "Secrets Filter ↳ overrides (pri: 60)"
2. Clicks [Configure]
3. Modal shows server override with [Reset to Global] button
4. Clicking reset removes server-specific config
5. Plugin reverts to "inherited (pri: 60)"

### Flow 4: Re-enable Disabled Plugin
1. User sees "☐ Secrets Filter ↳ disabled (pri: 60)" with [Enable] button
2. Clicks [Enable]
3. System removes the `enabled: false` override from server config
4. Plugin reverts to "☑ Secrets Filter ↳ inherited (pri: 60)"

## Success Criteria

1. **Complete Visibility**: Users can see ALL plugins affecting each server with execution order
2. **Clear Inheritance**: Obvious which plugins are global vs server-specific vs overrides vs disabled
3. **Deterministic Ordering**: Plugin execution order is consistent and predictable with clear tie-breaking
4. **Priority Display**: Execution order clearly shown for security/middleware, "runs in listed order" for auditing
5. **Management Actions**: Can add, remove, override, disable, enable, and reset plugins
6. **Consistent UX**: Plugin configuration matches global panel behavior
7. **Live Updates**: UI refreshes immediately after save to show current state
8. **No Data Loss**: Changes properly saved to configuration file

## Testing Requirements

### Unit Tests
- Plugin inheritance detection logic (including enabled/disabled states)
- Deterministic ordering with tie-breakers (equal priorities, mixed global/server)
- Add dialog filtering (excludes configured plugins even if disabled)
- Compatibility filtering for add plugin
- Override detection and handling
- Disable-via-override mechanism
- Post-save state refresh

### Integration Tests
- Full flow of override creation
- Disable and re-enable flows
- Plugin resolution with complex configurations (including disabled plugins)
- Server add/remove with plugin cleanup
- Priority ordering verification

### Manual Testing
- Visual clarity of inheritance indicators
- Smooth interaction flows
- Configuration persistence
- Edge cases (empty configs, many plugins, etc.)

## Notes on Existing Implementation

### What to Keep
- Basic panel structure (just merge middle and right)
- ListView for server list
- Plugin configuration modal system
- Save/reload functionality

### What to Change
- Fix `_populate_server_plugins()` to show ALL plugins
- Add inheritance detection and display
- Implement management actions
- Simplify server list display

### What to Add
- Server add/remove functionality
- Plugin add functionality 
- Override mechanism
- Reset/remove actions

## References

- **Backend Implementation**: `docs/todos-completed/plugin-server-overrides/requirements.md`
- **Plugin Resolution**: `PluginManager._resolve_plugins_for_upstream()` 
- **Configuration Structure**: Dictionary-based with `_global` and server keys
- **Progress Tracker**: `docs/todos/visual-configuration-interface/tui-progress-tracker.md`