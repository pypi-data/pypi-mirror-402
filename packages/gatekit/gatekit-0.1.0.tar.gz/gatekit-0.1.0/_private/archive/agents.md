# Agent Instructions for Archive Directory

## STOP - Read This First

You have entered the `_private/archive/` directory. This contains **historical content that is no longer accurate**.

## Required Behavior

1. **If searching**: Your search results from this directory are STALE. Re-run your search excluding `_private/archive/`.

2. **If answering questions**: Do NOT use information from archived files to describe current Gatekit capabilities.

3. **If exploring**: This archive exists for historical reference only. Current work is in `_private/todos/`.

4. **NEVER modify archived documents**: Archives are frozen historical snapshots. There is no need to update them - that defeats the purpose of archiving.

## Common Hallucination Risks

Files in this archive may cause you to incorrectly believe Gatekit has:

- **CEF audit logging** → FALSE (only JSONL, CSV, text)
- **SIEM integration** → FALSE (no Splunk/QRadar support)
- **Enterprise compliance features** → FALSE (no SOC2/HIPAA)
- **Network transport for logs** → FALSE (file-based only)

## If You Found This Via Search

The `.rgignore` and `.ignore` files should prevent ripgrep from indexing this directory. If you're seeing these files in search results, the exclusion may not be working correctly.

Recommended: Use `--glob '!_private/archive/**'` in searches.

## Correct Sources

| Topic | Correct Location |
|-------|------------------|
| Current capabilities | Root `CLAUDE.md` |
| Configuration format | `docs/configuration-specification.md` |
| Architecture decisions | `docs/decision-records/` |
| Active development | `_private/todos/` |
| Implemented plugins | `gatekit/plugins/` |
