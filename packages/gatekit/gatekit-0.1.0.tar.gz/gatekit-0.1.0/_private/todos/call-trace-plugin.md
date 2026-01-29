# Call Trace Plugin

## Overview

A middleware plugin that appends trace information to tool responses, demonstrating Gatekit's middleware capabilities while providing immediate value to users. This plugin showcases what middleware can do: intercepting responses, extracting metadata, tracking state, and modifying content.

**Default behavior**: Enabled by default in guided-setup-generated configs to ensure users see immediate value and understand plugin capabilities.

## Plugin Metadata

- **Handler**: `call_trace`
- **Display Name**: "Call Trace"
- **Type**: Middleware plugin
- **Priority**: 90 (runs after other middleware)
- **Critical**: False (fail-open - never break requests)

## Purpose

1. **Immediate value**: Show users what Gatekit is doing with their requests
2. **Educational**: Demonstrate middleware plugin capabilities (interception, state tracking, content modification)
3. **Practical utility**:
   - Multi-server routing visibility
   - Request correlation via request ID
   - Performance visibility via duration
   - Easy link to audit logs for deeper investigation

## Functionality

### What It Does

Appends a "Gatekit Gateway Trace" section to tool responses showing:

- **Server**: Which upstream server handled the request
- **Tool**: Tool name (extracted from `tools/call`)
- **Params**: Request parameters (with truncation for long values)
- **Response**: Response size in human-readable format (B, KB, MB, GB)
- **Duration**: Time from request to response in milliseconds
- **Request ID**: JSON-RPC request ID
- **Timestamp**: ISO 8601 timestamp
- **Audit log guidance**: Instructions for finding full audit trail

### Output Format

```markdown
---
🔍 **Gatekit Gateway Trace**
- Server: filesystem
- Tool: read_file
- Params: {"path": "/home/user/projects/gatekit/config/loader.py"}
- Response: 2.3 KB
- Duration: 45ms
- Request ID: 1
- Timestamp: 2025-01-12T15:30:45Z

Search your audit logs near timestamp 2025-01-12T15:30:45Z (request_id: 1) to see the audit trail for this request.
To find audit log locations, open your Gatekit config using `gatekit <path_to_config.yaml>`
---
```

### Error Case

**Note**: Trace is NOT added to error responses. Error responses use `response.error` (not `response.result`), and per JSON-RPC 2.0 spec, `result` and `error` are mutually exclusive. The trace is only appended to successful responses with `response.result.content[]`.

## Implementation Requirements

### File Location
`gatekit/plugins/middleware/call_trace.py`

### Class Structure

```python
class CallTracePlugin(MiddlewarePlugin):
    DISPLAY_NAME = "Call Trace"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._request_times: Dict[Union[str, int], float] = {}  # request_id -> start_time

    async def process_request(self, request: MCPRequest, server_name: str) -> PluginResult:
        # Store request start time for duration calculation
        if request.id is not None:
            self._request_times[request.id] = time.time()
        return PluginResult()

    async def process_response(self, request: MCPRequest, response: MCPResponse, server_name: str) -> PluginResult:
        # Pop request time immediately (ensures cleanup for all paths)
        start_time = self._request_times.pop(request.id, None) if request.id is not None else None

        # Skip non-traced requests (errors, non-tools/call methods)
        # Use start_time to calculate duration, format trace, append to response
        pass

    async def process_notification(self, notification: MCPNotification, server_name: str) -> PluginResult:
        # Pass through unchanged
        pass
```

### Key Implementation Details

#### 1. Timing Tracking
- Store `request_id -> start_time` mapping in `process_request`
- **Pop request time immediately at start of `process_response`** - this ensures cleanup happens for all code paths (traced requests, skipped requests, errors, exceptions)
- Pass popped `start_time` to `_calculate_duration(start_time)` which computes: `duration_ms = int((time.time() - start_time) * 1000)`
- Handle missing request times gracefully (show "N/A" for duration when `start_time` is `None`)

#### 2. Response Size Formatting
```python
def _format_size(self, size_bytes: int) -> str:
    """Format bytes into human-readable size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"
```

#### 3. Parameter Handling
- Extract `arguments` from request params
- Serialize to JSON string
- Truncate if longer than configurable limit (default: 200 chars)
- Example: `{"path": "/very/long/path/that/goes..."}`

#### 4. Method Scope
- Only handle `tools/call` responses
- Pass through all other methods unchanged

#### 5. Response Content Modification
- **Only modify successful responses** (responses with `response.result`, not `response.error`)
- Add new text content block to `response.result.content[]` array per MCP spec
- MCP `tools/call` successful responses have required structure: `{"result": {"content": [array of content blocks]}}`
- Append trace as: `{"type": "text", "text": "---\n🔍 **Gatekit Gateway Trace**\n..."}`
- Works for all response types (text, image, etc.) - trace is always a separate text block
- **Skip error responses entirely** - they use `response.error` which is mutually exclusive with `response.result` per JSON-RPC 2.0
- Outer try/except in `process_response` provides fail-open behavior - any exception logs warning and returns pass-through

#### 6. Error Handling
- Error responses (response.error exists): Pass through unchanged - do NOT add trace
- Missing request ID: Show "N/A"
- Missing duration data: Show "N/A"
- Any exception during processing: Log error, return unmodified response (fail-open)

### Configuration

```yaml
middleware:
  - handler: call_trace
    enabled: true
    priority: 90
    config:
      max_param_length: 200  # Max chars for params display
```

### Handler Registration

```python
# In gatekit/plugins/middleware/call_trace.py
HANDLERS = {
    "call_trace": CallTracePlugin
}
```

## Testing Requirements

### Unit Tests
`tests/unit/plugins/middleware/test_call_trace.py`

Test cases:
1. **Basic trace appending** - Verify trace is added to successful response
2. **Duration calculation** - Verify timing is accurate
3. **Size formatting** - Test B, KB, MB, GB formatting
4. **Parameter truncation** - Test long params are truncated
5. **Missing data handling** - Request without ID, missing duration
6. **Error responses** - Verify trace is NOT added to error responses (pass through unchanged)
7. **Multiple methods** - tools/call handled, others passed through
8. **Configuration** - Respect enabled, priority, config options
9. **Fail-open behavior** - Errors don't break requests
10. **Request time cleanup** - Completed requests cleaned immediately after use

## Documentation Requirements

### Plugin Source Code Documentation
Add comprehensive module and class docstrings to the plugin source code explaining:
- Purpose and value proposition
- What middleware plugins can do (this is a reference implementation)
- Configuration options
- How to customize/extend
- Output format examples

Users may examine the plugin source code to learn how to build their own plugins, so it should be heavily commented and educational.

Example module docstring:
```python
"""Call Trace middleware plugin for Gatekit.

This plugin appends diagnostic trace information to tool responses, demonstrating
Gatekit's middleware capabilities while providing immediate value to users.

Purpose:
    - Show users what Gatekit is doing with their requests
    - Demonstrate middleware plugin capabilities
    - Provide request correlation for audit log lookup
    - Show multi-server routing visibility

Middleware Capabilities Demonstrated:
    - Intercepting requests and responses
    - Tracking state across request/response cycle
    - Modifying response content
    - Extracting and formatting metadata

This plugin is enabled by default in guided-setup configs to showcase Gatekit's
capabilities. Users can disable it or use it as a starting point for custom plugins.

Configuration:
    enabled: bool - Enable/disable plugin (default: true)
    priority: int - Execution order, 0-100 (default: 90, runs after other middleware)
    max_param_length: int - Max characters for parameter display (default: 200)
"""
```

### User Guidance
Guided setup completion screen emphasizes automatic plugins with a single info box:

```
✅ Configuration Complete

┌─ Default Plugins Enabled ────────────────────┐
│ These plugins help you understand what your  │
│ MCP servers and clients are doing:           │
│                                               │
│ • Call Trace - Appends diagnostic info to    │
│   tool responses showing which server handled │
│   the call, timing, and parameters           │
│                                               │
│ • JSONL Auditing - Logs MCP messages to      │
│   logs/gatekit_audit.jsonl for debugging   │
└────────────────────────────────────────────────┘

Files Created:
  Gatekit Config: /path/... [Open]
  Restore Scripts: /path/... [Open]

Servers Configured:
  • filesystem

Clients Configured:
  • Claude Desktop
```

**UX Rationale:** Only the plugins get an info box because they're automatically enabled without explicit user choice. Files, servers, and clients are plain text confirmations since the user already encountered them in previous steps.

## Guided Setup Integration

### Default Configuration
- **Always enabled** in guided-setup-generated configs
- Priority 90 (after other middleware)
- Default config with `max_param_length: 200`

## Resolved Questions

1. ✅ **Response structure**: Add trace as a separate text content block to handle all response types (text, image, etc.)
2. ✅ **Content detection**: Always show trace, even for binary-only responses (Option A)
3. ✅ **LLM visibility**: No practical security concern - we're reporting data the LLM already has access to
4. ✅ **State cleanup**: Pop request time at start of process_response - ensures cleanup for all paths (traced, skipped, errors)
5. ✅ **Format flexibility**: Fixed verbose format - can add options later if users request

## Implementation Checklist

- [x] Create plugin file: `gatekit/plugins/middleware/call_trace.py`
- [x] Implement `CallTracePlugin` class with timing tracking
- [x] Implement response size formatting
- [x] Implement parameter truncation
- [x] Handle error responses
- [x] Register handler
- [x] Write unit tests (25 test cases covering all functionality)
- [x] Update guided setup to include plugin
- [x] Document in plugin docs
- [x] Run full test suite: `pytest tests/ -n auto`
- [x] Run linting: `uv run ruff check gatekit`

## Success Criteria

1. ✅ Plugin appends trace to tool responses without breaking functionality
2. ✅ Timing is accurate (±5ms tolerance)
3. ✅ All tests pass
4. ✅ Fail-open: Errors never break requests
5. ✅ Default enabled in guided setup
6. ✅ Clear, helpful output that demonstrates middleware capabilities
7. ✅ Users can easily find audit logs using the information provided
