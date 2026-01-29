# Phase 3 Critical Fixes - QC Feedback Resolution

## Overview
This document addresses critical architectural issues identified in QC review that must be fixed before implementation.

## 1. JSON Pointer Consistency

### Problem
- Mixed use of JSON Pointers and underscore-based naming
- Widget IDs use `/properties/` but validators don't
- `compound_name = f"{parent_name}_{field_name}"` breaks with underscores in field names

### Solution: Canonical JSON Pointer Form

**Decision**: Use schema-relative paths WITH `/properties/` and `/items/` segments throughout.

```python
# Canonical form for all paths:
/properties/enabled                          # Top-level field
/properties/tools/items/properties/action    # Array item field  
/properties/config/properties/timeout        # Nested object field

# NOT these mixed forms:
/enabled                    # Validator style - NO
/tools/0/action            # Instance path - NO
config_timeout             # Underscore compound - NO
```

### Implementation: Field Registry

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

## 2. Validator Caching

### Problem
Code claims "cached singleton" but creates new validator per modal.

### Solution: Module-Level Singleton

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

## 3. Validation Error Mapping

### Problem
Full validation has `pass` placeholder for error parsing.

### Solution: Implement Error Parser

**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/utils/error_parser.py`

```python
"""Parse validation errors to extract paths and map to widgets."""

import re
from typing import List, Tuple, Optional

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

## 4. Required Field Extraction

### Problem
- Marks parent objects as required, not just leaves
- Doesn't handle optional parents with required children

### Solution: Proper Leaf Detection

**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/utils/json_pointer.py` (update)

```python
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
```

## 5. Tool Manager Messaging Update

### Problem
Uses "Security Mode" language but Tool Manager is for workflow curation, not primarily security.

### Solution: Update UI Text

**File:** `/Users/dbright/mcp/gatekit/gatekit/tui/utils/tool_manager_widget.py` (update)

```python
def compose(self) -> ComposeResult:
    """Compose the mode selector."""
    with Vertical():
        yield Label("Tool Configuration Mode", classes="section-title")  # NOT "Security Mode"
        
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
```

## 6. Missing Validation Hooks

### Problem
Checkboxes and array editors don't trigger validation on change.

### Solution: Add Missing Handlers

```python
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

def on_array_editor_item_added(self, event: ArrayEditor.ItemAdded) -> None:
    """Validate array after item added."""
    # Validate the entire array
    editor_id = event.sender.id
    if editor_id and editor_id.startswith("wg__"):
        info = self.field_registry.get_by_widget_id(editor_id)
        if info:
            self._validate_field(info.json_pointer, event.sender.get_value())

def on_array_editor_item_removed(self, event: ArrayEditor.ItemRemoved) -> None:
    """Validate array after item removed."""
    # Similar to item_added
    pass
```

## 7. Fix "Supports ALL Types" Claim

### Problem
Claims to support "ALL JSON Schema types" but explicitly excludes many.

### Solution: Accurate Documentation

```python
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
```

## 8. Force Explicit Mode Choice

### Problem
Mixed mode silently defaults to allowlist.

### Solution: Require User Decision

```python
def _detect_mode(self) -> str:
    """Detect current mode from existing tools."""
    if not self.tools:
        return "empty"
    
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
        return "allowlist" if "allow" in actions else "blocklist"

def compose(self) -> ComposeResult:
    """Compose the mode selector."""
    # ... existing code ...
    
    if self._has_mixed_mode:
        # Force choice - no default selection
        with RadioSet(id="tool_mode", name="mode"):
            yield RadioButton(
                "Convert to Allowlist Mode\nAll tools will use 'allow' action",
                value="allowlist",
                id="mode_allowlist"
            )
            yield RadioButton(
                "Convert to Blocklist Mode\nAll tools will use 'deny' action",
                value="blocklist",
                id="mode_blocklist"
            )
        
        # Disable save until choice made
        self.require_mode_selection = True
```

## Testing Updates

### New Test Cases Required

```python
def test_json_pointer_consistency():
    """Test that all paths use canonical form."""
    registry = FieldRegistry()
    
    # Register a nested field
    registry.register(
        "/properties/config/properties/timeout",
        MockWidget(),
        {"type": "integer"},
        required=True
    )
    
    # Should NOT use underscore names
    assert "config_timeout" not in str(registry.by_pointer)
    
    # Should map error paths correctly
    widget_id = registry.map_error_path("/config/timeout")
    assert widget_id is not None

def test_validator_caching():
    """Test that validator is truly cached."""
    from gatekit.tui.utils.schema_cache import get_schema_validator
    
    validator1 = get_schema_validator()
    validator2 = get_schema_validator()
    
    assert validator1 is validator2  # Same instance

def test_required_leaf_extraction():
    """Test that only leaves are marked required."""
    schema = {
        "type": "object",
        "required": ["config"],
        "properties": {
            "config": {
                "type": "object",
                "required": ["timeout"],
                "properties": {
                    "timeout": {"type": "integer"}
                }
            }
        }
    }
    
    required = extract_required_leaf_fields(schema)
    
    # Should only have leaf
    assert "/properties/config/properties/timeout" in required
    # Should NOT have parent object
    assert "/properties/config" not in required

def test_mixed_mode_no_default():
    """Test that mixed mode doesn't silently default."""
    tools = [
        {"tool": "read", "action": "allow"},
        {"tool": "write", "action": "deny"}
    ]
    
    selector = ToolManagerModeSelector(tools)
    assert selector.current_mode == "undecided"
    assert selector.require_mode_selection is True
```

## Migration Notes

For existing configurations:
1. Mixed tool_manager configs will require explicit mode selection on first edit
2. Empty string values preserved (not converted to null)
3. Field registry maintains backward compatible error mapping

## Priority Order for Implementation

1. **Canonical JSON Pointer form** - Everything depends on this
2. **Field Registry** - Central to error mapping
3. **Validator caching** - Performance and correctness
4. **Error parser** - Makes validation useful
5. **Required leaf fields** - UX clarity
6. **Tool Manager messaging** - User understanding
7. **Validation hooks** - Completeness
8. **Mode selection forcing** - Safety