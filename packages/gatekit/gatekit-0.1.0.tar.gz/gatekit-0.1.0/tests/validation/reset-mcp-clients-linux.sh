#!/bin/bash
# Reset MCP Clients to Known Baseline State - LINUX VERSION
# For manual validation testing of Gatekit Guided Setup (Section 2)
#
# This script sets up configs for testing Guided Setup on Linux over SSH.
#
# REAL CLIENTS (can test E2E on Linux):
#   Claude Code: context7 server (CLI tool, works natively)
#   Codex: everything server (CLI tool, works natively)
#
# MOCK CLIENTS (for TUI detection testing only):
#   Claude Desktop: everything server (GUI app - no Linux native support)
#   Cursor: puppeteer server (GUI app - MCP config is local-only)
#   Windsurf: sequential-thinking server (GUI app - MCP config is local-only)
#
# NOTE: Claude Desktop and Codex both have "everything" server - tests deduplication!
#
# The mock configs allow you to test that Guided Setup correctly:
#   - Detects all 5 client config files
#   - Displays servers from each client
#   - Generates correct migration instructions
#
# However, you cannot verify the generated instructions work for mock clients
# since those GUI apps don't run on Linux / read configs from the SSH server.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Linux config paths (verified against official documentation)
# Claude Desktop: ~/.config/Claude/ on Linux (unofficial packages only)
# Claude Code: ~/.claude.json (same on all platforms)
# Codex: ~/.codex/config.toml (same on all platforms)
# Cursor: ~/.cursor/mcp.json (same on all platforms)
# Windsurf: ~/.codeium/windsurf/mcp_config.json (same on all platforms)

CLAUDE_DESKTOP_CONFIG="$HOME/.config/Claude/claude_desktop_config.json"
CLAUDE_CODE_CONFIG="$HOME/.claude.json"
CODEX_CONFIG="$HOME/.codex/config.toml"
CURSOR_CONFIG="$HOME/.cursor/mcp.json"
WINDSURF_CONFIG="$HOME/.codeium/windsurf/mcp_config.json"
PROJECT_MCP_CONFIG="$SCRIPT_DIR/../../.mcp.json"  # Gatekit project-level

# Parse arguments
SKIP_CONFIRM=false
for arg in "$@"; do
    case $arg in
        -y|--yes)
            SKIP_CONFIRM=true
            shift
            ;;
    esac
done

echo "=========================================="
echo "  MCP Client Reset Script (Linux)"
echo "  For Gatekit Manual Validation"
echo "=========================================="
echo ""
echo "This script will set up MCP client configs for testing Guided Setup."
echo ""
echo -e "${CYAN}REAL CLIENTS (E2E testable on Linux):${NC}"
echo "  - Claude Code: context7 server"
echo "  - Codex: everything server"
echo ""
echo -e "${YELLOW}MOCK CLIENTS (TUI detection testing only):${NC}"
echo "  - Claude Desktop: everything server"
echo "  - Cursor: puppeteer server"
echo "  - Windsurf: sequential-thinking server"
echo ""
echo -e "${CYAN}NOTE:${NC} Claude Desktop + Codex both have 'everything' - tests deduplication!"
echo ""
echo -e "${YELLOW}NOTE: Mock client configs test TUI detection only.${NC}"
echo "These GUI apps don't run on Linux / read configs from SSH servers."
echo ""
echo "Backups will be saved to: $BACKUP_DIR"
echo ""

if [[ "$SKIP_CONFIRM" != true ]]; then
    read -p "Continue? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

backup_file() {
    local file="$1"
    local name="$2"
    if [[ -f "$file" ]]; then
        local ext="${file##*.}"
        cp "$file" "$BACKUP_DIR/${name}-${TIMESTAMP}.${ext}"
        echo -e "  ${GREEN}Backed up${NC}: $file"
    fi
}

echo ""
echo "--- Creating backups ---"
backup_file "$CLAUDE_DESKTOP_CONFIG" "claude-desktop"
backup_file "$CLAUDE_CODE_CONFIG" "claude-code"
backup_file "$CODEX_CONFIG" "codex"
backup_file "$CURSOR_CONFIG" "cursor"
backup_file "$WINDSURF_CONFIG" "windsurf"
if [[ -f "$PROJECT_MCP_CONFIG" ]]; then
    backup_file "$PROJECT_MCP_CONFIG" "project-mcp"
fi

# ============================================
# Claude Desktop (MOCK - for detection testing)
# ============================================
echo ""
echo -e "--- Resetting Claude Desktop ${YELLOW}(MOCK)${NC} ---"

mkdir -p "$(dirname "$CLAUDE_DESKTOP_CONFIG")"
cat > "$CLAUDE_DESKTOP_CONFIG" << 'EOF'
{
  "mcpServers": {
    "everything": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-everything"
      ]
    }
  }
}
EOF
echo -e "  ${GREEN}Done${NC}: Set to everything server (mock config for TUI testing)"

# ============================================
# Claude Code (REAL - E2E testable)
# ============================================
echo ""
echo -e "--- Resetting Claude Code ${CYAN}(REAL)${NC} ---"

# Check if claude CLI is available
if command -v claude &> /dev/null; then
    # Remove all user-scope servers
    CURRENT_SERVERS=$(claude mcp list --scope user 2>/dev/null | grep -E '^\s+\w' | awk '{print $1}' || true)
    for server in $CURRENT_SERVERS; do
        claude mcp remove "$server" --scope user 2>/dev/null || true
        echo "  Removed (user): $server"
    done
fi

# Remove project-level .mcp.json in gatekit directory if it exists
if [[ -f "$PROJECT_MCP_CONFIG" ]]; then
    rm "$PROJECT_MCP_CONFIG"
    echo "  Removed: $PROJECT_MCP_CONFIG"
fi

# Write clean config with only context7 at user level
cat > "$CLAUDE_CODE_CONFIG" << 'EOF'
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
EOF
echo -e "  ${GREEN}Done${NC}: Reset ~/.claude.json to context7 only"

# ============================================
# Codex (REAL - E2E testable)
# ============================================
echo ""
echo -e "--- Resetting Codex ${CYAN}(REAL)${NC} ---"

# Codex uses TOML config at ~/.codex/config.toml
mkdir -p "$(dirname "$CODEX_CONFIG")"

if [[ -f "$CODEX_CONFIG" ]]; then
    # Remove existing [mcp_servers.*] sections, keep everything else
    awk '
    /^\[mcp_servers\./ { in_mcp = 1; next }
    /^\[/ { in_mcp = 0 }
    !in_mcp { print }
    ' "$CODEX_CONFIG" > "${CODEX_CONFIG}.tmp" && mv "${CODEX_CONFIG}.tmp" "$CODEX_CONFIG"
    echo "  Removed existing MCP servers"
else
    # Create minimal config if none exists
    cat > "$CODEX_CONFIG" << 'EOF'
# Codex configuration
EOF
fi

# Add the everything server
cat >> "$CODEX_CONFIG" << 'EOF'

[mcp_servers.everything]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-everything"]
EOF
echo -e "  ${GREEN}Done${NC}: Set to everything server"

# ============================================
# Cursor (MOCK - for detection testing)
# ============================================
echo ""
echo -e "--- Resetting Cursor ${YELLOW}(MOCK)${NC} ---"

mkdir -p "$(dirname "$CURSOR_CONFIG")"
cat > "$CURSOR_CONFIG" << 'EOF'
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-puppeteer"
      ]
    }
  }
}
EOF
echo -e "  ${GREEN}Done${NC}: Set to puppeteer server (mock config for TUI testing)"

# ============================================
# Windsurf (MOCK - for detection testing)
# ============================================
echo ""
echo -e "--- Resetting Windsurf ${YELLOW}(MOCK)${NC} ---"

mkdir -p "$(dirname "$WINDSURF_CONFIG")"
cat > "$WINDSURF_CONFIG" << 'EOF'
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sequential-thinking"
      ]
    }
  }
}
EOF
echo -e "  ${GREEN}Done${NC}: Set to sequential-thinking server (mock config for TUI testing)"

# ============================================
# Summary
# ============================================
echo ""
echo "=========================================="
echo -e "  ${GREEN}Reset Complete${NC}"
echo "=========================================="
echo ""
echo "Backups saved to: $BACKUP_DIR"
echo ""
echo -e "${CYAN}What you can test on Linux:${NC}"
echo "  1. TUI Guided Setup detection (all 5 clients)"
echo "  2. Server selection and deduplication"
echo "  3. Config generation and instruction display"
echo "  4. Claude Code E2E: Apply generated 'claude mcp' commands"
echo "  5. Codex E2E: Verify generated TOML config works"
echo ""
echo -e "${YELLOW}What requires macOS/Windows:${NC}"
echo "  - Claude Desktop E2E (GUI app)"
echo "  - Cursor E2E (MCP config is local to GUI)"
echo "  - Windsurf E2E (MCP config is local to GUI)"
echo ""
echo "Next steps:"
echo "  1. Run 'gatekit --debug' to start Guided Setup testing"
echo "  2. Verify all 5 clients appear with their servers"
echo "  3. Test Claude Code migration commands work"
echo ""
