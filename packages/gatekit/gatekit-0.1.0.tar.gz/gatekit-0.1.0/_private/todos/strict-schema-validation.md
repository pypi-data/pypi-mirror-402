# Strict Schema Validation for Plugin Configs

## Problem

Unknown plugin configuration options are silently ignored, creating security risks:
- Typos like `action: blcok` (instead of `block`) cause defaults to be used silently
- Users believe security controls are configured when they're not
- False sense of security - a core anti-pattern for security software

Example from seed config that went unnoticed:
```yaml
- handler: audit_jsonl
  config:
    include_pipeline: true   # Silently ignored - not a valid option
    rotation:                # Silently ignored - not implemented
      enabled: true
```

## Solution

Implement fail-closed JSON schema validation during config loading. The infrastructure exists (`SchemaValidator` with `additionalProperties: false` schemas) but is only used in the TUI.

---

## Implementation

### 1. Add Schema Validation to Config Loader

**File**: `gatekit/config/loader.py`

**Location**: After `validate_config()` (line 248), BEFORE `validate_paths()` (line 251)

This ordering is critical: schema validation must run before `_validate_single_plugin_paths()` which instantiates plugins at line 466. Validating after would allow malformed configs to run arbitrary plugin code before rejection.

**Add call**:
```python
# Run additional validation
self.validate_config(config)

# Validate plugin configs against JSON schemas (fail-closed for unknown fields)
self.validate_plugin_schemas(config)

# Run path validation for all path-aware components
self.validate_paths(config, config_directory)
```

**Add new method** `validate_plugin_schemas()`:

```python
def validate_plugin_schemas(self, config: ProxyConfig) -> None:
    """Validate plugin configurations against their JSON schemas.

    Enforces fail-closed behavior: unknown fields are rejected rather than
    silently ignored. This prevents configuration typos from weakening
    security controls.

    Plugins without schemas are skipped (allows custom plugins).

    Args:
        config: Parsed ProxyConfig object

    Raises:
        ConfigError: If any plugin configuration has schema violations
    """
    from gatekit.config.json_schema import get_schema_validator

    validator = get_schema_validator()
    all_errors = []

    if not config.plugins:
        return

    for category, category_attr in [
        ("security", config.plugins.security),
        ("auditing", config.plugins.auditing),
        ("middleware", config.plugins.middleware),
    ]:
        for upstream, plugin_list in category_attr.items():
            for idx, plugin_config in enumerate(plugin_list):
                handler = plugin_config.handler
                plugin_conf = plugin_config.config

                # Check if schema exists for this handler
                if not validator.has_schema(handler):
                    # Skip plugins without schemas (custom plugins, etc.)
                    continue

                schema_errors = validator.validate(handler, plugin_conf)
                if schema_errors:
                    field_path = f"plugins.{category}.{upstream}.{idx}.config"
                    all_errors.append({
                        "handler": handler,
                        "field_path": field_path,
                        "errors": schema_errors,
                    })

    if all_errors:
        # Format error message
        error_parts = []
        suggestions = []

        for err in all_errors:
            handler = err["handler"]
            for schema_err in err["errors"]:
                # Include handler name in error for clarity when multiple plugins have errors
                error_parts.append(f"{handler} ({err['field_path']}): {schema_err}")

                # Add "valid fields" suggestion only for additionalProperties errors
                if "Additional properties are not allowed" in schema_err:
                    schema = validator.get_schema(handler)
                    if schema and "properties" in schema:
                        valid_fields = ", ".join(sorted(schema["properties"].keys()))
                        suggestions.append(f"Valid fields for {handler}: {valid_fields}")

        suggestions.append("Remove or rename unknown fields")

        raise ConfigError(
            message=f"Plugin configuration validation failed:\n  " + "\n  ".join(error_parts),
            error_type="validation_error",
            field_path=all_errors[0]["field_path"],
            suggestions=suggestions[:3],  # Max 3 suggestions
        )
```

### 2. Add `critical` Field to Framework Fields

**File**: `gatekit/config/framework_fields.py`

The `critical` field (fail-open/fail-closed behavior) is a framework field used by many configs but not currently injected into schemas. Add it:

```python
CRITICAL_FIELD_SCHEMA: Dict[str, Any] = {
    "type": "boolean",
    "title": "Critical Plugin",
    "description": "If true (default), plugin failures cause startup to fail. If false, plugin failures are logged but startup continues.",
    "default": True,
}

# Default values for framework fields when not specified in config
DEFAULT_FRAMEWORK_VALUES: Dict[str, Any] = {
    "enabled": False,  # Default to disabled for new plugins in TUI
    "priority": 50,
    "critical": True,  # Default to fail-closed (secure by default)
}

def get_framework_fields(plugin_type: str) -> Dict[str, Dict[str, Any]]:
    """Get framework field schemas for a plugin type."""
    if plugin_type == "auditing":
        return {
            "enabled": deepcopy(ENABLED_FIELD_SCHEMA),
            "critical": deepcopy(CRITICAL_FIELD_SCHEMA),
        }
    else:
        return {
            "enabled": deepcopy(ENABLED_FIELD_SCHEMA),
            "priority": deepcopy(PRIORITY_FIELD_SCHEMA),
            "critical": deepcopy(CRITICAL_FIELD_SCHEMA),
        }
```

**Why**:
1. Configs like `non-critical-failure-test.yaml` use `critical: false`. Without injecting this field into schemas, it would be rejected as unknown once strict validation is enforced.
2. `DEFAULT_FRAMEWORK_VALUES` must include `critical: True` because `config_adapter.py:92` uses this mapping to populate TUI form defaults. Without it, new plugins would show `critical: False` (fail-open), undermining the "secure by default" principle.

### 3. Add `has_schema()` Method to SchemaValidator

**File**: `gatekit/config/json_schema.py`

Add method after `get_schema()`:
```python
def has_schema(self, handler_name: str) -> bool:
    """Check if a schema exists for the given handler.

    Returns False for plugins that haven't implemented get_json_schema().
    This allows custom plugins to work without schemas.
    """
    return handler_name in self.validators
```

### 4. Add Singleton Cache and Clear Function to Config Module

**File**: `gatekit/config/json_schema.py`

Add at module level (bottom of file):
```python
# Module-level singleton for performance
_schema_validator_instance: Optional[SchemaValidator] = None

def get_schema_validator() -> SchemaValidator:
    """Get cached SchemaValidator instance.

    Avoids repeated plugin discovery on every config load.
    """
    global _schema_validator_instance
    if _schema_validator_instance is None:
        _schema_validator_instance = SchemaValidator()
    return _schema_validator_instance

def clear_validator_cache() -> None:
    """Clear the cached validator (for testing or reload).

    Tests use this to reset plugin discovery state between test runs.
    """
    global _schema_validator_instance
    _schema_validator_instance = None
```

**Why `clear_validator_cache()` is needed**: Tests in `tests/unit/test_tui_validation.py` call `clear_validator_cache()` to reset plugin discovery between runs. Without this function, tests cannot reset the singleton state.

Update TUI's `schema_cache.py` to re-export from shared module:
```python
from gatekit.config.json_schema import get_schema_validator, clear_validator_cache

__all__ = ["get_schema_validator", "clear_validator_cache"]
```

### 5. Remove Dead TUI Code

**File**: `gatekit/tui/utils/object_item_modal.py`

Remove the manual `additionalProperties` check (lines 157-162) that can never trigger in practice:

```python
# DELETE THIS BLOCK (lines 157-162):
        # Check additionalProperties if false
        if self.item_schema.get("additionalProperties") is False:
            allowed_fields = set(properties.keys())
            extra_fields = set(data.keys()) - allowed_fields
            if extra_fields:
                errors.append(f"Unexpected fields: {', '.join(extra_fields)}")
```

**Why remove**: This validation is dead code because:
1. TUI forms only generate widgets for schema-defined fields - users cannot add unknown fields through the UI
2. Unknown fields from manually-edited configs are preserved via "passthrough" which bypasses this validation entirely
3. The jsonschema validation in `modal.py` handles this constraint anyway (though it's also bypassed by passthrough)

The `additionalProperties: false` property in schemas must stay - it's the source of truth for the gateway validation being added.

**File**: `tests/unit/test_array_editor.py`

Delete the test `test_object_modal_additional_properties` (lines 201-218) which tests the dead code being removed:

```python
# DELETE THIS TEST:
def test_object_modal_additional_properties():
    """Test object modal with additionalProperties false."""
    schema = {
        "type": "object",
        "required": ["name"],
        "properties": {"name": {"type": "string"}, "value": {"type": "integer"}},
        "additionalProperties": False,
    }

    modal = ObjectItemModal(schema)

    # Test with extra field
    errors = modal._validate_item({"name": "test", "value": 10, "extra": "not allowed"})
    assert any("Unexpected fields" in e for e in errors)

    # Test without extra field
    errors = modal._validate_item({"name": "test", "value": 10})
    assert len(errors) == 0
```

### 6. Create Test Config File

**File**: `tests/validation/invalid-configs/unknown-options.yaml`

```yaml
# Test config with unknown plugin options
# Expected: Startup fails with clear error about unknown fields

proxy:
  transport: stdio
  upstreams:
    - name: filesystem
      transport: stdio
      command:
        - echo
        - test

plugins:
  auditing:
    _global:
      - handler: audit_jsonl
        config:
          enabled: true
          output_file: /tmp/test.jsonl
          include_pipeline: true      # Unknown - should fail
          include_timing: true        # Unknown - should fail
```

### 7. Add Unit Tests

**File**: `tests/unit/config/test_schema_validation.py`

```python
"""Tests for strict plugin schema validation."""

import pytest
from gatekit.config.loader import ConfigLoader
from gatekit.config.errors import ConfigError


class TestPluginSchemaValidation:
    """Test that unknown plugin config options are rejected."""

    def test_unknown_option_rejected(self, tmp_path):
        """Unknown options should raise ConfigError."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
proxy:
  transport: stdio
  upstreams:
    - name: test
      transport: stdio
      command: ["echo", "test"]
plugins:
  auditing:
    _global:
      - handler: audit_jsonl
        config:
          enabled: true
          output_file: /tmp/test.jsonl
          unknown_option: true
""")

        loader = ConfigLoader()
        with pytest.raises(ConfigError) as exc_info:
            loader.load_from_file(config_file)

        assert "unknown_option" in str(exc_info.value.message).lower() or \
               "additional properties" in str(exc_info.value.message).lower()

    def test_valid_config_passes(self, tmp_path):
        """Valid configs should load without error."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
proxy:
  transport: stdio
  upstreams:
    - name: test
      transport: stdio
      command: ["echo", "test"]
plugins:
  auditing:
    _global:
      - handler: audit_jsonl
        config:
          enabled: true
          output_file: /tmp/test.jsonl
          include_request_body: true
""")

        loader = ConfigLoader()
        config = loader.load_from_file(config_file)
        assert config is not None

    def test_plugin_without_schema_skipped(self, tmp_path):
        """Plugins without schemas should be skipped, not rejected."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
proxy:
  transport: stdio
  upstreams:
    - name: test
      transport: stdio
      command: ["echo", "test"]
plugins:
  security:
    _global:
      - handler: nonexistent_custom_plugin
        config:
          enabled: true
          any_field: "should not trigger schema error"
          another_field: 123
""")

        loader = ConfigLoader()
        # Should NOT raise "No schema found" - schema validation skips unknown handlers
        # It WILL raise a handler discovery error later, which is expected
        with pytest.raises(ConfigError) as exc_info:
            loader.load_from_file(config_file)

        # Verify the error is about handler not found, NOT about schema validation
        error_msg = str(exc_info.value.message).lower()
        assert "no schema found" not in error_msg, \
            "Schema validation should skip plugins without schemas"
        assert "handler" in error_msg or "plugin" in error_msg, \
            "Error should be about handler discovery, not schema validation"

    def test_error_includes_valid_fields_suggestion(self, tmp_path):
        """Error message should suggest valid fields."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
proxy:
  transport: stdio
  upstreams:
    - name: test
      transport: stdio
      command: ["echo", "test"]
plugins:
  auditing:
    _global:
      - handler: audit_jsonl
        config:
          enabled: true
          output_file: /tmp/test.jsonl
          bad_field: true
""")

        loader = ConfigLoader()
        with pytest.raises(ConfigError) as exc_info:
            loader.load_from_file(config_file)

        # Should have suggestion with valid fields
        assert any("valid fields" in s.lower() for s in exc_info.value.suggestions)
```

### 8. Update Manual Validation Guide

**File**: `tests/validation/manual-validation-guide.md`

Add section **5.7 Unknown Configuration Options** after section 5.6:

```markdown
### 5.7 Unknown Configuration Options

```bash
/Users/dbright/mcp/gatekit/.venv/bin/gatekit-gateway --config tests/validation/invalid-configs/unknown-options.yaml
```

**Expected output** (clean, no traceback):
```
[ERROR] Startup failed: Plugin configuration validation failed:
  audit_jsonl (plugins.auditing._global.0.config): At /: Additional properties are not allowed ('include_pipeline', 'include_timing' were unexpected)
[ERROR]     Field: plugins.auditing._global.0.config
[ERROR]   Suggestions:
    • Valid fields for audit_jsonl: critical, enabled, output_file, include_request_body, include_response_body, include_notification_body, max_body_size
    • Remove or rename unknown fields
[ERROR] Not in MCP client context (running in terminal), exiting
```

**Checklist**:
- [ ] Error mentions the unknown field names
- [ ] Error mentions the plugin handler name
- [ ] Field path uses dot notation (`_global.0.config` not `_global[0].config`)
- [ ] Suggestions list valid fields for the plugin
- [ ] **No Python traceback** (this is a config validation error)

**Why this matters**: Unknown fields are silently ignored without this validation. A typo like `action: blcok` (instead of `block`) would cause the plugin to use its default action, potentially weakening security without any warning.
```

---

## Files to Modify

| File | Change |
|------|--------|
| `gatekit/config/framework_fields.py` | Add `CRITICAL_FIELD_SCHEMA`, update `get_framework_fields()` and `DEFAULT_FRAMEWORK_VALUES` |
| `gatekit/config/loader.py` | Add `validate_plugin_schemas()`, call before `validate_paths()` |
| `gatekit/config/json_schema.py` | Add `has_schema()`, add `get_schema_validator()` and `clear_validator_cache()` singleton functions |
| `gatekit/tui/utils/schema_cache.py` | Re-export from `json_schema.py` instead of duplicate implementation |
| `gatekit/tui/utils/object_item_modal.py` | Remove dead `additionalProperties` check (lines 157-162) |
| `tests/unit/test_array_editor.py` | Delete `test_object_modal_additional_properties` test (lines 201-218) |
| `tests/validation/invalid-configs/unknown-options.yaml` | New test config |
| `tests/unit/config/test_schema_validation.py` | New unit tests |
| `tests/validation/manual-validation-guide.md` | Add section 5.7 |

---

## Key Design Decisions

1. **Validation order**: Schema validation runs BEFORE path validation to prevent plugin instantiation with bad configs

2. **Missing schemas = skip**: Plugins without `get_json_schema()` are silently skipped, allowing custom plugins to work

3. **Singleton pattern with clear function**: Reuse cached `SchemaValidator` to avoid repeated plugin discovery. Include `clear_validator_cache()` for test isolation.

4. **Framework field injection**: The `critical` field must be added to `framework_fields.py` alongside `enabled` and `priority`, since it's used by existing configs.

5. **Handler name in errors**: Error messages include the handler name for clarity: `audit_jsonl (plugins.auditing._global.0.config): ...`

6. **Preserve error messages**: JSON Schema errors are passed through verbatim; "valid fields" suggestion only added for additionalProperties violations

7. **Dot notation**: Field paths use `.0.` not `[0]` to match existing conventions

---

## Testing

1. Run unit tests: `pytest tests/unit/config/test_schema_validation.py -v`
2. Run full suite: `pytest tests/ -n auto`
3. Manual validation: Follow section 5.7 in the guide
4. Verify existing valid configs still work

---

## Implementation Order

1. Add `critical` field to `framework_fields.py` (prerequisite for other changes)
2. Add `has_schema()` method and `get_schema_validator()` / `clear_validator_cache()` to `json_schema.py`
3. Update `schema_cache.py` to re-export from `json_schema.py`
4. Add `validate_plugin_schemas()` to `loader.py`
5. Remove dead `additionalProperties` check from `object_item_modal.py`
6. Create `unknown-options.yaml` test config
7. Write unit tests
8. Update manual validation guide with section 5.7
9. Run `pytest tests/ -n auto` to verify no regressions
