# Phase 6: Migrate tool_allowlist to Middleware

## Prerequisites
- Phase 5 completed (Plugin manager supports middleware)
- All tests passing

## Overview
Migrate the existing `tool_allowlist` security plugin to become `tool_manager` middleware plugin. This demonstrates the middleware system working with a real plugin that manages tool availability.

## Implementation Tasks

### 1. Create Middleware Directory Structure

#### Task 1.1: Create directories
```bash
mkdir -p gatekit/plugins/middleware
touch gatekit/plugins/middleware/__init__.py
```

### 2. Move and Rename tool_allowlist

#### Task 2.1: Move the file
```bash
git mv gatekit/plugins/security/tool_allowlist.py gatekit/plugins/middleware/tool_manager.py
```

### 3. Convert to MiddlewarePlugin

#### Location: `gatekit/plugins/middleware/tool_manager.py`

#### Task 3.1: Update imports
```python
from gatekit.plugins.interfaces import MiddlewarePlugin, PluginResult
from gatekit.protocol.messages import MCPRequest, MCPResponse, MCPNotification
# Remove SecurityPlugin import
```

#### Task 3.2: Update __init__ method for MiddlewarePlugin
```python
def __init__(self, config: Dict[str, Any]):
    """Initialize middleware plugin with configuration."""
    # Call parent __init__ first - MiddlewarePlugin handles priority and critical
    super().__init__(config)
    
    # Rest of initialization stays the same
    # Validate configuration type first
    if not isinstance(config, dict):
        raise ValueError("Configuration must be a dictionary")
    
    # Continue with mode and tools validation...
```

#### Task 3.3: Change class inheritance and update docstring
```python
class ToolManagerPlugin(MiddlewarePlugin):  # Changed from SecurityPlugin
    """Middleware plugin for managing tool visibility and availability.
    
    This plugin controls which tools are exposed to clients through allowlist
    or blocklist policies. Tools can be hidden for various reasons including
    context optimization, workflow simplification, or capability management.
    
    Note: This is NOT a security plugin. Tools are filtered at the middleware
    layer for operational purposes. For security-based tool restrictions,
    implement a separate SecurityPlugin.
    """
    
    # Update display metadata
    DISPLAY_NAME = "Tool Manager"
    DISPLAY_SCOPE = "server_aware"
    
    # Note: MiddlewarePlugin uses priority for ordering
    # priority: 0-100 (lower = runs earlier)

# At end of file:
# Handler declaration for discovery (not POLICIES)
HANDLERS = {
    "tool_manager": ToolManagerPlugin  # Changed from "tool_allowlist"
}
```

#### Task 3.4: Update process_request method
```python
async def process_request(self, request: MCPRequest, server_name: str) -> PluginResult:
    """Process tool invocations, filtering tools based on policy.
    
    Args:
        request: The MCP request to process
        server_name: Name of the target server
        
    Returns:
        PluginResult with completed_response if tool is hidden
    """
    # Only process tools/call requests
    if request.method != "tools/call":
        return PluginResult()  # Pass through unchanged
    
    tool_name = request.params.get("name") if request.params else None
    if not tool_name:
        return PluginResult()
    
    # Check if tool should be hidden
    should_hide = False
    if self.mode == "allowlist":
        should_hide = not self._is_tool_allowed(tool_name, self.tools)
    elif self.mode == "blocklist":
        should_hide = self._is_tool_allowed(tool_name, self.tools)
    
    if should_hide:
        # Return error response for hidden tool
        error_response = MCPResponse(
            jsonrpc=request.jsonrpc,
            id=request.id,
            error={
                "code": -32601,  # Method not found
                "message": f"Tool '{tool_name}' is not available",
                "data": {
                    "reason": "hidden_by_policy",
                    "plugin": "tool_manager"
                }
            }
        )
        
        return PluginResult(
            completed_response=error_response,
            reason=f"Tool '{tool_name}' hidden by {self.mode} policy",
            metadata={"hidden_tool": tool_name, "mode": self.mode}
        )
    
    # Tool is allowed, pass through
    return PluginResult()
```

#### Task 3.5: Update process_response method
```python
async def process_response(self, request: MCPRequest, response: MCPResponse, server_name: str) -> PluginResult:
    """Filter tools from tools/list responses based on policy.
    
    Args:
        request: The original MCP request
        response: The MCP response to process
        server_name: Name of the source server
        
    Returns:
        PluginResult with modified_content if tools were hidden
    """
    # Only process tools/list responses
    if request.method != "tools/list" or not response.result:
        return PluginResult()
    
    tools = response.result.get("tools", [])
    if not tools:
        return PluginResult()
    
    # Filter tools based on configuration
    filtered_tools = []
    hidden_count = 0
    
    for tool in tools:
        tool_name = tool.get("name")
        if not tool_name:
            filtered_tools.append(tool)
            continue
        
        should_hide = False
        if self.mode == "allowlist":
            should_hide = not self._is_tool_allowed(tool_name, self.tools)
        elif self.mode == "blocklist":
            should_hide = self._is_tool_allowed(tool_name, self.tools)
        
        if should_hide:
            hidden_count += 1
            logger.debug(f"Hiding tool '{tool_name}' from tools/list response")
        else:
            filtered_tools.append(tool)
    
    if hidden_count > 0:
        # Create modified response with filtered tools
        modified_response = MCPResponse(
            jsonrpc=response.jsonrpc,
            id=response.id,
            result={"tools": filtered_tools}
        )
        
        return PluginResult(
            modified_content=modified_response,
            reason=f"Hidden {hidden_count} tools based on {self.mode} policy",
            metadata={"hidden_count": hidden_count, "total_tools": len(tools)}
        )
    
    return PluginResult()
```

#### Task 3.6: Update process_notification method
```python
async def process_notification(self, notification: MCPNotification, server_name: str) -> PluginResult:
    """Process notifications - currently pass through.
    
    Args:
        notification: The MCP notification to process
        server_name: Name of the source server
        
    Returns:
        PluginResult with no modifications
    """
    return PluginResult()
```

### 4. Update Test Files

#### Task 4.1: Move and rename test file
```bash
git mv tests/unit/test_tool_allowlist_plugin.py tests/unit/test_tool_manager_plugin.py
git mv tests/unit/test_tool_allowlist_response_filtering.py tests/unit/test_tool_manager_response_filtering.py
```

#### Task 4.2: Update test imports and class names
In both test files:
- Replace `ToolAllowlistPlugin` with `ToolManagerPlugin`
- Update import from `gatekit.plugins.security.tool_allowlist` to `gatekit.plugins.middleware.tool_manager`
- Replace return types with `PluginResult` throughout
- Update assertions to check for `completed_response` instead of `allowed=False`

### 5. Update Integration Tests

Search for any integration tests that reference tool_allowlist and update them:
```bash
grep -r "tool_allowlist" tests/integration/ --include="*.py"
```

Update configuration in tests from:
```yaml
security:
  _global:
    - policy: tool_allowlist
```

To:
```yaml
middleware:
  _global:
    - handler: tool_manager  # Note: use 'handler' not 'policy' for middleware
```

### 6. Update Documentation References

#### Task 6.1: Update any documentation
```bash
grep -r "tool_allowlist" docs/ --include="*.md"
```

Replace references with "tool_manager" and update descriptions to emphasize it's middleware for tool management, not security.

### 7. Remove Old References

#### Task 7.1: Ensure no tool_allowlist references remain
```bash
# Should return no results
grep -r "tool_allowlist" gatekit/ tests/ --include="*.py"
grep -r "ToolAllowlistPlugin" gatekit/ tests/ --include="*.py"
```

## Testing Checklist

1. [ ] Tool manager tests pass: `pytest tests/unit/test_tool_manager_plugin.py`
2. [ ] Response filtering tests pass: `pytest tests/unit/test_tool_manager_response_filtering.py`
3. [ ] Integration tests updated and passing
4. [ ] Tool filtering works (tools are hidden from tools/list)
5. [ ] Tool calls to hidden tools return appropriate error
6. [ ] Run `pytest tests/` - ALL tests pass

## Configuration Example

Update example configurations:

```yaml
# Old (security plugin)
plugins:
  security:
    my_server:
      - policy: tool_allowlist
        enabled: true
        config:
          mode: allowlist
          tools:
            - read_file
            - write_file

# New (middleware plugin)  
plugins:
  middleware:
    my_server:
      - handler: tool_manager  # Note: use 'handler' not 'policy' for middleware
        enabled: true
        config:
          mode: allowlist
          priority: 30  # Run early in pipeline
          tools:
            - read_file
            - write_file
```

## Success Criteria

- tool_allowlist no longer exists
- tool_manager works as middleware
- Tools are filtered based on operational policies, not security
- All tests pass with the migrated plugin
- Integration tests work with middleware configuration

## Migration Notes

Key changes from security to middleware:
1. Returns `PluginResult` (same as security, but different fields used)
2. Uses `completed_response` for hidden tools (not `allowed=False`)
   - Middleware cannot make security decisions (no `allowed` field)
3. Emphasis on tool management and availability control, not security
4. Runs earlier in pipeline (lower priority number)
5. Configuration moves from `security` to `middleware` section

## Rollback Plan

If issues arise:
1. `git mv` the files back
2. Revert class inheritance to SecurityPlugin
3. Keep using PluginResult but restore security plugin behavior
4. Move configuration back to security section