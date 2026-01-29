# ARCHIVED CONTENT - DO NOT USE OR MODIFY

## Critical Warning

**STOP. This directory contains HISTORICAL content that NO LONGER APPLIES to Gatekit.**

Everything in `_private/archive/` is:
- **Deprecated** - superseded by current implementation
- **Potentially misleading** - may describe features that were never built
- **Not representative** - of current architecture, capabilities, or roadmap
- **Frozen** - archived documents are never updated, by definition

## What This Means For You

1. **DO NOT** cite information from this directory as current capabilities
2. **DO NOT** assume features described here exist in the codebase
3. **DO NOT** use configuration examples from archived docs
4. **DO NOT** reference archived planning docs when answering user questions
5. **DO NOT** update or modify archived documents - they are historical snapshots

## Why This Archive Exists

Historical documents are preserved for:
- Understanding past design decisions
- Auditing the evolution of the project
- Reference if we need to revisit abandoned approaches

## If You're Searching For Something

If a search led you here, **search again excluding this directory**. The information you found is outdated.

Current documentation locations:
- **Configuration**: `docs/configuration-specification.md`
- **Architecture**: `docs/decision-records/`
- **Active work**: `_private/todos/`

## Specific Warnings

### CEF (Common Event Format)
CEF audit logging was **planned but never implemented**. Gatekit v0.1.x only supports:
- JSON Lines
- CSV
- Human-readable text

Any references to CEF in this archive are historical planning artifacts.

### Enterprise Features (SIEM, Compliance, Transport)
Enterprise-focused features like SIEM integration, compliance platforms, and network transport were explored but **not built**. Gatekit is positioned as a personal developer tool, not an enterprise gateway.
