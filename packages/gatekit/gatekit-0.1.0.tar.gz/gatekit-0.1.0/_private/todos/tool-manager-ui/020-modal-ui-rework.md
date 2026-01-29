# Modal UI Rework

## Tasks
- [ ] Introduce `ToolSelectionField` widget rendering a scrollable list of discovered tools.
- [ ] For each row display: checkbox (default checked), tool id (readonly), discovered name/description, editable `display_name`, editable `display_description`.
- [ ] Inject the custom widget from `PluginConfigModal.compose` by detecting the tool-array schema (required `tool` string with optional display overrides) rather than schema extensions, so any plugin sharing the shape benefits automatically.
- [ ] Preserve manual entries by appending unchecked rows sourced from the existing config but missing from discovery.
- [ ] Hide the “Add another tool” affordance for now; manual additions only appear for legacy config entries.
- [ ] Render a warning banner inside the widget whenever discovery data is unavailable or stale, and continue to show manual rows in that case.

## UX Considerations
- Reuse existing CSS classes where possible; add new styles under `PluginConfigModal.CSS` if necessary.
- Ensure keyboard navigation cooperates with `_navigate_to_next_widget` / `_navigate_to_previous_widget` helpers.
- Reserve a compact header row in the widget for status text (e.g., last refreshed timestamp) and a future refresh button, even if the button ships disabled initially.
- Display an inline banner when discovery metadata is missing, guiding the user to server diagnostics.

## Assets & Layout
```
┌ tool row ─────────────────────────────────────────────┐
│ [✔] tool_id (Discovered Name)
│     Discovered: lorem ipsum description from server
│     Display name:      [ Input                 ]
│     Display description[ TextArea-style Input    ]
└───────────────────────────────────────────────────────┘
```
