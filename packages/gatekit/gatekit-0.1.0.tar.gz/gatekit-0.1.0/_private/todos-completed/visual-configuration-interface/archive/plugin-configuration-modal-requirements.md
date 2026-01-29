# Plugin Configuration Modal Requirements

## Overview

Design and implement a generic plugin configuration modal that allows users to configure any plugin through a rich, dynamic form interface within the TUI. The modal should work universally for all plugins (built-in and user-created) without requiring hardcoded knowledge of specific plugin configurations.

**Status**: 📋 Requirements Defined

## Prerequisites

This work builds on two completed implementations:

1. **✅ centralize-plugin-options** - All plugins now have centralized constants (PII_TYPES, ACTIONS, etc.) and configuration validation
2. **✅ plugin-display-metadata** - All plugins implement display metadata (DISPLAY_NAME, describe_status(), get_display_actions())

## Problem Statement

Currently, when users click "Configure" on a plugin in the TUI, nothing happens. We need:

1. **Generic Configuration UI** - A modal that works for any plugin without hardcoding
2. **Schema-Driven Forms** - Dynamic form generation based on plugin configuration schema
3. **Rich Field Types** - Support for strings, numbers, booleans, enums, lists, and complex objects
4. **Validation & Save Flow** - Validate configuration and persist changes
5. **Fallback Support** - Handle plugins that don't expose schema

## Technical Requirements

### 1. Plugin Schema Discovery

Extend the `PluginInterface` with a new schema discovery method:

```python
@classmethod
def get_config_schema(cls) -> Dict[str, Any]:
    """Return configuration schema for this plugin.
    
    Returns a dictionary describing configuration fields:
    {
        "field_name": {
            "type": "string|number|boolean|enum|list|object",
            "label": "Human-readable label",
            "description": "Help text for the field",
            "default": <default_value>,
            "required": True/False,
            "options": [...],  # For enum types
            "min": <min_value>,  # For numbers
            "max": <max_value>,  # For numbers
            "pattern": "regex",  # For string validation
            "items": {...},    # For list item schema
            "properties": {...} # For object properties
        }
    }
    """
    return {}
```

### 2. Modal UI Architecture

Create a generic `PluginConfigModal` class that:

- Extends Textual's `ModalScreen`
- Accepts plugin class and current configuration
- Generates form fields dynamically from schema
- Handles validation and save operations
- Provides consistent UX across all plugins

### 3. Field Rendering System

Implement field widgets for each schema type:

```python
class PluginConfigModal(ModalScreen):
    def render_field(self, name: str, schema: Dict) -> Widget:
        field_type = schema.get("type", "string")
        
        match field_type:
            case "boolean":
                return Checkbox(
                    label=schema.get("label", name),
                    value=self.get_current_value(name),
                    tooltip=schema.get("description")
                )
            
            case "number":
                return Input(
                    placeholder=schema.get("label"),
                    type="number",
                    validators=[NumberRange(
                        schema.get("min"), 
                        schema.get("max")
                    )],
                    value=str(self.get_current_value(name))
                )
            
            case "enum":
                options = [(opt, opt) for opt in schema.get("options", [])]
                return Select(
                    options, 
                    value=self.get_current_value(name)
                )
            
            case "list":
                return ListEditor(
                    items=self.get_current_value(name),
                    item_schema=schema.get("items", {})
                )
            
            case "object":
                return ObjectEditor(
                    value=self.get_current_value(name),
                    properties=schema.get("properties", {})
                )
            
            case _:  # string
                return Input(
                    placeholder=schema.get("label"),
                    value=self.get_current_value(name),
                    validators=self.build_validators(schema)
                )
```

### 4. Complex Field Widgets

Create compound widgets for complex configuration:

#### List Editor Widget
```python
class ListEditor(Container):
    """Widget for editing lists of items."""
    
    def compose(self) -> ComposeResult:
        with VerticalScroll():
            for item in self.items:
                yield ListItem(item, self.item_schema)
        yield Button("Add Item", id="add-item")
```

#### Object Editor Widget
```python
class ObjectEditor(Container):
    """Widget for editing nested objects."""
    
    def compose(self) -> ComposeResult:
        for prop_name, prop_schema in self.properties.items():
            yield self.render_field(prop_name, prop_schema)
```

## Implementation Plan

### Phase 1: Core Schema System (Week 1)
1. **Extend Plugin Interface**
   - Add `get_config_schema()` method to `PluginInterface`
   - Define standard schema format and field types
   - Add validation for schema format

2. **Implement Schema for Built-in Plugins**
   - PII Filter: Action, PII types, custom patterns
   - Tool Allowlist: Mode, tools list, server targeting
   - Secrets Filter: Action, secret types, patterns
   - JSON Logger: Output file, pretty print, metadata
   - CSV Logger: Output file, delimiter, format options

### Phase 2: Modal Infrastructure (Week 2)  
1. **Create Modal Base Class**
   - `PluginConfigModal` extending `ModalScreen`
   - Schema loading and field generation logic
   - Layout and styling system

2. **Basic Field Renderers**
   - String, number, boolean field widgets
   - Validation display and error messaging
   - Field help and description tooltips

### Phase 3: Advanced Field Types (Week 3)
1. **Complex Field Widgets**
   - Enum/Select widget with option support
   - List editor with add/remove functionality
   - Object editor for nested configurations
   - File path browser integration

2. **Custom Widgets for Common Patterns**
   - PII type selector with enable/disable
   - Tool list manager with import functionality
   - Pattern editor with validation

### Phase 4: Integration & Polish (Week 4)
1. **TUI Integration**
   - Connect "Configure" button to modal display
   - Load current configuration into modal
   - Save and validation flow
   - Hot-swap configuration updates

2. **Fallback Systems**
   - JSON editor for plugins without schema
   - Error handling for malformed schemas
   - Graceful degradation strategies

## Detailed Design Specifications

### Modal Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│                Configure: PII Filter                     │ ← Plugin DISPLAY_NAME
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ─────────────── Basic Settings ─────────────           │ ← Field groups
│                                                          │
│  Enabled        [✓]                                     │ ← Boolean field
│                                                          │
│  Priority       [50_____] (0-100)                       │ ← Number field with range
│                                                          │
│  Action         [▼ Redact            ]                  │ ← Enum field
│                   • Block                               │
│                   • Redact                              │
│                   • Audit Only                          │
│                                                          │
│  ─────────────── PII Detection ──────────────           │
│                                                          │
│  [✓] Email Addresses                                    │ ← Nested object fields
│  [✓] Phone Numbers                                      │
│  [✓] Credit Card Numbers                                │
│  [ ] IP Addresses                                       │
│  [✓] SSN/National IDs                                   │
│                                                          │
│  ─────────────── Advanced Options ──────────────        │
│                                                          │
│  Scan Base64    [ ]                                     │ ← Boolean field
│                                                          │
│  Custom Patterns                        [Add Pattern]   │ ← List field
│  ┌────────────────────────────────────┐                │
│  │ Pattern: \b[A-Z]{2}\d{6}\b         │ [Remove]       │
│  │ Name: Employee ID                  │                │
│  └────────────────────────────────────┘                │
│                                                          │
│                              [Cancel]  [Save]           │ ← Action buttons
└─────────────────────────────────────────────────────────┘
```

### Example Plugin Schemas

#### PII Filter Plugin Schema
```python
@classmethod
def get_config_schema(cls) -> Dict[str, Any]:
    return {
        "enabled": {
            "type": "boolean",
            "label": "Enabled",
            "description": "Enable PII detection and filtering",
            "default": True,
            "required": True
        },
        "priority": {
            "type": "number", 
            "label": "Priority",
            "description": "Plugin execution priority (0-100, lower = higher priority)",
            "default": 50,
            "min": 0,
            "max": 100,
            "required": False
        },
        "action": {
            "type": "enum",
            "label": "Action",
            "description": "What to do when PII is detected",
            "options": cls.ACTIONS,  # Uses existing constants
            "default": "redact",
            "required": True
        },
        "pii_types": {
            "type": "object",
            "label": "PII Types",
            "description": "Configure which types of PII to detect",
            "properties": {
                pii_type: {
                    "type": "object",
                    "label": display_name,
                    "properties": {
                        "enabled": {
                            "type": "boolean",
                            "label": f"Detect {display_name}",
                            "default": False
                        },
                        "formats": {
                            "type": "list",
                            "label": "Formats",
                            "description": f"Formats to detect for {display_name}",
                            "items": {
                                "type": "enum",
                                "options": cls.PII_FORMATS.get(pii_type, [])
                            },
                            "default": ["all"] if "all" in cls.PII_FORMATS.get(pii_type, []) else []
                        }
                    }
                } for pii_type, display_name in cls.PII_TYPES.items()
            }
        },
        "custom_patterns": {
            "type": "list",
            "label": "Custom Patterns",
            "description": "Add custom regex patterns for PII detection",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "label": "Pattern Name",
                        "required": True
                    },
                    "pattern": {
                        "type": "string", 
                        "label": "Regex Pattern",
                        "pattern": r"^.+$",  # Valid regex
                        "required": True
                    },
                    "enabled": {
                        "type": "boolean",
                        "label": "Enabled",
                        "default": True
                    }
                }
            },
            "default": []
        },
        "scan_base64": {
            "type": "boolean",
            "label": "Scan Base64 Content",
            "description": "Decode and scan base64 content for PII (security risk)",
            "default": False
        }
    }
```

#### Tool Allowlist Plugin Schema
```python
@classmethod  
def get_config_schema(cls) -> Dict[str, Any]:
    return {
        "enabled": {
            "type": "boolean",
            "label": "Enabled", 
            "default": True
        },
        "mode": {
            "type": "enum",
            "label": "Mode",
            "description": "Allow or block specified tools",
            "options": ["allowlist", "blocklist"],
            "default": "allowlist",
            "required": True
        },
        "tools": {
            "type": "list",
            "label": "Tools",
            "description": "List of tool names to allow or block",
            "items": {
                "type": "string",
                "pattern": r"^[a-zA-Z_][a-zA-Z0-9_]*$"
            },
            "default": []
        }
    }
```

### Styling and UX Guidelines

#### CSS Framework
```css
PluginConfigModal {
    align: center middle;
}

#plugin-config-container {
    width: 80;
    max-width: 120;
    max-height: 90%;
    background: $panel;
    border: thick $primary;
    padding: 1 2;
}

.config-section {
    margin: 1 0;
    padding: 1;
    border: round $accent;
}

.config-section-title {
    text-style: bold;
    color: $primary;
}

.config-field {
    margin: 1 0;
}

.config-field-label {
    margin-bottom: 0;
    text-style: bold;
}

.config-field-help {
    margin-top: 0;
    color: $text-muted;
    text-style: italic;
}

.config-field-error {
    color: $error;
    text-style: bold;
}

#config-buttons {
    dock: bottom;
    height: 3;
    align: right middle;
    padding: 0 1;
}

#config-buttons Button {
    margin-left: 1;
}
```

#### Interaction Patterns
1. **Field Focus** - Tab navigation through all form fields
2. **Validation** - Real-time validation with error display
3. **Help System** - Hover tooltips for field descriptions
4. **Save Confirmation** - Validate before save, show confirmation
5. **Cancel Behavior** - Confirm if changes made, otherwise close
6. **Keyboard Shortcuts** - Ctrl+S to save, Escape to cancel

## Success Criteria

### Functional Requirements
- [ ] Modal opens when "Configure" is clicked on any plugin
- [ ] Form is generated dynamically from plugin schema
- [ ] All field types render correctly with proper validation
- [ ] Configuration saves successfully and updates plugin
- [ ] Cancel/save/validation flows work correctly

### Plugin Coverage
- [ ] All built-in security plugins have schema implemented
- [ ] All built-in auditing plugins have schema implemented
- [ ] User plugins work correctly (with and without schema)
- [ ] Edge cases handled gracefully (missing schema, invalid config)

### User Experience  
- [ ] Modal is intuitive and follows TUI design patterns
- [ ] Field validation provides helpful error messages
- [ ] Configuration changes are immediately reflected in plugin status
- [ ] Performance is acceptable for complex configurations
- [ ] Keyboard navigation works throughout the modal

### Technical Quality
- [ ] Code follows existing patterns and architecture
- [ ] All tests pass including new modal functionality
- [ ] Documentation updated for schema system
- [ ] No regression in existing plugin functionality

## Future Enhancements

### Advanced Features (Phase 2)
1. **Configuration Templates** - Save and load common configurations
2. **Bulk Configuration** - Apply settings to multiple plugins at once
3. **Configuration Validation** - Test configuration against live data
4. **Import/Export** - Share configurations between systems
5. **Configuration History** - Track and rollback configuration changes

### Plugin Ecosystem Support
1. **Schema Validation Tools** - Help plugin developers create valid schemas
2. **Schema Documentation** - Auto-generate docs from plugin schemas  
3. **Configuration Testing** - Framework for testing plugin configurations
4. **Schema Versioning** - Handle schema evolution across plugin versions

## Dependencies

### Internal Dependencies
- **Plugin Interface System** - For schema discovery method
- **TUI Framework** - For modal and form widgets  
- **Configuration System** - For loading and saving configuration
- **Plugin Manager** - For hot-swap configuration updates

### External Dependencies
- **Textual Framework** - Modal screens, form widgets, validation
- **Pydantic** - Configuration validation and serialization
- **Rich** - Text formatting and display components

## Risk Mitigation

### Technical Risks
1. **Complex Schema Handling** - Start with simple schemas, add complexity gradually
2. **Performance with Large Configs** - Implement lazy loading and virtualization
3. **Plugin Compatibility** - Maintain backward compatibility throughout
4. **Modal UI Complexity** - Use proven Textual patterns and components

### User Experience Risks  
1. **Overwhelming Interface** - Group related fields, use progressive disclosure
2. **Configuration Errors** - Provide clear validation and error messages
3. **Data Loss** - Implement auto-save and change detection
4. **Learning Curve** - Provide tooltips and contextual help

## References

- **centralize-plugin-options/requirements.md** - Plugin constants and validation foundation
- **plugin-display-metadata.md** - Display metadata implementation  
- **Textual Modal Documentation** - UI framework capabilities
- **ADR-018** - Plugin UI widget architecture decisions