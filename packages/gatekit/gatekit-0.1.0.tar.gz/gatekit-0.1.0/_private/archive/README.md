# Archived Documentation

> **WARNING: HISTORICAL CONTENT ONLY - DO NOT MODIFY**
>
> This directory contains deprecated documentation that does NOT reflect current Gatekit capabilities.
> Do not use this content for understanding current features or capabilities.
> **Archived documents are never updated** - they are frozen historical snapshots.

## Purpose

This archive preserves historical documentation for reference only:
- Past design explorations
- Abandoned feature planning
- Superseded configuration formats
- Historical decision context

## Directory Structure

```
archive/
├── cef-planning/           # CEF format - NEVER IMPLEMENTED
├── enterprise-planning/    # SIEM, compliance, transport - NEVER IMPLEMENTED
├── financial-services/     # Enterprise use cases - NOT CURRENT FOCUS
├── user/                   # Old user docs - SUPERSEDED
├── developer/              # Old dev docs - SUPERSEDED
├── v0.1.0/                 # Pre-release planning
└── ...
```

## What Was Never Built

The following features appear in archived docs but **do not exist** in Gatekit:

| Feature | Status | Notes |
|---------|--------|-------|
| CEF audit format | Never implemented | Only JSONL, CSV, text exist |
| SIEM integration | Never implemented | No Splunk/QRadar/Sentinel |
| TLS syslog transport | Never implemented | File-based logging only |
| Compliance platforms | Never implemented | No SOC2/HIPAA/SOX features |
| Enterprise dashboards | Never implemented | TUI only |

## Search Exclusion

This directory is configured to be **excluded from ripgrep searches** via `.rgignore` and `.ignore` files. This prevents AI tools from accidentally treating historical content as current capabilities.

## Current Documentation

For accurate, current information:
- **Configuration**: `docs/configuration-specification.md`
- **Architecture**: `docs/decision-records/`
- **Active development**: `_private/todos/`
- **Project overview**: Root `CLAUDE.md`
