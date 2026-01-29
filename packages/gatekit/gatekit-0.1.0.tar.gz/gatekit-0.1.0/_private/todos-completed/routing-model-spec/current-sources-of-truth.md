# Current Routing Implementation - Sources of Truth

## Overview
This document captures the CURRENT implementation of the boundary translation routing pattern in Gatekit after the refactoring completed in v0.1.0.

## 1. Current Implementation

### core/routing.py - Boundary Translation Pattern

The routing module implements clean boundary translation with three key components:

#### RoutedRequest - Cohesive Request + Routing Context
```python
@dataclass
class RoutedRequest:
    request: MCPRequest           # Clean, denamespaced request
    target_server: Optional[str]  # Extracted server name
    namespaced_name: Optional[str] # Original namespaced identifier for error messages
```

#### Parse Once at Ingress
```python
def parse_incoming_request(request: MCPRequest) -> Union[RoutedRequest, MCPResponse]:
    # Single parsing point - extracts namespace ONCE
    # Returns RoutedRequest with clean request + routing metadata
    # OR returns MCPResponse error if invalid namespace
```

#### Restore at Egress
```python
def prepare_outgoing_response(response: MCPResponse, routed: RoutedRequest) -> MCPResponse:
    # Re-namespaces error messages using preserved namespaced_name
    # Uses regex with word boundaries to avoid partial replacements
```

### proxy/server.py - Request Flow

#### Step 1: Parse at Ingress
```python
routed = parse_incoming_request(request)
if isinstance(routed, MCPResponse):
    # Audit parse-time rejection and return error
    return routed
```

#### Step 2: Plugin Processing with Clean Request
```python
request_pipeline = await self._plugin_manager.process_request(routed.request, routed.target_server)
# Plugins see CLEAN request (no namespacing)
```

#### Step 3: Route Using RoutedRequest
```python
response = await self._route_request(routed)
# Passes complete RoutedRequest to routing
```

#### Step 4: Response Processing with Clean Request
```python
response_pipeline = await self._plugin_manager.process_response(routed.request, response, routed.target_server)
# Response plugins also see CLEAN request
```

#### Step 5: Restore Namespacing at Egress
```python
final_response = prepare_outgoing_response(response, routed)
# Re-namespaces error messages for client
```

## 2. Key Principles

1. **Single Parse Point**: Namespacing is extracted ONCE at ingress
2. **Clean Internal Representation**: All internal processing uses clean, denamespaced requests
3. **Boundary Translation**: Namespacing only exists at system boundaries (ingress/egress)
4. **No Single-Server Special Cases**: ALL tool/resource/prompt calls must be namespaced
5. **Immutable Routing**: Routing-critical parameters cannot be changed by plugins (see ADR-024)

## 3. Enforcement Points

### Validation at Parse Time
- Non-namespaced tool/resource/prompt calls return `MCPResponse` errors
- Invalid namespace format returns structured JSON-RPC errors
- Parse-time rejections are audited for security visibility

### Immutability in RoutedRequest
```python
def update_request(self, new_request: MCPRequest) -> 'RoutedRequest':
    # Cannot change: ID, method
    # Cannot change: tool name, resource URI, prompt name
    # These are routing-critical and must remain immutable
```

### Server Validation
- Server existence is validated AFTER plugin processing
- Allows plugins to potentially affect routing (future enhancement)
- Non-existent servers return `MCPErrorCodes.INVALID_PARAMS`

## 4. Rationale for Design Choices

### Why Parse Once?
- Eliminates triple-parsing inefficiency
- Single source of truth for routing decisions
- Consistent extraction logic

### Why Clean Internal Representation?
- Plugins don't need to understand namespacing
- Simplifies plugin development
- Consistent request format throughout pipeline

### Why Immutable Routing Parameters?
- Security: Prevents bypassing allowlists
- Auditability: What was requested is what gets logged
- Correctness: Error messages match client's request
- See ADR-024 for detailed rationale

### Why Validate Server After Plugins?
- Allows future routing plugins to redirect requests
- Plugins might create virtual servers or modify routing
- Trade-off: Some plugin CPU spent on impossible routes
- Benefit: Maximum flexibility for future enhancements

## 5. Testing Coverage

All routing behavior is tested in:
- `tests/unit/test_routing.py` - Core routing logic
- `tests/integration/test_proxy_integration.py` - End-to-end routing
- `tests/integration/test_aggregated_tools_list_integration.py` - List aggregation with namespacing
- `tests/unit/test_proxy_server.py` - Request flow through proxy

## 6. Migration from Previous Implementation

The old implementation had:
- `extract_server_context()` - Called multiple times
- `create_denamespaced_request_params()` - Redundant denamespacing
- `parse_namespaced_name()` - Low-level parsing

These have been replaced by:
- `parse_incoming_request()` - Single parse point
- `RoutedRequest` - Carries context throughout
- `prepare_outgoing_response()` - Restore at egress

## 7. Future Considerations

If dynamic routing is needed, see ADR-024 for proposed approaches:
- Explicit redirect mechanism
- Router plugin type
- Mutable routing with recomputation

The current implementation is intentionally restrictive to maintain security and correctness guarantees.