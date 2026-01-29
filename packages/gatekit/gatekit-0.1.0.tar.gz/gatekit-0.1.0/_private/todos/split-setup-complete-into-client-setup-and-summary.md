# Split Setup Complete Screen into Two Screens

## Problem
The current SetupCompleteScreen is too crowded on normal-sized terminals. The master-detail layout (client instructions) only gets 5-10 lines of vertical space because:
- Screen title + description take ~3 lines
- FileLocationsSummary box takes ~5 lines
- Bottom buttons take ~3 lines
- Header/Footer take space

This makes the most important interactive part (client setup instructions) practically unusable.

## Solution
Split SetupCompleteScreen into two separate screens:
1. **ClientSetupScreen** - Dedicated to showing client setup instructions with full vertical space
2. **SetupCompleteScreen** (new) - Final summary showing what was configured and file locations

---

## New Wizard Flow
1. ServerSelectionScreen
2. ConfigLocationScreen
3. ClientSelectionScreen (generates files)
4. **ClientSetupScreen** (renamed from SetupCompleteScreen - shows client instructions)
5. **SetupCompleteScreen** (NEW - final summary)

---

## File Changes

### 1. Rename `setup_complete.py` → `client_setup.py`

**File**: `gatekit/tui/screens/guided_setup/client_setup.py` (renamed from `gatekit/tui/screens/setup_complete.py`)

**Changes to make it ClientSetupScreen:**
- Class name: `SetupCompleteScreen` → `ClientSetupScreen`
- Keep screen title: "MCP Client Setup Instructions"
- Keep description text: "Use these instructions to configure your MCP clients to use Gatekit. Select a client from the list to view setup instructions for it."
- **Remove**:
  - `FileLocationsSummary` class definition
  - `FileLocationsSummary` instantiation from `compose()` (the `yield FileLocationsSummary(...)` block)
  - Button handlers for `open_config_file` and `open_restore_folder` (only used by FileLocationsSummary)
- **Keep**:
  - `_open_in_editor()` and `_open_folder()` helper methods (still needed by `open_existing_config`, `open_editor_*`, `open_restore_*` buttons)
  - `_copy_to_clipboard()` method (still needed by copy buttons)
  - `platform` and `subprocess` imports (still needed by `_copy_to_clipboard()` and `_open_in_editor()`)
- **Change button**:
  - ID: `finish_button` → `next_button`
  - Label: "Finish" → "Next"
  - Variant: Keep as "primary"
- **Change navigation**:
  - Return `NavigationAction.CONTINUE` on Next (proceeds to new summary screen)
  - Keep BACK and CANCEL handling as-is
- **Keep**: Master-detail layout (gets full vertical space now)
- **Keep**: All client instruction logic (AlreadyConfiguredAlert, detail panel building, etc.)

**Button handler changes:**
```python
# OLD:
elif button_id == "finish_button":
    if self.state is not None:
        self.dismiss(ScreenResult(action=NavigationAction.CONTINUE, state=self.state))

# NEW:
elif button_id == "next_button":
    if self.state is not None:
        self.dismiss(ScreenResult(action=NavigationAction.CONTINUE, state=self.state))
```

### 2. Create NEW `setup_complete.py`

**File**: `gatekit/tui/screens/setup_complete.py` (NEW)

**Important**: FileLocationsSummary component will live in this new file (only this screen uses it). The old setup_complete.py will be renamed to client_setup.py, so FileLocationsSummary effectively stays in setup_complete.py but in a new implementation.

**New SetupCompleteScreen (final summary):**

**Structure:**
```python
class SetupCompleteScreen(Screen[ScreenResult]):
    """Final summary screen showing configuration results.

    Contract:
    - Requires GuidedSetupState from ClientSetupScreen
    - Returns ScreenResult with BACK/CONTINUE actions
    - BACK returns to ClientSetupScreen
    - CONTINUE (Finish button) indicates wizard completion
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        # No navigation bindings needed - simpler screen
    ]

    CSS = SHARED_WIZARD_CSS + """
    /* Any screen-specific styles if needed */
    """
```

**Layout:**
```
- Header
- Container (wizard-screen pattern):
  - Screen title: "Configuration Summary"
  - Description: "Your Gatekit configuration is ready. Review the details below."
  - Summary info box (.info-box):
    - Title: "Configuration Complete"
    - Content showing:
      - "Servers configured:" + Rich Columns of server names
      - "Clients configured:" + Rich Columns of client display names
  - FileLocationsSummary component (moved from ClientSetupScreen)
  - Bottom buttons: Back + Finish (no Cancel)
- Footer
```

**Implementation details:**

1. Import shared wizard styles from `wizard.tcss`
2. Build summary using `state.get_selected_servers()` and selected client types
3. Use Rich Columns for server/client names (pattern from ConfigLocationScreen)
4. Reuse `FileLocationsSummary` component
5. Button handlers:
   - Back: `NavigationAction.BACK`
   - Finish: `NavigationAction.CONTINUE` (wizard completion)
   - **FileLocationsSummary buttons** (uses copied helper methods):
     - `open_config_file`: Opens config file in editor (uses `_open_in_editor()` method - copied from ClientSetupScreen)
     - `open_restore_folder`: Opens restore folder (uses `_open_folder()` method - copied from ClientSetupScreen)

**Note**: The `_open_in_editor()` and `_open_folder()` helper methods are **copied** to both ClientSetupScreen and SetupCompleteScreen. ClientSetupScreen needs them for its instruction buttons (`open_existing_config`, `open_editor_*`, `open_restore_*`), while SetupCompleteScreen needs them for FileLocationsSummary buttons. This is acceptable code duplication for clean separation of concerns.

**Summary builder method:**
```python
def _build_summary_renderable(self):
    """Build summary of configuration as Rich renderable.

    Returns:
        Rich Group containing servers and clients configured
    """
    from rich.columns import Columns
    from rich.console import Group
    from rich.text import Text

    renderables = []

    # Guard for legacy flow where state might be None
    if not self.state:
        return Group(Text("Configuration complete."))

    # Servers
    selected_servers = self.state.get_selected_servers()
    if selected_servers:
        renderables.append(Text("Servers configured:"))
        server_bullets = [Text(f"  • {ds.server.name}") for ds in selected_servers]
        server_columns = Columns(
            server_bullets,
            padding=(0, 2),
            column_first=True,
            expand=False
        )
        renderables.append(server_columns)
        renderables.append(Text(""))  # Spacing

    # Clients
    selected_clients = self.state.get_selected_clients()
    if selected_clients:
        renderables.append(Text("Clients configured:"))
        client_bullets = [Text(f"  • {c.client_type.display_name()}") for c in selected_clients]
        client_columns = Columns(
            client_bullets,
            padding=(0, 2),
            column_first=True,
            expand=False
        )
        renderables.append(client_columns)

    return Group(*renderables)
```

**FileLocationsSummary component:**
Copy the entire `FileLocationsSummary` class definition from the backup file (`/tmp/file_locations_summary.py`). This component will only be used by SetupCompleteScreen.

### 3. Update `wizard_navigator.py`

**File**: `gatekit/tui/screens/guided_setup/wizard_navigator.py`

**Changes:**
```python
# Update imports
from gatekit.tui.screens.guided_setup.client_setup import ClientSetupScreen
from gatekit.tui.screens.setup_complete import SetupCompleteScreen

# Update screens list in launch() method
screens = [
    ServerSelectionScreen,
    ConfigLocationScreen,
    ClientSelectionScreen,
    ClientSetupScreen,      # NEW position
    SetupCompleteScreen,    # NEW final screen
]

# Update docstring
"""Launch wizard with automatic back navigation.

Navigation Flow:
1. ServerSelectionScreen: Select servers + detect clients
2. ConfigLocationScreen: Choose gatekit.yaml path
3. ClientSelectionScreen: Select clients, set restore location, generate files
4. ClientSetupScreen: Show interactive client setup instructions
5. SetupCompleteScreen: Final summary of configuration

All screens support BACK/CONTINUE/CANCEL actions for flexible navigation.

Returns:
    Path to created config file, or None if cancelled
"""
```

### 4. Update `guided_setup/__init__.py`

**File**: `gatekit/tui/screens/guided_setup/__init__.py`

**Changes:**
- Update module docstring to describe 5-screen flow (not 4)
- Add `ClientSetupScreen` to imports
- Add `ClientSetupScreen` to `__all__` exports (keep existing entries!)
- Update Wizard Flow documentation

```python
"""Guided setup wizard screens and navigation.

This module provides the complete guided setup wizard flow with:
- Individual screen implementations
- WizardNavigator for managing screen flow with back navigation
- launch_guided_setup entry point function

Wizard Flow:
1. ServerSelectionScreen: Select servers + detect clients
2. ConfigLocationScreen: Choose gatekit.yaml path
3. ClientSelectionScreen: Select clients, set restore location, generate files
4. ClientSetupScreen: View client setup instructions              # ADD THIS LINE
5. SetupCompleteScreen: Final configuration summary               # ADD THIS LINE (renumber from 4)
"""

# ADD THIS IMPORT
from .client_setup import ClientSetupScreen

__all__ = [
    "ServerSelectionScreen",
    "ConfigLocationScreen",
    "ClientSelectionScreen",
    "ClientSetupScreen",      # ADD THIS - keep existing WizardNavigator and launch_guided_setup!
    "WizardNavigator",
    "launch_guided_setup",
]
```

### 5. Update GuidedSetupState Docstring

**File**: `gatekit/tui/guided_setup/models.py`

**Change the Lifecycle docstring in GuidedSetupState:**
```python
"""Wizard state that flows through all screens.

Lifecycle (updated flow):
1. ServerSelectionScreen: Populates detected_clients, deduplicated_servers, user modifies selected_server_names
2. ConfigLocationScreen: User sets config_path
3. ClientSelectionScreen: User modifies selected_client_types, sets restore_dir, generate_restore,
   populates already_configured_clients; generates files and populates created_files, generation_errors, migration_instructions
4. ClientSetupScreen: Displays interactive client setup instructions using migration_instructions and already_configured_clients
5. SetupCompleteScreen: Displays final summary of configuration
"""
```

### 6. Update Tests

**Files to update:**

#### `tests/unit/test_guided_setup_setup_complete_screen.py`
- May need renaming to `test_guided_setup_client_setup_screen.py`
- Update imports: `from gatekit.tui.screens.guided_setup.client_setup import ClientSetupScreen`
- Update class instantiation
- Tests should still pass as screen logic is unchanged

#### `tests/unit/test_setup_complete_master_detail_widgets.py`
- **Split this file** into two test modules:
  - `test_client_setup_widgets.py` - Tests for ClientListItem and AlreadyConfiguredAlert (used by ClientSetupScreen)
  - `test_setup_complete_widgets.py` - Tests for FileLocationsSummary (used by SetupCompleteScreen)
- Update imports:
  - ClientSetupScreen from `gatekit.tui.screens.guided_setup.client_setup`
  - SetupCompleteScreen from `gatekit.tui.screens.setup_complete`
- This avoids cross-module imports in tests and keeps widget tests co-located with the screens that use them

#### `tests/unit/test_guided_setup_wizard_navigator.py`
- Update to expect 5 screens instead of 4
- Verify wizard flow: ServerSelection → ConfigLocation → ClientSelection → ClientSetup → SetupComplete
- Test BACK navigation from SetupComplete returns to ClientSetup

#### NEW: `tests/unit/test_guided_setup_setup_complete_summary.py`
- Test new SetupCompleteScreen
- Test summary builder with various server/client combinations
- Test button handlers (Back, Finish)
- Test navigation actions

---

## Implementation Steps

**IMPORTANT**: Preserve FileLocationsSummary before modifying files, then move it to the new location.

1. **Backup FileLocationsSummary component and helper methods**:
   ```bash
   # Extract FileLocationsSummary class by name (stops at next class, ignores blank lines)
   python3 << 'EOF' > /tmp/file_locations_summary.py
import re
with open('gatekit/tui/screens/setup_complete.py') as f:
    lines = f.readlines()

in_class = False
for line in lines:
    if re.match(r'^class FileLocationsSummary', line):
        in_class = True
    elif in_class and re.match(r'^class ', line):
        break  # Stop at next class

    if in_class:
        print(line, end='')
EOF

   # Also extract the helper methods it needs: _open_in_editor and _open_folder
   # (These will be copied to both files since both screens use them)
   awk '/^    def _open_in_editor/,/^    def [^_]|^class /{if (/^    def [^_]/ || /^class /) exit; print}' \
       gatekit/tui/screens/setup_complete.py >> /tmp/file_locations_summary.py
   awk '/^    def _open_folder/,/^    def [^_]|^class /{if (/^    def [^_]/ || /^class /) exit; print}' \
       gatekit/tui/screens/setup_complete.py >> /tmp/file_locations_summary.py
   ```

2. **Git move** (rename existing file):
   ```bash
   git mv gatekit/tui/screens/setup_complete.py gatekit/tui/screens/guided_setup/client_setup.py
   ```

3. **Modify `client_setup.py`**:
   - Rename class to ClientSetupScreen
   - Remove FileLocationsSummary class definition (entire class)
   - Remove FileLocationsSummary instantiation from compose() (the `yield FileLocationsSummary(config_path=..., restore_dir=...)` block, located after the master-detail split or empty state)
   - Remove button handlers for `open_config_file` and `open_restore_folder` (only used by FileLocationsSummary)
   - **Keep** `_open_in_editor()`, `_open_folder()`, and `_copy_to_clipboard()` methods (still needed by client instruction buttons)
   - **Keep** `platform` and `subprocess` imports (still needed by `_copy_to_clipboard()` and `_open_in_editor()`)
   - Change button: `finish_button` → `next_button`, label "Finish" → "Next"
   - Update button handler for next_button

4. **Create new `setup_complete.py`** with SetupCompleteScreen (final summary):
   - **Add imports** needed by helper methods: `import platform`, `import subprocess`, `from pathlib import Path`
   - Include FileLocationsSummary component (paste from /tmp/file_locations_summary.py)
   - **Copy** (not move) helper methods from ClientSetupScreen: `_open_in_editor()` and `_open_folder()` (these are also still needed in ClientSetupScreen)
   - Implement summary builder (`_build_summary_renderable()`)
   - Implement compose() with:
     - info-box showing servers/clients using `_build_summary_renderable()`
     - FileLocationsSummary instantiated with:
       - `config_path=self.state.config_path if self.state else self.gatekit_config_path`
       - `restore_dir=self.state.restore_dir if self.state else self.restore_script_dir`
       - (Supports both new state-based flow and legacy direct-attribute flow)
   - Implement button handlers:
     - Back: dismiss with NavigationAction.BACK
     - Finish: dismiss with NavigationAction.CONTINUE
     - open_config_file:
       - Use `config_path = self.state.config_path if self.state else self.gatekit_config_path`
       - Guard: `if config_path: self._open_in_editor(config_path)`
       - (Supports both new state-based and legacy direct-attribute flows)
     - open_restore_folder:
       - Use `restore_dir = self.state.restore_dir if self.state else self.restore_script_dir`
       - Guard: `if restore_dir: self._open_folder(restore_dir)`
       - (Supports both new state-based and legacy direct-attribute flows)

5. **Update `guided_setup/__init__.py`**:
   - Update module docstring (4-screen → 5-screen)
   - Add ClientSetupScreen import
   - Add ClientSetupScreen to `__all__` (keep WizardNavigator and launch_guided_setup!)

6. **Update `wizard_navigator.py`** with new imports and screen list

7. **Update `models.py`** docstring (lifecycle documentation)

8. **Split and update test files**:
   - Split `test_setup_complete_master_detail_widgets.py` into client_setup and setup_complete widget tests
   - Update `test_guided_setup_setup_complete_screen.py` → `test_guided_setup_client_setup_screen.py`
   - Update `test_guided_setup_wizard_navigator.py` for 5-screen flow
   - Create new tests for SetupCompleteScreen

9. **Run tests** (matching repo gates):
   ```bash
   uv run pytest --no-header -v
   ```

10. **Run linting** (matching repo gates):
    ```bash
    uv run ruff check gatekit tests
    ```

---

## Benefits

✅ ClientSetupScreen gets 10-15+ more lines for master-detail instructions
✅ Clean separation: instructions (screen 4) vs. summary (screen 5)
✅ Better UX on normal-sized terminals
✅ Consistent wizard pattern throughout
✅ Users can navigate back to review/change client setup
✅ Clear final summary shows what was accomplished

---

## Testing Plan

1. **Unit tests**: Verify all existing tests pass with updated imports
2. **Integration test**: Run wizard end-to-end through all 5 screens
3. **Navigation test**: Verify BACK from summary returns to client setup
4. **Content test**: Verify summary shows correct server/client counts and names
5. **Visual test**: Verify client setup screen has adequate vertical space on normal terminal

---

## Notes

- FileLocationsSummary component is reused as-is (no changes needed)
- All existing client setup logic remains unchanged (just moved to new file)
- GuidedSetupState already has all needed data (no state changes required)
- Follows existing wizard patterns (screen-title, description, info-box, buttons)
