# Seed MCP Clients with Test Servers (Windows)
# For manual validation testing of Gatekit Guided Setup
#
# Server Distribution:
#   Claude Desktop: everything + memory (npx)
#   Claude Code: mcp-server-sqlite (uvx/PyPI)
#   Codex: sequential-thinking (npx)
#   Cursor: filesystem (npx)
#   Windsurf: mcp-server-time (uvx/PyPI)

param(
    [switch]$NoBackup,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Get script location and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path "$ScriptDir\..\..").Path
$BackupDir = Join-Path $ScriptDir "backups"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Test database path (relative to project root for portability in config)
$TestDbPath = Join-Path $ProjectRoot "tests\validation\test-files\test-database.db"

# Config paths
$ConfigPaths = @{
    ClaudeDesktop = Join-Path $env:APPDATA "Claude\claude_desktop_config.json"
    ClaudeCode    = Join-Path $env:USERPROFILE ".claude.json"
    Codex         = Join-Path $env:USERPROFILE ".codex\config.toml"
    Cursor        = Join-Path $env:USERPROFILE ".cursor\mcp.json"
    Windsurf      = Join-Path $env:USERPROFILE ".codeium\windsurf\mcp_config.json"
}

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  MCP Client Seed Script (Windows)" -ForegroundColor Cyan
Write-Host "  For Gatekit Manual Validation" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will seed all 5 MCP clients with test servers:"
Write-Host "  - Claude Desktop: everything + memory (npx)"
Write-Host "  - Claude Code: mcp-server-sqlite (uvx)"
Write-Host "  - Codex: sequential-thinking (npx)"
Write-Host "  - Cursor: filesystem (npx)"
Write-Host "  - Windsurf: mcp-server-time (uvx)"
Write-Host ""
Write-Host "SQLite server will use: $TestDbPath" -ForegroundColor Gray
Write-Host ""

if (-not $Force) {
    Write-Host "WARNING: This will overwrite your current MCP configurations!" -ForegroundColor Yellow
    if (-not $NoBackup) {
        Write-Host "Backups will be saved to: $BackupDir" -ForegroundColor Gray
    }
    Write-Host ""
    $response = Read-Host "Continue? (y/N)"
    if ($response -notmatch '^[Yy]') {
        Write-Host "Aborted." -ForegroundColor Red
        exit 1
    }
}

# Backup function
function Backup-ConfigFile {
    param([string]$Path, [string]$Name)

    if (Test-Path $Path) {
        if (-not (Test-Path $BackupDir)) {
            New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
        }
        $ext = [System.IO.Path]::GetExtension($Path)
        $backupPath = Join-Path $BackupDir "$Name-$Timestamp$ext"
        Copy-Item $Path $backupPath
        Write-Host "  Backed up: $Path" -ForegroundColor Green
    }
}

# Ensure parent directory exists and write config
function Write-ConfigFile {
    param([string]$Path, [string]$Content)

    $parentDir = Split-Path -Parent $Path
    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }
    # Use .NET directly to write UTF-8 without BOM (Set-Content adds BOM which breaks JSON parsers)
    [System.IO.File]::WriteAllText($Path, $Content)
}

# ============================================
# Create Backups
# ============================================
if (-not $NoBackup) {
    Write-Host ""
    Write-Host "--- Creating backups ---" -ForegroundColor Cyan
    foreach ($client in $ConfigPaths.Keys) {
        Backup-ConfigFile -Path $ConfigPaths[$client] -Name $client.ToLower()
    }
}

# ============================================
# Claude Desktop: everything + memory
# ============================================
Write-Host ""
Write-Host "--- Seeding Claude Desktop ---" -ForegroundColor Cyan

$claudeDesktopConfig = @'
{
  "mcpServers": {
    "everything": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
'@

Write-ConfigFile -Path $ConfigPaths.ClaudeDesktop -Content $claudeDesktopConfig
Write-Host "  Done: Set to everything + memory servers" -ForegroundColor Green

# ============================================
# Claude Code: mcp-server-sqlite
# ============================================
Write-Host ""
Write-Host "--- Seeding Claude Code ---" -ForegroundColor Cyan

# Claude Code config uses the db path - need to escape backslashes for JSON
$escapedDbPath = $TestDbPath -replace '\\', '\\\\'

$claudeCodeConfig = @"
{
  "mcpServers": {
    "sqlite": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "$escapedDbPath"]
    }
  }
}
"@

Write-ConfigFile -Path $ConfigPaths.ClaudeCode -Content $claudeCodeConfig
Write-Host "  Done: Set to mcp-server-sqlite (pointing to test DB)" -ForegroundColor Green

# ============================================
# Codex: sequential-thinking
# ============================================
Write-Host ""
Write-Host "--- Seeding Codex ---" -ForegroundColor Cyan

# Codex uses TOML format
$codexConfig = @'
# MCP Server Configuration for Codex

[mcp_servers.sequential-thinking]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-sequential-thinking"]
'@

Write-ConfigFile -Path $ConfigPaths.Codex -Content $codexConfig
Write-Host "  Done: Set to sequential-thinking server" -ForegroundColor Green

# ============================================
# Cursor: filesystem
# ============================================
Write-Host ""
Write-Host "--- Seeding Cursor ---" -ForegroundColor Cyan

# Escape project root path for JSON
$escapedProjectRoot = $ProjectRoot -replace '\\', '\\\\'

$cursorConfig = @"
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "$escapedProjectRoot"]
    }
  }
}
"@

Write-ConfigFile -Path $ConfigPaths.Cursor -Content $cursorConfig
Write-Host "  Done: Set to filesystem server (scoped to project root)" -ForegroundColor Green

# ============================================
# Windsurf: mcp-server-time
# ============================================
Write-Host ""
Write-Host "--- Seeding Windsurf ---" -ForegroundColor Cyan

$windsurfConfig = @'
{
  "mcpServers": {
    "time": {
      "command": "uvx",
      "args": ["mcp-server-time"]
    }
  }
}
'@

Write-ConfigFile -Path $ConfigPaths.Windsurf -Content $windsurfConfig
Write-Host "  Done: Set to mcp-server-time server" -ForegroundColor Green

# ============================================
# Summary
# ============================================
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Seeding Complete" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
if (-not $NoBackup) {
    Write-Host "Backups saved to: $BackupDir" -ForegroundColor Gray
}
Write-Host ""
Write-Host "Server distribution:" -ForegroundColor White
Write-Host "  Claude Desktop : everything, memory (npx)" -ForegroundColor Gray
Write-Host "  Claude Code    : sqlite (uvx, PyPI)" -ForegroundColor Gray
Write-Host "  Codex          : sequential-thinking (npx)" -ForegroundColor Gray
Write-Host "  Cursor         : filesystem (npx)" -ForegroundColor Gray
Write-Host "  Windsurf       : time (uvx, PyPI)" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Restart any running MCP clients"
Write-Host "  2. Run 'gatekit --debug' to start Guided Setup testing"
Write-Host ""
