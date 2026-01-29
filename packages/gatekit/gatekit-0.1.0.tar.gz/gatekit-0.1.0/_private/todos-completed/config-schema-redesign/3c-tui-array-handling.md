# Phase 3c: TUI Array Handling

## Overview
Implement array editing with proper support for simple arrays and object arrays using modal editing.

## Critical Design Points
1. **Object arrays use modals** - Full editing, not lossy inline
2. **Simple arrays use inline** - Direct add/remove for primitives
3. **Enum arrays use multi-select** - Better UX than repeated add/remove
4. **JSON Pointer IDs throughout** - Consistent with rest of system

## Implementation

### Step 1: Object Item Modal
**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/utils/object_item_modal.py`

```python
"""Modal for editing objects within arrays."""

from typing import Dict, Any, Optional, List
from textual.screen import ModalScreen
from textual.widgets import Button, Label
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult

class ObjectItemModal(ModalScreen):
    """Modal for editing an object within an array."""
    
    def __init__(self, item_schema: Dict[str, Any], 
                 item_data: Dict[str, Any] = None,
                 item_index: Optional[int] = None):
        """Initialize object item editor modal.
        
        Args:
            item_schema: JSON Schema for the object
            item_data: Existing object data (for editing)
            item_index: Index of item being edited (None for new)
        """
        super().__init__()
        self.item_schema = item_schema
        self.item_data = item_data or {}
        self.item_index = item_index
        self.form_adapter = None
    
    def compose(self) -> ComposeResult:
        """Compose the modal UI."""
        # Import here to avoid circular dependency
        from gatekit.tui.utils.json_form_adapter import JSONFormAdapter
        
        # Create a temporary schema wrapping the item
        wrapper_schema = {
            "type": "object",
            "properties": self.item_schema.get("properties", {}),
            "required": self.item_schema.get("required", [])
        }
        
        # Additional properties handling
        if "additionalProperties" in self.item_schema:
            wrapper_schema["additionalProperties"] = self.item_schema["additionalProperties"]
        
        self.form_adapter = JSONFormAdapter(
            wrapper_schema, 
            initial_data=self.item_data,
            json_pointer_base="/items"  # Array item context
        )
        
        with Vertical(classes="object-item-modal"):
            # Title
            title = f"Edit Item #{self.item_index + 1}" if self.item_index is not None else "Add New Item"
            yield Label(title, classes="modal-title")
            
            # Generate form from item schema
            yield from self.form_adapter.generate_form()
            
            # Action buttons
            with Horizontal(classes="modal-buttons"):
                yield Button("Save", id="save", variant="primary")
                yield Button("Cancel", id="cancel", variant="default")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "save":
            # Get form data
            item_data = self.form_adapter.get_form_data()
            
            # Quick validation
            errors = self._validate_item(item_data)
            if errors:
                error_msg = "\n".join(errors)
                self.notify(error_msg, severity="error", title="Validation Error")
                return
            
            # Return the data with index
            self.dismiss({"index": self.item_index, "data": item_data})
            
        elif event.button.id == "cancel":
            self.dismiss(None)
    
    def _validate_item(self, data: Dict[str, Any]) -> List[str]:
        """Validate item data against schema.
        
        Args:
            data: Item data to validate
            
        Returns:
            List of error messages
        """
        errors = []
        required = self.item_schema.get("required", [])
        properties = self.item_schema.get("properties", {})
        
        # Check required fields
        for field in required:
            if field not in data or data[field] is None or data[field] == "":
                errors.append(f"{field} is required")
        
        # Validate each field
        for field, value in data.items():
            if field in properties:
                field_schema = properties[field]
                
                # Pattern validation
                if "pattern" in field_schema and isinstance(value, str):
                    import re
                    if value and not re.match(field_schema["pattern"], value):
                        pattern = field_schema["pattern"]
                        errors.append(f"{field}: Does not match pattern {pattern}")
                
                # Enum validation (should already be enforced by Select widget)
                if "enum" in field_schema and value not in field_schema["enum"]:
                    allowed = ", ".join(map(str, field_schema["enum"]))
                    errors.append(f"{field}: Must be one of {allowed}")
                
                # Range validation
                if field_schema.get("type") in ["integer", "number"] and value is not None:
                    if "minimum" in field_schema and value < field_schema["minimum"]:
                        errors.append(f"{field}: Must be >= {field_schema['minimum']}")
                    if "maximum" in field_schema and value > field_schema["maximum"]:
                        errors.append(f"{field}: Must be <= {field_schema['maximum']}")
        
        # Check additionalProperties if false
        if self.item_schema.get("additionalProperties") is False:
            allowed_fields = set(properties.keys())
            extra_fields = set(data.keys()) - allowed_fields
            if extra_fields:
                errors.append(f"Unexpected fields: {', '.join(extra_fields)}")
        
        return errors
```

### Step 2: Array Editor Widget
**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/utils/array_editor.py`

```python
"""Array editor widget for JSON Schema arrays."""

from typing import Dict, Any, List, Optional
from textual.app import ComposeResult
from textual.widgets import Button, DataTable, Input, Select, Checkbox, Static, Label
from textual.containers import Container, Vertical, Horizontal
from textual.message import Message
from textual.events import Key
from gatekit.tui.utils.json_pointer import path_to_widget_id

class ArrayEditor(Container):
    """Widget for editing array values based on JSON Schema."""
    
    class ItemAdded(Message):
        """Message when an item is added."""
        def __init__(self, item: Any):
            self.item = item
            super().__init__()
    
    class ItemRemoved(Message):
        """Message when an item is removed."""
        def __init__(self, index: int):
            self.index = index
            super().__init__()
    
    class ItemEdited(Message):
        """Message when an item is edited."""
        def __init__(self, index: int, item: Any):
            self.index = index
            self.item = item
            super().__init__()
    
    def __init__(self, name: str, schema: Dict[str, Any], 
                 items: List[Any] = None,
                 json_pointer_base: str = ""):
        """Initialize array editor.
        
        Args:
            name: Field name for the array
            schema: JSON Schema for the array
            items: Initial array items
            json_pointer_base: Base JSON Pointer path for this array
        """
        widget_id = path_to_widget_id(f"{json_pointer_base}/properties/{name}")
        super().__init__(id=widget_id, classes="array-editor")
        
        self.name = name
        self.schema = schema
        self.items = items if items is not None else []
        self.item_schema = schema.get("items", {})
        self.json_pointer_base = json_pointer_base
        self.table = None
    
    def compose(self) -> ComposeResult:
        """Compose the array editor."""
        with Vertical():
            # Array title
            title = self.schema.get("title", self.name.replace("_", " ").title())
            yield Label(f"{title} ({len(self.items)} items)", classes="array-title")
            
            # Description if available
            if "description" in self.schema:
                yield Static(self.schema["description"], classes="field-description")
            
            # Different UI based on array type
            if self._is_enum_array():
                # Multi-select for enum arrays
                yield from self._compose_enum_array()
            elif self._is_simple_array():
                # Inline editing for simple types
                yield from self._compose_simple_array()
            else:
                # Table with modal editing for object arrays
                yield from self._compose_object_array()
    
    def _is_enum_array(self) -> bool:
        """Check if this is an array of enum values."""
        return "enum" in self.item_schema
    
    def _is_simple_array(self) -> bool:
        """Check if this is an array of simple types."""
        item_type = self.item_schema.get("type")
        return item_type in ["string", "number", "integer", "boolean"]
    
    def _compose_enum_array(self) -> ComposeResult:
        """Compose UI for enum array (multi-select)."""
        from textual.widgets import SelectMultiple
        
        options = [(str(v), v) for v in self.item_schema["enum"]]
        widget_id = path_to_widget_id(f"{self.json_pointer_base}/properties/{self.name}/items")
        
        yield SelectMultiple(
            options,
            selected=self.items,
            id=widget_id,
            classes="enum-array-select"
        )
    
    def _compose_simple_array(self) -> ComposeResult:
        """Compose UI for simple array (inline add/remove)."""
        # Table for existing items
        table = DataTable(
            id=f"{self.name}_table",
            show_header=True,
            cursor_type="row",
            classes="simple-array-table"
        )
        table.add_columns("Value", "Actions")
        
        # Add existing items
        for i, item in enumerate(self.items):
            table.add_row(str(item), "❌")
        
        self.table = table
        yield table
        
        # Add controls
        with Horizontal(classes="add-item-controls"):
            item_type = self.item_schema.get("type")
            widget_id = path_to_widget_id(
                f"{self.json_pointer_base}/properties/{self.name}/new_item"
            )
            
            if item_type == "boolean":
                yield Checkbox("New Value", id=widget_id)
            elif item_type in ["string", "number", "integer"]:
                placeholder = f"Enter {item_type}"
                if "pattern" in self.item_schema:
                    placeholder += f" (pattern: {self.item_schema['pattern']})"
                yield Input(placeholder=placeholder, id=widget_id)
            
            yield Button("Add", id=f"add_{self.name}", variant="primary")
    
    def _compose_object_array(self) -> ComposeResult:
        """Compose UI for object array (table with modal editing)."""
        # Determine columns from object properties
        properties = self.item_schema.get("properties", {})
        
        # Use first 4 properties as columns (plus actions)
        display_props = list(properties.keys())[:4]
        columns = [prop.replace("_", " ").title() for prop in display_props]
        columns.extend(["Edit", "Remove"])
        
        # Create table
        table = DataTable(
            id=f"{self.name}_table",
            show_header=True,
            cursor_type="row",
            classes="object-array-table"
        )
        table.add_columns(*columns)
        
        # Add existing items
        for item in self.items:
            if isinstance(item, dict):
                row_data = []
                for prop in display_props:
                    value = item.get(prop, "")
                    # Truncate long values
                    str_value = str(value)
                    if len(str_value) > 20:
                        str_value = str_value[:17] + "..."
                    row_data.append(str_value)
                row_data.extend(["✏️", "❌"])
                table.add_row(*row_data)
        
        self.table = table
        yield table
        
        # Add button
        yield Button(
            f"Add {self.name.replace('_', ' ').title()}",
            id=f"add_{self.name}",
            variant="primary",
            classes="add-object-button"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == f"add_{self.name}":
            if self._is_simple_array():
                self._add_simple_item()
            else:
                self._add_object_item()
    
    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Handle cell selection in DataTable."""
        if not self.table:
            return
        
        row = event.coordinate.row
        col = event.coordinate.column
        col_count = self.table.column_count
        
        if self._is_simple_array():
            # Simple array - last column is remove
            if col == col_count - 1:  # Remove column
                self._remove_item(row)
        else:
            # Object array - last two columns are edit/remove
            if col == col_count - 2:  # Edit column
                self._edit_object_item(row)
            elif col == col_count - 1:  # Remove column
                self._remove_item(row)
    
    def on_key(self, event: Key) -> None:
        """Handle keyboard events for accessibility."""
        if event.key in ("delete", "backspace") and self.table:
            if self.table.cursor_row is not None and self.table.cursor_row < len(self.items):
                self._remove_item(self.table.cursor_row)
                event.stop()
    
    def _add_simple_item(self):
        """Add a simple item from inline controls."""
        widget_id = path_to_widget_id(
            f"{self.json_pointer_base}/properties/{self.name}/new_item"
        )
        
        try:
            widget = self.query_one(f"#{widget_id}")
            
            if isinstance(widget, Input):
                value = widget.value.strip()
                if not value:
                    self.notify("Value is required", severity="error")
                    return
                
                # Type conversion
                item_type = self.item_schema.get("type")
                if item_type == "integer":
                    try:
                        value = int(value)
                    except ValueError:
                        self.notify("Must be an integer", severity="error")
                        return
                elif item_type == "number":
                    try:
                        value = float(value)
                    except ValueError:
                        self.notify("Must be a number", severity="error")
                        return
                
                # Pattern validation
                if "pattern" in self.item_schema and isinstance(value, str):
                    import re
                    if not re.match(self.item_schema["pattern"], value):
                        self.notify(f"Invalid format", severity="error")
                        return
                
                self.items.append(value)
                widget.value = ""  # Clear input
                
            elif isinstance(widget, Checkbox):
                self.items.append(widget.value)
            
            self._rebuild_table()
            self.post_message(self.ItemAdded(self.items[-1]))
            
        except Exception as e:
            self.notify(f"Error adding item: {e}", severity="error")
    
    def _add_object_item(self):
        """Open modal to add an object item."""
        from gatekit.tui.utils.object_item_modal import ObjectItemModal
        
        modal = ObjectItemModal(self.item_schema)
        self.app.push_screen(modal, self._handle_object_modal_result)
    
    def _edit_object_item(self, index: int):
        """Open modal to edit an object item."""
        if 0 <= index < len(self.items):
            from gatekit.tui.utils.object_item_modal import ObjectItemModal
            
            modal = ObjectItemModal(
                self.item_schema,
                self.items[index],
                index
            )
            self.app.push_screen(modal, self._handle_object_modal_result)
    
    def _handle_object_modal_result(self, result: Optional[Dict[str, Any]]):
        """Handle result from object item modal.
        
        Args:
            result: None if cancelled, or {"index": int/None, "data": dict}
        """
        if result is None:
            return  # Cancelled
        
        index = result.get("index")
        data = result.get("data")
        
        if index is None:
            # Adding new item
            self.items.append(data)
            self.post_message(self.ItemAdded(data))
        else:
            # Editing existing item
            if 0 <= index < len(self.items):
                self.items[index] = data
                self.post_message(self.ItemEdited(index, data))
        
        self._rebuild_table()
    
    def _remove_item(self, index: int):
        """Remove an item by index."""
        if 0 <= index < len(self.items):
            removed = self.items.pop(index)
            self._rebuild_table()
            self.post_message(self.ItemRemoved(index))
            self.notify(f"Item removed", severity="information")
    
    def _rebuild_table(self):
        """Rebuild the table after changes."""
        if not self.table:
            return
        
        self.table.clear()
        
        if self._is_simple_array():
            # Simple array
            for item in self.items:
                self.table.add_row(str(item), "❌")
        else:
            # Object array
            properties = self.item_schema.get("properties", {})
            display_props = list(properties.keys())[:4]
            
            for item in self.items:
                if isinstance(item, dict):
                    row_data = []
                    for prop in display_props:
                        value = item.get(prop, "")
                        str_value = str(value)
                        if len(str_value) > 20:
                            str_value = str_value[:17] + "..."
                        row_data.append(str_value)
                    row_data.extend(["✏️", "❌"])
                    self.table.add_row(*row_data)
        
        # Update title with count
        title_label = self.query_one(".array-title", Label)
        title = self.schema.get("title", self.name.replace("_", " ").title())
        title_label.update(f"{title} ({len(self.items)} items)")
    
    def get_value(self) -> List[Any]:
        """Get the current array value."""
        if self._is_enum_array():
            # Get from multi-select widget
            try:
                widget_id = path_to_widget_id(
                    f"{self.json_pointer_base}/properties/{self.name}/items"
                )
                select = self.query_one(f"#{widget_id}")
                return list(select.selected)
            except:
                return self.items
        
        return self.items
```

## Testing

### Test Array Types
```python
def test_array_type_detection():
    """Test detection of array types."""
    from gatekit.tui.utils.array_editor import ArrayEditor
    
    # Enum array
    enum_schema = {
        "type": "array",
        "items": {
            "type": "string",
            "enum": ["red", "green", "blue"]
        }
    }
    editor = ArrayEditor("colors", enum_schema)
    assert editor._is_enum_array()
    assert not editor._is_simple_array()
    
    # Simple array
    simple_schema = {
        "type": "array",
        "items": {"type": "string"}
    }
    editor = ArrayEditor("tags", simple_schema)
    assert not editor._is_enum_array()
    assert editor._is_simple_array()
    
    # Object array
    object_schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "integer"}
            }
        }
    }
    editor = ArrayEditor("items", object_schema)
    assert not editor._is_enum_array()
    assert not editor._is_simple_array()

def test_object_item_modal_validation():
    """Test object item validation in modal."""
    from gatekit.tui.utils.object_item_modal import ObjectItemModal
    
    schema = {
        "type": "object",
        "required": ["tool", "action"],
        "properties": {
            "tool": {
                "type": "string",
                "pattern": "^[a-zA-Z][a-zA-Z0-9_-]*$"
            },
            "action": {
                "type": "string",
                "enum": ["allow", "deny"]
            }
        }
    }
    
    modal = ObjectItemModal(schema)
    
    # Test invalid data
    errors = modal._validate_item({"tool": "123-invalid"})
    assert any("pattern" in e for e in errors)
    
    errors = modal._validate_item({"tool": "valid-tool"})
    assert any("required" in e.lower() for e in errors)  # Missing action
    
    # Test valid data
    errors = modal._validate_item({
        "tool": "valid-tool",
        "action": "allow"
    })
    assert len(errors) == 0

def test_array_crud_operations():
    """Test array add/edit/remove operations."""
    from gatekit.tui.utils.array_editor import ArrayEditor
    
    initial_items = [
        {"name": "item1", "value": 10},
        {"name": "item2", "value": 20}
    ]
    
    schema = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "value": {"type": "integer"}
            }
        }
    }
    
    editor = ArrayEditor("items", schema, initial_items)
    
    # Test initial state
    assert len(editor.get_value()) == 2
    
    # Simulate adding item
    editor.items.append({"name": "item3", "value": 30})
    assert len(editor.get_value()) == 3
    
    # Simulate editing item
    editor.items[0] = {"name": "edited", "value": 15}
    assert editor.get_value()[0]["name"] == "edited"
    
    # Simulate removing item
    editor.items.pop(1)
    assert len(editor.get_value()) == 2
```

## CSS Styling
**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/styles/arrays.css`

```css
/* Array editor containers */
.array-editor {
    border: solid $border;
    padding: 1;
    margin: 1 0;
}

.array-title {
    font-weight: bold;
    margin-bottom: 0.5;
}

/* Array tables */
.simple-array-table,
.object-array-table {
    margin: 1 0;
    height: auto;
    max-height: 20;
}

/* Highlight action columns on hover */
DataTable:hover .datatable--cursor-cell:last-child,
DataTable:hover .datatable--cursor-cell:nth-last-child(2) {
    background: $primary-lighten-3;
}

/* Add controls */
.add-item-controls {
    margin-top: 1;
    padding-top: 1;
    border-top: solid $border-subtle;
}

.add-object-button {
    margin-top: 1;
}

/* Multi-select for enum arrays */
.enum-array-select {
    max-height: 10;
    border: solid $border;
}

/* Object item modal */
.object-item-modal {
    padding: 2;
    max-width: 60;
    max-height: 80%;
}

.modal-title {
    font-size: 1.2em;
    font-weight: bold;
    margin-bottom: 1;
}

.modal-buttons {
    margin-top: 2;
    align: right;
}
```

## Success Criteria
- [ ] Simple arrays use inline add/remove
- [ ] Object arrays use modal for full editing
- [ ] Enum arrays use multi-select widget
- [ ] All array operations preserve data integrity
- [ ] Edit modal shows all object fields
- [ ] Validation works in modal before save
- [ ] Keyboard shortcuts (Delete) work
- [ ] Table updates properly after changes
- [ ] Item count displayed and updated