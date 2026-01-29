# Global vs Server Configuration Clarification

## Overview

Document and clarify the `_global` configuration behavior patterns, especially the differences between how security and auditing plugins work with global vs server-specific configurations.

## Problem Statement

The current documentation doesn't clearly explain:
- How `_global` configuration interacts with server-specific configuration
- Why security and auditing plugins have different global behavior patterns  
- Which plugins can be configured globally vs server-specifically
- How to show partial enablement in the TUI

## Current Behavior (Needs Documentation)

### Security Plugins - Flexible Scoping
Security plugins can be configured in multiple ways:

1. **Global only** - Applies to all servers
```yaml
plugins:
  security:
    _global:
      - policy: pii
        enabled: true
```

2. **Server-specific only** - Applies to subset of servers
```yaml
plugins:
  security:
    filesystem:
      - policy: pii
        enabled: true
    # Not configured for other servers
```

3. **Mixed configuration** - Global + server overrides
```yaml
plugins:
  security:
    _global:
      - policy: pii
        enabled: true
        config:
          action: redact
    filesystem:
      - policy: pii  
        enabled: true
        config:
          action: block  # Override global setting
```

### Auditing Plugins - Simpler Global Model
Auditing plugins have simpler behavior:
- When in `_global`: Always apply to ALL servers
- Server-specific auditing is less common
- No complex override behavior needed

### Plugin Categories and Global Behavior

Based on the new scope categories:

1. **Global scope plugins** - CAN be in `_global`
   - PII Filter, Secrets Filter, Prompt Injection Defense
   - All auditing plugins
   
2. **Server-aware plugins** - CANNOT be in `_global`
   - Tool Allowlist (needs server-specific tool names)
   
3. **Server-specific plugins** - CANNOT be in `_global`
   - Filesystem Server Security (only works with specific servers)

## Documentation Tasks

### Phase 1: Document Global Configuration Patterns
- [ ] Create comprehensive examples of valid configuration patterns
- [ ] Explain additive vs override behavior for mixed configurations
- [ ] Document which plugin types can use each pattern
- [ ] Clarify security vs auditing plugin differences

### Phase 2: Document Plugin Category Rules
- [ ] Create table showing which plugins can be configured where:
  - Global scope: Can be in `_global` and/or server sections
  - Server-aware: Only in server sections
  - Server-specific: Only in compatible server sections
- [ ] Provide rationale for each category's restrictions

### Phase 3: Create Configuration Examples
- [ ] Simple global-only configurations
- [ ] Server-specific only configurations  
- [ ] Mixed global + server override configurations
- [ ] Invalid configurations with clear error explanations

### Phase 4: Document TUI Display Implications
- [ ] How partial enablement appears in global sections
- [ ] How server-specific configuration appears in server sections
- [ ] How to interpret status descriptions for different configuration patterns

### Phase 5: Add Validation Rules Documentation
- [ ] Document which combinations are valid/invalid
- [ ] Explain validation error messages
- [ ] Provide troubleshooting guide for common configuration issues

## Configuration Examples to Document

### Example 1: Global Security Plugin with Partial Enablement
```yaml
plugins:
  security:
    _global:
      - policy: pii
        enabled: true
    filesystem:
      # PII inherited from global, enabled on filesystem
    github:
      - policy: pii
        enabled: false  # Explicitly disabled for github
```

**TUI Display:**
- Global section: "PII Filter ✅ Enabled on 2/3 servers"
- Filesystem section: "PII Filter ✅ Enabled (from global)"
- GitHub section: "PII Filter ❌ Disabled (overrides global)"

### Example 2: Server-Aware Plugin (Tool Allowlist)
```yaml
plugins:
  security:
    # _global section - tool_allowlist NOT allowed here
    filesystem:
      - policy: tool_allowlist
        enabled: true
        config:
          mode: allowlist
          tools: ["read_file", "write_file"]
```

**TUI Display:**
- Global section: Tool Allowlist not shown (server-aware scope)
- Filesystem section: "Tool Allowlist ✅ Allow 2 tools"

### Example 3: Mixed Configuration with Override
```yaml
plugins:
  security:
    _global:
      - policy: secrets
        enabled: true
        config:
          action: redact
    production_server:
      - policy: secrets
        enabled: true
        config:
          action: block  # Stricter for production
```

**TUI Display:**
- Global section: "Secrets Filter ✅ Enabled on all servers"
- Production section: "Secrets Filter ✅ Block (overrides global redact)"

## Validation Rules to Document

### Valid Configurations
- ✅ Global scope plugins in `_global` section
- ✅ Global scope plugins in server sections (with or without global)
- ✅ Server-aware plugins in server sections only
- ✅ Server-specific plugins in compatible server sections only

### Invalid Configurations  
- ❌ Server-aware plugins in `_global` section
- ❌ Server-specific plugins in `_global` section
- ❌ Server-specific plugins in incompatible server sections

## Documentation Structure

Create comprehensive documentation in:
- [ ] Update `docs/user/reference/configuration-reference.md`
- [ ] Add examples to `docs/user/guides/plugin-configuration.md`
- [ ] Update ADR-018 with configuration behavior
- [ ] Add troubleshooting section for common misconfigurations

## Dependencies

- Depends on `plugin-scope-refactor` scope categories (✅ completed in todos-completed/)
- Should be completed before `4-tui-plugin-display-enhancement`

## Success Metrics

- [ ] Clear documentation of all configuration patterns
- [ ] Unambiguous rules for what can be configured where
- [ ] Comprehensive examples covering common use cases
- [ ] Clear explanation of TUI display behavior
- [ ] Validation rules clearly documented