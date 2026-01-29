# Phase 1: Tool Manager Configuration Restructure

## Overview
Convert the tool_manager plugin from its current mixed-type array format to a homogeneous tool configuration structure. This change eliminates `oneOf` schemas and `additionalProperties`, making the configuration machine-parseable for TUI serialization.

## Prerequisites
- Python 3.11+ development environment
- All existing tests passing (`pytest tests/`)
- Understanding of current tool_manager functionality

## Success Criteria
- [ ] All tests pass with updated test configurations
- [ ] New tools format works correctly
- [ ] All config files updated to new format
- [ ] No regression in functionality

## Current Problem
The current format mixes strings and objects in the same array:
```yaml
tool_manager:
  allow:
    - read_file              # String
    - write_file             # String  
    - execute:               # Object with dynamic key!
        name: run_command
        description: "Execute commands"
```

This requires `oneOf` in the schema and uses the tool name as a dynamic key, preventing proper TUI form generation.

## New Format Design
```yaml
tool_manager:
  tools:
    - tool: read_file
      action: allow
      
    - tool: write_file
      action: allow
      
    - tool: execute
      action: allow
      display_name: run_command
      display_description: "Execute commands"
      
    - tool: dangerous_tool
      action: deny
```

Every item has the same structure. No dynamic keys. No mixed types.

## Implementation Steps

### Step 1: Update Schema Definition
**File:** `/Users/dbright/mcp/gatekit/gatekit/plugins/middleware/tool_manager.py`

In the `get_config_schema()` method, add the new `tools` field:

**Note:** The schema definition here uses Gatekit's internal format. This will be converted to JSON Schema 2020-12 in Phase 2.

```python
"tools": {
    "type": "list",
    "label": "Tool configurations",
    "description": "List of tools with their access permissions and display settings",
    "items": {
        "type": "object",
        "properties": {
            "tool": {
                "type": "string",
                "pattern": r"^[a-zA-Z][a-zA-Z0-9_-]*$",
                "description": "Original tool name",
                "required": True
            },
            "action": {
                "type": "string",
                "enum": ["allow", "deny"],
                "description": "Whether to allow or deny this tool",
                "required": True
            },
            "display_name": {
                "type": "string",
                "pattern": r"^[a-zA-Z][a-zA-Z0-9_-]*$",
                "description": "Name to show to clients (for renaming)",
                "required": False
            },
            "display_description": {
                "type": "string",
                "description": "Description to show to clients",
                "required": False
            }
        }
    },
    "required": False
}
```

Replace the existing `allow`, `allow_all_except`, and `also_rename` fields with the new `tools` field.

### Step 2: Add Tools Parser Method
Add a new method to parse the tools format:

```python
def _parse_tools_config(self, tools: List[Dict[str, Any]]) -> tuple[str, List[str], Dict[str, tuple[str, str|None]], Dict[str, str]]:
    """Parse 'tools' configuration into mode, tools list, and rename maps.
    
    Important semantics:
    - Empty list with action=allow (allowlist mode) blocks ALL tools
    - Empty list with action=deny (blocklist mode) allows ALL tools
    - Mode is determined by the first tool's action
    
    Returns:
        tuple: (mode, tools, rename_map, reverse_map)
        - mode: 'allowlist' or 'blocklist' 
        - tools: list of allowed/denied tool names
        - rename_map: original_name -> (new_name, new_description or None)
        - reverse_map: new_name -> original_name
    """
    if not isinstance(tools, list):
        raise ValueError("'tools' must be a list")
    
    # Determine mode based on tools content
    has_allow = any(t.get("action") == "allow" for t in tools if isinstance(t, dict))
    has_deny = any(t.get("action") == "deny" for t in tools if isinstance(t, dict))
    
    if has_allow and has_deny:
        raise ValueError("Cannot mix 'allow' and 'deny' actions in tools. Use either all 'allow' (allowlist mode) or all 'deny' (blocklist mode)")
    
    # Handle empty list - default to allowlist (blocks all)
    if not has_allow and not has_deny:
        if len(tools) == 0:
            # Empty list defaults to allowlist mode (blocks all tools)
            return "allowlist", [], {}, {}
        raise ValueError("Tools must contain at least one valid action")
    
    mode = "allowlist" if has_allow else "blocklist"
    tool_list = []
    rename_map = {}
    reverse_map = {}
    
    for tool_entry in tools:
        if not isinstance(tool_entry, dict):
            raise ValueError(f"Each tool entry must be a dictionary, got {type(tool_entry).__name__}")
        
        # Validate required fields
        if "tool" not in tool_entry:
            raise ValueError("Each tool entry must have a 'tool' field")
        if "action" not in tool_entry:
            raise ValueError("Each tool entry must have an 'action' field")
        
        tool_name = tool_entry["tool"]
        action = tool_entry["action"]
        
        # Validate tool name format
        if not isinstance(tool_name, str):
            raise ValueError(f"Tool name must be a string, got {type(tool_name).__name__}")
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", tool_name):
            raise ValueError(
                f"Invalid tool name '{tool_name}': must start with letter, "
                f"contain only letters, numbers, underscores, and hyphens"
            )
        
        # Validate action matches mode
        if mode == "allowlist" and action != "allow":
            raise ValueError(f"In allowlist mode, all actions must be 'allow', got '{action}' for tool '{tool_name}'")
        if mode == "blocklist" and action != "deny":
            raise ValueError(f"In blocklist mode, all actions must be 'deny', got '{action}' for tool '{tool_name}'")
        
        # Add to tools list
        if tool_name not in tool_list:
            tool_list.append(tool_name)
        else:
            raise ValueError(f"Duplicate entry for tool '{tool_name}'")
        
        # Handle renaming if present
        if "display_name" in tool_entry:
            new_name = tool_entry["display_name"]
            
            # Validate new name format
            if not isinstance(new_name, str):
                raise ValueError(f"Display name must be a string, got {type(new_name).__name__}")
            if not re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", new_name):
                raise ValueError(
                    f"Invalid display name '{new_name}': must start with letter, "
                    f"contain only letters, numbers, underscores, and hyphens"
                )
            
            # Validate not self-mapping
            if tool_name == new_name:
                raise ValueError(f"Cannot rename '{tool_name}' to itself")
            
            # Check for duplicate renamed names
            if new_name in reverse_map:
                raise ValueError(
                    f"Cannot rename '{tool_name}' to '{new_name}': "
                    f"'{reverse_map[new_name]}' is already renamed to '{new_name}'"
                )
            
            new_desc = tool_entry.get("display_description")
            rename_map[tool_name] = (new_name, new_desc)
            reverse_map[new_name] = tool_name
    
    return mode, tool_list, rename_map, reverse_map
```

### Step 3: Update __init__ Method
Modify the `__init__` method to use only the new format:

```python
def __init__(self, config: Dict[str, Any]):
    """Initialize plugin with configuration."""
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a dictionary")
    
    super().__init__(config)
    
    # Only support new tools format
    if "tools" not in config:
        raise ValueError("Configuration must include 'tools' field")
    
    self.mode, self.tools, self.rename_map, self.reverse_map = self._parse_tools_config(config["tools"])
```

### Step 4: Update describe_status Method
Update the status description to handle the new format:

```python
@classmethod
def describe_status(cls, config: Dict[str, Any]) -> str:
    """Generate status description from tool configuration."""
    if not config or not config.get("enabled", False):
        return "Optimize tool context for better agent performance"
    
    parts = []
    rename_count = 0
    
    # Only handle new tools format
    if "tools" not in config:
        return "Not configured"
    
    tools = config["tools"]
    if not tools:
        return "No tools configured"
    
    # Determine mode from first tool entry
    first_action = tools[0].get("action") if tools else None
    
    if first_action == "allow":
        tool_count = len(tools)
        rename_count = sum(1 for t in tools if "display_name" in t)
        if tool_count == 0:
            parts.append("Block all tools")
        else:
            parts.append(f"Allow only {tool_count} tools")
    elif first_action == "deny":
        tool_count = len(tools)
        if tool_count == 0:
            parts.append("Allow all tools")
        else:
            parts.append(f"Block {tool_count} tools")
    
    if rename_count > 0:
        parts.append(f"rename {rename_count}")
    
    return ", ".join(parts) if parts else "Not configured"
```

### Step 5: Update All Config Files

#### 5.1: Main config
**File:** `/Users/dbright/mcp/gatekit/configs/gatekit.yaml`

Find all `tool_manager` sections and convert them. Example:

**Before:**
```yaml
tool_manager:
  allow:
    - read_file
    - write_file
    - list_directory
```

**After:**
```yaml
tool_manager:
  tools:
    - tool: read_file
      action: allow
    - tool: write_file
      action: allow
    - tool: list_directory
      action: allow
```

#### 5.2: Validation config
**File:** `/Users/dbright/mcp/gatekit/tests/validation/validation-config.yaml`

Convert all three tool_manager instances. For renamed tools:

**Before:**
```yaml
tool_manager:
  allow:
    - read_file
    - execute:
        name: run_sql_query
        description: "Execute SQL queries"
```

**After:**
```yaml
tool_manager:
  tools:
    - tool: read_file
      action: allow
    - tool: execute
      action: allow
      display_name: run_sql_query
      display_description: "Execute SQL queries"
```

#### 5.3: Tutorial configs
**Files:** `/Users/dbright/mcp/gatekit/configs/tutorials/*.yaml`

Convert all 4 tutorial files:
- `01-basic-allowlist.yaml`
- `02-filesystem-restrictions.yaml`
- `03-multi-server.yaml`
- `04-llm-optimization.yaml`

### Step 6: Remove Old Format Code
**File:** `/Users/dbright/mcp/gatekit/gatekit/plugins/middleware/tool_manager.py`

Remove all code related to the old `allow`, `allow_all_except`, and `mode` formats from the plugin. The plugin should only support the new `tools` format.

### Step 7: Run Tests and Fix Issues

```bash
# Run all tests
pytest tests/

# Run specific tool_manager tests
pytest tests/unit/test_tool_manager.py -v

# Run validation tests
pytest tests/validation/ -v
```

Common test failures to expect and fix:

1. **Test expects old format:** Update test configs to use new format
2. **Error message changes:** Update assertions for new error messages
3. **Schema validation:** Ensure schema only accepts new format

### Step 8: Verification Checklist

- [ ] Run `pytest tests/` - ALL tests must pass
- [ ] Test new format manually:
  ```bash
  gatekit --config configs/gatekit.yaml
  ```
- [ ] Verify renamed tools work correctly
- [ ] Check error messages are clear and helpful

## Rollback Plan
If issues arise:
1. Git revert the commit
2. Restore original tool_manager.py
3. Restore original config files
4. Document the issue for investigation

## Common Pitfalls to Avoid

1. **Don't forget to update ALL configs** - Use grep to find them all:
   ```bash
   grep -r "tool_manager:" configs/ tests/
   ```
2. **Test renaming thoroughly** - It's the most complex part
3. **Validate action consistency** - Can't mix allow/deny in same tools list
4. **Check for duplicate tool names** - Each tool should appear once

## Testing the Implementation

### Manual Test Cases

1. **Basic allowlist:**
   ```yaml
   tool_manager:
     tools:
       - tool: read_file
         action: allow
   ```
   - Only read_file should be available
   - Other tools should return "not available" error

2. **With renaming:**
   ```yaml
   tool_manager:
     tools:
       - tool: execute
         action: allow
         display_name: run_command
   ```
   - Tool should appear as "run_command" in tools/list
   - Calling "run_command" should work
   - Calling "execute" should fail

3. **Blocklist mode:**
   ```yaml
   tool_manager:
     tools:
       - tool: dangerous_tool
         action: deny
   ```
   - All tools except dangerous_tool should work
   - dangerous_tool should return "not available" error

4. **Invalid config detection:**
   ```yaml
   tool_manager:
     tools:
       - tool: read_file
         action: allow
       - tool: write_file
         action: deny  # ERROR: Can't mix allow/deny
   ```
   - Should raise clear error on startup

## Notes for Implementation

- The `tools` format is more verbose but much clearer and machine-parseable
- Each tool entry is self-contained - no need to look elsewhere to understand it
- The format naturally extends to more complex configurations in the future
- Focus on clear error messages when validation fails
- **Important:** There is no `tool_allowlist` plugin - it was already migrated to `tool_manager` middleware
- Error messages should include context (handler name, server if applicable) for better UX