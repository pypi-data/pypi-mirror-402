# Remove Redundant Plugin Validation

## Problem

Validation constraints are duplicated between JSON schemas and runtime code. This causes:
1. **Sync bugs**: The `display_name` pattern was in runtime code but missing from JSON schema, so TUI modal didn't catch invalid input
2. **Maintenance burden**: Changes require updating multiple locations
3. **Dead code**: Constants like `ACTIONS` exist but aren't used consistently
4. **Orphaned code**: Fields removed from schemas (`custom_patterns`, `pretty_print`) still have runtime code handling them

## Solution

**Option B: Remove constants, trust the schema**

- JSON schema is the single source of truth for valid values
- Remove redundant runtime validation checks
- Remove unused constants (like `ACTIONS`)
- Remove orphaned code for fields no longer in schemas (`custom_patterns`, `pretty_print`)
- Hardcoded strings in business logic are fine - schema guarantees they're valid by the time `__init__` runs

## Background

JSON schema validation runs BEFORE plugin `__init__` in both contexts:
- **Gateway**: `ConfigLoader.validate_plugin_schemas()` validates before instantiation
- **TUI**: `PluginConfigModal._handle_save_action()` validates before dismissing modal

---

## Changes by File

### 1. tool_manager.py

**`gatekit/plugins/middleware/tool_manager.py`**

Remove redundant regex checks from `_parse_tools_config()`:

**Remove lines 165-169:**
```python
# DELETE THIS:
if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", tool_name):
    raise ValueError(
        f"Invalid tool name '{tool_name}': must start with letter, "
        f"contain only letters, numbers, underscores, and hyphens"
    )
```

**Remove lines 202-206:**
```python
# DELETE THIS:
if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", new_name):
    raise ValueError(
        f"Invalid display name '{new_name}': must start with letter, "
        f"contain only letters, numbers, underscores, and hyphens"
    )
```

**Fix `display_description: null` mismatch (line 188):**
Schema rejects null but runtime accepts it. Change:
```python
# From:
if desc is not None and not isinstance(desc, str):

# To:
if not isinstance(desc, str):
```

**Keep:** isinstance checks, duplicate detection, self-rename check, collision checks (business logic)

---

### 2. csv.py

**`gatekit/plugins/auditing/csv.py`**

Remove redundant enum check from `_validate_config()`:

**Remove lines 179-182:**
```python
# DELETE THIS:
if self.quote_style not in ["minimal", "all", "nonnumeric", "none"]:
    raise ValueError(
        f"Invalid quote_style '{self.quote_style}'. Must be one of: minimal, all, nonnumeric, none"
    )
```

**Keep:** delimiter/quote_char single character checks (helpful error messages)

---

### 3. pii.py

**`gatekit/plugins/security/pii.py`**

**Remove class constant (line 64):**
```python
# DELETE THIS:
ACTIONS = ["block", "redact", "audit_only"]
```

**Remove from `_validate_configuration()` (lines 190-192):**
```python
# DELETE THIS:
if action not in self.ACTIONS:
    raise ValueError(
        f"Invalid action '{action}'. Must be one of: {', '.join(self.ACTIONS)}"
    )
```

**Remove orphaned `custom_patterns` code:**
- `describe_status()` references (lines 89-92)
- `self.custom_patterns` in `__init__` (line 176)
- `_validate_custom_patterns()` method (lines 203-239)
- Any usage in detection methods

**Keep:** PII type validation (business logic)

---

### 4. secrets.py

**`gatekit/plugins/security/secrets.py`**

**Remove class constant (line 69):**
```python
# DELETE THIS:
ACTIONS = ["block", "redact", "audit_only"]
```

**Remove from `_validate_configuration()` (lines 231-233):**
```python
# DELETE THIS:
if action not in self.ACTIONS:
    raise ValueError(
        f"Invalid action '{action}'. Must be one of: {', '.join(self.ACTIONS)}"
    )
```

**Remove orphaned `custom_patterns` code:**
- `describe_status()` references (lines 98-99)
- `self.custom_patterns` in `__init__` (line 299)
- Any usage in detection methods (line 340)
- Comments referencing custom_patterns (lines 194-198, 200-213, 294)

**Remove orphaned `allowlist` code:**
- Commented schema definition (lines 214-221)
- `self.allowlist` in `__init__` (lines 301-304)
- `self.compiled_allowlist` and pattern compilation (lines 349-357)
- `_matches_allowlist()` method (lines 429-433)
- Allowlist check in detection (lines 440-441)

**Remove `detection_types` backward compatibility (no backward compat needed for v0.1.x):**
- `describe_status()` fallback (line 83): `config.get("secret_types", config.get("detection_types", {}))`
- `_validate_configuration()` fallback (line 237)
- `__init__` fallback (lines 268-270)

**Keep:** Secret type validation, entropy config validation (business logic)

---

### 5. prompt_injection.py

**`gatekit/plugins/security/prompt_injection.py`**

**Remove class constants (lines 50, 51):**
```python
# DELETE THIS:
ACTIONS = ["block", "redact", "audit_only"]
SENSITIVITY_LEVELS = ["relaxed", "standard", "strict"]
```

**Remove from `_validate_configuration()` (lines 174-183):**
```python
# DELETE THIS:
if action not in self.ACTIONS:
    raise ValueError(
        f"Invalid action '{action}'. Must be one of: {', '.join(self.ACTIONS)}"
    )

# DELETE THIS:
sensitivity = config.get("sensitivity", "standard")
if sensitivity not in self.SENSITIVITY_LEVELS:
    raise ValueError(
        f"Invalid sensitivity '{sensitivity}'. Must be one of: {', '.join(self.SENSITIVITY_LEVELS)}"
    )
```

**Remove orphaned `custom_patterns` code:**
- `describe_status()` references (lines 76-77)
- `self.custom_patterns` in `__init__` (lines 230-236)
- Any usage in detection methods (line 486)

**Rename to OWASP standard terminology `context_hijacking` (no backward compat for v0.1.x):**
- Update `PATTERN_CATEGORIES` to use `context_hijacking` instead of `context_breaking` (line 46)
- Update schema to use `context_hijacking` instead of `instruction_override` (lines 154-161)
- Remove `alias_map` from `_validate_configuration()` (lines 188-192)
- Remove `alias_map` from `__init__` (lines 216-224)
- Update all internal references from `context_breaking` to `context_hijacking` (lines 328, 360, 471-477)
- Schema should match `PATTERN_CATEGORIES`: `delimiter_injection`, `role_manipulation`, `context_hijacking`

**Keep:** Pattern compilation (business logic)

---

### 6. json_lines.py

**`gatekit/plugins/auditing/json_lines.py`**

**Remove type checks from `_validate_config()`** that schema already handles:

```python
# DELETE type checks like:
if not isinstance(self.include_request_body, bool):
    raise TypeError("include_request_body must be a boolean")
```

**Remove orphaned `pretty_print` code:**
- Type annotation (line 55)
- Docstring reference (line 66)
- `self.pretty_print` assignment in `__init__` (lines 91, 97-98)
- Validation in `_validate_config()` (lines 165-166)
- Usage in `_format_log_entry()` (lines 444-445, 473-474)

**Keep:** "Minimum 50 bytes if non-zero" business logic (not expressible in JSON schema)

---

## Summary of Changes

| File | Remove | Keep |
|------|--------|------|
| tool_manager.py | Regex pattern checks (lines 165-169, 202-206), **fix `display_description: null` mismatch** | Duplicate detection, self-rename, collision checks |
| csv.py | quote_style enum check (lines 179-182) | Single character checks for delimiter/quote_char |
| pii.py | ACTIONS constant, action validation, **orphaned `custom_patterns` code** | PII type validation |
| secrets.py | ACTIONS constant, action validation, **orphaned `custom_patterns` code**, **orphaned `allowlist` code**, **`detection_types` backward compat** | Secret type validation, entropy validation |
| prompt_injection.py | ACTIONS, SENSITIVITY_LEVELS constants and checks, **orphaned `custom_patterns` code**, **rename `context_breaking`→`context_hijacking` (OWASP standard)** | Pattern compilation |
| json_lines.py | Boolean/integer type checks, **orphaned `pretty_print` code** | "Min 50 if non-zero" business logic |

---

## Test Plan

### 1. Pre-Flight
```bash
pytest tests/ -n auto
uv run ruff check gatekit
```

### 2. After Each File Change
```bash
pytest tests/ -n auto
uv run ruff check gatekit
```

### 3. Specific Test Files
```bash
pytest tests/unit/test_tool_manager_plugin.py -v
pytest tests/unit/test_csv_auditing.py -v
pytest tests/unit/test_pii_filter.py -v
pytest tests/unit/test_secrets_filter.py -v
pytest tests/unit/test_prompt_injection_defense.py -v
pytest tests/unit/test_json_lines_auditing.py -v
```

### 3a. Tests That Need Updating (orphaned feature tests)

These tests reference removed features and must be updated/removed:

**`custom_patterns` tests:**
- `tests/unit/test_pii_filter_plugin.py`
- `tests/unit/test_secrets_filter_plugin.py`
- `tests/unit/test_prompt_injection_defense_plugin.py`
- `tests/fixtures/golden_configs/basic_secrets_filter/edge.yaml`
- `tests/validation/manual-validation-config.yaml`

**`pretty_print` tests:**
- `tests/unit/test_json_lines_format_compliance.py`
- `tests/unit/test_base_auditing.py`

**`allowlist` tests (DELETE ENTIRE FILE):**
- `tests/unit/test_secrets_allowlist.py` - entire file should be deleted

**`allowlist`/`detection_types` references in other tests:**
- `tests/unit/test_secrets_filter_plugin.py`
- `tests/fixtures/golden_configs/basic_secrets_filter/edge.yaml`
- `tests/validation/manual-validation-config.yaml`
- Various integration tests may have references

**`instruction_override`/`context_breaking` references (rename to `context_hijacking`):**
- `tests/unit/test_prompt_injection_defense_plugin.py`
- `tests/unit/test_prompt_injection_sensitivity.py`
- `tests/validation/manual-validation-config.yaml`
- `tests/validation/manual-validation-config-win.yaml`
- `tests/fixtures/golden_configs/basic_prompt_injection_defense/edge.yaml`
- `tests/fixtures/golden_configs/basic_prompt_injection_defense/typical.yaml`

### 4. Verify Schema Catches Errors

Add test to verify schema validation catches what runtime used to catch:

```python
# tests/unit/test_schema_validation_coverage.py

from gatekit.config.json_schema import get_schema_validator

def test_schema_rejects_invalid_display_name():
    """Schema should reject display_name with spaces."""
    validator = get_schema_validator()
    config = {
        "enabled": True,
        "tools": [{"tool": "test", "display_name": "Has Spaces"}]
    }
    errors = validator.validate("tool_manager", config)
    assert errors, "Schema should reject display_name with spaces"

def test_schema_rejects_invalid_action():
    """Schema should reject invalid action enum."""
    validator = get_schema_validator()
    errors = validator.validate("basic_pii_filter", {
        "enabled": True,
        "action": "invalid_action"
    })
    assert errors, "Schema should reject invalid action"

def test_schema_rejects_invalid_quote_style():
    """Schema should reject invalid quote_style."""
    validator = get_schema_validator()
    errors = validator.validate("audit_csv", {  # Note: handler ID is "audit_csv"
        "enabled": True,
        "output_file": "test.csv",
        "csv_config": {"quote_style": "invalid"}
    })
    assert errors, "Schema should reject invalid quote_style"
```

### 5. Verify Business Logic Still Works

```python
def test_duplicate_tool_still_rejected():
    """Business logic should catch duplicates."""
    from gatekit.plugins.middleware.tool_manager import ToolManagerPlugin
    config = {
        "enabled": True,
        "tools": [{"tool": "read_file"}, {"tool": "read_file"}]
    }
    with pytest.raises(ValueError, match="Duplicate"):
        ToolManagerPlugin(config)

def test_self_rename_still_rejected():
    """Business logic should reject self-rename."""
    from gatekit.plugins.middleware.tool_manager import ToolManagerPlugin
    config = {
        "enabled": True,
        "tools": [{"tool": "test", "display_name": "test"}]
    }
    with pytest.raises(ValueError, match="Cannot rename.*to itself"):
        ToolManagerPlugin(config)
```

### 6. Verify Orphaned Fields Are Rejected by Schema

```python
def test_schema_rejects_custom_patterns():
    """Schema should reject custom_patterns (removed feature)."""
    validator = get_schema_validator()
    errors = validator.validate("basic_pii_filter", {
        "enabled": True,
        "action": "redact",
        "custom_patterns": [{"pattern": "test", "name": "test"}]
    })
    assert errors, "Schema should reject custom_patterns field"

def test_schema_rejects_pretty_print():
    """Schema should reject pretty_print (removed feature)."""
    validator = get_schema_validator()
    errors = validator.validate("audit_jsonl", {  # Note: handler ID is "audit_jsonl"
        "enabled": True,
        "output_file": "test.jsonl",
        "pretty_print": True
    })
    assert errors, "Schema should reject pretty_print field"

def test_schema_rejects_allowlist():
    """Schema should reject allowlist (removed feature)."""
    validator = get_schema_validator()
    errors = validator.validate("basic_secrets_filter", {
        "enabled": True,
        "action": "redact",
        "allowlist": {"patterns": ["test"]}
    })
    assert errors, "Schema should reject allowlist field"

def test_schema_rejects_detection_types():
    """Schema should reject detection_types (use secret_types instead)."""
    validator = get_schema_validator()
    errors = validator.validate("basic_secrets_filter", {
        "enabled": True,
        "action": "redact",
        "detection_types": {}  # Legacy field name
    })
    assert errors, "Schema should reject detection_types field"

def test_schema_rejects_display_description_null():
    """Schema should reject display_description: null (use omission instead)."""
    validator = get_schema_validator()
    errors = validator.validate("tool_manager", {
        "enabled": True,
        "tools": [{"tool": "test", "display_description": None}]
    })
    assert errors, "Schema should reject display_description: null"
```

### 7. Manual TUI Verification

1. Run `gatekit`
2. Configure tool manager plugin
3. Enter display_name with spaces: "Has Spaces"
4. Click OK
5. **Expected**: Inline validation error, modal does not dismiss

### 8. Final Verification
```bash
pytest tests/ -n auto --cov=gatekit
uv run ruff check gatekit
```

---

## Implementation Approach: TDD

This plan should be implemented using Test-Driven Development:

1. **Write/update tests first** - Before modifying plugin code, write the schema validation tests that verify the expected behavior
2. **Run tests to see them fail** - Confirm tests fail for the right reasons (e.g., schema doesn't reject field yet, orphaned code still exists)
3. **Implement the changes** - Modify plugin code to make tests pass
4. **Refactor** - Clean up while keeping tests green

For each plugin:
1. Write schema rejection tests for removed fields (custom_patterns, allowlist, etc.)
2. Update/remove tests that use orphaned features
3. Remove orphaned code from plugin
4. Remove redundant validation
5. Verify all tests pass

---

## Implementation Order

1. tool_manager.py (highest impact, already partially fixed)
2. csv.py (simple)
3. pii.py + update tests (remove custom_patterns tests)
4. secrets.py + update tests (remove custom_patterns tests)
5. prompt_injection.py + update tests (remove custom_patterns tests)
6. json_lines.py + update tests (remove pretty_print tests)
7. Update fixture files (golden_configs, manual-validation-config.yaml)
8. Add schema validation coverage tests

Run `pytest tests/ -n auto && uv run ruff check gatekit` after each file.
