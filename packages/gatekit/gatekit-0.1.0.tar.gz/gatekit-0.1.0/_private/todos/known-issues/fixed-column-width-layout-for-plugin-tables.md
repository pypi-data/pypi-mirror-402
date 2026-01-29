# Fixed Column Width Layout for Plugin Tables

**Status:** Not Started
**Priority:** High
**Complexity:** Medium (~2-3 hours)

## Problem Statement

Plugin table column headers and rows are misaligned when using fractional units (`fr`) for column widths. This is a fundamental layout issue that cannot be solved with `fr` units.

### Root Cause

Each `Horizontal` container (header and each row) calculates flex layout independently:

```
PluginTableWidget (Container)
├── PluginTableHeader (Horizontal) ← Independent flex context
└── rows_container (Container)
    ├── PluginRowWidget #1 (Horizontal) ← Independent flex context
    ├── PluginRowWidget #2 (Horizontal) ← Independent flex context
    └── ...
```

**The Issue:** When columns use `fr` units, Textual's layout algorithm:
1. Resolves fixed widths first (checkbox: 3, priority: 8)
2. Calculates remaining space: `remaining = container_width - sum(fixed_widths)`
3. Distributes remaining space proportionally: `width = (fr_value / total_fr) × remaining`

**Why it fails:**
- Header Actions column: "Actions" text ≈ 7-8 cols
- Row Actions column: "Configure" button ≈ 12-13 cols
- Different fixed widths → different remaining space → different `fr` unit values → **misalignment**

Example:
```
Header: remaining = W - 3 - 8 - 8 = W - 19
  Name (2.5fr): 71.4% of (W - 19)
  Status (1fr): 28.6% of (W - 19)

Row: remaining = W - 3 - 8 - 13 = W - 23
  Name (2.5fr): 71.4% of (W - 23)
  Status (1fr): 28.6% of (W - 23)

Result: Even though ratios match, pixel widths differ by ~4 cols → misalignment
```

## Proposed Solution

**Use programmatically-calculated fixed widths** with priority-based column allocation.

### Core Principles

1. **Calculate once, apply everywhere** - One width calculation shared by header and all rows
2. **Fixed integers only** - No `fr` units, guarantees alignment
3. **Priority-based allocation** - Ensure critical columns always visible
4. **Responsive** - Recalculate on container resize
5. **Context-aware** - Adapt to different container widths (global: ~60 cols, server: ~84 cols)

### Column Priority Order

**High → Low importance:**

1. **Checkbox** (3 cols) - Always show, critical for enable/disable
2. **Actions** (13 cols) - Always show, critical for "Configure" button
3. **Name** (15-30 cols) - Show as much as possible, primary identifier
4. **Priority** (8 cols) - Show if space available, hide if cramped
5. **Status/Scope** (10+ cols) - Show remaining space, hide if too narrow

This ensures users can always **see what the plugin is** and **interact with it**, even in constrained layouts.

## Architecture Design

### 1. Width Calculation on Resize

```python
class PluginTableWidget(Container):
    def __init__(self, ...):
        self._column_widths: Optional[Dict[str, int]] = None
        self._last_container_width: int = 0

    async def on_resize(self, event: Resize) -> None:
        """Recalculate and apply column widths when container resizes."""
        # Only recalculate if width actually changed
        if event.width != self._last_container_width:
            self._last_container_width = event.width
            self._column_widths = self._calculate_column_widths(event.width)
            self._apply_column_widths()

    def _calculate_column_widths(self, container_width: int) -> Dict[str, int]:
        """Calculate fixed column widths with priority-based allocation.

        Args:
            container_width: Total width available to the table widget

        Returns:
            Dictionary mapping column names to integer widths
        """
        # Constants
        CHECKBOX_WIDTH = 3
        ACTIONS_WIDTH = 13  # "Configure" button
        PRIORITY_WIDTH = 8
        MARGINS_PER_COLUMN = 2  # Left + right margin (margin: 0 1)
        BORDER_PADDING = 4  # 2 for border, 2 for widget padding

        # Calculate margins: checkbox + name + status + priority + actions = 5 columns
        total_margins = MARGINS_PER_COLUMN * 5

        # Available space after accounting for borders and margins
        available = container_width - BORDER_PADDING - total_margins

        # Allocation: Priority-based progressive disclosure

        # CRITICAL: Always show at full width
        checkbox = CHECKBOX_WIDTH
        actions = ACTIONS_WIDTH
        critical_total = checkbox + actions
        remaining = available - critical_total

        # HIGH PRIORITY: Name - show as much as possible
        NAME_MIN = 15      # Absolute minimum (e.g., "Basic PII Filter" truncates)
        NAME_IDEAL = 30    # Ideal width for full display names
        name = max(NAME_MIN, min(NAME_IDEAL, remaining * 0.6))  # Try to allocate 60% of remaining
        name = int(name)  # Must be integer
        remaining -= name

        # MEDIUM PRIORITY: Priority column - show if we have room
        STATUS_MIN = 10  # Need at least this much for status to be useful
        if self.show_priority and remaining >= (PRIORITY_WIDTH + STATUS_MIN):
            priority = PRIORITY_WIDTH
            remaining -= priority
        else:
            # Not enough space - hide priority column entirely
            priority = 0

        # LOW PRIORITY: Status/Scope - gets whatever is left
        if remaining >= STATUS_MIN:
            status = remaining
        else:
            # Too cramped - hide status column
            status = 0

        return {
            'checkbox': checkbox,
            'name': name,
            'status': status,
            'priority': priority,
            'actions': actions,
        }
```

### 2. Applying Widths to Widgets

```python
class PluginTableWidget(Container):
    def _apply_column_widths(self) -> None:
        """Apply calculated column widths to header and all rows."""
        if not self._column_widths:
            return

        try:
            # Apply to header (if present)
            headers = self.query(PluginTableHeader)
            if headers:
                header = headers.first()
                header.apply_column_widths(self._column_widths)

            # Apply to all rows
            for row in self.query(PluginRowWidget):
                row.apply_column_widths(self._column_widths)

        except Exception as e:
            # Fail gracefully - widgets may not be mounted yet
            from ..debug import get_debug_logger
            logger = get_debug_logger()
            if logger:
                logger.log_event(
                    "column_width_application_failed",
                    widget=self,
                    context={"error": str(e)}
                )
```

### 3. Header Widget Updates

```python
class PluginTableHeader(Horizontal):
    # Remove fractional width calculations from compose()
    # Remove width setting from CSS (will be set programmatically)

    def apply_column_widths(self, widths: Dict[str, int]) -> None:
        """Apply calculated fixed widths to header columns.

        Args:
            widths: Dictionary of column widths from PluginTableWidget
        """
        try:
            # Checkbox spacer
            checkbox = self.query_one(".header-checkbox")
            checkbox.styles.width = widths['checkbox']

            # Name column
            name = self.query_one(".header-name")
            name.styles.width = widths['name']

            # Status/Scope column
            status = self.query_one(".header-status")
            if widths['status'] > 0:
                status.styles.width = widths['status']
                status.styles.display = "block"
            else:
                status.styles.display = "none"  # Hide if no space

            # Priority column
            if self.show_priority:
                priority = self.query_one(".header-priority")
                if widths['priority'] > 0:
                    priority.styles.width = widths['priority']
                    priority.styles.display = "block"
                else:
                    priority.styles.display = "none"

            # Actions column
            actions = self.query_one(".header-actions")
            actions.styles.width = widths['actions']

        except Exception:
            # Widgets may not be composed yet - will be called again
            pass
```

### 4. Row Widget Updates

```python
class PluginRowWidget(Horizontal):
    # Remove fractional width calculations from compose()

    def apply_column_widths(self, widths: Dict[str, int]) -> None:
        """Apply calculated fixed widths to row columns.

        Args:
            widths: Dictionary of column widths from PluginTableWidget
        """
        try:
            # Checkbox
            checkbox = self.query_one("ASCIICheckbox")
            checkbox.styles.width = widths['checkbox']

            # Name
            name = self.query_one(".plugin-name")
            name.styles.width = widths['name']

            # Status/Scope
            status = self.query_one(".plugin-status")
            if widths['status'] > 0:
                status.styles.width = widths['status']
                status.styles.display = "block"
            else:
                status.styles.display = "none"

            # Priority
            if self.show_priority:
                priority = self.query_one(".plugin-priority")
                if widths['priority'] > 0:
                    priority.styles.width = widths['priority']
                    priority.styles.display = "block"
                else:
                    priority.styles.display = "none"

            # Actions (if shown)
            if self.show_actions:
                actions_container = self.query_one(".plugin-actions")
                actions_container.styles.width = widths['actions']

        except Exception:
            pass
```

## CSS Changes Required

### Remove Fractional Widths

**Current CSS (remove these):**
```css
/* PluginRowWidget */
PluginRowWidget > .plugin-name {
    /* Remove: width set via Scalar(fr, Unit.FRACTION) in compose() */
}

PluginRowWidget > .plugin-status {
    width: 1fr;  /* REMOVE THIS */
    min-width: 0;
}

PluginRowWidget > .plugin-actions {
    width: auto;  /* REMOVE THIS */
}
```

**New CSS (fixed widths set programmatically):**
```css
/* PluginRowWidget - widths set in Python, just keep layout properties */
PluginRowWidget > .plugin-name {
    /* width: set programmatically */
    margin: 0 1;
    content-align: left middle;
    overflow: hidden;
    text-overflow: ellipsis;
}

PluginRowWidget > .plugin-status {
    /* width: set programmatically */
    /* display: set programmatically (none if hidden) */
    margin: 0 1;
    content-align: left middle;
    overflow: hidden;
    text-overflow: ellipsis;
}

PluginRowWidget > .plugin-priority {
    /* width: set programmatically */
    /* display: set programmatically (none if hidden) */
    margin: 0 1;
    content-align: center middle;
}

PluginRowWidget > .plugin-actions {
    /* width: set programmatically */
    margin: 0 1;
    align: left middle;
}
```

Same changes apply to `PluginTableHeader`.

## Implementation Steps

### Phase 1: Core Infrastructure
1. ✅ Add `_column_widths` and `_last_container_width` fields to `PluginTableWidget.__init__()`
2. ✅ Implement `_calculate_column_widths()` with priority-based algorithm
3. ✅ Implement `_apply_column_widths()` to propagate widths
4. ✅ Add `on_resize()` event handler to trigger recalculation

### Phase 2: Widget Updates
5. ✅ Add `apply_column_widths()` method to `PluginTableHeader`
6. ✅ Add `apply_column_widths()` method to `PluginRowWidget`
7. ✅ Remove fractional width calculations from both classes' `compose()` methods
8. ✅ Update CSS to remove fixed/fractional widths, keep layout properties only

### Phase 3: Testing & Edge Cases
9. ✅ Test with various terminal widths (60, 80, 100, 120, 150 cols)
10. ✅ Test global plugins (narrow container, ~60 cols)
11. ✅ Test server plugins (wide container, ~84 cols)
12. ✅ Test with long plugin names (ensure truncation works)
13. ✅ Test with missing plugins ("⚠ name (not found)" format)
14. ✅ Verify priority column hides in narrow layouts
15. ✅ Verify status column hides in very narrow layouts

## Width Allocation Examples

### Scenario 1: Global Plugins (Narrow, ~60 cols available)

```
Container: 60 cols
- Borders/padding: 4
- Column margins: 10
- Available: 46 cols

Allocation:
- Checkbox: 3 (critical)
- Actions: 13 (critical)
- Remaining: 30
- Name: 18 (60% of 30, clamped to NAME_MIN=15)
- Remaining: 12
- Priority: 8 (fits: 12 >= 8 + 10? No, skip)
- Priority: 0 (hidden)
- Status: 12 (gets remainder)

Result: [✓] [Plugin Name Short] [Scope Text] [Configure]
```

### Scenario 2: Server Plugins (Wide, ~84 cols available)

```
Container: 84 cols
- Borders/padding: 4
- Column margins: 10
- Available: 70 cols

Allocation:
- Checkbox: 3 (critical)
- Actions: 13 (critical)
- Remaining: 54
- Name: 30 (60% of 54 = 32, clamped to NAME_IDEAL=30)
- Remaining: 24
- Priority: 8 (fits: 24 >= 8 + 10? Yes)
- Remaining: 16
- Status: 16 (gets remainder)

Result: [✓] [Plugin Name Much Longer Her] [Scope/Status] [10] [Configure]
```

### Scenario 3: Very Wide (120+ cols)

```
Container: 120 cols
- Available: 106 cols after margins/padding

Allocation:
- Checkbox: 3
- Actions: 13
- Remaining: 90
- Name: 30 (clamped at NAME_IDEAL, even though 60% = 54)
- Remaining: 60
- Priority: 8
- Remaining: 52
- Status: 52 (plenty of room!)

Result: [✓] [Full Plugin Name Visible!!] [Very Long Scope Text Fits] [10] [Configure]
```

## Edge Cases & Considerations

### 1. Initial Render (No Size Yet)
- `on_resize()` will fire after initial layout
- Widgets compose with default styling
- Widths applied asynchronously after first resize event
- **Mitigation:** Set reasonable CSS defaults that won't break layout

### 2. Rapid Resizing
- Only recalculate if width actually changed
- Check: `if event.width != self._last_container_width`
- Prevents redundant calculations on height-only changes

### 3. Widget Not Mounted Yet
- `apply_column_widths()` may be called before widgets are composed
- **Mitigation:** Wrap in try/except, fail gracefully
- Will be called again on next resize

### 4. Global vs Server Plugins
- Both use same `PluginTableWidget` class
- Different container widths automatically handled by calculation
- Global: narrower → priority may hide
- Server: wider → all columns fit

### 5. Missing Plugin Names
- "⚠ Plugin Name (not found)" format adds ~15 chars
- Already accounted for in `_calculate_name_width()`
- Name column calculation considers longest name

### 6. Auditing Plugins (No Priority Column)
- `show_priority=False` parameter
- Algorithm checks `if self.show_priority` before allocating priority width
- More space available for name/status

### 7. Actions Column Variability
- "Configure" = 9 chars + padding ≈ 13 cols
- "Use Global" = 10 chars + padding ≈ 14 cols
- **Solution:** Calculate based on max button width (14 cols) or measure dynamically

## Testing Checklist

### Visual Tests (Manual)
- [ ] Global security plugins align at 80 cols terminal
- [ ] Global auditing plugins align at 80 cols terminal
- [ ] Server security plugins align at 80 cols terminal
- [ ] Server middleware plugins align at 120 cols terminal
- [ ] Server auditing plugins align at 150 cols terminal
- [ ] Priority column hides at ~70 cols terminal
- [ ] Status column hides at ~55 cols terminal
- [ ] Long plugin names truncate with ellipsis
- [ ] Missing plugins show "⚠ name (not found)" properly
- [ ] Resize terminal: columns adjust smoothly

### Unit Tests (Automated)
```python
def test_column_width_calculation_wide():
    """Test column allocation with plenty of space."""
    widget = PluginTableWidget(...)
    widths = widget._calculate_column_widths(120)

    assert widths['checkbox'] == 3
    assert widths['actions'] == 13
    assert widths['name'] == 30  # Clamped at ideal
    assert widths['priority'] == 8
    assert widths['status'] > 10

def test_column_width_calculation_narrow():
    """Test priority column hiding in narrow layout."""
    widget = PluginTableWidget(...)
    widths = widget._calculate_column_widths(60)

    assert widths['checkbox'] == 3
    assert widths['actions'] == 13
    assert widths['name'] >= 15  # At least minimum
    assert widths['priority'] == 0  # Hidden
    assert widths['status'] >= 0

def test_column_width_calculation_very_narrow():
    """Test status column hiding in very narrow layout."""
    widget = PluginTableWidget(...)
    widths = widget._calculate_column_widths(50)

    assert widths['checkbox'] == 3
    assert widths['actions'] == 13
    assert widths['name'] >= 15
    assert widths['priority'] == 0  # Hidden
    assert widths['status'] == 0  # Hidden too

def test_widths_applied_to_all_rows():
    """Test that all rows get same widths."""
    widget = PluginTableWidget(...)
    widget._column_widths = {'checkbox': 3, 'name': 25, ...}
    widget._apply_column_widths()

    # All rows should have matching widths
    rows = widget.query(PluginRowWidget)
    for row in rows:
        assert row.query_one(".plugin-name").styles.width == 25
```

## Performance Considerations

- **Calculation cost:** O(1) - simple arithmetic
- **Application cost:** O(n) where n = number of rows
- **Frequency:** Only on width change (not height-only resizes)
- **Expected impact:** Negligible - runs in microseconds

## Rollback Plan

If issues arise:
1. Git revert to commit before changes
2. Old CSS with `1fr` status and `auto` actions still in history
3. Known issue: misalignment, but functional

## Future Enhancements

### Dynamic Actions Width
Currently hardcoded to 13 cols for "Configure". Could measure actual button widths:

```python
def _calculate_actions_width(self) -> int:
    """Calculate max width needed for action buttons."""
    # Check if any rows have "Use Global" (14 cols) vs just "Configure" (13 cols)
    has_use_global = any(
        p.get('inheritance') in ['overrides', 'server-only']
        for p in self.plugins_data
    )
    return 14 if has_use_global else 13
```

### Adaptive Name/Status Split
Instead of fixed 60/40, could analyze actual data:
- If all status text is short ("Global", "Inherited"), allocate more to name
- If status text is long ("filesystem_server only"), allocate more to status

## Success Criteria

- ✅ Column headers align perfectly with column data
- ✅ Alignment holds at all terminal widths (60-150 cols)
- ✅ Critical columns (checkbox, actions) always fully visible
- ✅ Layout adapts gracefully to narrow terminals
- ✅ No visual regressions in existing functionality
- ✅ Code is maintainable and well-documented

## Related Files

- `gatekit/tui/widgets/plugin_table.py` - Main implementation
- `gatekit/tui/screens/config_editor/base.py` - Container CSS
- `gatekit/tui/screens/config_editor/plugin_rendering.py` - Table instantiation

## References

- Textual layout algorithm: `/tmp/textual/src/textual/_resolve.py`
- Horizontal layout: `/tmp/textual/src/textual/layouts/horizontal.py`
- Git history: Commits `b7228d0` and `971983b` introduced fractional widths
