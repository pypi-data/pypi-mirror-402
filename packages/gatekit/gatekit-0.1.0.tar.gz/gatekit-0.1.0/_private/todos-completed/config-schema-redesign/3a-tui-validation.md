# Phase 3a: TUI Validation Infrastructure

## Overview
Implement JSON Schema validation with inline feedback and proper error mapping using JSON Pointer-based widget IDs.

## Implementation

### Step 1: Import Centralized SchemaValidator
**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/utils/schema.py`

```python
"""TUI schema validation - imports from centralized module."""

# Import centralized JSON Schema validator from Phase 2
from gatekit.config.json_schema import SchemaValidator

# Re-export for backward compatibility during transition
__all__ = ['SchemaValidator']

# Note: The old custom validator at gatekit/plugins/schema.py is deprecated
# Any TUI-specific schema extensions can be added here
```

### Step 2: JSON Pointer Utilities and Field Registry
**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/utils/json_pointer.py`

```python
"""JSON Pointer utilities for widget ID generation and error mapping."""

from typing import Dict, Any, Set

def escape_json_pointer(path: str) -> str:
    """Escape a JSON Pointer path for use in widget IDs.
    
    Args:
        path: JSON Pointer path (e.g., "/properties/tools/items/0")
    
    Returns:
        Escaped string safe for widget IDs
    """
    # First escape ~ as ~0, then / as ~1
    return path.replace("~", "~0").replace("/", "~1")

def unescape_json_pointer(escaped: str) -> str:
    """Unescape a widget ID back to JSON Pointer path.
    
    Args:
        escaped: Escaped widget ID component
    
    Returns:
        Original JSON Pointer path
    """
    # Unescape in reverse order: ~1 as /, then ~0 as ~
    return escaped.replace("~1", "/").replace("~0", "~")

def path_to_widget_id(json_pointer: str) -> str:
    """Convert JSON Pointer path to widget ID.
    
    Args:
        json_pointer: JSON Pointer path (e.g., "/properties/enabled")
    
    Returns:
        Widget ID (e.g., "wg__~1properties~1enabled")
    """
    return f"wg__{escape_json_pointer(json_pointer)}"

def widget_id_to_path(widget_id: str) -> str:
    """Convert widget ID back to JSON Pointer path.
    
    Args:
        widget_id: Widget ID (e.g., "wg__~1properties~1enabled")
    
    Returns:
        JSON Pointer path (e.g., "/properties/enabled")
    """
    if not widget_id.startswith("wg__"):
        raise ValueError(f"Invalid widget ID format: {widget_id}")
    
    escaped = widget_id[4:]  # Remove "wg__" prefix
    return unescape_json_pointer(escaped)

def extract_required_leaf_fields(schema: Dict[str, Any], 
                                path_prefix: str = "",
                                parent_required: bool = True) -> Set[str]:
    """Extract paths to required LEAF fields only.
    
    Args:
        schema: JSON Schema object
        path_prefix: Current path prefix for recursion
        parent_required: Whether parent object is required
        
    Returns:
        Set of JSON Pointer paths to required leaf fields
    """
    required_paths = set()
    
    if schema.get("type") != "object":
        # Leaf field - add if parent is required
        if parent_required:
            required_paths.add(path_prefix)
        return required_paths
    
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    for prop_name, prop_schema in properties.items():
        field_path = f"{path_prefix}/properties/{prop_name}"
        is_required = prop_name in required
        
        if prop_schema.get("type") == "object":
            # Recurse into nested object
            nested_required = extract_required_leaf_fields(
                prop_schema, 
                field_path,
                parent_required and is_required  # Only if both parent and field required
            )
            required_paths.update(nested_required)
        elif prop_schema.get("type") == "array":
            # Arrays themselves aren't required leaves, but items might be
            items_schema = prop_schema.get("items", {})
            if items_schema.get("type") == "object":
                # Extract required fields from array item schema
                item_required = extract_required_leaf_fields(
                    items_schema,
                    f"{field_path}/items",
                    parent_required and is_required
                )
                required_paths.update(item_required)
        else:
            # Leaf field - add if required and parent chain is required
            if is_required and parent_required:
                required_paths.add(field_path)
    
    return required_paths

def get_field_schema(schema: Dict[str, Any], json_pointer: str) -> Dict[str, Any]:
    """Get schema for a field by JSON Pointer path.
    
    Args:
        schema: Root JSON Schema
        json_pointer: JSON Pointer path (e.g., "/properties/config/properties/timeout")
    
    Returns:
        Field schema or empty dict if not found
    """
    if not json_pointer or json_pointer == "/":
        return schema
    
    # Split path and traverse
    parts = json_pointer.strip("/").split("/")
    current = schema
    
    for part in parts:
        # Unescape JSON Pointer escapes
        part = part.replace("~1", "/").replace("~0", "~")
        
        if isinstance(current, dict):
            current = current.get(part, {})
        else:
            return {}
    
    return current
```

### Step 3: Field Registry
**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/utils/field_registry.py`

```python
"""Central field registry for widget-to-path mapping."""

from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class FieldInfo:
    """Information about a form field."""
    json_pointer: str      # Canonical schema path
    widget_id: str         # Generated widget ID
    widget: Any           # Widget instance
    schema: Dict[str, Any]  # Field schema
    required: bool         # Whether field is required
    parent_path: Optional[str] = None  # Parent object path if nested

class FieldRegistry:
    """Central registry mapping JSON Pointers to widgets."""
    
    def __init__(self):
        self.by_pointer: Dict[str, FieldInfo] = {}
        self.by_widget_id: Dict[str, FieldInfo] = {}
    
    def register(self, pointer: str, widget: Any, schema: Dict[str, Any], 
                 required: bool = False) -> str:
        """Register a field and return its widget ID.
        
        Args:
            pointer: Canonical JSON Pointer path
            widget: Widget instance
            schema: Field schema
            required: Whether field is required
            
        Returns:
            Generated widget ID
        """
        from gatekit.tui.utils.json_pointer import path_to_widget_id
        
        widget_id = path_to_widget_id(pointer)
        widget.id = widget_id  # Ensure widget has correct ID
        
        info = FieldInfo(
            json_pointer=pointer,
            widget_id=widget_id,
            widget=widget,
            schema=schema,
            required=required
        )
        
        self.by_pointer[pointer] = info
        self.by_widget_id[widget_id] = info
        
        return widget_id
    
    def get_by_pointer(self, pointer: str) -> Optional[FieldInfo]:
        """Get field info by JSON Pointer."""
        return self.by_pointer.get(pointer)
    
    def get_by_widget_id(self, widget_id: str) -> Optional[FieldInfo]:
        """Get field info by widget ID."""
        return self.by_widget_id.get(widget_id)
    
    def get_widget(self, pointer: str) -> Optional[Any]:
        """Get widget by JSON Pointer."""
        info = self.get_by_pointer(pointer)
        return info.widget if info else None
    
    def map_error_path(self, error_path: str) -> Optional[str]:
        """Map a validator error path to widget ID.
        
        Args:
            error_path: Path from validator (e.g., "/tools/0/action")
            
        Returns:
            Widget ID if found
        """
        # Convert instance path to schema path
        schema_path = self._instance_to_schema_path(error_path)
        info = self.get_by_pointer(schema_path)
        return info.widget_id if info else None
    
    def _instance_to_schema_path(self, instance_path: str) -> str:
        """Convert instance path to schema path.
        
        Example:
            /tools/0/action -> /properties/tools/items/properties/action
        """
        parts = instance_path.strip("/").split("/")
        schema_parts = []
        
        for i, part in enumerate(parts):
            if i == 0 or not parts[i-1].isdigit():
                # Property name - add /properties/ prefix
                schema_parts.append("properties")
                schema_parts.append(part)
            elif part.isdigit():
                # Array index - replace with /items/
                schema_parts[-1] = "items"
            # Else it's a property after array index
        
        return "/" + "/".join(schema_parts)
```

### Step 4: Schema Cache
**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/utils/schema_cache.py`

```python
"""Cached schema validator singleton."""

from typing import Optional
from gatekit.config.json_schema import SchemaValidator

_validator_instance: Optional[SchemaValidator] = None

def get_schema_validator() -> SchemaValidator:
    """Get or create the singleton schema validator.
    
    Returns:
        Cached SchemaValidator instance
    """
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = SchemaValidator()
    return _validator_instance

def clear_validator_cache():
    """Clear the cached validator (for testing or reload)."""
    global _validator_instance
    _validator_instance = None
```

### Step 5: Error Parser
**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/utils/error_parser.py`

```python
"""Parse validation errors to extract paths and map to widgets."""

import re
from typing import List, Tuple, Dict

def parse_validation_errors(errors: List[str]) -> List[Tuple[str, str]]:
    """Parse validation errors to extract paths and messages.
    
    Args:
        errors: List of error strings from validator
        
    Returns:
        List of (json_pointer, error_message) tuples
    """
    parsed = []
    
    for error in errors:
        # Expected format: "At /path/to/field: Error message"
        # Or: "field_name: Error message" 
        # Or: "Error message"
        
        # Try to extract path
        path_match = re.match(r"At ([^:]+):\s*(.+)", error)
        if path_match:
            path = path_match.group(1).strip()
            message = path_match.group(2).strip()
            parsed.append((path, message))
        else:
            # Try simple field:message format
            field_match = re.match(r"([^:]+):\s*(.+)", error)
            if field_match and "/" not in field_match.group(1):
                field = field_match.group(1).strip()
                message = field_match.group(2).strip()
                # Convert field name to path
                path = f"/properties/{field}"
                parsed.append((path, message))
            else:
                # No path found, general error
                parsed.append(("", error))
    
    return parsed

def map_errors_to_widgets(errors: List[str], 
                         registry: 'FieldRegistry') -> Dict[str, List[str]]:
    """Map validation errors to widget IDs.
    
    Args:
        errors: List of error strings
        registry: Field registry for mapping
        
    Returns:
        Dict of widget_id -> [error_messages]
    """
    widget_errors = {}
    parsed = parse_validation_errors(errors)
    
    for path, message in parsed:
        if path:
            widget_id = registry.map_error_path(path)
            if widget_id:
                if widget_id not in widget_errors:
                    widget_errors[widget_id] = []
                widget_errors[widget_id].append(message)
            else:
                # No widget found, add to general errors
                if "" not in widget_errors:
                    widget_errors[""] = []
                widget_errors[""].append(f"{path}: {message}")
        else:
            # General error
            if "" not in widget_errors:
                widget_errors[""] = []
            widget_errors[""].append(message)
    
    return widget_errors
```

### Step 6: Validation Modal Base
**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/screens/plugin_config_modal.py`

```python
from typing import Dict, Any, Optional, List
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Select, Checkbox, Static
from textual.containers import Horizontal
from gatekit.tui.utils.schema_cache import get_schema_validator
from gatekit.tui.utils.field_registry import FieldRegistry
from gatekit.tui.utils.error_parser import map_errors_to_widgets
from gatekit.tui.utils.json_pointer import (
    path_to_widget_id, 
    widget_id_to_path,
    extract_required_leaf_fields,
    get_field_schema
)

class PluginConfigModal(ModalScreen):
    """Modal for configuring a plugin with JSON Schema validation."""
    
    def __init__(self, handler_name: str, config: Dict[str, Any] = None):
        super().__init__()
        self.handler_name = handler_name
        self.config = config or {}
        self.validator = get_schema_validator()  # Truly cached singleton
        self.field_registry = FieldRegistry()  # Central field registry
        self.error_labels = {}  # Widget ID -> error label mapping
        self.plugin_class = self._get_plugin_class()
        self.schema = self.plugin_class.get_json_schema()
        self.required_fields = extract_required_leaf_fields(self.schema)
    
    def on_input_blur(self, event: Input.Blur) -> None:
        """Validate field on blur for inline feedback."""
        widget_id = event.input.id
        if not widget_id.startswith("wg__"):
            return
        
        # Use field registry to get field info
        try:
            info = self.field_registry.get_by_widget_id(widget_id)
            if info:
                self._validate_field(info.json_pointer, event.input.value)
        except ValueError:
            pass  # Not a schema-based field
    
    def on_select_blur(self, event: Select.Blur) -> None:
        """Validate select field on blur."""
        widget_id = event.select.id
        if not widget_id.startswith("wg__"):
            return
        
        try:
            info = self.field_registry.get_by_widget_id(widget_id)
            if info:
                self._validate_field(info.json_pointer, event.select.value)
        except ValueError:
            pass
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Validate checkbox on change."""
        widget_id = event.checkbox.id
        if not widget_id.startswith("wg__"):
            return
        
        try:
            info = self.field_registry.get_by_widget_id(widget_id)
            if info:
                self._validate_field(info.json_pointer, event.checkbox.value)
        except ValueError:
            pass
    
    def _validate_field(self, field_path: str, value: Any) -> bool:
        """Validate a single field and show inline error if needed.
        
        Args:
            field_path: JSON Pointer path to field
            value: Field value to validate
        
        Returns:
            True if valid, False otherwise
        """
        # Get schema for this field
        field_schema = get_field_schema(self.schema, field_path)
        if not field_schema:
            return True
        
        # Quick inline validation (subset of full validation)
        error = None
        
        # Check required
        if field_path in self.required_fields and not value:
            error = "This field is required"
        
        # Check enum FIRST (before type)
        elif "enum" in field_schema and value not in field_schema["enum"]:
            error = f"Must be one of: {', '.join(map(str, field_schema['enum']))}"
        
        # Check pattern
        elif "pattern" in field_schema and isinstance(value, str):
            import re
            if value and not re.match(field_schema["pattern"], value):
                error = f"Invalid format (pattern: {field_schema['pattern']})"
        
        # Check type
        elif field_schema.get("type") == "integer":
            try:
                if value:
                    int(value)
            except (ValueError, TypeError):
                error = "Must be an integer"
        elif field_schema.get("type") == "number":
            try:
                if value:
                    float(value)
            except (ValueError, TypeError):
                error = "Must be a number"
        
        # Check min/max
        if field_schema.get("type") in ["integer", "number"] and value:
            try:
                num_value = int(value) if field_schema.get("type") == "integer" else float(value)
                if "minimum" in field_schema and num_value < field_schema["minimum"]:
                    error = f"Must be >= {field_schema['minimum']}"
                elif "maximum" in field_schema and num_value > field_schema["maximum"]:
                    error = f"Must be <= {field_schema['maximum']}"
            except (ValueError, TypeError):
                pass  # Already handled above
        
        # Update or clear error display
        widget_id = path_to_widget_id(field_path)
        self._update_field_error(widget_id, error)
        
        return error is None
    
    def _update_field_error(self, widget_id: str, error: Optional[str]):
        """Update or clear field error display.
        
        Args:
            widget_id: Widget ID
            error: Error message or None to clear
        """
        error_label_id = f"{widget_id}_error"
        
        if error:
            # Show or update error label
            if error_label_id not in self.error_labels:
                # Create error label below field
                try:
                    widget = self.query_one(f"#{widget_id}")
                    error_label = Static(error, classes="field-error", id=error_label_id)
                    widget.parent.mount(error_label, after=widget)
                    self.error_labels[error_label_id] = error_label
                except:
                    pass  # Widget not found or mounting failed
            else:
                # Update existing error
                self.error_labels[error_label_id].update(error)
        else:
            # Clear error if exists
            if error_label_id in self.error_labels:
                self.error_labels[error_label_id].remove()
                del self.error_labels[error_label_id]
    
    def _validate_full(self, form_data: Dict[str, Any]) -> List[str]:
        """Perform full validation with JSON Schema.
        
        Args:
            form_data: Complete form data
            
        Returns:
            List of error messages
        """
        # Use centralized validator
        errors = self.validator.validate(self.handler_name, form_data)
        
        # Map errors to fields using the error parser
        widget_errors = map_errors_to_widgets(errors, self.field_registry)
        
        # Update field error displays
        for widget_id, field_errors in widget_errors.items():
            if widget_id:  # Skip general errors (empty string key)
                self._update_field_error(widget_id, field_errors[0] if field_errors else None)
        
        return errors
    
    def _save_configuration(self):
        """Save the plugin configuration with full validation."""
        # Get form data
        form_data = self._get_form_data()
        
        # Add handler field
        form_data["handler"] = self.handler_name
        
        # Full validation with JSON Schema
        errors = self._validate_full(form_data)
        if errors:
            # Show summary
            self.notify("\n".join(errors), severity="error", title="Validation Failed")
            return
        
        # Save configuration
        self._write_config(form_data)
        self.dismiss(form_data)
```

## Testing

### Test JSON Pointer Utilities
```python
def test_json_pointer_utilities():
    """Test JSON Pointer path conversions."""
    from gatekit.tui.utils.json_pointer import (
        path_to_widget_id,
        widget_id_to_path,
        escape_json_pointer,
        unescape_json_pointer
    )
    
    # Basic path
    path = "/properties/enabled"
    widget_id = path_to_widget_id(path)
    assert widget_id == "wg__~1properties~1enabled"
    assert widget_id_to_path(widget_id) == path
    
    # Path with special characters
    path = "/properties/config~/timeout"
    escaped = escape_json_pointer(path)
    assert "~0" in escaped  # ~ becomes ~0
    assert "~1" in escaped  # / becomes ~1
    assert unescape_json_pointer(escaped) == path
    
    # Nested path
    path = "/properties/tools/items/0/action"
    widget_id = path_to_widget_id(path)
    assert widget_id == "wg__~1properties~1tools~1items~10~1action"
    assert widget_id_to_path(widget_id) == path

def test_required_field_extraction():
    """Test extraction of required fields from schema."""
    from gatekit.tui.utils.json_pointer import extract_required_fields
    
    schema = {
        "type": "object",
        "required": ["name", "config"],
        "properties": {
            "name": {"type": "string"},
            "enabled": {"type": "boolean"},
            "config": {
                "type": "object",
                "required": ["timeout"],
                "properties": {
                    "timeout": {"type": "integer"},
                    "retries": {"type": "integer"}
                }
            }
        }
    }
    
    required = extract_required_fields(schema)
    assert "/properties/name" in required
    assert "/properties/config" in required
    assert "/properties/config/properties/timeout" in required
    assert "/properties/enabled" not in required  # Not required

def test_inline_validation():
    """Test inline field validation logic."""
    # Test required field
    error = validate_required_field("", True)
    assert error == "This field is required"
    
    # Test enum
    error = validate_enum_field("invalid", ["allow", "deny"])
    assert "Must be one of" in error
    
    # Test pattern
    error = validate_pattern_field("123-invalid", "^[a-zA-Z][a-zA-Z0-9_-]*$")
    assert "Invalid format" in error
    
    # Test integer
    error = validate_integer_field("not-a-number")
    assert error == "Must be an integer"
    
    # Test min/max
    error = validate_range_field(150, 0, 100)
    assert "Must be <=" in error
```

## CSS Styling
**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/styles/validation.css`

```css
/* Field error messages */
.field-error {
    color: $error;
    font-size: 0.85em;
    margin-top: 0.25;
    margin-bottom: 0.5;
}

/* Invalid field highlighting */
Input.invalid {
    border: solid $error;
}

Select.invalid {
    border: solid $error;
}

/* Required field indicator */
Label.required::after {
    content: " *";
    color: $error;
}

/* Validation summary panel */
.validation-summary {
    background: $error-lighten-3;
    border: solid $error;
    padding: 1;
    margin: 1 0;
}
```

## Success Criteria
- [ ] Centralized validator imported and cached
- [ ] JSON Pointer utilities handle all escaping correctly
- [ ] Inline validation triggers on blur
- [ ] Error messages appear below invalid fields
- [ ] Required fields validated correctly
- [ ] Enum fields validated before type
- [ ] Pattern validation works
- [ ] Min/max constraints enforced
- [ ] Full validation on save prevents invalid data