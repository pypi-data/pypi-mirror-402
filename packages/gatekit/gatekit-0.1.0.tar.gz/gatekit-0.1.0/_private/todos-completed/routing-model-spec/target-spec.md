# Gatekit Routing Model

**Version**: 0.1.0
**Status**: Target Architecture Specification  

> **Note**: This document describes the TARGET routing architecture for Gatekit. It serves as the authoritative reference for how routing WILL work after implementation of the boundary translation pattern.

## Table of Contents

1. [Core Principles](#core-principles)
2. [Architecture Layers](#architecture-layers)
3. [Data Flow](#data-flow)
4. [Request Routing](#request-routing)
5. [Response Routing](#response-routing)
6. [Broadcast Methods](#broadcast-methods)
7. [Plugin Interactions](#plugin-interactions)
8. [Error Handling](#error-handling)
9. [Example Scenarios](#example-scenarios)

## Core Principles

### Principle 1: Boundary Translation
Namespacing with the `__` separator is an **external protocol concern** required by the MCP client/LLM. It should be handled ONLY at system boundaries, not throughout internal architecture.

### Principle 2: Single Parse Point
Each namespaced identifier should be parsed **exactly once** at system ingress. The extracted routing metadata should be preserved and passed through the system.

### Principle 3: Clean Internal Representation
Internal components work with clean, structured data. They should never need to understand or parse namespacing.

### Principle 4: Explicit Routing Context
Routing decisions are made using explicitly preserved context, not by re-extracting information from modified content.

### Principle 5: No Single-Server Special Cases
There is **no distinction** between single-server and multi-server deployments. ALL non-broadcast requests (tools/call, resources/call, prompts/get) MUST be namespaced with the `server__name` format, regardless of the number of configured upstream servers. This ensures consistent behavior and prevents ambiguity.

## Architecture Layers

### 1. Protocol Boundary Layer (Proxy)

**Responsibilities:**
- Parse namespaced identifiers at ingress (client → proxy)
- Apply namespacing at egress (proxy → client)
- Maintain clean internal representations
- Preserve routing metadata throughout processing

**Key Operations:**
- `parse_namespace(request)` → `(server_name, clean_params)`
- `apply_namespace(response, server_name)` → namespaced response

**This is the ONLY layer that understands the `__` separator.**

### 2. Processing Layer (Plugin System)

**Responsibilities:**
- Process clean requests/responses through plugins
- Pass routing context as explicit metadata
- Allow content modification without affecting routing
- Maintain plugin isolation from routing concerns

**What Plugins See:**
- Clean tool/resource names (no namespace prefix)
- Server context as a separate parameter
- Can modify content without breaking routing

### 3. Routing Layer (Server Communication)

**Responsibilities:**
- Route requests to correct upstream server
- Use preserved routing context (never re-parse)
- Handle connection management
- Send clean requests to upstream servers

**Key Operations:**
- Uses `server_name` from initial parse
- Never attempts to extract routing from content
- Maintains request→server correlation for responses

## Data Flow

### Ingress Flow (Client → Upstream)

```
1. CLIENT REQUEST
   {"method": "tools/call", "params": {"name": "filesystem__read_file"}}
   
2. BOUNDARY PARSE (Once, at proxy entry)
   server_name = "filesystem"
   clean_params = {"name": "read_file"}
   
3. PLUGIN PROCESSING
   Plugins receive: clean_params + server_name
   Can modify params but server_name remains stable
   
4. ROUTING DECISION
   Uses preserved server_name (not re-extracted)
   
5. UPSTREAM REQUEST
   Send clean_params to filesystem server
```

### Egress Flow (Upstream → Client)

```
1. UPSTREAM RESPONSE
   {"result": {"tools": [{"name": "read_file"}, {"name": "write_file"}]}}
   
2. PLUGIN PROCESSING
   Plugins see clean response
   Can modify content
   
3. BOUNDARY TRANSFORM (at proxy exit)
   Add namespace: "filesystem__read_file", "filesystem__write_file"
   
4. CLIENT RESPONSE
   {"result": {"tools": [{"name": "filesystem__read_file"}, ...]}}
```

## Request Routing

### Non-Broadcast Requests (tools/call, resources/call, prompts/get)

**Pattern**: All non-broadcast requests MUST be namespaced

```
Input: tools/call with "filesystem__read_file"
Parse: server="filesystem", tool="read_file"
Route: Send to filesystem server with tool="read_file"
```

**Key Points:**
- ALL requests must include server namespace (no single-server exceptions)
- Server name extracted once at boundary
- Travels with request through pipeline
- Never re-extracted from modified content
- Non-namespaced requests are rejected with ValueError

### Multi-Server Disambiguation

**Pattern**: Namespace prevents tool name conflicts

```
Server A has: read_file, write_file
Server B has: read_file, delete_file

Client sees: 
- filesystem__read_file (Server A)
- database__read_file (Server B)
```

**Key Points:**
- Each server's tools are isolated
- Client disambiguates via namespacing
- Internal processing uses clean names

## Response Routing

### Response Correlation

Responses are correlated to their originating requests using:
1. Request ID mapping to server name
2. Preserved routing context from request phase
3. Never parsing response content for routing

### Response Processing

```
1. Receive response from known server (context preserved)
2. Process through plugins with server context
3. Apply namespace at boundary for client
```

## Broadcast Methods

### Tools/List Aggregation

**Pattern**: Broadcast, collect, namespace, aggregate

```
1. CLIENT: "tools/list" (no namespace)
2. PROXY: Identify as broadcast method
3. BROADCAST: Send to all servers
4. COLLECT: 
   - filesystem: ["read_file", "write_file"]
   - database: ["query", "insert"]
5. NAMESPACE: Apply prefixes
   - ["filesystem__read_file", "filesystem__write_file"]
   - ["database__query", "database__insert"]
6. AGGREGATE: Combine and return to client
```

**Key Points:**
- No namespace in request (broadcast indicator)
- Each server returns clean names
- Proxy adds namespaces before aggregation
- Client sees fully namespaced results

### Resources and Prompts

Same pattern as tools/list:
- `resources/list` → aggregated with namespaces
- `prompts/list` → aggregated with namespaces

## Plugin Interactions

### What Plugins Receive

```python
# Plugins see:
request: MCPRequest with clean params (no namespace)
server_name: str with routing context

# Example:
request.params = {"name": "read_file"}  # Clean
server_name = "filesystem"  # Context
```

### Plugin Modifications

**Allowed Modifications:**
- Tool/resource names (plugin manages mapping)
- Parameters and arguments
- Descriptions and metadata

**Preserved Through Pipeline:**
- Server routing context
- Request correlation IDs

### Tool Name Mutations

When a plugin mutates tool names:

```
1. REQUEST: Client sends "safe_read" (custom name)
2. PLUGIN: Maps "safe_read" → "read_file" (server name)
3. UPSTREAM: Receives "read_file" (what it expects)
4. RESPONSE: Returns for "read_file"
5. PLUGIN: Maps "read_file" → "safe_read" (reverse)
6. CLIENT: Sees "safe_read" (custom name)
```

**Key Points:**
- Plugin owns the bidirectional mapping
- Routing uses post-plugin-processing names
- Server always gets its expected names

## Error Handling

### Routing Failures

**Missing Server Context:**
```
Error: "No server specified for non-broadcast request"
When: Tool call without namespace in multi-server setup
Resolution: Client must use namespaced tool names
```

**Unknown Server:**
```
Error: "Unknown server: {server_name}"
When: Namespace references non-existent server
Resolution: Check configured servers
```

**Connection Failures:**
```
Error: "Server {server_name} unavailable"
When: Target server not connected
Resolution: Retry or fallback logic
```

### Parse Failures

**Invalid Namespace:**
```
Error: "Invalid namespace format"
When: Multiple __ separators or malformed
Resolution: Validate at boundary
```

## Example Scenarios

### Scenario 1: Simple Tool Call

**Request Flow:**
```
Client: {"method": "tools/call", "params": {"name": "filesystem__read_file", "arguments": {"path": "/tmp/data"}}}
↓ Parse at boundary
Internal: server="filesystem", params={"name": "read_file", "arguments": {"path": "/tmp/data"}}
↓ Plugin processing (may modify params)
↓ Route to filesystem server
Upstream: {"method": "tools/call", "params": {"name": "read_file", "arguments": {"path": "/tmp/data"}}}
```

### Scenario 2: Tool Mutation by Plugin

**Request Flow:**
```
Client: "filesystem__safe_read"
↓ Parse: server="filesystem", tool="safe_read"
↓ Plugin maps: "safe_read" → "read_file"
↓ Route to filesystem
Upstream: "read_file"
```

**Response Flow:**
```
Upstream: "read_file" completed
↓ Plugin maps: "read_file" → "safe_read"
↓ Apply namespace: "filesystem__safe_read"
Client: "filesystem__safe_read" completed
```

### Scenario 3: Aggregated Tools List

**Request Flow:**
```
Client: {"method": "tools/list"}
↓ Identify as broadcast
↓ Send to all servers in parallel
```

**Response Aggregation:**
```
filesystem: ["read_file", "write_file"]
database: ["query", "insert"]
↓ Apply namespaces
["filesystem__read_file", "filesystem__write_file", "database__query", "database__insert"]
↓ Return to client
```

### Scenario 4: Single Server Deployment

**Configuration:** Only one upstream server named "filesystem"

**Behavior:**
- Namespacing is STILL REQUIRED for all non-broadcast requests
- No special handling for single-server setups
- Consistent behavior regardless of upstream count

**Valid Request:**
```
Client: "filesystem__read_file" (namespace required)
↓ Parse at ingress: server="filesystem", tool="read_file"
↓ Route to filesystem server
Upstream: "read_file" (clean)
```

**Invalid Request:**
```
Client: "read_file" (missing namespace)
↓ Parse at ingress
✗ ValueError: Tool 'read_file' is not namespaced
```

## Implementation Notes

### Migration Strategy

1. **Phase 1**: Implement boundary parsing in proxy
2. **Phase 2**: Remove denamespacing from plugin manager
3. **Phase 3**: Update routing to use preserved context
4. **Phase 4**: Add namespace application at egress
5. **Phase 5**: Validate and test all scenarios

### Backward Compatibility

- Single-server configurations continue to work without namespacing
- Existing plugins continue to receive server_name parameter
- No changes to plugin interfaces required

### Performance Considerations

- Single parse operation (vs current triple parsing)
- Reduced string manipulation
- Direct routing without re-extraction
- Parallel broadcast for aggregation

## Summary

### Key Principles

1. **Namespace at boundaries only** - Internal components use clean data
2. **Parse once, preserve context** - No re-extraction from modified content
3. **Explicit routing metadata** - Context travels separately from content
4. **Plugin isolation** - Plugins don't know about routing

### Benefits

- **Simplicity**: Single parse point, clear responsibilities
- **Reliability**: No context loss, no re-extraction failures
- **Flexibility**: Plugins can modify content without breaking routing
- **Performance**: Reduced parsing and string operations
- **Maintainability**: Clear separation of concerns

### Common Patterns

1. **Ingress**: Parse → Process → Route
2. **Egress**: Process → Namespace → Return
3. **Broadcast**: Identify → Fanout → Collect → Namespace → Aggregate
4. **Mutation**: Plugin maps names bidirectionally

---

*This document represents the target architecture for Gatekit routing as of version 0.1.0. Implementation will follow the patterns and principles defined here.*