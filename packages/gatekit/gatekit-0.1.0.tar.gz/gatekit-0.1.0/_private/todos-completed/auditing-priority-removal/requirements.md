# Remove Priority from Auditing Plugins - Implementation Requirements

## Overview
Remove the priority field from auditing plugins to simplify the plugin architecture. Auditing plugins will continue to run sequentially but without priority-based ordering, since their execution order doesn't affect outcomes.

## Rationale

### Why Priority Doesn't Make Sense for Auditing
1. **No interdependencies**: Audit plugins don't depend on each other's output
2. **Immutable input**: All receive the same data that cannot be modified
3. **No blocking**: One audit plugin can't prevent another from running
4. **Independent destinations**: Each typically writes to its own log file/system
5. **Order irrelevance**: The sequence of audit logging doesn't affect correctness

### Why We're Keeping Sequential Execution
- **Simpler implementation**: No threading complexity or async confusion
- **Predictable behavior**: Easy to understand and debug
- **No fake parallelism**: Honest about what's actually happening (file I/O blocks anyway)
- **Good enough performance**: Auditing is not typically a bottleneck

## User Messaging

### Before (Confusing)
> "Gatekit has separate priority systems for security/middleware plugins (0-100) and auditing plugins (0-100)."

### After (Clear)
> "Gatekit has ONE priority system (0-100) that controls processing order for middleware and security plugins. Auditing plugins run after processing completes without priority-based ordering since their execution order doesn't matter."

## Implementation Tasks

### 1. Update AuditingPlugin Base Class

#### Location: `gatekit/plugins/interfaces.py`

#### Task 1.1: Override priority initialization
Keep PluginInterface unchanged but override in AuditingPlugin:

```python
class AuditingPlugin(PluginInterface):
    """Abstract base class for auditing plugins.
    
    Auditing plugins observe the complete processing pipeline for security
    monitoring, compliance, and debugging purposes. They execute sequentially
    after message processing completes, but do not use priority ordering.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize auditing plugin with configuration.
        
        Args:
            config: Plugin-specific configuration dictionary
        """
        # Call parent to maintain interface compatibility
        super().__init__(config)
        
        # Remove priority attribute for auditing plugins
        if hasattr(self, 'priority'):
            delattr(self, 'priority')
        
        # Auditing plugins never block processing
        self.critical = False  # Always false for audit plugins
```

### 2. Update Plugin Manager

#### Location: `gatekit/plugins/manager.py`

#### Task 2.1: Remove priority sorting for audit plugins
In the `_load_upstream_scoped_auditing_plugins` method:

```python
def _load_upstream_scoped_auditing_plugins(self, auditing_config: Dict[str, List[Dict[str, Any]]]) -> None:
    """Load auditing plugins from upstream-scoped configuration.
    
    Note: Auditing plugins are not sorted by priority as their order doesn't matter.
    """
    # ... existing loading code ...
    
    # Remove this line:
    # upstream_plugins.sort(key=lambda p: getattr(p, 'priority', 50))
    
    # Just store them in the order they're defined
    self.upstream_auditing_plugins[upstream_name] = upstream_plugins
    
    # Log warning if priority is specified
    for plugin_config in plugin_configs:
        if 'priority' in plugin_config.get('config', {}):
            policy_name = plugin_config.get('policy', 'unknown')
            logger.warning(
                f"Priority field ignored for audit plugin '{policy_name}' - "
                "audit plugins do not use priority ordering"
            )
```

#### Task 2.2: Update audit methods to handle missing priority
Keep the existing sequential execution but make it resilient to missing priority:

```python
async def audit_request(self, request: MCPRequest, decision: PolicyDecision, server_name: Optional[str] = None) -> None:
    """Send request and decision to auditing plugins sequentially.
    
    Audit plugins execute in the order they're defined (not by priority).
    Failures are logged but don't block processing or other audit plugins.
    
    Args:
        request: The MCP request that was processed
        decision: The security decision made
        server_name: Name of the target server
    """
    if not self._initialized:
        await self.load_plugins()
    
    # Get upstream-specific auditing plugins (no sorting needed)
    upstream_plugins = self.get_plugins_for_upstream(server_name or "unknown")
    auditing_plugins = upstream_plugins["auditing"]
    
    # Execute sequentially in definition order
    for plugin in auditing_plugins:
        try:
            await plugin.log_request(request, decision, server_name)
            logger.debug(f"Audit plugin {plugin.plugin_id} logged request")
        except Exception as e:
            # Audit failures never block processing
            logger.error(
                f"Audit plugin {plugin.plugin_id} failed: {e}", 
                exc_info=True
            )
```

#### Task 2.3: Update _resolve_plugins_for_upstream
Make the method handle plugins without priority gracefully:

```python
def _resolve_plugins_for_upstream(self, plugin_map: Dict[str, List[T]], 
                                  upstream_name: str) -> List[T]:
    """Resolve plugins for a specific upstream, with fallback to _global.
    
    Args:
        plugin_map: Mapping of upstream names to plugin lists
        upstream_name: Name of the upstream to get plugins for
    
    Returns:
        List of plugins for the upstream (security/middleware sorted by priority,
        auditing unsorted)
    """
    # ... existing resolution logic ...
    
    # Only sort if plugins have priority attribute (security/middleware)
    if plugins and hasattr(plugins[0], 'priority'):
        plugins.sort(key=lambda p: getattr(p, 'priority', 50))
    
    return plugins
```

### 3. Update Configuration Validation

#### Location: `gatekit/config/models.py` or validation logic

#### Task 3.1: Log warning for audit plugin priority
Don't reject priority in audit configs but warn about it:

```python
def validate_plugin_config(plugin_type: str, config: Dict[str, Any]) -> None:
    """Validate plugin configuration based on type.
    
    Args:
        plugin_type: Type of plugin ('security', 'middleware', 'auditing')
        config: Plugin configuration dictionary
    """
    if plugin_type == 'auditing' and 'priority' in config:
        policy_name = config.get('policy', 'unknown')
        logger.warning(
            f"Configuration warning: Priority field for audit plugin '{policy_name}' "
            "will be ignored. Audit plugins do not use priority ordering."
        )
```

### 4. Update Existing Audit Plugins

#### Location: `gatekit/plugins/auditing/*.py`

#### Task 4.1: Remove priority from get_config_schema
For each audit plugin, remove priority from the configuration schema:

```python
@classmethod
def get_config_schema(cls) -> Dict[str, Any]:
    """Return configuration schema for audit plugin."""
    return {
        "enabled": {
            "type": "boolean",
            "label": "Enable audit logging",
            "default": True,
            "required": True
        },
        # Remove priority field from schema
        # "priority": { ... }  # DELETE THIS
        
        "output_file": {
            "type": "string",
            "label": "Path to audit log file",
            "default": "audit.log",
            "required": True
        },
        # ... other config fields ...
    }
```

### 5. Update Configuration Examples

#### Task 5.1: Update example YAML files
Remove or comment out priority in audit plugin configurations:

```yaml
plugins:
  middleware:
    _global:
      - policy: response_enricher
        priority: 10  # Priority controls execution order
        
  security:
    _global:
      - policy: pii_filter
        priority: 50  # Runs after middleware
        
  auditing:
    _global:
      # Note: Audit plugins don't use priority - they run in definition order
      - policy: json_lines
        # priority: 10  # Ignored if specified
        config:
          output_file: audit.jsonl
          
      - policy: human_readable  
        config:
          output_file: human.log
```

### 6. Update Documentation

#### Location: `docs/plugins/auditing.md`

#### Task 6.1: Document the lack of priority
Update documentation to explain auditing doesn't use priority:

```markdown
# Auditing Plugins

Auditing plugins observe and log all message processing in Gatekit. Unlike middleware and security plugins which execute in priority order, **audit plugins do not use priority** and execute in the order they are defined.

## Execution Order

Audit plugins run sequentially after all security/middleware processing completes. The order of execution is determined by:
- The order they appear in configuration (for same upstream)
- No priority-based sorting is applied

This is because:
- Audit plugins cannot modify data
- They don't depend on each other
- Their order doesn't affect outcomes
- Each writes to independent destinations

## Configuration

```yaml
plugins:
  auditing:
    _global:
      # These run in the order defined - no priority field needed
      - policy: json_lines
        config:
          output_file: audit.jsonl
      - policy: human_readable
        config:
          output_file: human.log
```

If you specify a `priority` field for an audit plugin, it will be ignored with a warning.
```

### 7. Update Tests

#### Location: `tests/unit/test_audit_plugins.py`

#### Task 7.1: Test that priority is ignored
Add tests to verify audit plugins work without priority:

```python
class TestAuditPluginPriority:
    """Test that audit plugins don't use priority."""
    
    def test_audit_plugin_no_priority_attribute(self):
        """Verify audit plugins don't have priority attribute."""
        plugin = JsonAuditingPlugin({"enabled": True})
        assert not hasattr(plugin, 'priority')
    
    def test_audit_plugin_priority_ignored_with_warning(self, caplog):
        """Verify priority in config is ignored with warning."""
        config = {
            "enabled": True,
            "priority": 99,  # Should be ignored
            "output_file": "test.json"
        }
        plugin = JsonAuditingPlugin(config)
        
        # Plugin should work but not have priority
        assert not hasattr(plugin, 'priority')
        
        # Warning should be logged (if validation is done)
        # Check in manager loading or config validation
    
    @pytest.mark.asyncio
    async def test_audit_plugins_run_in_definition_order(self):
        """Verify audit plugins execute in configuration order."""
        call_order = []
        
        class OrderTrackingPlugin(AuditingPlugin):
            def __init__(self, name):
                super().__init__({"enabled": True})
                self.name = name
                
            async def log_request(self, request, decision, server_name):
                call_order.append(self.name)
        
        # Create plugins in specific order
        plugin_a = OrderTrackingPlugin("A")
        plugin_b = OrderTrackingPlugin("B")
        plugin_c = OrderTrackingPlugin("C")
        
        manager = PluginManager({})
        manager.upstream_auditing_plugins["test"] = [plugin_a, plugin_b, plugin_c]
        
        # They should execute in the order they were added
        await manager.audit_request(request, decision, "test")
        assert call_order == ["A", "B", "C"]
```

### 8. Check for Priority Dependencies

#### Task 8.1: Audit codebase for .priority references
Search for any code that accesses `.priority` on audit plugins:

```bash
# Find potential issues
grep -r "\.priority" --include="*.py" | grep -i audit
```

Areas to check:
- TUI display components
- Status reporting
- Plugin listing/introspection
- Any sorting operations

## Migration Guide

### For Users

If you have audit plugins with priority in your config:

**Before:**
```yaml
auditing:
  _global:
    - policy: json_lines
      priority: 10  # This will be ignored
```

**After:**
```yaml
auditing:
  _global:
    - policy: json_lines  # No priority needed
```

The priority field will be ignored with a warning but won't break functionality.

### For Plugin Developers

Audit plugins should not expect or use priority:

```python
class MyAuditPlugin(AuditingPlugin):
    def __init__(self, config):
        super().__init__(config)
        # Don't use self.priority - it won't exist
        # Don't sort based on priority
```

## Testing Checklist

1. [ ] Audit plugins work without priority attribute
2. [ ] Priority in audit config generates warning but doesn't break
3. [ ] Audit plugins execute in definition order
4. [ ] Plugin manager handles missing priority gracefully
5. [ ] No AttributeError when accessing audit plugins
6. [ ] Configuration validation warns about audit priority
7. [ ] Documentation updated to explain no priority
8. [ ] TUI/status displays work without audit priority

## Success Criteria

The implementation is successful when:
1. Audit plugins have no priority attribute
2. Audit plugins execute sequentially in definition order
3. Priority in audit config generates warning but doesn't break
4. Documentation clearly explains ONE priority system (middleware/security only)
5. All tests pass with audit plugins lacking priority
6. No regression in audit functionality

## Benefits

This change provides:
- **Cleaner mental model**: ONE priority system for processing order only
- **Simpler configuration**: No need to assign meaningless priority to audit plugins
- **Less confusion**: Clear when priority matters (processing) vs when it doesn't (observation)
- **Easier maintenance**: Less complexity in the plugin system
- **Honest implementation**: No false parallelism, just simple sequential execution