# Phase 3b: TUI Core Form Generation

## Overview
Implement JSON Schema-driven form generation with proper widget ID generation and enum handling.

## Critical Design Points
1. **Check enum BEFORE type** - Prevents treating constrained fields as free-form
2. **Use JSON Pointer IDs everywhere** - No underscore-based IDs
3. **Required fields from parent** - Not from field itself

## Implementation

### Step 1: Base Form Adapter
**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/utils/json_form_adapter.py`

```python
"""Adapter to generate Textual forms from JSON Schema."""

from typing import Dict, Any, List, Optional, Set
from textual.app import ComposeResult
from textual.widgets import Input, Checkbox, Select, Label, Static, Button
from textual.containers import Vertical, Horizontal, Container
from gatekit.tui.utils.json_pointer import (
    path_to_widget_id,
    extract_required_leaf_fields
)
from gatekit.tui.utils.field_registry import FieldRegistry

class JSONFormAdapter:
    """Generates Textual forms from core JSON Schema types.
    
    Supported:
    - Basic types: string, number, integer, boolean
    - Structures: object, array
    - Constraints: enum, pattern, minimum/maximum, required
    - Validation: minLength/maxLength (strings), minItems/maxItems (arrays)
    
    NOT supported (will show warning):
    - Conditional: oneOf, anyOf, allOf, if/then/else
    - Advanced: $ref (beyond single level), patternProperties, dependencies
    - Format: Beyond basic pattern matching
    """
    
    def __init__(self, schema: Dict[str, Any], initial_data: Dict[str, Any] = None,
                 json_pointer_base: str = "", field_registry: FieldRegistry = None):
        """Initialize with JSON Schema.
        
        Args:
            schema: JSON Schema object
            initial_data: Initial form data
            json_pointer_base: Base path for nested forms
            field_registry: Central field registry (created if not provided)
        """
        self.schema = schema
        self.initial_data = initial_data or {}
        self.json_pointer_base = json_pointer_base
        self.field_registry = field_registry or FieldRegistry()
        self.widgets = {}  # name -> widget mapping (for backward compat)
        self.array_editors = {}  # name -> ArrayEditor mapping
        self.required_fields = extract_required_leaf_fields(schema, json_pointer_base)
    
    def can_generate_form(self) -> bool:
        """Check if we can generate a form for this schema.
        
        Returns True for any valid object schema.
        """
        return self.schema.get("type") == "object"
    
    def generate_form(self) -> ComposeResult:
        """Generate form widgets from schema."""
        if not self.can_generate_form():
            raise ValueError("Schema must be type 'object' for form generation")
        
        properties = self.schema.get("properties", {})
        required = set(self.schema.get("required", []))
        
        with Vertical():
            for prop_name, prop_schema in properties.items():
                # Skip handler field (it's implicit)
                if prop_name == "handler":
                    continue
                
                # Get initial value
                initial_value = self.initial_data.get(prop_name)
                    
                yield from self._generate_field(
                    prop_name, 
                    prop_schema, 
                    prop_name in required,
                    initial_value
                )
    
    def _generate_field(self, name: str, schema: Dict[str, Any], 
                       required: bool, initial_value: Any = None) -> ComposeResult:
        """Generate widgets for a single field - handles ALL types.
        
        CRITICAL: Check for enum BEFORE type to avoid treating enums as free-form fields.
        
        Args:
            name: Field name
            schema: Field schema
            required: Whether field is required
            initial_value: Initial value for the field
        """
        label = schema.get("title", name.replace("_", " ").title())
        description = schema.get("description", "")
        default = initial_value if initial_value is not None else schema.get("default")
        field_type = schema.get("type")
        
        # Generate canonical JSON Pointer path
        field_path = f"{self.json_pointer_base}/properties/{name}"
        
        # Label with required indicator
        required_mark = " *" if required else ""
        yield Label(f"{label}{required_mark}", classes="field-label")
        
        if description:
            yield Static(description, classes="field-description")
        
        # CRITICAL: Check enum FIRST before type
        if "enum" in schema:
            # Enum field - use Select regardless of type
            options = [(str(v), v) for v in schema["enum"]]
            
            # Find initial selection
            initial_selection = default
            if initial_selection not in schema["enum"] and schema["enum"]:
                initial_selection = schema["enum"][0]
            
            widget = Select(
                options, 
                value=initial_selection
            )
            widget_id = self.field_registry.register(
                field_path, widget, schema, required
            )
            self.widgets[name] = widget  # Backward compat
            yield widget
            
        elif field_type == "boolean":
            widget = Checkbox(
                label, 
                value=bool(default) if default is not None else False
            )
            widget_id = self.field_registry.register(
                field_path, widget, schema, required
            )
            self.widgets[name] = widget  # Backward compat
            yield widget
            
        elif field_type in ["string", "number", "integer"]:
            # Build placeholder with validation hints
            placeholder = f"Enter {label.lower()}"
            
            # Add pattern hint
            if "pattern" in schema:
                placeholder += f" (pattern: {schema['pattern']})"
            
            # Add range hints
            if "minimum" in schema and "maximum" in schema:
                placeholder += f" ({schema['minimum']}-{schema['maximum']})"
            elif "minimum" in schema:
                placeholder += f" (min: {schema['minimum']})"
            elif "maximum" in schema:
                placeholder += f" (max: {schema['maximum']})"
            
            # Add length hints for strings
            if field_type == "string":
                if "minLength" in schema and "maxLength" in schema:
                    placeholder += f" ({schema['minLength']}-{schema['maxLength']} chars)"
                elif "minLength" in schema:
                    placeholder += f" (min {schema['minLength']} chars)"
                elif "maxLength" in schema:
                    placeholder += f" (max {schema['maxLength']} chars)"
            
            widget = Input(
                value=str(default) if default is not None else "",
                placeholder=placeholder
            )
            widget_id = self.field_registry.register(
                field_path, widget, schema, required
            )
            self.widgets[name] = widget  # Backward compat
            yield widget
            
        elif field_type == "array":
            # Import ArrayEditor (defined in 3c-tui-array-handling.md)
            from gatekit.tui.utils.array_editor import ArrayEditor
            
            array_editor = ArrayEditor(
                name, 
                schema, 
                initial_value or [],
                self.json_pointer_base,
                self.field_registry  # Pass registry for array items
            )
            # Register the array editor itself
            widget_id = self.field_registry.register(
                field_path, array_editor, schema, required
            )
            self.array_editors[name] = array_editor
            yield array_editor
            
        elif field_type == "object":
            # For nested objects, create a sub-container with nested fields
            yield from self._generate_nested_object(name, schema, initial_value or {})
            
        else:
            # Fallback for any unhandled types
            yield Static(f"Unsupported type: {field_type}", classes="error")
    
    def _generate_nested_object(self, name: str, schema: Dict[str, Any], 
                                initial_value: Dict[str, Any]) -> ComposeResult:
        """Generate widgets for a nested object.
        
        Args:
            name: Object field name
            schema: Object schema
            initial_value: Initial object value
        """
        nested_path = f"{self.json_pointer_base}/properties/{name}"
        container = Container(classes="nested-object")
        
        # Register the container for the nested object
        container_id = self.field_registry.register(
            nested_path, container, schema, False
        )
        
        with container:
            yield Static(f"{name.replace('_', ' ').title()} Settings", classes="section-title")
            
            properties = schema.get("properties", {})
            required = set(schema.get("required", []))
            
            for prop_name, prop_schema in properties.items():
                # Get nested initial value
                nested_initial = initial_value.get(prop_name)
                
                # Generate field with nested path
                yield from self._generate_nested_field(
                    name,
                    prop_name,
                    prop_schema,
                    prop_name in required,
                    nested_initial,
                    nested_path
                )
    
    def _generate_nested_field(self, parent_name: str, field_name: str,
                               schema: Dict[str, Any], required: bool,
                               initial_value: Any, parent_path: str) -> ComposeResult:
        """Generate a field within a nested object.
        
        Args:
            parent_name: Parent object name
            field_name: Field name within object
            schema: Field schema
            required: Whether field is required
            initial_value: Initial value
            parent_path: Parent JSON Pointer path
        """
        # Create a temporary adapter for the nested field, sharing the registry
        nested_adapter = JSONFormAdapter(
            {"type": "object", "properties": {field_name: schema}},
            {field_name: initial_value} if initial_value is not None else {},
            parent_path,
            self.field_registry  # Share the same registry
        )
        
        # Generate just this field
        yield from nested_adapter._generate_field(
            field_name,
            schema,
            required,
            initial_value
        )
        
        # No longer using compound names - registry handles all mapping
    
    def get_form_data(self) -> Dict[str, Any]:
        """Extract data from form widgets using field registry.
        
        Returns:
            Dictionary of form data
        """
        data = {}
        
        # Build data structure from registry
        for pointer, info in self.field_registry.by_pointer.items():
            if not pointer.startswith(self.json_pointer_base):
                continue  # Skip fields from other forms
            
            # Parse the pointer to reconstruct the data structure
            value = self._get_widget_value_from_info(info)
            if value is not None:
                self._set_nested_value(data, pointer, value)
        
        # Get data from array editors (they handle their own data)
        for name, editor in self.array_editors.items():
            data[name] = editor.get_value()
        
        return data
    
    def _get_widget_value_from_info(self, info: 'FieldInfo') -> Any:
        """Get value from widget using field info."""
        widget = info.widget
        
        if isinstance(widget, Checkbox):
            return widget.value
        elif isinstance(widget, Select):
            return widget.value
        elif isinstance(widget, Input):
            value = widget.value
            field_type = info.schema.get("type")
            
            # Type conversion
            if field_type == "integer":
                try:
                    return int(value) if value else None
                except ValueError:
                    return None
            elif field_type == "number":
                try:
                    return float(value) if value else None
                except ValueError:
                    return None
            else:
                return value
        
        return None
    
    def _set_nested_value(self, data: Dict[str, Any], pointer: str, value: Any):
        """Set a value in nested dict structure based on JSON Pointer."""
        # Remove base path if present
        if self.json_pointer_base and pointer.startswith(self.json_pointer_base):
            pointer = pointer[len(self.json_pointer_base):]
        
        # Parse pointer path
        parts = pointer.strip("/").split("/")
        
        # Skip "properties" segments
        parts = [p for p in parts if p != "properties" and p != "items"]
        
        # Navigate to parent
        current = data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the value
        if parts:
            current[parts[-1]] = value
    
    def _get_widget_value(self, name: str, widget: Any) -> Any:
        """Get value from a widget with type conversion.
        
        Args:
            name: Field name
            widget: Widget instance
            
        Returns:
            Properly typed value
        """
        if isinstance(widget, Checkbox):
            return widget.value
            
        elif isinstance(widget, Select):
            return widget.value
            
        elif isinstance(widget, Input):
            value = widget.value
            
            # Get schema for type conversion
            schema = self._get_field_schema(name)
            field_type = schema.get("type")
            
            # Type conversion
            if field_type == "integer":
                try:
                    return int(value) if value else None
                except ValueError:
                    return None
            elif field_type == "number":
                try:
                    return float(value) if value else None
                except ValueError:
                    return None
            else:
                return value
        
        return None
    
    def _get_field_schema(self, name: str) -> Dict[str, Any]:
        """Get schema for a field by name.
        
        Args:
            name: Field name
            
        Returns:
            Field schema or empty dict
        """
        return self.schema.get("properties", {}).get(name, {})
```

## Testing

### Test Enum Detection Order
```python
def test_enum_detection_before_type():
    """Test that enum is checked before type."""
    schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["allow", "deny"]
            }
        }
    }
    
    adapter = JSONFormAdapter(schema)
    # Should generate Select widget, not Input
    widgets = list(adapter.generate_form())
    
    # Find the action widget
    action_widget = None
    for widget in widgets:
        if hasattr(widget, 'id') and 'action' in widget.id:
            action_widget = widget
            break
    
    assert isinstance(action_widget, Select)
    assert not isinstance(action_widget, Input)

def test_json_pointer_widget_ids():
    """Test that all widgets use JSON Pointer IDs."""
    schema = {
        "type": "object",
        "properties": {
            "enabled": {"type": "boolean"},
            "config": {
                "type": "object",
                "properties": {
                    "timeout": {"type": "integer"}
                }
            }
        }
    }
    
    adapter = JSONFormAdapter(schema)
    widgets = list(adapter.generate_form())
    
    # Check widget IDs
    for widget in widgets:
        if hasattr(widget, 'id') and widget.id:
            assert widget.id.startswith("wg__"), f"Widget ID doesn't use JSON Pointer: {widget.id}"
            # Should be escapable back to path
            from gatekit.tui.utils.json_pointer import widget_id_to_path
            try:
                path = widget_id_to_path(widget.id)
                assert path.startswith("/properties/")
            except ValueError:
                pass  # Not all widgets need JSON Pointer IDs

def test_required_field_indicators():
    """Test that required fields are properly marked."""
    schema = {
        "type": "object",
        "required": ["name", "email"],
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"},
            "age": {"type": "integer"}
        }
    }
    
    adapter = JSONFormAdapter(schema)
    widgets = list(adapter.generate_form())
    
    # Count labels with required marks
    required_labels = 0
    for widget in widgets:
        if isinstance(widget, Label) and "*" in widget.renderable:
            required_labels += 1
    
    assert required_labels == 2  # name and email

def test_type_conversion():
    """Test that values are properly converted based on schema type."""
    schema = {
        "type": "object",
        "properties": {
            "count": {"type": "integer"},
            "price": {"type": "number"},
            "name": {"type": "string"}
        }
    }
    
    adapter = JSONFormAdapter(schema)
    
    # Simulate form input
    adapter.widgets["count"] = MockInput("42")
    adapter.widgets["price"] = MockInput("19.99")
    adapter.widgets["name"] = MockInput("test")
    
    data = adapter.get_form_data()
    
    assert isinstance(data["count"], int)
    assert data["count"] == 42
    assert isinstance(data["price"], float)
    assert data["price"] == 19.99
    assert isinstance(data["name"], str)
    assert data["name"] == "test"
```

## Success Criteria
- [ ] All widgets use JSON Pointer-based IDs
- [ ] Enum fields detected before type checking
- [ ] Required fields marked with asterisk
- [ ] Initial values properly populated
- [ ] Type conversion works correctly
- [ ] Nested objects generate proper sub-forms
- [ ] Placeholder text includes validation hints
- [ ] No underscore-based widget IDs remain