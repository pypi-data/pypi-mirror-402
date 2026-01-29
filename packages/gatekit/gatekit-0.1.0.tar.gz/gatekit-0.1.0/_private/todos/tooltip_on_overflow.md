# Tooltip on overflow for text widgets

Problem
- Long strings in labels and table cells are truncated (clip/ellipsis). We want a tooltip that shows the full string, but only when the visible text actually overflows its container.

Why
- Improves discoverability without cluttering the UI.
- Keeps headers/rows compact but still allows reading full values when needed.

Scope
- Apply to places where we render text that may be truncated, starting with:
  - Custom PluginTable cell widgets (name, scope, priority)
  - Other Label/Static text in the config editor that can be ellipsized
- Nice-to-have: DataTable-based cells (trickier since cells aren’t standalone widgets)

Requirements (acceptance criteria)
- Tooltip is set to the full string only when content width exceeds available width; otherwise tooltip is cleared/absent.
- Works when:
  - The panel is resized (terminal or layout change)
  - The content updates dynamically
  - The user hovers over the text (optional lazy computation)
- No flicker: Tooltip should not rapidly toggle when hovering.
- Handles wide/ambiguous-width characters and markup safely.

Design notes
- Textual tooltips are supported per-widget via `Widget.set_tooltip(...)`, `widget.tooltip`, or `with_tooltip(...)`.
- There isn’t a built-in “auto-ellipsis tooltip” feature; we need to detect overflow ourselves.
- Overflow detection strategy:
  - For Label/Static, the rendered content is a `Content` visual (textual.content.Content)
    - Available width: `widget.content_region.width`
    - Needed width:
      - For single-line/nowrap: `content.cell_length` is often sufficient
      - Generic: `content.get_optimal_width(widget.styles, available)` (better with markup/wide glyphs)
  - If `needed > available`, set tooltip to `content.plain`; else clear it.
- Styling:
  - Use `text-wrap: nowrap;` and `text-overflow: ellipsis;` for single-line truncation, where appropriate.
  - Multi-line content: either disable wrapping (preferred for tables) or consider tooltips when any line would overflow.

Proposed implementation
- Create `OverflowTooltipLabel` (subclass Label) or a small mixin that:
  - Hooks into `on_mount` and `on_resize` to re-evaluate overflow
  - Overrides `update()` to re-evaluate when content changes
  - Optionally re-evaluates on `on_mouse_enter` for lazy calculation
  - Logic:
    1. Obtain `visual = self.visual` (from Static/Label)
    2. If not a Content instance, wrap with `Content.from_text(...)`
    3. Compute `available = self.content_region.width`
    4. Compute `needed = content.get_optimal_width(self.styles, available)`
    5. Set `self.set_tooltip(content.plain if needed > available else None)`
- Apply to our custom PluginTable widgets by replacing current `Label` instances with `OverflowTooltipLabel` where values can be truncated (e.g., plugin display name).
- Optional phase: Add a helper that can traverse a container and attach hover-time evaluation to generic `Static`/`Label` descendants.
- DataTable note: Since cells aren’t widgets, per-cell tooltip is harder; defer or provide a separate approach if needed.

Edge cases
- Empty strings → never show tooltip
- Very narrow columns (1–2 cells): still show tooltip when overflowing
- Wide/emoji/combining characters → rely on `Content` width helpers rather than `len()`
- Markup strings → use Content.plain for tooltip text

Testing (TDD)
- Unit tests for `OverflowTooltipLabel`:
  - Given a content string and a mocked/specified available width, verify tooltip is set/cleared correctly
  - Verify re-evaluation on `update()` and `on_resize`
  - Cover wide-character case (e.g., emoji) to ensure we don’t regress on width handling
- Integration tests (optional): mount a simple app with a narrow container and assert tooltip presence via widget state

Risks / performance
- Recomputing on every resize for many widgets can be expensive. Mitigation: compute lazily on mouse enter, and/or throttle resize recalcs.
- DataTable limitation may require a separate solution or be explicitly out of scope for first pass.

References
- Widget tooltips API: https://textual.textualize.io/api/widget/#textual.widget.Widget.set_tooltip
- Text overflow: https://textual.textualize.io/styles/text_overflow/
- Text wrapping: https://textual.textualize.io/styles/text_wrap/
- Content API (width helpers): https://textual.textualize.io/api/content/

Open questions
- Should we enable tooltips for multi-line wrapping contexts, or only when nowrap+ellipsis is used?
- Should we compute on hover only (performance) or always keep tooltip state up-to-date (simplicity)?

Owner
- TUI team

Status
- Planned
