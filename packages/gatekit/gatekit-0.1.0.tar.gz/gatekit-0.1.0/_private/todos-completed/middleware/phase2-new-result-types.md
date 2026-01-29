# Phase 2: Create New Result Types

## Prerequisites
- Phase 1 (method rename) must be completed
- All tests passing with `process_*` methods

## Overview
Create the new `MiddlewareResult` and `SecurityResult` types that will replace `PolicyDecision`. These will coexist with PolicyDecision temporarily until Phase 3.

## Implementation Tasks

### 1. Add New Result Types to interfaces.py

#### Location: `gatekit/plugins/interfaces.py`

#### Task 1.1: Add imports
Add to existing imports:
```python
from typing import Optional
```

#### Task 1.2: Add MiddlewareResult class (after PolicyDecision)
```python
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

#### Task 1.3: Add SecurityResult class (after MiddlewareResult)
```python
@dataclass
class SecurityResult(MiddlewareResult):
    """Security plugin result that requires an allow/block determination.
    
    Security plugins must return SecurityResult with allowed set to True or False.
    """
    allowed: bool = True  # Required field for security decisions
    
    def __post_init__(self):
        """Ensure metadata is initialized and validate allowed field."""
        super().__post_init__()
        # allowed field must be a boolean
        if not isinstance(self.allowed, bool):
            raise ValueError("Security plugins must set allowed to True or False")
```

### 2. Update Exports

#### Location: `gatekit/plugins/__init__.py`

#### Task 2.1: Add new exports
Add to the existing imports from interfaces:
```python
from .interfaces import (
    PluginInterface,
    PolicyDecision,  # Keep for now
    PathResolvablePlugin,
    SecurityPlugin,
    AuditingPlugin,
    MiddlewareResult,  # Add
    SecurityResult     # Add
)
```

Update `__all__`:
```python
__all__ = [
    "PluginInterface",
    "PolicyDecision",  # Keep for now
    "PathResolvablePlugin", 
    "SecurityPlugin",
    "AuditingPlugin",
    "MiddlewareResult",  # Add
    "SecurityResult",    # Add
    "PluginManager"
]
```

### 3. Write Tests for New Types

#### Location: Create `tests/unit/test_middleware_result_types.py`

```python
"""Tests for new MiddlewareResult and SecurityResult types."""

import pytest
from gatekit.plugins.interfaces import MiddlewareResult, SecurityResult
from gatekit.protocol.messages import MCPRequest, MCPResponse

def test_middleware_result_basic():
    """Test basic MiddlewareResult creation."""
    result = MiddlewareResult(reason="test")
    assert result.reason == "test"
    assert result.metadata == {}
    assert result.modified_content is None
    assert result.completed_response is None

def test_middleware_result_with_modified_content():
    """Test MiddlewareResult with modified content."""
    request = MCPRequest(jsonrpc="2.0", id=1, method="test", params={})
    result = MiddlewareResult(
        modified_content=request,
        reason="Modified request"
    )
    assert result.modified_content == request
    assert result.completed_response is None

def test_middleware_result_with_completed_response():
    """Test MiddlewareResult with completed response."""
    response = MCPResponse(jsonrpc="2.0", id=1, result={})
    result = MiddlewareResult(
        completed_response=response,
        reason="Handled directly"
    )
    assert result.completed_response == response
    assert result.modified_content is None

def test_middleware_result_cannot_have_both():
    """Test that MiddlewareResult cannot have both modified_content and completed_response."""
    request = MCPRequest(jsonrpc="2.0", id=1, method="test", params={})
    response = MCPResponse(jsonrpc="2.0", id=1, result={})
    
    with pytest.raises(ValueError, match="Cannot set both"):
        MiddlewareResult(
            modified_content=request,
            completed_response=response
        )

def test_security_result_basic():
    """Test basic SecurityResult creation."""
    result = SecurityResult(allowed=True, reason="test")
    assert result.allowed is True
    assert result.reason == "test"
    assert result.metadata == {}

def test_security_result_inherits_middleware():
    """Test that SecurityResult inherits MiddlewareResult fields."""
    request = MCPRequest(jsonrpc="2.0", id=1, method="test", params={})
    result = SecurityResult(
        allowed=False,
        modified_content=request,
        reason="Blocked but modified",
        metadata={"test": "value"}
    )
    assert result.allowed is False
    assert result.modified_content == request
    assert result.metadata == {"test": "value"}

def test_security_result_requires_boolean_allowed():
    """Test that SecurityResult requires allowed to be a boolean."""
    with pytest.raises(ValueError, match="must set allowed to True or False"):
        SecurityResult(allowed="yes", reason="test")
```

## Testing Checklist

1. [ ] Run `pytest tests/unit/test_middleware_result_types.py` - new tests pass
2. [ ] Run `pytest tests/` - ALL existing tests still pass
3. [ ] No import errors from the new types
4. [ ] PolicyDecision still works (not broken)

## Success Criteria

- New types are created and tested
- Old types still work
- All tests pass
- System behavior unchanged

## Notes
- PolicyDecision remains untouched for now
- SecurityResult extends MiddlewareResult for clean hierarchy
- Both new types can coexist with PolicyDecision