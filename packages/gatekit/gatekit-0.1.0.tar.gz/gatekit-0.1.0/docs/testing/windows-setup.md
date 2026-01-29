# Windows Environment Setup for Gatekit Validation

This guide covers setting up a Windows environment for Part 6 (Platform Delta) validation of Gatekit.

## Prerequisites

- Windows 10 or Windows 11
- Administrator access (for software installation)
- GitHub access to the Gatekit repository

## Setup (~30 minutes)

### Step 1: Install Development Tools

Open PowerShell as Administrator and run:

```powershell
# Python 3.12
winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements

# Git
winget install Git.Git

# Node.js LTS (for npx MCP servers)
winget install OpenJS.NodeJS.LTS

# UV package manager
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Restart PowerShell to pick up PATH changes
```

### Step 2: Enable Script Execution

PowerShell blocks scripts by default. Enable them for npm to work:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3: Install MCP Clients (for testing)

```powershell
# Claude Desktop
winget install Anthropic.Claude

# Claude Code
npm install -g @anthropic-ai/claude-code
```

For other clients (Codex, Cursor, Windsurf), install from their respective websites if needed for testing.

### Step 4: Clone and Set Up Gatekit

```powershell
# Navigate to your preferred location
cd C:\Users\$env:USERNAME

# Clone the repository
# For private repos, Git will prompt for credentials via Windows Credential Manager
git clone https://github.com/YOUR_ORG/gatekit.git
cd gatekit

# Create virtual environment and install dependencies
uv venv
uv pip install -e ".[dev]"

# Verify installation
uv run pytest tests/ -n auto
uv run ruff check gatekit
```

### Step 5: Configure Claude Code (Optional)

If using Claude Code for fixing issues found during validation:

```powershell
# Set your API key permanently (restart PowerShell after)
[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-api03-xxxxx", "User")

# Verify Claude Code works
claude --version
```

### Step 6: Create Feature Branch

```powershell
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
git checkout -b platform/windows-part6-validation
```

## Running Validation

After setup, follow the Part 6 checklist in `tests/validation/manual-validation-guide.md`.

### Quick Verification Commands

```powershell
# 6.1 Process Management - Start gateway
.venv\Scripts\gatekit-gateway.exe --config tests\validation\gateway-test-config.yaml --verbose

# 6.2 Path Handling - Check debug logs
gatekit --debug
dir $env:LOCALAPPDATA\gatekit\logs\

# 6.3 Client Config Paths - Verify all 5 clients
python -c "from gatekit.tui.guided_setup.client_registry import *; print('Claude Desktop:', get_claude_desktop_path())"
python -c "from gatekit.tui.guided_setup.client_registry import *; print('Claude Code:', get_claude_code_path())"
python -c "from gatekit.tui.guided_setup.client_registry import *; print('Codex:', get_codex_path())"
python -c "from gatekit.tui.guided_setup.client_registry import *; print('Cursor:', get_cursor_path())"
python -c "from gatekit.tui.guided_setup.client_registry import *; print('Windsurf:', get_windsurf_path())"

# 6.4 Shell Commands - Run TUI and check generated instructions
gatekit
# Select Guided Setup > Select servers > Select Claude Code as target
# Verify PowerShell syntax in generated instructions

# 6.5 Restore Scripts - Check generated scripts
dir configs\restore\
type configs\restore\restore-claude-code-*.txt
```

## Fixing Issues

When you find a Windows-specific issue:

```powershell
cd C:\Users\$env:USERNAME\gatekit

# Option A: Use Claude Code
claude
# Describe the issue, let it investigate and fix

# Option B: Manual fix
# Edit files as needed

# Commit with descriptive message
git add -A
git commit -m "Fix Windows issue (Part 6.x): brief description"
git push -u origin platform/windows-part6-validation
```

## Key Files for Windows Platform Code

| Area | File |
|------|------|
| Platform paths | `gatekit/tui/platform_paths.py` |
| Client detection | `gatekit/tui/guided_setup/detection.py` |
| Client registry | `gatekit/tui/guided_setup/client_registry.py` |
| PowerShell commands | `gatekit/tui/guided_setup/migration_instructions.py` |
| Restore scripts | `gatekit/tui/guided_setup/restore_scripts.py` |
| Clipboard | `gatekit/tui/clipboard.py` |

## Troubleshooting

### winget not found

If `winget` is not available, install "App Installer" from the Microsoft Store, or download installers directly:
- Python: https://www.python.org/downloads/
- Git: https://git-scm.com/download/win
- Node.js: https://nodejs.org/

### Python not in PATH

After installing Python, restart PowerShell. If still not found:
```powershell
# Check installation location
where.exe python
# If not found, add to PATH manually or reinstall with "Add to PATH" option
```

### UV not found

After installing UV, restart PowerShell. If still not found:
```powershell
# UV installs to ~/.cargo/bin by default
$env:PATH += ";$env:USERPROFILE\.cargo\bin"
```

### Permission errors during clone

For private repositories, use a Personal Access Token (PAT):
1. Generate PAT at: https://github.com/settings/tokens
2. Scopes needed: `repo` (full control)
3. When Git prompts for password, enter the PAT instead
