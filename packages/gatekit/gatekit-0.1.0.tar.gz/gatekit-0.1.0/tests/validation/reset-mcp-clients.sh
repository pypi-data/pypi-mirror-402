#!/bin/bash
# Reset MCP Clients to Known Baseline State
# For manual validation testing of Gatekit Guided Setup (Section 2)
#
# Baseline State:
#   Claude Desktop: domain-names server
#   Claude Code: context7 server
#   Codex: (no servers)
#   Cursor: puppeteer server
#   Windsurf: sequential-thinking server

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Config paths
CLAUDE_DESKTOP_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
CLAUDE_CODE_CONFIG="$HOME/.claude.json"
CODEX_CONFIG="$HOME/.codex/config.toml"
CURSOR_CONFIG="$HOME/.cursor/mcp.json"
WINDSURF_CONFIG="$HOME/.codeium/windsurf/mcp_config.json"
PROJECT_MCP_CONFIG="$SCRIPT_DIR/../../.mcp.json"  # Gatekit project-level

echo "=========================================="
echo "  MCP Client Reset Script"
echo "  For Gatekit Manual Validation"
echo "=========================================="
echo ""
echo "This script will reset all 5 MCP clients to a known baseline state:"
echo "  - Claude Desktop: domain-names server"
echo "  - Claude Code: context7 server"
echo "  - Codex: (no servers)"
echo "  - Cursor: puppeteer server"
echo "  - Windsurf: sequential-thinking server"
echo ""
echo -e "${YELLOW}WARNING: This will overwrite your current MCP configurations!${NC}"
echo "Backups will be saved to: $BACKUP_DIR"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

backup_file() {
    local file="$1"
    local name="$2"
    if [[ -f "$file" ]]; then
        cp "$file" "$BACKUP_DIR/${name}-${TIMESTAMP}.json"
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
# Claude Desktop
# ============================================
echo ""
echo "--- Resetting Claude Desktop ---"

mkdir -p "$(dirname "$CLAUDE_DESKTOP_CONFIG")"
cat > "$CLAUDE_DESKTOP_CONFIG" << 'EOF'
{
  "mcpServers": {
    "domain-names": {
      "command": "/Users/dbright/mcp/domain_names/.venv/bin/python",
      "args": [
        "/Users/dbright/mcp/domain_names/main.py"
      ],
      "cwd": "/Users/dbright/mcp/domain_names"
    }
  }
}
EOF
echo -e "  ${GREEN}Done${NC}: Set to domain-names server"

# ============================================
# Claude Code
# ============================================
echo ""
echo "--- Resetting Claude Code ---"

# Remove all user-scope servers (iterate through list)
CURRENT_SERVERS=$(claude mcp list --scope user 2>/dev/null | grep -E '^\s+\w' | awk '{print $1}' || true)
for server in $CURRENT_SERVERS; do
    claude mcp remove "$server" --scope user 2>/dev/null || true
    echo "  Removed (user): $server"
done

# Remove project-level .mcp.json in gatekit directory if it exists
if [[ -f "$PROJECT_MCP_CONFIG" ]]; then
    rm "$PROJECT_MCP_CONFIG"
    echo "  Removed: $PROJECT_MCP_CONFIG"
fi

# Also clean the projects block from ~/.claude.json if it exists
# We rewrite the file with only mcpServers containing context7
if [[ -f "$CLAUDE_CODE_CONFIG" ]]; then
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
else
    # If no config exists, add via CLI
    claude mcp add --transport stdio --scope user context7 \
        -- npx -y @upstash/context7-mcp
    echo -e "  ${GREEN}Done${NC}: Added context7 server"
fi

# ============================================
# Codex
# ============================================
echo ""
echo "--- Resetting Codex ---"

# Codex uses TOML config at ~/.codex/config.toml
# To ensure zero servers, we remove all [mcp_servers.*] sections
if [[ -f "$CODEX_CONFIG" ]]; then
    # Use awk to remove [mcp_servers.*] sections and their contents
    # Keeps everything else intact
    awk '
    /^\[mcp_servers\./ { in_mcp = 1; next }
    /^\[/ { in_mcp = 0 }
    !in_mcp { print }
    ' "$CODEX_CONFIG" > "${CODEX_CONFIG}.tmp" && mv "${CODEX_CONFIG}.tmp" "$CODEX_CONFIG"
    echo -e "  ${GREEN}Done${NC}: Removed all MCP servers from config.toml"
else
    echo "  No Codex config found (OK - baseline is zero servers)"
fi

# ============================================
# Cursor
# ============================================
echo ""
echo "--- Resetting Cursor ---"

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
echo -e "  ${GREEN}Done${NC}: Set to puppeteer server"

# ============================================
# Windsurf
# ============================================
echo ""
echo "--- Resetting Windsurf ---"

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
echo -e "  ${GREEN}Done${NC}: Set to sequential-thinking server"

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
echo "Next steps:"
echo "  1. Restart any running MCP clients"
echo "  2. Run 'gatekit --debug' to start Guided Setup testing"
echo ""
