# Audit Plugin Duplicate Code Refactor

## Problem Statement
The auditing plugins (JSON Lines, CSV, Line/Human Readable) have massive code duplication in their `_format_request_log`, `_format_response_log`, and `_format_notification_log` methods. Each plugin duplicates the same business logic for extracting data from requests/responses/decisions, then only differs in the final formatting step.

Note: The future-work plugins (CEF, OpenTelemetry, Syslog) also have this duplication and should be refactored using the same pattern.

## Current Duplication
Every auditing plugin repeats this same logic:

1. **Plugin info extraction**: `self._extract_plugin_info(decision)`
2. **Allowed status check**: `is_allowed = getattr(decision, 'allowed', True)` with the nonsensical comment "PluginResult (when allowed=None) doesn't have allowed field - treat as allowed"
3. **Event type determination**:
   ```python
   if not is_allowed:
       event_type = "SECURITY_BLOCK"
   elif decision.metadata and decision.metadata.get("filtered_count", 0) > 0:
       event_type = "TOOLS_FILTERED"
   elif decision.modified_content is not None:
       event_type = "REQUEST_MODIFIED"
   else:
       event_type = "REQUEST"
   ```
4. **Tool name extraction**: For `tools/call` requests, extracting `params["name"]`
5. **Timestamp generation**: Each format has its own timestamp format but the underlying data is the same
6. **Request validation**: Checking if `request.method` exists
7. **Metadata extraction**: Getting `filtered_count`, `plugin`, etc. from decision.metadata
8. **Server name handling**: Sanitizing and including server_name

## Proposed Solution

### Step 1: Extract Common Data in Base Class
Add methods to `BaseAuditingPlugin` that extract all common data:

```python
def _extract_common_request_data(self, request: MCPRequest, decision: PluginResult, server_name: str) -> Dict[str, Any]:
    """Extract all common data needed for logging a request."""
    # Check allowed status (with clearer logic)
    is_allowed = decision.allowed is not False  # None or True means proceed
    
    # Determine event type
    if decision.allowed is False:
        event_type = "SECURITY_BLOCK"
    elif decision.metadata and decision.metadata.get("filtered_count", 0) > 0:
        event_type = "TOOLS_FILTERED"  
    elif decision.modified_content is not None:
        event_type = "REQUEST_MODIFIED"
    else:
        event_type = "REQUEST"
    
    # Build common data dictionary
    data = {
        "timestamp": datetime.utcnow(),  # Let formatters decide format
        "event_type": event_type,
        "method": request.method if hasattr(request, 'method') else None,
        "request_id": request.id if hasattr(request, 'id') else None,
        "server_name": server_name,
        "is_allowed": is_allowed,
        "plugin_name": self._extract_plugin_info(decision),
        "reason": decision.reason if decision.reason else "",
        "modified": decision.modified_content is not None,
    }
    
    # Add tool-specific data
    if request.method == "tools/call" and request.params and "name" in request.params:
        data["tool_name"] = request.params["name"]
    
    # Add filtering data
    if decision.metadata:
        data["filtered_count"] = decision.metadata.get("filtered_count", 0)
        data["metadata"] = decision.metadata
    
    return data

def _extract_common_response_data(self, request: MCPRequest, response: MCPResponse, decision: PluginResult, server_name: str) -> Dict[str, Any]:
    """Extract all common data needed for logging a response."""
    # Similar logic for responses
    ...

def _extract_common_notification_data(self, notification: MCPNotification, decision: PluginResult, server_name: str) -> Dict[str, Any]:
    """Extract all common data needed for logging a notification."""
    # Similar logic for notifications
    ...
```

### Step 2: Update Base Class Format Methods
Change the base class methods to use the extraction:

```python
def _format_request_log(self, request: MCPRequest, decision: PluginResult, server_name: str) -> str:
    """Format a request log message."""
    data = self._extract_common_request_data(request, decision, server_name)
    return self._format_log_entry(data, "request")

def _format_response_log(self, request: MCPRequest, response: MCPResponse, decision: PluginResult, server_name: str) -> str:
    """Format a response log message."""
    data = self._extract_common_response_data(request, response, decision, server_name)
    return self._format_log_entry(data, "response")

def _format_notification_log(self, notification: MCPNotification, decision: PluginResult, server_name: str) -> str:
    """Format a notification log message."""
    data = self._extract_common_notification_data(notification, decision, server_name)
    return self._format_log_entry(data, "notification")

def _format_log_entry(self, data: Dict[str, Any], entry_type: str) -> str:
    """Format extracted data into a log entry. Must be implemented by subclasses."""
    raise NotImplementedError(f"Subclass {self.__class__.__name__} must implement _format_log_entry")
```

### Step 3: Simplify Each Plugin
Each plugin now only needs to implement `_format_log_entry`:

```python
# JsonAuditingPlugin
def _format_log_entry(self, data: Dict[str, Any], entry_type: str) -> str:
    """Format data as JSON."""
    # Convert datetime to string
    data["timestamp"] = data["timestamp"].isoformat() + "Z"
    # Remove any non-JSON-serializable items
    return json.dumps(data, default=str)

# CsvAuditingPlugin  
def _format_log_entry(self, data: Dict[str, Any], entry_type: str) -> str:
    """Format data as CSV."""
    # Convert to CSV fields in the right order
    fields = [
        data["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
        data["event_type"],
        data.get("method", ""),
        data.get("tool_name", ""),
        # ... etc
    ]
    return self._format_csv_row(fields)

# LineAuditingPlugin
def _format_log_entry(self, data: Dict[str, Any], entry_type: str) -> str:
    """Format data as human-readable line."""
    timestamp = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S UTC")
    if data["event_type"] == "SECURITY_BLOCK":
        return f"{timestamp} - SECURITY_BLOCK: {data['method']} - [{data['plugin_name']}] {data['reason']}"
    # ... etc
```

## Benefits

1. **Eliminate 200+ lines of duplicated code** across the auditing plugins
2. **Single source of truth** for business logic (event type determination, etc.)
3. **Easier to maintain** - fix bugs or add features in one place
4. **Clearer separation of concerns** - data extraction vs formatting
5. **Fix the nonsensical comment** about "doesn't have allowed field" 
6. **Easier to add new formats** - just implement `_format_log_entry`

## Implementation Steps

1. Add the `_extract_common_*_data` methods to BaseAuditingPlugin
2. Update base class `_format_*_log` methods to use extraction + call `_format_log_entry`
3. Implement `_format_log_entry` in each plugin (JSON Lines, CSV, Line/Human Readable, and future-work: CEF, OpenTelemetry, Syslog)
4. Remove all the duplicated logic from each plugin's `_format_*_log` methods
5. Test thoroughly to ensure output format hasn't changed

## Compatibility Note

This is a pure refactor - the output format of each plugin should remain EXACTLY the same. We're just moving the common logic to the base class.

## Testing Requirements

Since this is a refactor that shouldn't change behavior:
1. Capture current output from all audit plugins for various scenarios
2. After refactor, verify output is identical
3. Ensure all existing tests still pass without modification