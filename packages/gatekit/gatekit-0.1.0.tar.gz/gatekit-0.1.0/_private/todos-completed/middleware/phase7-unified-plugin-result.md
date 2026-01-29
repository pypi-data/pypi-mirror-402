# Phase 7: Unified PluginResult

## Prerequisites
- Phase 5 completed (Plugin manager supports middleware with Union types)
- Phase 6 completed (POLICIES → HANDLERS rename) 
- All tests passing

## Overview
Replace the dual SecurityResult/MiddlewareResult system with a single unified PluginResult that all plugins return, while maintaining the semantic distinction between plugin types for organizational clarity.

## Problem Statement

### Current Issues

1. **Type Complexity**
   - Carrying `Union[SecurityResult, MiddlewareResult]` throughout the codebase
   - Constant `isinstance()` checks polluting the code
   - Complex type annotations reducing readability

2. **Artificial Distinction**
   - SecurityResult and MiddlewareResult are 99% the same
   - Only difference is SecurityResult has required `allowed` field
   - Inheritance hierarchy (SecurityResult extends MiddlewareResult) feels forced

3. **Lost Processing History**
   - Each plugin's modifications replace the previous (except metadata)
   - Only the last plugin's reason is preserved
   - No visibility into what each plugin did

4. **Wrong Return Type for Middleware-Only Pipelines**
   - When only middleware plugins are configured, we return `SecurityResult(allowed=True, reason="Allowed by all security plugins")`
   - This is semantically wrong - no security plugins even ran!

## Solution: Unified PluginResult

### Core Design

```python
@dataclass
class PluginResult:
    """Unified result from any plugin processing.
    
    All plugins return this single type, simplifying the type system
    while maintaining semantic clarity through the plugin class hierarchy.
    """
    
    # Security decision (None if no security decision made)
    allowed: Optional[bool] = None
    
    # Content transformations
    modified_content: Optional[Union[MCPRequest, MCPResponse, MCPNotification]] = None
    completed_response: Optional[MCPResponse] = None
    
    # Processing information
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate state consistency."""
        if self.metadata is None:
            self.metadata = {}
        # Can't set both modified_content and completed_response
        if self.modified_content and self.completed_response:
            raise ValueError("Cannot set both modified_content and completed_response")
```

### Plugin Type Distinction Remains

While all plugins return the same result type, we maintain different plugin classes for organizational and semantic clarity:

```python
class MiddlewarePlugin(PluginInterface):
    """Plugin that processes messages (base for all plugins)."""
    
    @abstractmethod
    async def process_request(self, request: MCPRequest, server_name: str) -> PluginResult:
        """Process an incoming request.
        
        Returns:
            PluginResult: May set modified_content, completed_response, or leave as pass-through
        """
        pass

class SecurityPlugin(MiddlewarePlugin):
    """Plugin that MUST make security decisions.
    
    Security plugins are required to set the allowed field to True or False.
    The plugin manager enforces this contract.
    """
    
    # SecurityPlugin keeps the same abstract methods as before,
    # just with PluginResult return type instead of SecurityResult.
    # The contract enforcement happens in the plugin manager.
```

## Why Keep Plugin Type Distinction?

The distinction between SecurityPlugin and MiddlewarePlugin is **a useful organizational fiction**:

1. **Human Understanding**: People think in categories - "security plugins protect", "middleware transforms"
2. **Configuration Organization**: Clear sections in YAML for different concerns
3. **Contract Enforcement**: Security plugins MUST make decisions, middleware MAY transform
4. **Documentation**: Clear sections for different plugin types
5. **Discovery**: "What security plugins are available?" is a meaningful question

## Contract Invariants

### Plugin Type Contracts

| Plugin Type | `allowed` Field | `modified_content` | `completed_response` | Notes |
|------------|----------------|-------------------|---------------------|-------|
| **MiddlewarePlugin** | Must be `None` | Optional | Optional | Cannot make security decisions |
| **SecurityPlugin** | Must be `True` or `False` | Optional | Optional | MUST make security decision |

### State Invariants

1. **Mutual Exclusion**: `modified_content` and `completed_response` cannot both be set
2. **Security Decision Required**: SecurityPlugin MUST set `allowed` to boolean value
3. **Middleware No Decision**: MiddlewarePlugin MUST NOT set `allowed` (leave as None)
4. **Pipeline Termination**: `allowed=False` immediately stops pipeline execution

### Validation Example

```python
def validate_plugin_result(result: PluginResult, plugin_type: str) -> None:
    """Validate that plugin result meets contract requirements."""
    
    # Check mutual exclusion
    if result.modified_content and result.completed_response:
        raise ValueError("Cannot set both modified_content and completed_response")
    
    # Check type-specific contracts
    if plugin_type == "security":
        if result.allowed is None:
            raise ValueError("Security plugin must set allowed to True or False")
    elif plugin_type == "middleware":
        if result.allowed is not None:
            raise ValueError("Middleware plugin cannot make security decisions")
```

## PluginResult State Machine

### Valid States

| State | `allowed` | `modified_content` | `completed_response` | `reason` | Description |
|-------|-----------|-------------------|---------------------|----------|-------------|
| **Pass-through** | `None` | `None` | `None` | Optional | No changes, continue pipeline |
| **Modified** | `None`/`bool` | Set | `None` | Required | Content transformed |
| **Completed** | `None`/`bool` | `None` | Set | Required | Request fully handled |
| **Blocked** | `False` | Optional | `None` | Required | Security rejection |
| **Allowed** | `True` | Optional | `None` | Optional | Security approval |
| **Invalid** | Any | Set | Set | Any | ❌ Error - both set |

### State Transitions

```
Start → Pass-through → Next Plugin
      → Modified → Next Plugin  
      → Completed → End Pipeline (return response)
      → Blocked → End Pipeline (return error)
      → Allowed → Next Plugin
```

## Implementation Tasks

### 1. Replace Result Classes

#### Location: `gatekit/plugins/interfaces.py`

#### Task 1.1: Replace SecurityResult and MiddlewareResult with PluginResult
Remove the existing SecurityResult and MiddlewareResult classes and add the new PluginResult class as shown above.

### 2. Update Plugin Base Classes

#### Task 2.1: Update MiddlewarePlugin to return PluginResult
```python
class MiddlewarePlugin(PluginInterface):
    @abstractmethod
    async def process_request(self, request: MCPRequest, server_name: str) -> PluginResult:
        """Process an incoming request."""
        pass
    
    @abstractmethod
    async def process_response(self, request: MCPRequest, response: MCPResponse, server_name: str) -> PluginResult:
        """Process a response from the upstream server."""
        pass
    
    @abstractmethod
    async def process_notification(self, notification: MCPNotification, server_name: str) -> PluginResult:
        """Process a notification message."""
        pass
```

#### Task 2.2: SecurityPlugin uses same structure, just new return type
```python
class SecurityPlugin(MiddlewarePlugin):
    # No changes to the class structure - abstract methods remain abstract
    # Just change the return type from SecurityResult to PluginResult
    
    @abstractmethod
    async def process_request(self, request: MCPRequest, server_name: str) -> PluginResult:
        """Process request and make security decision.
        
        Returns:
            PluginResult: MUST have allowed field set to True or False
        """
        pass
    
    @abstractmethod
    async def process_response(self, request: MCPRequest, response: MCPResponse, server_name: str) -> PluginResult:
        """Process response and make security decision.
        
        Returns:
            PluginResult: MUST have allowed field set to True or False
        """
        pass
    
    @abstractmethod
    async def process_notification(self, notification: MCPNotification, server_name: str) -> PluginResult:
        """Process notification and make security decision.
        
        Returns:
            PluginResult: MUST have allowed field set to True or False
        """
        pass
```

### 3. Update All Plugins

#### Task 3.1: Update all security plugins at once
For each security plugin, change from SecurityResult to PluginResult:
```python
# OLD
return SecurityResult(allowed=True, reason="No PII detected")

# NEW  
return PluginResult(allowed=True, reason="No PII detected")
```

#### Task 3.2: Update future middleware plugins
When middleware plugins are created, they will use:
```python
return PluginResult(modified_content=modified_request, reason="...")
# or
return PluginResult(completed_response=response, reason="...")
# or
return PluginResult()  # Pass-through
```

### 4. Update Plugin Manager

#### Task 4.1: Change return types and add contract enforcement
```python
async def process_request(self, request: MCPRequest, server_name: Optional[str] = None) -> PluginResult:
    """Process request through middleware and security plugins."""
    
    # ... existing code ...
    
    for plugin in plugins:
        result = await self._execute_plugin_check(plugin, "process_request", current_request, server_name=server_name)
        
        # Enforce SecurityPlugin contract
        if isinstance(plugin, SecurityPlugin) and result.allowed is None:
            raise ValueError(
                f"Security plugin {plugin.plugin_id} failed to make a security decision. "
                f"Must return PluginResult with allowed=True or allowed=False"
            )
        
        # Handle completion
        if result.completed_response:
            logger.info(f"Plugin {result.metadata.get('plugin')} completed request: {result.reason}")
            return result
        
        # Handle security decisions
        if result.allowed is not None:
            if not result.allowed:
                logger.info(f"Request denied by {result.metadata.get('plugin')}: {result.reason}")
                return result
        
        # Apply content modifications
        if result.modified_content:
            current_request = result.modified_content
            final_metadata.update(result.metadata)
        
        # ... rest of processing ...
```

Note: The same contract enforcement check should be added to `process_response` and `process_notification` methods.

#### Task 4.2: Remove all Union type annotations
Replace all occurrences of `Union[SecurityResult, MiddlewareResult]` with `PluginResult` throughout the plugin manager.

### 5. Update Auditing Interface

#### Task 5.1: Change method signatures to accept PluginResult
```python
class AuditingPlugin(PluginInterface):
    @abstractmethod
    async def log_request(self, request: MCPRequest, decision: PluginResult, server_name: str) -> None:
        """Log request with plugin result."""
        pass
    
    @abstractmethod
    async def log_response(self, request: MCPRequest, response: MCPResponse, decision: PluginResult, server_name: str) -> None:
        """Log response with plugin result."""
        pass
    
    @abstractmethod
    async def log_notification(self, notification: MCPNotification, decision: PluginResult, server_name: str) -> None:
        """Log notification with plugin result."""
        pass
```

### 6. Update All Tests

#### Task 6.1: Update test fixtures and mocks
- Replace all SecurityResult/MiddlewareResult instantiations with PluginResult
- Update mock return values to use PluginResult

#### Task 6.2: Update test assertions
- Tests checking for SecurityResult/MiddlewareResult types need updating
- Verify security plugins set allowed field (not None)
- Verify middleware plugins leave allowed as None

#### Task 6.3: Add contract enforcement tests
- Test that SecurityPlugin raises ValueError when allowed is None
- Test that middleware plugins can return without setting allowed
- Test all valid PluginResult states

## Future Enhancement: PipelineResult Container

In a future phase, we could add a PipelineResult container for full history:

```python
@dataclass
class PipelineResult:
    """Container for accumulated plugin results from entire pipeline."""
    plugin_results: List[Tuple[str, PluginResult]]  # (plugin_name, result)
    
    @property
    def allowed(self) -> Optional[bool]:
        """Get final security decision."""
        for name, result in self.plugin_results:
            if result.allowed is False:
                return False
        # Check if any security decisions were made
        has_security = any(r.allowed is not None for _, r in self.plugin_results)
        return True if has_security else None
    
    @property
    def final_content(self):
        """Get final modified content."""
        for name, result in reversed(self.plugin_results):
            if result.modified_content:
                return result.modified_content
        return None
```

This would provide complete visibility into the pipeline, but is not required for the initial implementation.

## Error Handling

### Plugin Failures

When a plugin raises an exception, the behavior depends on the plugin's criticality:

```python
try:
    result = await plugin.process_request(request, server_name)
except Exception as e:
    if hasattr(plugin, 'is_critical') and not plugin.is_critical():
        # Non-critical plugin: log and continue
        logger.warning(f"Non-critical plugin {plugin.plugin_id} failed: {e}")
        continue
    else:
        # Critical plugin (default): fail closed for security
        logger.error(f"Critical plugin {plugin.plugin_id} failed: {e}")
        return PluginResult(
            allowed=False,
            reason=f"Critical plugin {plugin.plugin_id} failed",
            metadata={"error": str(e), "plugin_failure": True}
        )
```

### Default Behavior

- **Security plugins**: Default to critical (fail closed on error)
- **Middleware plugins**: Can be marked non-critical (fail open)
- **Timeout**: Not implemented in initial version (future enhancement)

## Security Hardening

### Pipeline Termination Rules

1. **Security Block is Final**: Once any plugin sets `allowed=False`, the pipeline immediately terminates
2. **No Override**: Later plugins cannot override a security block decision
3. **Short-circuit Evaluation**: Pipeline stops at first block, saving resources

```python
for plugin in plugins:
    result = await plugin.process_request(request, server_name)
    
    # Security block immediately terminates pipeline
    if result.allowed is False:
        logger.info(f"Request blocked by {plugin.plugin_id}")
        return result  # No further plugins execute
    
    # Completion also terminates (but with success)
    if result.completed_response:
        logger.info(f"Request completed by {plugin.plugin_id}")
        return result
```

### Security Invariants

- Middleware plugins CANNOT make security decisions (enforced by base class)
- Security decisions are binary and final (no "maybe" state)
- Failed security plugins default to blocking (fail closed)

## Plugin Execution Order

### Priority System

Plugins execute in priority order, regardless of type:

```python
# All plugins share the same priority space
middleware_plugin.priority = 10  # Runs first
security_plugin.priority = 50    # Runs second  
audit_plugin.priority = 90       # Runs last
```

### Ordering Rules

1. **Primary Sort**: By priority (lower number = earlier execution)
2. **Stable Sort**: Plugins with same priority maintain configuration order
3. **Mixed Types**: Middleware and security plugins interleave based on priority

Example execution order:
```
1. RateLimiter (middleware, priority=10)
2. RequestLogger (middleware, priority=20)  
3. PIIFilter (security, priority=30)
4. SecretsFilter (security, priority=40)
5. ResponseCache (middleware, priority=60)
```

## Configuration Example

### Updated YAML Structure

```yaml
# Example gatekit.yaml with unified PluginResult
plugins:
  # Middleware plugins section
  middleware:
    _global:
      - handler: rate_limiter
        enabled: true
        priority: 10
        config:
          requests_per_minute: 100
          
    my_server:
      - handler: tool_manager
        enabled: true
        priority: 20
        config:
          mode: allowlist
          tools: ["read_file", "write_file"]
  
  # Security plugins section  
  security:
    _global:
      - handler: pii
        enabled: true
        priority: 30
        config:
          sensitivity: high
          
      - handler: secrets
        enabled: true
        priority: 40
        config:
          patterns: ["api_key", "password"]
          
  # Auditing plugins section
  auditing:
    _global:
      - handler: json_lines
        enabled: true
        config:
          output_file: "/var/log/gatekit/audit.jsonl"
```

### Configuration Notes

- Each plugin type has its own section for organization
- All plugins share the same priority space
- Handlers return unified PluginResult type
- No references to SecurityResult or MiddlewareResult

## Migration Strategy

### Direct Replacement Approach
Since Gatekit is v0.1.0 with no backward compatibility requirements, we perform a clean break:

1. **Replace all result types at once**
   - Remove SecurityResult and MiddlewareResult classes
   - Add PluginResult class
   - No parallel support or gradual migration needed

2. **Update all code in single commit**
   - All plugins updated to return PluginResult
   - Plugin manager simplified to only handle PluginResult
   - Auditing interfaces updated
   - All tests updated

3. **Ensure tests pass**
   - Phase 7 is self-contained
   - All existing tests must pass after migration
   - Add new tests for contract enforcement

### Future Enhancement (Not Part of Phase 7)
- Optional PipelineResult container for full history tracking
- Enhanced debugging capabilities
- Could be added later without breaking changes

## Benefits

### 1. Simplified Type System
- No more Union types in return values
- No more isinstance() checks everywhere
- Cleaner type annotations

### 2. Semantic Correctness
- Middleware-only pipelines don't return SecurityResult
- Result type accurately reflects what happened

### 3. Maintains Organizational Clarity
- Plugin types still distinct for human understanding
- Configuration remains organized
- Documentation stays clear

### 4. Flexible Evolution
- Easy to add new fields to PluginResult
- Optional PipelineResult for full history later
- Clean architecture for future enhancements

## Testing Checklist

1. [ ] PluginResult class works correctly
2. [ ] Security plugins enforce allowed field
3. [ ] Middleware plugins work without allowed field  
4. [ ] Plugin manager enforces SecurityPlugin contract
5. [ ] Audit plugins work with PluginResult
6. [ ] No Union types remain after migration
7. [ ] Middleware-only pipelines return correct type
8. [ ] All existing tests pass

## Success Criteria

- Single PluginResult type used throughout
- No Union[SecurityResult, MiddlewareResult] anywhere
- Security contract enforced (must set allowed)
- Middleware-only pipelines handled correctly
- All tests passing
- Clean break implementation complete