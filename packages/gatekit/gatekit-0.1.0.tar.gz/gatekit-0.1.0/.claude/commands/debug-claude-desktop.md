---
description: "Debug Claude Desktop issues with Gatekit"
---

# Claude Desktop + Gatekit Debugging

Debug an issue with Claude Desktop when using Gatekit as MCP gateway.

## Step 1: Identify Active Configuration

Read Claude Desktop's MCP config to find which Gatekit config is in use:
- **Claude Desktop config**: `/Users/dbright/Library/Application Support/Claude/claude_desktop_config.json`

Look for the Gatekit entry (likely named "gatekit" or similar) and note the `--config` path argument.

## Step 2: Read Log Files

### Claude Desktop Logs
- **mcp.log**: `~/Library/Logs/Claude/mcp.log` - Contains MCP protocol-level communication and errors

### Gatekit Logs (derive paths from the config identified in Step 1)
- **System log**: Check `proxy.logging.file_path` in the Gatekit YAML config
- **TUI debug log**: `~/Library/Logs/gatekit/gatekit_tui_debug.log` (only exists if TUI was run with `--debug`)
- **Auditing logs**: Check each plugin under `proxy.plugins.auditing` for `output_file` paths - these contain detailed request/response logs

## Step 3: Analyze the Issue

$ARGUMENTS

## Troubleshooting Checklist
- Look for JSON-RPC errors or connection failures in mcp.log
- Check Gatekit system log for startup errors, plugin loading issues, or upstream connection failures
- Review auditing logs for blocked requests, security plugin denials, or transformation errors
- Verify all config paths resolve correctly (relative paths are resolved from the config file's directory)
- Check that upstream server commands and arguments in the config are correct
