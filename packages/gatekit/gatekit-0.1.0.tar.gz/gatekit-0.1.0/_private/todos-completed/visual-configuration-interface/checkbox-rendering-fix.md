# Mac Terminal Checkbox Rendering Issue - Custom Widget Solution

## Problem Summary
The checkbox widgets in the Gatekit TUI are not rendering properly on Mac Terminal.app due to poor Unicode half-block character support. Instead of showing proper checkbox borders, they appear as horizontal lines (`▔▔▔▔`) or other malformed characters.

## Root Cause Analysis

### Textual's Checkbox Implementation
Textual uses three Unicode characters to create checkboxes:
- **BUTTON_LEFT**: `▐` (U+2590 - Right half block)
- **BUTTON_INNER**: `X` (ASCII X for checked state)  
- **BUTTON_RIGHT**: `▌` (U+258C - Left half block)

This creates a visual pattern like: `▐X▌` (checked) or `▐ ▌` (unchecked)

### Mac Terminal.app Limitations
1. **Poor Unicode Support**: Terminal.app has known issues with Unicode box-drawing and half-block characters
2. **Font Rendering**: Different fonts may not include complete Unicode block character sets
3. **Limited Color Support**: Only 256 colors vs modern terminals with full color support
4. **Performance**: Slower rendering compared to modern terminal emulators

### Test Results
Our investigation using test programs confirmed:
- Widget creation works correctly
- The issue is specifically in visual rendering
- Characters render as `▔▔▔▔` instead of proper half-blocks
- This affects many Mac users on the default Terminal.app

## Recommended Solution: Custom ASCII-Safe Checkbox Widget

Since many users will be on Mac Terminal.app, we should implement a custom checkbox widget that uses ASCII-safe characters.

### Implementation Plan

#### 1. Create Custom Checkbox Widget Class

**File**: `gatekit/tui/widgets/ascii_checkbox.py`

```python
"""ASCII-safe checkbox widget for better Mac Terminal compatibility."""

from textual.widgets._toggle_button import ToggleButton


class ASCIICheckbox(ToggleButton):
    """Checkbox widget using ASCII-safe characters for Mac Terminal compatibility."""
    
    # Override the Unicode half-block characters with ASCII brackets
    BUTTON_LEFT: str = "["
    BUTTON_INNER: str = "X"  # Keep X for checked, space for unchecked
    BUTTON_RIGHT: str = "]"
    
    # Custom CSS to ensure proper spacing
    DEFAULT_CSS = """
    ASCIICheckbox {
        width: auto;
        border: none;
        padding: 0;
        background: transparent;
        text-wrap: nowrap;
        text-overflow: ellipsis;
        
        & > .toggle--button {
            color: $text;
            background: transparent;
        }
        
        &.-on > .toggle--button {
            color: $success;
            background: transparent;
        }
        
        &:focus > .toggle--button {
            color: $text-success;
            background: $block-cursor-background;
        }
    }
    """
    
    def _button(self) -> Content:
        """Override button rendering to handle unchecked state."""
        from textual.content import Content
        from textual.style import Style
        
        # Get the button style
        button_style = self.get_visual_style("toggle--button")
        
        # For unchecked state, use space instead of X
        inner_char = self.BUTTON_INNER if self.value else " "
        
        return Content.assemble(
            (self.BUTTON_LEFT, button_style),
            (inner_char, button_style),
            (self.BUTTON_RIGHT, button_style),
        )
```

#### 2. Update Global Plugin Widgets

**File**: `gatekit/tui/widgets/global_plugins.py`

```python
# Add import at top
from gatekit.tui.widgets.ascii_checkbox import ASCIICheckbox

# In GlobalPluginItem.compose() method, replace:
yield Checkbox(
    "",
    value=self.plugin_data["enabled"],
    id=f"checkbox_{self.plugin_data['policy']}"
)

# With:
yield ASCIICheckbox(
    "",
    value=self.plugin_data["enabled"],
    id=f"checkbox_{self.plugin_data['policy']}"
)
```

#### 3. Update CSS Styling

**In `GlobalPluginItem` CSS (global_plugins.py):**

```css
/* Update checkbox styling for ASCII version */
GlobalPluginItem > ASCIICheckbox {
    width: 3;          /* Reduced from 4 since ASCII is more compact */
    min-width: 3;
    margin: 0 1;
}
```

### Visual Result

The checkboxes will render as:
- **Checked**: `[X]` (in success color)
- **Unchecked**: `[ ]` (in normal text color)
- **Focused**: Highlighted background with cursor colors

### Alternative Approaches Considered

#### 1. Environment Variable Fix
Setting `NCURSES_NO_UTF8_ACS=1` might help but:
- Requires user configuration
- Not guaranteed to work on all Mac setups
- Puts burden on end users

#### 2. Font Recommendations
Suggesting specific fonts (Monaco, Menlo) might help but:
- Requires user terminal configuration
- May not be available on all systems
- Inconsistent results across versions

#### 3. Terminal Emulator Switch
Recommending iTerm2 or other modern terminals:
- Good long-term solution
- But many users prefer default Terminal.app
- Should not be required for basic functionality

### Implementation Steps

1. **Create ASCII Checkbox Widget**
   - Implement `ASCIICheckbox` class with ASCII-safe characters
   - Add proper CSS styling for visual consistency
   - Ensure accessibility and keyboard navigation works

2. **Update Plugin Widgets** 
   - Replace `Checkbox` imports with `ASCIICheckbox`
   - Update CSS selectors and styling
   - Maintain existing functionality and event handling

3. **Testing**
   - Test on Mac Terminal.app (primary target)
   - Verify on other terminals (iTerm2, Linux terminals)
   - Ensure no regression in functionality
   - Test checkbox state changes and events

4. **Documentation**
   - Update user documentation about terminal compatibility
   - Add troubleshooting section for rendering issues
   - Consider adding environment variable option as alternative

### Benefits of This Approach

1. **Universal Compatibility**: ASCII characters work on all terminals
2. **No User Configuration**: Works out-of-the-box
3. **Professional Appearance**: Clean `[X]` / `[ ]` style is familiar
4. **Maintainable**: Simple implementation, easy to modify
5. **Backward Compatible**: Doesn't break existing functionality

### File Locations

- **New file**: `gatekit/tui/widgets/ascii_checkbox.py`
- **Modify**: `gatekit/tui/widgets/global_plugins.py`
- **Test**: Add tests in `tests/unit/tui/test_ascii_checkbox.py`

### Testing Requirements

Before considering this fix complete:
1. Visual verification on Mac Terminal.app
2. Functional testing of checkbox state changes
3. Keyboard navigation testing
4. Focus and hover state verification
5. Integration testing with plugin configuration flow

This solution prioritizes user experience and compatibility over using the latest Unicode features, which aligns with Gatekit's goal of being a reliable, professional tool that works consistently across platforms.