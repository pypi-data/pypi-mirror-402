# Phase 2: JSON Schema Adoption for All Plugins

## Overview
Convert all Gatekit plugin configuration schemas from the custom format to industry-standard JSON Schema. This provides better tooling support, IDE autocomplete, and standardized validation.

## Prerequisites
- Phase 1 (Tool Manager Configuration Restructure) must be complete
- All tests passing with new tool_manager tools format
- Python 3.11+ environment
- Understanding of JSON Schema specification (2020-12)

## Success Criteria
- [ ] All plugins have JSON Schema definitions
- [ ] Schema validation using jsonschema library works
- [ ] Generated .schema.json files for IDE support
- [ ] All tests pass

## Dependencies to Add
```toml
# In pyproject.toml or requirements.txt
jsonschema = "^4.20.0"  # For schema validation
```

## Implementation Steps

### Step 1: Create Centralized JSON Schema Validator
**File:** `/Users/dbright/mcp/gatekit/gatekit/config/json_schema.py` (new file)

**Note:** There's an existing custom validator at `gatekit/plugins/schema.py` - we're creating a NEW JSON Schema-based validator in a different location to avoid confusion. The old validator will be deprecated.

Create a centralized JSON Schema validator to replace the old custom validator:

```python
"""Centralized JSON Schema validation for Gatekit."""

from jsonschema import Draft202012Validator, ValidationError
from typing import Dict, Any, List, Optional
import json
from pathlib import Path

class SchemaValidator:
    """Centralized validator supporting JSON Schema 2020-12."""
    
    def __init__(self):
        self.validator_class = Draft202012Validator
        self.validators: Dict[str, Draft202012Validator] = {}
        # Use local $defs to avoid network fetches
        self._load_schemas()
    
    def _load_schemas(self):
        """Load all plugin schemas dynamically."""
        from gatekit.plugins import discover_all_plugins
        
        plugins = discover_all_plugins()
        for plugin_name, plugin_class in plugins.items():
            if hasattr(plugin_class, 'get_json_schema'):
                schema = plugin_class.get_json_schema()
                # Use Draft202012Validator explicitly
                self.validators[plugin_name] = Draft202012Validator(schema)
    
    def validate(self, handler_name: str, config: Dict[str, Any]) -> List[str]:
        """Validate a plugin configuration.
        
        Returns list of error messages with JSON pointer paths for context.
        """
        if handler_name not in self.validators:
            return [f"No schema found for handler '{handler_name}'"]
        
        validator = self.validators[handler_name]
        errors = []
        
        for error in validator.iter_errors(config):
            # Include JSON pointer path for better error context
            error_path = "/" + "/".join(str(p) for p in error.absolute_path) if error.absolute_path else ""
            errors.append(f"{handler_name}{error_path}: {error.message}")
        
        return errors
```

Then update TUI to import from this central location:
```python
# In gatekit/tui/utils/schema.py
from gatekit.config.json_schema import SchemaValidator
# Re-export for backward compatibility if needed
```

### Step 2: Add JSON Schema Support to Base Classes

#### 1.1: Update Plugin Base Class
**File:** `/Users/dbright/mcp/gatekit/gatekit/plugins/interfaces.py`

Add a new method to the base plugin class:

```python
from typing import Dict, Any, Optional
import json

class BasePlugin:
    """Base class for all plugins."""
    
    @classmethod
    def get_json_schema(cls) -> Dict[str, Any]:
        """Return JSON Schema for this plugin's configuration.
        
        Returns:
            Dict containing JSON Schema (2020-12) for plugin configuration
        """
        # Plugins should override this with their specific schema
        raise NotImplementedError("Plugin must implement get_json_schema")
```

### Step 2: Convert Tool Manager Plugin

#### 2.1: Implement get_json_schema for Tool Manager
**File:** `/Users/dbright/mcp/gatekit/gatekit/plugins/middleware/tool_manager.py`

Add this method to ToolManagerPlugin class:

```python
@classmethod
def get_json_schema(cls) -> Dict[str, Any]:
    """Return JSON Schema for Tool Manager configuration.
    
    Important semantics:
    - Empty allowlist (action=allow with no tools) blocks ALL tools
    - Empty blocklist (action=deny with no tools) allows ALL tools
    """
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://gatekit.dev/schemas/tool-manager.json",
        "type": "object",
        "description": "Tool Manager middleware plugin configuration",
        "properties": {
            "configVersion": {
                "type": "string",
                "description": "Configuration format version",
                "const": "1.0"
            },
            "enabled": {
                "type": "boolean",
                "description": "Enable tool access control",
                "default": true
            },
            "priority": {
                "type": "number",
                "description": "Plugin execution priority (0-100, lower = higher priority)",
                "default": 50,
                "minimum": 0,
                "maximum": 100
            },
            "tools": {
                "type": "array",
                "description": "List of tool configurations. Empty allowlist blocks all tools. Empty blocklist allows all tools.",
                "items": {
                    "type": "object",
                    "properties": {
                        "tool": {
                            "type": "string",
                            "pattern": "^[a-zA-Z][a-zA-Z0-9_-]*$",
                            "description": "Original tool name"
                        },
                        "action": {
                            "type": "string",
                            "enum": ["allow", "deny"],
                            "description": "Whether to allow or deny this tool"
                        },
                        "display_name": {
                            "type": "string",
                            "pattern": "^[a-zA-Z][a-zA-Z0-9_-]*$",
                            "description": "Name to show to clients (for renaming)"
                        },
                        "display_description": {
                            "type": "string",
                            "description": "Description to show to clients"
                        }
                    },
                    "required": ["tool", "action"],
                    "additionalProperties": false,
                    "unevaluatedProperties": false
                }
            }
        },
        "required": ["tools"],
        "additionalProperties": false,
        "unevaluatedProperties": false
    }
```

### Step 3: Add Common Schema Definitions
**File:** `/Users/dbright/mcp/gatekit/gatekit/config/schema_defs.py` (new file)

Place in `gatekit/config/` to avoid circular imports. Create shared schema definitions to reduce duplication:

```python
"""Common JSON Schema definitions for all plugins."""

COMMON_DEFS = {
    "enabled": {
        "type": "boolean",
        "description": "Enable this plugin",
        "default": True
    },
    "priority": {
        "type": "integer",
        "description": "Plugin execution priority (0-100, lower = higher priority)",
        "default": 50,
        "minimum": 0,
        "maximum": 100
    },
    "file_path": {
        "type": "string",
        "description": "Path to file (supports ~ expansion and date formatting)"
    }
}
```

### Step 4: Convert Security Plugins

#### 4.1: PII Filter Plugin
**File:** `/Users/dbright/mcp/gatekit/gatekit/plugins/security/pii.py`

```python
@classmethod
def get_json_schema(cls) -> Dict[str, Any]:
    """Return JSON Schema for PII Filter configuration."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://gatekit.dev/schemas/pii-filter.json",
        "type": "object",
        "description": "PII Filter security plugin configuration",
        "$defs": {
            "patternConfig": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "default": true},
                    "pattern": {"type": "string"},
                    "action": {
                        "type": "string",
                        "enum": ["block", "redact"],
                        "default": "redact"
                    },
                    "redaction_text": {"type": "string"}
                },
                "additionalProperties": false
            }
        },
        "properties": {
            "enabled": {
                "type": "boolean",
                "description": "Enable PII filtering",
                "default": true
            },
            "patterns": {
                "type": "object",
                "description": "PII pattern configurations",
                "properties": {
                    "ssn": {"$ref": "#/$defs/patternConfig"},
                    "credit_card": {
                        "allOf": [{"$ref": "#/$defs/patternConfig"}],
                        "properties": {
                            "validate_luhn": {
                                "type": "boolean",
                                "description": "Validate credit card numbers using Luhn algorithm",
                                "default": true
                            }
                        }
                    },
                    "email": {"$ref": "#/$defs/patternConfig"},
                    "phone": {"$ref": "#/$defs/patternConfig"}
                },
                "additionalProperties": false
            },
            "custom_patterns": {
                "type": "array",
                "description": "Additional custom PII patterns",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "pattern": {"type": "string"},
                        "action": {
                            "type": "string",
                            "enum": ["block", "redact"]
                        },
                        "redaction_text": {"type": "string"}
                    },
                    "required": ["name", "pattern", "action"],
                    "additionalProperties": false
                }
            }
        },
        "additionalProperties": false,
        "unevaluatedProperties": false
    }
```

#### 4.2: Secrets Filter Plugin
**File:** `/Users/dbright/mcp/gatekit/gatekit/plugins/security/secrets.py`

Similar pattern using `$defs` for reusable pattern configurations.

#### 4.3: Prompt Injection Plugin
**File:** `/Users/dbright/mcp/gatekit/gatekit/plugins/security/prompt_injection.py`

```python
@classmethod
def get_json_schema(cls) -> Dict[str, Any]:
    """Return JSON Schema for Prompt Injection configuration."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://gatekit.dev/schemas/prompt-injection.json",
        "type": "object",
        "description": "Prompt Injection detection plugin configuration",
        "properties": {
            "enabled": {
                "type": "boolean",
                "description": "Enable prompt injection detection",
                "default": true
            },
            "sensitivity": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Detection sensitivity level",
                "default": "medium"
            },
            "block_on_detection": {
                "type": "boolean",
                "description": "Block requests when injection is detected",
                "default": true
            },
            "patterns": {
                "type": "array",
                "description": "Custom injection patterns to detect",
                "items": {"type": "string"}
            }
        },
        "additionalProperties": false,
        "unevaluatedProperties": false
    }
```

### Step 5: Convert Auditing Plugins

#### 5.1: CSV Auditing Plugin
**File:** `/Users/dbright/mcp/gatekit/gatekit/plugins/auditing/csv.py`

```python
@classmethod
def get_json_schema(cls) -> Dict[str, Any]:
    """Return JSON Schema for CSV Auditing configuration."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://gatekit.dev/schemas/csv-auditing.json",
        "type": "object",
        "description": "CSV audit logging plugin configuration",
        "properties": {
            "enabled": {
                "type": "boolean",
                "description": "Enable CSV audit logging",
                "default": true
            },
            "file_path": {
                "type": "string",
                "description": "Path to CSV log file (supports date formatting)",
                "default": "gatekit_audit_{date}.csv"
            },
            "include_request_params": {
                "type": "boolean",
                "description": "Include request parameters in logs",
                "default": true
            },
            "include_response_data": {
                "type": "boolean",
                "description": "Include response data in logs",
                "default": false
            },
            "max_field_length": {
                "type": "integer",
                "description": "Maximum length for logged fields",
                "default": 1000,
                "minimum": 100
            },
            "fields": {
                "type": "array",
                "description": "CSV fields to include",
                "items": {
                    "type": "string",
                    "enum": [
                        "timestamp",
                        "server_name",
                        "method",
                        "tool_name",
                        "decision",
                        "reason",
                        "request_params",
                        "response_data",
                        "error"
                    ]
                },
                "default": ["timestamp", "server_name", "method", "tool_name", "decision", "reason"]
            }
        },
        "additionalProperties": false,
        "unevaluatedProperties": false
    }
```

Similar patterns for JSON Lines and Human Readable auditing plugins.

### Step 6: Update Special Server Plugins

#### 6.1: Filesystem Server Plugin
**File:** `/Users/dbright/mcp/gatekit/gatekit/plugins/security/filesystem_server.py`

Include proper JSON Schema with `$id` and use `$defs` for common patterns.

### Step 7: Update Configuration Loader

#### 7.1: Configuration Loader Integration
**File:** `/Users/dbright/mcp/gatekit/gatekit/core/config_loader.py`

Integrate schema validation into configuration loading:

```python
from gatekit.config.json_schema import SchemaValidator
import yaml

class ConfigLoader:
    """Loads and validates Gatekit configuration."""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.validator = SchemaValidator()
    
    def load(self) -> Dict[str, Any]:
        """Load and validate configuration."""
        # Load YAML
        with open(self.config_path) as f:
            config = yaml.safe_load(f)
        
        # Validate each plugin configuration
        errors = []
        for server_config in config.get("servers", {}).values():
            for plugin_type in ["security", "auditing", "middleware"]:
                for plugin_config in server_config.get(plugin_type, []):
                    handler_name = plugin_config.get("handler")
                    if handler_name:
                        validation_errors = self.validator.validate(handler_name, plugin_config)
                        if validation_errors:
                            errors.extend([f"{handler_name}: {e}" for e in validation_errors])
        
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))
        
        return config
```

### Step 8: Generate Schema Files for IDE Support

#### 8.1: Create Schema Generation Script
**File:** `/Users/dbright/mcp/gatekit/scripts/generate_schemas.py`

```python
#!/usr/bin/env python3
"""Generate JSON Schema files for all plugins."""

import json
import sys
from pathlib import Path

# Add gatekit to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gatekit.plugins import discover_all_plugins

def generate_schemas():
    """Generate JSON Schema files for all plugins."""
    output_dir = Path(__file__).parent.parent / "schemas"
    output_dir.mkdir(exist_ok=True)
    
    # Generate combined schema for gatekit.yaml
    combined_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://gatekit.dev/schemas/gatekit.json",
        "type": "object",
        "properties": {
            "servers": {
                "type": "object",
                "patternProperties": {
                    "^[a-zA-Z_][a-zA-Z0-9_-]*$": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"},
                            "args": {"type": "array", "items": {"type": "string"}},
                            "env": {"type": "object"},
                            "security": {"type": "array"},
                            "auditing": {"type": "array"},
                            "middleware": {"type": "array"}
                        }
                    }
                }
            }
        },
        "$defs": {}
    }
    
    # Generate individual plugin schemas
    plugins = discover_all_plugins()
    
    for handler_name, plugin_class in plugins.items():
        if hasattr(plugin_class, 'get_json_schema'):
            schema = plugin_class.get_json_schema()
            
            # Save individual schema
            schema_file = output_dir / f"{handler_name}.schema.json"
            with open(schema_file, 'w') as f:
                json.dump(schema, f, indent=2)
            
            print(f"Generated schema: {schema_file}")
            
            # Add to combined schema $defs
            combined_schema["$defs"][handler_name] = schema
    
    # Save combined schema
    combined_file = output_dir / "gatekit.schema.json"
    with open(combined_file, 'w') as f:
        json.dump(combined_schema, f, indent=2)
    
    print(f"Generated combined schema: {combined_file}")
    
    # Generate VS Code settings recommendation
    vscode_settings = {
        "yaml.schemas": {
            "./schemas/gatekit.schema.json": ["gatekit.yaml", "gatekit.yml"]
        }
    }
    
    vscode_file = output_dir / "vscode-settings.json"
    with open(vscode_file, 'w') as f:
        json.dump(vscode_settings, f, indent=2)
    
    print(f"Generated VS Code settings: {vscode_file}")
    print("\nTo enable IDE support, add the contents of vscode-settings.json to your .vscode/settings.json")

if __name__ == "__main__":
    generate_schemas()
```

### Step 9: Add VS Code Settings

#### 9.1: Create VS Code Settings Template
**File:** `/Users/dbright/mcp/gatekit/.vscode/settings.json.template`

```json
{
  "yaml.schemas": {
    "./schemas/gatekit.schema.json": [
      "gatekit.yaml",
      "gatekit.yml",
      "configs/*.yaml",
      "configs/**/*.yaml"
    ]
  }
}
```

Copy this to `.vscode/settings.json` for IDE support. Consider committing generated schemas for consistent `$id` resolution.

### Step 10: Update Tests

#### 10.1: Add Schema Validation Tests
**File:** `/Users/dbright/mcp/gatekit/tests/unit/test_schema_validation.py`

```python
"""Test JSON Schema validation for all plugins."""

import pytest
from gatekit.config.json_schema import SchemaValidator
from jsonschema import Draft202012Validator

class TestSchemaValidation:
    """Test schema validation for plugins."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SchemaValidator()
    
    def test_tool_manager_valid_tools(self):
        """Test valid tool_manager tools configuration."""
        config = {
            "enabled": True,
            "tools": [
                {"tool": "read-file", "action": "allow"},
                {"tool": "execute", "action": "allow", "display_name": "run-command"}
            ]
        }
        assert self.validator.is_valid("tool_manager", config)
    
    def test_tool_manager_invalid_mixed_actions(self):
        """Test that mixing allow/deny is caught in plugin init."""
        config = {
            "enabled": True,
            "tools": [
                {"tool": "read-file", "action": "allow"},
                {"tool": "dangerous", "action": "deny"}  # Mixed!
            ]
        }
        # Schema allows this, but plugin __init__ should catch it
        errors = self.validator.validate("tool_manager", config)
        assert len(errors) == 0  # Schema valid, business logic in __init__
    
    def test_tool_manager_empty_allowlist(self):
        """Test that empty allowlist blocks all tools."""
        config = {
            "enabled": True,
            "tools": []  # Empty with action=allow blocks all
        }
        # Document this behavior
        plugin = ToolManagerPlugin(config)
        assert plugin.mode == "allowlist"
        assert len(plugin.tools) == 0  # Blocks all tools
    
    def test_tool_manager_empty_blocklist(self):
        """Test that empty blocklist allows all tools."""
        config = {
            "enabled": True,
            "tools": []  # Would need first tool to determine mode
        }
        # Document this behavior
        # Note: Implementation detail - need at least one tool to determine mode
        pass
    
    def test_json_pointer_paths_in_errors(self):
        """Test that errors include JSON pointer paths."""
        config = {
            "enabled": True,
            "tools": [
                {"action": "allow"}  # Missing "tool" field
            ]
        }
        errors = self.validator.validate("tool_manager", config)
        assert any("/tools/0/tool" in error for error in errors)
    
    def test_duplicate_tool_names(self):
        """Test that duplicate tool names are caught."""
        config = {
            "enabled": True,
            "tools": [
                {"tool": "read-file", "action": "allow"},
                {"tool": "read-file", "action": "allow"}  # Duplicate!
            ]
        }
        # This should be caught by plugin __init__
        with pytest.raises(ValueError, match="Duplicate"):
            ToolManagerPlugin(config)
    
    def test_self_rename(self):
        """Test that self-rename is caught."""
        config = {
            "enabled": True,
            "tools": [
                {"tool": "read-file", "action": "allow", 
                 "display_name": "read-file"}  # Self-rename!
            ]
        }
        with pytest.raises(ValueError, match="to itself"):
            ToolManagerPlugin(config)
    
    def test_duplicate_display_names(self):
        """Test that duplicate display names are caught."""
        config = {
            "enabled": True,
            "tools": [
                {"tool": "read-file", "action": "allow", 
                 "display_name": "safe-read"},
                {"tool": "write-file", "action": "allow",
                 "display_name": "safe-read"}  # Duplicate display name!
            ]
        }
        with pytest.raises(ValueError, match="already renamed"):
            ToolManagerPlugin(config)
    
    def test_invalid_tool_name_pattern(self):
        """Test that invalid tool names are rejected."""
        config = {
            "enabled": True,
            "tools": [
                {"tool": "123-invalid", "action": "allow"}  # Starts with number!
            ]
        }
        errors = self.validator.validate("tool_manager", config)
        assert len(errors) > 0
        assert any("pattern" in error.lower() for error in errors)
```

### Step 11: CI Integration  

Add to CI pipeline (e.g., in GitHub Actions or similar):
```yaml
- name: Generate JSON Schemas
  run: python scripts/generate_schemas.py
  
- name: Validate Schemas
  run: python -m jsonschema.cli --version 2020-12 schemas/*.schema.json
```

## Verification Checklist

- [ ] All plugins have `get_json_schema()` method returning 2020-12 schemas
- [ ] All schemas have `$id` fields with stable URLs
- [ ] Common patterns use `$defs` for reusability
- [ ] Schema generation script works
- [ ] All schema files generated in `schemas/` directory
- [ ] JSON Schema validation passes for valid configs
- [ ] JSON Schema validation fails for invalid configs
- [ ] IDE autocomplete works in VS Code
- [ ] All existing tests still pass
- [ ] New schema validation tests pass

## Notes for Implementation

- **Use Draft202012Validator explicitly** - Don't rely on default validator
- **Centralize schema validation** - Use `gatekit/config/schema.py` to avoid duplication
- **Include JSON pointer paths in errors** - Better UX with context
- Add `$id` to each schema for stable referencing
- Use `$defs` for common patterns (enabled, priority, file_path)
- Keep `additionalProperties: false` for strictness (no `x-*` extensions in v1)
- Business logic validation stays in plugin `__init__` (e.g., mixed allow/deny)
- Generate schemas to `./schemas/` directory for IDE support
- Use local `$defs` to avoid network fetches
- Test with Draft 2020-12 validator explicitly