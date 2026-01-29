# Gatekit Manual Validation Guide

**Philosophy**: "See it once" + automation. Manual validation exists for:
1. Things that can't be automated (TUI visual behavior, client integration)
2. Seeing real behavior with your own eyes once, then trusting pytest

**After completing each section once**, you can trust pytest for regression protection.

**Workflow**: TUI first, then gateway. Gateway tests use configs created by the TUI to ensure the full user workflow is validated.

---

## Prerequisites

Before starting, ensure:

```bash
# Gatekit is installed and tests pass
cd /path/to/gatekit
pytest tests/ -n auto  # All tests must pass
uv run ruff check gatekit  # No linting errors

# Verify test files exist
ls tests/validation/test-files/
# Should show: clean.txt, personal-info.txt, secrets.txt, prompt-injection.txt, etc.
```

### Platform Paths Reference

| Platform | Gatekit Path | TUI Debug Log |
|----------|----------------|---------------|
| macOS    | `/Users/dbright/mcp/gatekit` | `~/Library/Logs/gatekit/` |
| Linux    | `/home/dbright/mcp/gatekit` | `~/.local/state/gatekit/` |
| Windows  | `C:\Users\dbright\mcp\gatekit` | `%LOCALAPPDATA%\gatekit\logs\` |

---

## Part 1: TUI Config Editor (~45 min)

**Goal**: Verify the TUI correctly loads, edits, and saves plugin configurations.

### Setup

```bash
# Start TUI with debug logging
gatekit --debug

# Open the seed config file
# File > Open > tests/validation/manual-validation-config.yaml
```

### 1.1 Load Seed Config and Create Working Copy

1. Open `tests/validation/manual-validation-config.yaml` in the TUI
2. **Immediately Save As** `tests/validation/tui-test-config.yaml` (Ctrl+Shift+S or File > Save As)
   - This preserves the seed config and creates a working copy for testing

**Verify**:
- [ ] Config loads without errors
- [ ] Upstream server "filesystem" appears in server list
- [ ] Global security plugins visible (PII filter, secrets filter, prompt injection)
- [ ] Global auditing plugins visible (JSONL, CSV, human readable)
- [ ] Per-server middleware plugins visible for "filesystem" (tool manager, call trace)

### 1.2 Security Plugin Configuration

For each security plugin, perform an edit cycle:

**PII Filter (`basic_pii_filter`)**:
1. Navigate to plugin configuration
2. Change `action` from `redact` to `block`
3. Disable one PII type (e.g., `email: false`)
4. Save configuration (Ctrl+S)
5. Close and reopen `tui-test-config.yaml`
6. Verify:
   - [ ] `action` is still `block`
   - [ ] Disabled PII type is still disabled
   - [ ] Other settings preserved

**Secrets Filter (`basic_secrets_filter`)**:
1. Edit entropy threshold (e.g., 4.5 → 5.0)
2. Toggle a secret type (e.g., disable `jwt_tokens`)
3. Toggle base64 detection (e.g., disable `scan_base64`)
4. Save and reload
   - [ ] Entropy threshold preserved
   - [ ] Secret type toggle state preserved
   - [ ] Base64 detection toggle preserved

> **Note**: Custom patterns and allowlist are supported in the gateway and raw config files,
> but the TUI does not yet support editing these fields. To test these features, edit the
> config file directly.

**Prompt Injection (`basic_prompt_injection_defense`)**:
1. Change sensitivity (standard → strict)
2. Disable one detection method
3. Add a custom pattern
4. Save and reload
   - [ ] Sensitivity preserved
   - [ ] Detection method state preserved
   - [ ] Custom pattern preserved

### 1.3 Middleware Plugin Configuration

**Call Trace (`call_trace`)**:
1. Toggle include options
2. Change max content length
3. Save and reload
   - [ ] Toggle states preserved
   - [ ] Max content length preserved
   
**Tool Manager (`tool_manager`)**:
1. Add a tool to the allowlist
2. Remove a tool from the allowlist
3. Save and reload
   - [ ] Tool list preserved correctly

### 1.4 Auditing Plugin Configuration

**JSONL Auditing (`audit_jsonl`)**:
1. Change output path
2. Toggle body inclusion options (request/response/notification)
3. Change max body size
4. Save and reload
   - [ ] Output path preserved
   - [ ] Body inclusion settings preserved
   - [ ] Max body size preserved

**CSV Auditing (`audit_csv`)**:
1. Change output path
2. Change CSV format options (delimiter, quote style)
3. Save and reload
   - [ ] Output path preserved
   - [ ] CSV format options preserved

**Human Readable Auditing (`audit_human_readable`)**:
1. Change output path
2. Save and reload
   - [ ] Output path preserved

### 1.5 Framework Fields

For security or middleware plugins (not auditing - auditing plugins don't have priority):
1. Change priority (e.g., 50 → 25)
2. Toggle enabled state
3. Save and reload
   - [ ] Priority preserved
   - [ ] Enabled state preserved
   - [ ] Plugin-specific config still intact

### 1.6 Prepare Config for Gateway Testing

After completing the TUI tests, prepare the config for Part 3:

1. Re-open the seed config: `tests/validation/manual-validation-config.yaml`
2. Save As: `tests/validation/gateway-test-config.yaml`
3. Verify the saved file is valid YAML:
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('tests/validation/gateway-test-config.yaml')); print('Valid YAML')"
   ```
   Expected output: `Valid YAML` (any other output indicates an error)

This gives you a clean TUI-generated config for gateway testing, separate from your `tui-test-config.yaml` working copy.

---

## Part 2: TUI Guided Setup (~30 min)

**Goal**: Verify the guided setup wizard works with actual MCP client configurations.

### Setup

First, reset all MCP clients to the known baseline state:

**macOS:**
```bash
cd /Users/dbright/mcp/gatekit
./tests/validation/reset-mcp-clients.sh
```

**Linux (including SSH sessions):**
```bash
cd /path/to/gatekit
./tests/validation/reset-mcp-clients-linux.sh
```

> **Linux Note:** The Linux script creates mock configs for Claude Desktop, Cursor, and Windsurf
> (these GUI apps don't run on Linux / read configs from SSH servers). These mock configs allow
> you to test TUI detection and instruction generation, but E2E validation is only possible for
> Claude Code and Codex. See Part 6 for full platform delta testing.

Expected output (macOS):
```
==========================================
  MCP Client Reset Script
  For Gatekit Manual Validation
==========================================

This script will reset all 5 MCP clients to a known baseline state:
  - Claude Desktop: domain-names server
  - Claude Code: context7 server
  - Codex: (no servers)
  - Cursor: puppeteer server
  - Windsurf: sequential-thinking server

WARNING: This will overwrite your current MCP configurations!
Backups will be saved to: /Users/dbright/mcp/gatekit/tests/validation/backups
Continue? (y/N) y

--- Creating backups ---
  Backed up: /Users/dbright/Library/Application Support/Claude/claude_desktop_config.json
  Backed up: /Users/dbright/.claude.json
  ...

--- Resetting Claude Desktop ---
  Done: Set to domain-names server

--- Resetting Claude Code ---
  Done: Reset ~/.claude.json to context7 only

--- Resetting Codex ---
  Done: Removed all MCP servers from config.toml
  (or: No Codex config found (OK - baseline is zero servers))

--- Resetting Cursor ---
  Done: Set to puppeteer server

--- Resetting Windsurf ---
  Done: Set to sequential-thinking server

==========================================
  Reset Complete
==========================================
```

Then start the TUI:

```bash
gatekit --debug
# Select "Guided Setup" from the main menu
```

### 2.1 Server Selection Screen

After selecting "Guided Setup", you should see the server selection screen.

**Title:** "Select MCP Servers to Manage"

**Expected: 4 servers in table format**

| Server | Used By | Command/Transport |
|--------|---------|-------------------|
| `domain-names` | Claude Desktop | `/Users/dbright/mcp/domain_names/.venv/bin/python ...` |
| `context7` | Claude Code | `npx -y @upstash/context7-mcp` |
| `puppeteer` | Cursor | `npx -y @modelcontextprotocol/server-puppeteer` |
| `sequential-thinking` | Windsurf | `npx -y @modelcontextprotocol/server-sequential-thinking` |

**Test these interactions:**
1. Press `Space` on a server → toggles `[X]` / `[ ]`
2. Press `A` → all 4 servers selected `[X]`
3. Press `N` → all 4 servers deselected `[ ]`
4. Select only `domain-names` and `context7` for the remaining tests

**Checklist:**
- [ ] Exactly 4 servers shown (Codex has none, so not listed)
- [ ] Three columns: Server, Used By, Command/Transport
- [ ] Space toggles selection
- [ ] A selects all, N deselects all
- [ ] No "Gatekit already configured" warnings

### 2.2 Client Selection Screen

Press Enter to proceed to client selection.

**Expected: All 5 clients shown**

```
[ ] Claude Desktop
[ ] Claude Code
[ ] Codex
[ ] Cursor
[ ] Windsurf
```

Select `Claude Desktop` and `Claude Code` for testing.

This screen also shows restore scripts location

**Checklist:**
- [ ] All 5 clients shown regardless of whether they had servers
- [ ] Can select clients independently of server selection
- [ ] No "already configured" warnings
- [ ] Output path shown (defaults to current directory)

Press Enter/Continue to generate the configuration files.

### 2.3 Client Setup Screen

After generating files, the wizard shows the **MCP Client Setup Instructions** screen.

This screen has:
- Left panel: List of selected clients (Claude Desktop, Claude Code)
- Right panel: Setup instructions for the highlighted client

**Now check the instructions shown in the TUI:**

**Claude Desktop** (click in left panel to select):

The right panel shows:
1. Config path: `~/Library/Application Support/Claude/claude_desktop_config.json`
2. "Open in Editor" and "Copy Path" buttons
3. Label: "Replace your entire config file with:"
4. A complete JSON config

**Expected JSON structure:**
```json
{
  "mcpServers": {
    "gatekit": {
      "command": "/Users/dbright/mcp/gatekit/.venv/bin/gatekit-gateway",
      "args": ["--config", "/Users/dbright/mcp/gatekit/gatekit.yaml"]
    }
  }
}
```

**Claude Code** (click in left panel to select):

The right panel shows:
1. Label: "Run these commands in your terminal:"
2. A multi-line bash script with line continuations

**Expected command structure:**
```bash
echo 'Removing original servers...'
claude mcp remove context7 --scope user

echo 'Adding Gatekit...'
claude mcp add --transport stdio --scope user gatekit \
  -- \
  /Users/dbright/mcp/gatekit/.venv/bin/gatekit-gateway \
  --config /Users/dbright/mcp/gatekit/configs/gatekit.yaml
```

Note:
- Echo statements provide progress feedback
- Remove commands appear for each migrated server (e.g., `context7`)
- Full paths are used for `gatekit-gateway` and the config file
- Paths are only quoted if they contain spaces or special characters
- `--env` flags appear if migrated servers had environment variables

**Checklist:**
- [ ] Left panel lists: Claude Desktop, Claude Code
- [ ] Claude Desktop: Shows "Replace your entire config file with:"
- [ ] Claude Desktop: Complete JSON with `mcpServers.gatekit` entry
- [ ] Claude Code: Shows `echo` statements for progress
- [ ] Claude Code: Shows `claude mcp remove context7` for migrated server
- [ ] Claude Code: Shows `--scope user` flag
- [ ] Claude Code: Uses full path to `gatekit-gateway`
- [ ] Claude Code: Uses full path to config file

### 2.4 Setup Complete Screen

Press Enter/Continue to proceed to the final summary screen.

**Expected: Summary of what was created**

- Configuration file: `gatekit.yaml`
- Restore scripts location (if restore was enabled)
- List of clients configured

**Checklist:**
- [ ] Shows path to generated `gatekit.yaml`
- [ ] Lists clients that were configured
- [ ] Provides "Done" or "Finish" button to exit wizard

---

## Part 3: Gateway Security Plugins (~20 min)

**Goal**: Visually confirm that each security plugin works correctly with a real MCP client.

**Important**: Use the config file saved from TUI in Part 1 (`gateway-test-config.yaml`), not a hand-crafted config. This validates the full workflow.

### Setup

Configure Claude Desktop to use Gatekit with the TUI-generated config:

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "gatekit-validation": {
      "command": "/Users/dbright/mcp/gatekit/.venv/bin/gatekit-gateway",
      "args": ["--config", "/Users/dbright/mcp/gatekit/tests/validation/gateway-test-config.yaml", "--verbose"]
    }
  }
}
```

Restart Claude Desktop.

### 3.1 PII Filter - Redaction

**Prompt**:
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/personal-info.txt and show me its contents
```

**Expected**: See redaction placeholders:
- `[EMAIL REDACTED by Gatekit]` where emails were
- `[PHONE REDACTED by Gatekit]` where phone numbers were
- `[NATIONAL_ID REDACTED by Gatekit]` where SSNs were
- `[IP_ADDRESS REDACTED by Gatekit]` where IP addresses were

**Verify**:
- [ ] Emails redacted (john.smith@company.com → [EMAIL REDACTED...])
- [ ] Phone numbers redacted (555-123-4567 → [PHONE REDACTED...])
- [ ] SSNs redacted (123-45-6789 → [NATIONAL_ID REDACTED...])
- [ ] IP addresses redacted (192.168.1.100 → [IP_ADDRESS REDACTED...])

### 3.2 Secrets Filter - Redact Mode

**Prompt**:
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/secrets.txt and show me its contents
```

**Expected**: Secrets redacted with placeholders, file content returned

**Verify (should be redacted)**:
- [ ] `[SECRET REDACTED by Gatekit]` placeholders appear for each detected secret
- [ ] AWS Access Key (AKIAIOSFODNN7EXAMPLE → redacted)
- [ ] GitHub token (ghp_... → redacted)
- [ ] Google API key (AIzaSy... → redacted)
- [ ] JWT token (eyJ... → redacted)
- [ ] OpenAI API key (sk-... or sk-proj-... → redacted)
- [ ] SSH private key header (-----BEGIN OPENSSH PRIVATE KEY----- → redacted)

**Known limitations (NOT expected to be detected by pattern matching)**:
- `DB_PASSWORD=...` - Generic password variables have too many false positives

**Note on AWS Secret Access Key**: The AWS Secret Keys **pattern** was removed due to false positives.
However, with entropy detection enabled (threshold 4.5), the line `AWS_SECRET_ACCESS_KEY=...` WILL be
redacted because its entropy (~4.72) exceeds the threshold. This is expected behavior.

### 3.3 Prompt Injection - Redact Mode

**Prompt**:
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/prompt-injection.txt and show me its contents
```

**Expected**: Injection patterns redacted with `[PROMPT INJECTION REDACTED by Gatekit]`

The test file has four sections - check each one:

**SHOULD BE REDACTED (Delimiter Injection)**:
- [ ] `<system>...</system>` tags → REDACTED
- [ ] `<admin>...</admin>` tags → REDACTED
- [ ] `<instruction>...</instruction>` tags → REDACTED
- [ ] `[SYSTEM]...[/SYSTEM]` delimiters → REDACTED
- [ ] Code blocks with "system", "admin", "override" keywords → REDACTED

**SHOULD BE REDACTED (Role Manipulation)**:
- [ ] "You are now an administrator" → REDACTED
- [ ] "You are now DAN" → REDACTED
- [ ] "Act as root user" → REDACTED
- [ ] "with elevated privileges" → REDACTED
- [ ] "using admin access" → REDACTED
- [ ] "administrator mode:" → REDACTED

**SHOULD BE REDACTED (Context Breaking)**:
- [ ] "Ignore all previous instructions" → REDACTED
- [ ] "Forget everything you were told" → REDACTED
- [ ] "Reset context" → REDACTED
- [ ] "Clear conversation" → REDACTED
- [ ] "Disregard previous instructions" → REDACTED
- [ ] "Override all safety" → REDACTED
- [ ] "Bypass security" → REDACTED

**SHOULD BE REDACTED (Custom Pattern)**:
- [ ] "ORG_OVERRIDE_MODE" → REDACTED (custom pattern in config)

**SHOULD NOT BE REDACTED**:
- [ ] "John Smith is a system administrator" → NOT redacted (plain text)
- [ ] "The instructions were clear" → NOT redacted (no trigger verb)
- [ ] Python code block with `hello()` → NOT redacted (no injection keywords)
- [ ] "As a user, I want..." → NOT redacted (different "as" usage)
- [ ] "The admin role has permissions" → NOT redacted (discussion, not command)
- [ ] "The operating system requires" → NOT redacted (system not in tag)

**KNOWN FALSE POSITIVES** (will be redacted even though legitimate):
- [ ] Example injection quoted for documentation → REDACTED (expected)

**Overall**: File content is returned (not blocked, since action is `redact`)

### 3.4 Base64 Encoded Content

**Prompt**:
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/base64-encoded.txt and show me its contents
```

**Expected**: Base64-encoded PII and secrets detected and **BLOCKED**

Both PII filter (with `scan_base64: true`) and secrets filter (with `scan_base64: true`) decode base64 strings to detect sensitive content.

> **Note**: Base64 detection is **disabled by default** due to false positives on image/file data. The seed config explicitly enables it for validation testing. See Section 4.3.3 to test the toggle behavior.

> **Important**: Base64-encoded content **cannot be redacted** - any modification corrupts the underlying binary data. When `scan_base64: true` and sensitive data is detected with `action: redact`, the plugin will force **BLOCK** instead. With `action: audit_only`, detections are logged but content passes through. See ADR-025.

The test file has clear sections. With the seed config (`action: redact`), base64 detections will **BLOCK**:

**WILL CAUSE BLOCK (Base64-Encoded PII)**:
- [ ] `am9obi5zbWl0aEBjb21wYW55LmNvbQ==` (email) → BLOCKED
- [ ] `MTIzLTQ1LTY3ODk=` (SSN) → BLOCKED
- [ ] `KDU1NSkgMTIzLTQ1Njc=` (phone) → BLOCKED
- [ ] `NDUzMiAwMTUxIDEyODMgMDM2Ng==` (credit card) → BLOCKED
- [ ] Inline base64 in sentence → BLOCKED

**WILL CAUSE BLOCK (Base64-Encoded Secrets)**:
- [ ] `QUtJQUlPU0ZPRE5ON0VYQU1QTEU=` (AWS key) → BLOCKED
- [ ] GitHub token base64 → BLOCKED
- [ ] OpenAI key base64 → BLOCKED

**WILL NOT CAUSE BLOCK (Known Limitations)**:
- [ ] Data URL (`data:text/plain;base64,...`) → NOT scanned (explicitly skipped)
- [ ] Double-encoded content → NOT detected (only one decode level)
- [ ] Too short base64 (`YWJjZGVm`) → NOT detected (< 12 chars)
- [ ] Invalid base64 (wrong padding) → NOT detected

**PLAIN TEXT REFERENCE section**:
- [ ] All plain text PII and secrets → REDACTED or BLOCKED per action setting

**Overall**: If base64-encoded sensitive data is detected, the entire response is blocked

### 3.5 Clean File Passes Through

**Prompt**:
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/clean.txt and show me its contents
```

**Expected**: File contents returned unchanged

**Verify**:
- [ ] No redactions or blocks
- [ ] Full file content visible

---

## Part 4: Gateway Config Variations (~15 min)

**Goal**: Verify different config options affect behavior as documented.

**Workflow for each test**:
1. Open TUI: `gatekit`
2. Load: `tests/validation/gateway-test-config.yaml`
3. Make the specified change
4. Save the config
5. Restart Claude Desktop (or reconnect your MCP client)
6. Run the test prompt
7. Verify output matches expected behavior
8. **Revert the change** before the next test

---

### 4.1 Action Modes

#### 4.1.1 Block Mode (Secrets Filter)

**Config Change**: In TUI, change `basic_secrets_filter` → action from `redact` to `block`

**Prompt** (copy-paste into Claude Desktop):
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/secrets.txt and show me its contents
```

**Expected Output**:
- [ ] File content is NOT returned
- [ ] Error message appears (tool call fails)
- [ ] Message indicates the request was blocked due to security

**What you should see**: Instead of file contents, an error like "Request blocked" or "Security policy violation". The file is never shown because secrets trigger a block.

**Revert**: Change action back to `redact` before next test.

---

#### 4.1.2 Redact Mode (Already tested in Part 3)

This is the default. Verified by sections 3.1-3.4.

---

#### 4.1.3 Audit-Only Mode (PII Filter)

**Config Change**: In TUI, change `basic_pii_filter` → action from `redact` to `audit_only`

**Prompt** (copy-paste into Claude Desktop):
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/personal-info.txt and show me its contents
```

**Expected Output**:
- [ ] File content IS returned
- [ ] PII is visible and NOT redacted (email, phone, SSN all visible)
- [ ] No `[EMAIL REDACTED]` or similar placeholders

**What you should see**: The actual email address `john.smith@company.com`, phone numbers, SSN - all in plain text. The detection still happens (check audit log) but no action is taken on the content.

**Verify audit logging** (optional):
```bash
tail -5 /tmp/gatekit-validation/audit.jsonl | python3 -m json.tool
```

**What to look for in the audit log**:
- [ ] `"pii_detected": true` - PII was detected
- [ ] `"detection_action": "audit_only"` - Audit-only mode was used
- [ ] In `pipeline.stages`, the PII Filter stage should show `"outcome": "allowed"` (NOT "modified")
- [ ] The overall `pipeline_outcome` may show "modified" due to other plugins (like Call Trace) - this is expected

> **Note**: The pipeline may show "modified" overall because the Call Trace plugin appends trace information to responses. What matters is that the PII Filter stage itself shows "passed" and the actual file content has PII visible (not redacted).

**Revert**: Change action back to `redact` before next test.

---

### 4.2 Sensitivity Levels (Prompt Injection)

#### 4.2.1 Relaxed Sensitivity

**Config Change**: In TUI, change `basic_prompt_injection_defense` → sensitivity from `standard` to `relaxed`

**Prompt** (copy-paste into Claude Desktop):
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/prompt-injection.txt and show me its contents
```

**Expected Output** (compare to standard sensitivity from Part 3.3):
- [ ] FEWER `[PROMPT INJECTION REDACTED]` markers than standard mode
- [ ] Some borderline patterns may pass through unredacted
- [ ] Most aggressive patterns still redacted (e.g., `<system>` tags)

**What you should see**: More content visible than in standard mode. The relaxed mode only catches the most obvious injection attempts.

**Revert**: Change sensitivity back to `standard` before next test.

---

#### 4.2.2 Strict Sensitivity

**Config Change**: In TUI, change `basic_prompt_injection_defense` → sensitivity from `standard` to `strict`

**Prompt** (copy-paste into Claude Desktop):
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/prompt-injection.txt and show me its contents
```

**Expected Output** (compare to standard sensitivity from Part 3.3):
- [ ] MORE `[PROMPT INJECTION REDACTED]` markers than standard mode
- [ ] Additional patterns detected that weren't caught in standard
- [ ] May see redaction in "SHOULD NOT BE REDACTED" section (false positives expected)

**What you should see**: More redaction than standard mode. Strict mode may redact legitimate content that looks suspicious.

**Revert**: Change sensitivity back to `standard` before next test.

---

### 4.3 Entropy Thresholds (Secrets)

Entropy detection catches high-randomness strings that might be secrets even without known patterns.

**How it works**: Strings are flagged when their entropy ≥ threshold. Lower threshold = more aggressive (catches more). Higher threshold = more conservative (catches fewer).

**Test strings in secrets.txt**:
- `ENTROPY_LOW=...` has entropy ~3.9 → only caught at threshold ≤ 3.9
- `ENTROPY_MED=...` has entropy ~4.7 → caught at threshold ≤ 4.7
- `ENTROPY_HIGH=...` has entropy ~5.4 → caught at any standard threshold

#### 4.3.1 Low Entropy Threshold (More Aggressive)

**Config Change**: In TUI, change `basic_secrets_filter` → entropy_detection → threshold from `4.5` to `4.0`

**Prompt** (copy-paste into Claude Desktop):
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/secrets.txt and show me its contents
```

**Expected Output**:
- [ ] `ENTROPY_MED=...` line is REDACTED (entropy 4.7 ≥ threshold 4.0)
- [ ] `ENTROPY_HIGH=...` line is REDACTED (entropy 5.4 ≥ threshold 4.0)
- [ ] `ENTROPY_LOW=...` line is NOT redacted (entropy 3.9 < threshold 4.0)
- [ ] Pattern-based detections unchanged (AWS keys, GitHub tokens, etc.)

**What you should see**: The threshold 4.0 catches strings with entropy ≥ 4.0. Since ENTROPY_LOW has entropy ~3.9, it's still below the threshold and passes through. To catch it, you'd need threshold 3.9 or lower (not recommended due to false positives).

**Revert**: Change threshold back to `4.5` before next test.

---

#### 4.3.2 High Entropy Threshold (More Conservative)

**Config Change**: In TUI, change `basic_secrets_filter` → entropy_detection → threshold from `4.5` to `5.0`

**Prompt** (copy-paste into Claude Desktop):
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/secrets.txt and show me its contents
```

**Expected Output**:
- [ ] `ENTROPY_HIGH=...` line is REDACTED (entropy 5.4 ≥ threshold 5.0)
- [ ] `ENTROPY_MED=...` line is NOT redacted (entropy 4.7 < threshold 5.0)
- [ ] `ENTROPY_LOW=...` line is NOT redacted (entropy 3.9 < threshold 5.0)
- [ ] Pattern-based detections still work (AWS keys, GitHub tokens, etc.)

**What you should see**: Pattern-matched secrets (AKIA..., ghp_..., sk-...) are still redacted because they match known patterns. Only very high-entropy strings (≥ 5.0) are caught by entropy detection.

**Revert**: Change threshold back to `4.5` before next test.

---

#### 4.3.3 Base64 Detection Toggle

Base64 detection decodes base64-encoded strings and scans their contents for secrets.

**How it works**: When enabled, strings that look like base64 are decoded, and the decoded content is scanned for secret patterns. Disabled by default due to false positives on images and file data.

**Test A: Verify Base64 Detection is Enabled (seed config)**

The seed config has `scan_base64: true`. Verify it works:

**Prompt** (copy-paste into Claude Desktop):
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/base64-encoded.txt and show me its contents
```

**Expected Output**:
- [ ] Request is **BLOCKED** because base64-encoded secrets were detected
- [ ] Error message indicates base64 content detection

> **Note**: Base64-encoded content cannot be redacted without corrupting binary data, so detection always results in blocking. See ADR-025.

**Test B: Disable Base64 Detection**

**Config Change**: In TUI, change `basic_secrets_filter` → `scan_base64` from `true` to `false`

**Prompt** (same as above):
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/base64-encoded.txt and show me its contents
```

**Expected Output**:
- [ ] Base64-encoded secrets are **NOT** detected (raw base64 strings visible, request succeeds)
- [ ] Plain-text secrets in the same file are still handled (pattern matching still works)
- [ ] PII base64 detection still works (controlled by PII filter's `scan_base64`, not this setting)

**What you should see**: The base64 strings like `QUtJQUlPU0ZPRE5ON0VYQU1QTEU=` pass through undetected because the secrets filter no longer decodes them. Plain-text secrets like `AKIAIOSFODNN7EXAMPLE` are still caught and handled per action setting.

**Why this matters**: Base64 detection causes false positives on legitimate binary data (images, PDFs). Disabling it allows file content to pass through without spurious blocking while still catching plain-text secrets.

**Revert**: Change `scan_base64` back to `true` before next test.

---

### 4.4 Plugin Enable/Disable

#### 4.4.1 Disable PII Filter

**Config Change**: In TUI, change `basic_pii_filter` → enabled from `true` to `false`

**Prompt** (copy-paste into Claude Desktop):
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/personal-info.txt and show me its contents
```

**Expected Output**:
- [ ] All PII visible (emails, phones, SSN, credit cards)
- [ ] No `[EMAIL REDACTED]` or similar placeholders
- [ ] Secrets filter still works if you test secrets.txt

**What you should see**: The PII filter is completely bypassed. All personal information is shown in plain text.

**Revert**: Change enabled back to `true` before next test.

---

### 4.5 Auditing Configuration Options

#### 4.5.1 Body Inclusion Toggles (JSONL)

**Config Changes**: In TUI, change `audit_jsonl`:
- `include_request_body` from `false` to `true`
- `include_response_body` from `false` to `true`

**Prompt** (copy-paste into Claude Desktop):
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/clean.txt and show me its contents
```

**Check the audit log**:
```bash
tail -5 /tmp/gatekit-validation/audit.jsonl | python3 -m json.tool --indent 2
```

**Expected Output (Request)**:
- [ ] Entry exists for the `tools/call` request
- [ ] `request_body` field is present and contains the request parameters
- [ ] Shows the tool name and file path that was requested

**Expected Output (Response)**:
- [ ] Entry exists for the `tools/call` response
- [ ] `response_body` field is present and contains the file contents
- [ ] Shows the actual text from `clean.txt`

**What you should see**: Both the request parameters (tool name, file path) AND the response content (file contents) are logged. With the defaults (`false`), only metadata is logged without the actual bodies.

**Revert**: Change both `include_request_body` and `include_response_body` back to `false` before next test.

---

#### 4.5.2 Body Size Truncation (JSONL)

**Config Changes** (two changes required):
1. In TUI, change `audit_jsonl` → `include_response_body` from `false` to `true`
2. In TUI, change `audit_jsonl` → `max_body_size` from `10240` to `100`

**Prompt** (copy-paste into Claude Desktop):
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/clean.txt and show me its contents
```

**Check the audit log**:
```bash
tail -5 /tmp/gatekit-validation/audit.jsonl | python3 -m json.tool --indent 2
```

**Expected Output**:
- [ ] `response_body` field is present (because `include_response_body: true`)
- [ ] `response_body` field is truncated
- [ ] Truncation indicator present (e.g., `"...[truncated]"` or body ends at ~100 chars)
- [ ] Large file content is NOT fully logged

**What you should see**: The response body should be cut off at approximately 100 characters. This prevents audit logs from growing excessively large when tools return large content.

**Revert**: Change `include_response_body` back to `false` and `max_body_size` back to `10240` before next test.

---

#### 4.5.3 CSV Delimiter Option

**Config Change**: In TUI, change `audit_csv` → `csv_config` → `delimiter` from `,` to `|`

**Prompt** (copy-paste into Claude Desktop):
```
Using the MCP filesystem tool, read the file /Users/dbright/mcp/gatekit/tests/validation/test-files/clean.txt and show me its contents
```

**Check the CSV audit log**:
```bash
tail -3 /tmp/gatekit-validation/audit.csv
```

**Expected Output**:
- [ ] Fields separated by `|` instead of `,`
- [ ] Header row uses `|` delimiter
- [ ] Data rows use `|` delimiter

**What you should see**: Output like `timestamp|server|method|outcome` instead of `timestamp,server,method,outcome`.

**Revert**: Change `csv_config` → `delimiter` back to `,` before next test.

---

#### 4.5.4 Notification Body Inclusion (JSONL)

This test verifies that Gatekit captures and logs MCP notifications from upstream servers.

> **Understanding MCP Notifications**: Notifications are transport-level messages from servers to the client application (Claude Desktop). They are **not** injected into the LLM's conversation context. Gatekit forwards them to Claude Desktop, which may use them for UI purposes (progress bars, status updates) but won't show them to the model. This is expected MCP behavior, not a limitation.

**Step 1: Add the everything server to your config**

The "Everything" demo server sends `notifications/message` periodically. Add it to your config:

1. Click "+ Add Server" in the server list
2. Enter server name: `everything`
3. In the Command field, enter the full command as a single string:
   ```
   npx -y @modelcontextprotocol/server-everything
   ```
4. Click "Connect" to verify it works
5. Save the config

> **Reference**: The [Everything MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/src/everything) is a demo server that exercises all MCP protocol features.

**Step 2: Enable notification body logging**

In TUI, change `audit_jsonl` → `include_notification_body` from `false` to `true`

Save the config and restart Claude Desktop.

**Step 3: Trigger a tool call to generate notifications**

Use this prompt in Claude Desktop (copy-paste):
```
This is a test for MCP notifications. Please call the longRunningOperation tool from the "everything" MCP server with duration=5 and steps=3. This is just for validation - no need to do anything with the result.
```

The server sends `notifications/message` during the operation. Claude won't "see" these (they're client-level, not model-level), but Gatekit will log them.

**Step 4: Check the audit log for notification entries**:
```bash
grep '"method": "notifications/' /tmp/gatekit-validation/audit.jsonl | tail -5 | python3 -m json.tool --indent 2
```

**Expected Output**:
- [ ] Notification entries exist with `"method": "notifications/message"` or `"notifications/progress"`
- [ ] `notification_body` field is present and contains the notification params
- [ ] Example body: `{"level": "notice", "data": "Notice-level message"}`

**What this verifies**:
- [ ] Gatekit receives notifications from upstream servers
- [ ] Gatekit processes them through the plugin pipeline
- [ ] Gatekit forwards them to Claude Desktop (via `write_notification()` in `proxy/server.py:888`)
- [ ] Audit logging captures notification bodies when enabled

**If no notifications appear**:
- [ ] Verify the config change was saved (reopen in TUI and check `include_notification_body: true`)
- [ ] Check that the `everything` server connected successfully
- [ ] Some MCP clients may not support all notification types

**Revert**:
1. Change `include_notification_body` back to `false`
2. Optionally remove the `everything` server if you don't need it for other tests

---

#### 4.5.5 Audit Log Verification (All Formats)

After running the above tests, verify all three audit formats captured events correctly.

**Check JSONL audit log**:
```bash
tail -20 /tmp/gatekit-validation/audit.jsonl | python3 -m json.tool --indent 2 | head -100
```

**Verify**:
- [ ] Each tool call has an entry
- [ ] `method` field shows `tools/call`
- [ ] `pipeline` shows which plugins processed the request
- [ ] `outcome` shows `ALLOWED`, `BLOCKED`, or `MODIFIED`

**Check CSV audit log**:
```bash
cat /tmp/gatekit-validation/audit.csv
```

**Verify**:
- [ ] Header row with column names
- [ ] One row per request/response
- [ ] Timestamps, server names, methods, outcomes visible

**Check human-readable log**:
```bash
tail -30 /tmp/gatekit-validation/audit.log
```

**Verify**:
- [ ] Readable timestamps
- [ ] Clear indication of what was processed
- [ ] Duration/timing information if configured

---

## Part 5: Error Messages (~10 min)

**Goal**: Verify error messages are clear and actionable.

### 5.1 Malformed YAML

```bash
/Users/dbright/mcp/gatekit/.venv/bin/gatekit-gateway --config tests/validation/invalid-configs/malformed.yaml
```

**Expected output** (clean, no traceback):
```
[ERROR] Startup failed: YAML syntax error: mapping values are not allowed here
[ERROR]     File: /Users/dbright/mcp/gatekit/tests/validation/invalid-configs/malformed.yaml
    Line: 18
    Content:       - handler: basic_pii_filter
[ERROR]   Suggestions:
    • Check YAML syntax
[ERROR] Not in MCP client context (running in terminal), exiting
```

**Checklist**:
- [ ] Error mentions "YAML" or "syntax"
- [ ] Line number shown (Line: 18)
- [ ] Problematic content shown
- [ ] Suggestion for how to fix
- [ ] **No Python traceback** (this is a config parsing error)

### 5.2 Invalid Priority

```bash
/Users/dbright/mcp/gatekit/.venv/bin/gatekit-gateway --config tests/validation/invalid-configs/invalid-priority.yaml
```

**Expected output** (clean, no traceback):
```
[ERROR] Startup failed: Configuration validation failed: Value error, Plugin priority must be an integer between 0 and 100, got 999
[ERROR]     Field: plugins.security._global.0.config
[ERROR]   Suggestions:
    • Check field value is valid
```

**Checklist**:
- [ ] Error mentions "priority"
- [ ] Valid range shown (0-100)
- [ ] Invalid value shown (999)
- [ ] Field path shown
- [ ] **No Python traceback** (caught during config validation)

### 5.3 Missing Handler

```bash
/Users/dbright/mcp/gatekit/.venv/bin/gatekit-gateway --config tests/validation/invalid-configs/missing-handler.yaml
```

**Expected output** (clean, no traceback):
```
[ERROR] Startup failed: Plugin 'nonexistent_super_plugin' not found
[ERROR]     Field: plugins.security.nonexistent_super_plugin
[ERROR]   Suggestions:
    • Available security: basic_pii_filter, basic_prompt_injection_defense, basic_secrets_filter
```

**Checklist**:
- [ ] Error mentions the handler name (`nonexistent_super_plugin`)
- [ ] Lists available handlers as suggestions
- [ ] Shows field path where error occurred
- [ ] **No Python traceback** (this is a config validation error)

### 5.4 Upstream Server Error

```bash
/Users/dbright/mcp/gatekit/.venv/bin/gatekit-gateway --config tests/validation/invalid-configs/upstream-server-error.yaml
```

**Expected behavior**: Gateway starts successfully, but fails when connecting to the broken server.

**Expected output** (error occurs on connection attempt, includes traceback):
```
[INFO] gatekit.main: Gatekit is ready and accepting connections
...
[INFO] gatekit.server_manager: Connecting to server 'broken-server'
[ERROR] gatekit.transport.stdio: Failed to start MCP server process
Traceback (most recent call last):
  ...
FileNotFoundError: [Errno 2] No such file or directory: 'nonexistent-command-that-does-not-exist'
```

**Checklist**:
- [ ] Gateway starts (shows "ready and accepting connections")
- [ ] Error occurs when connecting to server
- [ ] Error mentions the server name (`broken-server`)
- [ ] Error shows the command that failed
- [ ] Note: Traceback is expected (runtime connection error)

### 5.5 Permission Error

```bash
/Users/dbright/mcp/gatekit/.venv/bin/gatekit-gateway --config tests/validation/invalid-configs/permission-error.yaml
```

**Expected output** (includes detailed error with traceback):
```
[ERROR] Startup failed: Startup error - Critical auditing plugin JsonAuditingPlugin failed to initialize...
...
ISSUE: Parent directory does not exist: /root
SOLUTION: Create the directory or use a path where the parent directory exists
To continue with non-critical auditing, set 'critical: false' in plugin config.
```

**Checklist**:
- [ ] Error mentions permission or read-only filesystem
- [ ] Path that failed is shown (`/root/gatekit-audit.jsonl`)
- [ ] ISSUE and SOLUTION guidance provided
- [ ] Suggests `critical: false` as workaround
- [ ] Note: Traceback is expected (runtime initialization error)

### 5.6 Critical Plugin Failure Handling

**Goal**: Verify that critical plugins (default) prevent startup on failure, while non-critical plugins allow startup with warnings.

All plugins default to `critical: true` (fail-closed behavior). This test validates that behavior.

**Test A: Critical Plugin Failure (should fail to start)**

```bash
/Users/dbright/mcp/gatekit/.venv/bin/gatekit-gateway \
  --config tests/validation/invalid-configs/critical-failure-test.yaml
```

**Expected output** (includes detailed error with traceback):
```
[ERROR] Startup failed: Startup error - Critical auditing plugin JsonAuditingPlugin failed to initialize...
...
ISSUE: Parent directory does not exist: /nonexistent/directory/that/does/not/exist
SOLUTION: Create the directory or use a path where the parent directory exists
To continue with non-critical auditing, set 'critical: false' in plugin config.
```

**Checklist**:
- [ ] Gateway exits immediately with non-zero status
- [ ] Error message mentions "Critical auditing plugin"
- [ ] Error message mentions the plugin class name (`JsonAuditingPlugin`)
- [ ] Error message shows the problematic path
- [ ] Error message includes ISSUE and SOLUTION guidance
- [ ] No "Listening" or "Started" message (gateway never reaches ready state)
- [ ] Note: Traceback is expected here (runtime initialization error)

**Test B: Non-Critical Plugin Failure (should start with warning)**

```bash
/Users/dbright/mcp/gatekit/.venv/bin/gatekit-gateway \
  --config tests/validation/invalid-configs/non-critical-failure-test.yaml
```

**Expected output** (clean startup with warning):
```
... [INFO] gatekit.plugins.manager: Discovered 3 handlers in auditing category
... [WARNING] gatekit.config.loader: Non-critical auditing plugin 'audit_jsonl' has path validation errors: Parent directory does not exist: /nonexistent/directory/that/does/not/exist ...
... [INFO] gatekit.main: Loading configuration from tests/validation/invalid-configs/non-critical-failure-test.yaml
... [INFO] gatekit.main: Starting Gatekit MCP Gateway
... [INFO] gatekit.main: Gatekit is ready and accepting connections
... [WARNING] gatekit.plugins.manager: Non-critical auditing plugin 'audit_jsonl' has path validation errors: ...
... [INFO] gatekit.plugins.manager: Loaded 1 auditing plugins for upstream '_global'
... [INFO] gatekit.server_manager: Connecting to server 'filesystem'
... [INFO] gatekit.server_manager: Successfully connected to server 'filesystem' ...
... [INFO] gatekit.proxy.server: MCPProxy now accepting client connections
```

Note: Do NOT use `--verbose` for this test - it enables DEBUG logging which produces excessive output.
The warning appears twice (once during config validation, once during plugin initialization) - this is expected.

**Checklist**:
- [ ] Gateway starts successfully (shows "ready and accepting connections")
- [ ] Warning logged about the failed plugin
- [ ] Warning mentions the plugin name (`audit_jsonl`)
- [ ] Gateway waits for connections (Ctrl+C to exit after verifying)

**Why this matters**:
- **Security plugins** with `critical: true` (default) ensure that if a security check can't run, no traffic flows
- **Auditing plugins** with `critical: true` (default) ensure compliance - if audit logging fails, operations halt
- Setting `critical: false` explicitly opts into degraded operation for specific plugins

### 5.7 Unknown Configuration Options

**Goal**: Verify that unknown plugin configuration fields are handled according to the `critical` flag - fatal for critical plugins (default), warning and skip for non-critical plugins.

**Test A: Critical Plugin with Unknown Options (should fail to start)**

```bash
/Users/dbright/mcp/gatekit/.venv/bin/gatekit-gateway --config tests/validation/invalid-configs/unknown-options.yaml
```

**Expected output** (clean, no traceback):
```
[ERROR] Startup failed: Plugin configuration validation failed:
  audit_jsonl (plugins.auditing._global.0.config): At /: Additional properties are not allowed ('include_pipeline', 'include_timing' were unexpected)
[ERROR]     Field: plugins.auditing._global.0.config
[ERROR]   Suggestions:
    • Valid fields for audit_jsonl: critical, enabled, include_notification_body, include_request_body, include_response_body, max_body_size, output_file
    • Remove or rename unknown fields
[ERROR] Not in MCP client context (running in terminal), exiting
```

**Checklist**:
- [ ] Gateway exits immediately with non-zero status
- [ ] Error mentions the unknown field names
- [ ] Error mentions the plugin handler name
- [ ] Field path uses dot notation (`_global.0.config` not `_global[0].config`)
- [ ] Suggestions list valid fields for the plugin
- [ ] **No Python traceback** (this is a config validation error)

**Test B: Non-Critical Plugin with Unknown Options (should start with warning)**

```bash
/Users/dbright/mcp/gatekit/.venv/bin/gatekit-gateway --config tests/validation/invalid-configs/non-critical-schema-error.yaml
```

**Expected output** (clean startup with warning):
```
... [WARNING] root: Non-critical auditing plugin 'audit_jsonl' has schema validation errors: At /: Additional properties are not allowed ('another_bad_option', 'unknown_option' were unexpected). Plugin will be skipped.
... [INFO] gatekit.main: Loading configuration from tests/validation/invalid-configs/non-critical-schema-error.yaml
... [INFO] gatekit.main: Starting Gatekit MCP Gateway
... [INFO] gatekit.main: Gatekit is ready and accepting connections
```

**Checklist**:
- [ ] Gateway starts successfully (shows "ready and accepting connections")
- [ ] Warning logged about schema validation errors
- [ ] Warning mentions the plugin name (`audit_jsonl`)
- [ ] Warning mentions the unknown field names
- [ ] Warning says "Plugin will be skipped"
- [ ] Gateway continues without the invalid plugin

**Why this matters**: Unknown fields are silently ignored without this validation. A typo like `action: blcok` (instead of `block`) would cause the plugin to use its default action, potentially weakening security without any warning. The `critical` flag allows users to choose between fail-closed (default) and graceful degradation behavior.

---

## Part 6: Platform Delta (Non-macOS Only)

**Run only on Linux or Windows after macOS validation passes.**

**Setup**: See `docs/testing/windows-setup.md` for Windows environment setup instructions.

### 6.1 Process Management

When the MCP client connects to Gatekit:
- [ ] Gateway starts cleanly (no platform-specific warnings)
- [ ] When client disconnects, gateway exits cleanly
- [ ] No zombie processes after client shutdown
- [ ] Upstream servers terminate when gateway exits

**Windows verification**:
```powershell
.venv\Scripts\gatekit-gateway.exe --config tests\validation\gateway-test-config.yaml --verbose
# Connect Claude Desktop, make a tool call, disconnect
# Check Task Manager for orphan python.exe or node.exe processes
```

### 6.2 Path Handling

**Linux**:
- [ ] Debug logs written to `~/.local/state/gatekit/`
- [ ] Default config discovered in XDG-compliant locations

**Windows**:
- [ ] Debug logs written to `%LOCALAPPDATA%\gatekit\logs\`
- [ ] Paths with spaces handled correctly

**Windows verification**:
```powershell
gatekit --debug
dir $env:LOCALAPPDATA\gatekit\logs\
# Should show: gatekit_tui_debug.log
```

### 6.3 All 5 Client Config Paths

Verify each client's config path is correct for the platform:

| Client | Expected Path (Windows) | Expected Path (Linux) |
|--------|------------------------|----------------------|
| Claude Desktop | `%APPDATA%\Claude\claude_desktop_config.json` | `~/.config/Claude/claude_desktop_config.json` |
| Claude Code | `~/.claude.json` | `~/.claude.json` |
| Codex | `~/.codex/config.toml` | `~/.codex/config.toml` |
| Cursor | `~/.cursor/mcp.json` | `~/.cursor/mcp.json` |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` | `~/.codeium/windsurf/mcp_config.json` |

**Windows verification**:
```powershell
python -c "from gatekit.tui.guided_setup.client_registry import *; print('Claude Desktop:', get_claude_desktop_path())"
python -c "from gatekit.tui.guided_setup.client_registry import *; print('Claude Code:', get_claude_code_path())"
python -c "from gatekit.tui.guided_setup.client_registry import *; print('Codex:', get_codex_path())"
python -c "from gatekit.tui.guided_setup.client_registry import *; print('Cursor:', get_cursor_path())"
python -c "from gatekit.tui.guided_setup.client_registry import *; print('Windsurf:', get_windsurf_path())"
```

- [ ] Claude Desktop path correct for platform
- [ ] Claude Code path correct
- [ ] Codex path correct
- [ ] Cursor path correct
- [ ] Windsurf path correct

### 6.4 Shell Commands

**Linux**:
- [ ] Generated shell commands use bash syntax
- [ ] Backslash (`\`) for line continuation
- [ ] Single quotes for values (via `shlex.quote`)

**Windows**:
- [ ] Generated commands use PowerShell syntax
- [ ] Backtick (`` ` ``) for line continuation
- [ ] Double quotes for values
- [ ] Shell name shows "PowerShell" not "terminal"

**Test CLI clients (Claude Code, Codex)**:

Run Guided Setup, select Claude Code or Codex as target client:
- [ ] Instructions show PowerShell syntax on Windows
- [ ] Instructions show bash syntax on Linux
- [ ] Line continuation character correct for platform

**Test manual-edit clients (Claude Desktop, Cursor, Windsurf)**:
- [ ] JSON config shown correctly
- [ ] Paths in config are valid for the platform

### 6.5 Restore Scripts

After completing Guided Setup with restore enabled, verify generated scripts:

**CLI Clients (Claude Code, Codex)**:
- **Linux**: `.sh` executable scripts with bash syntax
- **Windows**: `.txt` files with PowerShell instructions

**Manual-Edit Clients (Claude Desktop, Cursor, Windsurf)**:
- **All platforms**: `.txt` files with JSON config to copy

**Windows verification**:
```powershell
# Check restore scripts exist
dir configs\restore\

# Verify PowerShell restore script (Claude Code)
type configs\restore\restore-claude-code-*.txt
# Should show:
# - Write-Host statements (not echo)
# - Backtick line continuation
# - "PowerShell" in header text

# Verify JSON restore script (Claude Desktop)
type configs\restore\restore-claude-desktop-*.txt
# Should show:
# - JSON config to paste
# - Correct Windows config file path
```

**Checklist**:
- [ ] Claude Code restore script has PowerShell syntax (Windows) / bash syntax (Linux)
- [ ] Codex restore script has PowerShell syntax (Windows) / bash syntax (Linux)
- [ ] Claude Desktop restore shows correct platform-specific path
- [ ] Cursor restore shows correct platform-specific path
- [ ] Windsurf restore shows correct platform-specific path

### 6.6 Clipboard Operations

- [ ] "Copy" buttons in TUI work on Windows (uses `clip` command)
- [ ] "Copy" buttons in TUI work on Linux (uses `xclip` or `xsel`)
- [ ] Copied content pastes correctly into other applications

### 6.7 Full Integration Test (Windows)

```powershell
# 1. Configure Claude Desktop to use Gatekit
notepad "$env:APPDATA\Claude\claude_desktop_config.json"
# Add gatekit server configuration

# 2. Restart Claude Desktop
# 3. Make a tool call through Gatekit
# 4. Verify audit logs are written correctly
```

- [ ] MCP communication works end-to-end on Windows

---

## Quick Reference

### Test Files Location

```
tests/validation/test-files/
├── clean.txt              # No sensitive data (ALLOWED)
├── personal-info.txt      # PII: emails, phones, SSNs, IPs (REDACTED)
├── secrets.txt            # AWS keys, tokens (REDACTED)
├── prompt-injection.txt   # Injection patterns (REDACTED/BLOCKED)
├── base64-encoded.txt     # Base64-encoded PII/secrets
└── high-entropy.txt       # High-entropy strings for threshold testing
```

### Config Files

```
tests/validation/
├── manual-validation-config.yaml  # Seed config (DO NOT MODIFY - use as starting point)
├── tui-test-config.yaml           # Working copy for TUI testing (created in 1.1)
├── gateway-test-config.yaml       # Clean TUI-saved config for gateway tests (created in 1.6)
└── invalid-configs/               # Error testing configs (Part 5)
    ├── malformed.yaml                   # 5.1: YAML syntax error
    ├── invalid-priority.yaml            # 5.2: Priority outside 0-100 range
    ├── missing-handler.yaml             # 5.3: Unknown plugin handler name
    ├── upstream-server-error.yaml       # 5.4: Nonexistent server command
    ├── permission-error.yaml            # 5.5: Unwritable audit log path
    ├── critical-failure-test.yaml       # 5.6A: critical=true (default) - gateway fails
    ├── non-critical-failure-test.yaml   # 5.6B: critical=false - gateway warns and starts
    ├── unknown-options.yaml             # 5.7A: critical=true - unknown options fatal
    └── non-critical-schema-error.yaml   # 5.7B: critical=false - unknown options skipped
```

### Debugging Tips

**TUI issues**:
```bash
gatekit --debug
# Logs: ~/Library/Logs/gatekit/gatekit_tui_debug.log (macOS)
```

**Gateway issues**:
Add `--verbose` to the gateway args in your MCP client config:
```json
{
  "mcpServers": {
    "gatekit": {
      "command": "/Users/dbright/mcp/gatekit/.venv/bin/gatekit-gateway",
      "args": ["--config", "/path/to/gatekit.yaml", "--verbose"]
    }
  }
}
```

Check the audit log files configured in your config for detailed request/response info.

**Config validation** (quick syntax check):
```bash
python3 -c "import yaml; yaml.safe_load(open('gatekit.yaml'))"
```

**Full config validation** (validates against Gatekit schema):
```bash
/Users/dbright/mcp/gatekit/.venv/bin/gatekit-gateway --config gatekit.yaml --help
# This loads and validates the config, then exits
```

---

## After Validation

Once you've completed each section:

1. **Trust pytest** - The automated tests cover regression protection
2. **Skip manual validation** for subsequent changes unless:
   - Major feature additions
   - Platform-specific changes
   - TUI flow changes
3. **Update this guide** if you find gaps in coverage

The goal is to see each behavior once with your own eyes, confirm it works, then rely on automation.
