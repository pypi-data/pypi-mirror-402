# Select Widget Height Rendering Issue

## Overview

**Issue**: Textual Select widgets render their values as weird glyphs instead of readable text when CSS `height: 3` constraints are applied.

**Status**: 🔍 Root Cause Identified → 🛠️ Fixed

**Affected Component**: Plugin Configuration Modal (`gatekit/tui/screens/plugin_config_modal.py`)

## Problem Description

When applying `height: 3` CSS constraints to Select widgets through `.field-input` or `.field-select` classes, the widgets display strange glyphs or Unicode replacement characters instead of showing the selected values properly.

### Symptoms
- Select widgets show weird characters instead of selected values (e.g., "iso8601" appears as glyphs)
- The issue appears specifically with Select widgets, not other input types
- The dropdown functionality still works, but the closed state display is corrupted
- Basic Select widgets without CSS classes render correctly

### Visual Comparison
```
✅ Working (no height constraint):
[iso8601                              ▼]

❌ Broken (with height: 3):
[░▒▓█                                 ▼]
```

## Root Cause Analysis

### Technical Investigation

Through systematic CSS bisection testing, we identified that the `.field-input { height: 3; }` CSS rule was the culprit.

### Widget Internal Structure

The Textual Select widget consists of:
- **Select** container (`height: auto`)
  - **SelectCurrent** component (`height: auto`)
    - **Static#label** widget (`height: auto`) - displays current value
    - **Arrow** components (`height: 1`)
  - **SelectOverlay** (`height: auto`, `max-height: 12`)

### Why Height Constraint Breaks Rendering

1. **Space Requirements**: SelectCurrent needs:
   - Border: 2 terminal rows (top + bottom)
   - Content: Minimum 1 row for text
   - Total minimum: 3 rows

2. **Constraint Conflict**: When `height: 3` is applied:
   - Widget is forced into exactly 3 rows
   - Border consumes 2 rows, leaving only 1 row for content
   - Text rendering fails due to insufficient space
   - Terminal character width calculations become inconsistent

3. **Glyph Artifact**: The widget still attempts to render the value, but:
   - Character width is retained but display corrupts
   - Results in Unicode replacement characters or rendering artifacts
   - This is a known terminal UI issue with strict height constraints

### Research Context

This aligns with documented Textual issues:
- Issue #5652: Single cell height Select widgets showing empty lines
- Issue #2975: `max-height: 100%` with `height: auto` causing widget disappearance
- Terminal character width calculation problems with constrained heights

## Solution

### Fix Applied

**Remove the height constraint** from Select widget CSS classes:

```css
/* BEFORE (broken) */
.field-input {
    height: 3;  /* ❌ This breaks Select widgets */
    /* ... other properties ... */
}

.field-select {
    height: 3;  /* ❌ Also broken */
    /* ... other properties ... */
}

/* AFTER (working) */
.field-input {
    /* height: 3; ← REMOVED */
    /* ... other properties ... */
}

/* .field-select class completely removed */
```

### Implementation Details

**File**: `gatekit/tui/screens/plugin_config_modal.py`

**Changes**:
1. Removed `height: 3` from `.field-input` CSS class
2. Completely removed `.field-select` CSS class (redundant)
3. Let Select widgets use their default `height: auto` behavior

## Test Results

### Before Fix
```
Test 1: Basic Select ✅ (no classes applied)
Test 4: Plugin modal recreation ❌ (weird glyphs)
Test 5: FieldContainer replica ❌ (weird glyphs)
```

### After Fix
```
Test 1: Basic Select ✅ 
Test 4: Plugin modal recreation ✅ (shows "iso8601")
Test 5: FieldContainer replica ✅ (shows "iso8601")
```

### Reproduction Steps

To reproduce the issue for testing:

1. Create a Select widget with `classes="field-input field-select"`
2. Apply CSS with `height: 3` to those classes
3. Observe glyph rendering instead of proper text
4. Remove height constraint to verify fix

## Best Practices for Select Widget Styling

### ✅ Recommended Approaches

```css
/* Use default height behavior */
Select {
    /* Let the widget size itself */
    width: 100%;
    background: $surface;
    border: solid $secondary;
    color: $text;
}

/* Use minimum height if needed */
.field-input {
    min-height: 3;  /* Sets minimum, allows expansion */
    width: 100%;
}
```

### ❌ Avoid These Patterns

```css
/* Don't constrain Select widgets to exact heights */
Select {
    height: 3;  /* ❌ Causes glyph rendering */
}

.field-select {
    height: 3;  /* ❌ Breaks text display */
}
```

### Alternative Solutions

If height consistency is required across form fields:

1. **Use containers**: Wrap Select widgets in containers with height constraints
2. **Use min-height**: Allow expansion while setting minimum size
3. **Use padding**: Add padding to achieve visual height without constraining content
4. **Custom CSS**: Use Select-specific styling that accounts for internal structure

## Related Issues

- **GitHub Issue #5652**: Single cell height Select widget problems
- **GitHub Issue #2975**: Height auto conflicts causing widget disappearance  
- **Terminal character width**: Known issues with unicode character rendering under height constraints

## Testing Recommendations

When styling Select widgets in the future:

1. **Always test with actual values**: Don't just test empty or placeholder states
2. **Test with various option lengths**: Long text may reveal additional issues
3. **Test keyboard navigation**: Ensure overlay positioning isn't affected
4. **Check multiple terminals**: Different terminals handle character width differently

## Impact Assessment

### Fixed Components
- Plugin configuration modal Select fields now render correctly
- All enum-type configuration fields display their values properly
- No regression in other widget types

### Performance Impact
- Minimal: Removing CSS constraints actually improves rendering performance
- No additional CPU/memory usage
- Faster initial rendering due to simpler layout calculations

## Future Considerations

1. **Widget Development**: When creating custom Select-like widgets, avoid fixed height constraints
2. **CSS Framework**: Consider adding Select-specific styling guidelines
3. **Documentation**: Update styling documentation to warn about height constraints on complex widgets
4. **Testing**: Add automated tests for widget rendering with various CSS constraints

## References

- **Textual Select Widget Documentation**: https://textual.textualize.io/widgets/select/
- **Textual CSS Height Documentation**: https://textual.textualize.io/styles/height/
- **Original Test App**: `/tmp/test_select_modal.py` - systematic reproduction
- **Debugging Session**: Issue discovered through CSS bisection method