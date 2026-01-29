# Phase 2: Middleware Plugin System Implementation

## Prerequisites
- Phase 1 (method rename) must be completed first
- All `check_*` methods have been renamed to `process_*`
- All tests are passing with the renamed methods

## Overview
Implement the complete middleware plugin system, including the new base class, hierarchy changes, tool_manager migration, and plugin manager updates. This is a complex but self-contained change.

## Implementation Status
- **✅ COMPLETED**: Auditing plugin priority removal and critical support (from earlier work)
- **⏳ NOT STARTED**: Everything in this document

## Core Concept
- **Middleware plugins**: Process MCP messages and can modify content, fully handle requests, or trigger side effects
- **Security plugins**: Make trust decisions and can block messages based on security policies
- **Middleware vs Security**: Middleware shapes functionality ("how to make this work better"), Security makes trust decisions ("is this safe?")

## Implementation Tasks

### 1. Create New Return Type: MiddlewareResult

#### Location: `gatekit/plugins/interfaces.py`

#### Task 1.1: Add MiddlewareResult dataclass
Add the following class BEFORE the existing SecurityResult class:

```python
from typing import Optional

@dataclass
class MiddlewareResult:
    """Result of middleware plugin processing.
    
    Middleware can either transform content for further processing OR
    fully handle the request by providing a complete response.
    
    Attributes:
        modified_content: Optional modified version of the message for further processing
        completed_response: Optional complete response that ends pipeline processing
        reason: Human-readable explanation of what was done
        metadata: Additional information about the processing
    """
    modified_content: Union[MCPRequest, MCPResponse, MCPNotification, None] = None
    completed_response: Optional[MCPResponse] = None  # If set, pipeline stops here
    reason: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize metadata to empty dict if None."""
        if self.metadata is None:
            self.metadata = {}
        # Validate that both aren't set
        if self.modified_content and self.completed_response:
            raise ValueError("Cannot set both modified_content and completed_response")
```

#### Task 1.2: Update SecurityResult to extend MiddlewareResult
```python
@dataclass
class SecurityResult(MiddlewareResult):
    """Security handler result that requires an allow/block determination.
    
    Security plugins must return SecurityResult with allowed set to True or False.
    """
    allowed: bool = True  # Required field for security decisions
    
    def __post_init__(self):
        """Ensure metadata is initialized."""
        super().__post_init__()
        # allowed field is required for security plugins
        if not isinstance(self.allowed, bool):
            raise ValueError("Security plugins must set allowed to True or False")
```

### 2. Create MiddlewarePlugin Base Class

#### Location: `gatekit/plugins/interfaces.py`

#### Task 2.1: Add MiddlewarePlugin class
Add this class AFTER PluginInterface and BEFORE SecurityPlugin:

```python
class MiddlewarePlugin(PluginInterface):
    """Base class for all middleware plugins.
    
    Middleware plugins process MCP messages and can modify content, trigger side effects,
    communicate with external systems, or enhance functionality. They cannot block
    messages - use SecurityPlugin for blocking capability.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize middleware plugin with configuration."""
        super().__init__(config)
        # Middleware plugins default to non-critical (fail open)
        self.critical = config.get("critical", False)
    
    def is_critical(self) -> bool:
        """Return whether this plugin is critical for operation."""
        return self.critical
    
    @abstractmethod
    async def process_request(self, request: MCPRequest, server_name: str) -> MiddlewareResult:
        """Process an incoming request.
        
        Can:
        - Modify the request for further processing (set modified_content)
        - Fully handle the request (set completed_response)
        - Trigger side effects and pass through unchanged (return empty result)
        """
        pass
    
    @abstractmethod
    async def process_response(self, request: MCPRequest, response: MCPResponse, server_name: str) -> MiddlewareResult:
        """Process a response from the upstream server."""
        pass
    
    @abstractmethod
    async def process_notification(self, notification: MCPNotification, server_name: str) -> MiddlewareResult:
        """Process a notification message."""
        pass
```

### 3. Update SecurityPlugin to Extend MiddlewarePlugin

#### Location: `gatekit/plugins/interfaces.py`

#### Task 3.1: Make SecurityPlugin inherit from MiddlewarePlugin
```python
class SecurityPlugin(MiddlewarePlugin):
    """Specialized middleware that can block content based on security policies.
    
    Security plugins extend middleware with the ability to prevent
    requests/responses from proceeding when they violate security policies.
    They MUST return SecurityResult with allowed=True or allowed=False.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize security plugin with configuration."""
        super().__init__(config)
        # Security plugins default to critical (fail closed)
        self.critical = config.get("critical", True)
    
    # Override the abstract methods with SecurityResult return type
    @abstractmethod
    async def process_request(self, request: MCPRequest, server_name: str) -> SecurityResult:
        """Process request and decide if it should be allowed."""
        pass
    
    @abstractmethod
    async def process_response(self, request: MCPRequest, response: MCPResponse, server_name: str) -> SecurityResult:
        """Process response and decide if it should be allowed."""
        pass
    
    @abstractmethod
    async def process_notification(self, notification: MCPNotification, server_name: str) -> SecurityResult:
        """Process notification and decide if it should be allowed."""
        pass
```

### 4. Create ProcessingPipeline Types (Optional for Phase 2)

#### Location: `gatekit/plugins/interfaces.py`

These types support full observability but aren't required for basic middleware functionality.

#### Task 4.1: Add PipelineStage and ProcessingPipeline dataclasses
```python
@dataclass
class PipelineStage:
    """Record of a single plugin's processing within the pipeline."""
    plugin_name: str
    plugin_type: str  # "middleware" or "security"
    input_content: Union[MCPRequest, MCPResponse, MCPNotification]
    output_content: Optional[Union[MCPRequest, MCPResponse, MCPNotification]]
    result: MiddlewareResult
    processing_time_ms: float
    
    @property
    def modified(self) -> bool:
        """Check if this stage modified the content."""
        return self.output_content is not None and self.output_content != self.input_content
    
    @property
    def blocked(self) -> bool:
        """Check if this stage blocked the request (security plugins only)."""
        return self.result.allowed is False if hasattr(self.result, 'allowed') else False

@dataclass
class ProcessingPipeline:
    """Complete record of message processing through all plugins."""
    original_content: Union[MCPRequest, MCPResponse, MCPNotification]
    stages: List[PipelineStage]
    final_content: Union[MCPRequest, MCPResponse, MCPNotification]
    total_time_ms: float
    final_decision: bool
    blocked_at_stage: Optional[str] = None
    completed_by: Optional[str] = None
```

### 5. Update Plugin Imports

#### Location: `gatekit/plugins/__init__.py`

#### Task 5.1: Add new exports
```python
from .interfaces import (
    SecurityPlugin, 
    AuditingPlugin, 
    PluginInterface, 
    SecurityResult,
    MiddlewarePlugin,
    MiddlewareResult,
    PipelineStage,
    ProcessingPipeline
)

__all__ = [
    "SecurityPlugin", 
    "AuditingPlugin", 
    "PluginInterface", 
    "SecurityResult",
    "MiddlewarePlugin",
    "MiddlewareResult",
    "PipelineStage",
    "ProcessingPipeline",
    "PluginManager"
]
```

### 6. Migrate tool_allowlist to tool_manager

#### Location: `gatekit/plugins/security/tool_allowlist.py` → `gatekit/plugins/middleware/tool_manager.py`

#### Task 6.1: Create middleware directory and move file
```bash
mkdir -p gatekit/plugins/middleware
git mv gatekit/plugins/security/tool_allowlist.py gatekit/plugins/middleware/tool_manager.py
```

#### Task 6.2: Update the class to be a MiddlewarePlugin
```python
from gatekit.plugins.interfaces import MiddlewarePlugin, MiddlewareResult

class ToolManagerPlugin(MiddlewarePlugin):
    """Middleware plugin for shaping tool capabilities to optimize LLM context.
    
    This helps manage agentic workflows by hiding tools to reduce context bloat.
    Note: This is NOT a security plugin. Hidden tools are removed for performance.
    """
    
    DISPLAY_NAME = "Tool Manager"
    DISPLAY_SCOPE = "server_aware"
    
    async def process_request(self, request: MCPRequest, server_name: str) -> MiddlewareResult:
        """Process tool invocations, hiding tools to optimize context."""
        if request.method != "tools/call":
            return MiddlewareResult()  # Pass through
        
        tool_name = request.params.get("name")
        
        # Check if tool is hidden (capability shaping, not security)
        if self.mode == "allowlist" and tool_name not in self.tools:
            # Return "not available" response
            error_response = MCPResponse(
                jsonrpc=request.jsonrpc,
                id=request.id,
                error={
                    "code": -32601,  # Method not found
                    "message": f"Tool '{tool_name}' is not available in this context",
                    "data": {"reason": "capability_filtered"}
                }
            )
            return MiddlewareResult(
                completed_response=error_response,
                reason=f"Tool hidden to reduce context: {tool_name}"
            )
        
        return MiddlewareResult()

# Update manifest
HANDLERS = {"tool_manager": ToolManagerPlugin}
```

### 7. Update Plugin Manager

#### Location: `gatekit/plugins/manager.py`

#### Task 7.1: Add middleware plugin storage
In `__init__` method:
```python
self.upstream_middleware_plugins: Dict[str, List[MiddlewarePlugin]] = {}
```

#### Task 7.2: Add middleware loading method
```python
def _load_upstream_scoped_middleware_plugins(self, middleware_config: Dict[str, List[Dict[str, Any]]]) -> None:
    """Load middleware plugins from upstream-scoped configuration."""
    self.upstream_middleware_plugins.clear()
    
    if not middleware_config:
        logger.info("No middleware plugin configuration found")
        return
    
    available_handlers = self._discover_handlers("middleware")
    
    for upstream_name, plugin_configs in middleware_config.items():
        upstream_plugins = []
        
        for plugin_config in plugin_configs:
            if not plugin_config.get("enabled", True):
                continue
                
            handler_name = plugin_config.get("handler")
            if handler_name not in available_handlers:
                raise ValueError(f"Handler '{handler_name}' not found")
                
            try:
                plugin_class = available_handlers[handler_name]
                plugin_instance = self._create_plugin_instance(
                    plugin_class, plugin_config, handler_name, "middleware"
                )
                if plugin_instance:
                    upstream_plugins.append(plugin_instance)
            except Exception as e:
                logger.error(f"Failed to load middleware plugin '{handler_name}': {e}")
        
        upstream_plugins.sort(key=lambda p: getattr(p, 'priority', 50))
        self.upstream_middleware_plugins[upstream_name] = upstream_plugins
```

#### Task 7.3: Update load_plugins method
```python
def load_plugins(self):
    """Load all plugins from configuration."""
    middleware_config = self.plugins_config.get("middleware", {})
    self._load_upstream_scoped_middleware_plugins(middleware_config)
    # ... existing security and auditing loading ...
```

#### Task 7.4: Add method to get combined middleware and security plugins
```python
def _get_all_middleware_and_security_plugins(self, upstream_name: str) -> List[Union[MiddlewarePlugin, SecurityPlugin]]:
    """Get all middleware and security plugins for an upstream, sorted by priority."""
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
    
    # Sort by priority
    all_plugins.sort(key=lambda p: getattr(p, 'priority', 50))
    return all_plugins
```

#### Task 7.5: Update process_request to handle middleware
The key change is handling `completed_response` from middleware:

```python
async def process_request(self, request: MCPRequest, server_name: Optional[str] = None) -> SecurityResult:
    """Run request through all middleware and security plugins."""
    plugins = self._get_all_middleware_and_security_plugins(server_name or "unknown")
    
    current_request = request
    
    for plugin in plugins:
        try:
            # Process based on plugin type
            if isinstance(plugin, SecurityPlugin):
                result = await plugin.process_request(current_request, server_name)
            else:
                # Pure middleware
                result = await plugin.process_request(current_request, server_name)
                
                # Check if middleware completed the request
                if result.completed_response:
                    return SecurityResult(
                        allowed=True,
                        modified_content=result.completed_response,
                        reason=result.reason,
                        metadata={"completed_by": plugin.__class__.__name__}
                    )
            
            # Check if blocked (security plugins only)
            if hasattr(result, 'allowed') and result.allowed is False:
                return result
            
            # Apply modifications
            if result.modified_content and isinstance(result.modified_content, MCPRequest):
                current_request = result.modified_content
                
        except Exception as e:
            if hasattr(plugin, 'is_critical') and plugin.is_critical():
                return SecurityResult(allowed=False, reason=f"Critical plugin failed: {e}")
            logger.warning(f"Non-critical plugin failed: {e}")
    
    # Return final result
    return SecurityResult(
        allowed=True,
        modified_content=current_request if current_request != request else None,
        reason="Processed successfully"
    )
```

### 8. Update Configuration Models

#### Location: `gatekit/config/models.py`

#### Task 8.1: Add middleware to PluginsConfig
```python
class PluginsConfig(BaseModel):
    """Configuration for plugins."""
    security: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    auditing: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)
    middleware: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict)  # Add this
```

### 9. Create Example Middleware Plugins

#### Location: `gatekit/plugins/middleware/`

Create simple examples like cache.py and rate_limit.py (see original requirements for full code).

### 10. Update Tests

#### Task 10.1: Create middleware plugin tests
Create `tests/unit/test_middleware_plugin.py` with basic tests.

#### Task 10.2: Update integration tests
Ensure middleware plugins work in the full pipeline.

## Testing Checklist

1. [ ] All existing tests still pass
2. [ ] Security plugins still work (can block requests)
3. [ ] tool_manager works as middleware (can hide tools)
4. [ ] Middleware can transform requests
5. [ ] Middleware can complete requests (return responses)
6. [ ] Priority ordering works correctly
7. [ ] Critical vs non-critical plugins behave correctly
8. [ ] Configuration loads middleware section

## Success Criteria

- `pytest tests/` passes all tests
- Middleware plugins can be loaded and executed
- tool_manager successfully migrated to middleware
- Security plugins still function correctly
- System maintains backward compatibility where needed

## Estimated Time
- 3-4 hours for implementation
- 1 hour for testing
- Medium complexity but self-contained