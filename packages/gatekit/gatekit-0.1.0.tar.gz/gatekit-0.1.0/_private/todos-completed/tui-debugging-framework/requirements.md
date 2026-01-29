# TUI Debugging Framework Requirements

## Overview

The Gatekit TUI requires a comprehensive debugging framework to enable effective troubleshooting of complex user interactions, focus management, navigation behaviors, and widget state changes. This framework must provide visibility into internal TUI operations without disrupting the user experience.

## Problem Statement

Current debugging challenges:
- **Invisible State Changes**: Focus memory, navigation state, and widget lifecycles happen internally
- **Ephemeral Events**: User interactions and focus changes are transient and hard to capture
- **Complex Navigation Logic**: Custom Tab navigation with focus memory creates intricate state flows
- **Visual-Only Debugging**: Screenshots provide limited insight into underlying widget state
- **Remote Debugging**: Developer cannot directly observe user interactions in real-time

## Core Requirements

### 1. Debug Mode Infrastructure

**REQ-1.1**: TUI must support a `--debug` command line flag that enables comprehensive logging
- Enable via `gatekit --tui --debug` 
- Default to disabled for production use
- No performance impact when disabled
- Graceful degradation if logging fails

**REQ-1.2**: Debug output must be machine-readable structured data (JSON)
- Consistent schema for all event types
- ISO 8601 timestamps for all events
- Unique event IDs for correlation
- Hierarchical context (screen → container → widget)

**REQ-1.3**: Debug log files must be written to predictable locations
- Primary log: `/tmp/gatekit_tui_debug.log`
- State dumps: `/tmp/gatekit_tui_state_YYYYMMDD_HHMMSS.json`
- Auto-rotation when files exceed 10MB
- Cleanup of logs older than 7 days

### 2. Event Logging System

**REQ-2.1**: Focus Events
- Widget focus gained/lost events
- Focus memory storage and retrieval operations
- Focus target resolution (remembered vs fallback)
- Container-to-widget focus mapping

**REQ-2.2**: Navigation Events
- Tab/Shift+Tab key press events
- Container transitions (previous → current → next)
- Navigation index changes

**REQ-2.3**: Widget Lifecycle Events
- Widget creation and destruction
- Widget tree changes (mount/unmount)
- Dynamic content updates (plugin data refresh)
- Container content changes

**REQ-2.4**: User Input Events
- All key press events with context
- Mouse interactions (if enabled)
- Action method invocations
- Event handler execution paths

**REQ-2.5**: State Change Events
- Focus memory dictionary updates
- Current container index changes
- Button index modifications
- Configuration reload events

### 3. State Inspection System

**REQ-3.1**: On-Demand State Dumps
- Hotkey trigger (Ctrl+Shift+D)
- Complete widget hierarchy snapshot
- Focus memory contents
- Navigation state variables
- Current selections and values

**REQ-3.2**: State Dump Contents
```json
{
  "timestamp": "2025-01-15T14:30:45.123Z",
  "session_id": "uuid4-string",
  "screen_type": "ConfigEditorScreen",
  "focused_widget": {
    "id": "checkbox_secrets",
    "class": "ASCIICheckbox",
    "parent_chain": ["GlobalPluginItem", "VerticalScroll", "GlobalSecurityWidget"]
  },
  "navigation_state": {
    "current_container_index": 0,
    "container_names": ["global_security", "global_auditing", ...]
  },
  "focus_memory": {
    "global_security": "checkbox_secrets",
    "global_auditing": "checkbox_csv_auditing",
    "servers_list": "servers_list",
    ...
  },
  "widget_tree": {
    "ConfigEditorScreen": {
      "children": [...],
      "properties": {...}
    }
  }
}
```

**REQ-3.3**: Widget Tree Analysis
- Complete DOM-like structure
- Widget IDs and classes
- Focusability status
- Visibility and mounting state
- Parent-child relationships

### 4. Debugging Tools Integration

**REQ-4.1**: External Tool Support
- Asciinema recording compatibility
- Terminal output capture support
- JSON log parsing utilities
- State diff analysis tools

**REQ-4.2**: Event Replay Capability
- Record all user input events
- Save event sequences to replay files
- Deterministic replay for testing
- Regression test case generation

**REQ-4.3**: Performance Monitoring
- Event processing latency
- Memory usage tracking
- Widget count monitoring
- Focus chain depth analysis

### 5. Developer Experience

**REQ-5.1**: Debug Log Analysis
- Human-readable event summaries
- Chronological event sequences
- State transition visualization
- Error correlation and highlighting

**REQ-5.2**: Common Debugging Workflows
- "Show me what happened when user pressed Tab"
- "Why did focus go to wrong widget?"
- "What was the focus memory state at time T?"
- "Trace navigation path from A to B"

**REQ-5.3**: Documentation and Examples
- Debug mode usage guide
- Common debugging scenarios
- Log interpretation guidelines
- Troubleshooting playbook

## Implementation Architecture

### Debug Logger Component
```python
class TUIDebugLogger:
    def __init__(self, enabled: bool = False, log_path: str = None)
    def log_event(self, event_type: str, widget: Widget, **context)
    def log_focus_change(self, old_widget: Widget, new_widget: Widget)
    def log_navigation(self, direction: str, from_container: str, to_container: str)
    def log_state_change(self, component: str, old_value: Any, new_value: Any)
    def dump_state(self) -> str
    def close(self)
```

### Integration Points
- Screen initialization (`__init__`)
- Focus event handlers (`on_descendant_focus`)
- Navigation actions (`action_navigate_next`, `action_navigate_previous`)
- Focus memory operations (`_track_widget_focus`, `_get_*_target`)
- Configuration updates (`update_plugins_data`)

### Event Schema
```json
{
  "event_id": "uuid4",
  "timestamp": "ISO8601",
  "session_id": "uuid4", 
  "event_type": "focus_change|navigation|state_change|user_input|widget_lifecycle",
  "screen": "ConfigEditorScreen",
  "widget": {
    "id": "string",
    "class": "string", 
    "path": ["parent", "child", "target"]
  },
  "context": {
    "direction": "next|previous",
    "container": "global_security",
    "reason": "user_tab|remembered|fallback"
  },
  "data": {...}
}
```

## Success Criteria

### Functional Requirements
- [ ] Debug mode can be enabled/disabled via command line
- [ ] All focus changes are captured with full context
- [ ] Navigation sequences are traceable end-to-end
- [ ] State dumps provide complete widget hierarchy
- [ ] Log files are created in predictable locations
- [ ] Debug output is structured and parseable

### Performance Requirements  
- [ ] Debug logging adds <10ms latency per event
- [ ] Memory usage increases <50MB with debug enabled
- [ ] Log file rotation prevents disk space issues
- [ ] Debug mode gracefully handles I/O failures

### Usability Requirements
- [ ] Developer can trace user interactions from logs
- [ ] State dumps are human-readable and comprehensive
- [ ] Common debugging questions are answerable from logs
- [ ] Documentation enables effective troubleshooting

## Security and Privacy Considerations

**Data Sensitivity**: Debug logs may contain configuration paths and plugin names
- Sanitize sensitive file paths
- Avoid logging configuration values
- Mask personal identifiers
- Clear documentation of what data is captured

**File Permissions**: Debug files should be readable only by user
- Use restrictive permissions (600)
- Write to user-specific temp directories
- Automatic cleanup of old files

## Future Enhancements

### Phase 2 Features
- Real-time debug dashboard (web interface)
- Remote debugging over network
- Visual state diagrams
- Automated issue detection

### Phase 3 Features
- Integration with testing framework
- Continuous integration debug captures
- Performance regression detection
- User interaction analytics

## Dependencies

### Required
- Python `json` module (built-in)
- Python `datetime` module (built-in) 
- Python `uuid` module (built-in)
- File system write access to `/tmp`

### Optional
- `rich` library for enhanced console output
- `jsonschema` for log validation
- External analysis tools (jq, etc.)

## Timeline

### Week 1: Core Infrastructure
- Debug logger implementation
- Command line flag integration
- Basic event logging

### Week 2: Event Coverage
- Focus event logging
- Navigation event logging
- State change tracking

### Week 3: State Inspection
- State dump implementation
- Widget tree analysis
- Hotkey integration

### Week 4: Polish and Documentation
- Log analysis tools
- Documentation and examples
- Testing and validation

## Acceptance Testing

### Manual Test Cases
1. Enable debug mode and perform common navigation sequences
2. Trigger state dumps at various interaction points
3. Reproduce known bugs and verify log captures root cause
4. Test performance impact with debug mode enabled
5. Validate log file rotation and cleanup

### Automated Test Cases
1. Unit tests for debug logger components
2. Integration tests for event capture
3. Schema validation for log output
4. Performance regression tests
5. File system error handling tests