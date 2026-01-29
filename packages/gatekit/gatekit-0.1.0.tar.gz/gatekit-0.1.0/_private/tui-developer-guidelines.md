# TUI Developer Guidelines – Navigation, Focus, and Key Handling

Status: Draft
Audience: Contributors working on `gatekit/tui/*`
Scope: Textual-based screens (especially Config Editor), widget composition, key handling, and debug/validation patterns.

## Goals
- Make TUI changes predictable and testable.
- Prevent regressions from screen-level key bindings that interfere with widget behavior.
- Document small, strict “contracts” for ListView and navigation so contributors and AI agents can work safely.

---

## 1) Single Source of Truth for Screens

- Ensure there is only one runtime `ConfigEditorScreen`.
- Delete or archive obsolete copies (e.g., a monolithic `config_editor.py`) so imports can’t silently pick the wrong file.
- If a legacy file must remain, add a loud comment and raise at import to prevent accidental use.

Rationale: Editing the wrong class leads to “no effect” symptoms and wasted time.

---

## 2) ListView Contract (CRITICAL)

- A ListView must contain only selectable items. Do NOT insert headers, footers, or button rows into the list.
  - Put static headers adjacent (e.g., `Static#servers_title`).
  - Put controls in a sibling container (e.g., `Horizontal#server_buttons_row`).
- Always set an initial index to a real row, then re-assert after render:
  - On populate: if a previous selection exists, set its index; else set `index = 0` if any rows exist.
  - Also call the same setter via `call_after_refresh` to survive layout timing.
- When entering a ListView from another panel, set `index = 0` if index is invalid.

Why: ListView won’t emit Highlighted/Selected unless it has a valid index on a selectable row.

---

## 3) Key Ownership and Boundary Policy

- Let widgets own intra-widget keys:
  - For ListView, Up/Down should call `action_cursor_up()` / `action_cursor_down()` during normal movement.
- Let the screen own only boundary transitions across containers:
  - At list top (index 0), Up moves focus back to the previous container (e.g., last Global Security checkbox).
  - At list bottom, Down moves to the next container.
- If the screen uses priority=True bindings for Up/Down, it must explicitly pass keys through to the focused widget when not at a boundary.
- Enter handling:
  - Prefer a focused-widget or targeted screen `on_key` intercept that:
    - Detects focus on the intended widget (e.g., `#servers_list`).
    - Calls selection logic (e.g., `action_select_cursor()` or `select_current` helper).
    - Calls `prevent_default()` + `stop()` to prevent stray container navigation.
  - Avoid generic, global Enter bindings that may chain into navigation actions.

---

## 4) Navigation Mixin Contract

- Keep a clear container order and document it (e.g., global_security → global_auditing → servers_list → server_details).
- Maintain focus memory per container and row/column memory per panel when relevant.
- Boundary rules must be explicit and side-effect free:
  - Do not call list cursor actions when performing container jumps.
  - When jumping into the list, set a sane index (0) if needed.

---

## 5) Debug Breadcrumbs (Keep These Signals)

Emit consistent, machine-readable events to accelerate diagnosis:
- `list_init_index` / `list_ensure_index` – on initial index set (context: `{list, index, count}`)
- `list_highlight` – on ListView.Highlighted (context: `{list, highlighted}`)
- `selection_change` – on ListView.Selected (context: `{selection_type, old_selection, new_selection}`)
- `list_enter_intercept` – when Enter is locally handled and propagation is stopped
- `focus_change` – already present
- `state_change` – container index changes
- `navigation` – container jumps (direction, from_container, to_container)

Keep these names stable; they are used as acceptance criteria in logs.

---

## 6) Coding Conventions for TUI

- Prefer `isinstance(widget, ListView)` over string class checks.
- Use `call_after_refresh` for any initial focus/index updates that depend on layout.
- When stopping a key at the screen, call both `prevent_default()` and `stop()`.
- Keep widget composition pure:
  - Selection widgets contain selection rows.
  - Headers and button rows live in adjacent containers.

---

## 7) VerticalScroll Usage in Config Modals (CRITICAL)

Textual's `VerticalScroll` has specific requirements for scrolling to work properly. This pattern has been verified across the codebase.

### The Pattern That Works:

1. **VerticalScroll has `height: 1fr`** (or another fixed height) to define the scroll viewport
2. **Direct children MUST have `height: auto`** (or explicit fixed heights) - this is the critical requirement
3. **Do NOT wrap children in an extra container** - yield widgets directly into VerticalScroll

### Example (Plugin Config Modal):

```python
# In compose():
with VerticalScroll(classes="form-content"):
    yield from self.form_adapter.generate_form()  # Yields directly, no wrapper

# In CSS:
.form-content {
    height: 1fr;  # Defines the scroll viewport
}

# CRITICAL: All direct children need height: auto
Input {
    height: auto;  # Required for scrolling
}

Select {
    height: auto;  # Required for scrolling
}

.field-label {
    height: auto;  # Required for scrolling
}

.nested-object-container {
    height: auto;  # Required for scrolling
}
```

### What DOESN'T Work:

❌ **Wrapping in an extra Vertical container** (even with `height: auto` on the wrapper):
```python
# This will NOT enable scrolling:
with VerticalScroll(classes="form-content"):
    with Vertical(classes="wrapper"):  # Extra wrapper breaks scrolling
        yield from self.form_adapter.generate_form()
```

❌ **Direct children without explicit heights**:
```python
# CSS without height: auto on children won't scroll:
Input {
    background: $surface;
    # Missing: height: auto;
}
```

### Verified Working Examples:

- **`config_editor/base.py`**: Server details pane with Container children that have `height: auto`
- **`array_editor.py`**: Enum array with checkboxes yielded directly into VerticalScroll
- **`plugin_config/modal.py`**: Form fields with all widgets having `height: auto`

### Custom Widget Requirements:

If creating custom Container-based widgets used inside VerticalScroll, add `height: auto` to the widget's DEFAULT_CSS:

```python
class ToolSelectionField(Container):
    DEFAULT_CSS = """
    ToolSelectionField {
        height: auto;  # Required when used in VerticalScroll
        layout: vertical;
        # ... other styles
    }
    """
```

### Debugging Scrolling Issues:

1. Check that VerticalScroll has an explicit height (`1fr`, `90%`, etc.)
2. Verify ALL direct children have `height: auto` in CSS
3. Remove any wrapper containers between VerticalScroll and content
4. Use `textual console` to inspect the layout tree and verify heights are computed correctly

---

## 8) Minimal Integration Tests (High Leverage)

Add a small test module using Textual’s pilot (or equivalent) to simulate keys:
- Test A: Enter servers list, ensure `list_init_index` and highlight appear; Down moves within list; Up at index 0 returns to Global Security.
- Test B: Press Enter in servers list; ensure details update and no navigation event follows.
- Test C: Boundary transitions between all containers work (tab/shift+tab or arrow-based rules).

These 2–4 tests will catch most regressions from key binding changes.

---

## 9) PR Checklist for TUI Changes

- [ ] If editing screens, confirm only one implementation exists/is used at runtime.
- [ ] If touching a ListView, verify: only selectable rows, initial index set + re-asserted after render.
- [ ] If changing key bindings, document widget vs. screen ownership for the key.
- [ ] If adding Enter handling, ensure propagation is stopped at the correct layer.
- [ ] If using VerticalScroll, verify all direct children have `height: auto` in CSS.
- [ ] Run TUI tests (if present) or capture a short debug log excerpt showing breadcrumbs above.

---

## 10) Future Enhancements (Optional)

- A tiny in-repo “TUI playground” screen that renders the critical widgets and prints live breadcrumbs for manual dev.
- A debug overlay toggle to show: focused widget id/type, current container index, list index.

---

## 11) Tool Manager Configure Modal (Allowlist-Only)

- The Configure modal now hydrates tool rows from the live MCP server and defaults every tool to **Enabled**.
- Unchecking a row removes that tool from the allowlist; unchecked tools no longer appear in the client, they are not “blocklisted”.
- Renaming/descriptions only apply to checked rows. Leave unchecked rows blank—naming hidden tools has no effect.
- Schema/UI no longer expose a mode toggle. If you encounter a legacy config with `mode`/`action`, surface the validation error and ask the user to update the YAML.

Rationale: This keeps runtime behavior and UI copy aligned with the implicit allowlist contract introduced in v0.1.0.

---

## Appendix: Textual Devtools & Logging Workflow (5.3+)

Follow this when you need Textual’s live devtools or layout trace:

1. Install the standalone CLI once (outside the project venv): `uv tool install textual-dev`.
2. Add a helper function to your shell rc so the TUI runs with the right flags:
   ```bash
   gatekit-dev() {
     local devtools_site
     devtools_site="$(ls -d "$HOME/.local/share/uv/tools/textual-dev"/lib/python*/site-packages 2>/dev/null | head -n1)"
     if [ -z "$devtools_site" ]; then
       printf 'textual-dev tool not found – run `uv tool install textual-dev`\n' >&2
       return 1
     fi
     TEXTUAL_DEVTOOLS_PORT="${TEXTUAL_DEVTOOLS_PORT:-8081}"
     TEXTUAL_LOG="${TEXTUAL_LOG:-/tmp/textual-debug.log}"
     PYTHONPATH="${devtools_site}${PYTHONPATH:+:$PYTHONPATH}" \
       TEXTUAL="devtools,debug" \
       uv run gatekit --debug "$@"
   }
   ```
3. Start the devtools console in one terminal: `textual console --port 8081`.
   - Use `script -q /tmp/textual-devtools.log textual console --port 8081` when you need a sharable log file (the console UI still appears, but all output is captured).
4. Launch the TUI in another terminal: `gatekit-dev <path-to-your-config>` (omit the path for the picker).
   - Layout traces stream to `/tmp/textual-debug.log`; tail with `tail -f /tmp/textual-debug.log`.

Share both `/tmp/textual-debug.log` and `/tmp/textual-devtools.log` (if captured) when requesting assistance so maintainers/agents can diagnose rendering issues without the live console.

---

## References
- Code paths: `gatekit/tui/screens/config_editor/*`, `gatekit/tui/debug/*`
- Recent issues fixed: ListView selection initialization, Up/Down boundary handling, Enter intercept to prevent container jumps.
