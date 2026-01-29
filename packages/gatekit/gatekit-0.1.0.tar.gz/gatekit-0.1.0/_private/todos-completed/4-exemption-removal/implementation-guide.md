# Exemption Removal Implementation Guide

## Overview
This document provides specific code changes needed to remove the exemptions system from Gatekit. Changes are organized by file with exact line numbers and replacement code.

## Security Plugin Changes

### 1. PII Filter Plugin (`gatekit/plugins/security/pii.py`)

**Remove exemption initialization (lines 133-134):**
```python
# REMOVE these lines:
# Initialize exemptions
self.exemptions = config.get("exemptions", {"tools": [], "paths": []})
```

**Remove exemption checking method (around line 525):**
```python
# REMOVE this method:
def _is_tool_exempted(self, tool_name: str) -> bool:
    """Check if tool is exempted from PII filtering."""
    return tool_name in self.exemptions.get("tools", [])
```

**Update request processing (around line 568):**
```python
# REMOVE exemption check:
# Check for tool exemptions
if self._is_tool_exempted(request.method):
    return PolicyDecision(allowed=True, reason="Tool exempted from PII filtering")
```

**Update plugin docstring (line 18):**
```python
# CHANGE from:
- Tool and path-based exemptions

# TO:
# Remove this line entirely
```

### 2. Prompt Injection Plugin (`gatekit/plugins/security/prompt_injection.py`)

**Remove exemption initialization (lines 152-156):**
```python
# REMOVE these lines:
# Initialize exemptions
exemptions = config.get("exemptions", {})
self.exemptions = {
    "tools": set(exemptions.get("tools", []))
}
```

**Remove exemption checking methods (around line 440):**
```python
# REMOVE this method:
def _is_tool_exempted(self, tool_name: str) -> bool:
    """Check if tool is exempted from injection filtering."""
    return tool_name in self.exemptions["tools"]
```

**Update request processing (around lines 448, 456, 495):**
```python
# REMOVE exemption checking logic:
# Check tool exemptions first
if self._is_tool_exempted(request.method):
    return PolicyDecision(
        allowed=True,
        reason=f"Tool '{request.method}' exempted from injection filtering",
        metadata={
            "exemption_applied": True,
        }
    )

# AND remove exemption_applied from other metadata:
"exemption_applied": False,  # REMOVE this line
```

**Update response processing (around lines 556, 564, 616):**
```python
# REMOVE similar exemption checking and metadata
```

### 3. Secrets Filter Plugin (`gatekit/plugins/security/secrets.py`)

**Remove exemption initialization (lines 174-179):**
```python
# REMOVE these lines:
# Initialize exemptions
self.exemptions = config.get("exemptions", {"tools": [], "paths": []})
if "tools" not in self.exemptions:
    self.exemptions["tools"] = []
if "paths" not in self.exemptions:
    self.exemptions["paths"] = []
```

**Remove exemption checking method (around line 308):**
```python
# REMOVE this method:
def _is_tool_exempted(self, tool_name: str) -> bool:
    """Check if tool is exempted from secrets filtering."""
    return tool_name in self.exemptions["tools"]
```

**Update request processing (around line 533):**
```python
# REMOVE exemption check:
# Check tool exemptions
if self._is_tool_exempted(request.method):
    return PolicyDecision(allowed=True, reason="Tool exempted from secrets filtering")
```

**Update plugin docstring (line 20):**
```python
# CHANGE from:
- Tool and path-based exemptions

# TO:
# Remove this line entirely
```

## Configuration Model Changes

### File: `gatekit/config/models.py`

**Remove exemption validation (lines 392-400):**
```python
# REMOVE this entire block:
# Check plugins for exemptions (generic validation for all plugins)
if "exemptions" in config and isinstance(config["exemptions"], dict):
    exemptions = config["exemptions"]
    if "tools" in exemptions and isinstance(exemptions["tools"], dict):
        for server_name in exemptions["tools"].keys():
            if server_name not in self.upstreams:
                errors.append(
                    f"Plugin '{plugin.policy}' references unknown server '{server_name}' in exemptions. "
                    f"Available servers: {list(self.upstreams.keys())}"
                )
```

## Test File Changes

### 1. PII Filter Tests (`tests/unit/test_pii_filter_plugin.py`)

**Remove exemption configuration from basic test (lines 27+):**
```python
# REMOVE exemption configuration:
"exemptions": {
    "tools": ["allowed_tool_name"],
    "paths": ["allowed/path/*"]
},
```

**Remove exemption assertions (lines 39-40):**
```python
# REMOVE these assertions:
assert plugin.exemptions["tools"] == ["allowed_tool_name"]
assert plugin.exemptions["paths"] == ["allowed/path/*"]
```

**Remove entire TestExemptions class (lines 1171+):**
```python
# REMOVE the entire class:
class TestExemptions:
    """Test exemption functionality."""
    # ... entire class content
```

### 2. Prompt Injection Tests (`tests/unit/test_prompt_injection_defense_plugin.py`)

**Remove exemption configuration test (lines 119-129):**
```python
# REMOVE this entire test method:
def test_exemption_configuration(self):
    """Test tool exemption configuration."""
    # ... entire method
```

**Remove entire TestExemptionFunctionality class (lines 553+):**
```python
# REMOVE the entire class:
class TestExemptionFunctionality:
    """Test exemption functionality."""
    # ... entire class content
```

**Remove exemption test from response tests (lines 1268+):**
```python
# REMOVE this test method:
async def test_tool_exemption_applies_to_responses(self):
    """Test that tool exemptions work for response checking."""
    # ... entire method
```

### 3. Secrets Filter Tests (`tests/unit/test_secrets_filter_plugin.py`)

**Remove exemption configuration (lines 36+):**
```python
# REMOVE exemption configuration:
"exemptions": {
    "tools": ["development_tool"],
    "paths": ["logs/*"]
},
```

**Remove exemption assertion (line 56):**
```python
# REMOVE this assertion:
assert "development_tool" in plugin.exemptions["tools"]
```

**Remove exemption test method (lines 415+):**
```python
# REMOVE this entire test method:
async def test_tool_exemption_for_requests(self):
    """Test that tool exemptions work for request checking."""
    # ... entire method
```

### 4. Plugin Config Model Tests (`tests/unit/test_plugin_config_models.py`)

**Remove exemption validation test (lines 371+):**
```python
# REMOVE this entire test:
# Test that other plugins support server-aware exemptions
config_schema = ConfigSchema()
config_schema.upstreams = {"test_server": {"command": "test"}}
config_schema.plugins = [
    PluginConfig(
        policy="prompt_injection",
        config={
            "exemptions": {
                "tools": {"test_server": ["safe_tool"]}
            }
        }
    )
]
# ... rest of test
```

### 5. Simple Secrets Test (`tests/unit/test_secrets_filter_plugin_simple.py`)

**Remove exemption configuration (line 36+):**
```python
# REMOVE exemption configuration:
"exemptions": {
    "tools": ["safe_tool"],
    "paths": ["safe/path/*"]
},
```

## Documentation Changes

### 1. Configuration Reference (`docs/user/reference/configuration-reference.md`)

**Remove exemption documentation sections:**
- Lines 962+: Remove PII exemptions example
- Lines 979+: Remove exemptions description
- Lines 1094+: Remove secrets exemptions example  
- Lines 1114+: Remove exemptions description

### 2. Plugin UI Architecture (`docs/decision-records/018-plugin-ui-widget-architecture.md`)

**Remove exemption reference (line 20):**
```markdown
# CHANGE from:
- **Security plugins** need complex UIs (PII types, detection actions, exemptions)

# TO:
- **Security plugins** need complex UIs (PII types, detection actions)
```

## Validation Steps

### 1. Code Removal Verification
```bash
# Verify no exemption references remain in security plugins
grep -r "exemption" gatekit/plugins/security/
# Should return no results

# Verify no exemption validation in config models
grep -r "exemption" gatekit/config/models.py
# Should return no results
```

### 2. Test Suite Validation
```bash
# Run full test suite
pytest tests/

# Verify exemption tests are removed
grep -r "exemption\|Exemption" tests/unit/
# Should only return archived/historical references
```

### 3. Configuration Compatibility
```bash
# Test legacy config loading (exemptions should be ignored)
# Create test config with exemptions and verify it loads without error
```

### 4. Plugin Functionality
```bash
# Test each security plugin individually
pytest tests/unit/test_pii_filter_plugin.py -v
pytest tests/unit/test_prompt_injection_defense_plugin.py -v  
pytest tests/unit/test_secrets_filter_plugin.py -v
```

## Rollback Plan

If issues arise during implementation:

1. **Immediate rollback**: Use git to revert specific commits
2. **Partial rollback**: Re-add exemption logic to specific plugins as needed
3. **Configuration rollback**: Restore exemption validation if compatibility issues occur

## Post-Implementation Tasks

1. **Update plugin documentation** - Remove exemption references from plugin docstrings
2. **Update tutorial configurations** - Ensure no exemption examples remain
3. **Performance testing** - Verify removal doesn't impact performance
4. **Security testing** - Confirm security policies apply consistently

This implementation removes approximately 500+ lines of exemption-related code and significantly simplifies the security plugin architecture.