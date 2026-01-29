# Config Error Messaging System - Requirements (Minimal V1)

## Overview

Implement a **minimal but effective** error messaging and recovery system for invalid configuration files in Gatekit's TUI. Focus on **low-hanging fruit** that provides maximum user value with minimal implementation effort.

Current users receive generic error messages like "Error loading configuration: [technical error]" with no guidance. This minimal system will provide clear error location, basic suggestions, and simple recovery options to **ship quickly** while solving 80% of user frustration.

## Problem Statement & Priority

**High-impact issues to solve in V1:**
- Generic error messages that don't explain what's wrong ⭐ **CRITICAL**
- No indication of where in the config file the error occurred ⭐ **CRITICAL** 
- Plugin typos with no suggestions ⭐ **HIGH IMPACT, LOW EFFORT**
- No recovery options - users completely blocked ⭐ **CRITICAL**

**Defer to V2:** Rich examples, templates, multiple recovery actions, CSS polish

## Requirements

### 1. Minimal ConfigError Class ⏱️ **30 minutes**

Create a **simple** exception class in `gatekit/config/errors.py`:

```python
from typing import List, Optional
from pathlib import Path

class ConfigError(Exception):
    """Minimal structured configuration error for user-friendly display."""
    
    def __init__(
        self,
        message: str,
        error_type: str,
        file_path: Optional[Path] = None,
        line_number: Optional[int] = None,
        field_path: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
        line_snippet: Optional[str] = None
    ):
        super().__init__(message)
        self.error_type = error_type          # 'yaml_syntax', 'missing_plugin', 'validation_error'  
        self.error_code = f"CFG_{error_type.upper()}"  # Future CLI/analytics support
        self.file_path = file_path
        self.line_number = line_number        # 1-based line numbers (editor standard)
        self.field_path = field_path          # "plugins.auditing._global[2].policy"
        self.line_snippet = line_snippet     # Actual line content for YAML errors, None otherwise
        
        # Filter out empty suggestions to prevent blank bullets
        self.suggestions = [s for s in (suggestions or []) if s][:3]  # Max 3, no empties
        
        # V1: Hardcode recovery actions - only missing_plugin can be safely ignored
        self.can_edit = True
        self.can_ignore = error_type == 'missing_plugin'  # Only plugins, not validation errors
```

**V1 Error Types (3 only):**
- `yaml_syntax`: YAML parsing errors with line number + snippet (includes empty files)
- `missing_plugin`: Plugin not found with fuzzy suggestions  
- `validation_error`: Pydantic validation with field path (cannot be safely ignored)

**Defer to V2:** path_error, permission_error, etc.

### 2. YAML Syntax Errors with Line + Snippet ⏱️ **45 minutes**

**Simple implementation in `ConfigLoader.load_from_file()`:**

```python
def load_from_file(self, path: Path) -> ProxyConfig:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if not content:
            # Empty file is a YAML parsing issue, not validation
            raise ConfigError(
                message="Configuration file is empty",
                error_type="yaml_syntax",
                file_path=path,
                suggestions=["Add basic config structure", "Check file was saved properly"]
            )
        
        config_dict = yaml.safe_load(content)
        # ... existing validation logic ...
        
    except yaml.YAMLError as e:
        # Extract line number if available (1-based for editors)
        line_num = getattr(e, 'problem_mark', None)
        line_number = line_num.line + 1 if line_num else None
        
        # Get the actual line content with secret redaction
        line_snippet = self._get_line_snippet_safe(path, line_number) if line_number else None
        
        # Generate 1-3 heuristic suggestions
        suggestions = self._get_yaml_suggestions(str(e))
        
        raise ConfigError(
            message=f"YAML syntax error: {getattr(e, 'problem', str(e))}",
            error_type="yaml_syntax", 
            file_path=path,
            line_number=line_number,
            line_snippet=line_snippet,
            suggestions=suggestions
        )

def _get_line_snippet_safe(self, file_path: Path, line_num: int) -> str:
    """Get the problematic line, trimmed and with secrets redacted."""
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            if 0 < line_num <= len(lines):
                line = lines[line_num - 1].rstrip()
                
                # Redact simple secrets for security
                import re
                line = re.sub(
                    r'(password|token|key|secret|api_key)\s*:\s*[^\s]+', 
                    r'\1: ****', 
                    line, 
                    flags=re.IGNORECASE
                )
                
                return line[:80] + "..." if len(line) > 80 else line
    except:
        pass
    return ""

def _get_yaml_suggestions(self, error_msg: str) -> List[str]:
    """Generate 1-3 simple suggestions based on error."""
    suggestions = []
    error_lower = error_msg.lower()
    
    if "expected <block end>" in error_lower:
        suggestions.append("Check indentation - use consistent spaces")
    elif "found character '\\t'" in error_lower:
        suggestions.append("Replace tabs with spaces")
    elif "could not find expected ':'" in error_lower:
        suggestions.append("Add ':' after field names")
    else:
        suggestions.append("Check YAML syntax")
    
    return suggestions[:3]  # Max 3
```
### 3. Missing Plugin with Fuzzy Suggestions ⏱️ **20 minutes** 

**HIGH IMPACT, LOW EFFORT - Add to `ConfigLoader._get_plugin_class()`:**

```python
def _get_plugin_class(self, category: str, policy_name: str):
    """Get plugin class with fuzzy suggestion on failure."""
    # ... existing cache logic ...
    
    try:
        if category not in self._plugin_policy_cache:
            from gatekit.plugins.manager import PluginManager
            temp_manager = PluginManager({}, None)
            available_policies = temp_manager._discover_policies(category)
            self._plugin_policy_cache[category] = available_policies
        
        plugin_class = self._plugin_policy_cache[category].get(policy_name)
        if not plugin_class:
            # Generate fuzzy suggestions (2 lines!)
            from difflib import get_close_matches
            available = list(self._plugin_policy_cache[category].keys())
            similar = get_close_matches(policy_name, available, n=2, cutoff=0.6)
            
            suggestions = []
            if similar:
                suggestions.append(f"Did you mean '{similar[0]}'?")
            
            # Cap available list to prevent overwhelming line length (max 8 plugins)
            available_sorted = sorted(available)
            if len(available_sorted) <= 8:
                suggestions.append(f"Available {category}: {', '.join(available_sorted)}")
            else:
                suggestions.append(f"Available {category}: {', '.join(available_sorted[:8])}, ...")
            
            raise ConfigError(
                message=f"Plugin '{policy_name}' not found",
                error_type="missing_plugin",
                field_path=f"plugins.{category}.{policy_name}",
                suggestions=suggestions
            )
        
        return plugin_class
        
    except ConfigError:
        raise  # Re-raise our ConfigError
    except Exception:
        # Cache negative result and return None (existing behavior)
        if category not in self._plugin_policy_cache:
            self._plugin_policy_cache[category] = {}
        self._plugin_policy_cache[category][policy_name] = None
        return None
```

### 4. First Pydantic Validation Error ⏱️ **30 minutes**

**Simple wrapper in `ConfigLoader.load_from_dict()`:**

```python  
def load_from_dict(self, config_dict: Dict[str, Any], config_directory: Optional[Path] = None) -> ProxyConfig:
    # ... existing validation logic ...
    
    try:
        config = ProxyConfig(**config_dict)
        # ... rest of existing logic ...
    except ValidationError as e:
        # Only handle the FIRST error to keep simple
        first_error = e.errors()[0]
        field_path = '.'.join(str(loc) for loc in first_error['loc'])
        
        suggestions = []
        error_type = first_error['type']
        
        # Use startswith for robust Pydantic error matching (handles type_error.str, etc.)
        if error_type.startswith('missing'):
            suggestions.append(f"Add required field: {field_path}")
        elif error_type.startswith('type_error'):
            expected = first_error.get('ctx', {}).get('expected_type', 'correct type')
            suggestions.append(f"Change to {expected}")
            if 'int' in str(expected):
                suggestions.append("Remove quotes around numbers")
        elif error_type.startswith('value_error'):
            suggestions.append("Check field value is valid")
        else:
            suggestions.append("Check field value and type")
        
        raise ConfigError(
            message=first_error['msg'],
            error_type="validation_error", 
            field_path=field_path,
            suggestions=suggestions
        )
```

### 5. Minimal TUI Modal ⏱️ **60 minutes**

**Basic modal without CSS polish - `gatekit/tui/screens/config_error_modal.py`:**

```python
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal  
from textual.widgets import Button, Static
from textual.screen import ModalScreen

class ConfigErrorModal(ModalScreen[str]):
    """Minimal modal for config errors with basic recovery."""
    
    def __init__(self, config_error):
        super().__init__()
        self.config_error = config_error
        
    def compose(self) -> ComposeResult:
        with Container():
            yield Static("❌ Configuration Error")
            
            # Location info (if available)
            if self.config_error.file_path:
                location = f"📍 {self.config_error.file_path.name}"
                if self.config_error.line_number:
                    location += f", line {self.config_error.line_number}"
                if self.config_error.field_path:
                    location += f" ({self.config_error.field_path})"
                yield Static(location)
            
            # Problem
            yield Static(f"Problem: {self.config_error.message}")
            
            # Line snippet for YAML errors (proper field, no hasattr needed)
            if (self.config_error.error_type == "yaml_syntax" and 
                self.config_error.line_snippet):
                yield Static(f"Line: {self.config_error.line_snippet}")
            
            # Suggestions (max 3)
            if self.config_error.suggestions:
                yield Static("Suggestions:")
                for suggestion in self.config_error.suggestions:
                    yield Static(f"• {suggestion}")
            
            # Buttons - hardcoded for V1
            with Horizontal():
                if self.config_error.can_edit:
                    yield Button("Edit Config", id="edit")
                if self.config_error.can_ignore:
                    yield Button("Ignore", id="ignore") 
                yield Button("Close", id="close")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        self.dismiss(event.button.id)
```

**Integration - Replace exception handling in TUI screens:**

```python
# In config_selector.py and app.py - replace generic exception handling:

try:
    loader = ConfigLoader()
    config = loader.load_from_file(selected_path)
    # ... success path ...
    
except ConfigError as e:
    # Show our modal instead of bell/fallback
    self.app.push_screen(ConfigErrorModal(e), self._handle_error_action)
    
except Exception as e:
    # Wrap any other errors
    wrapped_error = ConfigError(
        message=str(e),
        error_type="unknown_error", 
        file_path=selected_path,
        suggestions=["Check file permissions", "Verify syntax"]
    )
    self.app.push_screen(ConfigErrorModal(wrapped_error), self._handle_error_action)

def _handle_error_action(self, action: str) -> None:
    """Handle user's choice from modal."""  
    if action == "edit":
        self._open_file_in_editor()
    elif action == "ignore":
        self._try_load_with_fallbacks()
    # "close" - do nothing, user stays in current screen
```

### 6. Simple Edit Action ⏱️ **20 minutes**

```python
def _open_file_in_editor(self) -> None:
    """Try to open config in editor."""
    import subprocess
    import os
    
    file_path = str(self.selected_file)  # or wherever config path is stored
    
    # Try $EDITOR, then VS Code, then fallback
    editor = os.environ.get('EDITOR')
    if editor:
        try:
            subprocess.run([editor, file_path])
            self.app.notify(f"Opened in {editor}")
            return
        except:
            pass
    
    # Try VS Code with line jumping
    try:
        line_arg = f"{file_path}:{getattr(self.error, 'line_number', 1)}"
        subprocess.run(["code", "-g", line_arg])
        self.app.notify("Opened in VS Code")
        return
    except:
        pass
    
    # Fallback - just tell user
    message = f"Please edit: {file_path}"
    if hasattr(self.error, 'line_number') and self.error.line_number:
        message += f" (line {self.error.line_number})"
    self.app.notify(message)
```

### 7. Safe Ignore with Skip Logic ⏱️ **40 minutes**

```python  
def _try_load_with_fallbacks(self) -> None:
    """Load config, skipping problematic parts when safe to do so."""
    if self.error.error_type == "missing_plugin":
        # Only missing plugins can be safely ignored - validation errors could break system
        try:
            # Modify config dict to disable the problematic plugin
            modified_config = self._disable_plugin_entry(self.config_dict, self.error.field_path)
            config = ConfigLoader().load_from_dict(modified_config)
            
            plugin_name = self.error.field_path.split('.')[-1]
            self.app.notify(f"⚠️ Loaded config with 1 skipped plugin: {plugin_name}")
            
            # Proceed with modified config
            self._open_config_editor(config)
            
        except Exception as e:
            self.app.notify(f"Cannot recover: {e}", severity="error")
    else:
        # For validation errors, YAML syntax errors - cannot safely ignore
        self.app.notify("This error type cannot be safely ignored", severity="error")

def _disable_plugin_entry(self, config_dict: dict, field_path: str) -> dict:
    """Remove or disable problematic plugin entry from config."""
    # Simple implementation - just set enabled: false for the plugin
    # More sophisticated version could remove the entry entirely
    # This is a minimal approach for V1
    pass  # Implementation details depend on config structure
```
## Implementation Order (Total ~4 hours)

**Phase 1: Foundation (50 mins)**
1. ✅ ConfigError class (30 mins) 
2. ✅ Plugin fuzzy suggestions (20 mins) - **Highest impact**

**Phase 2: Error Capture (75 mins)**  
3. ✅ YAML syntax with line numbers (45 mins)
4. ✅ Pydantic validation wrapper (30 mins)

**Phase 3: TUI Integration (80 mins)**
5. ✅ Basic error modal (60 mins)
6. ✅ Edit action helper (20 mins) 

**Phase 4: Recovery (60 mins)**
7. ✅ Safe ignore logic (40 mins)
8. Test integration (20 mins)

## Success Metrics

**Before:** "Error loading configuration: Policy 'syslog_audit' not found. Available policies: csv_auditing, json_auditing, line_auditing, otel_auditing"

**After:** 
```
❌ Configuration Error
📍 gatekit.yaml, line 124 (plugins.auditing.syslog_auditing)
Problem: Plugin 'syslog_auditing' not found
Suggestions:
• Did you mean 'json_auditing'?  
• Available auditing: csv_auditing, json_auditing, line_auditing, otel_auditing

[Edit Config] [Ignore] [Close]
```
## Testing (Minimal V1)

**Quick validation with 3 test configs:**
```yaml  
# bad_plugin.yaml - Test fuzzy suggestions
plugins:
  auditing:
    _global:
      - policy: "syslog_audit"  # Typo, should suggest syslog_auditing or json_auditing

# bad_yaml.yaml - Test line numbers  
proxy:
  transport: stdio
  upstreams:
    - name: test
      command: echo hello
    bad_indent: value  # Wrong indentation

# bad_value.yaml - Test validation  
proxy:
  transport: stdio
  upstreams:
    - name: test
      command: ["array", "not", "string"]  # Wrong type
```

**Test that:**
1. Each error shows in modal with location + suggestions
2. Edit button works (opens editor or shows path)
3. Ignore button only appears for plugin errors (not validation/YAML)
4. Close button returns to config selector
5. Secrets are redacted in line snippets (test with `password: secret123`)
6. Available plugins list capped at 8 items (test with many plugins)

## Acceptance Criteria (V1)

✅ **Plugin typos show "Did you mean?" suggestions**
✅ **YAML errors show line number and snippet**  
✅ **Modal appears instead of generic failure**
✅ **Edit action attempts to open file in editor**
✅ **Users can ignore missing plugins to continue**

## Deferred to V2

❌ Template generation
❌ Rich CSS styling  
❌ Multiple recovery actions
❌ Help integration
❌ Complex error recovery
❌ Real-time validation