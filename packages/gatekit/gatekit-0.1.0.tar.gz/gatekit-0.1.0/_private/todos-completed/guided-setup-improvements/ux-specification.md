# Guided Setup UX Improvements

## Problem Statement
The current guided setup flow is too engineering-focused - it asks for all inputs upfront (file paths, directories) before showing any value to the user. This creates a poor user experience where users are "giving" information before they understand what they're getting.

## Solution: Progressive Discovery Flow
Implement a wizard-like experience that progressively reveals information and only asks for user input after providing context and value.

## New Flow Design

### Screen 1: Discovery Screen
**Purpose:** Show live progress while scanning for MCP clients

**Features:**
- Animated progress bars for each client type being scanned
- Real-time display of found configurations with paths
- Running count of clients and servers found
- Auto-transition to complete state when done

**Key Elements:**
- Show which clients we're looking for (Claude Desktop, Claude Code, Codex)
- Display checkmarks/x-marks as each scan completes
- Show file paths where configs were found
- Count total servers discovered

**Mockup (Scanning in Progress):**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Detecting MCP Clients                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Scanning your system for MCP client configurations...                 │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │  Claude Desktop  [████████████████████] ✓ Found                │    │
│  │  ~/Library/Application Support/Claude/claude_desktop_config.json│    │
│  │  • 3 servers detected                                          │    │
│  │                                                                 │    │
│  │  Claude Code     [████████████████████] ✗ Not found            │    │
│  │  Checked: ~/.claude.json, .mcp.json                            │    │
│  │                                                                 │    │
│  │  Codex           [██████████░░░░░░░░░░] ⟳ Scanning...          │    │
│  │  Checking: ~/.codex/config.toml                                │    │
│  │                                                                 │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────────────────────────────────┐                         │
│  │ Found: 1 client, 3 servers total         │                         │
│  │ Scanning: 1 remaining                    │                         │
│  └─────────────────────────────────────────┘                         │
│                                                                         │
│                              [Cancel]                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Mockup (Detection Complete - No Errors):**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Detection Complete                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ✅ Found 2 MCP clients with 5 servers total                          │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │  Claude Desktop  ✓                                             │    │
│  │  • filesystem-server                                           │    │
│  │  • github-server                                               │    │
│  │  • slack-server                                                │    │
│  │                                                                 │    │
│  │  Codex          ✓                                             │    │
│  │  • python-executor                                             │    │
│  │  • terminal-server                                             │    │
│  │                                                                 │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│         [Continue to Server Selection]  [Rescan]  [Cancel]            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Mockup (Detection Complete - With Errors):**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Detection Complete                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ✅ Found 2 MCP clients with 5 servers total                          │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │  Claude Desktop  ✓                                             │    │
│  │  • filesystem-server                                           │    │
│  │  • github-server                                               │    │
│  │  • slack-server                                                │    │
│  │                                                                 │    │
│  │  Codex          ✓ (⚠ 1 parsing error – [View details])        │    │
│  │  • python-executor                                             │    │
│  │  • terminal-server                                             │    │
│  │                                                                 │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ⚠ Some servers had parsing errors and will not be migrated.          │
│    Fix the errors and click Rescan to try again.                      │
│                                                                         │
│         [Continue to Server Selection]  [Rescan]  [Cancel]            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Mockup (Detection Complete - Errors Expanded):**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Detection Complete                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ✅ Found 2 MCP clients with 5 servers total                          │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │  Claude Desktop  ✓                                             │    │
│  │  • filesystem-server                                           │    │
│  │  • github-server                                               │    │
│  │  • slack-server                                                │    │
│  │                                                                 │    │
│  │  Codex          ✓ (⚠ 1 parsing error – [Hide details])        │    │
│  │  • python-executor                                             │    │
│  │  • terminal-server                                             │    │
│  │  ⚠ Error parsing server 'broken-server':                      │    │
│  │    Missing required field 'command' in server configuration    │    │
│  │                                                                 │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ⚠ Some servers had parsing errors and will not be migrated.          │
│    Fix the errors and click Rescan to try again.                      │
│                                                                         │
│         [Continue to Server Selection]  [Rescan]  [Cancel]            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Mockup (Detection Complete - With HTTP Servers):**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Detection Complete                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ✅ Found 2 MCP clients with 7 servers total                          │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │  Claude Desktop  ✓                                             │    │
│  │  • filesystem-server                                           │    │
│  │  • github-server                                               │    │
│  │  • slack-server                                                │    │
│  │  • api-server (HTTP)                                           │    │
│  │                                                                 │    │
│  │  Codex          ✓                                             │    │
│  │  • python-executor                                             │    │
│  │  • terminal-server                                             │    │
│  │  • webhook-server (HTTP)                                       │    │
│  │                                                                 │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ⓘ 2 HTTP servers detected but not yet supported.                     │
│    Only stdio servers (5) will be available for selection.             │
│                                                                         │
│         [Continue to Server Selection]  [Rescan]  [Cancel]            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Error Handling Notes:**
- Parse errors are logged for telemetry (same data shown in UI)
- Errors default to collapsed state (don't overwhelm happy path)
- Click to expand/collapse error details
- Failed servers are excluded from Server Selection screen

**Rescan/Retry Support:**
- Add "Rescan" button on Detection Complete screen
- Allows users to fix config issues and re-run detection
- Clears previous state and starts fresh scan
- Useful if user needs to:
  - Fix JSON syntax errors in config files
  - Add missing config files
  - Grant filesystem permissions

**HTTP/SSE Server Visibility:**
- Detection counts ALL servers (including HTTP/SSE)
- Only stdio servers are selectable in Server Selection screen
- Clear messaging about skipped servers:
  - "Found 5 servers total (2 HTTP servers not shown - coming soon)"
  - HTTP servers listed in informational modal if user wants details
- Prevents confusion when detection count doesn't match selection count

### Screen 2: Server Selection Screen
**Purpose:** Let users choose which servers to manage with Gatekit

**Features:**
- Flat list of unique servers (deduplicates identical configurations)
- Checkboxes for each server (all selected by default)
- Shows which clients use each server (provenance)
- Clear handling of name conflicts (auto-renamed with suffixes)
- Select All/None buttons

**Key Information Shown:**
- Server names with command/configuration details
- Which clients use each server ("Used by: X, Y" for shared, "From: X" for single)
- Automatic conflict resolution when needed
- Running count of unique servers

**Deduplication Logic:**
- Identical servers (same name + command + env) shown once
- Name conflicts (same name, different config) automatically renamed with suffixes
- One checkbox per unique server in final Gatekit config
- Environment variables are preserved (consolidated into Gatekit entry during migration)

**Mockup (No Conflicts):**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Select Servers to Manage                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Choose which MCP servers Gatekit should manage:                     │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │  ☑ filesystem-server                                          │    │
│  │    Command: npx @modelcontextprotocol/server-filesystem /tmp   │    │
│  │    Used by: Claude Desktop, Codex                              │    │
│  │                                                                 │    │
│  │  ☑ github-server                                              │    │
│  │    Command: npx @modelcontextprotocol/server-github            │    │
│  │    From: Claude Desktop                                        │    │
│  │                                                                 │    │
│  │  ☑ slack-server                                               │    │
│  │    Command: npx @modelcontextprotocol/server-slack             │    │
│  │    From: Claude Desktop                                        │    │
│  │                                                                 │    │
│  │  ☑ python-executor                                             │    │
│  │    Command: python-executor-server                             │    │
│  │    From: Codex                                                 │    │
│  │                                                                 │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Selected: 4 unique servers (1 shared by multiple clients)            │
│                                                                         │
│     [Select All]  [Select None]  [Continue]  [Back]                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Mockup (Name Conflicts Detected):**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Select Servers to Manage                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ⚠ Name Conflicts Resolved                                            │
│  Multiple clients have servers named "filesystem-server" with          │
│  different configurations. They've been renamed to avoid conflicts.    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │  ☑ filesystem-server-desktop                                   │    │
│  │    Command: npx @m.../server-filesystem /home/user/docs        │    │
│  │    From: Claude Desktop (renamed from "filesystem-server")     │    │
│  │                                                                 │    │
│  │  ☑ filesystem-server-codex                                     │    │
│  │    Command: npx @m.../server-filesystem /tmp/workspace         │    │
│  │    From: Codex (renamed from "filesystem-server")              │    │
│  │                                                                 │    │
│  │  ☑ github-server                                              │    │
│  │    Command: npx @modelcontextprotocol/server-github            │    │
│  │    From: Claude Desktop                                        │    │
│  │                                                                 │    │
│  │  ☑ python-executor                                             │    │
│  │    Command: python-executor-server                             │    │
│  │    From: Codex                                                 │    │
│  │                                                                 │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Selected: 4 servers                                                   │
│                                                                         │
│  ⓘ Renamed servers keep their unique configurations separate.         │
│                                                                         │
│     [Select All]  [Select None]  [Continue]  [Back]                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Screen 3: Client Migration Selection
**Purpose:** Choose which clients should be configured to use Gatekit

**Features:**
- List of detected clients with their config paths
- Checkboxes to include/exclude clients from migration
- Clear explanation that we provide instructions only (no automatic updates)
- Preview of what instructions will be provided

**Default Behavior:**
- All clients with selected servers are checked by default
- Assumption is user wants to migrate everything (they chose guided setup)

**Key Messaging:**
- "We'll generate instructions for updating these clients"
- "For security, you'll apply these changes yourself"
- "Gatekit never modifies client configurations directly"

**Mockup:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                   Migration Instructions                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  We'll generate instructions for updating these clients:               │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │  ☑ Claude Desktop → Gatekit                                  │    │
│  │    • Servers: filesystem-server, github-server, slack-server   │    │
│  │    • Proxied via Gatekit gateway                             │    │
│  │                                                                 │    │
│  │  ☑ Codex → Gatekit                                           │    │
│  │    • Servers: python-executor                                  │    │
│  │    • Proxied via Gatekit gateway                             │    │
│  │                                                                 │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Uncheck any clients you want to keep using servers directly.          │
│                                                                         │
│  What you'll get:                                                      │
│  • Step-by-step manual update instructions for each client             │
│  • Copy-paste ready configuration snippets                             │
│  • Backup and restore instructions                                     │
│                                                                         │
│  ⓘ For security, you'll apply these changes yourself.                 │
│    Gatekit never modifies client configurations directly.            │
│                                                                         │
│                     [Continue]  [Back]  [Cancel]                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Screen 4: Configuration Summary
**Purpose:** Show what will be created before asking for file paths

**Features:**
- Summary of Gatekit configuration structure
- List of servers that will be managed
- Preview of default plugin configuration
- Which clients will get migration instructions
- **NOW ask for file paths** (config location, optional restore scripts)

**Key Elements:**
- Clear preview of configuration before commitment
- File path inputs with sensible defaults
- Optional restore script generation (checkbox)
- Generate & Apply button

**Mockup (No Env Var Conflicts):**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Review Configuration                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Here's what will be created:                                         │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │ Gatekit Configuration                                        │    │
│  │                                                                 │    │
│  │ Upstream Servers (4):                                          │    │
│  │   • filesystem-server  (from Claude Desktop)                   │    │
│  │   • github-server      (from Claude Desktop)                   │    │
│  │   • slack-server       (from Claude Desktop)                   │    │
│  │   • python-executor    (from Codex)                            │    │
│  │                                                                 │    │
│  │ Default Plugins:                                                │    │
│  │   • JSON audit logging (enabled)                               │    │
│  │   • No security policies (add later)                           │    │
│  │                                                                 │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │ Client Updates                                                 │    │
│  │                                                                 │    │
│  │ Will Update:                                                   │    │
│  │   ✓ Claude Desktop - Add Gatekit proxy server               │    │
│  │   ✓ Codex - Modify config to use Gatekit                    │    │
│  │                                                                 │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Save Locations:                                                       │
│                                                                         │
│  Gatekit config: [configs/gatekit.yaml        ] [Browse...]       │
│                                                                         │
│  ☐ Generate restore scripts                                           │
│  Restore scripts:  [~/Documents/gatekit-restore ] [Browse...]       │
│                                                                         │
│                  [Generate & Apply]  [Back]  [Cancel]                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Mockup (With Env Var Conflicts):**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Review Configuration                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Here's what will be created:                                         │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │ Gatekit Configuration                                        │    │
│  │                                                                 │    │
│  │ Upstream Servers (4):                                          │    │
│  │   • filesystem-server  (from Claude Desktop)                   │    │
│  │   • github-server      (from Claude Desktop)                   │    │
│  │   • slack-server       (from Claude Desktop)                   │    │
│  │   • python-executor    (from Codex)                            │    │
│  │                                                                 │    │
│  │ Default Plugins:                                                │    │
│  │   • JSON audit logging (enabled)                               │    │
│  │   • No security policies (add later)                           │    │
│  │                                                                 │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │ Client Updates                                                 │    │
│  │                                                                 │    │
│  │ Will Update:                                                   │    │
│  │   ✓ Claude Desktop - Add Gatekit proxy server               │    │
│  │   ✓ Codex - Modify config to use Gatekit                    │    │
│  │                                                                 │    │
│  │ ⚠ Environment Variable Conflicts (1):  [View Details]         │    │
│  │   OPENAI_API_KEY has different values between servers.        │    │
│  │   Value from slack-server will be used.                       │    │
│  │                                                                 │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Save Locations:                                                       │
│                                                                         │
│  Gatekit config: [configs/gatekit.yaml        ] [Browse...]       │
│                                                                         │
│  ☐ Generate restore scripts                                           │
│  Restore scripts:  [~/Documents/gatekit-restore ] [Browse...]       │
│                                                                         │
│                  [Generate & Apply]  [Back]  [Cancel]                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Mockup (Env Var Conflicts Expanded):**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Review Configuration                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Here's what will be created:                                         │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │ Gatekit Configuration                                        │    │
│  │                                                                 │    │
│  │ Upstream Servers (4):                                          │    │
│  │   • filesystem-server  (from Claude Desktop)                   │    │
│  │   • github-server      (from Claude Desktop)                   │    │
│  │   • slack-server       (from Claude Desktop)                   │    │
│  │   • python-executor    (from Codex)                            │    │
│  │                                                                 │    │
│  │ Default Plugins:                                                │    │
│  │   • JSON audit logging (enabled)                               │    │
│  │   • No security policies (add later)                           │    │
│  │                                                                 │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │ Client Updates                                                 │    │
│  │                                                                 │    │
│  │ Will Update:                                                   │    │
│  │   ✓ Claude Desktop - Add Gatekit proxy server               │    │
│  │   ✓ Codex - Modify config to use Gatekit                    │    │
│  │                                                                 │    │
│  │ ⚠ Environment Variable Conflicts (1):  [Hide Details]         │    │
│  │                                                                 │    │
│  │   OPENAI_API_KEY has different values:                        │    │
│  │     • github-server: ********xyz1                              │    │
│  │     • slack-server:  ********abc2                              │    │
│  │   Using value from slack-server                               │    │
│  │                                                                 │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Save Locations:                                                       │
│                                                                         │
│  Gatekit config: [configs/gatekit.yaml        ] [Browse...]       │
│                                                                         │
│  ☐ Generate restore scripts                                           │
│  Restore scripts:  [~/Documents/gatekit-restore ] [Browse...]       │
│                                                                         │
│                  [Generate & Apply]  [Back]  [Cancel]                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Notes:**
- Env var conflicts shown in both summary screen and migration instructions
- Values are masked for security (show last 4 chars only)
- Conflicts default to collapsed state
- Clear indication of which value will be used (deterministic: servers sorted by name, last one wins)

### Screen 5: Setup Actions (Progress)
**Purpose:** Show progress while generating files

**Features:**
- Real-time progress indicators
- Checkmarks as each action completes
- Display file paths as they're created
- Show what's being written

**Actions Performed:**
1. Create Gatekit configuration
2. Generate migration instructions for each client
3. Create restore scripts (if requested)
4. Prepare final summary

**Error Handling Strategy:**
When filesystem errors occur during file generation, use **atomic operations with cleanup**:

1. **Write to temporary files first (cross-platform)**
   - Use `tempfile.NamedTemporaryFile(delete=False)` for each output
   - Only move to final location after successful write
   - Example (cross-platform):
     ```python
     import tempfile
     from pathlib import Path

     # Write to temp file
     with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as tmp:
         tmp.write(config_yaml)
         tmp_path = Path(tmp.name)

     # Atomic move to final location (works on Windows, macOS, Linux)
     final_path = Path("configs/gatekit.yaml")
     tmp_path.replace(final_path)  # Atomic on same filesystem
     ```

2. **Track created artifacts**
   - Maintain list of successfully created files
   - On error, show user which files were created
   - Offer cleanup option: "Remove partial files" or "Keep for manual inspection"

3. **Error scenarios:**
   - **Permission denied**: Show clear error, list what succeeded, offer to retry with different path
   - **Disk full**: Show error, cleanup temp files automatically, suggest alternate location
   - **Path doesn't exist**: Create parent directories automatically (with confirmation)
   - **File already exists**: Ask user: Overwrite, Skip, or Rename

4. **Recovery options:**
   - "Retry" - Attempt same operation again
   - "Change Path" - Let user pick different save location
   - "Skip This File" - Continue with remaining files (for restore scripts)
   - "Cancel Setup" - Rollback all changes, cleanup temp files

5. **No silent failures**
   - Never leave partial artifacts without user awareness
   - Always show what was created vs. what failed
   - Provide path to successful files for manual recovery

**Mockup:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Applying Configuration                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │                                                                 │    │
│  │  ✓ Created Gatekit configuration                             │    │
│  │    configs/gatekit.yaml                                      │    │
│  │                                                                 │    │
│  │  ✓ Generated Claude Desktop migration instructions             │    │
│  │    JSON snippet ready to copy                                  │    │
│  │                                                                 │    │
│  │  ✓ Generated Codex migration instructions                      │    │
│  │    CLI commands ready to copy                                  │    │
│  │                                                                 │    │
│  │  ⟳ Creating restore scripts...                                 │    │
│  │    Writing backup instructions                                 │    │
│  │                                                                 │    │
│  │  ○ Prepare final summary                                       │    │
│  │                                                                 │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Progress: [████████████████████░░░░░░░░] 75%                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Screen 6: Setup Complete
**Purpose:** Provide clear next steps and migration instructions

**Features:**
- Summary of what was created
- File paths with Copy/Open buttons
- Client-specific migration instructions (expandable)
- Clear next steps (restart clients)

**Mockup:**
```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Setup Complete!                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ✅ Gatekit has been successfully configured                        │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │ What was done:                                                 │    │
│  │                                                                 │    │
│  │ • Created Gatekit config with 4 servers                      │    │
│  │ • Generated Claude Desktop migration instructions              │    │
│  │ • Generated Codex migration instructions                       │    │
│  │ • Created restore scripts (optional rollback)                  │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │ Next Steps:                                                    │    │
│  │                                                                 │    │
│  │ 1. Follow the migration instructions below to update clients   │    │
│  │ 2. Restart each client after updating configuration            │    │
│  │ 3. Your MCP servers will now be managed by Gatekit!          │    │
│  │                                                                 │    │
│  │ Files Created:                                                 │    │
│  │ • Config: configs/gatekit.yaml         [Copy Path] [Open]    │    │
│  │ • Restore: ~/Documents/gatekit-restore [Copy Path] [Open]    │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │ Migration Instructions (expand each):                          │    │
│  │                                                                 │    │
│  │ ▶ Claude Desktop - Update configuration                        │    │
│  │ ▶ Codex - Run CLI commands                                     │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│                              [Done]                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Implementation Details

### Data Model Changes
```python
# Add to gatekit/tui/guided_setup/models.py
@dataclass
class GuidedSetupState:
    """Track state through guided setup wizard.

    Stores wizard state across screens. Deduplication happens once before
    Screen 2, so server names are stable throughout the flow.
    """
    detected_clients: List[DetectedClient]
    deduplicated_servers: List[DeduplicatedServer]  # Store deduplicated list
    selected_server_names: Set[str]  # Track selected names (stable after dedup)
    selected_client_types: Set[ClientType]  # Which clients to generate instructions for
    config_path: Optional[Path] = None
    restore_dir: Optional[Path] = None
    generate_restore: bool = False

    def update_deduplicated_servers(
        self,
        new_servers: List[DeduplicatedServer],
        new_clients: List[DetectedClient]
    ) -> None:
        """Update deduplicated servers and reconcile selections.

        Removes any selected names/types that no longer exist.
        Auto-selects NEWLY discovered servers and client types while preserving user opt-outs.
        This handles rescan scenarios where servers or clients may have changed.

        Args:
            new_servers: New list of deduplicated servers
            new_clients: New list of detected clients
        """
        # Capture old state before updating
        old_server_names = {s.server.name for s in self.deduplicated_servers}
        old_client_types = {c.client_type for c in self.detected_clients}

        # Update to new data
        self.deduplicated_servers = new_servers
        self.detected_clients = new_clients

        # Reconcile server selections
        valid_names = {s.server.name for s in new_servers}

        # Remove stale server selections (no longer detected)
        self.selected_server_names = self.selected_server_names & valid_names

        # Find truly NEW servers (not in previous deduplication)
        newly_discovered_servers = valid_names - old_server_names

        # Auto-select ONLY the newly discovered servers
        # This preserves user's intentional deselections from before
        self.selected_server_names = self.selected_server_names | newly_discovered_servers

        # Reconcile client type selections
        valid_client_types = {c.client_type for c in new_clients}

        # Remove stale client types (no longer detected)
        self.selected_client_types = self.selected_client_types & valid_client_types

        # Find truly NEW client types (not in previous detection)
        newly_detected_clients = valid_client_types - old_client_types

        # Auto-select ONLY the newly detected client types
        # This preserves user's intentional deselections from before
        self.selected_client_types = self.selected_client_types | newly_detected_clients
```

### Screen Navigation Flow
```
WelcomeScreen
  ↓ (Guided Setup)
DiscoveryScreen (auto-advance when complete)
  ↓
ServerSelectionScreen
  ↓
ClientMigrationScreen
  ↓
ConfigurationSummaryScreen
  ↓
SetupActionsScreen (auto-advance when complete)
  ↓
SetupCompleteScreen
```

### Server Deduplication Logic

**Purpose:** Present a clean, deduplicated view of servers to the user while handling conflicts gracefully.

**NOTE:** `DeduplicatedServer` must be defined in `gatekit/tui/guided_setup/models.py` alongside `DetectedServer` and `DetectedClient`.

**Approach:**
```python
import hashlib
from pathlib import Path

@dataclass
class DeduplicatedServer:
    """Represents a unique server after deduplication.

    NOTE: Must be defined in gatekit/tui/guided_setup/models.py
    """
    server: DetectedServer
    client_names: List[str]  # Which clients use this server (deduplicated)
    is_shared: bool  # True if used by multiple clients
    was_renamed: bool  # True if renamed due to conflict
    original_name: Optional[str] = None  # Original name if renamed

def _get_client_suffix(client_type: str) -> str:
    """Get short suffix for client type.

    Always returns a safe, title-case string even for unknown types.

    Args:
        client_type: Client type value (e.g., 'claude_desktop')

    Returns:
        Short suffix (e.g., 'desktop', 'code', 'codex')
    """
    suffixes = {
        "claude_desktop": "desktop",
        "claude_code": "code",
        "codex": "codex",
    }

    # Fallback: convert snake_case to title case for unknown types
    if client_type not in suffixes:
        return client_type.replace("_", "-").title()

    return suffixes[client_type]

def _generate_unique_suffix(
    server: DetectedServer,
    client_type: str,
    config_path: Path,
    used_names: set[str],
    base_name: str
) -> str:
    """Generate unique suffix incorporating client type, scope, and config hash.

    Args:
        server: The server being renamed
        client_type: Client type string
        config_path: Path to the client config file
        used_names: Set of already-used names
        base_name: Base server name

    Returns:
        Unique server name
    """
    parts = [base_name, _get_client_suffix(client_type)]

    # Add scope if available
    if server.scope:
        parts.append(server.scope.value)

    # Add short hash of config path for multi-profile disambiguation
    path_hash = hashlib.sha256(str(config_path).encode()).hexdigest()[:6]
    parts.append(path_hash)

    # Build candidate name
    candidate = "-".join(parts)

    # Add numeric increment if still not unique
    if candidate not in used_names:
        return candidate

    counter = 1
    while f"{candidate}-{counter}" in used_names:
        counter += 1

    return f"{candidate}-{counter}"

def deduplicate_servers(
    detected_clients: List[DetectedClient]
) -> List[DeduplicatedServer]:
    """
    Deduplicate servers across all detected clients.

    Process:
    1. Collect all servers from all clients with config paths
    2. Group by (name, transport, command, url, env, scope) to find true duplicates
    3. Deduplicate client names in each group
    4. Identify name conflicts (same name, different config)
    5. Resolve conflicts with scope + config hash + increment
    6. Return flat list with provenance metadata

    Returns:
        List of unique servers with metadata about sharing/conflicts
    """
    all_servers = []
    for client in detected_clients:
        for server in client.servers:
            all_servers.append((server, client.client_type.value, client.config_path))

    # Group identical servers - COMPLETE key including transport, url, scope
    server_groups = {}
    for server, client_name, config_path in all_servers:
        # Complete deduplication key
        key = (
            server.name,
            server.transport,  # Include transport
            tuple(server.command) if server.command else None,
            server.url,  # Include URL for HTTP servers
            frozenset(server.env.items()) if server.env else frozenset(),
            server.scope,  # Include scope for Claude Code
        )
        if key not in server_groups:
            server_groups[key] = {
                'server': server,
                'clients': [],
                'config_paths': []
            }
        server_groups[key]['clients'].append(client_name)
        server_groups[key]['config_paths'].append(config_path)

    # Deduplicate client lists (same config read twice, etc.)
    for group in server_groups.values():
        group['clients'] = list(dict.fromkeys(group['clients']))

    # Find name conflicts: same name but different key
    name_to_entries = {}
    for key, group in server_groups.items():
        name = key[0]  # First element is server name
        if name not in name_to_entries:
            name_to_entries[name] = []
        name_to_entries[name].append((key, group))

    conflicts = {name: entries for name, entries in name_to_entries.items() if len(entries) > 1}

    # Build deduplicated list with unique names
    result = []
    used_names = set()  # Track all names to prevent any duplicates

    for key, group in server_groups.items():
        server = group['server']
        clients = group['clients']
        config_paths = group['config_paths']
        original_name = server.name

        if server.name in conflicts:
            # Generate unique name
            new_name = _generate_unique_suffix(
                server,
                clients[0],
                config_paths[0],
                used_names,
                original_name
            )

            server = DetectedServer(
                name=new_name,
                transport=server.transport,
                command=server.command,
                url=server.url,
                env=server.env,
                scope=server.scope,
                raw_config=server.raw_config,
            )
            was_renamed = True
        else:
            was_renamed = False

        used_names.add(server.name)

        result.append(DeduplicatedServer(
            server=server,
            client_names=clients,
            is_shared=len(clients) > 1,
            was_renamed=was_renamed,
            original_name=original_name if was_renamed else None,
        ))

    return result
```

**UI Presentation:**
- Show flat list of deduplicated servers
- Display "Used by: X, Y" for servers found in multiple client configs
- Display "From: X" for servers found in single client config
- Show callout box at top if conflicts were resolved
- One checkbox per unique server = one server in final config

**Environment Variable Handling:**
- Env vars are NOT shown in the server selection UI
- Migration instructions will consolidate all env vars from selected servers
- Conflicts detected and warnings shown with masked values
- User applies consolidated env vars to the Gatekit entry in their client config
- Gatekit passes env vars to upstream servers via stdio process inheritance

**Environment Variable Consolidation Logic:**
```python
def _mask_env_value(key: str, value: str) -> str:
    """Mask sensitive environment variable values.

    Shows last 4 characters for debugging, masks the rest.

    Args:
        key: Environment variable name
        value: Environment variable value

    Returns:
        Masked value like "********abc123" or "********" for short values
    """
    if len(value) <= 4:
        return "********"
    return f"********{value[-4:]}"

def _collect_all_env_vars(servers: List[DetectedServer]) -> tuple[dict, list[str]]:
    """Collect all environment variables from all servers.

    Detects conflicts where the same key has different values across servers.
    Servers should be pre-sorted by name for deterministic conflict resolution
    (last server's value wins in case of conflicts).

    Args:
        servers: List of detected servers (pre-sorted by name for determinism)

    Returns:
        Tuple of (merged env vars dict, list of conflict warnings with masked values)
    """
    all_env_vars = {}
    conflicts = []
    env_sources = {}

    for server in servers:
        if server.has_env_vars():
            for key, value in server.env.items():
                if key in all_env_vars:
                    if all_env_vars[key] != value:
                        # Mask values in conflict warning
                        masked_existing = _mask_env_value(key, all_env_vars[key])
                        masked_new = _mask_env_value(key, value)
                        conflicts.append(
                            f"Environment variable '{key}' has different values:\n"
                            f"  • {env_sources[key]}: {masked_existing}\n"
                            f"  • {server.name}: {masked_new}\n"
                            f"  Using value from {server.name}"
                        )
                all_env_vars[key] = value
                env_sources[key] = server.name

    return all_env_vars, conflicts

# Usage in migration instruction helpers (e.g., _generate_claude_desktop_instructions):
def _generate_claude_desktop_instructions(
    client: DetectedClient,
    stdio_servers: List[DetectedServer],
    gatekit_gateway_path: Path,
    gatekit_config_path: Path,
) -> MigrationInstructions:
    """Generate Claude Desktop migration instructions (JSON snippet)."""

    # Sort servers by name for deterministic env var collection
    # (Within a single client's context, all servers belong to that client,
    # so we only need to sort by server name for determinism)
    stdio_servers_sorted = sorted(stdio_servers, key=lambda s: s.name)

    # Collect all env vars from sorted servers
    all_env_vars, env_conflicts = _collect_all_env_vars(stdio_servers_sorted)

    # Build gatekit entry with consolidated env vars
    gatekit_entry = {
        "gatekit": {
            "command": str(gatekit_gateway_path),
            "args": ["--config", str(gatekit_config_path)],
        }
    }

    if all_env_vars:
        gatekit_entry["gatekit"]["env"] = all_env_vars

    # Add env conflicts to instruction text if any
    conflict_warning = ""
    if env_conflicts:
        conflict_warning = "\n⚠ Environment Variable Conflicts:\n" + "\n".join(env_conflicts) + "\n"

    # ... rest of instruction generation
    # Format as JSON snippet
    snippet = json.dumps(gatekit_entry, indent=2)

    # SECURITY NOTE: The snippet contains plaintext env var values.
    # UI Handling:
    # - DO NOT display env var values in UI (use masked placeholders)
    # - Copy-to-clipboard IS safe (user explicitly requests full snippet)
    # - TextArea should show masked version: "API_KEY": "********xyz1"
    # - Clipboard gets real values for functional migration
    # OR alternatively:
    # - Show masked values in snippet, instruct user to manually replace
    #   with their existing secrets from original client config
```

**Benefits:**
- No ambiguity about what gets configured
- Clear provenance for every server
- Transparent conflict resolution
- Efficient use of Gatekit (shared servers serve multiple clients)
- Environment variables properly preserved through migration
- Env var conflicts detected with masked values for security
- Deterministic conflict resolution (servers sorted by name within each client's instructions)

### Key UX Principles

1. **Progressive Disclosure**
   - Show what we found before asking what to do with it
   - Build understanding at each step
   - Defer file path requests until the end

2. **Value Before Input**
   - User sees detected clients/servers before making choices
   - Configuration preview before file paths
   - Clear benefits before commitment

3. **Security & Transparency**
   - Never automatically modify client configs
   - Clear messaging about manual updates
   - Show exactly what will be created

4. **Sensible Defaults**
   - Pre-select all servers and clients
   - Provide good default file paths
   - Make restore scripts optional

5. **Clear Feedback**
   - Live progress during scanning
   - Visual indicators (checkmarks, warnings)
   - Descriptive status messages

## Benefits Over Current Implementation

1. **Better User Experience**
   - Feels like a helpful wizard, not a form
   - Users understand what they're getting before giving paths
   - Progressive revelation reduces cognitive load

2. **Increased Trust**
   - Transparent about what we're doing
   - User maintains control over their configs
   - Clear security messaging

3. **Reduced Confusion**
   - Each step has clear purpose
   - Visual hierarchy guides attention
   - Context provided before decisions

4. **Improved Success Rate**
   - Users less likely to abandon
   - Clear next steps reduce errors
   - Better understanding of Gatekit's role

## Testing Considerations

- Test partial selection scenarios (some servers, some clients)
- Verify no file operations until user confirms
- Test back navigation preserving selections
- Ensure cancellation at any point is safe
- Test with various client combinations (only Claude Desktop, only Codex, etc.)
- **Deduplication scenarios:**
  - Identical servers across clients (should show once, "Used by: X, Y")
  - Name conflicts with different configs (should auto-rename with scope + hash + increment)
  - Multi-profile scenarios (same client type, different config paths)
  - Mix of shared and unique servers
  - All servers identical across all clients
  - No shared servers (all unique)
  - HTTP servers with same name but different URLs (should be distinct)
  - Claude Code servers with same name but different scopes (user vs project)
- **Error handling:**
  - Parse errors displayed correctly with expand/collapse
  - Parse errors logged to telemetry
  - Failed servers excluded from selection
- **Environment variable conflicts:**
  - Conflicts detected and shown with masked values
  - Deterministic resolution (servers sorted by name within each client's context)
  - Conflicts shown in both summary screen and migration instructions
  - Credentials masked in UI display; plaintext only in clipboard (user-initiated copy)
- **Rescan functionality:**
  - Rescan button triggers fresh detection while preserving user intent
  - Works after user fixes config issues
  - `update_deduplicated_servers()` reconciles both server and client selections using identical diff logic:
    - **Servers**: Removed servers deselected, NEWLY discovered servers AUTO-SELECTED (preserves user opt-outs)
    - **Clients**: Removed clients deselected, NEWLY detected clients AUTO-SELECTED (preserves user opt-outs)
  - Smart logic compares old vs new to identify truly new additions vs re-discoveries
  - **Server selection test scenarios:**
    - **Scenario 1**: Scan finds A, B, C → all selected → user unchecks B → rescans with no changes → A & C selected, B STAYS UNCHECKED ✓
    - **Scenario 2**: Scan finds A, B → both selected → user adds server C to config → rescans → A, B, C all SELECTED ✓
    - **Scenario 3**: Scan finds A, B → both selected → user unchecks B → adds C → rescans → A & C selected, B STAYS UNCHECKED ✓
    - **Scenario 4**: Scan finds A, B → both selected → removes B from config → rescans → A selected, B REMOVED ✓
  - **Client selection test scenarios:**
    - **Scenario A**: Scan finds Desktop & Codex → both selected → user unchecks Codex → rescans → Desktop selected, Codex STAYS UNCHECKED ✓
    - **Scenario B**: Scan finds Desktop → selected → user adds Codex config → rescans → Desktop & Codex both SELECTED ✓
    - **Scenario C**: Scan finds Desktop & Codex → both selected → user unchecks Codex → adds Code config → rescans → Desktop & Code selected, Codex STAYS UNCHECKED ✓
    - **Scenario D**: Scan finds Desktop & Codex → both selected → removes Codex config → rescans → Desktop selected, Codex REMOVED ✓
- **HTTP/SSE server handling:**
  - Clearly communicated which servers are skipped
  - Counts match expectations (total vs. selectable)
- **Filesystem error recovery:**
  - Atomic operations with temp files
  - Proper cleanup on error
  - Clear recovery options presented to user
  - No silent failures or partial artifacts

## Future Enhancements

- Add connection testing before completion
- Support for HTTP/SSE servers when available
- Advanced mode for power users
- Import existing Gatekit configs
- Dry-run mode to preview changes
- Automatic backup of client configs before modification (when we add auto-update)
- Conflict resolution UI for env vars (let user choose which value to use)
- Export/import guided setup state for sharing between machines
- Enhanced rescan with per-server edit preservation (beyond current opt-out tracking)

## QC Review Addressed

This document incorporates feedback from multiple QC review rounds:

**Core Issues Fixed:**
1. ✅ Server name collision from same client type (added scope + config hash + increment)
2. ✅ Incomplete deduplication key (now includes transport, url, scope)
3. ✅ Mutable names in state tracking (changed to Set[str] with stable deduplication)
4. ✅ Parse errors not visible (added expandable error display)
5. ✅ Silent env var conflicts (detect + warn with masked values)

**QC Opportunities Incorporated:**
1. ✅ Rescan guidance added (button + instructions on Detection Complete screen)
2. ✅ HTTP/SSE server visibility strategy (clear messaging about skipped servers)
3. ✅ Partial progress error handling (atomic operations with cross-platform Path.replace(), cleanup strategy, recovery options)
4. ✅ Client list deduplication (prevent "Used by: X, X")
5. ✅ Deterministic client suffix fallback (handles unknown client types)
6. ✅ Collapsible UI for errors and conflicts (don't overwhelm happy path)
7. ✅ Telemetry logging for parse errors (UI and logs stay aligned)
8. ✅ Masked credential values in UI display (show last 4 chars); plaintext in clipboard for functional migration
9. ✅ Deterministic conflict resolution (servers sorted by name within each client)
10. ✅ Conflicts surfaced in both summary screen and migration instructions
11. ✅ Rescan reconciles selections with smart diff logic (both servers and clients: removes stale, auto-selects new, preserves opt-outs)
12. ✅ Connection testing moved to Future Enhancements (removed from Screen 6 mockup)
13. ✅ Secret handling in migration snippets documented (masked in UI, plaintext in clipboard OR masked with manual replacement instructions)