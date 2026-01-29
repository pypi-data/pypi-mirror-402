# Troubleshooting Guide

*[Home](../../../README.md) → [User Documentation](../../README.md) → [Reference](../README.md) → Troubleshooting*

This guide helps you diagnose and resolve common issues with Gatekit configuration, plugins, and operation.

## Table of Contents

1. [General Troubleshooting Steps](#general-troubleshooting-steps)
2. [Installation Issues](#installation-issues)
3. [Configuration Problems](#configuration-problems)
4. [Plugin Issues](#plugin-issues)
5. [Connection Problems](#connection-problems)
6. [Performance Issues](#performance-issues)
7. [TUI Display Issues](#tui-display-issues)
8. [Logging and Debugging](#logging-and-debugging)
9. [Error Messages](#error-messages)

## General Troubleshooting Steps

Before diving into specific issues, try these general debugging steps:

### 1. Enable Verbose Logging
```bash
gatekit --config your-config.yaml --verbose
```

### 2. Validate Configuration
```bash
gatekit debug config --validate --config your-config.yaml
```

### 3. Check Plugin Loading
```bash
gatekit debug plugins --validate-priorities --config your-config.yaml
```

### 4. Test MCP Server Directly
```bash
# Test your upstream MCP server without Gatekit
npx @modelcontextprotocol/server-filesystem ./your-directory/
```

## Installation Issues

### "Gatekit command not found"

**Symptoms**: Command line shows `gatekit: command not found`

**Causes & Solutions**:

1. **Gatekit not installed**:
   ```bash
   # Install with uv (recommended)
   uv add gatekit
   
   # Or install with pip
   pip install gatekit
   ```

2. **Python PATH issues**:
   ```bash
   # Check if gatekit is in PATH
   which gatekit
   
   # If not found, check Python scripts directory
   python -m site --user-base
   ```

3. **Virtual environment not activated**:
   ```bash
   # If using virtual environment, activate it
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```

### "Command 'uv' not found"

**Symptoms**: `uv: command not found` when trying to install

**Solution**: Install uv package manager:
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Alternative: use pip instead
pip install gatekit
```

### "Command 'npx' not found"

**Symptoms**: `npx: command not found` when starting MCP servers

**Solution**: Install Node.js which includes npx:
1. Visit [nodejs.org](https://nodejs.org/)
2. Download and install Node.js
3. Verify installation: `npx --version`

## Configuration Problems

### "Configuration file not found"

**Symptoms**: `Config file not found: your-config.yaml`

**Solutions**:

1. **Check file path**:
   ```bash
   # Use absolute path
   gatekit --config /full/path/to/your-config.yaml
   
   # Verify file exists
   ls -la your-config.yaml
   ```

2. **Check file permissions**:
   ```bash
   # Ensure file is readable
   chmod 644 your-config.yaml
   ```

### "Invalid YAML syntax"

**Symptoms**: YAML parsing errors on startup

**Solutions**:

1. **Check YAML syntax**:
   ```bash
   # Use online YAML validator or
   python -c "import yaml; yaml.safe_load(open('your-config.yaml'))"
   ```

2. **Common YAML issues**:
   - Inconsistent indentation (use spaces, not tabs)
   - Missing colons after keys
   - Unquoted strings with special characters
   - Missing quotes around file paths with spaces

**Example of corrected YAML**:
```yaml
# Bad
proxy:
transport: stdio    # Missing space after colon
  upstream:
    command: npx @modelcontextprotocol/server-filesystem /path with spaces/  # Unquoted path

# Good
proxy:
  transport: stdio  # Proper spacing
  upstream:
    command: "npx @modelcontextprotocol/server-filesystem '/path with spaces/'"  # Quoted path
```

### "Invalid configuration structure"

**Symptoms**: Validation errors about missing or invalid configuration sections

**Solution**: Ensure your configuration has the required structure:
```yaml
proxy:              # Required section
  transport: stdio  # Required field
  upstream:         # Required section
    command: "your-mcp-server-command"  # Required field

plugins:            # Optional section
  security:         # Optional
    - policy: "plugin_name"
      enabled: true
      config: {}
  auditing:         # Optional
    - policy: "plugin_name"
      enabled: true
      config: {}
```

## Plugin Issues

### "Plugin not loading"

**Symptoms**: Plugin appears in config but doesn't execute

**Debugging steps**:

1. **Check plugin name**:
   ```bash
   gatekit debug plugins --list-available
   ```

2. **Verify plugin is enabled**:
   ```yaml
   plugins:
     security:
       - policy: "tool_allowlist"
         enabled: true  # Must be true
   ```

3. **Check plugin configuration**:
   ```bash
   gatekit debug plugins --validate-config --config your-config.yaml
   ```

### "Plugin priority conflicts"

**Symptoms**: Plugins executing in wrong order

**Solutions**:

1. **Check priority values**:
   ```yaml
   plugins:
     security:
       - policy: "tool_allowlist"
         priority: 10  # Lower number = higher priority
       - policy: "content_access_control"
         priority: 20  # Runs after tool_allowlist
   ```

2. **Validate priorities**:
   ```bash
   gatekit debug plugins --validate-priorities --config your-config.yaml
   ```

### "Tool access control not working"

**Symptoms**: All tools are visible or none are blocked

**Common issues**:

1. **Wrong mode setting**:
   ```yaml
   # Problem: Typo in mode
   config:
     mode: "allowlsit"  # Should be "allowlist"
   
   # Solution: Correct spelling
   config:
     mode: "allowlist"
   ```

2. **Empty tools list**:
   ```yaml
   # Problem: No tools specified in allowlist mode
   config:
     mode: "allowlist"
     tools: []  # Empty list blocks everything
   
   # Solution: Add allowed tools
   config:
     mode: "allowlist"
     tools: ["read_file", "write_file"]
   ```

3. **Case sensitivity**:
   ```yaml
   # Problem: Wrong case
   tools: ["Read_File"]  # Wrong case
   
   # Solution: Correct case
   tools: ["read_file"]  # Correct case
   ```

### "Content access control patterns not matching"

**Symptoms**: Files are blocked or allowed unexpectedly

**Common pattern issues**:

1. **Case sensitivity**: Patterns are case-sensitive
   ```yaml
   # Problem
   resources: ["Public/*"]  # Won't match "public/"
   
   # Solution
   resources: ["public/*"]  # Matches "public/"
   ```

2. **Missing wildcards**:
   ```yaml
   # Problem: Only matches exact directory
   resources: ["docs"]
   
   # Solution: Add wildcards for contents
   resources: ["docs/*"]      # Files in docs/
   resources: ["docs/**/*"]   # Files in docs/ and subdirectories
   ```

3. **Negation order**:
   ```yaml
   # Problem: Negation before positive pattern
   resources:
     - "!sensitive/*"
     - "public/**/*"
   
   # Solution: Positive patterns first
   resources:
     - "public/**/*"
     - "!public/sensitive/*"
   ```

### Plugin Configuration Scope Errors

**Symptoms**: Configuration validation fails with scope-related errors

#### "Plugin has scope 'server_aware' and cannot be configured in _global section"

**Problem**: Attempting to configure server-aware plugins globally.

**Example error**:
```
Plugin 'tool_allowlist' has scope 'server_aware' and cannot be configured 
in the _global section. Server-aware plugins require per-server configuration.
```

**Wrong configuration**:
```yaml
plugins:
  security:
    _global:
      - policy: "tool_allowlist"  # ❌ Server-aware plugins need per-server config
        config:
          tools: ["read_file"]
```

**Correct configuration**:
```yaml
plugins:
  security:
    filesystem:                   # ✅ Configure per-server
      - policy: "tool_allowlist"
        config:
          tools: ["read_file", "write_file"]
    database:                     # ✅ Different config per server
      - policy: "tool_allowlist"
        config:
          tools: ["read_query", "list_tables"]
```

#### "Plugin has scope 'server_specific' and cannot be configured in _global section"

**Problem**: Attempting to configure server-specific plugins globally.

**Example error**:
```
Plugin 'filesystem_server' has scope 'server_specific' and cannot be configured 
in the _global section. Server-specific plugins only work with compatible server types.
```

**Wrong configuration**:
```yaml
plugins:
  security:
    _global:
      - policy: "filesystem_server"  # ❌ Only works with filesystem servers
```

**Correct configuration**:
```yaml
plugins:
  security:
    filesystem:                      # ✅ Only configure for compatible servers
      - policy: "filesystem_server"
        config:
          read: ["docs/**/*"]
          write: ["temp/**/*"]
```

#### "Plugin configuration references unknown upstream"

**Problem**: Plugin configured for a server that doesn't exist in upstreams.

**Example error**:
```
Plugin configuration references unknown upstream 'file_server'. 
Available upstreams: filesystem, database
```

**Wrong configuration**:
```yaml
proxy:
  upstreams:
    - name: "filesystem"           # Server is named "filesystem"
    - name: "database"

plugins:
  security:
    file_server:                   # ❌ "file_server" doesn't exist
      - policy: "pii"
```

**Correct configuration**:
```yaml
plugins:
  security:
    filesystem:                    # ✅ Matches actual server name
      - policy: "pii"
```

#### Plugin Configuration Debugging Steps

1. **Validate configuration structure**:
   ```bash
   gatekit --config your-config.yaml --validate
   ```

2. **Check available plugins and their scopes**:
   ```bash
   gatekit debug plugins --list-available
   ```

3. **Verify server names match**:
   ```bash
   # Check your upstream server names
   grep -A 10 "upstreams:" your-config.yaml
   
   # Check your plugin configurations reference the same names
   grep -A 5 "plugins:" your-config.yaml
   ```

4. **Test with minimal configuration**:
   ```yaml
   # Start with simple global configuration
   plugins:
     security:
       _global:
         - policy: "pii"           # ✅ Global scope plugins work in _global
           enabled: true
           config:
             action: "audit_only"  # Safe: only logs, doesn't block
   ```

5. **Understanding plugin scope categories**:
   
   **Global scope plugins** (can be in `_global`):
   - `pii`, `secrets`, `prompt_injection`
   - All auditing plugins (`json_auditing`, `line_auditing`, etc.)
   
   **Server-aware plugins** (must be per-server):
   - `tool_allowlist` (needs server-specific tool names)
   
   **Server-specific plugins** (only for compatible servers):
   - `filesystem_server` (only for filesystem servers)

#### Quick Configuration Fix Guide

| Error Type | Quick Fix |
|------------|-----------|
| Server-aware plugin in `_global` | Move to individual server sections |
| Server-specific plugin in `_global` | Move to compatible server sections |
| Unknown upstream reference | Check server names match `upstreams` section exactly |
| Invalid plugin scope | Use plugins appropriate for your server types |
| Configuration format error | Ensure proper YAML indentation and structure |

#### Prevention Tips

- **Start simple**: Begin with global-only configuration using global scope plugins
- **Validate early**: Use `--validate` flag when testing new configurations
- **Read error messages**: Validation errors provide specific guidance
- **Check examples**: See working configurations in `configs/tutorials/`
- **Use descriptive server names**: `customer_db_prod` vs `server1`

## Connection Problems

### "Connection refused"

**Symptoms**: Gatekit can't connect to upstream MCP server

**Solutions**:

1. **Test upstream server directly**:
   ```bash
   # Test the MCP server command directly
   npx @modelcontextprotocol/server-filesystem ./your-directory/
   ```

2. **Check command path**:
   ```yaml
   # Ensure command is correct and accessible
   upstream:
     command: "npx @modelcontextprotocol/server-filesystem ./existing-directory/"
   ```

3. **Verify directory exists**:
   ```bash
   # For filesystem server, ensure directory exists
   ls -la ./your-directory/
   mkdir -p ./your-directory/  # Create if missing
   ```

### "Claude Desktop not connecting"

**Symptoms**: Claude Desktop shows connection errors

**Solutions**:

1. **Check Claude Desktop configuration**:
   ```json
   {
     "mcpServers": {
       "gatekit": {
         "command": "gatekit",
         "args": [
           "--config", "/absolute/path/to/config.yaml"
         ]
       }
     }
   }
   ```

2. **Use absolute paths**:
   ```json
   // Problem: Relative path
   "args": ["--config", "config.yaml"]
   
   // Solution: Absolute path
   "args": ["--config", "/Users/username/gatekit/config.yaml"]
   ```

3. **Restart Claude Desktop** after configuration changes

## Performance Issues

### "Slow response times"

**Symptoms**: Operations take longer than expected

**Causes & Solutions**:

1. **Too many plugins**:
   - Reduce number of active plugins
   - Optimize high-priority plugins
   - Use `mode: "critical"` for auditing

2. **Complex content patterns**:
   ```yaml
   # Problem: Complex patterns
   resources:
     - "**/**/deeply/nested/**/*"
   
   # Solution: Simplify patterns
   resources:
     - "public/**/*"
     - "docs/**/*"
   ```

3. **Excessive logging**:
   ```yaml
   # Problem: Verbose logging in production
   config:
     format: "detailed"
     mode: "all"
   
   # Solution: Reduce logging
   config:
     format: "simple"
     mode: "critical"
   ```

### "High memory usage"

**Symptoms**: Gatekit consuming excessive memory

**Solutions**:

1. **Enable log rotation**:
   ```yaml
   config:
     file: "logs/audit.log"
     max_file_size_mb: 10
     backup_count: 5
   ```

2. **Reduce audit buffer size**:
   ```yaml
   config:
     buffer_size: 1000  # Reduce from default
   ```

## TUI Display Issues

### Mac Terminal.app Rendering Problems

**Symptoms**: When using the Gatekit TUI on Mac Terminal.app, you may see:
- Weird glyphs or corrupted characters in Select dropdowns
- Broken or misaligned borders around widgets  
- Strange-looking left side borders on form controls
- Box-drawing characters that don't connect properly

**What's Happening**: These are **not bugs in Gatekit** - they're limitations of Mac Terminal.app's rendering of text-based user interfaces. Terminal.app has known issues with:
- Unicode box-drawing characters used for borders
- Font stitching when combining multiple fonts
- Character width calculations for TUI elements

### Quick Fix: Adjust Terminal.app Font Settings

You can improve the rendering by adjusting Terminal.app's font settings:

1. **Open Terminal.app Preferences**:
   - Terminal menu → Settings (or `Cmd + ,`)

2. **Go to Text tab** in your profile settings

3. **Change font settings**:
   - **Font**: Menlo Regular
   - **Character Spacing**: 1
   - **Line Spacing**: 0.805

4. **Test the changes** by running `gatekit tui` again

**Note**: Even with these settings, some minor rendering artifacts may remain.

### Better Solution: Use a Modern Terminal

For the best Gatekit TUI experience on macOS, consider switching to a modern terminal emulator:

#### Recommended Alternatives:

**iTerm2** (Free):
- Download from [iterm2.com](https://iterm2.com/)
- Better Unicode support and box-drawing character rendering
- Superior color support (24-bit color vs Terminal.app's 256 colors)
- Faster performance with TUI applications

**Other Options**:
- **Warp**: Modern terminal with GPU acceleration
- **Alacritty**: Fast, cross-platform terminal emulator
- **Kitty**: Feature-rich terminal with excellent Unicode support

#### How to Test Different Terminals:

1. **Install alternative terminal** (e.g., iTerm2)
2. **Run Gatekit TUI**:
   ```bash
   gatekit tui --config your-config.yaml
   ```
3. **Compare rendering quality** - you should see:
   - Clean, properly aligned borders
   - No glyphs or corrupted characters in Select widgets
   - Smooth box-drawing character connections

### Why This Happens

Mac Terminal.app was built for basic terminal tasks and hasn't kept up with modern terminal user interface requirements:

- **Limited Unicode support**: Doesn't properly render the full range of box-drawing characters
- **Font mixing issues**: May combine fonts in ways that break character alignment  
- **Legacy architecture**: Based on older terminal standards with limited TUI support

Modern terminal emulators are designed specifically to handle rich text user interfaces, Unicode characters, and complex layouts.

### When to Contact Support

**Don't file a bug report if**:
- You're using Mac Terminal.app and seeing rendering issues
- Select dropdowns show glyphs but are otherwise functional
- Borders look broken but the TUI is still usable

**Do contact us if**:
- Rendering issues persist in modern terminals (iTerm2, etc.)
- The TUI crashes or becomes completely unusable
- You find workarounds that would help other Mac users

## Logging and Debugging

### System Logging Configuration Issues

**Problem: Log file not created**

**Check:**
1. File path is correct in configuration
2. Directory permissions allow file creation  
3. Disk space is available
4. `handlers` includes `"file"`

```yaml
logging:
  handlers: ["file"]           # Must include "file"
  file_path: "logs/system.log" # Must specify path for file handler
```

**Problem: Permission denied error**

Gatekit will fall back to stderr logging if file creation fails. Check:
1. Directory permissions
2. File permissions if file already exists
3. Disk space
4. SELinux/AppArmor policies if applicable

**Problem: Too many log files**

**Solution:** Adjust backup count:
```yaml
logging:
  backup_count: 3  # Keep only 3 backup files (plus current = 4 total)
```

**Problem: Log files too large**

**Solution:** Reduce rotation size:
```yaml
logging:
  max_file_size_mb: 5  # Rotate every 5MB instead of default 10MB
```

**Problem: Not seeing expected messages**

**Check:**
1. Log level is appropriate (`DEBUG` shows everything, `CRITICAL` shows almost nothing)
2. Messages might be below the configured level
3. Use `--verbose` flag to temporarily enable DEBUG logging

### Enable Debug Logging

For detailed troubleshooting information:

```bash
# Enable verbose output
gatekit --config config.yaml --verbose

# Set debug log level
export GATEKIT_LOG_LEVEL=DEBUG
gatekit --config config.yaml
```

### Understanding Log Messages

**Plugin Loading**:
```
[INFO] Loading plugin: tool_allowlist with priority 30
[DEBUG] Plugin tool_allowlist initialized with config: {...}
```

**Request Processing**:
```
[DEBUG] Processing request: tools/list
[DEBUG] Security plugin tool_allowlist: ALLOW
[DEBUG] Security plugin content_access_control: ALLOW
[INFO] Request processed successfully
```

**Security Blocks**:
```
[WARNING] Tool blocked by allowlist: delete_file not in ['read_file', 'write_file']
[INFO] Request denied by security policy
```

### Log File Analysis

```bash
# Find security blocks
grep "SECURITY_BLOCK\|blocked" logs/audit.log

# Monitor in real-time
tail -f logs/audit.log | grep -E "(ERROR|WARNING|BLOCK)"

# Count tool usage
grep "TOOL_CALL" logs/audit.log | cut -d'-' -f4 | sort | uniq -c

# Find performance issues
grep "DURATION" logs/audit.log | awk '{print $NF}' | sort -n
```

## Error Messages

### Common Error Messages and Solutions

**"Plugin priority must be between 0 and 100"**
- Check priority values in plugin configuration
- Ensure priority is an integer, not a string

**"Tool not found in allowlist"**
- Add the tool to your allowlist configuration
- Check tool name spelling and case

**"Resource blocked by pattern"**
- Review your content access control patterns
- Use debug mode to see pattern matching details

**"YAML parsing failed"**
- Check YAML syntax and indentation
- Ensure colons have spaces after them
- Quote strings with special characters

**"Upstream server connection failed"**
- Verify upstream server command is correct
- Test upstream server independently
- Check file paths and permissions

## Getting Help

If you're still experiencing issues:

1. **Check the logs** with verbose mode enabled
2. **Review this troubleshooting guide** for similar issues
3. **Test components individually** (plugins, upstream server, etc.)
4. **Simplify your configuration** to isolate the problem
5. **Check the [Configuration Reference](configuration-reference.md)** for correct syntax
6. **File an issue** on the Gatekit GitHub repository with:
   - Your configuration file (remove sensitive information)
   - Complete error messages
   - Steps to reproduce the issue
   - Output from `gatekit --config config.yaml --verbose`
