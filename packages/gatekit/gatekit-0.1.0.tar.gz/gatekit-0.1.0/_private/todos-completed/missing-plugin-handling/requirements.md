# Missing Plugin Handling

## Problem Description

**Issue**: Configuration validation fails with "Path validation error" when a plugin referenced in the configuration file is not available due to being disabled, removed, or failing to load.

**Discovery Context**:
- During TUI dynamic height testing, commenting out plugin POLICIES caused configuration validation errors
- The error occurs because `gatekit.yaml` references plugins that are no longer discoverable

## Current Behavior

1. **Configuration File**: Contains plugin configurations (e.g., `policy: "syslog_auditing"`)
2. **Plugin Discovery**: Scans for available plugins via POLICIES manifests
3. **Validation Mismatch**: Configuration validator tries to validate plugins that don't exist
4. **Result**: "Path validation error" in TUI, configuration loading fails

## Technical Details

**Example Scenario**:
```yaml
# In gatekit.yaml
plugins:
  auditing:
    _global:
      - policy: "syslog_auditing"  # ← References this plugin
        enabled: true
        config:
          facility: "local0"
```

```python
# In syslog.py
# POLICIES = {  # ← Plugin commented out/disabled
#     "syslog_auditing": SyslogAuditingPlugin
# }
```

**Error Flow**:
1. Configuration loader reads `gatekit.yaml`
2. Finds reference to `"syslog_auditing"` plugin
3. Attempts to validate plugin configuration
4. Plugin discovery returns empty (plugin not available)
5. Validation fails → "Path validation error"

## Impact

**Current Impact**:
- Configuration files become "brittle" - removing/disabling plugins breaks configs
- No graceful degradation when plugins are unavailable
- Difficult to test plugin subsets or debug individual plugins
- Poor user experience when plugins fail to load

**Affected Areas**:
- TUI configuration editor
- Configuration file validation
- Plugin development and testing workflows
- System upgrades that might remove plugins

## Potential Solutions (Not Implemented)

**Option 1: Graceful Plugin Missing Handling**
- Detect missing plugins during validation
- Show warnings but allow configuration to load
- Disable/skip missing plugin configurations
- Log missing plugins for user awareness

**Option 2: Configuration Validation Modes**
- `strict`: Current behavior (fail on missing plugins)
- `permissive`: Warn but continue with available plugins
- `development`: Allow missing plugins for testing

**Option 3: Plugin Availability Metadata**
- Track which plugins are "core" vs "optional"
- Different handling based on plugin type
- Better error messages for missing core plugins

**Option 4: Configuration Repair Tools**
- Auto-detect and comment out missing plugin references
- Suggest alternative plugins for missing ones
- Interactive configuration repair in TUI

## Related Areas

- Configuration validation system
- Plugin discovery and loading
- TUI error handling and user experience
- Plugin development workflows
- System robustness and graceful degradation

## Priority

**Medium** - Not blocking current functionality but affects:
- Developer experience during plugin testing
- System robustness in production
- User experience when plugins are unavailable
- Future plugin ecosystem development

## Notes

- This issue was discovered during dynamic height testing but represents a broader system design consideration
- The current "fail fast" behavior may be intentional for production safety
- Solution should balance safety (don't silently ignore important plugins) with usability (graceful degradation)
- Consider impact on both development and production use cases