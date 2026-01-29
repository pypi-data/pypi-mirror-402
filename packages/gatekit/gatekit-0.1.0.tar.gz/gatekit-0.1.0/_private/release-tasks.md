# Gatekit v0.1.0 Release Checklist

## Phase 1: Pre-Release Preparation

### Documentation & Metadata
- [x] README.md: Installation instructions (uv, pipx, pip)
- [x] README.md: Badge URL points to public repo
- [x] CHANGELOG.md: Created with release notes
- [x] CONTRIBUTING.md: Created (not accepting contributions yet)
- [x] SECURITY.md: Created with vulnerability reporting process
- [x] pyproject.toml: Keywords, classifiers, URLs configured
- [x] LICENSE: Apache 2.0

### Infrastructure
- [x] Email: security@gatekit.ai created
- [x] Sync script: Excludes CLAUDE.md, AGENTS.md, _private/, testing/

### Testing & Verification
- [x] All tests pass: `pytest tests/ -n auto`
- [x] Smoke tests pass: `pytest tests/ -n auto --run-slow`
- [x] Linting passes: `uv run ruff check gatekit`
- [x] TUI walkthrough on macOS
- [x] TUI walkthrough on Windows
- [x] Guided setup wizard end-to-end
- [x] Config editor open/save
- [x] Gateway runs with example config
- [x] TestPyPI installation works

---

## Phase 2: Final Checks (Day of Release)

### Content Review
- [x] README has no placeholder text
- [x] All URLs in README/docs are valid (GitHub URLs will work after repo creation)

### Website Analytics
- [x] Add Pirsch analytics to website (free tier, cookieless, GDPR-compliant)

### Build Verification
```bash
# Clean build
rm -rf dist/
uv build

# Verify package contents
tar -tzf dist/*.tar.gz | head -20

# Check package metadata renders correctly
uv run twine check dist/*
```

---

## Phase 3: GitHub Repository Setup

### Create Public Repository
- [x] Create `gatekit-ai/gatekit` repository on GitHub
- [x] Set repository description and topics
- [x] Configure repository settings:
  - [x] Enable Issues
  - [x] Disable Wiki (docs in repo)
  - [x] Enable Discussions
  - [x] Configure issue templates (bug report, feature request)
  - [x] Configure Discussions welcome post
- [x] Enable Private Vulnerability Reporting (Settings → Code security and analysis)
- [x] Enable Dependency graph and Dependabot alerts

### Final Commit
- [x] Update CHANGELOG.md date from "TBD" to actual release date
- [ ] Commit: `git add -A && git commit -m "Release v0.1.0"`

### Sync Code to Public Repo
```bash
# Tag the release in private repo
git tag v0.1.0
git push origin v0.1.0

# Run sync script
./scripts/sync-to-public.sh v0.1.0

# Review changes in public repo
cd ../gatekit-public
git log --oneline -5
git diff HEAD~1 --stat

# Push to GitHub
git push origin main
git push origin v0.1.0
```

### Post-Push Verification
- [ ] Verify README renders correctly on GitHub
- [ ] Verify all links work

---

## Phase 4: Update README for PyPI

PyPI doesn't resolve relative image paths. Now that the public repo exists, update README to use absolute URLs.

### Update Image URLs
- [ ] Change relative paths to absolute GitHub raw URLs:
  ```
  docs/images/gatekit-config-editor.png
  → https://raw.githubusercontent.com/gatekit-ai/gatekit/main/docs/images/gatekit-config-editor.png
  ```
- [ ] Update all three images in README.md

### Rebuild Package
```bash
rm -rf dist/
uv build
uv run twine check dist/*
```

### Commit and Re-sync
```bash
git add -A && git commit -m "Use absolute URLs for PyPI images"
git push origin main

# Re-sync to public repo
./scripts/sync-to-public.sh
cd ../gatekit-public
git push origin main
```

---

## Phase 5: PyPI Publication

### Publish to PyPI
```bash
# Ensure you're authenticated
# Option 1: API token in ~/.pypirc
# Option 2: uv will prompt for credentials

uv publish
```

### Verify PyPI Listing
- [ ] Package appears at https://pypi.org/project/gatekit/
- [ ] README/description renders correctly
- [ ] **Images display correctly** (this was the whole point)
- [ ] All metadata displays properly
- [ ] Version shows as 0.1.0

### Test Fresh Installation
```bash
# In a fresh environment
pip install gatekit
gatekit --version
gatekit --help
gatekit-gateway --help
```

---

## Phase 6: GitHub Release

### Create GitHub Release
- [ ] Go to https://github.com/gatekit-ai/gatekit/releases
- [ ] Click "Create a new release"
- [ ] Select tag: v0.1.0
- [ ] Title: "v0.1.0 - Initial Release"
- [ ] Copy release notes from CHANGELOG.md
- [ ] Publish release

---

## Phase 7: Post-Release

### Verification
- [ ] `pip install gatekit` works globally
- [ ] `pipx install gatekit` works
- [ ] `uv tool install gatekit` works

### Announcements (Optional)
- [ ] Post to relevant communities if desired

---

## Quick Reference: Release Commands

```bash
# 1. Final test
pytest tests/ -n auto
uv run ruff check gatekit

# 2. Build and verify
rm -rf dist/
uv build
uv run twine check dist/*

# 3. Create public repo on GitHub (gatekit-ai/gatekit)

# 4. Update CHANGELOG date, commit, tag, sync
# Edit CHANGELOG.md, change TBD to YYYY-MM-DD
git add -A && git commit -m "Release v0.1.0"
git tag v0.1.0
git push origin main v0.1.0
./scripts/sync-to-public.sh v0.1.0

# 5. Push public repo
cd ../gatekit-public
git push origin main v0.1.0

# 6. Update README image URLs for PyPI (relative → absolute)
cd ../gatekit
# Edit README.md: docs/images/... → https://raw.githubusercontent.com/gatekit-ai/gatekit/main/docs/images/...
git add -A && git commit -m "Use absolute URLs for PyPI images"
git push origin main
./scripts/sync-to-public.sh
cd ../gatekit-public && git push origin main

# 7. Rebuild and publish to PyPI
cd ../gatekit
rm -rf dist/
uv build
uv publish

# 8. Create GitHub release at github.com/gatekit-ai/gatekit/releases
```

---

## What's Already Complete

- TUI: 15K+ LOC, 81 test files
- Plugin System: 8 production plugins
- Gateway: Full MCP proxy
- Core Docs: Configuration spec, plugin guide, 27 ADRs
- License: Apache 2.0
- TestPyPI: Validated installation flow
