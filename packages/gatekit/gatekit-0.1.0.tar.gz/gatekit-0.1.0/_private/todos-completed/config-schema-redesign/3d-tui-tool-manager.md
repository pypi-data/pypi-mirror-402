# Phase 3d: TUI Tool Manager Special Handling

## Overview
Implement special handling for tool_manager configuration to enforce allowlist vs blocklist mode.

## Critical Design Points
1. **Mode enforcement** - Allowlist XOR blocklist, never mixed
2. **Action constraints** - Mode determines allowed action values
3. **Migration handling** - Detect and fix mixed configurations
4. **No hardcoded names** - Use handler detection, not string comparison

## Implementation

### Step 1: Tool Manager Mode Selector
**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/utils/tool_manager_widget.py`

```python
"""Special widget for tool_manager configuration with mode enforcement."""

from typing import Dict, Any, List, Optional
from textual.app import ComposeResult
from textual.widgets import RadioSet, RadioButton, Label, Static
from textual.containers import Container, Vertical
from textual.message import Message

class ToolManagerModeSelector(Container):
    """Mode selector for tool configuration to enforce allowlist vs blocklist.
    
    This helps users organize their tools for better workflow management.
    Generic widget that works for any plugin needing mutually exclusive modes.
    """
    
    class ModeChanged(Message):
        """Message when mode is changed."""
        def __init__(self, mode: str):
            self.mode = mode
            super().__init__()
    
    def __init__(self, tools: List[Dict[str, Any]] = None,
                 id: Optional[str] = None):
        """Initialize with existing tools to detect current mode.
        
        Args:
            tools: Existing tool configurations
            id: Widget ID
        """
        super().__init__(id=id or "mode_selector", classes="mode-selector")
        self.tools = tools or []
        self.current_mode = self._detect_mode()
        self._has_mixed_mode = False
    
    def _detect_mode(self) -> str:
        """Detect current mode from existing tools.
        
        Returns:
            "allowlist", "blocklist", or "empty"
        """
        if not self.tools:
            return "empty"
        
        # Check all actions
        actions = {tool.get("action") for tool in self.tools if "action" in tool}
        
        if not actions:
            return "empty"
        elif actions == {"allow"}:
            return "allowlist"
        elif actions == {"deny"}:
            return "blocklist"
        elif len(actions) > 1:
            # Mixed mode - require explicit choice
            self._has_mixed_mode = True
            return "undecided"  # NOT defaulting to allowlist
        else:
            # Single action type
            return "allowlist" if "allow" in actions else "blocklist"
    
    def compose(self) -> ComposeResult:
        """Compose the mode selector."""
        with Vertical():
            yield Label("Tool Configuration Mode", classes="section-title")
            
            # Warning if mixed mode detected
            if self._has_mixed_mode:
                yield Static(
                    "⚠️ Mixed allow/deny rules detected. "
                    "Please select a single mode to organize your tools consistently.",
                    classes="warning-message"
                )
            
            yield Static(
                "Choose how to manage tool availability:\n"
                "• Allowlist: Start with no tools, explicitly enable the ones you need\n"
                "• Blocklist: Start with all tools, explicitly disable ones you don't want",
                classes="field-description"
            )
            
            with RadioSet(id="tool_mode", name="mode"):
                yield RadioButton(
                    "Allowlist Mode\n"
                    "Start with a minimal toolset, add tools as needed for focused workflows",
                    value="allowlist",
                    id="mode_allowlist"
                )
                yield RadioButton(
                    "Blocklist Mode\n"
                    "Start with all tools available, hide specific tools to reduce clutter",
                    value="blocklist",
                    id="mode_blocklist"
                )
            
            # Set initial selection
            self._set_initial_mode()
    
    def _set_initial_mode(self):
        """Set the initial radio button selection."""
        # This is called after compose, so widgets exist
        if self.current_mode == "blocklist":
            self.query_one("#mode_blocklist", RadioButton).value = True
        elif self.current_mode == "allowlist":
            self.query_one("#mode_allowlist", RadioButton).value = True
        # If "undecided", neither is selected - user must choose
    
    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle mode change."""
        if event.radio_set.id == "tool_mode":
            new_mode = event.radio_set.pressed_button.value
            self.current_mode = new_mode
            self.post_message(self.ModeChanged(new_mode))
    
    def get_mode(self) -> str:
        """Get the selected mode.
        
        Returns:
            "allowlist" or "blocklist"
        """
        try:
            radio_set = self.query_one("#tool_mode", RadioSet)
            pressed = radio_set.pressed_button
            return pressed.value if pressed else self.current_mode
        except:
            return self.current_mode
    
    def validate_tools(self, tools: List[Dict[str, Any]]) -> List[str]:
        """Validate tools against selected mode.
        
        Args:
            tools: List of tool configurations
            
        Returns:
            List of error messages
        """
        mode = self.get_mode()
        errors = []
        
        for i, tool in enumerate(tools):
            tool_name = tool.get("tool", f"Tool {i+1}")
            action = tool.get("action")
            
            if mode == "allowlist" and action != "allow":
                errors.append(
                    f"{tool_name}: In allowlist mode, action must be 'allow' (found '{action}')"
                )
            elif mode == "blocklist" and action != "deny":
                errors.append(
                    f"{tool_name}: In blocklist mode, action must be 'deny' (found '{action}')"
                )
        
        return errors
    
    def fix_tools_for_mode(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fix tool actions to match selected mode.
        
        Args:
            tools: List of tool configurations
            
        Returns:
            Fixed tool configurations
        """
        mode = self.get_mode()
        fixed_tools = []
        
        for tool in tools:
            fixed_tool = tool.copy()
            if mode == "allowlist":
                fixed_tool["action"] = "allow"
            else:
                fixed_tool["action"] = "deny"
            fixed_tools.append(fixed_tool)
        
        return fixed_tools
```

### Step 2: Integration with Config Modal
**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/screens/plugin_config_modal_ext.py`

```python
"""Extension to plugin config modal for tool_manager support."""

from typing import Dict, Any, List
from textual.app import ComposeResult
from textual.widgets import Button, Label
from textual.containers import Horizontal, Vertical
from gatekit.tui.utils.tool_manager_widget import ToolManagerModeSelector

class ToolManagerConfigExtension:
    """Extension mixin for tool_manager configuration.
    
    This is designed as a mixin to avoid hardcoding in the main modal.
    """
    
    def should_use_mode_selector(self, handler_name: str, 
                                plugin_class: Any) -> bool:
        """Check if this plugin needs mode selection.
        
        Args:
            handler_name: Plugin handler name
            plugin_class: Plugin class
            
        Returns:
            True if mode selector should be used
        """
        # Check for a class attribute that indicates mode selection
        # This avoids hardcoding "tool_manager"
        return getattr(plugin_class, 'REQUIRES_MODE_SELECTION', False)
    
    def compose_with_mode_selector(self, handler_name: str,
                                  schema: Dict[str, Any],
                                  config: Dict[str, Any]) -> ComposeResult:
        """Compose form with mode selector for applicable plugins.
        
        Args:
            handler_name: Plugin handler name
            schema: Plugin JSON Schema
            config: Current configuration
            
        Yields:
            Composed widgets
        """
        from gatekit.tui.utils.json_form_adapter import JSONFormAdapter
        
        # Check if we need mode selector
        plugin_class = self._get_plugin_class()
        
        if self.should_use_mode_selector(handler_name, plugin_class):
            # Add mode selector
            tools = config.get("tools", [])
            self.mode_selector = ToolManagerModeSelector(tools)
            yield from self.mode_selector.compose()
            
            # Separator
            yield Static("", classes="separator")
        
        # Regular form generation
        self.form_adapter = JSONFormAdapter(schema, config)
        yield from self.form_adapter.generate_form()
        
        # Action buttons
        with Horizontal(classes="modal-buttons"):
            yield Button("Save", id="save", variant="primary")
            yield Button("Cancel", id="cancel")
    
    def on_tool_manager_mode_selector_mode_changed(self, 
                                                  event: ToolManagerModeSelector.ModeChanged):
        """Handle mode change event.
        
        Args:
            event: Mode change event
        """
        # When mode changes, we might want to update the array editor
        # to show the new constraints
        new_mode = event.mode
        
        # Update any existing tools to match the new mode
        if hasattr(self, 'form_adapter') and hasattr(self, 'mode_selector'):
            # Get current tools from form
            form_data = self.form_adapter.get_form_data()
            tools = form_data.get("tools", [])
            
            # Fix tools for new mode
            fixed_tools = self.mode_selector.fix_tools_for_mode(tools)
            
            # Update the array editor if it exists
            for name, editor in self.form_adapter.array_editors.items():
                if name == "tools":
                    editor.items = fixed_tools
                    editor._rebuild_table()
    
    def validate_with_mode(self, form_data: Dict[str, Any]) -> List[str]:
        """Validate form data including mode constraints.
        
        Args:
            form_data: Form data to validate
            
        Returns:
            List of error messages
        """
        errors = []
        
        # Check if we have mode selector
        if hasattr(self, 'mode_selector'):
            tools = form_data.get("tools", [])
            mode_errors = self.mode_selector.validate_tools(tools)
            errors.extend(mode_errors)
        
        return errors
    
    def process_save_with_mode(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process form data before save, applying mode constraints.
        
        Args:
            form_data: Form data to process
            
        Returns:
            Processed form data
        """
        # Apply mode fixes if needed
        if hasattr(self, 'mode_selector'):
            tools = form_data.get("tools", [])
            
            # Validate first
            errors = self.mode_selector.validate_tools(tools)
            
            if errors:
                # Auto-fix if there are mode mismatches
                fixed_tools = self.mode_selector.fix_tools_for_mode(tools)
                form_data["tools"] = fixed_tools
                
                # Notify user that we fixed the tools
                self.notify(
                    "Tool actions have been updated to match the selected mode",
                    severity="information"
                )
        
        return form_data
```

### Step 3: Mark Tool Manager Plugin
**File:** `/Users/dbright/mcp/gatekit/gatekit/plugins/middleware/tool_manager.py` (addition)

```python
# Add this class attribute to ToolManagerPlugin
class ToolManagerPlugin(MiddlewarePlugin):
    """Tool manager plugin with allowlist/blocklist support."""
    
    DISPLAY_NAME = "Tool Manager"
    DISPLAY_SCOPE = "server_aware"
    REQUIRES_MODE_SELECTION = True  # This triggers mode selector in TUI
    
    # ... rest of implementation ...
```

## Testing

### Test Mode Detection
```python
def test_mode_detection():
    """Test detection of current mode from tools."""
    from gatekit.tui.utils.tool_manager_widget import ToolManagerModeSelector
    
    # Empty tools
    selector = ToolManagerModeSelector([])
    assert selector.current_mode == "empty"
    
    # Allowlist mode
    tools = [
        {"tool": "read", "action": "allow"},
        {"tool": "write", "action": "allow"}
    ]
    selector = ToolManagerModeSelector(tools)
    assert selector.current_mode == "allowlist"
    
    # Blocklist mode
    tools = [
        {"tool": "delete", "action": "deny"},
        {"tool": "execute", "action": "deny"}
    ]
    selector = ToolManagerModeSelector(tools)
    assert selector.current_mode == "blocklist"
    
    # Mixed mode (should detect and flag)
    tools = [
        {"tool": "read", "action": "allow"},
        {"tool": "delete", "action": "deny"}
    ]
    selector = ToolManagerModeSelector(tools)
    assert selector._has_mixed_mode
    assert selector.current_mode == "undecided"  # Requires explicit choice
    assert selector._has_mixed_mode is True

def test_tool_validation():
    """Test validation of tools against mode."""
    from gatekit.tui.utils.tool_manager_widget import ToolManagerModeSelector
    
    selector = ToolManagerModeSelector()
    selector.current_mode = "allowlist"
    
    # Valid allowlist tools
    tools = [
        {"tool": "read", "action": "allow"},
        {"tool": "write", "action": "allow"}
    ]
    errors = selector.validate_tools(tools)
    assert len(errors) == 0
    
    # Invalid - wrong action for mode
    tools = [
        {"tool": "read", "action": "allow"},
        {"tool": "delete", "action": "deny"}  # Wrong!
    ]
    errors = selector.validate_tools(tools)
    assert len(errors) == 1
    assert "delete" in errors[0]
    assert "must be 'allow'" in errors[0]

def test_tool_fixing():
    """Test automatic fixing of tools for mode."""
    from gatekit.tui.utils.tool_manager_widget import ToolManagerModeSelector
    
    selector = ToolManagerModeSelector()
    selector.current_mode = "allowlist"
    
    # Mixed tools that need fixing
    tools = [
        {"tool": "read", "action": "deny"},
        {"tool": "write", "action": "allow"},
        {"tool": "delete", "action": "deny"}
    ]
    
    fixed = selector.fix_tools_for_mode(tools)
    
    # All should be "allow" now
    for tool in fixed:
        assert tool["action"] == "allow"
    
    # Original tools unchanged
    assert tools[0]["action"] == "deny"

def test_no_hardcoded_names():
    """Test that tool_manager name is not hardcoded."""
    from gatekit.tui.screens.plugin_config_modal_ext import ToolManagerConfigExtension
    
    ext = ToolManagerConfigExtension()
    
    # Mock plugin class without the attribute
    class RegularPlugin:
        pass
    
    assert not ext.should_use_mode_selector("anything", RegularPlugin)
    
    # Mock plugin class with the attribute
    class ModePlugin:
        REQUIRES_MODE_SELECTION = True
    
    assert ext.should_use_mode_selector("anything", ModePlugin)
    assert ext.should_use_mode_selector("tool_manager", ModePlugin)
    assert ext.should_use_mode_selector("other_name", ModePlugin)
```

## CSS Styling
**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/styles/tool_manager.css`

```css
/* Mode selector container */
.mode-selector {
    background: $panel;
    border: solid $border;
    padding: 1;
    margin: 1 0;
}

/* Warning message for mixed mode */
.warning-message {
    color: $warning;
    background: $warning-lighten-3;
    padding: 0.5;
    margin: 0.5 0;
    border: solid $warning;
}

/* Radio buttons in mode selector */
#tool_mode {
    margin: 1 0;
}

#tool_mode RadioButton {
    padding: 0.5;
    margin: 0.25 0;
}

#tool_mode RadioButton:hover {
    background: $primary-lighten-3;
}

#tool_mode RadioButton:checked {
    background: $primary-lighten-2;
    border-left: solid 2 $primary;
}

/* Separator between mode selector and form */
.separator {
    height: 1;
    border-bottom: solid $border-subtle;
    margin: 1 0;
}
```

## Success Criteria
- [ ] Mode selector detects current mode from tools
- [ ] Mixed mode configurations are detected and warned
- [ ] Mode selection constrains tool actions
- [ ] Validation prevents saving mismatched actions
- [ ] Auto-fix available for mode mismatches
- [ ] No hardcoded "tool_manager" strings
- [ ] Mode change updates existing tools
- [ ] Clear UI indication of selected mode
- [ ] Warning shown for dangerous configurations