# Auditing Format Improvement Requirements

## Overview

The auditing plugins need updating to properly reflect the ProcessingPipeline model introduced in phase8. Current formats lose important information by mapping the rich 5-state pipeline outcomes back to a binary ALLOWED/BLOCKED model, which is particularly problematic for compliance and security auditing.

## Problem Statement

### Current Issues

1. **Lost Pipeline Outcomes**: The CSV plugin uses binary `ALLOWED`/`BLOCKED` status, losing the distinction between:
   - `ALLOWED` (security evaluated and passed)
   - `NO_SECURITY_EVALUATION` (no security plugins ran)
   - `COMPLETED_BY_MIDDLEWARE` (middleware handled the request)
   - `ERROR` (critical plugin error)

2. **Missing Security Context**: Formats don't expose whether security plugins actually evaluated the request. A request with `NO_SECURITY_EVALUATION` appears identical to `ALLOWED`.

3. **Ambiguous Plugin Attribution**: When multiple plugins process a message, it's unclear which plugin made the key decision.

4. **Missing Pipeline Details**: No visibility into:
   - Which plugins ran
   - Processing times per stage
   - Which plugin blocked (if any)
   - Which middleware completed the request (if any)

## Requirements

### 1. CSV Format Updates

#### 1.1 Column Changes

**Remove:**
- `status` column (currently shows misleading ALLOWED/BLOCKED)

**Add New Columns:**
- `pipeline_outcome`: Enum value (ALLOWED, BLOCKED, NO_SECURITY, COMPLETED_BY_MIDDLEWARE, ERROR)
- `security_evaluated`: Boolean true/false
- `decision_plugin`: Name of plugin that determined the final outcome
- `decision_type`: Type of decision (block, response_provided, modified, passed, error)
- `total_plugins_run`: Number of plugins that processed the message
- `plugins_run`: Pipe-separated list of plugin names

**Reorder Columns:**
```
timestamp, event_type, request_id, server_name, method, tool, 
pipeline_outcome, security_evaluated, decision_plugin, decision_type,
total_plugins_run, plugins_run, reason, duration_ms
```

Note: `request_id` moves after `event_type` for logical grouping.

#### 1.2 Decision Attribution Logic

The `decision_plugin` should be set based on this priority:
1. If blocked → the blocking plugin
2. If middleware-completed → the middleware that provided the response
3. If modified → the last modifying plugin
4. Otherwise → the last plugin that ran

The `decision_type` clarifies what the decision_plugin did:
- `block` - Security plugin blocked the request
- `response_provided` - Middleware provided complete response
- `modified` - Content was modified
- `passed` - Normal processing
- `error` - Plugin encountered an error

#### 1.3 Example CSV Output

```csv
timestamp,event_type,request_id,server_name,method,tool,pipeline_outcome,security_evaluated,decision_plugin,decision_type,total_plugins_run,plugins_run,reason,duration_ms
2025-01-15T10:00:00Z,REQUEST,123,filesystem,tools/call,read_file,ALLOWED,true,SecretsFilter,passed,3,ToolAllowlist|PIIFilter|SecretsFilter,[ToolAllowlist] Tool in allowlist | [PIIFilter] No PII detected | [SecretsFilter] No secrets detected,15
2025-01-15T10:00:01Z,REQUEST,124,filesystem,tools/call,write_file,BLOCKED,true,ToolAllowlist,block,1,ToolAllowlist,[ToolAllowlist] Tool not in allowlist,2
2025-01-15T10:00:02Z,REQUEST,125,filesystem,tools/call,read_file,COMPLETED_BY_MIDDLEWARE,true,CacheMiddleware,response_provided,2,ToolAllowlist|CacheMiddleware,[ToolAllowlist] Tool in allowlist | [CacheMiddleware] Served from cache,5
2025-01-15T10:00:03Z,REQUEST,126,filesystem,tools/call,read_file,NO_SECURITY,false,LoggingMiddleware,passed,1,LoggingMiddleware,[LoggingMiddleware] Request logged,3
2025-01-15T10:00:04Z,REQUEST,127,filesystem,tools/call,read_file,ERROR,true,CustomPlugin,error,2,ToolAllowlist|CustomPlugin,[ToolAllowlist] Tool in allowlist | [CustomPlugin] Database connection failed,8
```

### 2. Human Readable Format Updates

#### 2.1 LineAuditingPlugin (Simple Format)

**Current Format:**
```
2025-01-15 10:00:00 UTC - REQUEST: tools/call - read_file - ALLOWED - filesystem
```

**New Format:**
```
2025-01-15 10:00:00 UTC - REQUEST: tools/call - read_file - filesystem - ALLOWED
2025-01-15 10:00:00 UTC - REQUEST: tools/call - read_file - filesystem - NO_SECURITY
2025-01-15 10:00:00 UTC - REQUEST: tools/call - read_file - filesystem - MIDDLEWARE_RESPONSE [CacheMiddleware]
2025-01-15 10:00:00 UTC - REQUEST: tools/call - read_file - filesystem - BLOCKED [ToolAllowlist]
2025-01-15 10:00:00 UTC - REQUEST: tools/call - read_file - filesystem - ERROR [CustomPlugin]
```

**Key Changes:**
- Server name comes after request details (more logical flow)
- Pipeline outcome clearly shown
- Plugin attribution in brackets for BLOCKED, MIDDLEWARE_RESPONSE, and ERROR
- NO request_id (keeping it simple)
- No redundant "(security: yes)" - ALLOWED implies security was evaluated

#### 2.2 DebugAuditingPlugin (Detailed Format)

**New Format:**
```
2025-01-15 10:00:00 UTC - REQUEST [req-123]: tools/call - read_file - filesystem - ALLOWED - 3 plugins - 15ms
2025-01-15 10:00:00 UTC - REQUEST [req-124]: tools/call - write_file - filesystem - BLOCKED [ToolAllowlist] - 2ms
2025-01-15 10:00:00 UTC - REQUEST [req-125]: tools/call - read_file - filesystem - MIDDLEWARE_RESPONSE [CacheMiddleware] - 2 plugins - 5ms
```

**Key Changes:**
- Include request_id in brackets after event type
- Show plugin count
- Include timing information
- Plugin attribution for significant outcomes

### 3. JSON Lines Format Updates

#### 3.1 Structure Changes

**New JSON Structure:**
```json
{
  "timestamp": "2025-01-15T10:00:00Z",
  "event_type": "REQUEST",
  "request_id": "123",
  "server_name": "filesystem",
  "method": "tools/call",
  "tool": "read_file",
  "pipeline_outcome": "ALLOWED",
  "security_evaluated": true,
  "pipeline": {
    "stages": [
      {
        "plugin": "ToolAllowlist",
        "outcome": "passed",
        "reason": "Tool in allowlist",
        "time_ms": 0.5
      },
      {
        "plugin": "PIIFilter",
        "outcome": "modified",
        "reason": "PII redacted",
        "time_ms": 2.1,
        "modified": true
      },
      {
        "plugin": "SecretsFilter",
        "outcome": "passed",
        "reason": "No secrets detected",
        "time_ms": 1.4,
        "decision": true
      }
    ],
    "total_time_ms": 15,
    "decision_plugin": "SecretsFilter",
    "decision_type": "passed"
  },
  "reason": "[ToolAllowlist] Tool in allowlist | [PIIFilter] PII redacted | [SecretsFilter] No secrets detected"
}
```

**Key Changes:**
- Proper nested `pipeline` object containing stages array
- Each stage is an object with its details
- The decision-making stage has `"decision": true` marker
- Stage that modified content has `"modified": true` marker
- Clean JSON structure that's queryable
- Include request_id for all events

#### 3.2 Blocked Request Example

```json
{
  "timestamp": "2025-01-15T10:00:01Z",
  "event_type": "REQUEST",
  "request_id": "124",
  "server_name": "filesystem",
  "method": "tools/call",
  "tool": "write_file",
  "pipeline_outcome": "BLOCKED",
  "security_evaluated": true,
  "pipeline": {
    "stages": [
      {
        "plugin": "ToolAllowlist",
        "outcome": "blocked",
        "reason": "Tool not in allowlist",
        "time_ms": 2.0,
        "decision": true
      }
    ],
    "total_time_ms": 2,
    "decision_plugin": "ToolAllowlist",
    "decision_type": "block"
  },
  "reason": "[ToolAllowlist] Tool not in allowlist"
}
```

#### 3.3 Middleware-Completed Request Example

```json
{
  "timestamp": "2025-01-15T10:00:02Z",
  "event_type": "REQUEST",
  "request_id": "125",
  "server_name": "filesystem",
  "method": "tools/call",
  "tool": "read_file",
  "pipeline_outcome": "COMPLETED_BY_MIDDLEWARE",
  "security_evaluated": true,
  "pipeline": {
    "stages": [
      {
        "plugin": "ToolAllowlist",
        "outcome": "passed",
        "reason": "Tool in allowlist",
        "time_ms": 0.3
      },
      {
        "plugin": "CacheMiddleware",
        "outcome": "completed",
        "reason": "Served from cache",
        "time_ms": 0.5,
        "decision": true,
        "response_provided": true
      }
    ],
    "total_time_ms": 5,
    "decision_plugin": "CacheMiddleware",
    "decision_type": "response_provided"
  },
  "reason": "[ToolAllowlist] Tool in allowlist | [CacheMiddleware] Served from cache"
}
```

## Implementation Notes

### Backward Compatibility

Since Gatekit is v0.1.0 with no backward compatibility requirements (per phase8 documentation), we can make these changes without worrying about existing log parsers. This is the optimal time to fix the formats before they become entrenched.

### Code Locations to Update

1. **`gatekit/plugins/auditing/base.py`**:
   - Update `_extract_common_request_data()` to include new fields
   - Update `_extract_common_response_data()` to include new fields
   - Ensure pipeline stage information is available

2. **`gatekit/plugins/auditing/csv.py`**:
   - Update column definitions and ordering
   - Modify `_format_request_entry()`, `_format_response_entry()`, `_format_notification_entry()`
   - Remove status determination logic, use pipeline_outcome directly
   - Add new column extraction logic

3. **`gatekit/plugins/auditing/human_readable.py`**:
   - Update `LineAuditingPlugin` format strings
   - Update `DebugAuditingPlugin` to include request_id and additional details
   - Adjust field ordering (server after request)

4. **`gatekit/plugins/auditing/json_lines.py`**:
   - Restructure JSON output to include nested pipeline object
   - Add stage details array
   - Include decision markers

### Testing Requirements

1. **Unit Tests**: Update tests for each auditing plugin to verify new format
2. **Integration Tests**: Verify complete pipeline scenarios produce correct audit logs
3. **Validation Tests**: Ensure CSV can be parsed, JSON is valid, human-readable is consistent

## Success Criteria

1. **Compliance**: Auditors can determine if security was actually evaluated
2. **Troubleshooting**: Ops teams can identify which plugin caused issues
3. **Performance**: Per-stage timing data is available for optimization
4. **Correctness**: NO_SECURITY_EVALUATION is clearly distinguished from ALLOWED
5. **Clarity**: No ambiguous field names or confusing terminology

## Priority

1. **Critical**: Fix CSV status column to show actual pipeline outcome
2. **Critical**: Add security_evaluated to all formats
3. **Important**: Add request_id to appropriate formats
4. **Important**: Include pipeline stage details in JSON format
5. **Nice-to-have**: Full stage details in debug format

## Notes

- The most critical fix is ensuring that `NO_SECURITY_EVALUATION` is distinguishable from `ALLOWED` in all formats
- Pipeline stage information should be available but not overwhelming in simpler formats
- The concatenated reason string (per ADR-023) remains unchanged
- All changes should maintain the principle of "one row/line per pipeline result"