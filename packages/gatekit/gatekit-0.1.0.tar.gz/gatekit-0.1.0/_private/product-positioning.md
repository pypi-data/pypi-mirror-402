# Gatekit Positioning

## Tagline

> An extensible MCP gateway with a terminal UI.

**Subtitle:**
> Configure your gateway visually in your terminal.

## Features

- Tool filtering, renaming, and description customization
- Audit logging (JSON Lines, CSV, human-readable)
- PII and secrets detection (regex-based)
- Extend with your own Python plugins when built-ins aren't enough

---

## Internal North Star

### "A Personal MCP Gateway for Privacy-Conscious Developers"

This is our **initial positioning** for prioritizing development—not a permanent constraint.

**Evolution path:** As the product matures and we establish a revenue path, enterprise features (team management, SSO, compliance tooling) may be added. This positioning helps us focus limited resources now, not forever. The archived enterprise planning docs can be revisited when the time is right.

**Why this positioning:**
- Architecture IS personal: local-only, TUI, Python plugins
- Avoids funded enterprise competition (Runlayer $11M, etc.)
- Privacy features (PII detection, local-only, audit logs) make sense for individuals
- Matches validated problems: config management, debugging, token optimization

**Current gaps (honest assessment):**
- PII/secrets filtering is basic (regex-based, not production-grade)
- No advanced privacy features yet
- Plugin ecosystem doesn't exist

**How to use this north star:**
When deciding where to focus resources, ask:
1. Does this help privacy-conscious individual developers?
2. Does this keep data local and under user control?
3. Does this avoid enterprise complexity (SSO, teams, dashboards)?

If yes to all three, it's aligned. If no, question whether it's the right priority.

---

## Announcement Strategy

- Lead with TUI differentiator
- Include carousel of TUI screenshots
- Keep it simple - don't oversell extensibility
- Don't claim "privacy-focused" until features support it

## Research Summary

### Competitive Landscape

**Enterprise players (Runlayer, MCP Manager, Lunar.dev):**
- Target teams with budgets, SSO, compliance needs
- Not our market

**Popular open source (2k+ stars):**
- sparfenyuk/mcp-proxy: Protocol bridging, simple
- Unla: Zero-code + web UI

**Key insight:** Simplicity and clear purpose wins. The most popular projects do one thing well.

### Gatekit's Differentiators

1. **Terminal UI** - Nobody else has one (Unla has web UI)
2. **Python-native** - Most gateways are Go/Rust/TypeScript
3. **Local-only** - Traffic never leaves your machine
4. **Open plugin system** - Extend with Python (competitors are closed)

### What We're NOT

- Not enterprise-focused (no SSO, no team management)
- Not leading with extensibility (it's an escape hatch, not the pitch)
- Not competing on security features (regex-based, not production-grade)
- Not claiming "privacy-focused" externally yet (north star, not current state)
