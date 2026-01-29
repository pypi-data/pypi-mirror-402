# TUI Debug Framework Testing Guide

This guide provides comprehensive testing scenarios to verify the TUI debugging framework works correctly.

## 🧪 Automated Tests

### Unit Tests
```bash
# Run all debug framework tests
pytest tests/unit/test_tui_debug_framework.py -v

# Run CLI integration tests  
pytest tests/unit/test_tui_invocation.py -v
pytest tests/unit/test_main_cli.py -v

# Run full test suite
pytest tests/
```

### Manual Integration Tests
```bash
# Run comprehensive manual tests
python test_debug_manual.py
```

## 🖥️ Interactive TUI Testing

### Basic Debug Mode Testing

1. **Start TUI with debug enabled:**
   ```bash
   gatekit --debug
   ```

2. **Check debug log location:**
   ```bash
   # Debug logs are written to platform-specific log directories:
   # - macOS: ~/Library/Logs/gatekit/gatekit_tui_debug.log
   # - Linux: ~/.local/state/gatekit/gatekit_tui_debug.log
   # - Windows: %LOCALAPPDATA%\gatekit\logs\gatekit_tui_debug.log

   # Monitor debug log in real-time (macOS example)
   tail -f ~/Library/Logs/gatekit/gatekit_tui_debug.log
   ```

3. **Verify session start logging:**
   - Debug log should immediately show session_start event
   - Should contain session_id, timestamp, and log path

### Navigation Testing

**Test Scenario:** Focus and navigation logging

1. **Start TUI with debug:**
   ```bash
   gatekit --debug docs/validation/validation-config.yaml
   ```

2. **Navigate through interface:**
   - Press `Tab` to move between containers
   - Press `Shift+Tab` to move backwards  
   - Use arrow keys within containers
   - Navigate to different plugin sections

3. **Expected debug events:**
   - `user_input` events for each Tab/Shift+Tab press
   - `navigation` events showing container transitions
   - `focus_change` events for widget focus changes
   - `state_change` events for focus memory updates

### State Dump Testing

**Test Scenario:** Manual state inspection

1. **Navigate to complex screen state:**
   - Open config editor
   - Navigate through several plugin containers
   - Focus on different widgets

2. **Trigger state dump:**
   - Press `Ctrl+Shift+D` 
   - Should work from any screen

3. **Verify state dump file:**
   ```bash
   # Check for state dump files (macOS example)
   ls ~/Library/Logs/gatekit/gatekit_tui_state_*.json

   # View state dump content
   cat ~/Library/Logs/gatekit/gatekit_tui_state_*.json | jq .
   ```

4. **Expected state dump content:**
   - Current screen type
   - Focused widget information  
   - Navigation state (container indices)
   - Focus memory contents
   - Widget tree structure

### Configuration Loading Testing

**Test Scenario:** Widget lifecycle and configuration events

1. **Start with various configs:**
   ```bash
   # Test with different config files
   gatekit --debug docs/validation/validation-config.yaml
   gatekit --debug nonexistent.yaml
   gatekit --debug  # No config
   ```

2. **Expected debug events:**
   - `widget_lifecycle` events for screen mounting
   - `widget_lifecycle` events for plugin data population
   - Configuration loading context in events

### Error Handling Testing

**Test Scenario:** Graceful degradation

1. **Test with restricted permissions:**
   ```bash
   # Run with restricted temp access (if possible)
   # Should gracefully disable debug logging
   ```

2. **Test with invalid config:**
   ```bash
   gatekit --debug /nonexistent/path.yaml
   ```

3. **Expected behavior:**
   - No crashes or exceptions
   - Graceful fallback to disabled state
   - Normal TUI operation continues

## 📊 Debug Log Analysis

### Log Structure Verification

**Check event structure:**
```bash
# Parse and analyze debug logs (macOS example)
cat ~/Library/Logs/gatekit/gatekit_tui_debug.log | jq '
{
  event_type: .event_type,
  timestamp: .timestamp,
  session_id: .session_id,
  has_widget: (.widget != null),
  has_context: (.context != null)
}'
```

**Event sequence analysis:**
```bash
# Show event sequence (macOS example)
cat ~/Library/Logs/gatekit/gatekit_tui_debug.log | jq -r '
"\(.timestamp) - \(.event_type) - \(.context.key // .context.direction // .context.component // "")"
'
```

### Common Event Patterns

**Expected sequence for Tab navigation:**
1. `user_input` - key="tab", action="navigate_next"
2. `navigation` - direction="next", from_container="X", to_container="Y"  
3. `focus_change` - old_widget → new_widget
4. `state_change` - component="focus_memory", old/new values
5. `state_change` - component="container_index", old/new indices

**Expected sequence for screen mounting:**
1. `session_start` - Initial session creation
2. `widget_lifecycle` - lifecycle_event="mount", screen context
3. `widget_lifecycle` - lifecycle_event="update", component="global_plugins"

## 🔍 Performance Testing

### Debug Overhead Testing

**Test impact of debug mode:**
```bash
# Compare startup time
time gatekit --help
time gatekit --debug --help

# Monitor memory usage
# (No specific commands - observe system resources)
```

### Log File Growth Testing

**Test log rotation:**
```bash
# Check initial log size (macOS example)
ls -la ~/Library/Logs/gatekit/gatekit_tui_debug.log

# Use TUI extensively, then check size growth
# Log should rotate at 10MB
```

## 🚨 Common Issues & Troubleshooting

### Issue: No debug log file created
**Symptoms:** TUI starts but no log file appears
**Diagnosis:**
```bash
# Check log directory exists and is writable (macOS example)
ls -la ~/Library/Logs/gatekit/

# Test manual logger creation
python -c "
from gatekit.tui.debug import TUIDebugLogger
logger = TUIDebugLogger(enabled=True)
print(f'Enabled: {logger.enabled}')
print(f'Log path: {logger.log_path}')
logger.close()
"
```

### Issue: State dumps not created
**Symptoms:** Ctrl+Shift+D doesn't create state files
**Diagnosis:**
- Check if TUI debug mode is enabled (`--debug` flag)
- Verify hotkey binding works in current screen
- Check log directory for files with pattern `gatekit_tui_state_*.json`

### Issue: Malformed JSON in logs
**Symptoms:** Log parsing fails with JSON errors
**Diagnosis:**
```bash
# Check log file for JSON validity (macOS example)
cat ~/Library/Logs/gatekit/gatekit_tui_debug.log | jq empty
# Should show no output if all JSON is valid

# Check for truncated lines (interrupted logging)
cat ~/Library/Logs/gatekit/gatekit_tui_debug.log | tail -10
```

## ✅ Success Criteria

A successful test run should demonstrate:

1. **✅ Core Functionality**
   - Debug logs created in system temp directory
   - JSON-structured events with required fields
   - Session management (start/end events)

2. **✅ Event Coverage**
   - Focus change events during navigation
   - User input events for key presses
   - Navigation events with container transitions
   - State change events for focus memory updates
   - Widget lifecycle events during screen loading

3. **✅ State Inspection**
   - Ctrl+Shift+D creates state dump files
   - State dumps contain complete widget hierarchy
   - Navigation and focus state captured accurately
   - Focus memory contents preserved correctly

4. **✅ Error Resilience**
   - Graceful degradation on file system errors
   - No crashes or exceptions during normal operation
   - TUI functionality unimpacted by debug failures

5. **✅ Performance**
   - No noticeable impact on TUI responsiveness
   - Log file rotation prevents disk space issues
   - Clean session termination and file cleanup

## 📝 Test Results Template

```
# TUI Debug Framework Test Results

**Date:** 
**Platform:** macOS/Linux/Windows
**Python Version:** 
**Gatekit Version:** 

## Automated Tests
- [ ] Unit tests pass: `pytest tests/unit/test_tui_debug_framework.py -v`
- [ ] CLI integration tests pass
- [ ] Manual integration tests pass: `python test_debug_manual.py`

## Interactive TUI Tests
- [ ] Debug mode starts successfully: `gatekit --debug`
- [ ] Debug log file created in temp directory
- [ ] Navigation events logged correctly
- [ ] Focus change events captured
- [ ] State dumps work with Ctrl+Shift+D
- [ ] State dump files contain expected data

## Error Handling Tests
- [ ] Invalid config paths handled gracefully
- [ ] File permission errors don't crash TUI
- [ ] Debug logging failures don't impact TUI operation

## Performance Tests
- [ ] No noticeable TUI performance impact
- [ ] Log files rotate properly at 10MB
- [ ] Old debug files cleaned up (7+ days)

**Notes:**
- Temp directory used: 
- Sample debug log events verified: 
- State dump files inspected:
- Any issues encountered:
```

This testing guide provides comprehensive verification that the TUI debugging framework works correctly across different scenarios and edge cases.