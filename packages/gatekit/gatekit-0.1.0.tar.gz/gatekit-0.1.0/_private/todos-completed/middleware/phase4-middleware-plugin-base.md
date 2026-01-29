# Phase 4: Create MiddlewarePlugin Base Class and Hierarchy [COMPLETED]

## Prerequisites
- Phase 3 completed (PolicyDecision eliminated, everything uses SecurityResult)
- All tests passing

## Overview
Introduce the MiddlewarePlugin base class and reorganize the plugin hierarchy so SecurityPlugin extends MiddlewarePlugin. This creates the proper inheritance structure without changing functionality.

## Implementation Tasks

### 1. Create MiddlewarePlugin Base Class

#### Location: `gatekit/plugins/interfaces.py`

#### Task 1.1: Add MiddlewarePlugin class (after PluginInterface, before SecurityPlugin)
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
        # Middleware uses priority for ordering
        self.priority = config.get('priority', 50)
        # Validate priority range
        if not isinstance(self.priority, int) or not (0 <= self.priority <= 100):
            raise ValueError(f"Plugin priority {self.priority} must be between 0 and 100")
    
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
        
        Args:
            request: The MCP request to evaluate
            server_name: Name of the target server
            
        Returns:
            MiddlewareResult: Processing result
        """
        pass
    
    @abstractmethod
    async def process_response(self, request: MCPRequest, response: MCPResponse, server_name: str) -> MiddlewareResult:
        """Process a response from the upstream server.
        
        Args:
            request: The original MCP request
            response: The MCP response to evaluate
            server_name: Name of the source server
            
        Returns:
            MiddlewareResult: Processing result
        """
        pass
    
    @abstractmethod
    async def process_notification(self, notification: MCPNotification, server_name: str) -> MiddlewareResult:
        """Process a notification message.
        
        Args:
            notification: The MCP notification to evaluate
            server_name: Name of the source server
            
        Returns:
            MiddlewareResult: Processing result
        """
        pass
```

### 2. Update SecurityPlugin to Extend MiddlewarePlugin

#### Location: `gatekit/plugins/interfaces.py`

#### Task 2.1: Change SecurityPlugin inheritance
```python
class SecurityPlugin(MiddlewarePlugin):  # Changed from PluginInterface
    """Abstract base class for security policy plugins.
    
    Security plugins evaluate MCP messages (requests, responses, and notifications)
    and determine whether they should be allowed to proceed.
    
    Security plugins extend middleware with the ability to prevent
    requests/responses from proceeding when they violate security policies.
    They MUST return SecurityResult with allowed=True or allowed=False.
    
    CRITICAL SECURITY REQUIREMENT: All three process methods MUST be properly 
    implemented with comprehensive security logic:
    
    - process_request: Validates incoming requests for security violations
    - process_response: Validates outgoing responses to prevent data leakage
    - process_notification: Validates notifications to prevent information disclosure
    
    Security vulnerabilities can occur if any method is not properly implemented.
    For example, only checking requests allows malicious content in responses 
    to bypass security filters.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize security plugin with configuration.
        
        Args:
            config: Plugin-specific configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
            TypeError: If configuration has wrong types
        """
        # Initialize base middleware class
        super().__init__(config)
        
        # Security plugins default to critical (fail closed) - override middleware default
        self.critical = config.get("critical", True)
        
        # Priority is already handled by MiddlewarePlugin
        # Security plugins can be configured as critical or non-critical
    
    # Remove is_critical() - inherited from MiddlewarePlugin
    
    # Override the abstract methods with SecurityResult return type
    @abstractmethod
    async def process_request(self, request: MCPRequest, server_name: str) -> SecurityResult:
        """Evaluate if request should be allowed.
        
        SECURITY REQUIREMENT: Must validate ALL request content for security 
        violations including method names, parameters, and any text content.
        
        Args:
            request: The MCP request to evaluate
            server_name: Name of the target server
            
        Returns:
            SecurityResult: Decision on whether to allow the request
            
        Raises:
            Exception: Plugin-specific errors that should be caught and handled
                      by the plugin manager
        """
        pass
    
    @abstractmethod
    async def process_response(self, request: MCPRequest, response: MCPResponse, server_name: str) -> SecurityResult:
        """Evaluate if response should be allowed.
        
        SECURITY REQUIREMENT: Must validate ALL response content to prevent 
        data leakage. Responses may contain sensitive information not present
        in the original request (file contents, secrets, etc.).
        
        Args:
            request: The original MCP request
            response: The MCP response to evaluate
            server_name: Name of the source server
            
        Returns:
            SecurityResult: Decision on whether to allow the response
            
        Raises:
            Exception: Plugin-specific errors that should be caught and handled
                      by the plugin manager
        """
        pass
    
    @abstractmethod
    async def process_notification(self, notification: MCPNotification, server_name: str) -> SecurityResult:
        """Evaluate if notification should be allowed.
        
        SECURITY REQUIREMENT: Must validate ALL notification content to prevent
        information disclosure. Notifications can leak information about 
        restricted operations, paths, or contain sensitive data.
        
        Args:
            notification: The MCP notification to evaluate
            server_name: Name of the source server
            
        Returns:
            SecurityResult: Decision on whether to allow the notification
            
        Raises:
            Exception: Plugin-specific errors that should be caught and handled
                      by the plugin manager
        """
        pass
```

### 3. Add ProcessingPipeline Types for Observability

#### Location: `gatekit/plugins/interfaces.py`

#### Task 3.1: Add PipelineStage and ProcessingPipeline dataclasses
These types support full observability of how messages flow through the plugin pipeline.

```python
from dataclasses import dataclass
from typing import List, Optional, Union
import time

@dataclass
class PipelineStage:
    """Record of a single plugin's processing within the pipeline.
    
    Captures how each plugin transforms or evaluates a message,
    enabling debugging and performance analysis.
    """
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
        return hasattr(self.result, 'allowed') and self.result.allowed is False
    
    @property
    def completed(self) -> bool:
        """Check if this stage completed the request (middleware only)."""
        return hasattr(self.result, 'completed_response') and self.result.completed_response is not None

@dataclass
class ProcessingPipeline:
    """Complete record of message processing through all plugins.
    
    Provides full visibility into how a message was processed,
    modified, and evaluated by the plugin pipeline.
    """
    original_content: Union[MCPRequest, MCPResponse, MCPNotification]
    stages: List[PipelineStage] = field(default_factory=list)
    final_content: Optional[Union[MCPRequest, MCPResponse, MCPNotification]] = None
    total_time_ms: float = 0.0
    final_decision: bool = True
    blocked_at_stage: Optional[str] = None
    completed_by: Optional[str] = None
    
    def add_stage(self, stage: PipelineStage) -> None:
        """Add a processing stage to the pipeline."""
        self.stages.append(stage)
        if stage.blocked:
            self.final_decision = False
            self.blocked_at_stage = stage.plugin_name
        elif stage.completed:
            self.completed_by = stage.plugin_name
    
    def get_modifications(self) -> List[str]:
        """Get list of plugins that modified the content."""
        return [stage.plugin_name for stage in self.stages if stage.modified]
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get a summary of the pipeline processing."""
        return {
            "total_stages": len(self.stages),
            "modifications": self.get_modifications(),
            "blocked": self.blocked_at_stage is not None,
            "blocked_by": self.blocked_at_stage,
            "completed_early": self.completed_by is not None,
            "completed_by": self.completed_by,
            "total_time_ms": self.total_time_ms,
            "final_decision": self.final_decision
        }
```

### 4. Update Exports

#### Location: `gatekit/plugins/__init__.py`

#### Task 4.1: Add MiddlewarePlugin and ProcessingPipeline types to exports
```python
from .interfaces import (
    PluginInterface,
    PathResolvablePlugin,
    MiddlewarePlugin,  # Add
    SecurityPlugin,
    AuditingPlugin,
    MiddlewareResult,
    SecurityResult,
    PipelineStage,  # Add
    ProcessingPipeline  # Add
)

__all__ = [
    "PluginInterface",
    "PathResolvablePlugin",
    "MiddlewarePlugin",  # Add
    "SecurityPlugin",
    "AuditingPlugin",
    "MiddlewareResult",
    "SecurityResult",
    "PipelineStage",  # Add
    "ProcessingPipeline",  # Add
    "PluginManager"
]
```

### 5. Write Tests for MiddlewarePlugin and ProcessingPipeline

#### Location: Create `tests/unit/test_middleware_plugin_base.py`

```python
"""Tests for MiddlewarePlugin base class."""

import pytest
from abc import ABC
from typing import Dict, Any
from gatekit.plugins.interfaces import MiddlewarePlugin, MiddlewareResult, SecurityPlugin, SecurityResult
from gatekit.protocol.messages import MCPRequest, MCPResponse, MCPNotification


class TestMiddlewarePlugin(MiddlewarePlugin):
    """Test implementation of MiddlewarePlugin."""
    
    async def process_request(self, request: MCPRequest, server_name: str) -> MiddlewareResult:
        return MiddlewareResult(reason="test")
    
    async def process_response(self, request: MCPRequest, response: MCPResponse, server_name: str) -> MiddlewareResult:
        return MiddlewareResult(reason="test")
    
    async def process_notification(self, notification: MCPNotification, server_name: str) -> MiddlewareResult:
        return MiddlewareResult(reason="test")


def test_middleware_plugin_defaults():
    """Test middleware plugin default configuration."""
    plugin = TestMiddlewarePlugin({})
    assert plugin.critical is False  # Middleware defaults to non-critical
    assert plugin.priority == 50
    assert plugin.is_critical() is False


def test_middleware_plugin_critical_config():
    """Test middleware plugin critical configuration."""
    plugin = TestMiddlewarePlugin({"critical": True})
    assert plugin.critical is True
    assert plugin.is_critical() is True


def test_middleware_plugin_priority():
    """Test middleware plugin priority configuration."""
    plugin = TestMiddlewarePlugin({"priority": 10})
    assert plugin.priority == 10
    
    # Test invalid priority
    with pytest.raises(ValueError, match="priority.*must be between"):
        TestMiddlewarePlugin({"priority": 150})


def test_security_plugin_inherits_middleware():
    """Test that SecurityPlugin properly inherits from MiddlewarePlugin."""
    # SecurityPlugin should be a subclass of MiddlewarePlugin
    assert issubclass(SecurityPlugin, MiddlewarePlugin)


def test_security_plugin_defaults():
    """Test that security plugins have different defaults than middleware."""
    
    class TestSecurityPlugin(SecurityPlugin):
        async def process_request(self, request: MCPRequest, server_name: str) -> SecurityResult:
            return SecurityResult(allowed=True, reason="test")
        
        async def process_response(self, request: MCPRequest, response: MCPResponse, server_name: str) -> SecurityResult:
            return SecurityResult(allowed=True, reason="test")
        
        async def process_notification(self, notification: MCPNotification, server_name: str) -> SecurityResult:
            return SecurityResult(allowed=True, reason="test")
    
    plugin = TestSecurityPlugin({})
    assert plugin.critical is True  # Security defaults to critical
    assert plugin.priority == 50
    assert plugin.is_critical() is True


@pytest.mark.asyncio
async def test_middleware_plugin_interface():
    """Test middleware plugin interface methods."""
    plugin = TestMiddlewarePlugin({})
    request = MCPRequest(jsonrpc="2.0", id=1, method="test", params={})
    response = MCPResponse(jsonrpc="2.0", id=1, result={})
    notification = MCPNotification(jsonrpc="2.0", method="test", params={})
    
    result1 = await plugin.process_request(request, "test_server")
    assert isinstance(result1, MiddlewareResult)
    
    result2 = await plugin.process_response(request, response, "test_server")
    assert isinstance(result2, MiddlewareResult)
    
    result3 = await plugin.process_notification(notification, "test_server")
    assert isinstance(result3, MiddlewareResult)


def test_pipeline_stage_properties():
    """Test PipelineStage properties."""
    from gatekit.plugins.interfaces import PipelineStage
    
    request = MCPRequest(jsonrpc="2.0", id=1, method="test", params={})
    modified_request = MCPRequest(jsonrpc="2.0", id=1, method="test_modified", params={})
    
    # Test modified property
    stage1 = PipelineStage(
        plugin_name="TestPlugin",
        plugin_type="middleware",
        input_content=request,
        output_content=modified_request,
        result=MiddlewareResult(modified_content=modified_request),
        processing_time_ms=1.5
    )
    assert stage1.modified is True
    
    # Test blocked property (security plugin)
    stage2 = PipelineStage(
        plugin_name="SecurityPlugin",
        plugin_type="security",
        input_content=request,
        output_content=None,
        result=SecurityResult(allowed=False, reason="Blocked"),
        processing_time_ms=0.5
    )
    assert stage2.blocked is True
    
    # Test completed property (middleware with completed_response)
    completed_response = MCPResponse(jsonrpc="2.0", id=1, result={})
    stage3 = PipelineStage(
        plugin_name="CachePlugin",
        plugin_type="middleware",
        input_content=request,
        output_content=None,
        result=MiddlewareResult(completed_response=completed_response),
        processing_time_ms=0.2
    )
    assert stage3.completed is True


def test_processing_pipeline():
    """Test ProcessingPipeline functionality."""
    from gatekit.plugins.interfaces import ProcessingPipeline, PipelineStage
    
    request = MCPRequest(jsonrpc="2.0", id=1, method="test", params={})
    pipeline = ProcessingPipeline(original_content=request)
    
    # Add a modification stage
    stage1 = PipelineStage(
        plugin_name="ModifierPlugin",
        plugin_type="middleware",
        input_content=request,
        output_content=request,
        result=MiddlewareResult(modified_content=request),
        processing_time_ms=1.0
    )
    pipeline.add_stage(stage1)
    
    # Add a blocking stage
    stage2 = PipelineStage(
        plugin_name="BlockerPlugin",
        plugin_type="security",
        input_content=request,
        output_content=None,
        result=SecurityResult(allowed=False, reason="Blocked"),
        processing_time_ms=0.5
    )
    pipeline.add_stage(stage2)
    
    assert pipeline.blocked_at_stage == "BlockerPlugin"
    assert pipeline.final_decision is False
    assert "ModifierPlugin" in pipeline.get_modifications()
    
    summary = pipeline.get_processing_summary()
    assert summary["total_stages"] == 2
    assert summary["blocked"] is True
    assert summary["blocked_by"] == "BlockerPlugin"
```

## Testing Checklist

1. [ ] Run `pytest tests/unit/test_middleware_plugin_base.py` - new tests pass
2. [ ] Run `pytest tests/` - ALL existing tests pass
3. [ ] Security plugins still work correctly
4. [ ] Plugin hierarchy is correct (SecurityPlugin extends MiddlewarePlugin)
5. [ ] ProcessingPipeline types work correctly for observability

## Success Criteria

- MiddlewarePlugin base class created
- SecurityPlugin properly extends MiddlewarePlugin
- ProcessingPipeline types provide plugin observability
- All existing security plugins still work
- New tests pass for middleware base class and pipeline types
- System behavior unchanged

## Notes
- This phase sets up the hierarchy but doesn't add middleware functionality yet
- Security plugins now inherit middleware capabilities but still use SecurityResult
- Priority handling is unified in MiddlewarePlugin