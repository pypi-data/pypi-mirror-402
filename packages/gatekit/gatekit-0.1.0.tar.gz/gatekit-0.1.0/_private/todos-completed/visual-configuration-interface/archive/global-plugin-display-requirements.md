# Global Plugin Display Requirements

**PHASE 1: DISPLAY ONLY** - This implementation focuses on displaying plugin data accurately. Checkboxes and buttons are visual elements only. Configuration updates and interactions will be implemented in Phase 2.

**Document Purpose**: Detailed implementation requirements for the Global Security and Global Auditing plugin display widgets that appear at the top of the main TUI screen.

**Target Audience**: Implementation model that needs step-by-step guidance.

**Prerequisites**: Must read `tui-data-layer-integration.md` before implementation.

## 1. Overview

### What We're Building
Two side-by-side widgets that display plugin information at the top of the main TUI screen:
- **Left Widget**: "GLOBAL SECURITY" - Shows security plugins with `DISPLAY_SCOPE = "global"`
- **Right Widget**: "GLOBAL AUDITING" - Shows all auditing plugins (no scope filtering)

### Visual Layout (from mockups)
```
┌─ GLOBAL SECURITY ──────────────────────────────────────────────────────┐ ┌─ GLOBAL AUDITING ──────────────────────────────────────────────────────┐
│ [☑] PII Filter      Redacting: Email, Phone, SSN                     [Configure] │ │ [☑] JSON Logger     logs/audit.json (2.3MB today)                    [View Logs] │
│ [☑] Secrets Filter  Blocking: API Keys, Tokens, Passwords            [Configure] │ │ [☐] CSV Export      Export audit logs to CSV format                 [Setup]     │
│ [☐] Prompt Defense  Click to enable injection protection             [Setup]     │ │ [☐] Syslog Forward  Send logs to remote syslog server               [Setup]     │ 
│ [☐] Rate Limiter    Control request frequency and concurrent limits  [Setup]     │ │ [☐] Webhook Logger  Send events to HTTP endpoints for monitoring     [Setup]     │
└─────────────────────────────────────────────────────────────────────────┘ └─────────────────────────────────────────────────────────────────────────┘
```

### Key Features (Phase 1: Display Only)
1. **Dynamic Plugin Discovery** - Shows all available plugins, not just configured ones
2. **Real-time Status Updates** - Status descriptions reflect current configuration
3. **Visual Controls** - Checkboxes and buttons displayed but not yet functional
4. **Configuration-driven Display** - All information comes from loaded YAML config
5. **Error Resilience** - Handles missing plugins, invalid configs, and method failures

## 2. Visual Design Requirements

### Widget Structure
Each widget contains:
1. **Border with Title** - "GLOBAL SECURITY" / "GLOBAL AUDITING"
2. **Plugin List** - Vertical list of plugin items
3. **Scrollable Area** - If plugin list exceeds widget height

### Plugin Item Layout
Each plugin displays in this exact format:
```
[checkbox] Plugin Name    Status Description                                    [Action Button]
```

**Layout Details**:
- **Checkbox**: `☑` (enabled) or `☐` (disabled) - 1 character + 1 space
- **Plugin Name**: Left-aligned, fixed width (15 characters), truncated with "..." if longer
- **Status Description**: Left-aligned, flexible width, truncated if too long
- **Action Button**: Right-aligned, fixed width (10 characters), in brackets

### Visual Indicators
- **☑** - Plugin enabled and configured
- **☐** - Plugin disabled or not configured
- **Configure** - Plugin enabled, has configuration options
- **Setup** - Plugin disabled, needs initial setup
- **View Logs** - Auditing plugin with accessible log files
- **Test** - Plugin supports testing functionality

### Color Scheme (CSS Classes)
```css
.plugin-enabled { color: $success; }      /* Green for enabled plugins */
.plugin-disabled { color: $text-muted; }  /* Gray for disabled plugins */
.plugin-error { color: $error; }          /* Red for error states */
.action-button { color: $accent; }        /* Blue for action buttons */
```

## 3. Widget Architecture

### Required Textual Components
```python
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Checkbox, Button
from textual.reactive import reactive
```

### Widget Class Structure
Create two main widget classes:

```python
class GlobalSecurityWidget(Container):
    """Global security plugins widget."""
    
    # Reactive properties for data updates
    plugins_data: reactive[List[Dict]] = reactive([], always_update=True)
    current_config_path: reactive[str] = reactive("")
    
    def compose(self) -> ComposeResult:
        # Widget composition (detailed below)
        pass
    
    async def update_plugins_data(self, config_path: Path) -> None:
        # Data loading and processing (detailed below)
        pass

class GlobalAuditingWidget(Container):
    """Global auditing plugins widget."""
    
    # Same structure as GlobalSecurityWidget
    pass
```

### Container Hierarchy
```
GlobalSecurityWidget (Container)
├── Static (Title: "GLOBAL SECURITY")
└── Vertical (Scrollable plugin list)
    ├── PluginItem (Container)
    │   ├── Horizontal
    │   │   ├── Checkbox
    │   │   ├── Static (Plugin name)
    │   │   ├── Static (Status description)
    │   │   └── Button (Action button)
    ├── PluginItem (Container)
    └── ... (more plugin items)
```

### Individual Plugin Item Widget
```python
class GlobalPluginItem(Container):
    """Individual plugin item in global widgets."""
    
    def __init__(self, plugin_data: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.plugin_data = plugin_data
    
    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Checkbox(
                self.plugin_data["enabled"],
                id=f"checkbox_{self.plugin_data['policy']}"
            )
            yield Static(
                self.plugin_data["name"][:15],  # Truncate to 15 chars
                classes="plugin-name"
            )
            yield Static(
                self.plugin_data["status"],
                classes="plugin-status",
                expand=True  # Take remaining space
            )
            yield Button(
                f"[{self.plugin_data['action']}]",
                classes="action-button",
                id=f"action_{self.plugin_data['policy']}"
            )
```

## 4. Data Flow Requirements

### Step 1: Configuration Loading
```python
async def load_configuration(self, config_path: Path) -> Optional[ProxyConfig]:
    """Load configuration from file."""
    try:
        from gatekit.config.loader import ConfigLoader
        loader = ConfigLoader()
        return loader.load_from_file(config_path)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return None
```

### Step 2: Plugin Discovery
```python
async def discover_plugins(self, category: str) -> Dict[str, type]:
    """Discover available plugins."""
    try:
        from gatekit.plugins.manager import PluginManager
        manager = PluginManager({})  # Empty config for discovery
        return manager._discover_policies(category)
    except Exception as e:
        logger.error(f"Failed to discover {category} plugins: {e}")
        return {}
```

### Step 3: Plugin Filtering
```python
def filter_global_security_plugins(self, all_plugins: Dict[str, type]) -> Dict[str, type]:
    """Filter security plugins that can appear in global section."""
    global_plugins = {}
    for policy_name, plugin_class in all_plugins.items():
        # Check DISPLAY_SCOPE attribute
        display_scope = getattr(plugin_class, 'DISPLAY_SCOPE', 'global')
        if display_scope == 'global':
            global_plugins[policy_name] = plugin_class
    return global_plugins

def filter_auditing_plugins(self, all_plugins: Dict[str, type]) -> Dict[str, type]:
    """All auditing plugins can appear in global section."""
    return all_plugins  # No filtering needed
```

### Step 4: Configuration Matching
```python
def get_plugin_configuration(self, plugins_config: Dict, policy_name: str) -> Optional[Dict]:
    """Get configuration for a specific plugin from _global section."""
    if not plugins_config:
        return None
    
    global_plugins = plugins_config.get("_global", [])
    for plugin_config in global_plugins:
        if plugin_config.get("policy") == policy_name:
            return plugin_config
    
    return None
```

### Step 5: Display Data Generation
```python
def generate_plugin_display_data(self, plugin_class: type, plugin_config: Optional[Dict], policy_name: str) -> Dict[str, Any]:
    """Generate display data for a plugin."""
    config_dict = plugin_config.get("config", {}) if plugin_config else {}
    
    try:
        # Get display information from plugin class
        display_name = getattr(plugin_class, 'DISPLAY_NAME', policy_name.title())
        status = plugin_class.describe_status(config_dict)
        actions = plugin_class.get_display_actions(config_dict)
        
        return {
            "policy": policy_name,
            "name": display_name,
            "status": status,
            "action": actions[0] if actions else "Configure",  # Use first action
            "enabled": plugin_config.get("enabled", True) if plugin_config else False,
            "configured": plugin_config is not None,
            "class": plugin_class
        }
    except Exception as e:
        # Fallback for plugin method failures
        return {
            "policy": policy_name,
            "name": policy_name.title(),
            "status": "Error loading plugin status",
            "action": "Configure",
            "enabled": False,
            "configured": False,
            "error": str(e),
            "class": plugin_class
        }
```

### Complete Data Flow Method
```python
async def update_plugins_data(self, config_path: Path) -> None:
    """Complete data flow to update plugin display data."""
    # Step 1: Load configuration
    config = await self.load_configuration(config_path)
    if not config:
        self.plugins_data = []
        return
    
    # Step 2: Discover plugins
    if self.__class__.__name__ == 'GlobalSecurityWidget':
        all_plugins = await self.discover_plugins("security")
        filtered_plugins = self.filter_global_security_plugins(all_plugins)
        plugins_config = config.plugins.security if config.plugins else {}
    else:  # GlobalAuditingWidget
        all_plugins = await self.discover_plugins("auditing")
        filtered_plugins = self.filter_auditing_plugins(all_plugins)
        plugins_config = config.plugins.auditing if config.plugins else {}
    
    # Step 3: Generate display data for each plugin
    plugins_data = []
    for policy_name, plugin_class in filtered_plugins.items():
        plugin_config = self.get_plugin_configuration(plugins_config, policy_name)
        display_data = self.generate_plugin_display_data(plugin_class, plugin_config, policy_name)
        plugins_data.append(display_data)
    
    # Step 4: Sort plugins (enabled first, then alphabetical)
    plugins_data.sort(key=lambda p: (not p["enabled"], p["name"]))
    
    # Step 5: Update reactive property
    self.plugins_data = plugins_data
```

## 5. Display Logic Requirements

### Plugin Status Descriptions

**For Security Plugins**:
- **Enabled plugins**: Show dynamic status from `describe_status(config)`
  - Examples: "Redacting: Email, Phone, SSN", "Blocking: API Keys, Tokens"
- **Disabled plugins**: Show encouragement text
  - Examples: "Click to enable PII protection", "Click to enable secrets detection"
- **Error states**: Show error message
  - Example: "Error loading plugin status"

**For Auditing Plugins**:
- **Enabled plugins**: Show file information when available
  - Examples: "logs/audit.json (2.3MB today)", "Logging to /var/log/gatekit.log"
- **Disabled plugins**: Show capability description
  - Examples: "Export audit logs to CSV format", "Send logs to remote syslog server"

### Action Button Logic

**Button Text Determination**:
```python
def determine_action_button_text(self, display_data: Dict[str, Any]) -> str:
    """Determine what text to show on action button."""
    if not display_data["enabled"]:
        return "Setup"
    
    # Get actions from plugin class
    actions = display_data.get("actions", ["Configure"])
    
    # Priority order for action selection
    action_priority = ["View Logs", "Configure", "Test", "Setup"]
    
    for preferred_action in action_priority:
        if preferred_action in actions:
            return preferred_action
    
    # Default fallback
    return actions[0] if actions else "Configure"
```

**Button Styling**:
```python
def get_action_button_classes(self, action_text: str) -> str:
    """Get CSS classes for action button."""
    if action_text == "Setup":
        return "action-button setup-button"
    elif action_text == "View Logs":
        return "action-button view-logs-button"
    else:
        return "action-button configure-button"
```

### Error Display Logic

**Plugin Discovery Errors**:
- If no plugins discovered: Show "No plugins available" message
- If plugin discovery fails: Show "Error discovering plugins" message

**Configuration Errors**:
- If config file doesn't exist: Show all plugins as disabled
- If config file invalid: Show error message in status
- If plugin config invalid: Show "Configuration error" in status

**Plugin Method Errors**:
- If `describe_status()` fails: Show "Error loading status"
- If `get_display_actions()` fails: Default to ["Configure"]
- If `DISPLAY_NAME` missing: Use policy name with title case

## 6. Interaction Behaviors

### Checkbox Interactions (Phase 2 - Future Implementation)

**Note**: In Phase 1, checkboxes are display-only. Users can navigate to them with keyboard but clicking them has no effect. Configuration updates will be implemented in Phase 2.

**On Checkbox Click** (Future):
```python
# Phase 2 implementation will handle checkbox state changes
# For now, checkboxes are visual indicators only
```

### Action Button Interactions (Phase 2 - Future Implementation)

**Note**: In Phase 1, action buttons are display-only. They show the appropriate text but clicking them has no effect. Button functionality will be implemented in Phase 2.

**On Action Button Click** (Future):
```python
# Phase 2 implementation will handle button clicks
# For now, buttons are visual indicators only showing what actions would be available
```

### Keyboard Navigation

**Required Key Bindings**:
```python
BINDINGS = [
    ("tab", "next_focus", "Next"),
    ("shift+tab", "previous_focus", "Previous"),
    ("enter", "activate", "Activate"),
    ("space", "toggle", "Toggle"),
]
```

**Focus Management**:
- Tab through checkboxes and action buttons in order
- Enter activates the focused button
- Space toggles the focused checkbox

## 7. Error Handling Requirements

### Configuration Loading Errors

**File Not Found**:
```python
if not config_path.exists():
    self.plugins_data = []
    self.show_error_message(f"Configuration file not found: {config_path}")
    return
```

**YAML Syntax Errors**:
```python
try:
    config = loader.load_from_file(config_path)
except ValueError as e:
    error_msg = str(e).lower()
    if "yaml" in error_msg:
        self.show_error_message("Invalid YAML syntax in configuration file")
    elif "proxy" in error_msg:
        self.show_error_message("Configuration missing required 'proxy' section")
    else:
        self.show_error_message(f"Configuration error: {e}")
    return
```

### Plugin Discovery Errors

**Plugin Directory Missing**:
```python
discovered_plugins = await self.discover_plugins(category)
if not discovered_plugins:
    logger.warning(f"No {category} plugins discovered")
    # Continue with empty plugin list - this is not an error
```

**Plugin Module Loading Errors**:
```python
# These are handled internally by PluginManager._discover_policies()
# Failed plugins are logged but don't prevent discovery of other plugins
```

### Plugin Method Errors

**describe_status() Failures**:
```python
try:
    status = plugin_class.describe_status(config_dict)
except Exception as e:
    logger.warning(f"Failed to get status for {policy_name}: {e}")
    status = "Error loading status"
```

**get_display_actions() Failures**:
```python
try:
    actions = plugin_class.get_display_actions(config_dict)
except Exception as e:
    logger.warning(f"Failed to get actions for {policy_name}: {e}")
    actions = ["Configure"]  # Fallback
```

### Configuration Save Errors (Phase 2 - Future Implementation)

**Note**: Phase 1 does not implement configuration saving. File write error handling will be added in Phase 2.

### Error Display Methods

**Error Message Display**:
```python
def show_error_message(self, message: str) -> None:
    """Show error message to user."""
    # Use Textual's notification system
    self.app.notify(message, severity="error", timeout=5.0)

def show_warning_message(self, message: str) -> None:
    """Show warning message to user."""
    self.app.notify(message, severity="warning", timeout=3.0)

def show_info_message(self, message: str) -> None:
    """Show info message to user."""
    self.app.notify(message, severity="information", timeout=2.0)
```

## 8. Implementation Checklist

### Phase 1: Basic Widget Structure
- [ ] Create `GlobalSecurityWidget` class inheriting from `Container`
- [ ] Create `GlobalAuditingWidget` class inheriting from `Container`
- [ ] Implement basic `compose()` method with title and scrollable area
- [ ] Add CSS styling for borders and layout
- [ ] Test widgets render correctly in main app

### Phase 2: Plugin Discovery
- [ ] Implement plugin discovery methods using `PluginManager._discover_policies()`
- [ ] Add filtering logic for global security plugins vs all auditing plugins
- [ ] Test discovery works with real plugin directories
- [ ] Handle discovery errors gracefully

### Phase 3: Configuration Loading
- [ ] Implement configuration loading using `ConfigLoader`
- [ ] Add configuration parsing to extract plugin configs
- [ ] Match discovered plugins with configuration data
- [ ] Test with various configuration file states (missing, invalid, valid)

### Phase 4: Display Data Generation
- [ ] Implement display data generation using plugin metadata methods
- [ ] Add error handling for failed plugin method calls
- [ ] Test display data generation with various plugin states
- [ ] Verify status descriptions update correctly

### Phase 5: Plugin Item Widgets
- [ ] Create `GlobalPluginItem` widget class
- [ ] Implement checkbox, name, status, and action button layout
- [ ] Add dynamic content updates when plugin data changes
- [ ] Test plugin items display correctly

### Phase 6: User Interactions (Future - Phase 2)
- [ ] **PHASE 2**: Implement checkbox click handling
- [ ] **PHASE 2**: Add configuration update logic for enable/disable
- [ ] **PHASE 2**: Implement action button click handling
- [ ] **PHASE 2**: Add placeholder handlers for Configure/Setup/View Logs/Test actions
- [ ] **PHASE 2**: Test interactions work correctly

### Phase 7: Error Handling
- [ ] Add comprehensive error handling for all failure scenarios
- [ ] Implement user-friendly error messages
- [ ] Test error scenarios (missing files, invalid configs, plugin failures)
- [ ] Verify graceful degradation

### Phase 8: Integration Testing
- [ ] Test widgets with real Gatekit configuration files
- [ ] Verify widgets work with different plugin combinations
- [ ] Test configuration changes persist correctly
- [ ] Validate widgets integrate properly with main TUI app

## 9. Code Templates

### Widget Base Template
```python
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Checkbox, Button
from textual.reactive import reactive
from textual.message import Message
from textual.events import Click
from textual import on

from gatekit.config.loader import ConfigLoader
from gatekit.plugins.manager import PluginManager

logger = logging.getLogger(__name__)

class GlobalSecurityWidget(Container):
    """Global security plugins widget."""
    
    DEFAULT_CSS = """
    GlobalSecurityWidget {
        height: 8;
        border: solid $primary;
        margin: 1;
    }
    
    GlobalSecurityWidget > .title {
        text-align: center;
        background: $primary;
        color: $text;
        height: 1;
    }
    
    .plugin-item {
        height: 1;
        padding: 0 1;
    }
    
    .plugin-enabled {
        color: $success;
    }
    
    .plugin-disabled {
        color: $text-muted;
    }
    
    .action-button {
        min-width: 12;
        height: 1;
        padding: 0 1;
    }
    """
    
    plugins_data: reactive[List[Dict[str, Any]]] = reactive([], always_update=True)
    current_config_path: reactive[str] = reactive("")
    
    def compose(self) -> ComposeResult:
        """Compose the widget layout."""
        yield Static("GLOBAL SECURITY", classes="title")
        with ScrollableContainer():
            with Vertical(id="plugins_container"):
                # Plugin items will be added dynamically
                pass
    
    def watch_plugins_data(self, plugins_data: List[Dict[str, Any]]) -> None:
        """React to plugins data changes."""
        self.update_plugin_display()
    
    def update_plugin_display(self) -> None:
        """Update the display of plugin items."""
        container = self.query_one("#plugins_container", Vertical)
        container.remove_children()
        
        for plugin_data in self.plugins_data:
            plugin_item = GlobalPluginItem(plugin_data)
            container.mount(plugin_item)
    
    async def update_plugins_data(self, config_path: Path) -> None:
        """Update plugins data from configuration file."""
        # Implementation from Data Flow Requirements section
        pass
    
    # Event handlers and other methods...
```

### Plugin Item Template
```python
class GlobalPluginItem(Horizontal):
    """Individual plugin item widget."""
    
    DEFAULT_CSS = """
    GlobalPluginItem {
        height: 1;
        padding: 0 1;
    }
    
    GlobalPluginItem > Checkbox {
        width: 3;
    }
    
    GlobalPluginItem > .plugin-name {
        width: 15;
    }
    
    GlobalPluginItem > .plugin-status {
        width: 1fr;
    }
    
    GlobalPluginItem > Button {
        width: 12;
    }
    """
    
    def __init__(self, plugin_data: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.plugin_data = plugin_data
    
    def compose(self) -> ComposeResult:
        """Compose the plugin item layout."""
        yield Checkbox(
            value=self.plugin_data["enabled"],
            id=f"checkbox_{self.plugin_data['policy']}"
        )
        yield Static(
            self.plugin_data["name"][:15],
            classes="plugin-name"
        )
        yield Static(
            self.plugin_data["status"],
            classes="plugin-status"
        )
        yield Button(
            f"[{self.plugin_data['action']}]",
            id=f"action_{self.plugin_data['policy']}",
            classes="action-button"
        )
```

### Configuration Helper Template (Phase 1: Load Only)
```python
class ConfigurationHelper:
    """Helper class for configuration operations."""
    
    @staticmethod
    async def load_config(config_path: Path) -> Optional[ProxyConfig]:
        """Load configuration from file with error handling."""
        try:
            loader = ConfigLoader()
            return loader.load_from_file(config_path)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            return None
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading configuration: {e}")
            return None
    
    # NOTE: Configuration saving will be implemented in Phase 2
```

## 10. Testing Requirements

### Unit Tests
Create `test_global_plugin_widgets.py` with the following test categories:

**Plugin Discovery Tests**:
```python
def test_security_plugin_discovery():
    """Test discovery of security plugins."""
    widget = GlobalSecurityWidget()
    plugins = await widget.discover_plugins("security")
    
    # Should find at least pii_filter, secrets_filter
    assert "pii_filter" in plugins
    assert callable(plugins["pii_filter"])

def test_security_plugin_filtering():
    """Test filtering for global-scope plugins."""
    widget = GlobalSecurityWidget()
    # Mock plugin classes with different DISPLAY_SCOPE values
    # Test that only 'global' scope plugins are included
```

**Configuration Loading Tests**:
```python
def test_config_loading_success():
    """Test successful configuration loading."""
    # Create test config file
    # Load configuration
    # Verify correct parsing

def test_config_loading_file_not_found():
    """Test handling of missing config file."""
    # Test with non-existent path
    # Verify graceful handling

def test_config_loading_invalid_yaml():
    """Test handling of invalid YAML syntax."""
    # Create config with syntax error
    # Verify error handling
```

**Display Data Generation Tests**:
```python
def test_display_data_generation_enabled_plugin():
    """Test display data for enabled plugin."""
    # Mock plugin class with describe_status, get_display_actions
    # Test data generation with valid config

def test_display_data_generation_disabled_plugin():
    """Test display data for disabled plugin."""
    # Test with plugin_config = None
    # Verify disabled state handling

def test_display_data_generation_plugin_method_error():
    """Test handling of plugin method failures."""
    # Mock plugin class with failing describe_status
    # Verify fallback behavior
```

**Interaction Tests (Phase 2 - Future)**:
```python
# Phase 2 implementation will include:
# - Checkbox interaction tests
# - Action button functionality tests  
# - Configuration update verification
# Phase 1 focuses on display accuracy only
```

### Integration Tests
Create `test_global_widgets_integration.py`:

**Real Configuration Tests**:
```python
def test_with_real_gatekit_config():
    """Test widgets with actual Gatekit configuration files."""
    # Use example configs from configs/ directory
    # Verify widgets display correctly

def test_display_refresh():
    """Test that display updates when config changes externally."""
    # Modify configuration file externally
    # Trigger widget refresh
    # Verify display reflects changes
```

### Manual Testing Checklist (Phase 1: Display Only)
- [ ] Widgets display correctly in main TUI
- [ ] Plugin discovery works with all plugin types
- [ ] Status descriptions are meaningful and accurate
- [ ] Checkboxes correctly reflect enabled/disabled state (visual only)
- [ ] Action buttons show appropriate text
- [ ] Error messages display for invalid configurations
- [ ] Widgets handle missing configuration gracefully
- [ ] Performance is acceptable with many plugins
- [ ] **PHASE 2**: Checkbox clicks update configuration
- [ ] **PHASE 2**: Action button clicks trigger handlers

## 11. Acceptance Criteria

### Visual Requirements
✅ **Layout Matches Mockups**
- Two side-by-side widgets with proper borders and titles
- Plugin items display in correct format: [checkbox] Name Status [Button]
- Visual indicators (☑/☐) display correctly
- Action buttons show context-appropriate text

✅ **Dynamic Content**
- All available plugins display, not just configured ones
- Status descriptions reflect actual configuration
- Enabled/disabled state reflects configuration
- Plugin order shows enabled first, then alphabetical

### Functional Requirements
✅ **Configuration Integration**
- Widgets load data from actual YAML configuration files
- Changes to checkboxes update configuration
- Configuration changes persist across app restarts
- Invalid configurations handled gracefully

✅ **Plugin Integration**
- Uses PluginManager for discovery
- Uses plugin display metadata methods
- Handles plugin method failures gracefully
- Respects plugin scope restrictions

✅ **User Interaction (Phase 1: Display Only)**
- Checkboxes display correct state (not yet clickable)
- Action buttons show appropriate text (not yet clickable)
- Keyboard navigation works (Tab, focus indication)
- Error messages display for display failures
- **PHASE 2**: Checkbox and button click functionality

### Technical Requirements
✅ **Error Resilience**
- Handles missing configuration files
- Handles invalid YAML syntax
- Handles missing or failing plugins
- Shows user-friendly error messages

✅ **Performance**
- Plugin discovery completes in reasonable time
- Configuration loading doesn't block UI
- Display updates are smooth and responsive
- Memory usage is reasonable

✅ **Code Quality**
- Follows established code patterns
- Includes comprehensive error handling
- Has unit and integration tests
- Documentation is complete and accurate

### Integration Requirements
✅ **TUI Integration**
- Widgets integrate properly with main TUI app
- Don't interfere with other TUI components
- Follow TUI-wide styling and behavior patterns
- Support TUI keyboard navigation

✅ **Backend Integration (Phase 1: Read-Only)**
- Uses existing ConfigLoader correctly (read-only)
- Uses existing PluginManager correctly
- Respects plugin equality principle
- Follows patterns from tui-data-layer-integration.md
- **PHASE 2**: Configuration write operations

## Final Implementation Notes (Phase 1: Display Only)

1. **Start Simple**: Implement basic widget structure and display first
2. **Phase 1 Focus**: Discovery → config loading → display only
3. **Test Early**: Write tests for display accuracy as you implement
4. **Error Handling**: Add comprehensive error handling for display scenarios
5. **Performance**: Profile if plugin discovery/loading becomes slow
6. **Phase 2 Preparation**: Design with interactions in mind but don't implement them yet

This requirements document provides everything needed to implement the display-only global plugin widgets successfully. Phase 2 will add interactions and configuration updates. Follow the implementation checklist and refer back to specific sections as needed during development.