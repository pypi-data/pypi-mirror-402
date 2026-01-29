# stderr Logging and Windsurf Compatibility

## Problem Statement

Windsurf IDE on Windows appears to terminate MCP server processes that write to stderr. This was discovered during v0.1.0 testing when Gatekit worked correctly with Claude Desktop but failed immediately when launched by Windsurf.

## Root Cause

When Gatekit logged to stderr (the previous default), Windsurf on Windows appeared to interpret this as an error condition and killed the process. The exact mechanism is unclear, but disabling stderr logging resolved the issue. The MCP specification explicitly allows stderr for logging:

> "The server MAY write UTF-8 strings to its standard error (stderr) for logging purposes. Clients MAY capture, forward, or ignore this logging."

Claude Desktop follows the spec correctly (captures stderr to log files). Windsurf on Windows does not appear to handle stderr the same way.

## Decision (v0.1.0)

Changed default logging from `["stderr", "file"]` to `["file"]` only:
- `gatekit/tui/guided_setup/config_generation.py` - `create_default_logging_config()` now returns `handlers=["file"]`
- Documented in `docs/known-issues.md`
- Brief reference in `docs/configuration-specification.md`

## If Windsurf Fixes This

If Windsurf updates their MCP client to properly handle stderr per the spec:

1. Consider reverting default to `["stderr", "file"]` for better developer experience
2. Update `docs/known-issues.md` to note the fix and which Windsurf version
3. Update docstring in `config_generation.py`

However, file-only logging is arguably a safer default regardless, since:
- Some users may have other non-compliant MCP clients
- File logging is more reliable for post-mortem debugging
- stderr can be added back by users who need it

## Related Issues

### Multiple Clients Same Log File

When multiple MCP clients use the same config, logs are interleaved. Workaround is documented in `docs/known-issues.md`. Future options:
- Add PID to default log filename (`gatekit-{pid}.log`)
- Add session ID to log format for filtering
- Structured JSON logging with correlation IDs

## References

- MCP Specification (Transports): https://modelcontextprotocol.io/specification/2025-03-26/basic/transports
- GitHub Issue on stderr ambiguity: https://github.com/modelcontextprotocol/modelcontextprotocol/issues/177
