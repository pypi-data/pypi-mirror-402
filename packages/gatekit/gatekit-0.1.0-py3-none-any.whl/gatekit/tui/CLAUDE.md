# TUI Development Context

Guidelines specific to Gatekit TUI development. These supplement the root CLAUDE.md.

## Development Philosophy

- **Iterative & Intuitive** - Build, test, refine based on feel rather than detailed specs
- **User Experience Focus** - If it feels clunky in the TUI, it needs improvement
- **No Backward Compatibility** - Pre-v0.1.0 release, can change anything
- **Pre-launch Development** - Can delete/modify tests that don't match current direction

## Key Documentation

When working on TUI features, consult these resources:

- **[tui-developer-guidelines.md](../../docs/tui-developer-guidelines.md)** - ListView contracts, key handling, VerticalScroll patterns, debug breadcrumbs (CRITICAL for any widget/navigation work)
- **[tui-progress-tracker.md](../../docs/todos/visual-configuration-interface/tui-progress-tracker.md)** - Current status and roadmap
- **[tui-data-layer-integration.md](../../docs/todos/visual-configuration-interface/tui-data-layer-integration.md)** - Backend integration patterns
- **[server-compatibility-design.md](../../docs/todos/visual-configuration-interface/server-compatibility-design.md)** - Server/plugin compatibility UX
- **[select-widget-height-issue.md](../../docs/todos/visual-configuration-interface/select-widget-height-issue.md)** - Known CSS issue with Select widget

## Critical Guidelines

### Don't Run the TUI
Claude cannot interact with the TUI interface. Avoid running it unless debugging startup issues or capturing specific error output.

### TUI-Only Testing
Unless changes could affect gatekit core (non-TUI), only run TUI tests:
```bash
pytest tests/unit/tui/ -n auto
pytest tests/integration/tui/ -n auto
```

### Event Handling (from root CLAUDE.md)
- **`on_key()` should rarely be used** - Almost always the wrong approach
- If tempted to use `on_key()` to work around an issue, **STOP and ask for help**
- Prefer Textual's proper event handlers (`@on(Widget.Event)`)

### Debug Logging
**NEVER use `self.app.log`, `print()`, or stderr for TUI debugging.** Always use `get_debug_logger()`:

```python
from ..debug import get_debug_logger

logger = get_debug_logger()
if logger:
    logger.log_event("event_name", screen=self, context={"key": "value"})
```

Debug logs location (when TUI is run with `--debug`):
- **macOS:** `~/Library/Logs/gatekit/gatekit_tui_debug.log`
- **Linux:** `~/.local/state/gatekit/gatekit_tui_debug.log`
- **Windows:** `%LOCALAPPDATA%\gatekit\logs\gatekit_tui_debug.log`

State snapshots (Ctrl+Shift+D): `gatekit_tui_state_*.json` in same directory.

### Textual Documentation
Use Context7 to lookup latest Textual framework docs:
```
context7 get-library-docs /textualize/textual
```

## Documentation Update Policy

After completing significant TUI work, **ASK** whether to update documentation:
- Only update for meaningful progress or approach changes
- Avoid updating for experimental iterations that don't pan out
- Primary focus on keeping `tui-progress-tracker.md` current
