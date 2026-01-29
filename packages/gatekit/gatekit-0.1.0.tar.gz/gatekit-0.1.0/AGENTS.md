# Repository Guidelines

## Agent Conduct
- Do not run `git checkout`, `git restore`, or similar destructive commands without explicit permission from the user. Uncommitted work must be preserved.

## Project Structure & Module Organization
- `gatekit/` hosts the runtime modules: core policies, proxy pipeline, plugins, transport, CLI/TUI.
- Tests mirror the runtime (`tests/unit`, `tests/integration`, `tests/validation`, `tests/utils`); design notes live in `docs/` and `future-work/`.
- Configuration examples live in `docs/configuration-specification.md`; generate your own configs via guided setup (we do not ship a default file).
- `docs/archive/` content is historical only and may diverge from the current implementation.

## Build, Test, and Development Commands
- `uv sync --dev` (or `pip install -e .`) installs the dev toolchain.
- `uv run gatekit <path>` launches the TUI; `uv run gatekit-gateway --config <path>` starts the proxy with your config.
- Gate merges with `uv run pytest --no-header -v`, `uv run ruff check gatekit tests`, and `uv run black --check gatekit tests`.

## Coding Style & Naming Conventions
- Python 3.10+, four-space indent, explicit type hints, async-first transports and plugins.
- Format with Black (line length 100) and Ruff; shared helpers belong in `gatekit/utils/`.
- Match module/test names to behavior (`proxy_manager.py`, `test_proxy_manager.py`); keep UI copy under `gatekit/cli/` or `gatekit/tui/`.

## Testing Guidelines
- Run the full suite before handoff and fix failures immediately.
- Use `tests/unit` for focused logic, `tests/integration` for pipeline flows, and `tests/validation` for schema checks.
- Apply `pytest.mark.asyncio` for coroutines and `pytest.mark.real_server` only when an upstream MCP server is required.
- Name tests `test_*`, keep fixtures in `tests/conftest.py` or `tests/utils/`, rely on `tempfile` helpers, and keep ≥90% coverage on touched code.

## Commit & Pull Request Guidelines
- Follow Conventional Commits and add scopes when they clarify impact.
- Link issues, describe behavioral changes, and list validation commands (tests, linters, manual TUI checks).
- Rebase before review, squash WIP noise, and update docs/config samples alongside code.

## Release Expectations
- v0.1.0 is the first release—treat every change as greenfield: backward compatibility is not required.
- Break schemas or APIs whenever clarity or security improves, as long as docs and tests ship in the same PR.
- Prefer small, decisive migrations and update verification artifacts in the same PR.

## Plugin Equality & Discovery
- Rely on handler discovery; never special-case built-in plugin names.
- Drive behavior with plugin metadata (`DISPLAY_SCOPE`, `DISPLAY_NAME`, `describe_status`).
- Cover bundled and custom plugins in tests to prove equal treatment.

## Security Principles
- Default to the safer configuration and record the rationale for any exception.
- Keep security decisions explicit—no hidden toggles or magic behaviors.
- Validate new configs with `uv run gatekit-gateway --config <path>` before review.

## Security & Configuration Tips
- Redact credentials from samples and logs; keep real secrets in local overrides.
- Register new plugins under `gatekit/plugins/` and extend your local config (see `docs/configuration-specification.md`).

## TUI Devtools Workflow (dbright local)
- Keep the helper `gatekit-dev` in your shell rc. Daily flow: `textual console --port 8081` (or run `script -q /tmp/textual-devtools.log textual console --port 8081` to capture output) then `gatekit-dev <your-config>`. Detailed instructions live in `docs/tui-developer-guidelines.md`.
- The `textual console` we ship is a log-only view (no widget inspector, watchers, or interactive panels). When you need layout data, capture the console output and search for the relevant events (e.g., `ScrollBar(... window_size=0 ...)`).

## Textual CSS Notes
- Textual does not support the standard `gap`/`column-gap` properties in layouts; use margin or padding on child widgets instead when you need spacing.
