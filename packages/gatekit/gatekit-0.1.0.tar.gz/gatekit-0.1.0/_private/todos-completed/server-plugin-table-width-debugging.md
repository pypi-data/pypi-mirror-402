# Server Plugin Table Width Debugging

## Problem Statement
The PluginTableWidget container (with blue border) for server plugin tables is expanding to fill nearly the full width of its parent container (~130+ columns) instead of shrink-wrapping to its content (~70-80 columns). The table content itself (headers, rows, columns) is perfectly sized and aligned, but the border extends way beyond the content.

## Current State
- Table content: ~70-80 columns (correct)
- Table container: ~130+ columns (incorrect - should match content)
- CSS: PluginTableWidget has `width: auto` which should size to content
- Classes: Server tables get `.server-mode` class which sets `width: auto !important`

## Potential Root Causes

### 1. Circular Width Dependency
- PluginTableWidget: `width: auto` (size to children)
- PluginRowWidget: `width: 100%` (fill parent)
- Creates ambiguous layout that Textual resolves by expanding

### 2. Parent Container Influence
- Hierarchy: Container → VerticalScroll → Horizontal → Container → PluginTableWidget
- One parent might be forcing expansion

### 3. Inner Container Issue
- The "table-scroll" Container inside PluginTableWidget might be expanding
- Container has `classes="table-scroll"` with CSS: `height: auto; overflow: hidden;` (no width specified)

### 4. CSS Class Not Applying
- The `.server-mode` class should apply but might not be working
- Inline styles might be overriding CSS

## Systematic Debugging Strategy

### Phase 1: Gather Diagnostic Information

#### 1.1 Add Comprehensive CSS/Style Logging
In PluginTableWidget's `on_mount()` or `on_resize()`:
```python
# Log actual CSS classes and timing
logger.log_event("TABLE_CSS_DEBUG", context={
    "event": "mount" or "resize",
    "server_name": self.server_name,
    "classes": list(self.classes),
    "has_server_mode": "server-mode" in self.classes,
    "computed_width": str(self.styles.width),
    "computed_max_width": str(self.styles.max_width),
    "computed_min_width": str(self.styles.min_width),
    "actual_size": self.size,
})
```

#### 1.2 Trace Width Source
```python
# Log parent chain with actual rendered sizes
parent = self.parent
depth = 0
while parent and depth < 5:
    logger.log_event(f"PARENT_{depth}", context={
        "class": parent.__class__.__name__,
        "size": parent.size,
        "styles_width": str(parent.styles.width),
        "content_size": parent.content_size if hasattr(parent, 'content_size') else None,
    })
    parent = parent.parent
    depth += 1
```

#### 1.3 Inspect Inner Container
```python
# Check the table-scroll container
try:
    scroll = self.query_one(".table-scroll")
    logger.log_event("TABLE_SCROLL_CONTAINER", context={
        "size": scroll.size,
        "styles_width": str(scroll.styles.width),
        "styles_display": str(scroll.styles.display),
    })
except:
    pass
```

#### 1.4 Add Visual Debug Borders
```python
# Temporarily in on_mount() - add colored borders to identify which container is expanding
try:
    scroll = self.query_one(".table-scroll")
    scroll.styles.border = ("heavy", "green")  # Inner container

    # Also add border to first row to see content vs container
    rows = self.query(PluginRowWidget)
    if rows:
        rows[0].styles.border = ("heavy", "yellow")
except:
    pass
```

#### 1.5 Measure Expected vs Actual Width
```python
# Calculate what width SHOULD be based on column configuration
expected_width = (
    sum(self.column_widths.values()) +
    len(self.column_widths) - 1  # column separators
)
logger.log_event("WIDTH_DELTA", context={
    "expected_content_width": expected_width,
    "actual_widget_width": self.size.width,
    "delta": self.size.width - expected_width,
    "column_widths": self.column_widths,
})
```

### Phase 2: Test Hypotheses

#### 2.1 Test Circular Dependency
Add to PluginTableWidget CSS:
```css
PluginTableWidget.server-mode PluginRowWidget {
    width: auto;  /* Break circular dependency */
}
```

#### 2.2 Test Container Isolation
Temporarily in `_apply_column_widths()`:
```python
if self.server_name != GLOBAL_SCOPE:
    self.styles.width = 80  # Fixed width test
    logger.log_event("FIXED_WIDTH_TEST", context={
        "applied": True,
        "actual_size": self.size.width after refresh
    })
```

#### 2.3 Test Without Inner Container
Modify `compose()` to mount rows directly:
```python
# Instead of:
# with Container(classes="table-scroll"):
#     for plugin_data in self.plugins_data:
#         yield PluginRowWidget(...)

# Try:
for plugin_data in self.plugins_data:
    yield PluginRowWidget(...)
```

#### 2.4 Test Parent Horizontal Container Influence
The parent hierarchy includes a `Horizontal` container that might be forcing expansion.
Temporarily modify the parent hierarchy to bypass or constrain it:
```python
# In the parent component, try wrapping server tables differently
# or add width constraints to the Horizontal container
```

### Phase 3: Minimal Reproduction (Fallback)

If none of the hypotheses identify the issue, create a minimal standalone reproduction:
```python
# Create minimal_table_test.py with just:
# - A Horizontal container
# - A Container with width: auto and a blue border
# - Some content inside (Static text widgets)
# Run standalone to see if it's Textual behavior or our code
```

This will isolate whether the issue is:
- Textual's layout algorithm behavior
- Something specific to our widget hierarchy
- CSS specificity/cascade issues

### Phase 4: Apply Fix

Based on findings, implement one of:

#### Option A: Fix Circular Dependency
```css
/* In DEFAULT_CSS */
PluginTableWidget.server-mode PluginRowWidget {
    width: auto;
    max-width: 100%;
}
```

#### Option B: Constrain Container
```python
def compose(self):
    if self.server_name != GLOBAL_SCOPE:
        # Set explicit size on table-scroll container
        rows_container = Container(classes="table-scroll")
        rows_container.styles.width = "auto"
```

#### Option C: Remove Inner Container
```python
# Mount rows directly without wrapper
# May need to handle scrolling differently
```

#### Option D: Force CSS Specificity
```css
PluginTableWidget.server-mode {
    width: auto !important;
    max-width: fit-content !important;  /* if supported */
}
```

## Implementation Order

1. **Start with Phase 1.4**: Add visual debug borders first (instant feedback)
2. **Add Phase 1.1-1.5**: Comprehensive diagnostic logging
3. **Run TUI and analyze**: Visual borders + logs should identify the culprit
4. **Test most likely hypothesis**: Based on findings (likely 2.1 circular dependency or 2.4 parent container)
5. **Phase 3 if needed**: Create minimal reproduction to isolate Textual vs our code
6. **Apply minimal fix**: Based on test results (Phase 4 options)
7. **Verify no regressions**: Global tables still fill width, alignment preserved

## Success Criteria

- Server plugin tables have borders that tightly wrap content (~70-80 columns)
- Global plugin tables continue to fill their container width
- No visual regression in layout or alignment
- Solution uses proper CSS/Textual patterns, not hacks

## Notes

- The content (columns, rows) renders correctly, so column width calculations are fine
- Only the container border is the issue
- This affects all three server plugin tables (security, middleware, auditing)
- Global plugin tables are intentionally different (`width: 100%`) so comparing them isn't useful
- No working version exists in git history - this has never been fully correct
- The blue border on PluginTableWidget is already visible - that's what's showing the problem
- The `.table-scroll` inner Container has minimal CSS: just `height: auto; overflow: hidden;` (no width specified)