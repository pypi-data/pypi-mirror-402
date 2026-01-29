# Phase 5: Plugin Manager Middleware Support [COMPLETED]

## Implementation Philosophy

### Core Principles
1. **Reuse existing infrastructure where possible**
   - Keep the `_execute_plugin_check` wrapper for all plugin calls
   - Preserve existing error handling and metadata collection
   - Maintain plugin discovery and loading patterns
   
2. **Accept necessary changes for proper type handling**
   - MiddlewareResult and SecurityResult are distinct types with different purposes
   - Downstream code must properly handle both result types
   - Tests will need updates to verify new functionality
   
3. **Avoid unnecessary complexity**
   - Don't create artificial workarounds to avoid legitimate changes
   - Keep the implementation clean and maintainable
   - Make the code's intent clear for future maintainers

4. **Preserve existing patterns and behaviors**
   - **DO NOT break accumulation patterns** - The original code accumulates metadata through the loop
   - **DO NOT change messages unnecessarily** - "Allowed by all security plugins" should stay as-is
   - **DO NOT replace None with "unknown"** - `server_name=None` is semantically meaningful
   - **DO NOT hardcode return values** - Use the accumulated `final_decision` object

### What Changes and What Stays

#### Preserve:
- The `_execute_plugin_check` wrapper pattern
- Plugin discovery and loading mechanisms
- Error handling for critical vs non-critical plugins
- Priority-based ordering
- Upstream-scoped plugin resolution

#### Update:
- Return types to `Union[SecurityResult, MiddlewareResult]`
- Proxy server to handle `completed_response` properly
- Auditing interfaces to accept both result types
- Tests to verify new middleware functionality

## Prerequisites
- Phase 4 completed (MiddlewarePlugin base class exists, SecurityPlugin extends it)
- All tests passing

## Overview
Add middleware plugin discovery, loading, and processing to the plugin manager. This enables the system to actually use middleware plugins WITHOUT breaking existing functionality.

## Implementation Tasks

### 1. Add Middleware Configuration Support

#### Location: `gatekit/config/models.py`

#### Task 1.1: Add middleware to PluginsConfig
```python
class PluginsConfig(BaseModel):
    """Configuration for plugins."""
    security: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    auditing: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    middleware: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)  # Add this
```

### 2. Update Plugin Manager Storage

#### Location: `gatekit/plugins/manager.py`

#### Task 2.1: Add middleware plugin storage
In the `__init__` method, add after security plugin storage:
```python
# Upstream-scoped plugin storage: upstream_name -> [plugins]
self.upstream_security_plugins: Dict[str, List[SecurityPlugin]] = {}
self.upstream_auditing_plugins: Dict[str, List[AuditingPlugin]] = {}
self.upstream_middleware_plugins: Dict[str, List[MiddlewarePlugin]] = {}  # Add this
```

#### Task 2.2: Import MiddlewarePlugin
Add to imports:
```python
from gatekit.plugins.interfaces import (
    SecurityPlugin, AuditingPlugin, SecurityResult, 
    PathResolvablePlugin, MiddlewarePlugin, MiddlewareResult  # Add these
)
```

### 3. Add Middleware Discovery and Loading

#### Location: `gatekit/plugins/manager.py`

#### Task 3.1: Add middleware loading method
Add this method after `_load_upstream_scoped_security_plugins`:
```python
def _load_upstream_scoped_middleware_plugins(self, middleware_config: Dict[str, List[Dict[str, Any]]]) -> None:
    """Load middleware plugins from upstream-scoped configuration.
    
    Args:
        middleware_config: Dictionary mapping upstream names to middleware plugin configs
    """
    self.upstream_middleware_plugins.clear()
    
    if not middleware_config:
        logger.info("No middleware plugin configuration found")
        return
    
    # Discover available middleware handlers
    available_policies = self._discover_policies("middleware")
    
    for upstream_name, plugin_configs in middleware_config.items():
        upstream_plugins = []
        
        for plugin_config in plugin_configs:
            if not plugin_config.get("enabled", True):
                logger.debug(f"Skipping disabled middleware plugin for {upstream_name}")
                continue
            
            policy_name = plugin_config.get("policy")
            if not policy_name:
                logger.warning(f"Middleware plugin configuration missing 'policy' field for {upstream_name}")
                continue
            
            if policy_name not in available_policies:
                logger.warning(f"Middleware policy '{policy_name}' not found for {upstream_name}")
                continue
            
            try:
                plugin_class = available_policies[policy_name]
                plugin_config_dict = plugin_config.get("config", {})
                plugin_instance = plugin_class(plugin_config_dict)
                
                # Set config directory if plugin is path-resolvable
                if isinstance(plugin_instance, PathResolvablePlugin) and self.config_directory:
                    plugin_instance.set_config_directory(self.config_directory)
                    errors = plugin_instance.validate_paths()
                    if errors:
                        for error in errors:
                            logger.error(f"Path validation error in {policy_name}: {error}")
                        raise ValueError(f"Path validation failed for {policy_name}")
                
                upstream_plugins.append(plugin_instance)
                logger.info(f"Loaded middleware plugin '{policy_name}' for upstream '{upstream_name}'")
                
            except Exception as e:
                if plugin_config.get("critical", False):
                    raise ValueError(f"Failed to load critical middleware plugin '{policy_name}': {e}")
                logger.warning(f"Failed to load non-critical middleware plugin '{policy_name}': {e}")
        
        # Sort by priority (lower number = higher priority = runs first)
        upstream_plugins.sort(key=lambda p: getattr(p, 'priority', 50))
        self.upstream_middleware_plugins[upstream_name] = upstream_plugins
        
        logger.info(f"Loaded {len(upstream_plugins)} middleware plugins for upstream '{upstream_name}'")
```

#### Task 3.2: Update load_plugins method
```python
def load_plugins(self):
    """Load all plugins from configuration."""
    # Load middleware plugins first (they run before security)
    middleware_config = self.plugins_config.get("middleware", {})
    self._load_upstream_scoped_middleware_plugins(middleware_config)
    
    # Then security and auditing as before
    security_config = self.plugins_config.get("security", {})
    self._load_upstream_scoped_security_plugins(security_config)
    
    auditing_config = self.plugins_config.get("auditing", {})
    self._load_upstream_scoped_auditing_plugins(auditing_config)
```

### 4. Add Combined Pipeline Processing

#### Location: `gatekit/plugins/manager.py`

#### Task 4.1: Add method to get all processing plugins
Add this method:
```python
def _get_processing_pipeline(self, upstream_name: str) -> List[Union[MiddlewarePlugin, SecurityPlugin]]:
    """Get all middleware and security plugins for an upstream, sorted by priority.
    
    Args:
        upstream_name: Name of the upstream server
        
    Returns:
        List of plugins sorted by priority (lower number runs first)
    """
    all_plugins = []
    
    # Get middleware plugins
    middleware_plugins = self._resolve_plugins_for_upstream(
        self.upstream_middleware_plugins, upstream_name
    )
    all_plugins.extend(middleware_plugins)
    
    # Get security plugins  
    security_plugins = self._resolve_plugins_for_upstream(
        self.upstream_security_plugins, upstream_name
    )
    all_plugins.extend(security_plugins)
    
    # Sort by priority (lower number = higher priority = runs first)
    all_plugins.sort(key=lambda p: getattr(p, 'priority', 50))
    
    return all_plugins
```

#### Task 4.2: Update `_execute_plugin_check` to handle both result types
Modify the wrapper to handle both MiddlewareResult and SecurityResult:
```python
async def _execute_plugin_check(self, plugin, check_method_name: str, *args, **kwargs) -> Union[SecurityResult, MiddlewareResult]:
    """Execute a plugin check method with automatic metadata injection.
    
    Args:
        plugin: The plugin instance to execute
        check_method_name: Name of the method to call ('process_request', 'process_response', 'process_notification')
        *args: Arguments to pass to the check method
        **kwargs: Keyword arguments to pass to the check method
        
    Returns:
        Union[SecurityResult, MiddlewareResult]: Result with plugin name automatically added to metadata
    """
    plugin_name = getattr(plugin, 'plugin_id', plugin.__class__.__name__)
    logger.debug(f"Executing plugin {plugin_name} with priority {getattr(plugin, 'priority', 50)}")
    
    check_method = getattr(plugin, check_method_name)
    decision = await check_method(*args, **kwargs)
    
    # Automatically add plugin name to metadata
    if decision.metadata is None:
        decision.metadata = {}
    decision.metadata["plugin"] = plugin_name
    
    return decision
```

### 5. Integrate Middleware into Existing Processing

#### Location: `gatekit/plugins/manager.py`

#### Implementation Requirements
**The `process_request`, `process_response`, and `process_notification` methods need updates to handle both middleware and security plugins.**

**Key Requirements:**
1. **Continue using `_execute_plugin_check` wrapper** - Essential for error handling and metadata
2. **Update return types** - Methods should return `Union[SecurityResult, MiddlewareResult]`
3. **Handle `completed_response` properly** - When middleware completes a request, return the MiddlewareResult
4. **Update downstream handling** - The proxy server must handle both result types correctly

#### Task 5.1: Modify process_request to handle both result types

**CRITICAL IMPLEMENTATION NOTES:**

⚠️ **PRESERVE THE ACCUMULATION PATTERN** - The original code initializes `final_decision` at the start and updates it through the loop. This pattern MUST be preserved.

⚠️ **DO NOT CHANGE server_name TO "unknown"** - If `server_name` is None, keep it as None in metadata. Only use fallbacks like `server_name or "unknown"` for display/logging purposes.

⚠️ **RETURN final_decision** - Do not create new SecurityResult objects at the end. Return the accumulated `final_decision`.

**Correct Implementation Pattern:**
```python
async def process_request(self, request: MCPRequest, server_name: Optional[str] = None) -> Union[SecurityResult, MiddlewareResult]:
    """Process request through middleware and security plugins."""
    
    # Get combined pipeline of middleware and security plugins
    # Use fallback only for function calls that need a string
    plugins = self._get_processing_pipeline(server_name or "unknown")
    
    # If no plugins, return allowed
    if not plugins:
        return SecurityResult(
            allowed=True,
            reason=f"No plugins configured for upstream '{server_name or 'unknown'}'",
            metadata={"upstream": server_name, "plugins_applied": []}  # Keep None in metadata
        )
    
    # Initialize final_decision that will accumulate changes
    plugin_names = [getattr(p, 'plugin_id', p.__class__.__name__) for p in plugins]
    final_decision = SecurityResult(
        allowed=True,
        reason=f"Allowed by all security plugins for upstream '{server_name or 'unknown'}'",
        metadata={
            "upstream": server_name,  # Preserve None if that's what was passed
            "plugins_applied": plugin_names
        }
    )
    
    # Track current request through modifications
    current_request = request
    
    # Process through all plugins in priority order
    for plugin in plugins:
        # Use wrapper for all plugin calls
        result = await self._execute_plugin_check(
            plugin, "process_request", current_request, server_name=server_name
        )
        
        # Handle middleware plugins that complete the request
        if isinstance(result, MiddlewareResult) and result.completed_response:
            logger.info(f"Middleware {result.metadata.get('plugin')} completed request: {result.reason}")
            return result  # Return the MiddlewareResult with completed_response
        
        # Handle plugins that block
        if isinstance(result, SecurityResult) and not result.allowed:
            logger.info(f"Request denied by {result.metadata.get('plugin')}: {result.reason}")
            return result
        
        # Accumulate changes into final_decision
        if result.modified_content and isinstance(result.modified_content, MCPRequest):
            current_request = result.modified_content
            final_decision.modified_content = current_request
            final_decision.reason = result.reason
            # Update metadata while preserving upstream
            final_decision.metadata.update(result.metadata or {})
            final_decision.metadata["upstream"] = server_name  # Preserve original value
            logger.debug(f"Request modified by {result.metadata.get('plugin')}")
    
    # All plugins processed successfully - return the accumulated decision
    return final_decision
```

**Key Changes:**
1. Return type is now `Union[SecurityResult, MiddlewareResult]`
2. When middleware completes a request, return the MiddlewareResult directly
3. Handle both result types properly without artificial wrapping
4. Preserve existing behavior for security-only pipelines

#### Task 5.2: Modify process_response similarly
Apply the same pattern to `process_response`:
1. Change return type to `Union[SecurityResult, MiddlewareResult]`
2. Use `_get_processing_pipeline` instead of just security plugins
3. Return MiddlewareResult directly when appropriate
4. Keep using `_execute_plugin_check`

#### Task 5.3: Modify process_notification similarly
Apply the same pattern to `process_notification`:
1. Change return type to `Union[SecurityResult, MiddlewareResult]`
2. Use `_get_processing_pipeline` instead of just security plugins
3. Return MiddlewareResult directly when appropriate
4. Keep using `_execute_plugin_check`

### 6. Update Proxy Server to Handle Both Result Types

#### Location: `gatekit/proxy/server.py`

#### Task 6.1: Update request handling in `_handle_request`
The proxy server needs to handle both SecurityResult and MiddlewareResult:

```python
# Step 1: Security check through plugins
try:
    decision = await self._plugin_manager.process_request(request, server_name)
except Exception as e:
    # ... existing error handling ...

# Step 2: Handle the decision based on type
if isinstance(decision, MiddlewareResult) and decision.completed_response:
    # Middleware completed the request - return the response directly
    response = decision.completed_response
    
    # Log the completed request (passing MiddlewareResult directly)
    try:
        await self._plugin_manager.log_request(request, decision, server_name)
        await self._plugin_manager.log_response(request, response, decision, server_name)
    except Exception as e:
        logger.warning(f"Auditing failed for completed request {request_id}: {e}")
    
    return response

elif isinstance(decision, SecurityResult):
    # Handle security result as before
    if not decision.allowed:
        # ... existing blocking logic ...
        return error_response
    
    # Forward to upstream server (use modified request if available)
    upstream_request = decision.modified_content if (
        decision.modified_content and isinstance(decision.modified_content, MCPRequest)
    ) else request
    # ... continue with existing flow ...
```

#### Task 6.2: Update response and notification handling similarly
Apply the same pattern to handle both result types in response and notification processing.

### 6. Create Test for Middleware Loading

#### Location: Create `tests/unit/test_plugin_manager_middleware.py`

```python
"""Tests for plugin manager middleware support."""

import pytest
from typing import Dict, Any
from gatekit.plugins.manager import PluginManager
from gatekit.plugins.interfaces import MiddlewarePlugin, MiddlewareResult
from gatekit.protocol.messages import MCPRequest, MCPResponse, MCPNotification


class TestMiddlewarePlugin(MiddlewarePlugin):
    """Test middleware plugin implementation."""
    
    POLICIES = {"test_middleware": "TestMiddlewarePlugin"}
    
    async def process_request(self, request: MCPRequest, server_name: str) -> MiddlewareResult:
        return MiddlewareResult(reason="Test middleware processed")
    
    async def process_response(self, request: MCPRequest, response: MCPResponse, server_name: str) -> MiddlewareResult:
        return MiddlewareResult(reason="Test middleware processed")
    
    async def process_notification(self, notification: MCPNotification, server_name: str) -> MiddlewareResult:
        return MiddlewareResult(reason="Test middleware processed")


def test_middleware_plugin_loading():
    """Test that middleware plugins can be loaded."""
    config = {
        "middleware": {
            "_global": [
                {
                    "policy": "test_middleware",
                    "enabled": True,
                    "config": {"priority": 30}
                }
            ]
        }
    }
    
    manager = PluginManager(config)
    # Mock the discovery to find our test plugin
    with pytest.MonkeyPatch().context() as m:
        m.setattr(manager, '_discover_policies', 
                  lambda category: {"test_middleware": TestMiddlewarePlugin} if category == "middleware" else {})
        manager.load_plugins()
    
    assert "_global" in manager.upstream_middleware_plugins
    assert len(manager.upstream_middleware_plugins["_global"]) == 1
    assert isinstance(manager.upstream_middleware_plugins["_global"][0], TestMiddlewarePlugin)


@pytest.mark.asyncio
async def test_middleware_pipeline_processing():
    """Test that middleware plugins are processed in the pipeline."""
    config = {
        "middleware": {
            "_global": [
                {
                    "policy": "test_middleware",
                    "enabled": True,
                    "config": {"priority": 30}
                }
            ]
        }
    }
    
    manager = PluginManager(config)
    # Mock discovery
    with pytest.MonkeyPatch().context() as m:
        m.setattr(manager, '_discover_policies',
                  lambda category: {"test_middleware": TestMiddlewarePlugin} if category == "middleware" else {})
        manager.load_plugins()
    
    request = MCPRequest(jsonrpc="2.0", id=1, method="test", params={})
    result = await manager.process_request(request, "test_server")
    
    assert result.allowed is True
    assert "processed successfully" in result.reason.lower()
```

## Testing Approach

### Expected Test Updates
Some tests will legitimately need updates to handle the new result types:

#### Tests that SHOULD be updated:
1. **Type checking tests** - Will need to accept `Union[SecurityResult, MiddlewareResult]`
2. **Mock implementations** - May need to handle both result types
3. **Integration tests** - Should verify middleware functionality works end-to-end
4. **New middleware tests** - Add comprehensive tests for middleware behavior

#### Tests that should NOT change:
1. **Security-only tests** - Existing security plugin tests should still work
2. **Basic plugin loading** - Plugin discovery and loading mechanisms unchanged
3. **Priority ordering** - Still works the same way
4. **Error handling** - Critical vs non-critical plugin behavior unchanged

### Test Implementation Strategy
```bash
# Step 1: Run existing tests to establish baseline
pytest tests/unit/test_plugin_manager.py -v

# Step 2: Update any tests that legitimately need new type handling
# These are not regressions but necessary updates for new functionality

# Step 3: Add new middleware-specific tests
pytest tests/unit/test_plugin_manager_middleware.py -v

# Step 4: Verify full test suite
pytest tests/ -v
```

### What Test Changes Are Acceptable
- Adding `Union` type imports where needed
- Updating mock objects to return appropriate result types
- Adding assertions to verify middleware behavior
- Creating new test cases for middleware functionality

### What Test Changes Indicate Problems
- Needing to change expected text in error messages (e.g., "Allowed by all security plugins" changing)
- Breaking existing security plugin tests
- Having to rewrite test logic (vs just updating types)
- Tests failing due to missing attributes or methods
- Tests expecting `upstream: "unknown"` when they previously expected `upstream: None`

### Common Implementation Mistakes to Avoid

#### ❌ Breaking the Accumulation Pattern
**Wrong:**
```python
# Don't create new objects at the end
if last_meaningful_result:
    return SecurityResult(...)  # Creates new object, loses accumulated data
else:
    return SecurityResult(...)  # Another new object
```

**Right:**
```python
# Initialize once, update through loop, return at end
final_decision = SecurityResult(...)
for plugin in plugins:
    # Update final_decision as needed
return final_decision
```

#### ❌ Changing server_name Unnecessarily
**Wrong:**
```python
if server_name is None:
    server_name = "unknown"  # Changes the actual value
```

**Right:**
```python
# Use fallback only where needed, preserve original
plugins = self._get_processing_pipeline(server_name or "unknown")
# But keep None in metadata
metadata={"upstream": server_name, ...}
```

#### ❌ Losing Plugin-Specific Context
**Wrong:**
```python
# Always returning generic message
return SecurityResult(
    reason="All security checks passed",  # Generic, loses plugin context
    ...
)
```

**Right:**
```python
# Preserve plugin's specific reason when content is modified
if result.modified_content:
    final_decision.reason = result.reason  # Keep plugin's message
```

## Success Criteria

- Plugin manager can discover and load middleware plugins
- Middleware plugins execute in the processing pipeline
- Security plugins still work correctly
- Middleware and security plugins are ordered by priority
- System supports middleware configuration in YAML
- The `_execute_plugin_check` wrapper is used for all plugin calls
- Both SecurityResult and MiddlewareResult are handled properly
- Middleware can complete requests with `completed_response`
- Proxy server correctly handles both result types

## Notes
- Middleware runs before security plugins at the same priority
- Middleware can complete requests early with `completed_response`
- Security plugins can still block even after middleware modifications
- When middleware completes a request, it returns MiddlewareResult directly
- The proxy server handles both SecurityResult and MiddlewareResult appropriately

## Implementation Summary

### Design Philosophy
The implementation properly handles two distinct result types:
- **MiddlewareResult**: Can modify content or complete requests entirely
- **SecurityResult**: Makes allow/block decisions with optional modifications

### Key Implementation Points
1. **Use Union types** - Methods return `Union[SecurityResult, MiddlewareResult]`
2. **Handle completed_response** - When set, return the response directly to client
3. **Preserve infrastructure** - Keep using `_execute_plugin_check` and existing patterns
4. **Update downstream code** - Proxy server must handle both result types
5. **Maintain compatibility** - Security-only pipelines work unchanged

### Final Checklist Before Implementation
Before starting:
- [ ] Understand the existing `process_request` method flow and its accumulation pattern
- [ ] Understand how `_execute_plugin_check` wrapper works
- [ ] Understand the difference between MiddlewareResult and SecurityResult
- [ ] Review existing test expectations to avoid unnecessary changes

During implementation:
- [ ] Use `_execute_plugin_check` for ALL plugin calls
- [ ] Preserve the accumulation pattern (initialize `final_decision`, update it, return it)
- [ ] Keep `server_name=None` as None in metadata (don't replace with "unknown")
- [ ] Return appropriate result types (don't wrap unnecessarily)
- [ ] Handle both result types in proxy server
- [ ] Update tests ONLY where type changes are needed
- [ ] Verify middleware can complete requests properly
- [ ] Preserve existing message strings ("Allowed by all security plugins", etc.)

After implementation:
- [ ] Verify no test assertions were changed unnecessarily
- [ ] Confirm metadata preservation works correctly
- [ ] Check that `upstream: None` is preserved where expected
- [ ] Ensure plugin-specific reasons are preserved when content is modified