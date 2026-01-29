# Tool Manager Blocklist Removal Plan

## Context
- Tool Manager currently supports `mode="allowlist"` and `mode="blocklist"`, with legacy migration logic for action-based configs.
- Renaming support only works for tools present in the allowlist; blocklist entries cannot be renamed.
- The upcoming TUI flow plans to fetch live tool catalogs, default everything to enabled, and let operators uncheck tools they want hidden. This matches a pure allowlist model.
- We have not shipped blocklist support yet, so we can break compatibility as long as we update docs/tests/schemas in the same change.

## High-Level Goals
1. Remove explicit mode handling and legacy migration helpers from `gatekit/plugins/middleware/tool_manager.py`. ✅
2. Make the allowlist semantics explicit: tools absent from the list are hidden; empty list blocks all tools. ✅
3. Ensure configuration schemas, generated artifacts, and TUI forms only expose the allowlist model. ✅ (TUI form updates pending follow-up sweep)
4. Update tests, docs, sample configs, and audit metadata to the new terminology (`policy=allowlist`, etc.). ✅
5. Provide a clean migration story (fail loudly if legacy `mode`/`action` fields remain in configs). ✅

## Open Questions
- **Runtime defaults**: confirm that enabling the plugin with `tools: []` is the intended way to block everything.
- **New tool discovery**: communicate in TUI/UX that newly surfaced tools remain hidden until re-synced; decide whether to add an "auto-enable new tools" toggle later.
- **Operational telemetry**: decide on replacement metadata fields (e.g., `policy="allowlist"`) now that `mode` is gone.

## Workstreams & TODOs

### 1. Runtime Refactor (owner: middleware)
- [x] Remove `_migrate_old_config`, `_parse_allow_config`, and `_parse_rename_config` from `gatekit/plugins/middleware/tool_manager.py`.
- [x] Collapse mode branching in `process_request` and `process_response` to a single allowlist path.
- [x] Normalize rename metadata to use explicit `policy` flag instead of `mode`.
- [x] Reject unknown fields (`mode`, `action`, legacy keys) during parsing with clear error messages.
- [x] Keep rename logic intact; ensure allowlist entries support `display_name`/`display_description`.

### 2. Config Schema & Validation (owner: platform/config)
- [x] Update `ToolManagerPlugin.get_json_schema()` to remove `mode` enum and legacy messaging.
- [x] Regenerate JSON schema artifacts (`scripts/generate_schemas.py`) after code change.
- [x] Adjust `configs/gatekit.yaml` sample to list tools without `action`/`mode`.
- [x] Update `PluginConfigSchema` validations or modal helpers if they currently expect a `mode` field.
- [x] Update TUI forms/copy to reflect the checkbox-only allowlist flow (docs: `tui-developer-guidelines.md`).

### 3. Tests (owner: QA/dev)
- [x] Rewrite unit tests in `tests/unit/test_tool_manager_plugin.py` and `tests/unit/test_tool_manager_response_filtering.py` to align with allowlist-only behavior.
- [x] Delete or repurpose `tests/unit/test_tool_manager_mode_persistence.py`.
- [x] Update integration tests (`test_proxy_response_filtering.py`, `test_aggregated_tools_list_integration.py`, `test_policy_integration.py`, etc.) to drop blocklist scenarios and assert new metadata keys.
- [x] Adjust config loader / plugin schema tests that reference `mode` or `action`.
- [ ] Run full suite (`uv run pytest --no-header -v`) after changes. _(Partially executed; see notes)_

### 4. Documentation & SDK Samples (owner: docs)
- [x] Refresh README sections describing Tool Manager modes.
- [x] Update `docs/security-model.md`, decision records, and archived tutorials to strike blocklist references or mark them historical. _(Decision records/archives remain for historical context)_
- [x] Note the new workflow in TUI documentation and upgrade notes (`tui-developer-guidelines.md`, `upgrade-notes.md`).

### 5. Communication & Release Notes (owner: product)
- [ ] Document the breaking change in `docs/pre-release-tasks/` or CHANGELOG (once created).
- [ ] Provide guidance for operators transitioning off blocklist configs (fail-fast error message + remediation steps).

## Sequencing Proposal
1. Implement runtime refactor + schema updates in a single PR, with failing tests temporarily skipped locally.
2. Update unit/integration tests in same PR to keep CI green.
3. Follow up with docs + TUI copy sweep.
4. Ship release note once everything merged.

## Validation Checklist
- [ ] `uv run pytest --no-header -v`
- [ ] `uv run ruff check gatekit tests`
- [ ] `uv run black --check gatekit tests`
- [ ] Manual TUI sanity check once the Configure modal is wired to the new schema.
