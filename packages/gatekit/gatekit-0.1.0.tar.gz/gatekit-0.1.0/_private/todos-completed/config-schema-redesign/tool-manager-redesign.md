# Tool Manager Configuration Redesign

## Current Problems

The tool_manager plugin has the most complex schema issues:

1. **Mixed type arrays** - `allow` can contain strings OR objects
2. **Dynamic object keys** - Renaming uses the tool name as a dynamic key
3. **Implicit structure** - Whether something is renamed depends on its type

## Proposed Redesign Options

### Option A: Flat Rule List (Recommended)

```yaml
tool_manager:
  # All rules in a single flat list
  rules:
    - tool: read_file
      action: allow
      
    - tool: write_file
      action: allow
      
    - tool: execute
      action: allow
      display_name: execute_sql_query
      display_description: "Execute SQL queries on production database"
      
    - tool: dangerous_tool
      action: block
      
    - tool: query
      action: allow
      display_name: query_database
      # No display_description means keep original
```

**JSON Schema**:
```json
{
  "type": "object",
  "properties": {
    "tool_manager": {
      "type": "object",
      "properties": {
        "rules": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "tool": {
                "type": "string",
                "pattern": "^[a-zA-Z_][a-zA-Z0-9_]{0,63}$"
              },
              "action": {
                "type": "string",
                "enum": ["allow", "block"]
              },
              "display_name": {
                "type": "string",
                "pattern": "^[a-zA-Z_][a-zA-Z0-9_]{0,63}$"
              },
              "display_description": {
                "type": "string"
              }
            },
            "required": ["tool", "action"]
          }
        }
      }
    }
  }
}
```

### Option B: Separate Lists by Action

```yaml
tool_manager:
  allowed:
    - name: read_file
    
    - name: write_file
    
    - name: execute
      display_name: execute_sql_query
      display_description: "Execute SQL queries"
      
    - name: query
      display_name: query_database
      
  blocked:
    - name: dangerous_tool
    
    - name: internal_debug_tool
```

### Option C: Database-Style Normalization

```yaml
tool_manager:
  default_action: block  # or allow
  
  tools:
    - name: read_file
      allowed: true
      
    - name: execute
      allowed: true
      display_name: execute_sql_query
      display_description: "Execute SQL queries"
      
    - name: dangerous_tool
      allowed: false
```

## Comparison

| Aspect | Option A (Rules) | Option B (Separate) | Option C (Database) |
|--------|------------------|---------------------|---------------------|
| Clarity | ⭐⭐⭐ Explicit action | ⭐⭐ Action from list | ⭐⭐ Needs default |
| Extensibility | ⭐⭐⭐ Easy to add fields | ⭐⭐ Duplicate structure | ⭐⭐⭐ Single structure |
| TUI Complexity | ⭐⭐⭐ Single list widget | ⭐⭐ Multiple lists | ⭐⭐⭐ Single list |
| Validation | ⭐⭐⭐ Simple schema | ⭐⭐ Two schemas | ⭐⭐⭐ Simple schema |
| Migration | ⭐⭐ Significant change | ⭐⭐ Significant change | ⭐⭐ Significant change |

## Recommendation: Option A (Flat Rule List)

Reasons:
1. **Most explicit** - Each rule clearly states its action
2. **Most extensible** - Easy to add new fields (priority, conditions, etc.)
3. **Best for TUI** - Single list to manage
4. **Best for AI** - Clear, consistent structure
5. **Follows industry patterns** - Similar to firewall rules, ACLs, etc.

## Migration Path

### Phase 1: Support Both Formats
```python
def __init__(self, config):
    # New format
    if "rules" in config:
        self._parse_rules_config(config["rules"])
    # Legacy format
    elif "allow" in config or "allow_all_except" in config:
        self._parse_legacy_config(config)
    else:
        raise ValueError("Configuration must include 'rules'")
```

### Phase 2: Migration Tool
```python
def migrate_config(old_config):
    """Convert old format to new rules format."""
    rules = []
    
    if "allow" in old_config:
        for item in old_config["allow"]:
            if isinstance(item, str):
                rules.append({"tool": item, "action": "allow"})
            else:
                # Handle renamed tools
                for tool, settings in item.items():
                    rule = {"tool": tool, "action": "allow"}
                    if "name" in settings:
                        rule["display_name"] = settings["name"]
                    if "description" in settings:
                        rule["display_description"] = settings["description"]
                    rules.append(rule)
    
    return {"rules": rules}
```

### Phase 3: Update Documentation
- Show new format in all examples
- Provide migration guide
- Update schema documentation

## Benefits of New Format

1. **TUI Implementation**: Trivial - just a list of forms
2. **Validation**: Simple JSON Schema, no oneOf or additionalProperties
3. **IDE Support**: Full autocomplete with JSON Schema
4. **AI Generation**: Consistent, predictable structure
5. **Human Readable**: Still reasonably clear even if not hand-edited
6. **Future Proof**: Easy to extend with new fields

## Example: Complex Configuration

```yaml
tool_manager:
  rules:
    # Simple allows
    - tool: read_file
      action: allow
    - tool: list_directory
      action: allow
      
    # Renamed tools for clarity
    - tool: execute
      action: allow
      display_name: execute_safe_command
      display_description: "Execute pre-approved safe commands only"
      
    - tool: query
      action: allow  
      display_name: query_readonly_database
      display_description: "Read-only database queries"
      
    # Blocked tools
    - tool: delete_everything
      action: block
    - tool: format_drive
      action: block
      
    # Future: Could add conditions
    # - tool: write_file
    #   action: allow
    #   condition: "path.startswith('/tmp')"
```

This structure is:
- ✅ Fully JSON Schema compatible
- ✅ Easy for TUI to generate forms
- ✅ Clear and unambiguous
- ✅ Extensible for future features
- ✅ Validatable with standard tools