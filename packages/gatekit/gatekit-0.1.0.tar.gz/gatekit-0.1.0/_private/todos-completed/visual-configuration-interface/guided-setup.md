# Guided Setup Feature - Requirements & Implementation

## Overview

Implement an Guided Setup feature for Gatekit TUI that guides users through initial configuration by detecting MCP clients on their system and generating appropriate Gatekit configurations. This feature will be the primary onboarding path for new users.

**Core Principle**: Detect and generate, but never auto-modify user's MCP client configurations. Users maintain full control over their client configs.

## Path Conventions

- `<PROJECT_ROOT>`: Directory containing the Gatekit repository (e.g., `/Users/username/Projects/gatekit`, `/home/username/projects/gatekit`, `C:\Users\username\Projects\gatekit`).
- `<HOME_DIR>`: User's home directory (e.g., `/Users/username`, `/home/username`, `C:\Users\username`).
- `<DOCUMENTS_DIR>`: Platform-default documents folder (e.g., `/Users/username/Documents`, `/home/username/Documents`, `C:\Users\username\Documents`).
- `<USERNAME>`: Placeholder user account name used in examples; replace with the detected account when rendering copy.

**Display Rules:**
- All paths shown to users must be absolute. Do not surface `~`, `%VAR%`, or other environment tokens in UI copy.
- Internally we may rely on `Path.expanduser()` / environment variables for discovery, but expand them before displaying any snippet.
- Unless otherwise noted, examples reference `<PROJECT_ROOT>` and `<DOCUMENTS_DIR>` for generated files.

**Quick Reference:**
| Artifact | Default Location | Notes |
| --- | --- | --- |
| Generated Gatekit config | `<PROJECT_ROOT>/configs/gatekit.yaml` | Users can override via save dialog |
| Restore script directory | `<DOCUMENTS_DIR>/gatekit-restore` | Windows outputs `.txt`; macOS/Linux output `.sh` where applicable |
| Audit log (JSONL) | `<PROJECT_ROOT>/logs/audit.json` | Enabled by default in generated config |

## Requirements

### Functional Requirements

#### FR-1: First-Run Welcome Experience
- **When**: User has no recent files in their history
- **Behavior**: Display welcome card in place of Recent Files DataTable
- **Content**: See approved messaging below
- **Action**: Primary CTA to launch Guided Setup wizard

#### FR-2: Returning User Experience
- **When**: User has recent files in their history
- **Behavior**: Display Recent Files DataTable normally
- **Action**: Guided Setup remains available in button hierarchy

#### FR-3: Button Hierarchy
All states (first-run and returning) must present actions in this priority order:
1. **Start Guided Setup** - `$primary` variant (most prominent)
2. **Open File...** - `$secondary` variant (standard action)
3. **Create blank configuration** - Link style (de-emphasized)

#### FR-4: MCP Client Detection & Configuration Generation
- Detect MCP clients installed on user's system (MVP: Claude Desktop, Claude Code, Codex)
- Parse existing MCP server definitions from detected client configs
- **STDIO transport only** - Skip HTTP/SSE servers with warning message (not supported in this release)
- Generate valid Gatekit configuration containing all detected STDIO servers
- **Do NOT modify client configurations** - provide copy-paste snippets instead

#### FR-5: Guided Manual Client Updates
- Generate client-specific configuration snippets for each detected client
- Provide "Open in Editor" buttons to open client config files
- Show clear instructions with copyable text for each client
- Use TextArea widgets (read-only, syntax-highlighted) for config snippets
- Provide Test Connection feature to verify setup success

### Non-Functional Requirements

#### NFR-1: Brand Voice
- Authoritative, professional tone (not marketing-style)
- No emojis
- No exclamation points
- Clear, technical language

#### NFR-2: Visual Design
- Use Textual's built-in palette colors (`$primary`, `$secondary`)
- Follow existing Gatekit TUI design patterns
- Maintain consistency with rest of application

#### NFR-3: Accessibility
- Keyboard navigation throughout wizard
- Ability to exit/skip at any point

## Approved Workflow

### High-Level Flow
1. **Detection Phase**: Scan for MCP client config files on the system
2. **Parsing Phase**: Extract MCP server definitions from detected clients
3. **Generation Phase**: Create Gatekit config containing all detected servers
4. **Restore Script Generation**: Save restore scripts so users can easily revert
5. **Instruction Phase**: Show user how to migrate clients to Gatekit
   - **Remove** old servers from client
   - **Add** Gatekit to client
   - Use CLI commands for Claude Code and Codex
   - Use manual JSON editing for Claude Desktop
6. **Verification Phase**: Test connections to all configured MCP servers

**CRITICAL: Users must remove old servers and add Gatekit** to avoid duplicate tool registrations.

### Why No Auto-Modification?

**Security & Trust:**
- Modifying other applications' configs is risky and violates user expectations
- One parsing error could break user's working Claude Desktop setup
- Security-conscious users (our target audience) prefer explicit control

**Maintenance Burden:**
- Supporting 10-50 clients means maintaining dozens of parsers
- Client updates can break our modification logic
- Edge cases in each client's implementation

**Better Approach:**
- Generate copy-paste snippets users can review before applying
- Users understand and control what's changing
- Aligns with Gatekit's security-first principles

## Approved Design

### First-Run Welcome Card

```
┌──────────────────────────────────────────────────────────┐
│  No recent files                                         │
│                                                           │
│  Guided Setup can detect MCP clients on your system,   │
│  read their server configurations, and generate a        │
│  Gatekit config from them.                             │
│                                                           │
│         [   Start Guided Setup   ] ($primary)          │
│                                                           │
│  Alternatively, open an existing configuration or        │
│  create a new one from scratch.                          │
└──────────────────────────────────────────────────────────┘
```

### Button Layout (All States)

```
┌─────────────────────────────────────────────────────────┐
│  [  Start Guided Setup  ]  ($primary variant)         │
│                                                          │
│  [  Open File...  ]  ($secondary variant)               │
│                                                          │
│  or create a blank configuration (link)                 │
└─────────────────────────────────────────────────────────┘
```

### Setup Complete Screen

**Important Design Change:** Use CLI commands for Claude Code and Codex (which have CLI support), manual JSON editing only for Claude Desktop (which doesn't).

**Important Path Requirements:**
- ALL paths in generated snippets/commands/restore scripts MUST be absolute paths
- NO `~` expansion, NO `%VARIABLES%`, NO environment variables in generated output
- Use `Path.expanduser().resolve()` to expand all paths before displaying to user
- Rationale: `~` won't expand on Windows for these MCP clients, and absolute paths ensure reliability across all platforms
- Layouts below use placeholder tokens; see platform substitution tables for per-OS values

**Placeholder glossary:**
- `<CONFIG_PATH>` – Generated Gatekit config path (defaults to `<PROJECT_ROOT>/configs/gatekit.yaml`).
- `<RESTORE_DIR>` – Directory chosen for restore instructions (defaults to `<DOCUMENTS_DIR>/gatekit-restore`).
- `<RESTORE_SCRIPT_PATH>` – Full path to the client-specific restore script inside `<RESTORE_DIR>`.
- `<CLAUDE_DESKTOP_CONFIG_PATH>` – Detected Claude Desktop configuration file for the active platform.
- `<GATEKIT_GATEWAY_PATH>` – Absolute path returned by `locate_gatekit_gateway()`.

**Claude Desktop Example** (manual JSON editing; layout shared across platforms):
```
┌──────────────────────────────────────────────────────────────────┐
│  Setup Complete                                                  │
│                                                                  │
│  Gatekit configuration created:                               │
│  <CONFIG_PATH>                                                  │
│  [Copy Path]                                                    │
│                                                                  │
│  Restore instructions saved:                                     │
│  <RESTORE_DIR>/restore-claude-desktop.txt                        │
│  [Copy Path]                                                    │
│                                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                  │
│  Update Claude Desktop                                          │
│  <CLAUDE_DESKTOP_CONFIG_PATH>                                   │
│  [Open in Editor]  [Copy Path]                                 │
│                                                                  │
│  Servers to migrate (remove these from your config):            │
│  • filesystem                                                   │
│  • github                                                       │
│  • sqlite                                                       │
│                                                                  │
│  Add this to your mcpServers section:                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ {                                              (TextArea)   │ │
│  │   "gatekit": {                                           │ │
│  │     "command": "<GATEKIT_GATEWAY_PATH>",                │ │
│  │     "args": [                                              │ │
│  │       "--config",                                          │ │
│  │       "<CONFIG_PATH>"                                      │ │
│  │     ]                                                      │ │
│  │   }                                                        │ │
│  │ }                                                          │ │
│  └────────────────────────────────────────────────────────────┘ │
│  Select all (Ctrl+A) then copy (Ctrl+C)                        │
│                                                                  │
│  [Copy Config Snippet]                                          │
│                                                                  │
│  ⓘ To restore your original configuration later:               │
│     See <RESTORE_DIR>/restore-claude-desktop.txt                │
│     [Open Restore Instructions]                                 │
│                                                                  │
│  After editing config, restart Claude Desktop                   │
│                                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                  │
│  [Test All Connections]  [Done]                                 │
└──────────────────────────────────────────────────────────────────┘
```

**Platform substitutions:**
- **macOS**
  - `<CONFIG_PATH>` = `/Users/<USERNAME>/Projects/gatekit/configs/gatekit.yaml`
  - `<RESTORE_DIR>` = `/Users/<USERNAME>/Documents/gatekit-restore`
  - `<CLAUDE_DESKTOP_CONFIG_PATH>` = `/Users/<USERNAME>/Library/Application Support/Claude/claude_desktop_config.json`
  - `<GATEKIT_GATEWAY_PATH>` = `/usr/local/bin/gatekit-gateway` (example from `locate_gatekit_gateway()`)
- **Linux**
  - `<CONFIG_PATH>` = `/home/<USERNAME>/projects/gatekit/configs/gatekit.yaml`
  - `<RESTORE_DIR>` = `/home/<USERNAME>/Documents/gatekit-restore`
  - `<CLAUDE_DESKTOP_CONFIG_PATH>` = `/home/<USERNAME>/.config/Claude/claude_desktop_config.json`
  - `<GATEKIT_GATEWAY_PATH>` = `/usr/local/bin/gatekit-gateway` (example from `locate_gatekit_gateway()`)
- **Windows**
  - `<CONFIG_PATH>` = `C:\Users\<USERNAME>\Projects\gatekit\configs\gatekit.yaml`
  - `<RESTORE_DIR>` = `C:\Users\<USERNAME>\Documents\gatekit-restore`
  - `<CLAUDE_DESKTOP_CONFIG_PATH>` = `C:\Users\<USERNAME>\AppData\Roaming\Claude\claude_desktop_config.json`
  - `<GATEKIT_GATEWAY_PATH>` = `C:\Users\<USERNAME>\AppData\Roaming\Python\Python<version>\Scripts\gatekit-gateway.exe`

**Claude Code Example** (CLI commands; layout shared across macOS and Linux):
```
┌──────────────────────────────────────────────────────────────────┐
│  Setup Complete                                                  │
│                                                                  │
│  Gatekit configuration created:                               │
│  <CONFIG_PATH>                                                  │
│  [Copy Path]                                                    │
│                                                                  │
│  Restore script saved:                                           │
│  <RESTORE_SCRIPT_PATH>                                          │
│  [Copy Path]                                                    │
│                                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                  │
│  Update Claude Code                                             │
│                                                                  │
│  Servers detected (will be migrated to Gatekit):             │
│  • filesystem                                                   │
│  • github                                                       │
│  • sqlite                                                       │
│                                                                  │
│  Run these commands in your terminal:                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ # Remove original servers                    (TextArea)     │ │
│  │ claude mcp remove filesystem --scope user                  │ │
│  │ claude mcp remove github --scope user                      │ │
│  │ claude mcp remove sqlite --scope user                      │ │
│  │                                                            │ │
│  │ # Add Gatekit                                            │ │
│  │ claude mcp add --transport stdio --scope user \            │ │
│  │   gatekit -- <GATEKIT_GATEWAY_PATH> \                  │ │
│  │   --config <CONFIG_PATH>                                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  [Copy Commands]                                                │
│                                                                  │
│  ⓘ To restore your original configuration later:               │
│     bash <RESTORE_SCRIPT_PATH>                                  │
│     [Open Restore Script]                                       │
│                                                                  │
│  After running commands, restart Claude Code                    │
│                                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                  │
│  [Test All Connections]  [Done]                                 │
└──────────────────────────────────────────────────────────────────┘
```

**Platform substitutions:**
- **macOS**
  - `<CONFIG_PATH>` = `/Users/<USERNAME>/Projects/gatekit/configs/gatekit.yaml`
  - `<RESTORE_SCRIPT_PATH>` = `/Users/<USERNAME>/Documents/gatekit-restore/restore-claude-code.sh`
  - `<GATEKIT_GATEWAY_PATH>` = `/usr/local/bin/gatekit-gateway`
- **Linux**
  - `<CONFIG_PATH>` = `/home/<USERNAME>/projects/gatekit/configs/gatekit.yaml`
  - `<RESTORE_SCRIPT_PATH>` = `/home/<USERNAME>/Documents/gatekit-restore/restore-claude-code.sh`
  - `<GATEKIT_GATEWAY_PATH>` = `/usr/local/bin/gatekit-gateway`

**Claude Code Example** (Windows PowerShell layout):
```
┌──────────────────────────────────────────────────────────────────┐
│  Setup Complete                                                  │
│                                                                  │
│  Gatekit configuration created:                               │
│  <CONFIG_PATH>                                                  │
│  [Copy Path]                                                    │
│                                                                  │
│  Restore script saved:                                           │
│  <RESTORE_SCRIPT_PATH>                                          │
│  [Copy Path]                                                    │
│                                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                  │
│  Update Claude Code                                             │
│                                                                  │
│  Servers detected (will be migrated to Gatekit):             │
│  • filesystem                                                   │
│  • github                                                       │
│  • sqlite                                                       │
│                                                                  │
│  Run these commands in PowerShell:                (TextArea)    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ # Remove original servers                                  │ │
│  │ claude mcp remove filesystem --scope user                 │ │
│  │ claude mcp remove github --scope user                     │ │
│  │ claude mcp remove sqlite --scope user                     │ │
│  │                                                            │ │
│  │ # Add Gatekit                                           │ │
│  │ claude mcp add --transport stdio --scope user `           │ │
│  │   gatekit -- <GATEKIT_GATEWAY_PATH> `                 │ │
│  │   --config <CONFIG_PATH>                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│  NOTE: Python<version> shown as example (e.g., Python311, Python312). │
│  Implementation uses actual path from locate_gatekit_gateway().
│                                                                  │
│  [Copy Commands]                                                │
│                                                                  │
│  ⓘ To restore your original configuration later:               │
│     Open <RESTORE_SCRIPT_PATH> in Notepad and paste commands    │
│     into PowerShell                                             │
│     [Open Restore Instructions]                                 │
│                                                                  │
│  After running commands, restart Claude Code                    │
│                                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                  │
│  [Test All Connections]  [Done]                                 │
└──────────────────────────────────────────────────────────────────┘
```

**Platform substitutions:**
- `<CONFIG_PATH>` = `C:\Users\<USERNAME>\Projects\gatekit\configs\gatekit.yaml`
- `<RESTORE_SCRIPT_PATH>` = `C:\Users\<USERNAME>\Documents\gatekit-restore\restore-claude-code.txt`
- `<GATEKIT_GATEWAY_PATH>` = `C:\Users\<USERNAME>\AppData\Roaming\Python\Python<version>\Scripts\gatekit-gateway.exe`

**NOTE**: Line continuation syntax varies by platform:
- **macOS/Linux bash**: `\` (backslash)
- **Windows PowerShell**: `` ` `` (backtick)
- Implementation must detect platform and generate appropriate syntax
- These commands are shown in the main UI for immediate copy-paste into terminal
- Restore scripts use a different approach: `.sh` files for POSIX, `.txt` instructions for Windows

**Codex Example** (CLI commands; layout shared across macOS and Linux):
```
┌──────────────────────────────────────────────────────────────────┐
│  Setup Complete                                                  │
│                                                                  │
│  Gatekit configuration created:                               │
│  <CONFIG_PATH>                                                  │
│  [Copy Path]                                                    │
│                                                                  │
│  Restore script saved:                                           │
│  <RESTORE_SCRIPT_PATH>                                          │
│  [Copy Path]                                                    │
│                                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                  │
│  Update Codex                                                   │
│                                                                  │
│  Servers detected (will be migrated to Gatekit):             │
│  • filesystem                                                   │
│  • github                                                       │
│  • sqlite                                                       │
│                                                                  │
│  Run these commands in your terminal:                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ # Remove original servers                    (TextArea)     │ │
│  │ codex mcp remove filesystem                                │ │
│  │ codex mcp remove github                                    │ │
│  │ codex mcp remove sqlite                                    │ │
│  │                                                            │ │
│  │ # Add Gatekit                                            │ │
│  │ codex mcp add gatekit -- \                               │ │
│  │   <GATEKIT_GATEWAY_PATH> \                               │ │
│  │   --config <CONFIG_PATH>                                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  [Copy Commands]                                                │
│                                                                  │
│  ⓘ To restore your original configuration later:               │
│     bash <RESTORE_SCRIPT_PATH>                                  │
│     [Open Restore Script]                                       │
│                                                                  │
│  After running commands, restart Codex                          │
│                                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                  │
│  [Test All Connections]  [Done]                                 │
└──────────────────────────────────────────────────────────────────┘
```

**Platform substitutions:**
- **macOS**
  - `<CONFIG_PATH>` = `/Users/<USERNAME>/Projects/gatekit/configs/gatekit.yaml`
  - `<RESTORE_SCRIPT_PATH>` = `/Users/<USERNAME>/Documents/gatekit-restore/restore-codex.sh`
  - `<GATEKIT_GATEWAY_PATH>` = `/usr/local/bin/gatekit-gateway`
- **Linux**
  - `<CONFIG_PATH>` = `/home/<USERNAME>/projects/gatekit/configs/gatekit.yaml`
  - `<RESTORE_SCRIPT_PATH>` = `/home/<USERNAME>/Documents/gatekit-restore/restore-codex.sh`
  - `<GATEKIT_GATEWAY_PATH>` = `/usr/local/bin/gatekit-gateway`

**Codex Example** (Windows PowerShell layout):
```
┌──────────────────────────────────────────────────────────────────┐
│  Setup Complete                                                  │
│                                                                  │
│  Gatekit configuration created:                               │
│  <CONFIG_PATH>                                                  │
│  [Copy Path]                                                    │
│                                                                  │
│  Restore script saved:                                           │
│  <RESTORE_SCRIPT_PATH>                                          │
│  [Copy Path]                                                    │
│                                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                  │
│  Update Codex                                                   │
│                                                                  │
│  Servers detected (will be migrated to Gatekit):             │
│  • filesystem                                                   │
│  • github                                                       │
│  • sqlite                                                       │
│                                                                  │
│  Run these commands in PowerShell:                (TextArea)    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ # Remove original servers                                  │ │
│  │ codex mcp remove filesystem                                │ │
│  │ codex mcp remove github                                    │ │
│  │ codex mcp remove sqlite                                    │ │
│  │                                                            │ │
│  │ # Add Gatekit                                           │ │
│  │ codex mcp add gatekit -- `                               │ │
│  │   <GATEKIT_GATEWAY_PATH> `                               │ │
│  │   --config <CONFIG_PATH>                                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  [Copy Commands]                                                │
│                                                                  │
│  ⓘ To restore your original configuration later:               │
│     Open <RESTORE_SCRIPT_PATH> in Notepad and paste commands    │
│     into PowerShell                                             │
│     [Open Restore Instructions]                                 │
│                                                                  │
│  After running commands, restart Codex                          │
│                                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                                  │
│  [Test All Connections]  [Done]                                 │
└──────────────────────────────────────────────────────────────────┘
```

**Platform substitutions:**
- `<CONFIG_PATH>` = `C:\Users\<USERNAME>\Projects\gatekit\configs\gatekit.yaml`
- `<RESTORE_SCRIPT_PATH>` = `C:\Users\<USERNAME>\Documents\gatekit-restore\restore-codex.txt`
- `<GATEKIT_GATEWAY_PATH>` = `C:\Users\<USERNAME>\AppData\Roaming\Python\Python<version>\Scripts\gatekit-gateway.exe`

**NOTE**: Same line continuation differences apply for Codex (bash `\` vs PowerShell `` ` ``). Main UI snippets use platform-appropriate syntax; restore files use `.sh` for POSIX and `.txt` paste instructions for Windows.

### Restore Script Save Dialog

After the user saves the Gatekit config, show a dialog to choose where to save restore scripts:

```
┌────────────────────────────────────────────────────────────────┐
│  Save Restore Instructions                                     │
│                                                                │
│  We'll create restore scripts so you can easily revert        │
│  to your original configuration if needed.                     │
│                                                                │
│  Save restore scripts to:                                     │
│  [/Users/username/Documents/gatekit-restore/      ] [Browse]│
│                                                                │
│  Files that will be created:                                  │
│  • restore-claude-desktop.txt                                 │
│  • restore-claude-code.sh (or .txt on Windows)                │
│  • restore-codex.sh (or .txt on Windows)                      │
│                                                                │
│  [Save Here]  [Skip - Don't Save Restore Scripts]            │
└────────────────────────────────────────────────────────────────┘
```

**Default Location (expanded to absolute path):**
- macOS: `/Users/username/Documents/gatekit-restore/`
- Linux: `/home/username/Documents/gatekit-restore/`
- Windows: `C:\Users\username\Documents\gatekit-restore\`

**Why this location:**
- ✅ Unlikely to be deleted accidentally (not in config directory)
- ✅ Easy to find (in Documents folder)
- ✅ Backed up by Time Machine/OneDrive/cloud services
- ✅ Survives Gatekit uninstall
- ✅ User-accessible and readable

**Allow Skip:**
Some users may not want restore scripts (e.g., comfortable manually reverting). Don't force it.

### Restore Script Examples

**IMPORTANT**: All paths in restore scripts are expanded to absolute paths (no `~` or environment variables) to ensure they work correctly across all platforms.

**Platform Considerations:**
- **Claude Desktop**: `.txt` file with instructions - platform-independent (user manually edits JSON)
- **Claude Code/Codex**: Platform-specific approach to avoid Windows execution policy issues:
  - **macOS/Linux**: `.sh` executable shell scripts (bash syntax with `\` line continuation)
  - **Windows**: `.txt` files with PowerShell commands (backtick syntax, user pastes into terminal)
- Rationale for Windows text files:
  - Avoids PowerShell execution policy issues (`.ps1` files blocked by default)
  - Pasting commands into PowerShell terminal has no restrictions
  - Cleaner than `.cmd` batch files with limited syntax
  - Consistent with Claude Desktop approach (text instructions)

**For Claude Desktop** (`restore-claude-desktop.txt`):
```
Gatekit Restore Instructions for Claude Desktop
Generated: 2025-01-16 14:30:00

SECURITY WARNING: This file contains environment variables (API keys, tokens)
from your original configuration. Store this file securely.

To restore your original configuration:

1. Open your Claude Desktop config file:
   /Users/username/Library/Application Support/Claude/claude_desktop_config.json

2. Remove the "gatekit" entry from mcpServers

3. Add back your original servers (copy this JSON):

{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "ghp_1234567890abcdef"
      }
    },
    "sqlite": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite"]
    }
  }
}

4. Restart Claude Desktop
```

**For Claude Code macOS/Linux** (`restore-claude-code.sh`):
```bash
#!/bin/bash
# Gatekit Restore Commands for Claude Code
# Generated: 2025-01-16 14:30:00
#
# SECURITY WARNING: This script contains environment variables (API keys, tokens)
# from your original configuration. Store this file securely.
#
# Run this script to restore your original MCP server configuration
# and remove Gatekit.

echo "Removing Gatekit..."
claude mcp remove gatekit --scope user

echo "Restoring original servers..."
claude mcp add --transport stdio --scope user filesystem -- \
  npx -y @modelcontextprotocol/server-filesystem /tmp

# Restoring github server with original environment variable
claude mcp add --transport stdio --scope user github \
  --env GITHUB_TOKEN=ghp_1234567890abcdef \
  -- npx -y @modelcontextprotocol/server-github

claude mcp add --transport stdio --scope user sqlite -- \
  npx -y @modelcontextprotocol/server-sqlite

echo "Done! Restart Claude Code to see changes."
```

**For Claude Code Windows** (`restore-claude-code-windows.txt`):
```
Gatekit Restore Commands for Claude Code (Windows)
Generated: 2025-01-16 14:30:00

SECURITY WARNING: These commands contain environment variables (API keys, tokens)
from your original configuration. Store this file securely.

INSTRUCTIONS:
1. Open PowerShell (search for "PowerShell" in Start menu)
2. Copy the commands below
3. Paste into PowerShell window and press Enter
4. Restart Claude Code when complete

COMMANDS TO PASTE:

# Remove Gatekit
claude mcp remove gatekit --scope user

# Restore original servers
claude mcp add --transport stdio --scope user filesystem -- `
  npx -y @modelcontextprotocol/server-filesystem C:\tmp

# Restoring github server with original environment variable
claude mcp add --transport stdio --scope user github `
  --env GITHUB_TOKEN=ghp_1234567890abcdef `
  -- npx -y @modelcontextprotocol/server-github

claude mcp add --transport stdio --scope user sqlite -- `
  npx -y @modelcontextprotocol/server-sqlite

Write-Host "Done! Restart Claude Code to see changes."
```

**For Codex macOS/Linux** (`restore-codex.sh`):
```bash
#!/bin/bash
# Gatekit Restore Commands for Codex
# Generated: 2025-01-16 14:30:00
#
# SECURITY WARNING: This script contains environment variables (API keys, tokens)
# from your original configuration. Store this file securely.

echo "Removing Gatekit..."
codex mcp remove gatekit

echo "Restoring original servers..."
codex mcp add filesystem -- \
  npx -y @modelcontextprotocol/server-filesystem /tmp

# Restoring github server with original environment variable
codex mcp add github \
  --env GITHUB_TOKEN=ghp_1234567890abcdef \
  -- npx -y @modelcontextprotocol/server-github

codex mcp add sqlite -- \
  npx -y @modelcontextprotocol/server-sqlite

echo "Done! Restart Codex to see changes."
```

**For Codex Windows** (`restore-codex-windows.txt`):
```
Gatekit Restore Commands for Codex (Windows)
Generated: 2025-01-16 14:30:00

SECURITY WARNING: These commands contain environment variables (API keys, tokens)
from your original configuration. Store this file securely.

INSTRUCTIONS:
1. Open PowerShell (search for "PowerShell" in Start menu)
2. Copy the commands below
3. Paste into PowerShell window and press Enter
4. Restart Codex when complete

COMMANDS TO PASTE:

# Remove Gatekit
codex mcp remove gatekit

# Restore original servers
codex mcp add filesystem -- `
  npx -y @modelcontextprotocol/server-filesystem C:\tmp

# Restoring github server with original environment variable
codex mcp add github `
  --env GITHUB_TOKEN=ghp_1234567890abcdef `
  -- npx -y @modelcontextprotocol/server-github

codex mcp add sqlite -- `
  npx -y @modelcontextprotocol/server-sqlite

Write-Host "Done! Restart Codex to see changes."
```

## Implementation Plan

### Phase 1: Welcome Screen Updates

**Tasks:**
- [ ] Add state detection for "has recent files"
- [ ] Create `FirstRunWelcome` component/container
  - [ ] Heading: "No recent files"
  - [ ] Body text explaining Guided Setup + backup reassurance
  - [ ] Primary CTA button
  - [ ] Alternative actions text
- [ ] Implement conditional rendering in `WelcomeScreen`
  - [ ] If no recent files: render `FirstRunWelcome`
  - [ ] If recent files exist: render `RecentFilesDataTable`
- [ ] Update button hierarchy
  - [ ] Reorder: Guided Setup → Open File → Create New
  - [ ] Apply `$primary` variant to Guided Setup button
  - [ ] Apply `$secondary` variant to Open File button
  - [ ] Convert Create New to link style

### Phase 2: MCP Client Detection

**Initial Supported Clients** (MVP - first release):
1. Claude Desktop (JSON format)
2. Claude Code (JSON format)
3. Codex (TOML format)

**Tasks:**
- [ ] Implement client detection for Claude Desktop
  - [ ] macOS: `<HOME_DIR>/Library/Application Support/Claude/claude_desktop_config.json`
  - [ ] Linux: `<HOME_DIR>/.config/Claude/claude_desktop_config.json`
  - [ ] Windows: `%APPDATA%\Claude\claude_desktop_config.json` (displays as `C:\Users\<USERNAME>\AppData\Roaming\Claude\claude_desktop_config.json`)
- [ ] Implement client detection for Claude Code
  - [ ] User-level: `<HOME_DIR>/.claude.json` (primary)
  - [ ] Project-level: `.mcp.json` (secondary)
  - [ ] Parse JSON with `mcpServers` section (same as Claude Desktop)
  - [ ] Track which file had servers (needed for correct `--scope` in CLI commands)
- [ ] Implement client detection for Codex
  - [ ] User-level: `<HOME_DIR>/.codex/config.toml` (or `$CODEX_HOME/config.toml`)
  - [ ] Parse TOML with `[mcp_servers.server_name]` sections
  - [ ] Handle TOML-specific quirks (underscore in section name, inline table syntax)
- [ ] Parse client configs
  - [ ] JSON parsing for Claude Desktop & Claude Code
  - [ ] TOML parsing for Codex (using tomllib/tomli)
  - [ ] Extract server definitions from both formats
  - [ ] Handle both command+args and url formats
  - [ ] Validate required fields and skip invalid servers
- [ ] Implement fallback detection logic
  - [ ] Try multiple paths per client
  - [ ] Gracefully handle missing/malformed configs
  - [ ] Log detailed errors for debugging
- [ ] Locate gatekit-gateway using robust fallback strategy
  - [ ] Strategy 1: Check if sibling to sys.executable (venv, pipx)
  - [ ] Strategy 2: Search PATH with shutil.which (--user, system installs)
  - [ ] Prefer sibling location when both exist
  - [ ] Show clear error if neither strategy finds it
  - [ ] Use full absolute path in generated snippets

### Phase 3: Configuration Generation

**Default Plugin Configuration** (applied automatically):
- **Auditing**: JSON lines logger only (minimal, observable, no config needed)
- **Security**: None (explicit opt-in after users understand the tool)
- **Middleware**: None (let users add as needed)

**Tasks:**
- [ ] Create Gatekit config generator
  - [ ] Convert detected servers to UpstreamConfig format
  - [ ] **CRITICAL**: Filter out HTTP/SSE servers (stdio only in this release)
  - [ ] Track skipped HTTP servers and show informational message to user
  - [ ] **CRITICAL**: Include environment variables with actual values from client configs
  - [ ] Add warning comment in generated YAML about plaintext secrets
  - [ ] Apply default plugin configuration (JSON lines logger)
  - [ ] Generate valid YAML output
  - [ ] Validate generated configuration using ConfigLoader
- [ ] Show informational message if HTTP servers were skipped
  - [ ] Display message: "Found N HTTP/SSE servers (server1, server2) - skipped (not supported in this release)"
  - [ ] This is informational only - no user action required
  - [ ] **Implementation example:**
    ```python
    client = detect_claude_code()

    # Get only supported servers for config generation
    stdio_servers = client.get_stdio_servers()  # These will be in the generated config

    # Get skipped servers for user notification
    http_servers = client.get_http_servers()
    if http_servers:
        names = ", ".join(s.name for s in http_servers)
        show_info(f"Found {len(http_servers)} HTTP/SSE servers ({names}) - skipped (not supported in this release)")
    ```
- [ ] Show security warning if env vars detected
  - [ ] Display before config generation: "Your configuration contains environment variables (API keys, tokens). These will be included in the Gatekit config in plaintext. Consider using a secrets manager for production use."
  - [ ] Allow user to continue or cancel
- [ ] Show file save dialog with smart default
  - [ ] Default: `configs/gatekit.yaml` (in current directory)
  - [ ] Allow user to choose location
- [ ] Show restore script save dialog (separate from config save)
  - [ ] Default: `<DOCUMENTS_DIR>/gatekit-restore/` (platform-specific)
  - [ ] Allow user to choose different location
  - [ ] Allow user to skip (don't force restore scripts)
  - [ ] List which restore files will be created based on detected clients
- [ ] Generate restore scripts for each detected client
  - [ ] For Claude Desktop: Generate `.txt` file with manual instructions (platform-independent)
  - [ ] For Claude Code: Generate platform-specific restore file
    - [ ] macOS/Linux: `.sh` executable script with bash syntax (`\` line continuation)
    - [ ] Windows: `.txt` file with PowerShell commands and paste instructions (`` ` `` line continuation)
  - [ ] For Codex: Generate platform-specific restore file
    - [ ] macOS/Linux: `.sh` executable script with bash syntax
    - [ ] Windows: `.txt` file with PowerShell commands and paste instructions
  - [ ] Include timestamp in each restore file
  - [ ] **CRITICAL**: Preserve original server definitions including env vars with actual values
  - [ ] Include security warning comment at top of each restore file about plaintext secrets
  - [ ] Generate complete restore commands with `--env KEY=value` for servers that had env vars
  - [ ] Use appropriate `--scope` flag for Claude Code based on where servers were found
  - [ ] Use absolute paths in all restore scripts (same requirement as snippets)
  - [ ] Windows .txt files should include clear numbered instructions for pasting into PowerShell
- [ ] Generate client-specific migration instructions
  - [ ] For Claude Desktop: JSON snippet with servers to remove + Gatekit to add
  - [ ] For Claude Code: CLI commands to remove old servers + add Gatekit
  - [ ] For Codex: CLI commands to remove old servers + add Gatekit
  - [ ] Include list of servers being migrated
  - [ ] **CRITICAL**: Expand ALL paths to absolute paths (no `~`, `%VAR%`, or env vars)
  - [ ] Use `Path.expanduser().resolve()` for all file paths in snippets
  - [ ] Use absolute path for gatekit-gateway command from `locate_gatekit_gateway()`
  - [ ] Use absolute path for Gatekit config file location
  - [ ] **CRITICAL**: Generate platform-specific line continuation syntax
    - [ ] macOS/Linux: Use `\` (backslash) for bash/zsh
    - [ ] Windows: Use `` ` `` (backtick) for PowerShell
    - [ ] Detect platform via `platform.system()`
  - [ ] Format with syntax highlighting (JSON for Desktop, bash/PowerShell for Code/Codex)
- [ ] Save generated configuration
- [ ] Save restore scripts (if user didn't skip)
- [ ] Add to recent files list

### Phase 4: Wizard UI & Instructions Screen

**Single-Step Wizard** (simpler, less overwhelming):
- Detect all clients automatically
- Generate config immediately
- Show complete instructions screen with client-specific commands

**Tasks:**
- [ ] Create Setup Complete screen (ModalScreen)
  - [ ] Header: "Setup Complete"
  - [ ] Gatekit config path display with [Copy Path] button
  - [ ] Restore script path display with [Copy Path] button (if saved)
  - [ ] Section dividers between each client
- [ ] For each detected client, generate appropriate UI:
  - [ ] **Claude Desktop** (manual JSON editing):
    - [ ] Show config file path
    - [ ] [Open in Editor] button using platform-specific commands
    - [ ] [Copy Path] button for config file location
    - [ ] List of "Servers to migrate (remove these)"
    - [ ] TextArea widget with JSON snippet (read-only, JSON syntax highlighting)
    - [ ] [Copy Config Snippet] button using `app.copy_to_clipboard()`
    - [ ] Instruction text: "Select all (Ctrl+A) then copy (Ctrl+C)"
    - [ ] Link to restore instructions with [Open Restore Instructions] button
  - [ ] **Claude Code** (CLI commands):
    - [ ] List of "Servers detected (will be migrated)"
    - [ ] TextArea widget with bash commands (read-only, bash syntax highlighting)
    - [ ] Include `claude mcp remove` commands for each detected server
    - [ ] Include `claude mcp add` command for Gatekit with correct `--scope`
    - [ ] [Copy Commands] button using `app.copy_to_clipboard()`
    - [ ] Link to restore script with [Open Restore Script] button
  - [ ] **Codex** (CLI commands):
    - [ ] List of "Servers detected (will be migrated)"
    - [ ] TextArea widget with bash commands (read-only, bash syntax highlighting)
    - [ ] Include `codex mcp remove` commands for each detected server
    - [ ] Include `codex mcp add` command for Gatekit
    - [ ] [Copy Commands] button using `app.copy_to_clipboard()`
    - [ ] Link to restore script with [Open Restore Script] button
- [ ] Show "After running commands, restart [Client Name]" for each client
- [ ] Bottom action buttons:
  - [ ] [Test All Connections] - Primary variant
  - [ ] [Done] - Secondary variant
- [ ] Implement keyboard navigation
  - [ ] Tab between buttons
  - [ ] Escape to exit
  - [ ] Enter to activate focused button

### Phase 5: Connection Testing

**Reuse Existing Logic** from `ConfigEditorScreen`:
- `_handshake_upstream(upstream)` - Core handshake + tool discovery
- `_discover_identity_for_upstream(upstream)` - Wrapper with error handling
- `_fetch_tools_list(transport)` - Gets tool catalog

**Tasks:**
- [ ] Create server connection testing utility (if extracting)
  - [ ] Or directly reuse `_handshake_upstream` from ConfigEditorScreen
  - [ ] Test single server connection
  - [ ] Test multiple servers in parallel
- [ ] Implement Test All Connections button
  - [ ] For each server: show status (✓ connected / ✗ failed)
  - [ ] Show results summary (X successful, Y failed)
  - [ ] Provide [View Details] for failures
  - [ ] Allow [Continue Anyway] or [Go Back]
- [ ] Handle connection test results
  - [ ] Store identity for successful connections
  - [ ] Show error messages for failures
  - [ ] Update Gatekit config with discovered identities

### Phase 6: Error Handling & Edge Cases

**Tasks:**
- [ ] Handle no clients detected
  - [ ] Show message: "No MCP clients detected"
  - [ ] Offer "Create blank configuration" option
  - [ ] Provide list of supported clients
- [ ] Handle parsing errors in client configs
  - [ ] Show which client config failed to parse
  - [ ] Offer to skip that client and continue
  - [ ] Log parsing errors for debugging
- [ ] Handle file system errors
  - [ ] Permission denied opening config files
  - [ ] Config file doesn't exist at expected location
  - [ ] Unable to write Gatekit config
- [ ] Handle editor opening failures
  - [ ] Editor not configured or available
  - [ ] File is locked by running application
  - [ ] Fall back to showing file path only
- [ ] Provide clear error messages
- [ ] Allow user to retry or choose alternative path

### Phase 7: Testing & Polish

**Tasks:**
- [ ] Write unit tests for detection logic (~15-20 tests)
- [ ] Write unit tests for configuration generation
- [ ] Write automated integration tests (~20 tests) using test harness
  - [ ] Convert Tier 3-6 manual scenarios to automated tests
  - [ ] Use `tempfile.TemporaryDirectory()` for fake client configs
  - [ ] Test detection, parsing, generation, error handling
  - [ ] Ensure all tests run in CI
- [ ] Manual smoke testing (5-7 scenarios)
  - [ ] One happy path per client (3 tests)
  - [ ] Platform-specific UI checks (editor opening, file dialogs on macOS/Linux/Windows)
  - [ ] Overall wizard UX flow validation
  - [ ] TextArea copy functionality and clipboard interactions
- [ ] Update documentation

## Testing Strategy

### The Challenge: Combinatorial Explosion

Supporting 3 MCP clients across 3 platforms with multiple configuration variations could theoretically create **864+ test cases** if we tried to test every combination:

- 3 clients (Claude Desktop, Claude Code, Codex)
- × 3 platforms (macOS, Linux, Windows)
- × 6 server config types (stdio, HTTP, absolute paths, relative paths, with/without env vars, etc.)
- × 4 config file states (exists, missing, malformed, empty)
- × 4 user action paths (skip test, pass test, fail+continue, fail+cancel)
- = **864 test cases**

This is completely impractical and would create an unmaintainable test suite.

### Tiered Testing Approach

Instead, use a strategic tiered approach that provides high confidence with manageable test count:

#### **Tier 1: Core Happy Path** (3 tests)
Test each client once on their primary platform with ideal conditions:

```
1. Claude Desktop + macOS + simple stdio servers → success
2. Claude Code + macOS + simple stdio servers → success
3. Codex + macOS + simple stdio servers → success
```

**Coverage**: Every client tested at least once with basic functionality

#### **Tier 2: Platform Variations** (3 tests)
Test platform-specific concerns with ONE representative client (Claude Desktop):

```
6. macOS: config path detection, editor opening
7. Linux: config path detection, editor opening
8. Windows: config path detection, editor opening, backslash handling
```

**Coverage**: Platform-specific logic thoroughly tested without repeating for every client

**Note**: gatekit-gateway path resolution (via sibling check + PATH fallback) is platform-independent and covered by automated unit tests, not manual platform testing.

#### **Tier 3: Server Configuration Edge Cases** (8 tests)
Test problematic server configs with ONE representative client:

```
9. Relative paths in command → skip with warning
10. Environment variables → include server WITH env vars and actual values, show security warning
11. Conflicting server names across clients → rename with suffix
12. Server name needs sanitization → sanitize
13. Complex args with spaces/quotes → preserve correctly
14. Invalid command (not in PATH) → connection test fails
15. Mix of valid and invalid servers → process both appropriately
16. HTTP transport → skip with "future release" message
```

**Coverage**: All server configuration edge cases handled correctly

**Note on test #10**: "Environment variable handling" means verifying that when a server HAS env vars in the client config, we:
- ✅ Include the server's command/args in generated Gatekit config
- ✅ Include the env vars section WITH actual values
- ✅ Show security warning about plaintext secrets before config generation
- ✅ Add warning comment in generated YAML about plaintext secrets

#### **Tier 4: File System Edge Cases** (6 tests)

```
17. Client config missing → "no clients detected" message
18. Client config malformed JSON → skip that client, warn
19. Client config unreadable → skip that client, warn
20. Existing Gatekit config → file dialog warns on overwrite
21. Save to custom path → respects user choice
22. User cancels file save → returns to welcome screen
```

**Coverage**: All file system error conditions handled gracefully

#### **Tier 5: User Flow Variations** (4 tests)

```
23. User skips connection test → proceeds to file save
24. Connection test fails, user continues → proceeds to file save
25. Connection test fails, user cancels → returns to welcome screen
26. Connection test passes → proceeds to file save
```

**Coverage**: All user decision paths tested

#### **Tier 6: Multi-Client Scenarios** (3 tests)

```
27. Multiple clients detected → merges all servers
28. Same server name in multiple clients → renames appropriately
29. No clients detected → shows message with manual setup option
```

**Coverage**: Complex multi-client interactions validated

### **Total: ~27 Strategic Tests**

This approach provides:
- ✅ Every client tested at least once
- ✅ Every platform tested thoroughly
- ✅ Every edge case covered
- ✅ Every user flow path validated
- ✅ Manageable test suite size (~27 vs 864)

**Note**: These are primarily manual/integration tests. Core business logic (parsing, generation, sanitization, path resolution) should have ~15-20 automated unit tests in addition to these strategic tests.

### Automated Unit Tests

In addition to the strategic manual tests above, the following logic should be covered by automated unit tests (~15-20 tests):

```python
# Core parsing and generation logic
- test_client_config_parsing_valid_json()
- test_client_config_parsing_malformed_json()
- test_client_config_parsing_missing_mcpservers()
- test_server_name_sanitization_invalid_chars()
- test_server_name_conflict_resolution_renames_with_suffix()
- test_env_vars_included_in_generated_config()
- test_env_vars_preserved_with_actual_values()
- test_security_warning_shown_when_env_vars_detected()
- test_relative_paths_detection()
- test_http_transport_detection()
- test_gatekit_config_generation_valid_yaml()
- test_gatekit_config_validates_with_configloader()
- test_complex_args_with_spaces_preserved()
- test_multiple_clients_servers_merged()
- test_duplicate_servers_across_clients_renamed()

# gatekit-gateway path resolution (robust fallback)
- test_gatekit_gateway_located_as_sibling_posix()
- test_gatekit_gateway_located_as_sibling_windows()
- test_gatekit_gateway_located_via_path()
- test_gatekit_gateway_prefers_sibling_over_path()
- test_gatekit_gateway_absolute_path_used_in_snippet()
- test_gatekit_gateway_missing_shows_error()

# Edge cases
- test_empty_mcp_servers_section_handled()
- test_permission_errors_caught_gracefully()
```

**Example test demonstrating env var inclusion:**

```python
def test_env_vars_included_in_generation():
    """Verify servers with env vars are included WITH the env section and values"""
    client_config = {
        "mcpServers": {
            "github": {
                "command": "npx",
                "args": ["@modelcontextprotocol/server-github"],
                "env": {"GITHUB_TOKEN": "secret123"}
            }
        }
    }

    generated_config = generate_gatekit_config(client_config)

    # Assert command/args present
    assert generated_config["upstreams"][0]["command"] == ["npx", "@modelcontextprotocol/server-github"]
    # Assert env IS present in generated config with actual values
    assert "env" in generated_config["upstreams"][0]
    assert generated_config["upstreams"][0]["env"]["GITHUB_TOKEN"] == "secret123"
```

**Example test for gatekit-gateway path resolution:**

```python
def test_gatekit_gateway_located_as_sibling_posix(tmp_path):
    """Locate gatekit-gateway when it's a sibling of sys.executable (POSIX)"""
    # Create fake bin directory structure (like venv)
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_gateway = fake_bin / "gatekit-gateway"
    fake_gateway.touch()

    # Mock sys.executable to point to our fake bin
    with patch("sys.executable", str(fake_bin / "python")):
        with patch("shutil.which", return_value=None):  # PATH search fails
            gateway_path = locate_gatekit_gateway()

    assert gateway_path == fake_gateway
    assert gateway_path.exists()

def test_gatekit_gateway_located_as_sibling_windows(tmp_path):
    """Locate gatekit-gateway.exe when it's a sibling of sys.executable (Windows)"""
    # Create fake Scripts directory structure (like Windows venv)
    fake_scripts = tmp_path / "Scripts"
    fake_scripts.mkdir()
    fake_gateway = fake_scripts / "gatekit-gateway.exe"
    fake_gateway.touch()

    # Mock sys.executable to point to our fake Scripts
    with patch("sys.executable", str(fake_scripts / "python.exe")):
        with patch("shutil.which", return_value=None):  # PATH search fails
            gateway_path = locate_gatekit_gateway()

    assert gateway_path == fake_gateway
    assert gateway_path.exists()

def test_gatekit_gateway_located_via_path(tmp_path):
    """Locate gatekit-gateway via PATH when not a sibling (like --user install)"""
    # Create fake structure where gateway is NOT a sibling
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_local_bin = tmp_path / ".local" / "bin"
    fake_local_bin.mkdir(parents=True)
    fake_gateway = fake_local_bin / "gatekit-gateway"
    fake_gateway.touch()

    # sys.executable is in different directory than gatekit-gateway
    with patch("sys.executable", str(fake_bin / "python")):
        with patch("shutil.which", return_value=str(fake_gateway)):
            gateway_path = locate_gatekit_gateway()

    assert gateway_path == fake_gateway
    assert gateway_path.exists()

def test_gatekit_gateway_prefers_sibling_over_path(tmp_path):
    """Prefer sibling location over PATH when both exist"""
    # Create two possible locations
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    sibling_gateway = fake_bin / "gatekit-gateway"
    sibling_gateway.touch()

    other_gateway = tmp_path / "other" / "gatekit-gateway"
    other_gateway.parent.mkdir(parents=True)
    other_gateway.touch()

    # Both exist, but prefer sibling
    with patch("sys.executable", str(fake_bin / "python")):
        with patch("shutil.which", return_value=str(other_gateway)):
            gateway_path = locate_gatekit_gateway()

    # Should prefer the sibling
    assert gateway_path == sibling_gateway

def test_gatekit_gateway_absolute_path_used_in_snippet():
    """Generated snippet should use absolute path from installation"""
    snippet = generate_client_snippet(
        gatekit_gateway_path="/usr/local/bin/gatekit-gateway",
        config_path="/home/user/gatekit.yaml"
    )

    assert snippet["gatekit"]["command"] == "/usr/local/bin/gatekit-gateway"
    assert snippet["gatekit"]["args"] == ["--config", "/home/user/gatekit.yaml"]

def test_gatekit_gateway_missing_shows_error(tmp_path):
    """If gatekit-gateway not found by any strategy, show clear error"""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    # Don't create gatekit-gateway anywhere

    with patch("sys.executable", str(fake_bin / "python")):
        with patch("shutil.which", return_value=None):  # PATH search fails too
            with pytest.raises(FileNotFoundError) as exc_info:
                locate_gatekit_gateway()

    error_msg = str(exc_info.value)
    assert "gatekit-gateway not found" in error_msg.lower()
    assert "sibling" in error_msg.lower()
    assert "path" in error_msg.lower()
```

These automated tests are fast, reliable, and catch regressions in business logic without requiring manual platform testing.

### Implementation Strategies

#### Use Mocks Aggressively

```python
# Mock client config detection
@pytest.fixture
def mock_claude_desktop_config():
    return {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            }
        }
    }

# Mock platform detection
@pytest.fixture
def mock_platform(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")

# Mock file system
@pytest.fixture
def mock_fs(tmp_path):
    config_dir = tmp_path / ".claude"
    config_dir.mkdir()
    return config_dir
```

#### Parameterized Tests for Variations

```python
@pytest.mark.parametrize("client,platform,config_path", [
    ("claude_desktop", "Darwin", "<HOME_DIR>/Library/Application Support/Claude/..."),
    ("claude_code", "Linux", "<HOME_DIR>/.claude.json"),
    ("codex", "Windows", "%USERPROFILE%/.codex/config.toml"),
])
def test_client_detection(client, platform, config_path, monkeypatch):
    # Test client detection logic
    pass
```

#### Test Helpers for Common Scenarios

```python
def create_test_client_config(servers: dict) -> dict:
    """Helper to create realistic client configs."""
    return {"mcpServers": servers}

def assert_gatekit_config_valid(config_path: Path):
    """Helper to validate generated Gatekit config."""
    # Parse YAML, validate structure
    pass
```

### Risk Assessment

**High Risk - Must Test:**
- ✅ Path resolution (cross-platform)
- ✅ Server name conflicts and sanitization
- ✅ Malformed input handling
- ✅ Connection test reliability

**Medium Risk - Should Test:**
- ✅ Environment variable handling
- ✅ Complex argument preservation
- ✅ File save dialog flows

**Low Risk - Nice to Test:**
- Multiple clients (handled by same code path)
- Every platform × client combination (diminishing returns)

### Phased Implementation Recommendation

**Automated Unit Tests (~15-20 tests)** - Write first:
- Fast feedback on business logic
- Catch regressions immediately
- Platform-independent, runs in CI

**Automated Integration Tests (convert most manual scenarios)** - Core testing strategy:
- Most Tier 3-6 scenarios (~20 tests) should be **automated integration tests** using test harness
- Write fake client configs into temp directories (`tempfile.TemporaryDirectory()`)
- Run detector/generator logic against fake configs
- Assert expected behavior (config generation, warnings, errors)
- Runs in CI on every commit
- Fast (seconds), consistent, no human error

**Example automated integration test:**
```python
def test_env_vars_included_with_values():
    """Automated version of manual test #10"""
    fake_config = {
        "mcpServers": {
            "github": {
                "command": "npx",
                "args": ["@modelcontextprotocol/server-github"],
                "env": {"GITHUB_TOKEN": "secret"}
            }
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        write_fake_client_config(tmpdir, "claude_desktop", fake_config)
        result = detect_and_generate(tmpdir)

        # Assert env vars INCLUDED with actual values
        assert "env" in result.upstreams["github"]
        assert result.upstreams["github"]["env"]["GITHUB_TOKEN"] == "secret"
        # Assert security warning was shown
        assert result.security_warning_shown is True
```

**Manual Smoke Tests (5-7 scenarios)** - Reserve for human validation:
- Tier 1: One happy path per client (3 tests)
- Tier 2: Platform-specific UI checks (2-3 tests) - editor opening, file dialogs
- Overall wizard UX flow validation
- Real clipboard/TextArea interactions

**Benefits of this approach:**
- ✅ Most edge cases tested automatically in CI (fast, reliable, consistent)
- ✅ Reduces manual testing burden from ~27 scenarios to 5-7 per release
- ✅ Manual tests focus on what humans are good at (UX, cross-platform UI, "does it feel right")
- ✅ Automated tests catch regressions immediately on every commit

**Total confidence with manageable effort** - Automated integration tests (~1-2 days to write) handle most edge cases and run in CI. Manual smoke tests (~30 minutes per release) validate UI and platform-specific behaviors that require human judgment.

## Technical Notes

### State Management
- Track recent files in TUI state (already implemented in `RecentFiles`)
- Store list of detected clients with their config paths
- Store generated Gatekit config path
- Track connection test results for each server

### MCP Client Detection

#### Locating gatekit-gateway (IMPORTANT)

**Challenge:** While `gatekit` and `gatekit-gateway` are both console scripts in the same package, they're not always installed as siblings of `sys.executable` due to various installation methods.

**Installation Scenarios:**

| Install Method | sys.executable | gatekit-gateway location | Sibling? |
|----------------|----------------|---------------------------|----------|
| `python -m venv` + pip (POSIX) | `.venv/bin/python` | `.venv/bin/gatekit-gateway` | ✅ YES |
| `python -m venv` + pip (Windows) | `.venv\Scripts\python.exe` | `.venv\Scripts\gatekit-gateway.exe` | ✅ YES |
| `pip install --user` | `/usr/bin/python3` | `~/.local/bin/gatekit-gateway` | ❌ NO |
| System pip | `/usr/bin/python3` | `/usr/local/bin/gatekit-gateway` | ❌ NO |
| pipx | `~/.local/pipx/venvs/gatekit/bin/python` | `~/.local/pipx/venvs/gatekit/bin/gatekit-gateway` | ✅ YES |

**Robust Lookup Strategy:**

Use a two-strategy fallback approach:

```python
import sys
import shutil
from pathlib import Path

def locate_gatekit_gateway() -> Path:
    """Find gatekit-gateway executable.

    Tries multiple strategies to handle different installation methods:
    1. Sibling to sys.executable (works for venvs, pipx)
    2. PATH search via shutil.which (works for --user, system installs)
    3. Error if not found
    """
    # Strategy 1: Try sibling to sys.executable
    # Works for: venv, pipx, some system installs
    # Check both bare name (POSIX) and .exe (Windows)
    bin_dir = Path(sys.executable).parent
    for candidate in ["gatekit-gateway", "gatekit-gateway.exe"]:
        sibling_path = bin_dir / candidate
        if sibling_path.exists():
            return sibling_path

    # Strategy 2: Search PATH
    # Works for: pip install --user, system installs where scripts
    # are in a different bin directory than python
    # shutil.which automatically handles .exe on Windows
    which_result = shutil.which("gatekit-gateway")
    if which_result:
        return Path(which_result)

    # Strategy 3: Not found - show clear error
    raise FileNotFoundError(
        "gatekit-gateway not found. "
        f"Tried:\n"
        f"  1. Sibling to Python: {bin_dir / 'gatekit-gateway'} (and .exe variant)\n"
        f"  2. PATH search: shutil.which('gatekit-gateway')\n"
        f"\n"
        f"Please ensure Gatekit is properly installed."
    )
```

**Why this approach:**
- ✅ Works for venv installations (sibling check succeeds on POSIX and Windows)
- ✅ Handles Windows `.exe` wrappers (checks both bare name and .exe variant)
- ✅ Works for `pip install --user` (PATH search succeeds)
- ✅ Works for system installs (PATH search succeeds)
- ✅ Works for pipx (sibling check succeeds)
- ✅ Prefers the "correct" path when both exist
- ✅ Clear, actionable error if neither strategy works
- ✅ Users do NOT need to manually configure anything

**For the generated snippets:**
- Use the absolute path returned by `locate_gatekit_gateway()`
- This is the full path that will work from any context
- MCP clients will use this full absolute path we provide

#### Supported Client Locations

**Claude Desktop:**
- macOS: `<HOME_DIR>/Library/Application Support/Claude/claude_desktop_config.json`
- Linux: `<HOME_DIR>/.config/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json` (displays as `C:\Users\<USERNAME>\AppData\Roaming\Claude\claude_desktop_config.json`)

**Claude Code:**
- User-level (in home directory):
  - macOS: `/Users/username/.claude.json` (docs may show: `~/.claude.json`)
  - Linux: `/home/username/.claude.json` (docs may show: `~/.claude.json`)
  - Windows: `C:\Users\username\.claude.json` (docs may show: `%USERPROFILE%\.claude.json`)
- Project-level: `.mcp.json` (in project root, cross-platform)
- Enterprise-managed:
  - macOS: `/Library/Application Support/ClaudeCode/managed-mcp.json`
  - Windows: `C:\ProgramData\ClaudeCode\managed-mcp.json`
  - Linux: `/etc/claude-code/managed-mcp.json`

**Codex:**
- User-level (in home directory):
  - macOS: `/Users/username/.codex/config.toml` (docs may show: `~/.codex/config.toml`)
  - Linux: `/home/username/.codex/config.toml` (docs may show: `~/.codex/config.toml`)
  - Windows: `C:\Users\username\.codex\config.toml` (docs may show: `%USERPROFILE%\.codex\config.toml`)
- Alternative: If `$CODEX_HOME` environment variable is set, `$CODEX_HOME/config.toml`

**Implementation Note:** Our Python code will use `Path.home() / ".codex" / "config.toml"` or `Path("~/.codex/config.toml").expanduser()` which works correctly on all platforms.

#### Config Format Parsing

**Claude Desktop & Claude Code** use JSON format:
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_1234567890abcdef"
      }
    }
  }
}
```

**NOTE**: These examples show realistic token values. The implementation copies actual env var values from client configs (not placeholders) - see "Environment Variables: Include with Security Warning" decision below.

**Codex** uses TOML format:
```toml
experimental_use_rmcp_client = true

[mcp_servers.filesystem]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

[mcp_servers.github]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
env = { "GITHUB_PERSONAL_ACCESS_TOKEN" = "ghp_1234567890abcdef" }

# HTTP/SSE servers (future)
[mcp_servers.figma]
url = "https://mcp.linear.app/mcp"
bearer_token_env_var = "FIGMA_TOKEN"
```

**IMPORTANT: Codex TOML Parsing Caveats:**
- Section name MUST be `mcp_servers` (underscore, not hyphen)
- Using `mcp-servers` or `mcpservers` will cause silent failure
- Server names follow the dot notation: `[mcp_servers.server_name]`

**Parsing Strategy for JSON (Claude Desktop & Claude Code):**
1. Check if file exists at expected location
2. Parse JSON safely (handle malformed JSON)
3. Extract `mcpServers` object
4. For each server entry:
   - Extract name (key)
   - Extract command (string)
   - Extract args (array)
   - Extract env vars (object, optional)
   - Detect transport type (stdio if command/args, http if url)
   - **Skip HTTP/SSE servers** - not supported in this release (stdio only)

**Parsing Strategy for TOML (Codex):**
1. Check if `~/.codex/config.toml` exists (or `$CODEX_HOME/config.toml`)
2. Parse TOML safely (handle malformed TOML)
3. Extract all `[mcp_servers.*]` sections
4. For each server section:
   - Extract name (part after `mcp_servers.`)
   - Extract command (string)
   - Extract args (array)
   - Extract env vars (inline table, optional)
   - Detect transport type (stdio if command/args, http if url/bearer_token_env_var)
   - **Skip HTTP/SSE servers** - not supported in this release (stdio only)

**Detection Priority:**
- Try user-level configs first (using `Path.expanduser()` to handle `~` on all platforms)
  - Claude Code: `~/.claude.json`
  - Codex: `~/.codex/config.toml`
- For Claude Code, also check project-level `.mcp.json` in current directory
- Skip enterprise-managed configs in MVP (read-only, IT-managed)

#### MCP Client CLI Commands

**Research Finding:** Two of the three MVP clients have CLI commands for managing MCP servers, which is simpler and less error-prone than manual config file editing.

| Client | CLI Available? | Command for Adding Server | Command for Removing Server |
|--------|----------------|---------------------------|----------------------------|
| **Claude Desktop** | ❌ NO | N/A - Must manually edit JSON | N/A |
| **Claude Code** | ✅ YES | `claude mcp add --transport stdio --scope <user\|project\|local> <name> -- <command>` | `claude mcp remove <name> --scope <user\|project\|local>` |
| **Codex** | ✅ YES | `codex mcp add <name> -- <command>` | `codex mcp remove <name>` |

**Claude Code Scopes:**
- `--scope user`: Stored in `~/.claude.json` (available across all projects)
- `--scope project`: Stored in `.mcp.json` (shared with team via version control)
- `--scope local`: Session-only (temporary, not persisted)

**Implementation Strategy:**
- **For Claude Desktop**: Provide JSON snippet with manual editing instructions
- **For Claude Code**: Provide bash commands using `claude mcp remove` + `claude mcp add` with appropriate `--scope` based on where we found their servers
- **For Codex**: Provide bash commands using `codex mcp remove` + `codex mcp add`

**Benefits of CLI approach:**
- ✅ Simpler UX (copy one command instead of editing JSON/TOML)
- ✅ Less error-prone (no manual syntax mistakes)
- ✅ Solves multi-config problem (correct `--scope` flag handles user vs project)
- ✅ Complete workflow: remove old + add new in one copyable script

#### Config Format Assumptions & Validation

**Assumptions Made:**
1. **JSON Clients (Claude Desktop, Claude Code)**:
   - Top-level key is `mcpServers` (camelCase)
   - Each server entry has either `command`+`args` OR `url`
   - `env` is optional object mapping string keys to string values
   - `args` is array of strings
   - Server names are valid JSON keys (alphanumeric, hyphens, underscores)

2. **TOML Client (Codex)**:
   - Section name is `mcp_servers` (snake_case with underscore)
   - Server sections use `[mcp_servers.server_name]` notation
   - Each server has either `command`+`args` OR `url`+`bearer_token_env_var`
   - `env` uses TOML inline table syntax: `{ "KEY" = "value" }`
   - `args` is TOML array: `["arg1", "arg2"]`

3. **Cross-Client Assumptions**:
   - All clients support stdio transport (`command`+`args`)
   - HTTP/SSE transport (`url`) exists but may not work in MVP
   - Environment variables follow same semantic meaning across clients
   - Relative paths in commands are problematic (skip with warning)
   - Server names should be filesystem-safe and YAML-compatible

**Validation Strategy:**
- Parse config file format (JSON vs TOML)
- Validate required fields exist (`command` OR `url`)
- Warn on unknown fields but don't fail
- Gracefully skip servers with invalid/incomplete configuration
- Log detailed parse errors for debugging

**Fallback Detection Logic:**

For robustness, try multiple possible config locations:

```python
# Claude Code detection with fallbacks
CLAUDE_CODE_PATHS = [
    "<HOME_DIR>/.claude.json",              # Primary user-level config
    ".mcp.json",                   # Project-level config
    "<HOME_DIR>/.claude/settings.local.json"  # Alternative (deprecated but check)
]

# Codex detection with fallbacks
CODEX_PATHS = [
    "$CODEX_HOME/config.toml",     # If CODEX_HOME env var set
    "<HOME_DIR>/.codex/config.toml",        # Default location
]
```

This ensures we find configs even if:
- Documentation changes
- Users have non-standard setups
- Client versions use different locations

**What If Assumptions Are Wrong?**
- **Graceful degradation**: Skip that client with clear error message
- **User feedback**: Log parse errors with file path and line number
- **Manual override**: Always offer "create blank config" option
- **Future updates**: Easy to add new parsers without breaking existing logic

### Configuration Generation

#### Gatekit Config Structure

**IMPORTANT**: For the canonical config specification, see [`docs/configuration-specification.md`](../configuration-specification.md).

```yaml
# Generated Gatekit configuration
proxy:
  transport: stdio

  upstreams:
    - name: filesystem
      command: ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/files"]

    - name: github
      command: ["npx", "-y", "@modelcontextprotocol/server-github"]
      # NOTE: Gatekit does NOT support 'env' field in upstream configs.
      # Environment variables must be set in MCP client configurations
      # (e.g., Claude Desktop's claude_desktop_config.json) or in your
      # shell environment before launching gatekit-gateway.

plugins:
  auditing:
    _global:
      - handler: audit_jsonl
        config:
          enabled: true
          priority: 50
          output_file: "logs/audit.json"
          mode: "all_events"
```

#### Config Save Location
- **Default (all platforms)**: `configs/gatekit.yaml`
- Create parent directories if they don't exist
- Validate config with `ConfigLoader` before saving

### Client Config Snippet Generation

For each detected client, generate a JSON snippet to add Gatekit as an MCP server:

```json
{
  "gatekit": {
    "command": "<GATEKIT_GATEWAY_PATH>",
    "args": ["--config", "<CONFIG_PATH>"]
  }
}
```

**CRITICAL Path Requirements:**
- **ALL paths must be absolute** - no `~`, no `%VAR%`, no environment variables
- Use `Path.expanduser().resolve()` to expand ALL paths before insertion
- Command path: From `locate_gatekit_gateway()` (returns absolute Path)
- Config path: Expand user input from file dialog to absolute path
- Why: `~` doesn't expand on Windows for these MCP clients, and even on POSIX we commit to absolute paths for reliability

**CRITICAL Line Continuation Requirements (for main UI snippets):**
- **Platform-specific syntax** - bash/zsh and PowerShell use different line continuation
- macOS/Linux: Use `\` (backslash) for bash/zsh shells
- Windows: Use `` ` `` (backtick) for PowerShell
- Detect platform: `platform.system()` returns "Darwin", "Linux", or "Windows"
- Why: POSIX line continuations (`\`) fail in PowerShell and cmd.exe on Windows

**Implementation Strategy for Main UI Snippets:**
```python
import platform

def format_multiline_command(parts: list[str]) -> str:
    """Format command with platform-appropriate line continuation.

    Used for generating commands shown in the main Setup Complete screen
    that users will immediately paste into their terminal.
    """
    if platform.system() == "Windows":
        # PowerShell uses backtick
        return " `\n  ".join(parts)
    else:
        # POSIX shells (bash, zsh) use backslash
        return " \\\n  ".join(parts)

# Example usage:
parts = [
    "claude mcp add --transport stdio --scope user",
    "gatekit -- <GATEKIT_GATEWAY_PATH>",
    "--config <CONFIG_PATH>"
]
command = format_multiline_command(parts)
```

**Implementation Strategy for Restore Files:**
- **macOS/Linux**: Generate executable `.sh` bash scripts with `\` line continuation
- **Windows**: Generate `.txt` files with numbered instructions and PowerShell commands (`` ` `` line continuation)
- Windows approach avoids PowerShell execution policy issues (pasting commands has no restrictions)
- See restore script examples above for exact format

**Additional Requirements:**
- Platform-specific path format (forward slashes on Unix, backslashes on Windows where needed)
- Validate paths exist before generating snippets
- Since TUI is running from Gatekit installation, gatekit-gateway lookup is guaranteed to work

### UI Implementation Details

#### TextArea Widget for Config Snippets

Use Textual's built-in `TextArea` widget:

```python
from textual.widgets import TextArea

config_snippet = TextArea(
    snippet_text,
    language="json",      # Syntax highlighting
    read_only=True,       # Users can't edit, only copy
    show_line_numbers=False,  # Cleaner look
    theme="github_dark"   # Or another theme
)
```

**Benefits over SelectableStatic:**
- Built-in text selection with mouse and keyboard
- Native Ctrl+C copy support
- Proper text area UX users are familiar with
- Scrollable for long configs

#### Opening Files in Default Editor

Platform-specific commands:

```python
import subprocess
import platform

def open_in_editor(file_path: str):
    """Open file in user's default text editor"""
    system = platform.system()

    if system == "Darwin":  # macOS
        subprocess.run(["open", "-t", file_path])  # -t forces text editor
    elif system == "Linux":
        subprocess.run(["xdg-open", file_path])
    elif system == "Windows":
        subprocess.run(["start", "", file_path], shell=True)
```

**Error Handling:**
- File might be locked by running client
- User might not have permissions
- Default editor might not be configured
- Gracefully degrade to showing file path only

**Editor Detection** (optional enhancement):
- Check `$EDITOR` or `$VISUAL` environment variables
- Detect if VSCode/Sublime/Atom are installed
- Ultimate fallback to system default

#### Copy to Clipboard

Use Textual's built-in clipboard support:

```python
# For programmatic copy (e.g., Copy buttons)
await self.app.copy_to_clipboard(text_to_copy)

# Users can also manually select text in TextArea and press Ctrl+C
# This works automatically with TextArea widgets
```

**Cross-Platform Support:**
- macOS: Uses pbcopy/pbpaste
- Linux: Uses xclip/xsel if available
- Windows: Uses Windows clipboard API
- SSH/Terminal: Falls back gracefully

### Connection Testing

#### Reuse Existing Infrastructure

From `gatekit/tui/screens/config_editor/base.py`:

```python
async def _handshake_upstream(self, upstream) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Perform MCP handshake and fetch tool metadata."""
    # Returns: (server_identity, tool_payload)
    # Handles: timeout (5s), initialization, tools/list
```

**Implementation Options:**

1. **Direct Reuse** (simplest):
```python
# In guided setup wizard
from gatekit.tui.screens.config_editor.base import ConfigEditorScreen

# Reuse the method
identity, tools = await ConfigEditorScreen._handshake_upstream(self, upstream)
```

2. **Extract to Utility** (cleaner, if needed elsewhere):
```python
# gatekit/tui/utils/server_testing.py
class ServerConnectionTester:
    async def test_server(self, upstream: UpstreamConfig) -> TestResult:
        # Core handshake logic extracted
        ...
```

#### Test Results Display

```
Testing connections...

filesystem ... ✓ Connected (@modelcontextprotocol/server-filesystem)
github ....... ✓ Connected (github-mcp-server)
postgres ..... ✗ Failed (connection timeout)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2 of 3 servers connected successfully

[View Details]  [Continue Anyway]  [Go Back]
```

**Test Result Data:**
```python
@dataclass
class TestResult:
    server_name: str
    success: bool
    identity: Optional[str] = None
    tool_count: Optional[int] = None
    error: Optional[str] = None
```

### Potential Issues & Mitigations

#### Issue: Multiple Clients with Same Servers, Different Params ✓ RESOLVED

**Scenario**: User has `filesystem` server in both Claude Desktop and Claude Code, but with different allowed paths.

**MVP Solution**: Rename servers with client suffix
- `filesystem` in Claude Desktop → `filesystem-claude-desktop` in Gatekit config
- `filesystem` in Claude Code → `filesystem-claude-code` in Gatekit config
- Update each client's snippet to use the renamed server name
- Both servers exist in Gatekit, clients point to their specific version

**Benefits**:
- No data loss - both configurations preserved
- No user choice required during setup
- Clear naming shows which config came from where

**Phase 2 Enhancement**: Let user choose preferred config and use canonical name

#### Issue: Version Compatibility

**Scenario**: Client config formats change over time.

**Mitigation**:
- Start conservative - support current stable versions only
- Document supported client versions
- Gracefully handle parse errors with clear messages
- Easy to update parsers as formats evolve

#### Issue: Partial Migrations

**Scenario**: User wants Gatekit for some servers but not others.

**Mitigation**:
- In Phase 1, generate config with ALL detected servers
- Future enhancement: Add server selection screen
- Users can manually edit Gatekit config to remove unwanted servers
- Document this workflow clearly

#### Issue: Corporate/Managed Environments

**Scenario**: Config files might be managed by IT or deployment tools.

**Mitigation**:
- Clear messaging that guided setup requires config file write access
- Provide option to export config for IT to deploy
- Documentation for enterprise deployment scenarios

#### Issue: Environment Variables & Secrets ✓ RESOLVED

**Scenario**: Many MCP servers require environment variables (API keys, tokens, passwords).

**MVP Solution**: Include env vars with actual values
- Copy env vars from client config to Gatekit config automatically
- Show security warning dialog before config generation if env vars detected
- Add warning comment in generated YAML about plaintext secrets
- Include actual env var values in restore scripts with security warning header
- Document that secrets are in plaintext (same security posture as original client configs)

**Why this works**:
- Original client configs already had secrets in plaintext
- Same security posture - both files in user's home directory with same permissions
- Generated configs actually work (servers have their required env vars)
- Users don't need to manually hunt down and copy env vars
- "Guided Setup" actually completes setup (not 90% setup + manual work)

**Phase 2 Enhancement**:
- Redact in UI display (show `GITHUB_TOKEN: "***************"` in TextArea widgets)
- Add option to exclude env vars from restore scripts (for extra paranoid users)
- Consider integration with system keychain or external secret stores
- Support for secrets manager references (e.g., `${env:GITHUB_TOKEN}` or Vault paths)

#### Issue: Relative Paths in Server Commands ✓ RESOLVED

**Scenario**: Server uses relative paths like `./bin/server` or `../data/config.json`

**MVP Solution**: Skip servers with relative paths
```
⚠ Warning: Server 'my-server' uses relative paths:
  Command: ./bin/server

  Gatekit cannot resolve relative paths automatically.
  Please update to absolute paths manually after setup.

[Skip this server]  [Include anyway (may not work)]
```

**Phase 2 Enhancement**: Ask user for base directory to resolve relative paths

#### Issue: Multiple Existing Gatekit Configs ✓ RESOLVED

**Scenario**: User manually set up different gatekit configs for different clients, then reruns guided setup.

**MVP Solution**: Ignore existing multi-config setup
- Generate new config based on save file dialog location
- If user chooses existing config location, warn about overwrite (standard file dialog behavior)
- User can cancel and manually consolidate if desired

**Rationale**:
- Detecting existing gatekit configs in client configs is complex
- MVP focuses on first-time setup, not migration from manual multi-config setups
- Users with complex setups can manually manage their configs

**Phase 2 Enhancement**: Detect gatekit in client configs and offer consolidation wizard

#### Issue: Empty MCP Servers Section ✓ RESOLVED

**Scenario**: Client config found, but `mcpServers` section is empty or missing.

**MVP Solution**: Show informative message
```
┌────────────────────────────────────────────────────┐
│  Claude Desktop detected, but no MCP servers       │
│  configured.                                       │
│                                                    │
│  Would you like to create a blank Gatekit       │
│  configuration?                                    │
│                                                    │
│  [Create Blank Config]  [Cancel]                  │
└────────────────────────────────────────────────────┘
```

#### Issue: gatekit-gateway Path ✓ RESOLVED

**Scenario**: Need to provide full path to gatekit-gateway in generated snippets, but it's not always a sibling of `sys.executable` due to various installation methods.

**MVP Solution**: Use robust fallback strategy to find gatekit-gateway
```python
import sys
import shutil
from pathlib import Path

def locate_gatekit_gateway() -> Path:
    """Find gatekit-gateway using fallback strategies."""
    # Strategy 1: Try sibling to sys.executable (works for venv, pipx)
    # Check both bare name (POSIX) and .exe (Windows)
    bin_dir = Path(sys.executable).parent
    for candidate in ["gatekit-gateway", "gatekit-gateway.exe"]:
        sibling_path = bin_dir / candidate
        if sibling_path.exists():
            return sibling_path

    # Strategy 2: Search PATH (works for --user, system installs)
    # shutil.which automatically handles .exe on Windows
    which_result = shutil.which("gatekit-gateway")
    if which_result:
        return Path(which_result)

    # Strategy 3: Not found
    raise FileNotFoundError(
        f"gatekit-gateway not found.\n"
        f"Tried sibling: {bin_dir / 'gatekit-gateway'} (and .exe variant)\n"
        f"Tried PATH: shutil.which('gatekit-gateway')\n"
        f"Please ensure Gatekit is properly installed."
    )

# Find gatekit-gateway
try:
    gatekit_gateway_path = locate_gatekit_gateway()
except FileNotFoundError as e:
    show_error("gatekit-gateway not found", str(e))
    return

# Use absolute path in generated snippet
snippet = {
    "gatekit": {
        "command": str(gatekit_gateway_path),  # Full absolute path
        "args": ["--config", str(Path(config_path).expanduser().resolve())]
    }
}
```

**Why this works:**
- ✅ Handles venv/pipx installs (sibling check succeeds on POSIX and Windows)
- ✅ Handles Windows `.exe` wrappers (checks both bare name and .exe variant)
- ✅ Handles `pip install --user` (PATH search)
- ✅ Handles system installs (PATH search)
- ✅ Prefers the "right" path when multiple options exist
- ✅ Clear error message with troubleshooting info
- ✅ Guaranteed version match with TUI (same installation)
- ✅ Works across all real-world installation methods

## Resolved Design Decisions

### 1. Wizard Flow: Single-Step ✓

**Decision**: Single-step wizard
**Rationale**:
- Simpler, less overwhelming for first-time users
- Detect → Generate → Show instructions all at once
- Users can immediately see results and take action
- Progressive disclosure - don't force plugin configuration decisions upfront

### 2. Plugin Configuration: Defaults Applied Automatically ✓

**Decision**: Apply minimal defaults, no user choices during setup
**Defaults**:
- Auditing: JSON lines logger only
- Security: None (explicit opt-in after users understand the tool)
- Middleware: None

**Rationale**:
- Security-first: Start minimal and safe
- Users can easily add more plugins after understanding the tool
- Avoids overwhelming new users with plugin concepts
- JSON lines provides basic observability without requiring configuration

### 3. Client Config Modification: Detection Only, No Auto-Modification ✓

**Decision**: Never automatically modify MCP client configurations
**Approach**:
- Detect client configs and parse MCP servers
- Generate Gatekit config
- Provide copy-paste snippets and instructions
- Users manually update their client configs

**Rationale**:
- Respects user control and expectations
- Avoids breaking working client setups
- Aligns with security-first principles
- Reduces maintenance burden (no need to support dozens of clients)

### 4. Test Connection: Reuse Existing Infrastructure ✓

**Decision**: Reuse `_handshake_upstream` from ConfigEditorScreen
**Rationale**:
- Battle-tested code that already works
- Consistent behavior across TUI
- Automatic tool discovery during handshake
- Proper timeout and error handling

**What Test Connection Tests**:
- ✅ Gatekit config is syntactically valid
- ✅ Gatekit can launch each MCP server
- ✅ Each server responds to initialization
- ✅ Each server reports identity correctly
- ✅ Tool discovery works
- ❌ NOT testing MCP client → Gatekit (user hasn't updated their client config yet)

### 5. Post-Setup Flow: Open in Config Editor ✓

**Decision**: After generation, automatically open config in editor
**Flow**:
1. Generate Gatekit config
2. Show instructions screen
3. [Done] button opens generated config in TUI config editor
4. User can immediately review, verify, and edit

**Rationale**:
- User sees exactly what was generated
- Can verify before updating client configs
- Natural transition to editing if needed
- Provides confidence and transparency

### 6. Config Save Location: File Dialog ✓

**Decision**: Show file save dialog with smart default
**Default Location**: `configs/gatekit.yaml` (in current directory)
**Alternative**: user-selected absolute path (e.g., `/Users/username/.config/gatekit/gatekit.yaml`)

**Rationale**:
- Users explicitly choose where config lives
- Standard file dialog behavior everyone understands
- Warn on overwrite automatically (system dialog)
- Allows multiple configs if user wants them

### 7. Conflicting Server Names: Rename with Suffix ✓

**Decision**: When same server name appears in multiple clients with different configs, rename both
**Example**:
- `filesystem` in Claude Desktop → becomes `filesystem-claude-desktop`
- `filesystem` in Claude Code → becomes `filesystem-claude-code`
- Both exist in Gatekit config
- Client snippets reference their specific renamed server

**Rationale**:
- No data loss - both configurations preserved
- No user decisions needed during setup
- Clear naming convention
- Users can manually merge later if desired

### 8. Connection Test Failures: Graceful Handling ✓

**Decision**: Allow users to continue even if all tests fail
**UX**:
```
┌────────────────────────────────────────────────────┐
│  Connection Test Results                           │
│                                                    │
│  ✗ All 3 servers failed to connect                │
│                                                    │
│  This might mean:                                  │
│  • Servers aren't running                         │
│  • Missing environment variables                  │
│  • Network/firewall issues                        │
│                                                    │
│  You can still save the configuration and         │
│  troubleshoot later.                              │
│                                                    │
│  [View Details]  [Save Anyway]  [Go Back]         │
└────────────────────────────────────────────────────┘
```

**Rationale**:
- Servers might be legitimately down
- Server dependencies might not be installed yet
- Don't block setup on connection issues
- User can troubleshoot after seeing generated config

### 9. CLI Commands vs Manual Editing ✓

**Decision**: Use native CLI commands for Claude Code and Codex, manual editing only for Claude Desktop

**Approach**:
- **Claude Desktop**: No CLI available → Provide JSON snippet with manual instructions
- **Claude Code**: Has `claude mcp` CLI → Provide bash commands with remove + add
- **Codex**: Has `codex mcp` CLI → Provide bash commands with remove + add

**Rationale**:
- Simpler UX - copy one command instead of editing config files
- Less error-prone - no manual JSON/TOML syntax mistakes
- Solves multi-config problem - use correct `--scope` flag for Claude Code
- Complete workflow - remove old servers + add Gatekit in one script
- Professional - leverages each client's native tooling

### 10. Restore Scripts with User-Chosen Location ✓

**Decision**: Generate restore scripts and let user choose where to save them (separate from Gatekit config)

**Default Location**: `<DOCUMENTS_DIR>/gatekit-restore/`

**Approach**:
- After saving Gatekit config, show separate dialog for restore script location
- Allow user to skip if they don't want restore scripts
- Generate client-specific restore files:
  - Claude Desktop: `.txt` file with manual instructions
  - Claude Code: `.sh` script with `claude mcp` commands
  - Codex: `.sh` script with `codex mcp` commands
- Include timestamps and original server definitions
- Add comments about env vars that need manual restoration

**Rationale**:
- User confidence - "I can always go back" makes users willing to try Gatekit
- Survives uninstall - not stored with Gatekit config that may be deleted
- Security-first - full transparency and reversibility
- Troubleshooting - easy to test with/without Gatekit
- Documentation - serves as record of what was changed

### 11. Migration Workflow: Remove + Add ✓

**Decision**: Users must remove old servers before adding Gatekit to avoid duplicates

**Approach**:
- List servers being migrated in the instructions
- For CLI clients: provide `mcp remove` commands for each server
- For Claude Desktop: show which servers to manually remove from JSON
- Make workflow clear: Remove old → Add Gatekit → Restart client

**Rationale**:
- Prevents duplicate tools - user would see two `filesystem` tools, etc.
- Makes migration explicit and understandable
- Ensures clean state in client configuration

### 12. Environment Variables: Include with Security Warning ✓

**Decision**: Copy env vars with actual values to Gatekit config and restore scripts

**Approach**:
- Parse env vars from client configs
- Include in generated Gatekit config with actual values
- Include in restore scripts with actual values
- Show security warning dialog before generation if env vars detected
- Add warning comments in generated files about plaintext secrets

**Rationale**:
- **Generated configs actually work** - servers have required env vars
- **No manual work required** - users don't hunt down env vars
- **Same security posture** - original configs already had secrets in plaintext
- **Completes the setup** - "Guided Setup" means setup works, not 90% + manual fixes
- **Users can delete later** - if they want to switch to secrets manager

**Phase 2 enhancements**:
- Redact in UI displays (show `***` in TextArea widgets)
- Optional env var exclusion for paranoid users
- Secrets manager integration (Vault, AWS Secrets Manager, etc.)

## Design Rationale

Based on UX research into onboarding patterns and empty states:

- **Educational empty state** - Explains what will happen and why
- **Direct pathway** - Clear CTA to primary action
- **Progressive disclosure** - Doesn't overwhelm with all options
- **Safety first** - Communicates backup behavior upfront
- **Professional tone** - Matches open-source tool expectations

### References
- Nielsen Norman Group: Empty States in Application Design
- Vercel Geist Design System: Empty State Patterns
- Wizard UI best practices from multiple sources

## Implementation Status

**Current Status**: Design complete, all major decisions resolved, ready for implementation

**Key Decisions Made**:
- ✓ No auto-modification of client configs (detection + copy-paste snippets only)
- ✓ Single-step wizard (simpler, less overwhelming)
- ✓ MVP supports 3 clients: Claude Desktop, Claude Code, and Codex
- ✓ Minimal default plugins (JSON lines logger only)
- ✓ Use CLI commands for Claude Code and Codex (simpler than manual editing)
- ✓ Manual JSON editing only for Claude Desktop (no CLI available)
- ✓ Generate restore scripts for easy rollback
- ✓ Restore scripts saved to user-chosen location (default: `<DOCUMENTS_DIR>/gatekit-restore/`)
- ✓ Migration workflow: Remove old servers + Add Gatekit (prevents duplicates)
- ✓ TextArea widgets for config snippets/commands (not SelectableStatic)
- ✓ Reuse existing test connection infrastructure (`_handshake_upstream`)
- ✓ Platform-specific editor opening with graceful fallbacks
- ✓ Use absolute path for gatekit-gateway (robust lookup: sibling check + PATH fallback)
- ✓ **All paths expanded to absolute** - no `~` or env vars in generated snippets (Windows compatibility)
- ✓ **Platform-specific line continuation** - bash `\` on POSIX, PowerShell `` ` `` on Windows
- ✓ **Platform-specific restore files** - `.sh` scripts for macOS/Linux, `.txt` paste instructions for Windows (avoids PowerShell execution policy issues)
- ✓ **Environment variables included with actual values** - copied from client configs to Gatekit config and restore scripts (makes setup actually work, same security posture as original configs)
- ✓ File save dialog defaulting to `configs/gatekit.yaml`
- ✓ Rename conflicting servers with client suffix (`filesystem-claude-desktop`, `filesystem-claude-code`)
- ✓ Open generated config in TUI editor after setup
- ✓ Graceful handling of connection test failures

**MVP Limitations** (Documented for Phase 2):
- ⏸ Relative paths - Servers with relative paths will be skipped with warning
- ⏸ HTTP transport - Only stdio servers supported in MVP
- ⏸ Multiple existing Gatekit configs - No detection/consolidation (use file dialog overwrite)
- ⏸ Secrets manager integration - Env vars included as plaintext, no Vault/keychain support yet

**Research Complete:**
- ✅ Claude Code config locations: `~/.claude.json` (user, expands platform-appropriately), `.mcp.json` (project)
- ✅ Codex config location: `~/.codex/config.toml` (expands platform-appropriately)
- ✅ Config format documentation: JSON for Claude Desktop/Code, TOML for Codex
- ✅ Parsing strategies defined for both formats
- ✅ Fallback detection logic documented
- ✅ Config format assumptions validated and documented

**Next Actions**:
1. Begin Phase 1: Welcome Screen Updates
   - Add first-run detection (check for empty recent files)
   - Create FirstRunWelcome component
   - Update button hierarchy
2. Begin Phase 2: MCP Client Detection (all 3 MVP clients)
   - Implement Claude Desktop detection for all platforms (macOS, Linux, Windows)
   - Implement Claude Code detection (JSON parsing, same as Claude Desktop)
   - Implement Codex detection (TOML parsing with `tomli`/`toml`)
   - Implement fallback detection (try multiple paths per client)
   - Parse configs and extract server definitions
   - Locate gatekit-gateway using robust fallback (sibling check + PATH search)
   - Implement conflict detection and renaming logic
3. Begin Phase 3: Configuration Generation
   - Generate Gatekit YAML with default plugins
   - Show file save dialog
   - Validate generated config with ConfigLoader
4. Continue with remaining phases as outlined in Implementation Plan

**Open Items for Research** (Future Enhancement):
- Additional MCP clients (Continue, Cursor, Zed, etc.) and their adoption rates
- Environment variable handling and redaction strategies

## Additional Edge Cases

### Server Name Sanitization
**Issue**: Server name contains invalid YAML/identifier characters
**Examples**: `my@server`, `server/name`, `server:8080`
**Solution**:
```python
def sanitize_server_name(name: str) -> str:
    """Convert server name to valid YAML identifier"""
    # Replace invalid chars with dash
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '-', name)
    # Ensure starts with letter/number
    sanitized = re.sub(r'^[^a-zA-Z0-9]+', '', sanitized)
    # Truncate if too long
    return sanitized[:48]
```

### Duplicate Server Names in Single Client
**Issue**: Same server name appears twice in one client's config
**Example**:
```json
{
  "mcpServers": {
    "test": { "command": "server1" },
    "test": { "command": "server2" }  // Invalid JSON but might occur
  }
}
```
**Solution**: JSON parsing will handle this (last one wins), or show parse error

### Malformed Client Configs
**Issue**: Client config is not valid JSON or has unexpected structure
**Solution**:
- Wrap JSON parsing in try/catch
- Show clear error: "Failed to parse Claude Desktop config"
- Offer to skip that client or cancel setup
- Log parse error for debugging

### Config File Permissions
**Issue**: User doesn't have read permission for client config
**Solution**:
- Catch permission errors during file read
- Show clear message: "Permission denied: Cannot read Claude Desktop config"
- Suggest running with appropriate permissions or manually copying config

### Very Large Configs
**Issue**: Client has 50+ MCP servers configured
**Solution**:
- MVP: Just handle it (generate large Gatekit config)
- UI: TextArea can scroll
- Performance: Async processing handles it fine
- Future: Add server selection screen to let user choose subset
