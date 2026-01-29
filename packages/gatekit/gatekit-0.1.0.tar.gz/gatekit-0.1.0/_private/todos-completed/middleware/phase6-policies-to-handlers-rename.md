# Phase 6: POLICIES → HANDLERS Nomenclature Change

## Prerequisites
- Phase 5 completed (Plugin manager supports middleware)
- All tests passing

## Overview
Rename all references from "POLICIES" to "HANDLERS" and "policy" to "handler" throughout the codebase. This change improves semantic clarity as "handler" is appropriate for all plugin types (middleware, security, auditing) while "policy" only makes sense for security/governance contexts.

## Why This Change Matters
- **Semantic Accuracy**: "handler" correctly describes what these are - code that handles messages
- **Consistency**: Works for ALL plugin types, not just security
- **Clarity**: Reduces confusion about what these manifest variables represent
- **Future-Proof**: Aligns with middleware architecture where not everything is a "policy"

## Pre-Implementation Audit

### 0. Comprehensive Grep Audit

Before making any changes, perform a thorough audit to identify ALL uses of "policy" terminology:

```bash
# Find plugin.policy attribute usage
grep -r "\.policy" gatekit/

# Find policy_name variables
grep -r "policy_name" gatekit/

# Find 'policy' string keys
grep -r "'policy'" gatekit/

# Find "policy" in docstrings/comments (excluding legitimate "security policy" usage)
grep -r '"policy"' gatekit/ | grep -v "security policy"

# Find log fields and serialization keys
grep -r "policy_" gatekit/
```

Document all findings before proceeding.

## Implementation Tasks

### 1. Update Plugin Manifests

#### Task 1.1: Update all POLICIES declarations to HANDLERS

For each plugin file, change the manifest declaration at the bottom:

**Security Plugins** (`gatekit/plugins/security/*.py`):
- `pii.py`
- `secrets.py`
- `filesystem_server.py`
- `prompt_injection.py`
- `tool_allowlist.py`

**Auditing Plugins** (`gatekit/plugins/auditing/*.py`):
- `human_readable.py`
- `json_lines.py`
- `csv.py`
- `common_event_format.py`
- `syslog.py`

Change from:
```python
POLICIES = {
    "plugin_name": PluginClass
}
```

To:
```python
HANDLERS = {
    "plugin_name": PluginClass
}
```

### 2. Update Plugin Discovery

#### Location: `gatekit/plugins/manager.py`

#### Task 2.1: Rename discovery method
```python
# Change method name
def _discover_handlers(self, plugin_category: str) -> Dict[str, Type[PluginInterface]]:
    """Discover available handlers for a plugin category.
    
    Args:
        plugin_category: Category to discover ('security', 'auditing', 'middleware')
        
    Returns:
        Dictionary mapping handler names to plugin classes
    """
    # ... existing implementation but with HANDLERS instead of POLICIES
```

#### Task 2.2: Update discovery implementation
Inside `_discover_handlers` (formerly `_discover_policies`), change:
```python
# OLD
policies = getattr(module, 'POLICIES', {})

# NEW
handlers = getattr(module, 'HANDLERS', {})
```

#### Task 2.3: Update all calls to discovery method
Search and replace all occurrences:
- `self._discover_policies` → `self._discover_handlers`
- `available_policies` → `available_handlers`

This affects:
- `_load_upstream_scoped_security_plugins`
- `_load_upstream_scoped_auditing_plugins`
- `_load_upstream_scoped_middleware_plugins` (if it exists)

### 3. Update Plugin Instance Attributes

#### Task 3.1: Update plugin.policy attribute

The plugin manager sets a `policy` attribute on plugin instances. This needs to be renamed:

```python
# In _create_plugin_instance (manager.py line ~1015)
# OLD
plugin_instance.policy = policy_name

# NEW
plugin_instance.handler = handler_name
```

Also update all code that reads this attribute:

```python
# In _resolve_plugins_for_upstream and other places
# OLD
plugin_policy = getattr(plugin, 'policy', plugin.__class__.__name__)

# NEW
plugin_handler = getattr(plugin, 'handler', plugin.__class__.__name__)
```

### 4. Update Configuration References

#### Task 4.1: Update configuration field references

In plugin loading methods, change all references from "policy" to "handler":

```python
# OLD
policy_name = plugin_config.get("policy")
if not policy_name:
    logger.error(f"Plugin configuration missing 'policy' field")

# NEW
handler_name = plugin_config.get("handler")
if not handler_name:
    logger.error(f"Plugin configuration missing 'handler' field")
```

This affects:
- `_load_upstream_scoped_security_plugins`
- `_load_upstream_scoped_auditing_plugins`
- `_load_upstream_scoped_middleware_plugins`

#### Task 3.2: Update error messages
Update all error messages to use "handler" terminology:
```python
# OLD
raise ValueError(f"Policy '{policy_name}' not found. Available policies: {available_names}")

# NEW
raise ValueError(f"Handler '{handler_name}' not found. Available handlers: {available_names}")
```

### 5. Update Test Files

#### Task 5.1: Update test configurations
In all test files, update configuration dictionaries:

```python
# OLD
config = {
    "security": {
        "_global": [
            {"policy": "pii", "enabled": True, "config": {}}
        ]
    }
}

# NEW
config = {
    "security": {
        "_global": [
            {"handler": "pii", "enabled": True, "config": {}}
        ]
    }
}
```

Files to update:
- `tests/unit/test_plugin_manager.py`
- `tests/unit/test_plugin_manager_middleware.py`
- `tests/integration/*.py`
- Any other test files with plugin configurations

#### Task 5.2: Update mock plugins in tests

For test plugins that declare POLICIES:
```python
# OLD
class MockSecurityPlugin(SecurityPlugin):
    POLICIES = {"mock_security": "MockSecurityPlugin"}

# NEW
class MockSecurityPlugin(SecurityPlugin):
    HANDLERS = {"mock_security": "MockSecurityPlugin"}
```

#### Task 5.3: Add test for old config rejection

Add a test to ensure old "policy" configuration is explicitly rejected:

```python
def test_old_policy_config_rejected():
    """Test that old 'policy' configuration field triggers clear error."""
    config = {
        "security": {
            "_global": [
                {"policy": "pii", "enabled": True}
            ]
        }
    }
    manager = PluginManager(config)
    with pytest.raises(ValueError, match="deprecated.*'policy'.*'handler'"):
        await manager.load_plugins()

def test_error_message_lists_available_handlers():
    """Test that error messages list available handler names."""
    config = {
        "security": {
            "_global": [
                {"handler": "nonexistent", "enabled": True}
            ]
        }
    }
    manager = PluginManager(config)
    with pytest.raises(ValueError, match="Available handlers:"):
        await manager.load_plugins()
For test plugins that declare POLICIES:
```python
# OLD
class MockSecurityPlugin(SecurityPlugin):
    POLICIES = {"mock_security": "MockSecurityPlugin"}

# NEW
class MockSecurityPlugin(SecurityPlugin):
    HANDLERS = {"mock_security": "MockSecurityPlugin"}
```

### 6. Update Configuration Examples

#### Task 6.1: Update YAML examples
If any example configuration files exist, update them:

```yaml
# OLD
plugins:
  security:
    _global:
      - policy: pii
        enabled: true

# NEW
plugins:
  security:
    _global:
      - handler: pii
        enabled: true
```

### 7. Update Documentation

#### Task 7.1: Update code comments
Search for comments mentioning "policy" or "policies" in plugin context and update to "handler"/"handlers"

#### Task 7.2: Update docstrings

Update docstrings in the plugin manager and interfaces:
```python
# OLD
"""Load security policies from configuration."""

# NEW
"""Load security handlers from configuration."""
```

#### Task 7.3: Update structured logging fields

Search for and update any structured logging that uses policy terminology:

```python
# OLD
logger.info("Loading plugin", extra={"policy_name": name})

# NEW
logger.info("Loading plugin", extra={"handler_name": name})
```

#### Task 7.4: Create ADR-020

Document the rationale for this change in `docs/decision-records/020-handler-nomenclature.md`
Update docstrings in the plugin manager and interfaces:
```python
# OLD
"""Load security policies from configuration."""

# NEW
"""Load security handlers from configuration."""
```

### 8. Backward Compatibility Considerations

Since this is v0.1.0 with no backward compatibility requirements, we can make this a clean break. However, for user-friendliness, consider adding a helpful error message during the transition:

```python
# In plugin loading, check for old format
if "policy" in plugin_config and "handler" not in plugin_config:
    raise ValueError(
        f"Configuration uses deprecated 'policy' field. "
        f"Please update to 'handler': {plugin_config.get('policy')}"
    )
```

## Testing Checklist

1. [ ] All existing tests pass with new nomenclature
2. [ ] Plugin discovery works with HANDLERS manifest
3. [ ] Configuration loading uses "handler" field
4. [ ] Old "policy" configuration triggers explicit error with guidance
5. [ ] Error messages reference "handlers" not "policies"
6. [ ] Error messages list available handler names
7. [ ] No references to POLICIES remain in codebase
8. [ ] No references to plugin.policy attribute remain
9. [ ] Mock plugins in tests use HANDLERS
10. [ ] Structured logging uses handler_name not policy_name

## Validation

Run these commands to verify the change is complete:

```bash
# Should return no results (except this file and migration helper)
grep -r "POLICIES" gatekit/
grep -r "\.policy" gatekit/
grep -r "policy_name" gatekit/
grep -r "'policy'" gatekit/ | grep -v "security policy"
grep -r '"policy"' gatekit/ | grep -v "security policy"

# Should return results
grep -r "HANDLERS" gatekit/
grep -r "\.handler" gatekit/
grep -r "handler_name" gatekit/
grep -r "'handler'" gatekit/

# All tests should pass
pytest tests/

# Specific test for config rejection
pytest -k "test_old_policy_config_rejected"
```

## Migration Script (Optional)

For users upgrading their configurations, provide a simple script:

```python
#!/usr/bin/env python3
"""Migrate Gatekit configuration from policy to handler format."""

import yaml
import sys

def migrate_config(config):
    """Migrate policy -> handler in configuration."""
    if 'plugins' in config:
        for category in ['security', 'auditing', 'middleware']:
            if category in config['plugins']:
                for upstream, plugins in config['plugins'][category].items():
                    for plugin in plugins:
                        if 'policy' in plugin:
                            plugin['handler'] = plugin.pop('policy')
                            print(f"Migrated {category}.{upstream} plugin to use 'handler'")
    return config

if __name__ == '__main__':
    with open(sys.argv[1], 'r') as f:
        config = yaml.safe_load(f)
    
    migrated = migrate_config(config)
    
    with open(sys.argv[1] + '.migrated', 'w') as f:
        yaml.dump(migrated, f, default_flow_style=False)
    
    print(f"Migrated configuration saved to {sys.argv[1]}.migrated")
```

## Success Criteria

- No references to POLICIES in plugin code (only HANDLERS)
- No references to "policy" in configuration field names (only "handler")
- No references to plugin.policy attribute (only plugin.handler)
- Old configuration explicitly rejected with helpful error message
- All tests pass with the new nomenclature
- Structured logging uses handler terminology
- ADR-020 documents the rationale
- Code is more semantically accurate and clear