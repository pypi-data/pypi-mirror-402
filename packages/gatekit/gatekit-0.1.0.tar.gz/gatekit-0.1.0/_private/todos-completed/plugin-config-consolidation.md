# Plugin Configuration Consolidation

## Problem Statement

### Current Architecture Issues

The current plugin configuration architecture has a split between **wrapper metadata** and **plugin configuration**:

```yaml
plugins:
  security:
    _global:
      - handler: secrets
        enabled: true      # Wrapper metadata
        priority: 50       # Wrapper metadata
        config:            # Plugin-specific config
          action: block
          secret_types: {...}
```

This split creates significant complexity and bugs:

1. **TUI State Management Bug**: When users toggle plugin enabled state via checkbox, then open the config modal, the modal shows incorrect state because:
   - Schema defaults (`enabled: true`) conflict with wrapper state (`enabled: false`)
   - Split/inject pattern creates state sync issues

2. **Code Complexity**: TUI requires complex split/inject patterns:
   - `_build_modal_config()` injects wrapper fields into config dict
   - `_split_priority_from_config()` extracts them back out
   - Multiple code paths for global vs server plugins
   - Error-prone state synchronization

3. **Inconsistency**: Field `critical` is already stored in config dict (injected by PluginManager), but `enabled`/`priority` are at wrapper level

4. **Schema Duplication**: Every plugin must define `enabled` and `priority` in their schemas (we just removed this, causing the current bug)

### The Trigger

We removed `enabled`/`priority` from plugin schemas to eliminate duplication. This revealed the fundamental architectural issue: the TUI was injecting wrapper metadata into config for the modal, but now there are no schema definitions for validation/rendering.

## Proposed Solution

### New Architecture

Move `enabled` and `priority` INTO the config dict:

```yaml
plugins:
  security:
    _global:
      - handler: secrets
        config:
          enabled: true     # All configuration in one place
          priority: 50
          action: block
          secret_types: {...}
```

### Key Benefits

1. ✅ **Eliminates TUI complexity** - No more split/inject/extract
2. ✅ **Single source of truth** - All plugin config in one dict
3. ✅ **Fixes state bug** - No conflicting state between wrapper and config
4. ✅ **Consistency** - Aligns with `critical` field pattern
5. ✅ **Simpler mental model** - Users configure "the plugin" not "wrapper vs plugin"
6. ✅ **Framework injection** - Schema fields injected once at framework level

## Technical Approach

### Data Model Changes

**Current:**
```python
@dataclass
class PluginConfig:
    handler: str
    enabled: bool = True
    priority: int = 50
    config: Dict[str, Any] = field(default_factory=dict)
```

**Proposed:**
```python
@dataclass
class PluginConfig:
    handler: str
    config: Dict[str, Any] = field(default_factory=dict)

    @property
    def enabled(self) -> bool:
        return self.config.get("enabled", True)

    @enabled.setter
    def enabled(self, value: bool):
        self.config["enabled"] = value

    @property
    def priority(self) -> int:
        return self.config.get("priority", 50)

    @priority.setter
    def priority(self, value: int):
        if not isinstance(value, int) or not (0 <= value <= 100):
            raise ValueError(f"Priority must be 0-100, got {value}")
        self.config["priority"] = value
```

### Schema Injection Strategy

Modal framework injects framework fields into any plugin schema:

```python
class PluginConfigModal:
    def __init__(self, plugin_class, current_config):
        # Get base schema from plugin
        base_schema = plugin_class.get_json_schema()

        # Framework fields (injected once, not duplicated per plugin)
        framework_fields = {
            "enabled": {
                "type": "boolean",
                "title": "Plugin Enabled",
                "description": "Enable this plugin instance",
                "default": True
            },
            "priority": {
                "type": "integer",
                "title": "Execution Priority",
                "description": "0-100, lower = higher priority",
                "default": 50,
                "minimum": 0,
                "maximum": 100
            }
        }

        # Merge: framework fields FIRST, then plugin fields
        self.json_schema = {
            **base_schema,
            "properties": {
                **framework_fields,
                **base_schema.get("properties", {})
            }
        }
```

### TUI Simplification

**Before (complex):**
```python
# Loading
def _build_modal_config(self, wrapper):
    config_copy = dict(wrapper.config)
    config_copy["priority"] = wrapper.priority  # INJECT
    config_copy["enabled"] = wrapper.enabled    # INJECT
    return config_copy

# Saving
def _split_priority_from_config(self, config):
    config_copy = dict(config)
    priority = config_copy.pop("priority", None)  # EXTRACT
    enabled = config_copy.pop("enabled", None)    # EXTRACT
    return config_copy, priority

# Update separately
plugin.enabled = enabled
plugin.priority = priority
plugin.config = sanitized_config
```

**After (simple):**
```python
# Loading
def _get_plugin_config(self, wrapper):
    return wrapper.config.copy()  # Done!

# Saving
plugin.config = new_config  # Done! Properties handle the rest
```

**Code Elimination:**
- Remove `_build_modal_config`
- Remove `_split_priority_from_config`
- Remove global vs server config path distinction
- Remove all split/inject complexity

## Test-Driven Development Plan

### Phase 1: Write Failing Tests ✅ RED

Create comprehensive test suite that defines expected behavior with new architecture:

#### Test File: `tests/unit/test_plugin_config_consolidation.py`

```python
class TestPluginConfigConsolidation:
    """Test suite for consolidated plugin configuration."""

    def test_plugin_config_enabled_property_access(self):
        """enabled property reads from config dict."""
        config = PluginConfig(handler="test", config={"enabled": False})
        assert config.enabled == False

    def test_plugin_config_enabled_property_setter(self):
        """enabled property writes to config dict."""
        config = PluginConfig(handler="test", config={})
        config.enabled = False
        assert config.config["enabled"] == False

    def test_plugin_config_priority_property_access(self):
        """priority property reads from config dict."""
        config = PluginConfig(handler="test", config={"priority": 20})
        assert config.priority == 20

    def test_plugin_config_priority_property_setter(self):
        """priority property writes to config dict."""
        config = PluginConfig(handler="test", config={})
        config.priority = 30
        assert config.config["priority"] == 30

    def test_plugin_config_priority_validation(self):
        """priority property validates range."""
        config = PluginConfig(handler="test", config={})
        with pytest.raises(ValueError):
            config.priority = 101  # > 100
        with pytest.raises(ValueError):
            config.priority = -1   # < 0

    def test_plugin_config_defaults(self):
        """enabled and priority have sensible defaults."""
        config = PluginConfig(handler="test", config={})
        assert config.enabled == True
        assert config.priority == 50

    def test_yaml_round_trip_new_format(self):
        """Config can be saved and loaded in new format."""
        yaml_content = """
plugins:
  security:
    _global:
      - handler: secrets
        config:
          enabled: true
          priority: 10
          action: block
"""
        config = load_config_from_yaml(yaml_content)
        plugin = config.plugins.security["_global"][0]
        assert plugin.enabled == True
        assert plugin.priority == 10
        assert plugin.config["action"] == "block"
```

#### Test File: `tests/unit/tui/test_plugin_modal_consolidation.py`

```python
class TestPluginModalConsolidation:
    """Test that modal handles consolidated config correctly."""

    def test_modal_no_split_inject_needed(self):
        """Modal receives config directly without injection."""
        wrapper = PluginConfig(
            handler="secrets",
            config={"enabled": True, "priority": 50, "action": "block"}
        )

        # Modal should receive config as-is
        modal_config = get_modal_config(wrapper)
        assert modal_config == wrapper.config
        assert "enabled" in modal_config
        assert "priority" in modal_config

    def test_modal_framework_field_injection(self):
        """Modal injects framework fields into schema."""
        modal = PluginConfigModal(BasicSecretsFilterPlugin, {})
        schema = modal.json_schema

        # Framework fields should be present
        assert "enabled" in schema["properties"]
        assert "priority" in schema["properties"]

        # Plugin fields should also be present
        assert "action" in schema["properties"]

        # Framework fields should come first (ordering)
        props_list = list(schema["properties"].keys())
        assert props_list.index("enabled") < props_list.index("action")
        assert props_list.index("priority") < props_list.index("action")

    def test_modal_save_no_extraction_needed(self):
        """Modal saves config directly without extraction."""
        wrapper = PluginConfig(handler="secrets", config={})
        new_config = {
            "enabled": False,
            "priority": 30,
            "action": "redact"
        }

        # Should update config directly
        wrapper.config = new_config
        assert wrapper.enabled == False
        assert wrapper.priority == 30
        assert wrapper.config["action"] == "redact"

    def test_modal_state_consistency(self):
        """Modal shows consistent state with wrapper."""
        wrapper = PluginConfig(
            handler="secrets",
            config={"enabled": False, "priority": 10}
        )

        # Modal should show same state
        modal_config = get_modal_config(wrapper)
        assert modal_config["enabled"] == False
        assert modal_config["enabled"] == wrapper.enabled  # Consistent!
```

#### Test File: `tests/unit/test_config_loading_consolidation.py`

```python
class TestConfigLoadingConsolidation:
    """Test config loader handles new consolidated format."""

    def test_load_new_format_directly(self):
        """New format loads with enabled/priority in config dict."""
        yaml_content = """
plugins:
  security:
    _global:
      - handler: secrets
        config:
          enabled: true
          priority: 50
          action: block
"""
        config = load_config_from_yaml(yaml_content)
        plugin = config.plugins.security["_global"][0]
        assert plugin.config["enabled"] == True
        assert plugin.config["priority"] == 50
        assert plugin.config["action"] == "block"

    def test_plugin_manager_instantiation(self):
        """PluginManager gets config with enabled/priority."""
        plugin_config = PluginConfig(
            handler="secrets",
            config={"enabled": True, "priority": 30, "action": "block"}
        )

        # Plugin receives full config
        manager = PluginManager({"security": {"_global": [plugin_config]}})
        # Plugin __init__ should receive config with enabled/priority
        # Base class extracts priority: self.priority = config.get("priority", 50)

    def test_old_format_not_supported(self):
        """Old format with top-level enabled/priority is not supported."""
        yaml_content = """
plugins:
  security:
    _global:
      - handler: secrets
        enabled: false
        priority: 20
        config:
          action: block
"""
        # This should fail validation or raise an error
        with pytest.raises((ValidationError, ValueError)):
            config = load_config_from_yaml(yaml_content)
```

### Phase 2: Update Data Model ⚙️ REFACTOR

Update `PluginConfig` to use properties:

**File**: `gatekit/config/models.py`
- Convert `enabled` and `priority` to `@property` decorators
- Add setters with validation
- Remove field declarations
- Add defaults in property getters

**Note**: No changes needed to `gatekit/config/loader.py` - it will naturally load the new format since enabled/priority will be in the config dict like any other field.

### Phase 3: Update Config Loading/Saving 🔧 GREEN

Simplify TUI configuration handling:

1. **File**: `gatekit/tui/screens/config_editor/plugin_actions.py`
   - Remove `_build_modal_config()` - no longer needed
   - Remove `_split_priority_from_config()` - no longer needed
   - Simplify `_get_global_plugin_config()` - just return config
   - Simplify `_get_server_plugin_config()` - just return config

2. **File**: `gatekit/tui/screens/config_editor/plugin_rendering.py`
   - Update `_get_current_plugin_config()` - simplified
   - Remove injection logic

3. **File**: `gatekit/tui/screens/config_editor/base.py`
   - Simplify save logic in handlers
   - Direct config assignment, no splitting

### Phase 4: Framework Schema Injection 🎨 REFACTOR

Add schema injection to modal framework:

1. **File**: `gatekit/tui/screens/plugin_config/modal.py`
   - Update `__init__()` to inject framework fields
   - Define framework field schemas (enabled, priority)
   - Merge with plugin schema
   - Ensure framework fields appear first

2. **Validation**:
   - Framework fields validated by injected schema
   - Plugin fields validated by plugin schema
   - No duplication across plugins

### Phase 5: Cleanup and Validation ✅ GREEN

1. **Remove dead code**:
   - Delete `_build_modal_config`
   - Delete `_split_priority_from_config`
   - Remove any wrapper-splitting logic

2. **Update all tests**:
   - Fix tests expecting old structure
   - Ensure all tests pass
   - Add tests for edge cases

3. **Documentation**:
   - Update CLAUDE.md with new structure
   - Update configuration examples
   - Update example configs with new format

4. **Verify bug fix**:
   - Test TUI: toggle plugin off, open modal, verify state matches
   - Test TUI: modify priority in modal, verify saves correctly
   - Test round-trip: save config, reload, verify consistency

## No Migration Required

**IMPORTANT**: This is the first release (v0.1.0), so **NO backward compatibility is required**.

- No migration logic needed in config loader
- No support for old format
- Clean break with simpler architecture
- Users updating from v0.1.0 will need to manually update their configs (or we provide a migration script if needed)

The old format:
```yaml
plugins:
  security:
    _global:
      - handler: secrets
        enabled: true      # OLD: at wrapper level
        priority: 50       # OLD: at wrapper level
        config:
          action: block
```

The new format:
```yaml
plugins:
  security:
    _global:
      - handler: secrets
        config:
          enabled: true    # NEW: in config dict
          priority: 50     # NEW: in config dict
          action: block
```

## Success Criteria

- ✅ All tests pass (existing + new)
- ✅ TUI state bug is fixed (modal shows correct enabled state)
- ✅ Code complexity reduced (split/inject code eliminated)
- ✅ Schema injection works (framework fields in all modals)
- ✅ YAML round-trip works (save/load preserves state)
- ✅ No test regressions
- ✅ Example configs updated to new format

## Implementation Checklist

### Phase 1: Write Failing Tests
- [ ] Create `tests/unit/test_plugin_config_consolidation.py`
- [ ] Create `tests/unit/tui/test_plugin_modal_consolidation.py`
- [ ] Create `tests/unit/test_config_loading_consolidation.py`
- [ ] Run tests - verify they fail (RED)

### Phase 2: Update Data Model
- [ ] Convert `PluginConfig.enabled` to property
- [ ] Convert `PluginConfig.priority` to property
- [ ] Add validation in setters
- [ ] Add defaults in getters
- [ ] Update type hints

### Phase 3: Update Config Loading/Saving
- [ ] Remove `_build_modal_config()` from TUI
- [ ] Remove `_split_priority_from_config()` from TUI
- [ ] Simplify config retrieval methods
- [ ] Simplify config save methods
- [ ] Update `tests/validation/validation-config.yaml` to new format
- [ ] Update `configs/gatekit.yaml` to new format
- [ ] Run tests - verify progress (some GREEN)

### Phase 4: Framework Schema Injection
- [ ] Add framework field definitions to modal
- [ ] Implement schema merging logic
- [ ] Ensure field ordering (framework first)
- [ ] Test schema injection with multiple plugins
- [ ] Run tests - verify more GREEN

### Phase 5: Cleanup and Validation
- [ ] Remove all split/inject helper methods
- [ ] Fix any remaining test failures
- [ ] Verify TUI bug is fixed manually
- [ ] Update documentation
- [ ] Run full test suite - ALL GREEN
- [ ] Final verification of bug fix

## Files to Modify

### Core Data Model
- `gatekit/config/models.py` - PluginConfig properties (add @property decorators)

### TUI Code (Simplification)
- `gatekit/tui/screens/config_editor/plugin_actions.py` - Remove split/inject
- `gatekit/tui/screens/config_editor/plugin_rendering.py` - Simplify config access
- `gatekit/tui/screens/config_editor/base.py` - Simplify save handlers
- `gatekit/tui/screens/plugin_config/modal.py` - Framework injection

### Tests (New + Updates)
- `tests/unit/test_plugin_config_consolidation.py` - New
- `tests/unit/tui/test_plugin_modal_consolidation.py` - New
- `tests/unit/test_config_loading_consolidation.py` - New
- Various existing tests - Update to new structure

### Example Configs (Update to New Format)
- `tests/validation/validation-config.yaml` - Update all plugin configs
- `configs/gatekit.yaml` - Update all plugin configs

## Risks and Mitigation

### Risk: Breaking existing configs
**Mitigation**: This is v0.1.0 (first release) - no backward compatibility required. Clean break is acceptable.

### Risk: Property access performance
**Mitigation**: Dict access is fast, no measurable impact

### Risk: Incomplete test coverage
**Mitigation**: Comprehensive test suite (Phase 1) covers all scenarios before implementation

### Risk: TUI complexity elsewhere
**Mitigation**: Careful code review, incremental changes, test coverage

## Current Status

**Phase**: Not Started
**Next Action**: Begin Phase 1 (write failing tests)
**Blocked By**: None

## Notes

This refactoring addresses a fundamental architectural issue discovered when fixing schema duplication. Moving `enabled` and `priority` into the config dict creates a simpler, more maintainable architecture with a single source of truth for plugin configuration.

The TDD approach ensures we don't break existing functionality while making this significant structural change.
