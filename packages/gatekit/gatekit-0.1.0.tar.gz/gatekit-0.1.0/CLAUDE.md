# Gatekit Project Memory

## Project Overview
Gatekit is a hackable MCP gateway. Built-in plugins handle tool filtering, audit logging, and content security. Extend with Python plugins when needed.

**Core Architecture**: Plugin-based • Async-first • YAML configuration • Pydantic validation • Pipeline processing

**⚠️ IMPORTANT: This is a first release (v0.1.0) - NO BACKWARD COMPATIBILITY REQUIRED**
- Tests can be updated to match new behavior if needed
- Configuration formats can change
- API interfaces can be modified 
- Focus on clean, maintainable code over legacy compatibility

### Required Test Workflow
Before completing any coding task, run BOTH of these commands:
1. `pytest tests/ -n auto` - All tests MUST pass (parallel execution strongly preferred for speed)
2. `uv run ruff check gatekit` - Fix any linting issues
Note that it is not necessary to run these commands if you only changed documentation.

**Parallel testing is strongly preferred** - only run serially (`pytest tests/`) if debugging test failures or investigating race conditions.

**Slow/smoke tests are skipped by default** to keep the development loop fast. Only run them with `--run-slow` when:
- Making potentially breaking changes to CLI startup or config loading
- Before releases or major merges
- Specifically debugging startup issues

If ANY tests fail or linting issues appear, fix them immediately. Ask for help rather than ignoring failures.

## Core Development Principles

### Security-First Mindset
Every decision must consider security implications:

- **Secure by default** - Choose the more secure option when alternatives exist
- **Explicit over implicit** - Make behaviors clear and observable, avoid "magic"
- **Signal professionalism** - Demonstrate thoughtfulness to security-conscious users
- **Document exceptions** - When deviating from strict patterns, document why

**Key Guidelines:**
1. Ask before loosening constraints or adding implicit behavior
2. Document the "why" behind any "magic" or implicit behavior
3. Consider how choices appear to security-conscious users
4. Test security implications of any convenience features

### Don't Guess - Ask or Research
- **Don't make assumptions** about APIs or implementation details
- **Consult documentation** first when you need information
- **Use available tools** to search and gather context
- **Ask directly** if genuinely unsure
- **Be transparent** about confidence levels
- **Read error messages carefully** before drawing conclusions

### Guided Setup: Client Configuration vs Server Migration
**Client configuration is independent of server selection.** Gatekit is a shared gateway - multiple clients connect to one instance managing a pool of servers. If user selected a client in "MCP clients to configure", generate instructions to add Gatekit to that client, regardless of which servers (if any) from that client were selected for migration. Don't conflate server selection with client configuration.

### TUI Development Guidelines

#### Event Handling
- **`on_key()` should rarely be used** - It's almost always the wrong approach for event handling
- If you find yourself trying to use `on_key()` to work around an issue, **STOP and ask for help**
- Prefer Textual's proper event handlers (`@on(Widget.Event)`) instead
- The framework provides the right events - if they're not firing, investigate why rather than working around them with `on_key()`

#### Debug Logging
**NEVER use `self.app.log`, `print()`, or stderr for TUI debugging**. Always use `get_debug_logger()`:

```python
from ..debug import get_debug_logger

logger = get_debug_logger()
if logger:
    logger.log_event("event_name", screen=self, context={"key": "value"})
```

Available methods: `log_event()`, `log_widget_lifecycle()`, `log_user_input()`, `log_focus_change()`, `log_state_change()`, `log_value_change()`. Writes JSON to `~/Library/Logs/gatekit/gatekit_tui_debug.log`. See `gatekit/tui/screens/config_editor/` for examples.

### Plugin Equality Principle
All plugins are first-class citizens in Gatekit - plugins that ship with Gatekit receive NO special treatment:

- **No hardcoded plugin names** - Core code must never contain hardcoded references to specific plugin names
- **Dynamic discovery only** - Use the plugin discovery system to find and interact with plugins
- **Metadata-driven behavior** - Plugins declare their own capabilities via class attributes (`DISPLAY_SCOPE`, `DISPLAY_NAME`, etc.)
- **Equal validation** - Built-in and user plugins must pass through identical validation logic
- **Same interfaces** - Built-in plugins use the same interfaces and base classes as user plugins

**Key Guidelines:**
1. **Never hardcode plugin names** in validation, configuration, or business logic
2. **Use plugin metadata** - Read `DISPLAY_SCOPE`, `DISPLAY_NAME` etc. via `getattr()` 
3. **Enable user plugins** - Any capability available to built-in plugins must be available to user plugins
4. **Test equally** - Write tests that verify user plugins get the same treatment as built-in plugins

**Violation Examples to Avoid:**
```python
# ❌ WRONG: Hardcoded plugin names
if plugin.handler == "tool_manager":
    # special handling

SERVER_AWARE_PLUGINS = {'tool_manager', 'filesystem_server'}  # ❌ WRONG

# ✅ CORRECT: Dynamic discovery
plugin_class = discover_plugin_class(plugin.handler)
display_scope = getattr(plugin_class, 'DISPLAY_SCOPE', 'global')
if display_scope == 'server_aware':
    # handle server-aware plugins generically
```

### Communication Standards
- **Honest feedback** - Communicate concerns clearly and directly
- **Evidence-based reasoning** - Back perspectives with examples
- **Suggest alternatives** that align with best practices
- **Timeless documentation** - Avoid dates/deadlines, use version numbers

**⚠️ CRITICAL: Always Provide Truthful Assessment**
- **Tell the truth, even when uncomfortable** - I value honest assessment over diplomatic responses
- **Don't worry about hurt feelings** - Direct feedback is more valuable than sugar-coating
- **Challenge assumptions and decisions** - Point out potential problems or better approaches
- **Be blunt about risks and downsides** - I need to understand real trade-offs and potential failures
- **Don't assume what I want to hear** - Focus on what I need to know, not what might be pleasant to hear

### Sycophancy Prevention Protocol

**When the user asks strategy, analysis, or evaluation questions, CHECK for these bias-inducing patterns and FLAG them before answering:**

| If you detect... | Say this before answering |
|------------------|---------------------------|
| Presupposition ("which of these...", "what are our strengths...") | "This question presupposes [X]. Do you want me to first evaluate whether [X] is true?" |
| Persona framing ("put on your MBA hat", "as an expert...") | "Persona framing can trigger pattern-matching over reasoning. I'll answer directly and cite evidence instead." |
| Anchoring ("I think X, what do you think?") | "You've stated a position. I'm at risk of anchoring on it. Want me to steelman the opposite view first?" |
| Generative bias ("brainstorm ways to...", "how can we...") | "This framing biases toward finding options. Should I also evaluate whether this is worth doing at all?" |

**For any business strategy, competitive analysis, or market research question:**
1. State upfront: "LLMs are not empirically validated for this task type. Treat this as hypothesis generation, not reliable analysis."
2. Cite sources for factual claims or flag when you're speculating
3. After answering, ask: "Do you want me to argue the opposite position?"

**Reliability reference (for context on why this matters):**
- LLMs are reliable for: code generation, information retrieval, summarization, tasks with objective correctness criteria
- LLMs are unreliable for: strategy, truthfulness without verification, self-assessment of correctness
- Research: Sycophancy ([Sharma 2023](https://arxiv.org/abs/2310.13548)), Truthfulness 58% vs 94% human ([TruthfulQA](https://arxiv.org/abs/2109.07958)), Overconfidence in 84% of scenarios ([FermiEval](https://arxiv.org/html/2510.26995))

## Development Workflows

### Two-Repository Workflow

Gatekit uses two repositories:
- **Private repo**: Day-to-day development with full commit history
- **Public repo**: Clean release snapshots only (no development history)

**Private content** lives in `_private/` (gitignored):
- `_private/todos/` - Active development tasks
- `_private/todos-completed/` - Historical implementation records
- `_private/archive/` - Old planning documents

**To release:**
1. Ensure all tests pass and code is ready
2. Tag in private repo: `git tag v0.x.x`
3. Run sync script: `./scripts/sync-to-public.sh v0.x.x`
4. Review changes in public repo
5. Push: `cd ../gatekit-public && git push origin main && git push origin v0.x.x`

The sync script copies the current state (excluding `_private/`) to the public repo as a single commit. No git history is transferred between repos.

### Release Checklist

Before each release, ensure:

1. **Tests pass**: `pytest tests/ -n auto --run-slow`
2. **Linting passes**: `uv run ruff check gatekit`
3. **Documentation updated**:
   - [ ] Update plugin reference docs (`docs/reference/plugins/*.md`) if plugin behavior/config changed
   - [ ] Update configuration spec if schema changed
   - [ ] Update known issues if applicable
4. **Website built**: `python scripts/build-website.py`
5. **Version bumped** in appropriate files

### Development Process
1. Follow existing patterns and conventions
2. **Run `pytest tests/` - ALL TESTS MUST PASS**
3. **Run `uv run ruff check gatekit` - FIX ALL LINTING ISSUES**
4. Document decisions and update feature documentation

### Configuration Development
1. **Schema first** - Update Pydantic models before YAML changes
2. **Validate early** - Test configuration loading first
3. **Document examples** - Every new option needs examples
4. **Test edge cases** - Invalid configs, missing sections, type mismatches

### Testing Patterns
- **Security plugins**: Test allow/deny scenarios, edge cases
- **Middleware plugins**: Test transformations, completions, side effects
- **Auditing plugins**: Verify log format, data completeness, performance
- **Integration tests**: Test plugin interactions with real MCP flows
- **Configuration tests**: Validate schemas and error handling
- **Real MCP server tests**: Use `npx` to run actual MCP servers (no global installs needed)
- **Test artifacts**: ALL test files and outputs must use temporary directories (`tempfile.TemporaryDirectory()` or `tempfile.NamedTemporaryFile()`) - never hardcode filenames that create artifacts in the project root (e.g., avoid `"test.log"`, `"test.csv"`, etc.)
- **Validation tests**: Tests that use external dev packages (e.g., `pycef`, `pandas`, `jc`) belong in `tests/validation/` - these provide additional format compliance verification with third-party tools
- **Test naming**: Test names must be descriptive of what they test (e.g., `test_json_rpc_error_classification`, `test_jsonl_format_enforcement`). NEVER use temporal names like `test_bug_fixes`, `test_enhancements`, `test_new_features` that will age poorly. Test names should describe the behavior being tested, not when/why it was added
- **Platform-specific tests**: Use `@pytest.mark.windows_only` or `@pytest.mark.posix_only` markers instead of `@pytest.mark.skipif`. These markers filter tests at collection time so they don't appear as "skipped" on other platforms - this keeps test output clean and prevents skip-blindness

### Code Style & Standards
- Python 3.10+ with type hints, follow existing patterns, async functions
- Clear error messages for user-facing errors
- Clean up temporary files after use
- Use existing documentation files when available

### Website

The website lives in `website/` and is built from markdown docs.

**Workflow:**
1. Edit markdown in `docs/` (or hand-edit `website/index.html` for landing page)
2. Run `python scripts/build-website.py`
3. Commit both source and generated files

**Structure:**
- `website/index.html` - Landing page (hand-crafted, not generated)
- `website/css/style.css` - Shared stylesheet
- `website/_templates/docs.html` - Template for generated docs
- `website/docs/` - Generated from `docs/*.md`
- `website/decisions/` - Generated from `docs/decision-records/*.md`

**Build script** (`scripts/build-website.py`) requires: `pip install mistune pygments`

**Note:** `scripts/` is excluded from public repo sync, so generated files must be committed.

## Quick Reference

### Essential Commands

**IMPORTANT:** Always run tests from within the virtual environment to ensure `python` resolves correctly:
```bash
source .venv/bin/activate  # or: .venv/bin/pytest directly
```

```bash
# CRITICAL: Run BOTH before completing any coding task
pytest tests/ -n auto                  # All tests must pass (parallel execution preferred)
uv run ruff check gatekit            # All linting must pass

# Development commands
pytest tests/unit/test_[module].py -v    # Run specific test file (use -n auto for parallel)
pytest tests/ -n auto --cov=gatekit    # Check coverage with parallel execution
pytest tests/                            # Run serially (only if parallel causes issues)
pytest tests/ -n auto --run-slow         # Include slow/smoke tests (before releases)
uv run ruff check gatekit --fix       # Auto-fix linting issues where possible
gatekit                              # Launch TUI configuration interface
gatekit --debug                       # Launch TUI with debug logging enabled
gatekit-gateway --config gatekit.yaml  # Run as MCP gateway proxy
```

### TUI Debug Logging
`gatekit --debug` writes structured JSON logs to:
- **macOS:** `~/Library/Logs/gatekit/gatekit_tui_debug.log`
- **Linux:** `~/.local/state/gatekit/gatekit_tui_debug.log`
- **Windows:** `%LOCALAPPDATA%\gatekit\logs\gatekit_tui_debug.log`

State snapshots (Ctrl+Shift+D): `gatekit_tui_state_*.json` in same directory. Use `get_debug_logger()` for TUI debugging - see guidelines above.

### Common Issues & Solutions
| Issue | Solution |
|-------|----------|
| "No tests found" | Check file paths and pytest discovery rules |
| Import errors | Verify package structure and `__init__.py` files |
| YAML syntax errors | Validate YAML syntax before testing |
| Plugin loading errors | Check plugin handlers declarations and class names |
| Connection failures | Verify upstream server command and arguments |

### Gatekit Usage Reminder
Gatekit is an MCP server gateway - it sits between MCP clients and upstream servers.
Run it via `gatekit-gateway --config <your-config.yaml>` and configure your MCP client to connect to it.

### Configuration Reference
Always refer to:
- **[`docs/configuration-specification.md`](docs/configuration-specification.md)** – Canonical spec (includes complete example)
- **[`gatekit/config/models.py`](gatekit/config/models.py)** – Source of truth (Pydantic schemas)

**Critical:** The configuration spec documents what fields are actually supported. Common mistakes:
- ❌ `env` field in upstream configs (not supported - set env vars in MCP client or shell)
- ❌ Missing `proxy:` wrapper (all config must be under `proxy:`)
- ❌ Server-aware plugins in `_global` section (requires per-server config)

**Path Resolution:** Relative paths in config files (e.g., `output_file: logs/gatekit_audit.jsonl`) are resolved **relative to the config file's directory**, not the working directory. If your config is at `configs/gatekit.yaml`, then `logs/gatekit_audit.jsonl` resolves to `configs/logs/gatekit_audit.jsonl`.

## Gatekit Domain Knowledge

### Architecture Overview
- **Security Model**: MCP Client ↔ Gatekit (security boundary) ↔ Upstream MCP Server
- **Plugin Types**: 
  - **Middleware plugins** (transform/complete requests, tool management)
  - **Security plugins** (block/allow/modify with security decisions)
  - **Auditing plugins** (observe/log without affecting flow)
- **Message Flow**: JSON-RPC 2.0 requests/responses/notifications intercepted and processed through pipeline
- **Configuration**: Config-relative paths, home directory expansion (`~`), cross-platform
- **Processing Pipeline**: All messages flow through ordered plugin pipeline with full observability

### Key Concepts
- **System Logging**: Gatekit internal logs (startup, errors, debug)
- **Auditing**: Plugin-based logs of MCP communication and processing pipeline
- **Plugin Discovery**: Handler-based system using `HANDLERS` declarations in plugin modules
- **Error Handling**: JSON-RPC error codes with Gatekit extensions (see ADR-004)
- **Concurrent Processing**: High-performance parallel request handling with proper correlation
- **Request Limiting**: Configurable limits for concurrent requests (default: 100)
- **Plugin Priority**: Plugins execute in priority order (0-100, lower = higher priority)
- **Critical Plugins**: All plugins default to `critical: true` (fail-closed). Set `critical: false` to allow fail-open behavior

### Plugin System Architecture

#### Unified Result Type
All plugins return `PluginResult` with optional fields:
- `allowed: Optional[bool]` - Security decision (None if no decision made)
- `modified_content: Optional[Union[MCPRequest, MCPResponse, MCPNotification]]` - Modified message
- `completed_response: Optional[MCPResponse]` - Complete response that ends pipeline
- `reason: str` - Human-readable explanation
- `metadata: Dict[str, Any]` - Additional processing information

#### Processing Pipeline
Messages flow through plugins creating a `ProcessingPipeline` with:
- **PipelineStage**: Record of each plugin's processing
- **StageOutcome**: `ALLOWED`, `BLOCKED`, `MODIFIED`, `COMPLETED_BY_MIDDLEWARE`, `ERROR`
- **PipelineOutcome**: Final pipeline result with full observability
- Complete audit trail of all transformations and decisions

### Plugin Development Quick Guide
```python
# Middleware Plugin Template
class MyMiddlewarePlugin(MiddlewarePlugin):
    DISPLAY_NAME = "My Middleware"
    
    async def process_request(self, request: MCPRequest, server_name: str) -> PluginResult:
        # Transform, complete, or pass through
        return PluginResult(modified_content=modified_request, reason="...")
    
    async def process_response(self, request, response, server_name) -> PluginResult:
        return PluginResult()  # Pass through unchanged
    
    async def process_notification(self, notification, server_name) -> PluginResult:
        return PluginResult()

# Security Plugin Template
class MySecurityPlugin(SecurityPlugin):
    DISPLAY_NAME = "My Security Plugin"
    DISPLAY_SCOPE = "global"  # or "server_aware" or "server_specific"
    
    async def process_request(self, request: MCPRequest, server_name: str) -> PluginResult:
        # MUST set allowed=True or allowed=False
        return PluginResult(allowed=True, reason="...")
    
    async def process_response(self, request, response, server_name) -> PluginResult:
        return PluginResult(allowed=True, reason="...")
    
    async def process_notification(self, notification, server_name) -> PluginResult:
        return PluginResult(allowed=True, reason="...")

# Auditing Plugin Template  
class MyAuditingPlugin(AuditingPlugin):
    DISPLAY_NAME = "My Auditing Plugin"
    
    async def log_request(self, request: MCPRequest, pipeline: ProcessingPipeline, server_name: str) -> None:
        # Log with full pipeline visibility
        pass
    
    async def log_response(self, request, response, pipeline, server_name) -> None:
        pass
    
    async def log_notification(self, notification, pipeline, server_name) -> None:
        pass

# Handler Registration (in plugin module)
HANDLERS = {
    "my_middleware": MyMiddlewarePlugin,
    "my_security": MySecurityPlugin,
    "my_auditing": MyAuditingPlugin
}
```

**Guidelines**: 
- Inherit from appropriate base class
- Security plugins MUST set `allowed` field
- Handle errors gracefully
- Stateless design
- Pydantic config models for validation

## Project Documentation Structure

### Configuration Documentation
- **[Configuration Specification](docs/configuration-specification.md)**: Canonical reference with complete example (START HERE for any config work)
- **[Config Models](gatekit/config/models.py)**: Pydantic schemas - source of truth for validation

### Decision Records (ADRs)
Key architectural decisions documented in `docs/decision-records/`:
- **001-013**: Transport layer, async architecture, TDD, error handling, configuration, plugin systems, response filtering, concurrent request handling
- **014-019**: Multi-server support, capability discovery, hot-swap config, TUI architecture
- **020**: Middleware plugins architecture
- **021**: Handler nomenclature (policy → handler terminology shift)
- **022**: Unified PluginResult type
- **023**: Pipeline reason concatenation

### Work Documentation (Private)
- **Active Todos** (`_private/todos/`): Current development priorities and research - **PRIMARY SOURCE for current work**
- **Completed Work** (`_private/todos-completed/`): Historical implementation records
- **Archive** (`_private/archive/`): Historical planning documents

Note: The `_private/` folder is gitignored and never synced to the public repo.

### Platform Notes
- **macOS Development**: No `timeout` command - use background processes with `sleep` and `kill`
- **Todo-based development**: Replaced version-based planning

## Project Philosophy
**High code quality and test coverage • Clear error messages • Extensible without breaking functionality • Security-first design • Full observability**
