# Testing Reorganization

## Goals

1. **Automated Regression Protection** - Strong unit and integration tests that run on every commit via `pytest tests/`
2. **Manual Developer Confidence** - A single checklist-driven process where you see the system work with your own eyes, supported by validation scripts
3. **Clear Organization** - No confusing "acceptance" terminology; tests are either unit, integration, or manual validation support

## Terminology

- **Unit tests** (`tests/unit/`) - Test individual components in isolation
- **Integration tests** (`tests/integration/`) - Test components working together
- **Validation** (`tests/validation/`) - Manual validation support: checklists, scripts, configs, test files

The term "acceptance testing" is retired. Manual validation IS our acceptance testing.

## Implementation Steps

- [x] Rename `tests/validation/test_csv_validation.py` → `validate_csv_output.py`
- [x] Create `tests/validation/manual-validation-guide.md` with full checklist
- [x] Delete `tests/validation/quick-validation-guide.md`
- [x] Delete `docs/testing/acceptance-harness-guide.md`
- [x] Update references to "acceptance" terminology in test comments/docstrings
- [x] Run `pytest tests/` to verify all automated tests pass (2312 tests)
- [x] Update `tests/unit/test_quick_validation_automation.py` to test new guide

**Note**: `docs/todos/acceptance-testing.md` was already in `docs/todos-completed/` - no move needed.

## Manual Validation Guide Content

The new `manual-validation-guide.md` will contain these sections:

### Section 1: Plugin Configuration Persistence

**By Plugin Type:**
- [ ] Security: basic_pii_filter - edit pii_types (nested), action (enum), scan_base64 (boolean)
- [ ] Security: basic_secrets_filter - edit secret_types, entropy settings, allowlist patterns (array)
- [ ] Security: basic_prompt_injection_defense - edit sensitivity (enum), detection_methods (nested)
- [ ] Middleware: tool_manager - edit tools array (add/remove), display_name, display_description
- [ ] Middleware: call_trace - edit trace_id_header (string)
- [ ] Auditing: audit_jsonl - edit output_file (path), include_* booleans, max_body_size (number)
- [ ] Auditing: audit_csv - edit delimiter, column selection
- [ ] Auditing: audit_human_readable - edit format options

**By Scope:**
- [ ] Global plugin config (_global) - changes apply to all servers
- [ ] Per-server plugin config - changes apply to specific server only
- [ ] Server-aware plugin (tool_manager) - must be per-server

**Framework Fields:**
- [ ] Enable/disable plugin via checkbox
- [ ] Change priority (0-100)
- [ ] Verify framework fields persist alongside plugin-specific config

### Section 2: Guided Setup

#### Screen 1: Server Selection & Discovery

**Discovery per MCP Client:**
- [ ] Claude Desktop - discovers servers from JSON config
- [ ] Claude Code - discovers servers (user-level ~/.claude.json + project-level)
- [ ] Codex - discovers servers from TOML config
- [ ] Cursor - discovers servers from JSON config
- [ ] Windsurf - discovers servers from JSON config

**Discovery Edge Cases:**
- [ ] Client not installed (config doesn't exist) - handled gracefully
- [ ] Client installed but no servers - shows in discovery but empty
- [ ] HTTP/SSE servers present - filtered out with warning (stdio only)
- [ ] Same server name in multiple clients - deduplication with suffix
- [ ] Parse errors in client config - non-fatal, shows error

**Server Selection:**
- [ ] Select individual servers (Space toggle)
- [ ] Select All (A) / Select None (N)
- [ ] Config file location - default and custom path
- [ ] Config file exists - auto-increment naming

#### Screen 2: Client Selection

- [ ] All 5 clients shown (detected and undetected)
- [ ] Client already has Gatekit - warning shown
- [ ] Select clients independent of server selection
- [ ] Restore directory - default and custom path

#### Screen 3: Client Setup Instructions

- [ ] Manual-edit clients (Claude Desktop, Cursor, Windsurf) - JSON snippet correct
- [ ] CLI clients (Claude Code, Codex) - shell commands correct
- [ ] Instructions actually work when followed

#### Screen 4: Setup Complete

- [ ] Summary shows selected servers and clients
- [ ] Default plugins listed (Call Trace, JSONL Auditing)
- [ ] Files created listed correctly
- [ ] Generated gatekit.yaml is valid and loadable

#### End-to-End Flows

- [ ] Fresh setup with servers from single client
- [ ] Fresh setup with servers from multiple clients
- [ ] No servers found - modal displays correctly
- [ ] Back navigation preserves selections
- [ ] Cancel aborts without partial config

### Section 3: Gateway Startup & Shutdown

- [ ] Start gateway with valid config - "Gatekit is ready"
- [ ] Graceful shutdown (Ctrl+C) - no errors
- [ ] Invalid config (malformed YAML) - clear error with line number
- [ ] Invalid config (validation error) - clear error with field path
- [ ] Missing plugin handler - error names the missing handler

### Section 4: Security Plugin Behavior

- [ ] PII filter: email redaction works
- [ ] PII filter: phone redaction works
- [ ] PII filter: SSN redaction works
- [ ] PII filter: IP address redaction works
- [ ] Secrets filter: AWS key blocking works
- [ ] Secrets filter: token blocking works
- [ ] Prompt injection: detection and blocking works
- [ ] Blocked request returns proper JSON-RPC error (not silent failure)

### Section 5: Middleware Plugin Behavior

- [ ] Tool manager: tool filtering (allowed list)
- [ ] Tool manager: tool renaming
- [ ] Tool manager: description changes
- [ ] Call trace: trace info appended to responses

### Section 6: Auditing Output

- [ ] Run `./validate_all_formats.sh`
- [ ] JSONL format produces valid JSON Lines
- [ ] CSV format produces valid CSV (parseable by pandas)
- [ ] Human-readable format is readable
- [ ] All formats capture ALLOWED, BLOCKED, MODIFIED events

### Section 7: Multi-Server Support

- [ ] Multiple upstreams in config
- [ ] Per-server plugin config works
- [ ] Requests route to correct server
- [ ] Upstream unavailable - clear error message, no hang

### Section 8: Platform-Specific Validation (Delta)

**Run only on non-primary platforms (Linux, Windows) after macOS validation passes.**

*Process Management:*
- [ ] Gateway starts and stops cleanly (no zombie processes)
- [ ] Upstream server process terminates on gateway shutdown

*Path Handling:*
- [ ] Config file discovered in platform-appropriate location
- [ ] Debug logs written to correct platform directory
- [ ] Audit logs written to configured path

*Guided Setup (if supported on platform):*
- [ ] Client config paths detected correctly
- [ ] Generated migration instructions use correct shell syntax
- [ ] Restore script uses correct shell quoting

## Final Directory Structure

```
tests/
├── unit/                           # Automated unit tests
│   ├── test_golden_configs.py
│   └── tui/
│       └── test_config_adapter.py
├── integration/                    # Automated integration tests
│   ├── test_gateway_harness.py
│   ├── test_tui_round_trip.py
│   ├── test_gateway_cli_smoke.py
│   └── helpers/
├── validation/                     # Manual validation support
│   ├── manual-validation-guide.md  # THE comprehensive checklist
│   ├── validate_all_formats.sh     # Auditing validation script
│   ├── validate_csv_output.py      # CSV output validation (renamed)
│   ├── validation-config.yaml      # Test configs
│   ├── test-files/                 # Test data (clean.txt, secrets.txt, etc.)
│   └── logs/                       # Output directory
├── fixtures/
│   └── golden_configs/             # Shared test fixtures
└── utils/
    ├── golden.py                   # Golden config helpers
    └── textual.py                  # TUI Pilot helpers
```
