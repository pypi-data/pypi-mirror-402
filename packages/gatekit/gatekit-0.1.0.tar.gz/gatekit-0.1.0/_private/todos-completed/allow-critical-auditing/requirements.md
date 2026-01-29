# Allow Critical Auditing Plugins

## Overview
Currently, auditing plugins are forced to be non-critical (critical=False), meaning audit failures never halt system operation. This prevents organizations from meeting strict compliance requirements where audit trail integrity is mandatory.

## Problem Statement
In highly regulated environments (finance, healthcare, government), audit logging failures must be treated as critical:
- **Regulatory Compliance**: SOX, HIPAA, PCI-DSS often mandate uninterrupted audit trails
- **Legal Requirements**: Some jurisdictions require immutable, guaranteed audit logs  
- **Security Policies**: Organizations may enforce "no audit, no access" policies
- **Forensic Requirements**: Critical systems need guaranteed audit trails for incident response

The current implementation prevents these use cases by hardcoding `critical=False` for all auditing plugins.

## Requirements

### 1. Allow Configurable Critical Setting
- Remove the forced `critical=False` override in `AuditingPlugin.__init__`
- Honor the `critical` configuration parameter from user config
- Default to `critical=False` for backward compatibility

### 2. Configuration Changes
```yaml
plugins:
  auditing:
    _global:
      - policy: "json_auditing"
        enabled: true
        critical: true  # Should now be honored
        config:
          output_file: "/secure/audit.log"
```

### 3. Implementation Updates

#### AuditingPlugin Base Class (gatekit/plugins/interfaces.py)
- **Line 270**: Remove `config.pop('critical', None)` comment saying "Remove critical as it's always False for audit"
- **Line 284**: Remove forced `self.critical = False` with comment "Always false for audit plugins"
- **Line 283**: Update comment "Auditing plugins never block processing"
- After parent init, restore critical value from original config if present (default False)
- Keep the config cleaning logic for priority only

#### Plugin Manager (gatekit/plugins/manager.py)
- Import `AuditingFailureError` from `gatekit.protocol.errors`
- **Lines 806-816 (log_request)**: Add critical checking for audit plugin failures
- **Lines 848-853 (log_response)**: Add critical checking for audit plugin failures
- **Lines 885-890 (log_notification)**: Add critical checking for audit plugin failures
- Update comments that say "Auditing failures are logged but don't block processing"

#### Test Updates
Update tests to reflect that auditing plugins CAN be critical:

**test_base_auditing.py:**
- **Line 51**: Update assertion to check configured critical value
- **Line 69**: Update assertion to check configured critical value
- **Line 253**: Update test comment "audit plugins are never critical"
- **Line 260**: Remove comment "Audit plugins should not raise exceptions (never critical)"
- **Line 262**: Update assertion "Should always be False for audit plugins"
- **Line 274**: Update assertion to check configured value

**test_audit_plugin_priority.py:**
- **Line 29-37**: Update `test_audit_plugin_critical_always_false` to test configurable critical
- **Line 30**: Change docstring from "Verify audit plugins always have critical=False"
- **Line 33**: Update assertion from "should always have critical=False"
- **Line 37**: Update assertion from "should ignore critical in config"

**test_file_auditing_path_resolution.py:**
- **Line 160**: Update comment "should always have critical=False (never critical)"
- **Line 163**: Update comment "they're never critical"
- **Lines 218, 220**: Update assertions and comments about critical=False
- **Lines 234, 236**: Update assertions and comments about critical=False

- Add new tests verifying critical audit plugins halt on failure

### 4. Behavior Specification

#### When critical=true:
- Audit plugin initialization failures should halt the system
- Audit logging failures during operation should return error to client
- File permission errors, disk full, etc. should be treated as critical

#### When critical=false (default):
- Current behavior is maintained
- Audit failures are logged but don't halt operation
- System continues processing even if audit logging fails

### 5. Testing Requirements

#### Add tests for:
1. Critical audit plugin with initialization failure (should halt)
2. Critical audit plugin with runtime failure (should error)
3. Non-critical audit plugin with failures (should continue)
4. Default behavior when critical not specified (should be false)
5. Multiple audit plugins with mixed critical settings

### 6. Documentation Updates

Update documentation to explain:
- When to use critical audit plugins
- Compliance scenarios that require critical auditing
- Performance and availability implications
- Best practices for critical audit configuration

#### Specific Documentation Files to Update:

**docs/todos/auditing-priority-removal/requirements.md:**
- **Line 61**: Remove example showing `self.critical = False` as always false
- **Line 103**: Update comment "Failures are logged but don't block processing"
- **Line 123**: Update comment "Audit failures never block processing"

**docs/user/core-concepts/2-plugin-architecture.md:**
- **Line 67**: Update "Plugin errors are logged but don't affect request processing"
- **Line 358**: Update "Don't block processing: Auditing failures shouldn't affect operations"

**docs/user/reference/plugin-ordering.md:**
- **Line 246**: Update "Plugin failures are logged but don't affect request processing"

**docs/user/reference/configuration-reference.md:**
- Already correctly documents critical parameter behavior

**docs/user/guides/plugin-configuration.md:**
- Already correctly shows critical usage examples

## Implementation Plan

### Phase 1: Core Changes
1. Modify `AuditingPlugin.__init__` to allow critical setting
2. Update affected tests
3. Add new test coverage

### Phase 2: Validation
1. Test with file permission errors
2. Test with disk full scenarios
3. Test with network audit destinations (future)

### Phase 3: Documentation
1. Update user documentation
2. Add compliance guide section
3. Document best practices

## Risk Analysis

### Risks:
- **Availability Impact**: Critical audit failures will halt the system
- **Misconfiguration**: Users may accidentally set critical=true without understanding implications

### Mitigations:
- Default to critical=false
- Clear documentation on implications
- Consider adding confirmation prompt in TUI when enabling critical auditing

## Success Criteria
1. Audit plugins can be configured as critical
2. Critical audit plugins halt system on failure
3. Non-critical audit plugins maintain current behavior
4. All existing tests pass with updates
5. New tests validate critical audit behavior

## Non-Goals
- Changing default behavior (remains non-critical)
- Adding warning logs (per user preference)
- Implementing retry logic for audit failures (future work)

## Future Considerations
- Add health checks for critical audit destinations
- Implement circuit breaker pattern for transient failures
- Add metrics for audit success/failure rates
- Consider audit buffering for temporary failures