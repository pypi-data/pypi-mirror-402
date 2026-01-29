# Tool Allowlist Configuration Cleanup

## Overview

Clean up the Tool Allowlist plugin's configuration inconsistencies by removing useless modes, prohibiting nonsensical global configuration, and simplifying the configuration structure.

## Problem Statement

The Tool Allowlist plugin currently has several issues:

1. **Useless `allow_all` mode**: Functionally identical to disabling the plugin
2. **Contradictory global configuration**: Can be placed in `_global` section but requires server-specific tool names
3. **Confusing nested structure**: When configured per-server, still requires nested server name mapping

Current problematic configuration:
```yaml
plugins:
  security:
    _global:  # Contradictory!
      - policy: tool_allowlist
        config:
          mode: allow_all  # Useless!
          tools:
            filesystem: ["read_file"]  # Server-specific in global!
```

## Proposed Solution

### 1. Remove `allow_all` Mode

The `allow_all` mode is pointless - users should just disable the plugin instead.

**Before:**
```yaml
- policy: tool_allowlist
  enabled: true
  config:
    mode: allow_all
```

**After:**
```yaml
- policy: tool_allowlist
  enabled: false  # Just disable it!
```

### 2. Prohibit Global Configuration

Tool Allowlist should NOT be allowed in `_global` section because:
- Tool names are server-specific
- No meaningful "global" tool allowlist exists
- Configuration requires server context

### 3. Simplify Server Configuration Structure

**Before (confusing nested structure):**
```yaml
plugins:
  security:
    filesystem:
      - policy: tool_allowlist
        config:
          mode: allowlist
          tools:
            filesystem: ["read_file", "write_file"]  # Redundant nesting!
```

**After (simplified structure):**
```yaml
plugins:
  security:
    filesystem:
      - policy: tool_allowlist
        config:
          mode: allowlist
          tools: ["read_file", "write_file"]  # Server is implied!
```

## Implementation Tasks

### Phase 1: Remove `allow_all` Mode
- [ ] Remove `allow_all` from valid modes in `ToolAllowlistPlugin`
- [ ] Update mode validation to only accept `allowlist` and `blocklist`
- [ ] Update error messages to suggest disabling plugin instead
- [ ] Update all tests that use `allow_all` mode

### Phase 2: Prohibit Global Configuration
- [ ] Add validation in PluginManager to reject tool_allowlist in `_global`
- [ ] Add clear error message explaining why it's not allowed
- [ ] Update configuration validation tests
- [ ] Remove any existing tests that put tool_allowlist in `_global`

### Phase 3: Simplify Configuration Structure
- [ ] Update `ToolAllowlistPlugin` to accept flat tool list when in server context
- [ ] Maintain backward compatibility during transition
- [ ] Update `describe_status()` method to work with simplified structure
- [ ] Add configuration migration guidance

### Phase 4: Update Plugin Scope
- [x] Change `DISPLAY_SCOPE = "server_aware"` (completed with 1-plugin-scope-refactor)
- [ ] Update `describe_status()` to reflect server-aware nature
- [ ] Remove logic that tries to handle global configuration

### Phase 5: Update Documentation and Tests
- [ ] Update all test cases to use new configuration format
- [ ] Add tests for new validation rules
- [ ] Update configuration examples in documentation
- [ ] Add migration guide for existing configurations

### Phase 6: Configuration Migration Support
- [ ] Add deprecation warnings for old configuration format
- [ ] Provide automatic migration logic where possible
- [ ] Document breaking changes clearly

## Configuration Examples

### Valid Configurations (After Changes)

```yaml
plugins:
  security:
    # Global plugins only
    _global:
      - policy: pii
      - policy: secrets
      
    # Server-aware plugins in server sections
    filesystem:
      - policy: tool_allowlist
        config:
          mode: allowlist
          tools: ["read_file", "list_directory"]
          
    github:
      - policy: tool_allowlist
        config:
          mode: blocklist
          tools: ["dangerous_operation"]
```

### Invalid Configurations (Will Be Rejected)

```yaml
plugins:
  security:
    _global:
      - policy: tool_allowlist  # ERROR: Not allowed in global!
        config:
          mode: allowlist
          tools: ["some_tool"]
          
    filesystem:
      - policy: tool_allowlist
        config:
          mode: allow_all  # ERROR: Mode removed!
```

## Breaking Changes

1. **`allow_all` mode removal** - Replace with `enabled: false`
2. **Global configuration prohibition** - Move to server sections
3. **Configuration structure simplification** - Remove nested server names

## Migration Guide

### For `allow_all` Mode Users
**Before:**
```yaml
- policy: tool_allowlist
  config:
    mode: allow_all
```

**After:**
```yaml
# Just remove the plugin or set enabled: false
```

### For Global Configuration Users
**Before:**
```yaml
plugins:
  security:
    _global:
      - policy: tool_allowlist
        config:
          mode: allowlist
          tools:
            server1: ["tool1", "tool2"]
            server2: ["tool3"]
```

**After:**
```yaml
plugins:
  security:
    server1:
      - policy: tool_allowlist
        config:
          mode: allowlist
          tools: ["tool1", "tool2"]
    server2:
      - policy: tool_allowlist
        config:
          mode: allowlist
          tools: ["tool3"]
```

## Dependencies

- Depends on `plugin-scope-refactor` for new scope categories (✅ completed in todos-completed/)

## Success Metrics

- [ ] No useless `allow_all` mode confusing users
- [ ] No contradictory global configurations
- [ ] Simplified, intuitive configuration structure
- [ ] Clear error messages for invalid configurations
- [ ] All tests pass with new structure