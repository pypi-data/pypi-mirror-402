# Validation & Tests

## Tasks
- [ ] Update `ToolSelectionField` to export schema-compliant data for save: `[{"tool": id, "display_name": optional, "display_description": optional}]`.
- [ ] Teach reset logic to rehydrate the custom widget (checkbox states + inputs) from `original_config`.
- [ ] Add unit coverage for data extraction/merge logic (prefer `tests/unit/tui` if available).
- [ ] Extend integration tests for Tool Manager modal to cover discovery data, manual entries, disabling tools, and empty selections (block-all scenario).
- [ ] Verify validator errors surface on the custom inputs (e.g., invalid tool id pattern) and highlight the offending row.

## Manual QA
- Smoke test in TUI: open Tool Manager for global and server contexts; toggle checkboxes; ensure save persists to config.
- Run `uv run pytest --no-header -v` to cover new tests.
- Run `uv run gatekit` to confirm layout renders within existing modal dimensions.
