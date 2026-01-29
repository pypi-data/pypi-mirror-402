#!/bin/bash
#
# Sync current state to public repository
#
# Usage: ./scripts/sync-to-public.sh v0.1.0
#
# This script copies the current state of the private repo to the public repo,
# excluding private content (_private/), and creates a commit with the release version.
# No git history is transferred - each sync is a clean snapshot.

set -e

# Configuration
PUBLIC_REPO_PATH="../gatekit-public"  # Path to local clone of public repo
VERSION="${1:-}"

if [[ -z "$VERSION" ]]; then
    echo "Usage: ./scripts/sync-to-public.sh v0.1.0"
    echo ""
    echo "This will:"
    echo "  1. Copy current state to public repo (excluding _private/)"
    echo "  2. Commit as 'Release <version>'"
    echo "  3. Tag with <version>"
    exit 1
fi

echo "Syncing to public repository as $VERSION..."

# Ensure we're in private repo root
if [[ ! -f "pyproject.toml" ]] || [[ ! -d "gatekit" ]]; then
    echo "Error: Must run from private repo root"
    exit 1
fi

# Ensure public repo exists
if [[ ! -d "$PUBLIC_REPO_PATH/.git" ]]; then
    echo "Error: Public repo not found at $PUBLIC_REPO_PATH"
    echo "Create it first:"
    echo "  1. Create repo on GitHub"
    echo "  2. git clone <url> $PUBLIC_REPO_PATH"
    exit 1
fi

# Save current directory
PRIVATE_REPO_PATH="$(pwd)"

# Clean public repo (keep .git)
echo "Cleaning public repo..."
cd "$PUBLIC_REPO_PATH"
find . -mindepth 1 -maxdepth 1 ! -name '.git' -exec rm -rf {} +

# Copy current state from private (excluding private content and build artifacts)
echo "Copying files..."
cd "$PRIVATE_REPO_PATH"
rsync -av \
    --exclude='_private/' \
    --exclude='.git/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache/' \
    --exclude='.ruff_cache/' \
    --exclude='.venv/' \
    --exclude='*.egg-info/' \
    --exclude='.uv-cache/' \
    --exclude='.uv_cache/' \
    --exclude='.uv_tools/' \
    --exclude='dist/' \
    --exclude='.coverage' \
    --exclude='.coverage.*' \
    --exclude='htmlcov/' \
    --exclude='scratch/' \
    --exclude='logs/' \
    --exclude='*.log' \
    --exclude='.DS_Store' \
    --exclude='configs/*.yaml' \
    --exclude='configs/logs/' \
    --exclude='tests/integration/test_data/' \
    --exclude='tests/validation/' \
    --exclude='CLAUDE.md' \
    --exclude='AGENTS.md' \
    --exclude='.claude/' \
    --exclude='.github/instructions/' \
    --exclude='.vscode/' \
    --exclude='.mypy_cache/' \
    --exclude='gatekit/tui/TUI_DEBUG_TESTING_GUIDE.md' \
    --exclude='docs/testing/' \
    --exclude='scripts/' \
    . "$PUBLIC_REPO_PATH/"

# Commit and tag in public repo
echo "Creating commit and tag..."
cd "$PUBLIC_REPO_PATH"
git add -A
git commit -m "Release $VERSION" || echo "No changes to commit"
git tag -a "$VERSION" -m "Release $VERSION"

echo ""
echo "========================================="
echo "Sync complete!"
echo ""
echo "Review the changes:"
echo "  cd $PUBLIC_REPO_PATH"
echo "  git log --oneline -5"
echo "  git diff HEAD~1 --stat"
echo ""
echo "Then push:"
echo "  git push origin main"
echo "  git push origin $VERSION"
echo "========================================="
