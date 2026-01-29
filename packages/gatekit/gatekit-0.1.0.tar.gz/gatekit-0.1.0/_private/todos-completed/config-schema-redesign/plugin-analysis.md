# Plugin Schema Compatibility Analysis

## Overview

Analysis of each plugin's current schema to identify JSON Schema compatibility issues and required changes.

## Plugin Analysis

### 1. Tool Manager (middleware/tool_manager.py)
**Compatibility: ❌ MAJOR ISSUES**

Problems:
- `allow` field uses `oneOf` with mixed types (string | object)
- Objects have dynamic keys via `additionalProperties`
- Complex nested structure for renaming

Required Changes:
- Flatten to homogeneous list structure
- Replace dynamic keys with explicit fields
- Separate allow/block/rename into discrete operations

### 2. PII Filter (security/pii.py)
**Compatibility: ✅ MOSTLY COMPATIBLE**

Structure:
- Nested object for `pii_types` with known keys
- Dynamic property generation but with fixed set of types
- Uses list comprehension in schema definition

Minor Issues:
- Dynamic property generation from `cls.PII_TYPES`
- Conditional properties based on `cls.PII_FORMATS`

Required Changes:
- Convert dynamic generation to static schema
- Could be used as-is with JSON Schema

### 3. Secrets Filter (security/secrets.py)
**Compatibility: ✅ MOSTLY COMPATIBLE**

Structure:
- Similar to PII filter
- Nested object for `secret_types`
- Entropy detection as nested object

Minor Issues:
- Dynamic property generation from `cls.SECRET_TYPES`

Required Changes:
- Convert to static schema definition
- Already well-structured for JSON Schema

### 4. Prompt Injection (security/prompt_injection.py)
**Compatibility: ✅ FULLY COMPATIBLE**

Structure:
- Simple flat configuration
- Only uses basic types (boolean, string, number, enum)
- No dynamic or complex structures

Required Changes:
- None - can directly convert to JSON Schema

### 5. CSV Auditing (auditing/csv.py)
**Compatibility: ✅ FULLY COMPATIBLE**

Structure:
- Nested `csv_config` object with fixed properties
- All properties have known keys
- Uses basic types

Required Changes:
- None - maps directly to JSON Schema

### 6. JSON Lines Auditing (auditing/json_lines.py)
**Compatibility: ✅ FULLY COMPATIBLE**

Structure:
- Simple configuration with basic types
- Fixed property names
- No dynamic structures

Required Changes:
- None - ready for JSON Schema

### 7. Human Readable Auditing (auditing/human_readable.py)
**Compatibility: ✅ FULLY COMPATIBLE**

Structure:
- Basic configuration options
- All fixed keys
- Simple types only

Required Changes:
- None - ready for JSON Schema

### 8. Filesystem Server (security/filesystem_server.py)
**Compatibility: ✅ FULLY COMPATIBLE**

Structure:
- List of patterns (strings)
- Simple object for path restrictions
- No complex structures

Required Changes:
- None - ready for JSON Schema

## Summary

| Plugin | Compatibility | Major Issues | Migration Effort |
|--------|--------------|--------------|------------------|
| Tool Manager | ❌ | oneOf, additionalProperties | High |
| PII Filter | ✅ | Dynamic generation | Low |
| Secrets Filter | ✅ | Dynamic generation | Low |
| Prompt Injection | ✅ | None | None |
| CSV Auditing | ✅ | None | None |
| JSON Lines | ✅ | None | None |
| Human Readable | ✅ | None | None |
| Filesystem Server | ✅ | None | None |

## Patterns to Standardize

### 1. Dynamic Type Lists (PII, Secrets)
Current:
```python
"properties": {
    pii_type: {...} for pii_type in cls.PII_TYPES
}
```

Proposed:
- Generate static schema at build time
- Or use JSON Schema definitions with `$ref`

### 2. Mixed Type Arrays (Tool Manager)
Current:
```yaml
items:
  oneOf: [string, object]
```

Proposed:
- Always use objects with optional fields
- Or separate into different arrays

### 3. Dynamic Keys (Tool Manager)
Current:
```yaml
execute:  # dynamic key
  name: new_name
```

Proposed:
```yaml
- tool: execute  # explicit field
  rename_to: new_name
```

## Migration Strategy

1. **Phase 1**: Update tool_manager to new structure (highest impact)
2. **Phase 2**: Convert dynamic schemas (PII, Secrets) to static
3. **Phase 3**: Add JSON Schema generation to all plugins
4. **Phase 4**: Update TUI to use JSON Schema for validation
5. **Phase 5**: Add IDE integration documentation

## Benefits After Migration

- Standard validation across all plugins
- IDE autocomplete for all config files  
- Automatic documentation generation
- TUI can use schema-to-form libraries
- Third-party tool compatibility
- Reduced maintenance burden