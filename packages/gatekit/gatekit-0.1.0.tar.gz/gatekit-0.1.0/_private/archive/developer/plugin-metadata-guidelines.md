# Plugin Metadata Guidelines

## Overview

This document provides guidelines for plugin developers on handling metadata in Gatekit plugins. Proper metadata management ensures traceability, debugging capability, and compliance requirements are met.

## Core Metadata Fields

Gatekit maintains several core metadata fields that should be preserved by plugins:

### System Metadata (Read-Only)

These fields are set by Gatekit and should **never** be modified by plugins:

- `security_plugin_count`: Number of security plugins applied
- `upstream`: The upstream server name
- `plugins_applied`: List of plugins that processed the message
- `timestamp`: When the message was processed (if present)
- `request_id`: Correlation ID for request/response matching (if present)

### Plugin Metadata

Plugins may add their own metadata fields but should follow these conventions:

- Use plugin name as prefix: `pii_filter.redacted_count`
- Be descriptive: `secrets_filter.detected_types` not `secrets.types`
- Include relevant context: `tool_allowlist.blocked_tools`

## Metadata Preservation Rules

### Rule 1: Never Remove Core Metadata

```python
# ❌ WRONG: Removes all existing metadata
decision.metadata = {"my_field": "value"}

# ✅ CORRECT: Preserves existing metadata
if not decision.metadata:
    decision.metadata = {}
decision.metadata["my_field"] = "value"
```

### Rule 2: When Modifying Content

When a plugin modifies message content, it takes responsibility for the decision. However, certain metadata should still be preserved:

```python
# When modifying content, preserve critical metadata
if decision.modified_content:
    # Preserve security_plugin_count and upstream
    security_count = final_decision.metadata.get("security_plugin_count", 0)
    upstream = final_decision.metadata.get("upstream")
    
    # Replace metadata with new decision's metadata
    final_decision.metadata = decision.metadata or {}
    
    # Restore critical fields
    final_decision.metadata["security_plugin_count"] = security_count
    final_decision.metadata["upstream"] = upstream
```

### Rule 3: Correlation IDs Must Be Preserved

If your deployment uses correlation IDs for request tracking, ensure they're preserved:

```python
# Preserve correlation IDs if present
correlation_id = original_metadata.get("correlation_id")
if correlation_id:
    new_metadata["correlation_id"] = correlation_id
```

## Plugin-Specific Metadata

### Security Plugins

Security plugins should include:
- Reason for blocking/allowing
- Specific violations detected
- Risk score (if applicable)
- Remediation performed (redaction, blocking, etc.)

Example:
```python
decision = PolicyDecision(
    allowed=False,
    reason="PII detected in request",
    metadata={
        "pii_filter.detected": ["email", "ssn"],
        "pii_filter.locations": ["params.user_data", "params.notes"],
        "pii_filter.action": "blocked",
        "pii_filter.risk_score": 8
    }
)
```

### Auditing Plugins

Auditing plugins should never modify decision metadata. They should:
- Read metadata for logging
- Add audit-specific context in their own logs
- Never remove or modify existing metadata

## Best Practices

### 1. Use Namespaced Keys

Prefix your metadata keys with your plugin name:

```python
# Good
metadata["pii_filter.redacted_count"] = 5

# Bad - could conflict with other plugins
metadata["redacted_count"] = 5
```

### 2. Document Your Metadata

Include metadata documentation in your plugin class:

```python
class MySecurityPlugin(SecurityPlugin):
    """
    My security plugin description.
    
    Metadata fields:
    - my_plugin.detected_issues: List of detected security issues
    - my_plugin.risk_score: Numeric risk score (0-10)
    - my_plugin.action_taken: Action performed (block/allow/redact)
    """
```

### 3. Handle Missing Metadata Gracefully

Always check for metadata existence:

```python
# Good - handles None gracefully
existing_value = (decision.metadata or {}).get("field", default_value)

# Bad - crashes if metadata is None
existing_value = decision.metadata.get("field", default_value)
```

### 4. Log Metadata Changes

When modifying metadata significantly, log the change:

```python
if significant_change:
    logger.debug(
        f"Plugin {self.plugin_id} modified metadata: "
        f"added={list(added_keys)}, removed={list(removed_keys)}"
    )
```

## Metadata in Error Scenarios

When plugins fail, include diagnostic metadata:

```python
try:
    # Plugin logic
    pass
except Exception as e:
    return PolicyDecision(
        allowed=False,
        reason=f"Plugin {plugin_name} encountered an error",
        metadata={
            "error": str(e),
            "plugin_failure": True,
            "plugin": plugin_name,  # Always include plugin identifier
            "error_type": e.__class__.__name__,
            "recovery_possible": False
        }
    )
```

## Testing Metadata Handling

### Unit Tests Should Verify

1. Core metadata preservation
2. Correlation ID persistence
3. Proper namespacing
4. Error metadata inclusion

Example test:
```python
def test_plugin_preserves_core_metadata():
    """Test that plugin preserves core metadata fields."""
    original_metadata = {
        "security_plugin_count": 3,
        "upstream": "test-server",
        "correlation_id": "test-123"
    }
    
    decision = plugin.process(request, original_metadata)
    
    # Core fields should be preserved
    assert decision.metadata["security_plugin_count"] == 3
    assert decision.metadata["upstream"] == "test-server"
    assert decision.metadata["correlation_id"] == "test-123"
```

## Future Considerations

As Gatekit evolves, consider:

1. **Protected Metadata**: Future versions may enforce certain fields as read-only
2. **Metadata Schema**: Formal schemas for metadata validation
3. **Metadata Routing**: Different metadata for different consumers (audit vs client)

## Summary

- Preserve core system metadata
- Use namespaced keys for plugin-specific data
- Document your metadata fields
- Handle missing metadata gracefully
- Include diagnostic information in error cases
- Test metadata preservation thoroughly