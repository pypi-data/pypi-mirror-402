# Acceptance Testing Plan

Status: **COMPLETE** - all programmatic preparatory work and automated tests implemented for v0.1.x

## Objectives

- Prove that the TUI can author, edit, and persist every supported plugin configuration without corrupting data.
- Prove that `gatekit-gateway` enforces the configured behavior for representative scenarios (security, middleware, auditing).
- Provide a deterministic manual checklist that mirrors real operator workflows so we can run a final confidence pass before a release.

## Preparatory Work (programmatic)

### 1. Golden Configuration Suite ✅
- Create `tests/fixtures/golden_configs/<plugin>/<scenario>.yaml`.
- Each plugin gets at least three files:
  1. `minimal.yaml` – smallest valid config accepted by the plugin.
  2. `typical.yaml` – realistic operator settings, including non-default enums/flags.
  3. `edge.yaml` – high-entropy or boundary values (long lists, nested overrides, toggled actions) that have historically regressed.
- Write a helper `load_golden_config(name: str) -> dict` (tests/utils/golden.py) that parses YAML, runs the plugin model for validation, and returns a normalized dict.

**Implemented:** 24 golden config files covering all 8 plugins. Helper at `tests/utils/golden.py`.

### 2. Serialization Helper Extraction ✅
- Extract the modal adapter logic into `gatekit/tui/config_adapter.py`:
  - `config_to_form(plugin_class, config_dict)`
  - `form_to_config(plugin_class, form_data)`
- Keep the Textual `PluginConfigModal` thin; it should just call these helpers.
- This unlocks pure unit testing without needing a running Textual app.

**Implemented:** `gatekit/tui/config_adapter.py` with `build_form_state()`, `serialize_form_data()`, `merge_with_passthrough()`.

### 3. Textual Pilot Harness ✅
- Add `tests/utils/textual.py` with a `launch_tui(config_path)` helper using `textual.testing.Pilot`.
- Provide utilities to:
  - Open the plugin modal for a given handler.
  - Simulate keystrokes (tab, enter, type).
  - Capture the resulting YAML on disk and return it for assertions.

**Implemented:** `tests/utils/textual.py` with `launch_tui()`, `navigate_to_plugin_modal()`, `toggle_checkbox_in_modal()`, `save_and_close_modal()`, etc.

### 4. Gateway Integration Harness ✅
- Add `tests/integration/helpers/gateway_harness.py` that:
  - Writes a temporary config file (mixing selected golden configs).
  - Launches `gatekit-gateway` in-process via `Gateway(config)` or as a subprocess using `uv run`. Prefer in-process for speed, but keep a subprocess path for smoke tests.
  - Provides async helpers `send_mcp_request(request_dict)` and `read_plugin_output(path)`.
  - Provides fixtures for fake upstream servers/tools (e.g., echo server, deterministic tool responses).

**Implemented:** `tests/integration/helpers/gateway_harness.py` with `compose_proxy_config()`, `instantiate_plugins()`. Echo server at `scripts/servers/acceptance_echo_server.py`.

### 5. CLI Smoke Test Runner ✅
- Add `scripts/run_acceptance_smoke.py`:
  - Iterates over curated configs (`configs/reference/*.yaml`).
  - Invokes `uv run gatekit-gateway --config <file>`.
  - Asserts process exit status 0 and checks logs for `Gateway started`.
  - Used in the manual checklist to ensure nothing obvious is broken before deeper testing.

**Implemented:** `tests/validation/test_gateway_cli_smoke.py` (pytest-based instead of script). Configs at `configs/acceptance/`.

## Automated Test Plan

### A. Unit: Adapter Fidelity (≈80% of coverage) ✅
- File: `tests/unit/tui/test_config_adapter.py`.
- For every plugin and every golden config:
  1. `round_trip = form_to_config(config_to_form(config))`.
  2. Assert dict equality using DeepDiff (ignore order, compare floats with tolerance).
- Specific cases:
  - Boolean ↔ checkbox mapping.
  - Enum ↔ dropdown mapping.
  - Arrays with add/remove operations (custom patterns, tool lists).
  - Nested objects (PII types, CSV compliance sections).
- Negative tests: feed intentionally malformed form data and assert validation errors bubble up.

**Implemented:** 25 tests in `tests/unit/tui/test_config_adapter.py`.

### B. Unit: Schema Regression Guard ✅
- File: `tests/unit/test_golden_configs.py`.
- Parametrize over all golden files; ensure each passes plugin model validation and produces deterministic `config_to_dict` output.

**Implemented:** 24 tests in `tests/unit/test_golden_configs.py`.

### C. Integration: Textual Round Trips ✅
- File: `tests/integration/test_tui_round_trip.py`.
- Use Pilot to:
  1. Launch TUI with test config seed.
  2. Open plugin modals, verify focus and navigation.
  3. Toggle fields, save, exit.
  4. Read the resulting YAML and compare to expected fixture.
- Keep scope small: choose three representative plugins (deep nesting, array-heavy, simple) and rely on adapter unit tests for full coverage.

**Implemented:** 14 tests covering TUI launch, navigation, plugin modal interaction, and config persistence for all three plugin types.

### D. Integration: Gateway Behavior ✅
- File: `tests/integration/test_gateway_harness.py`.
- Use the gateway harness to run the following suites:
  1. **Security plugins** – feed MCP requests containing emails, phone numbers, or sample AWS keys; assert redact/block/allow according to config.
  2. **ToolManager plugin** – call allowed tool, blocked tool, and verify `tools/list` respects `display_name` overrides.
  3. **Auditing plugins** – send a request, then read JSONL/CSV/line files and assert schema + field presence.
- Each test loads the relevant golden config and asserts both response semantics and side effects (files, logs).

**Implemented:** 13 tests covering PII filter, secrets filter, tool manager, JSON/CSV/human-readable auditing, prompt injection defense, and call trace.

### E. Smoke: CLI Invocation ✅
- File: `tests/validation/test_gateway_cli_smoke.py`.
- Parametrize over curated full configs (baseline, security-heavy, auditing-heavy).
- Run `uv run gatekit-gateway --config <file>` with a short timeout; assert exit 0 and that the log contains `Gatekit is ready` within N seconds.

**Implemented:** 3 tests covering security, tools, and auditing configs.

## Manual Acceptance Checklist

Run only after automated tests pass. Reserve 60–90 minutes.

### 1. Environment Prep
- `uv sync --dev`
- `uv run pytest --no-header -v` (expect green)
- `uv run ruff check gatekit tests`
- `uv run black --check gatekit tests`

### 2. TUI Hands-On
1. `uv run gatekit --config configs/gatekit.yaml`.
2. For each plugin listed in the config:
   - Open the plugin modal, verify fields pre-populate with fixture values.
   - Change one boolean, one enum, and a nested field; save.
   - Quit TUI; inspect the YAML diff (use `git diff` or `uv run gatekit --dump-config`). Confirm only expected fields changed.
3. Re-open TUI to ensure persisted values reload correctly.
4. Run at least one manual layout sweep:
   - Resize terminal to small/large widths.
   - Ensure forms remain usable (no clipped labels, scrollbars visible).

### 3. Gateway Smoke (subprocess)
1. For each curated config in `configs/acceptance/*.yaml`:
   - `uv run gatekit-gateway --config configs/acceptance/<name>.yaml`.
   - Wait for log `Gateway ready`.
   - Use `gatekit-dev --config ...` or `curl localhost:<port>/healthz` (if exposed) to confirm liveness.
   - Stop process (Ctrl+C) and ensure clean shutdown (no tracebacks).

### 4. Gateway Functional Runs (using harness or scripts)
1. Launch gateway with `configs/acceptance/security.yaml`.
   - Use the helper script `scripts/send_mcp_request.py` to send: harmless prompt, PII prompt, AWS key sample.
   - Observe responses: harmless allowed, PII redacted, AWS key blocked (matching config).
2. Launch gateway with `configs/acceptance/tools.yaml`.
   - Issue `tools/list` and `tools/call` via helper script.
   - Confirm only allowlisted tools appear/can run; custom display names appear.
3. Launch gateway with `configs/acceptance/auditing.yaml`.
   - Send two requests; inspect JSONL/CSV logs for correct entries.

### 5. Regression Notes
- Record any unexpected diffs or behavior in `docs/validation/acceptance-log.md` with date, config used, log snippet, and follow-up issue link.
- If manual tests uncover a bug, convert the scenario into an automated regression by adding/adjusting a golden config + test before closing the issue.

## Release Criteria

- All automated suites (unit, integration, smoke) pass in CI.
- Manual checklist completed within the current release cycle with no unresolved blockers.
- Acceptance log updated with results (even if all green) for traceability.
- At least one golden config per new plugin or major feature merged before release.

## Maintenance Notes

- When adding a plugin: supply golden configs, adapter unit tests, and at least one gateway behavior test before shipping.
- When changing schema: rerun adapter tests; if a golden config needs updates, document the reason in its YAML header comment.
- Rotate the curated acceptance configs every release so they always reflect real-world scenarios, not just contrived ones.
