# Routing Architecture Migration Plan

## Overview
This document details the step-by-step migration from the current triple-parsing routing architecture to the boundary translation pattern described in target-spec.md.

## Current State Summary
- Triple parsing of namespaced strings (proxy → plugin manager → proxy)
- Context loss during denamespacing for plugins
- Routing decisions attempted on already-denamespaced requests
- Namespacing logic scattered across multiple components

## Target State Summary
- Single parse at Protocol Boundary Layer
- Routing context preserved throughout processing
- Clean internal representations
- Namespacing only at system edges

## Migration Strategy
Incremental refactoring maintaining functionality at each step.

## Phase 1: Create Core Data Structures
**Goal**: Establish the foundation without changing behavior

### 1.1 Create RoutedRequest Class
```python
# gatekit/core/routing.py (NEW FILE)
@dataclass
class RoutedRequest:
    """Carries request and routing context through the system as a unit.
    
    This class encapsulates both the clean request for processing and
    the routing metadata needed to deliver it and format responses.
    """
    request: MCPRequest  # Clean, denamespaced request for processing
    target_server: Optional[str]  # Target server (None for broadcasts/single-server)
    namespaced_name: Optional[str]  # Original namespaced name for response formatting
    
    def update_request(self, new_request: MCPRequest) -> 'RoutedRequest':
        """Create new RoutedRequest with updated request but same routing context."""
        return RoutedRequest(
            request=new_request,
            target_server=self.target_server,
            namespaced_name=self.namespaced_name
        )
```

### 1.2 Create Boundary Translation Functions
```python
# gatekit/core/routing.py
def parse_incoming_request(request: MCPRequest) -> RoutedRequest:
    """Parse client request once at ingress - single point of namespace extraction."""
    if request.method == "tools/call" and request.params:
        tool_name = request.params.get("name", "")
        if not tool_name:
            raise ValueError("Tool call missing 'name' parameter")
        
        if "__" not in tool_name:
            # ALL tool calls must be namespaced - no special single-server handling
            raise ValueError(
                f"Tool '{tool_name}' is not namespaced. All tool calls must use "
                f"'server__tool' format"
            )
        
        parts = tool_name.split("__", 1)  # Split only on first __
        server_name = parts[0]
        clean_tool = parts[1]
        
        # Create clean request
        clean_params = {**request.params, "name": clean_tool}
        clean_request = MCPRequest(
            jsonrpc=request.jsonrpc,
            method=request.method,
            id=request.id,
            params=clean_params,
            sender_context=request.sender_context
        )
        
        return RoutedRequest(
            request=clean_request,
            target_server=server_name,
            namespaced_name=tool_name
        )
    
    # Similar strict validation for resources/call and prompts/get...
    
    # Broadcast methods (tools/list, initialize, etc.) don't need namespacing
    return RoutedRequest(
        request=request, 
        target_server=None,  # Will be broadcast to all servers
        namespaced_name=None
    )

def prepare_outgoing_response(response: MCPResponse, routed: RoutedRequest) -> MCPResponse:
    """Apply namespace to outgoing response if needed.
    
    Uses the preserved namespaced_name from the RoutedRequest to 
    restore namespacing in error messages or other response fields.
    """
    if not routed.namespaced_name:
        return response  # No namespacing needed
        
    # Re-namespace error messages that reference the tool
    if response.error:
        # Update error message to use original namespaced name
        # ...implementation...
    
    return response
```

### Files to Create:
- `/Users/dbright/mcp/gatekit/gatekit/core/routing.py`

### Tests to Create:
- `/Users/dbright/mcp/gatekit/tests/unit/test_routing.py`

## Phase 2: Update Protocol Boundary Layer
**Goal**: Implement single parse point and consistent data flow

### 2.1 Update GatekitServer.handle_request()
```python
# gatekit/proxy/server.py
async def handle_request(self, request: MCPRequest) -> MCPResponse:
    # Parse ONCE at ingress - create RoutedRequest
    routed = parse_incoming_request(request)
    
    # Process with clean request from RoutedRequest
    pipeline_result = await self.plugin_manager.process_request(
        routed.request,
        server_name=routed.target_server
    )
    
    # Update RoutedRequest if plugins modified the request
    if pipeline_result.final_content != routed.request:
        routed = routed.update_request(pipeline_result.final_content)
    
    # Route using the complete RoutedRequest
    response = await self._route_request(routed)
    
    # Apply namespace at egress using preserved context
    return prepare_outgoing_response(response, routed)
```

### 2.2 Update routing methods to accept RoutedRequest
```python
async def _route_request(self, routed: RoutedRequest) -> MCPResponse:
    """Route based on RoutedRequest context."""
    if self._is_broadcast_method(routed.request.method):
        return await self._broadcast_request(routed.request)
    return await self._route_to_single_server(routed)

async def _route_to_single_server(self, routed: RoutedRequest) -> MCPResponse:
    """Route to specific server using RoutedRequest.
    
    All non-broadcast requests MUST have a target server.
    No distinction between single and multi-server setups.
    """
    server_name = routed.target_server
    
    # This should never happen with proper boundary validation
    if not server_name:
        raise ValueError(
            "Internal error: Non-namespaced request reached routing layer. "
            "All tool/resource/prompt calls must be namespaced."
        )
    
    conn = self._server_manager.get_connection(server_name)
    if not conn:
        raise Exception(f"Unknown server: {server_name}")
    
    # Send the clean request from RoutedRequest
    return await conn.send_request(routed.request)
```

### Files to Modify:
- `/Users/dbright/mcp/gatekit/gatekit/proxy/server.py`
  - Update handle_request() to use RoutedRequest
  - Update _route_request() to accept RoutedRequest
  - Update _route_to_single_server() to accept RoutedRequest
  - Remove extract_server_context() calls
  - Remove create_denamespaced_request_params() calls

## Phase 3: Update Processing Layer
**Goal**: Remove denamespacing from plugin manager - plugins receive clean requests

### 3.1 Update PluginManager.process_request()
```python
# gatekit/plugins/manager.py
async def process_request(
    self,
    request: MCPRequest,  # Already clean from boundary layer
    server_name: Optional[str] = None
) -> ProcessingPipeline:
    # DELETE lines 358-369 - no more denamespacing needed
    # Request is already clean from the boundary layer
    
    # Plugins receive the clean request directly
    current_request = request
    
    # Rest of processing remains the same...
```

### 3.2 Clean up imports
```python
# Remove from gatekit/plugins/manager.py:
from gatekit.utils.namespacing import create_denamespaced_request_params
```

### Files to Modify:
- `/Users/dbright/mcp/gatekit/gatekit/plugins/manager.py`
  - Lines 358-369: Remove denamespacing block entirely
  - Line 22: Remove import of create_denamespaced_request_params

## Phase 4: Remove Old Routing Functions
**Goal**: Clean up duplicate/old routing code

### 4.1 Remove old functions from server.py
```python
# DELETE these old functions that do triple parsing:
# - Old _route_to_single_server() that calls extract_server_context()
# - Old _route_request() that duplicates routing logic
```

### 4.2 Remove namespacing utilities no longer needed
```python
# From gatekit/utils/namespacing.py, remove:
# - extract_server_context()
# - create_denamespaced_request_params()
# Keep only the list response namespacing functions
```

### Files to Modify:
- `/Users/dbright/mcp/gatekit/gatekit/proxy/server.py`
  - Remove duplicate routing functions
- `/Users/dbright/mcp/gatekit/gatekit/utils/namespacing.py`
  - Remove extraction/denamespacing utilities

## Phase 5: Update Response Processing
**Goal**: Consistent namespacing at boundaries

### 5.1 Ensure list responses are namespaced
The existing namespace_tools_response(), namespace_resources_response(), 
and namespace_prompts_response() functions already handle this correctly.
Just ensure they're called at the right boundary points.

### 5.2 Update prepare_outgoing_response()
```python
def prepare_outgoing_response(response: MCPResponse, routed: RoutedRequest) -> MCPResponse:
    """Apply namespace to error messages if needed."""
    if not routed.namespaced_name:
        return response
    
    # If error mentions the clean tool name, replace with namespaced version
    if response.error and routed.request.params:
        clean_name = routed.request.params.get("name") or \
                    routed.request.params.get("uri") 
        if clean_name and clean_name in response.error.get("message", ""):
            response.error["message"] = response.error["message"].replace(
                clean_name, routed.namespaced_name
            )
    
    return response
```

### Files to Modify:
- `/Users/dbright/mcp/gatekit/gatekit/core/routing.py`
  - Implement proper error message renamespacing

## Phase 6: Testing and Validation
**Goal**: Comprehensive test coverage of new routing

### 6.1 Unit Tests for Core Routing
```python
# tests/unit/test_routing.py
def test_routed_request_preserves_context():
    """Verify RoutedRequest maintains context through updates"""
    routed = RoutedRequest(request, "server1", "server1__tool")
    updated = routed.update_request(modified_request)
    assert updated.target_server == "server1"
    assert updated.namespaced_name == "server1__tool"

def test_parse_handles_double_underscore_in_names():
    """Verify only first __ is used for parsing"""
    request = create_request("server__tool__with__underscores")
    routed = parse_incoming_request(request)
    assert routed.target_server == "server"
    assert routed.request.params["name"] == "tool__with__underscores"
```

### 6.2 Integration Tests
```python
# tests/integration/test_routing_flow.py
async def test_routed_request_flows_through_system():
    """Verify RoutedRequest flows consistently through all layers"""
    # Test that routing context is preserved from ingress to egress
    
async def test_no_triple_parsing():
    """Verify namespacing is parsed exactly once"""
    # Hook into parse points and verify single parse
```

### 6.3 Update Existing Tests
- Update mock expectations to use RoutedRequest
- Remove tests that expect denamespacing in plugin manager
- Update tests to expect clean requests in plugins

## Rollback Plan
Each phase can be reverted independently:
1. Phase 1: Remove new files (no impact)
2. Phase 2-5: Git revert the specific phase commit
3. Tests will catch any regressions

## Success Criteria
- [ ] Single parse point at ingress (parse_incoming_request)
- [ ] RoutedRequest flows as a unit through all layers
- [ ] No unpacking/repacking of routing context
- [ ] Clean requests to plugins (no namespacing)
- [ ] Proper renamespacing at egress for errors
- [ ] All existing tests updated and passing
- [ ] New routing tests validate the flow

## Risk Assessment
**Low Risk**: Each phase maintains functionality
**Testing**: Comprehensive test coverage at each phase
**Rollback**: Simple git reverts if issues arise

## Key Design Principles
1. **RoutedRequest is the carrier**: It flows intact through the system
2. **Single parse point**: Namespacing extracted once at ingress  
3. **Consistent interfaces**: Functions accept RoutedRequest when they need routing context
4. **Clear field names**: `namespaced_name` not vague names like `original_tool`
5. **No redundancy**: Don't pass data that's already in RoutedRequest

## Timeline Estimate
- Phase 1: 30 minutes (create RoutedRequest and core functions)
- Phase 2: 1 hour (update boundary layer to use RoutedRequest consistently)
- Phase 3: 15 minutes (remove denamespacing from plugin manager)
- Phase 4: 15 minutes (remove old duplicate functions)
- Phase 5: 30 minutes (verify response namespacing)
- Phase 6: 1 hour (comprehensive testing)

**Total: ~3 hours of focused work**

## Next Steps
1. Review this plan for completeness
2. Create Phase 1 structures
3. Write initial tests
4. Proceed phase by phase with testing at each step