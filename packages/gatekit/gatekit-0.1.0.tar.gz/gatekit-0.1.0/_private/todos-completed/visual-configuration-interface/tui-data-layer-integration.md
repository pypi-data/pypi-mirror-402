# TUI Data Layer Integration Guide

This document serves as the authoritative reference for how Gatekit's Terminal User Interface (TUI) integrates with the existing backend systems. Every TUI feature should reference this guide to ensure consistent and correct interaction with configuration management, plugin discovery, and display metadata systems.

## Executive Summary

### Available Systems
- **ConfigLoader**: YAML configuration file reading/writing with validation
- **PluginManager**: Plugin discovery, loading, and upstream-scoped resolution
- **Plugin Display Metadata**: Rich plugin status and action information without instantiation
- **Upstream-Scoped Configuration**: Global plugins with per-server overrides

### Common Integration Patterns
1. **Read Configuration**: `ConfigLoader.load_from_file()` → `ProxyConfig`
2. **Discover Plugins**: `PluginManager._discover_policies()` → `Dict[policy_name, plugin_class]`
3. **Get Display Data**: `plugin_class.describe_status(config)` → status string
4. **Resolve Effective Config**: `PluginManager.get_plugins_for_upstream()` → resolved plugins

## Configuration Management

### ConfigLoader Usage

The `ConfigLoader` class handles all YAML configuration file operations:

```python
from gatekit.config.loader import ConfigLoader
from pathlib import Path

# Load configuration
loader = ConfigLoader()
config = loader.load_from_file(Path("gatekit.yaml"))

# Access plugin configurations
plugins_config = config.plugins
security_config = plugins_config.security if plugins_config else {}
auditing_config = plugins_config.auditing if plugins_config else {}
```

### ProxyConfig Structure

The loaded configuration provides this structure:

```python
config.upstreams          # List[UpstreamConfig] - MCP servers
config.transport          # str - "stdio" or "http"
config.plugins           # Optional[PluginsConfig] - Plugin configurations
config.plugins.security  # Dict[str, List[PluginConfig]] - Security plugins by upstream
config.plugins.auditing  # Dict[str, List[PluginConfig]] - Auditing plugins by upstream
```

### Plugin Configuration Format

Each plugin in the configuration follows this structure:

```python
{
    "policy": "pii_filter",           # str - Plugin policy name (required)
    "enabled": True,                  # bool - Whether plugin is active (default: True)
    "config": {                       # dict - Plugin-specific configuration
        "action": "redact",
        "pii_types": {"email": {"enabled": True}}
    },
    "priority": 50,                   # int - Execution priority (lower = higher, default: 50)
    "critical": True                  # bool - Whether plugin failure crashes system (default: True)
}
```

### Configuration Access Patterns

```python
# Get global security plugins
global_security = security_config.get("_global", [])

# Get plugins for specific upstream
filesystem_security = security_config.get("filesystem", [])

# Check if plugin is enabled
def is_plugin_enabled(plugin_config):
    return plugin_config.get("enabled", True)

# Get plugin configuration
plugin_specific_config = plugin_config.get("config", {})
```

### Error Handling

ConfigLoader provides structured error handling:

```python
try:
    config = loader.load_from_file(config_path)
except FileNotFoundError:
    # Configuration file doesn't exist
    pass
except ValueError as e:
    error_msg = str(e).lower()
    if "yaml" in error_msg:
        # YAML syntax error
    elif "proxy" in error_msg and "section" in error_msg:
        # Missing proxy section
    elif "path validation" in error_msg:
        # Path validation error
    elif "validation" in error_msg:
        # General validation error
```

## Plugin Discovery System

### PluginManager Discovery

The `PluginManager` discovers plugins by scanning directories for `POLICIES` manifests:

```python
from gatekit.plugins.manager import PluginManager

# Initialize plugin manager
manager = PluginManager({})  # Empty config for discovery only

# Discover available plugins
security_policies = manager._discover_policies("security")
auditing_policies = manager._discover_policies("auditing")

# Result format: {"policy_name": PluginClass, ...}
```

### POLICIES Manifest Structure

Each plugin module exports a `POLICIES` dictionary:

```python
# In gatekit/plugins/security/pii.py
POLICIES = {
    "pii_filter": BasicPIIFilterPlugin
}

# In gatekit/plugins/auditing/json_lines.py  
POLICIES = {
    "audit_jsonl": JsonLinesAuditingPlugin
}
```

### Discovery Error Handling

Plugin discovery gracefully handles missing directories and invalid modules:

```python
policies = manager._discover_policies("nonexistent")
# Returns: {} (empty dict, not an error)

# Invalid modules are logged but don't crash discovery
# Modules without POLICIES attribute are ignored
```

### Plugin Loading vs Discovery

**Important Distinction**:
- **Discovery** (`_discover_policies`): Find available plugin classes, no instantiation
- **Loading** (`load_plugins`): Create plugin instances from configuration

TUI should use **discovery** for display purposes, never loading.

## Plugin Display Metadata Interface

### Class-Level Attributes

All plugins that want TUI display must provide:

```python
class MySecurityPlugin(SecurityPlugin):
    # Required for TUI display
    DISPLAY_NAME = "My Security Plugin"        # Human-readable name
    DISPLAY_SCOPE = "global"                   # "global", "server_aware", or "server_specific"
    
    # Auditing plugins don't use DISPLAY_SCOPE - they're always global
```

### Display Scope Categories

**Global Scope** (`DISPLAY_SCOPE = "global"`):
- Can be configured in `_global` section
- Can be configured in server sections (overrides global)
- Examples: `pii_filter`, `secrets_filter`, `prompt_injection`

**Server-Aware Scope** (`DISPLAY_SCOPE = "server_aware"`):
- CANNOT be configured in `_global` section
- Must be configured per-server but works with any server
- Examples: `tool_allowlist`

**Server-Specific Scope** (`DISPLAY_SCOPE = "server_specific"`):
- CANNOT be configured in `_global` section
- Only works with specific server types
- Examples: `filesystem_server_security`

### Status Description Method

```python
@classmethod
def describe_status(cls, config: Dict[str, Any]) -> str:
    """Generate status description from configuration.
    
    Args:
        config: Current plugin configuration dict (may be empty/None)
        
    Returns:
        Status string for display (e.g. "Blocking: API Keys, Tokens")
    """
    if not config or not config.get("enabled", False):
        return "Click to enable protection"
    
    # Build dynamic description from config
    action = config.get("action", "block")
    return f"{action.title()}: Active"
```

### Display Actions Method

```python
@classmethod  
def get_display_actions(cls, config: Dict[str, Any]) -> List[str]:
    """Return available UI actions based on configuration state.
    
    Args:
        config: Current plugin configuration dict (may be empty/None)
        
    Returns:
        List of action strings (1-3 max for UI space)
    """
    if config and config.get("enabled", False):
        return ["Configure", "Test"]
    return ["Setup"]
```

### Fallback Behavior

```python
# Get display name with fallback
display_name = getattr(plugin_class, 'DISPLAY_NAME', policy_name)

# Get display scope with fallback (security plugins only)
display_scope = getattr(plugin_class, 'DISPLAY_SCOPE', 'global')

# Handle method failures gracefully
try:
    status = plugin_class.describe_status(config)
except Exception:
    status = "Error loading status"
```

## Upstream-Scoped Configuration

### Configuration Resolution Algorithm

Gatekit uses global plugins with server-specific overrides:

1. **Start with global plugins**: Copy all plugins from `_global` section
2. **Add server-specific plugins**: For each plugin in server section:
   - If same policy name exists from global: **replace it** (override)
   - If no matching global plugin: **add it** (augment)
3. **Sort by priority**: Order final list by priority (lower = higher)

### Configuration Structure

```yaml
plugins:
  security:
    _global:                    # Global plugins (apply to all servers)
      - handler: "pii_filter"
        config: {action: "redact"}
    filesystem:                 # Server-specific plugins
      - handler: "pii_filter"    # Override global pii_filter
        config: {action: "block"}
      - handler: "tool_allowlist" # Add new plugin
        config: {mode: "allowlist"}
```

### Effective Configuration Resolution

```python
# Get effective plugins for an upstream
def get_effective_plugins(manager, upstream_name, plugin_type):
    """Get resolved plugins for an upstream."""
    upstream_plugins = manager.get_plugins_for_upstream(upstream_name)
    return upstream_plugins[plugin_type]  # "security" or "auditing"

# Example usage
filesystem_security = get_effective_plugins(manager, "filesystem", "security")
# Result: [pii_filter_instance(action="block"), tool_allowlist_instance(...)]
```

### Global vs Server Display Logic

For TUI global sections, consider how to show mixed configurations:

```python
def get_global_plugin_status(plugin_class, all_configs, policy_name):
    """Get status for global plugin that might be overridden."""
    global_config = None
    server_configs = []
    
    for upstream_name, plugins in all_configs.items():
        for plugin_config in plugins:
            if plugin_config.get("policy") == policy_name:
                if upstream_name == "_global":
                    global_config = plugin_config
                else:
                    server_configs.append((upstream_name, plugin_config))
    
    if not global_config and not server_configs:
        return "Not configured"
    elif global_config and not server_configs:
        return plugin_class.describe_status(global_config.get("config", {}))
    elif server_configs and not global_config:
        return f"Configured on {len(server_configs)} servers"
    else:
        # Mixed: global + overrides
        return f"Global + {len(server_configs)} server overrides"
```

## Data Structures Reference

### Plugin Configuration Schema

```python
# Individual plugin configuration
PluginConfig = {
    "policy": str,              # Required: policy name from POLICIES
    "enabled": bool,            # Optional: default True
    "config": dict,             # Optional: plugin-specific config
    "priority": int,            # Optional: default 50 (lower = higher priority)
    "critical": bool           # Optional: default True
}

# Upstream-scoped plugin configuration
PluginsConfig = {
    "security": {
        "_global": List[PluginConfig],
        "upstream_name": List[PluginConfig]
    },
    "auditing": {
        "_global": List[PluginConfig],
        "upstream_name": List[PluginConfig]
    }
}
```

### Plugin Scope Categories

```python
GLOBAL_PLUGINS = {
    # Security plugins that can be global
    "basic_pii_filter", "basic_secrets_filter", "basic_prompt_injection_defense"
}

SERVER_AWARE_PLUGINS = {
    # Universal plugins requiring per-server config
    "tool_allowlist"
}

SERVER_SPECIFIC_PLUGINS = {
    # Plugins for specific server types
    "filesystem_server_security": ["filesystem"]
}
```

### Common Configuration Patterns

```python
# Pattern 1: Global-only (simple deployments)
plugins = {
    "security": {
        "_global": [
            {"policy": "pii_filter", "config": {"action": "redact"}},
            {"policy": "secrets_filter", "config": {"action": "block"}}
        ]
    }
}

# Pattern 2: Server-specific only (maximum control)
plugins = {
    "security": {
        "filesystem": [{"policy": "tool_allowlist", "config": {...}}],
        "github": [{"policy": "tool_allowlist", "config": {...}}]
    }
}

# Pattern 3: Mixed global + override (recommended)
plugins = {
    "security": {
        "_global": [
            {"policy": "pii_filter", "config": {"action": "redact"}}
        ],
        "filesystem": [
            {"policy": "pii_filter", "config": {"action": "block"}},  # Override
            {"policy": "tool_allowlist", "config": {...}}            # Add
        ]
    }
}
```

## Code Patterns & Examples

### Reading Current Configuration

```python
def load_current_config(config_path: Path) -> Optional[ProxyConfig]:
    """Load and validate current configuration."""
    try:
        loader = ConfigLoader()
        return loader.load_from_file(config_path)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return None
```

### Discovering Available Plugins

```python
def discover_all_plugins() -> Dict[str, Dict[str, type]]:
    """Discover all available plugins."""
    manager = PluginManager({})  # Empty config for discovery
    
    return {
        "security": manager._discover_policies("security"),
        "auditing": manager._discover_policies("auditing")
    }
```

### Getting Plugin Display Information

```python
def get_plugin_display_info(plugin_class, plugin_config) -> Dict[str, Any]:
    """Get display information for a plugin."""
    config_dict = plugin_config.get("config", {}) if plugin_config else {}
    
    return {
        "name": getattr(plugin_class, 'DISPLAY_NAME', 'Unknown Plugin'),
        "scope": getattr(plugin_class, 'DISPLAY_SCOPE', 'global'),
        "status": plugin_class.describe_status(config_dict),
        "actions": plugin_class.get_display_actions(config_dict),
        "enabled": plugin_config.get("enabled", True) if plugin_config else False
    }
```

### Filtering Plugins by Scope

```python
def get_global_plugins(all_policies: Dict[str, type]) -> Dict[str, type]:
    """Get plugins that can appear in global sections."""
    global_plugins = {}
    
    for policy_name, plugin_class in all_policies.items():
        scope = getattr(plugin_class, 'DISPLAY_SCOPE', 'global')
        if scope == 'global':
            global_plugins[policy_name] = plugin_class
    
    return global_plugins
```

### Getting Current Plugin Configuration

```python
def get_plugin_config(plugins_config: Dict, upstream_name: str, policy_name: str) -> Optional[Dict]:
    """Get configuration for a specific plugin."""
    if not plugins_config:
        return None
    
    # Check upstream-specific first
    upstream_plugins = plugins_config.get(upstream_name, [])
    for plugin_config in upstream_plugins:
        if plugin_config.get("policy") == policy_name:
            return plugin_config
    
    # Check global if not found and upstream isn't global
    if upstream_name != "_global":
        global_plugins = plugins_config.get("_global", [])
        for plugin_config in global_plugins:
            if plugin_config.get("policy") == policy_name:
                return plugin_config
    
    return None
```

## Integration Points

### Where TUI Reads Configuration
- **Entry Point**: `ConfigLoader.load_from_file(config_path)`
- **Used By**: All TUI screens that need configuration data
- **Returns**: `ProxyConfig` object with complete configuration

### Where TUI Discovers Plugins
- **Entry Point**: `PluginManager._discover_policies(category)`
- **Used By**: Plugin selection, global plugin widgets
- **Returns**: `Dict[policy_name, plugin_class]`

### Where TUI Gets Display Data
- **Entry Points**: 
  - `plugin_class.DISPLAY_NAME` - Human readable name
  - `plugin_class.DISPLAY_SCOPE` - Scope category (security only)
  - `plugin_class.describe_status(config)` - Dynamic status
  - `plugin_class.get_display_actions(config)` - Available actions
- **Used By**: Global plugin widgets, plugin lists
- **Note**: Never instantiate plugins for display

### Where TUI Saves Changes
- **Pattern**: Modify `ProxyConfig` object, serialize to YAML, write to file
- **Implementation**: TUI should use YAML serialization that preserves structure
- **Hot Reload**: Changes should trigger configuration reload in running instances

## Important Constraints

### Plugin Equality Principle
All plugins are first-class citizens:
- Built-in plugins get no special treatment
- Use dynamic discovery, never hardcode plugin names
- All plugins use same interfaces and validation

### No Plugin Instantiation for Display
Display metadata works without creating plugin instances:
- Use class methods and attributes only
- Handle cases where plugins are disabled/not configured
- Reduces overhead and prevents side effects

### Configuration-Driven Display
Status and actions reflect actual configuration:
- Parse configuration to build display information
- Show dynamic information (file sizes, enabled features)
- Handle empty/invalid configurations gracefully

### Graceful Degradation
TUI should handle errors without crashing:
- Missing plugins → show "Plugin not found"
- Invalid configs → show "Configuration error"  
- Failed methods → use fallback displays

## Common TUI Tasks Reference

### Task: Get All Global Security Plugins

```python
# Get available plugins
manager = PluginManager({})
all_security = manager._discover_policies("security")

# Filter for global-capable plugins
global_security = {}
for name, plugin_class in all_security.items():
    scope = getattr(plugin_class, 'DISPLAY_SCOPE', 'global')
    if scope == 'global':
        global_security[name] = plugin_class
```

### Task: Get Plugin Status Description

```python
# Load current config
config = ConfigLoader().load_from_file(config_path)
security_config = config.plugins.security if config.plugins else {}

# Get plugin config
global_plugins = security_config.get("_global", [])
pii_config = None
for plugin in global_plugins:
    if plugin.get("policy") == "pii_filter":
        pii_config = plugin
        break

# Get status
plugin_class = all_security["pii_filter"]
config_dict = pii_config.get("config", {}) if pii_config else {}
status = plugin_class.describe_status(config_dict)
```

### Task: Check If Plugin Is Enabled

```python
def is_plugin_enabled(plugin_config: Optional[Dict]) -> bool:
    """Check if a plugin configuration indicates enabled state."""
    if not plugin_config:
        return False
    return plugin_config.get("enabled", True)
```

### Task: Get Available But Unconfigured Plugins

```python
def get_unconfigured_plugins(all_policies: Dict, current_config: List) -> Dict:
    """Get plugins that are available but not configured."""
    configured_policies = {p.get("policy") for p in current_config}
    unconfigured = {}
    
    for policy_name, plugin_class in all_policies.items():
        if policy_name not in configured_policies:
            unconfigured[policy_name] = plugin_class
    
    return unconfigured
```

### Task: Save Configuration Changes

```python
def save_plugin_changes(config_path: Path, updated_config: ProxyConfig):
    """Save configuration changes to file."""
    # Convert ProxyConfig back to dictionary format
    config_dict = {
        "proxy": {
            "transport": updated_config.transport,
            "upstreams": [
                {
                    "name": upstream.name,
                    "command": upstream.command,
                    "args": upstream.args
                }
                for upstream in updated_config.upstreams
            ]
        }
    }
    
    if updated_config.plugins:
        config_dict["plugins"] = {
            "security": updated_config.plugins.security,
            "auditing": updated_config.plugins.auditing
        }
    
    # Write to YAML file
    import yaml
    with open(config_path, 'w') as f:
        yaml.safe_dump(config_dict, f, default_flow_style=False, sort_keys=False)
```

---

## Conclusion

This document provides the complete reference for TUI backend integration. Every TUI component should use these patterns to ensure consistent, reliable interaction with Gatekit's configuration and plugin systems.

**Key Principles**:
1. Always use ConfigLoader for configuration access
2. Use PluginManager for plugin discovery, not loading
3. Leverage plugin display metadata for rich UI
4. Handle errors gracefully with fallbacks
5. Never instantiate plugins for display purposes

**Next Steps**: Use this guide when implementing specific TUI features like global plugin widgets, server management, and configuration editing.