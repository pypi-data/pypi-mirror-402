# Guided Setup: Integrate Client Selection into ConfigurationSummaryScreen

**Status:** ✅ Complete
**Priority:** High
**Complexity:** Medium (~3-4 hours)

## Overview

Integrate MCP client selection into ConfigurationSummaryScreen to streamline the guided setup wizard flow. This consolidates client selection with the final review step, eliminating the need for a separate ClientSetupScreen and ensuring restore scripts are generated before any instructions are shown to users.

## Problem Statement

Current wizard flow has timing and UX issues:

1. **Timing constraint**: Restore scripts must be written BEFORE showing any config snippets to users (even previews), because users might immediately follow instructions and quit the app before files are generated
2. **Redundant screens**: Having separate screens for client selection and config summary creates unnecessary navigation
3. **Unclear phrasing**: "MCP Clients to Configure" implies Gatekit will make changes, when we only generate instructions
4. **ClientSetupScreen orphaned**: The screen exists in code but was never added to WizardNavigator flow

## Current Wizard Flow

```
1. ServerSelectionScreen       → Select servers to manage
2. ConfigLocationScreen        → Choose gatekit.yaml path
3. ConfigurationSummaryScreen  → Review config (no client selection)
4. SetupActionsScreen          → Generate files
5. SetupCompleteScreen         → Show instructions
```

**Missing:** Client selection happens nowhere!

## Proposed Solution

Move client selection into ConfigurationSummaryScreen using DataTable (consistent with ServerSelectionScreen), and generate files via thread worker when user clicks Next:

```
1. ServerSelectionScreen       → Select servers + detect clients
2. ConfigLocationScreen        → Choose gatekit.yaml path
3. ConfigurationSummaryScreen  → Review + select clients + choose restore path
   └─ Next button → Spawn thread worker for file generation
4. SetupCompleteScreen         → Show full interactive instructions
```

**Key improvements:**
- File generation happens via thread worker in ConfigurationSummaryScreen's Next button handler, preventing UI freeze on slow disks
- Eliminates separate SetupActionsScreen that only flashed briefly before auto-dismissing
- Reuses state.detected_clients from ServerSelectionScreen instead of re-scanning filesystem

## Requirements

### Functional Requirements

#### FR-1: State Initialization from Detection Results
- **Reuse** `state.detected_clients` populated by ServerSelectionScreen (do NOT re-scan)
- Handle empty/None `state.detected_clients` (detection failed upstream in ServerSelectionScreen)
- **Keep ALL clients in selection table** (including ones already using Gatekit)
- Mark clients already using Gatekit with visual indicator (⚠️ icon or colored text)
- Store all clients in `self._available_clients` (instance variable)
- Identify which clients already use Gatekit and store in `state.already_configured_clients: List[DetectedClient]`
  - **IMPORTANT:** Must be `List[DetectedClient]` (not `Set[ClientType]`) to preserve:
    - Config file paths for each client (needed to display "Open Existing Config")
    - Multiple instances of same client type (e.g., multiple Claude Code scopes)
    - Full metadata for SetupCompleteScreen to show per-client actions
  - This field provides a contract for SetupCompleteScreen to show special handling
  - **Atomically rebuilt** during `_initialize_from_state()`:
    - Clear existing list first (prevents duplicates on BACK navigation)
    - Identify clients already using Gatekit by checking their config files
    - Append DetectedClient objects for those clients
  - **Prerequisite:** Add field to GuidedSetupState dataclass in `gatekit/tui/guided_setup/models.py` (see Architecture Changes section below)
- Initialize `state.selected_client_types` with all clients if empty (first visit)
- Preserve `state.selected_client_types` on BACK navigation (don't re-initialize if non-empty)
- Show informational note if some/all clients already configured (don't block, just inform)

#### FR-2: Client Selection DataTable
- Display ALL detected clients in DataTable (similar to ServerSelectionScreen pattern)
- Columns:
  - **Checkbox column** (`[ ]` or `[X]`)
  - **Client** (client name: "Claude Desktop", "Claude Code", "Codex")
  - **Configuration File** (full path: `~/.config/Claude/claude_desktop_config.json`)
- Visual indicator for clients already using Gatekit:
  - Add ⚠️ icon or colored text in Client column
  - Example: "⚠️ Claude Desktop" or style differently
  - Tooltip/hover: "Already using Gatekit"
- All clients selected by default (including ones already configured)
- Selection state tracked in `state.selected_client_types`

#### FR-3: Selection Controls
- **Select All** button - checks all clients (compact button styling)
- **Select None** button - unchecks all clients (compact button styling)
- **Selection summary** - "Selected 2 of 3 clients"
- Space bar toggles checkbox for highlighted row
- Mouse click on checkbox toggles directly
- Button styling: Use compact variant similar to `[Change]` button in restore directory section

#### FR-4: Restore Directory Selection
- Default restore directory to same location as gatekit config: `{config_dir}/restore/`
- Show restore path with **[Change]** button
- [Change] button opens **SelectDirectory** picker for directory selection (not FileSave - that's for files)
- Store in `state.restore_dir`
- Checkbox: "☑ Generate restore scripts (recommended)"
- Store checkbox state in `state.generate_restore`

#### FR-5: Section Organization

**Add:**
1. **Compact Server Summary** section (new):
   - Show selected server count: "Managing 3 servers"
   - Compact list of server names (first 5, "+ N more" if over 5)
   - No env var conflicts display (defer to SetupCompleteScreen)
   - Purpose: Final verification before file generation

2. **Setup Instructions** section:
   - Description: "Generate instructions and restore scripts for selected clients"
   - DataTable with client selection
   - Select All/None buttons
   - Selection summary

3. **File Locations** section:
   - Gatekit config path (read-only, from ConfigLocationScreen)
   - Restore directory path with [Change] button
   - "Generate restore scripts" checkbox

#### FR-6: Threaded File Generation with Progress
- Generate all files when user clicks Next button (before dismissing screen)
- **Use thread worker** to avoid blocking UI thread (don't assume <100ms)
- Show progress notification (permanent until dismissed)
- File generation operations (call existing modules, don't reimplement):
  - Call `config_generation.generate_gatekit_config()` for gatekit.yaml
  - Call `migration_instructions.generate_migration_instructions()` for instruction files
  - Call `restore_scripts.generate_restore_scripts()` for restore scripts (if checkbox checked)
- Handle errors gracefully:
  - Show error modal if generation fails
  - Don't dismiss screen on error
  - Allow user to retry or go back
- Only dismiss and advance to SetupCompleteScreen after successful generation
- Update `state.created_files`, `state.generation_errors`, `state.migration_instructions`
- **Rationale:** File generation can take longer on slow disks/network mounts; thread worker prevents UI freeze

#### FR-7: Informational Messaging for Already-Configured Clients (ConfigurationSummaryScreen Only)
- **In scope for this spec:**
  - If some/all clients already use Gatekit, show **informational note** in ConfigurationSummaryScreen (not blocking warning):
    - "Note: Some clients already use Gatekit and are marked with ⚠️"
    - "You can regenerate instructions or update their configuration"
  - No confirmation dialog needed - selection is allowed
  - Users can freely select/deselect already-configured clients
  - Populate `state.already_configured_clients: List[DetectedClient]` with full DetectedClient objects for clients already using Gatekit
    - Preserves config paths, multiple instances, and all metadata
    - SetupCompleteScreen will consume this field to show per-client special handling (see follow-up work below)

- **Out of scope for this spec** (tracked in separate follow-up work section below):
  - SetupCompleteScreen enhancements for already-configured clients
  - Special alert boxes and "Open Existing Config" button functionality

### Non-Functional Requirements

#### NFR-1: Consistent UX Patterns
- DataTable selection pattern matches ServerSelectionScreen exactly
- Same keyboard navigation (arrows, space, enter)
- Same visual feedback (checkboxes, highlighting)
- Same button styling and layout

#### NFR-2: State Management
- Preserve `state.selected_client_types` on BACK navigation
- Initialize with all clients selected by default if first visit
- Don't lose selections if user goes back and returns

#### NFR-3: Error Handling
- Handle empty `state.detected_clients` from upstream (show empty state message, allow continuing)
- Handle None/invalid `state.detected_clients` gracefully (treat as empty)
- Handle all clients already using Gatekit (show informational note, allow selection)
- Handle file generation failures with clear error messages and retry option

## Technical Design

### Screen Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Review & Finalize Setup                                     │
├─────────────────────────────────────────────────────────────┤
│ Review your selections and choose file locations.           │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ MANAGING 3 SERVERS                                      │ │
│ │ • filesystem-server  • github-mcp  • brave-search       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ SETUP INSTRUCTIONS                                      │ │
│ │                                                         │ │
│ │ Generate instructions and restore scripts for selected │ │
│ │ clients:                                                │ │
│ │                                                         │ │
│ │ ┌───┬──────────────────┬────────────────────────────┐  │ │
│ │ │   │ Client           │ Configuration File         │  │ │
│ │ ├───┼──────────────────┼────────────────────────────┤  │ │
│ │ │[X]│ Claude Desktop   │ ~/.config/Claude/claude... │  │ │
│ │ │[ ]│ Claude Code      │ ~/.claude.json             │  │ │
│ │ │[X]│ Codex            │ ~/.codex/config.json       │  │ │
│ │ └───┴──────────────────┴────────────────────────────┘  │ │
│ │                                                         │ │
│ │ Selected 2 of 3 clients    [Select All] [Select None]  │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ FILE LOCATIONS                                          │ │
│ │                                                         │ │
│ │ Gatekit Configuration:                                │ │
│ │ ~/gatekit/gatekit.yaml                              │ │
│ │ (Selected in previous step)                             │ │
│ │                                                         │ │
│ │ Restore Scripts Directory:                              │ │
│ │ ~/gatekit/restore/              [Change]              │ │
│ │                                                         │ │
│ │ ☑ Generate restore scripts (recommended)               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Back]                                  [Cancel]   [Next]  │
└─────────────────────────────────────────────────────────────┘
```

### Architecture Changes

#### GuidedSetupState Model Updates (PREREQUISITE)

**File:** `gatekit/tui/guided_setup/models.py`

**Add new field to GuidedSetupState dataclass:**

```python
@dataclass
class GuidedSetupState:
    """Wizard state that flows through all screens.

    Lifecycle (updated flow - SetupActionsScreen removed):
    1. ServerSelectionScreen: Populates detected_clients, deduplicated_servers, user modifies selected_server_names
    2. ConfigLocationScreen: User sets config_path
    3. ConfigurationSummaryScreen: User modifies selected_client_types, sets restore_dir, generate_restore,
       already_configured_clients; generates files and populates created_files, generation_errors, migration_instructions
    4. SetupCompleteScreen: Displays results using migration_instructions and already_configured_clients
    """

    # Populated by ServerSelectionScreen
    detected_clients: List[DetectedClient] = field(default_factory=list)
    deduplicated_servers: List[DeduplicatedServer] = field(default_factory=list)

    # User selections (modified by ServerSelectionScreen for servers, ConfigurationSummaryScreen for clients)
    selected_server_names: Set[str] = field(default_factory=set)
    selected_client_types: Set[ClientType] = field(default_factory=set)

    # File paths (set by ConfigLocationScreen for config_path, ConfigurationSummaryScreen for restore paths)
    config_path: Optional[Path] = None
    restore_dir: Optional[Path] = None
    generate_restore: bool = False

    # NEW: Clients already using Gatekit (populated by ConfigurationSummaryScreen)
    already_configured_clients: List[DetectedClient] = field(default_factory=list)

    # Results (populated by ConfigurationSummaryScreen during file generation)
    created_files: List[Path] = field(default_factory=list)
    generation_errors: List[str] = field(default_factory=list)
    migration_instructions: List["MigrationInstructions"] = field(default_factory=list)

    # ... rest of methods unchanged
```

**Key points:**
- **Type:** `List[DetectedClient]` preserves full metadata (config paths, multiple instances, client details)
- **Default:** Empty list via `field(default_factory=list)`
- **Populated by:** ConfigurationSummaryScreen during `_initialize_from_state()` (atomically rebuilt on each visit)
- **Consumed by:** SetupCompleteScreen (follow-up work) to show per-client special handling
- **Update docstring:** Updated lifecycle to reflect SetupActionsScreen removal and ConfigurationSummaryScreen file generation

**Test updates required:**
- Update `tests/unit/test_guided_setup_models.py` to verify new field
- Test default value is empty list
- Test field persists through state updates

#### ConfigurationSummaryScreen Updates

**New imports:**
```python
from ...guided_setup.models import ClientType, DetectedClient
from textual.widgets import DataTable
# Note: Do NOT import detect_all_clients - reuse state.detected_clients instead
```

**New instance variables:**
```python
self._available_clients = []  # ALL clients from state.detected_clients (local cache for table rendering)
self._clients_table_initialized = False
# Note: Already-configured clients tracked in state.already_configured_clients (authoritative source)
```

**New methods:**
```python
def _initialize_from_state(self) -> None:
    """Initialize from existing state (reuse detected clients, don't re-scan).

    - Reuse state.detected_clients from ServerSelectionScreen
    - Keep ALL clients (including ones already using Gatekit)
    - ATOMICALLY rebuild state.already_configured_clients:
      - Clear existing list (prevents duplicates on BACK navigation)
      - Identify clients already using Gatekit by checking their config files
      - Append DetectedClient objects for those clients
    - Initialize state.selected_client_types if empty (first visit)
    - Preserve state.selected_client_types if non-empty (BACK navigation)
    """

def _populate_clients_table(self) -> None:
    """Populate DataTable with detected clients and checkboxes."""

def _update_selection_summary(self) -> None:
    """Update 'Selected X of Y clients' text."""

def action_select_all_clients(self) -> None:
    """Select all clients."""

def action_select_none_clients(self) -> None:
    """Deselect all clients."""

def action_toggle_client_selection(self) -> None:
    """Toggle checkbox for highlighted client."""
```

**Event handlers:**
```python
@on(DataTable.RowSelected, "#clients_table")
def on_client_row_selected(self, event: DataTable.RowSelected) -> None:
    """Handle Enter key on client row (toggle selection)."""

@on(Button.Pressed, "#select_all_clients")
def on_select_all_clients(self) -> None:
    """Handle compact Select All button."""

@on(Button.Pressed, "#select_none_clients")
def on_select_none_clients(self) -> None:
    """Handle compact Select None button."""

@on(Button.Pressed, "#change_restore_dir")
async def on_change_restore_dir(self) -> None:
    """Handle Change button for restore directory."""

@on(Button.Pressed, "#next_button")
async def on_next(self) -> None:
    """Generate files via thread worker and advance to completion screen."""
```

**File generation methods (synchronous worker):**
```python
def _generate_all_files_worker(self) -> None:
    """Generate all configuration files using existing modules (synchronous).

    Runs in thread worker to avoid blocking UI thread (thread=True).
    Must be synchronous (not async def) because it runs in a thread.
    Calls existing generation functions from gatekit.tui.guided_setup modules.

    Raises:
        Exception: If file generation fails
    """
```

#### Remove/Archive ClientSetupScreen

1. Delete or comment out `gatekit/tui/screens/guided_setup/client_setup.py`
2. Remove from `gatekit/tui/screens/guided_setup/__init__.py`
3. Remove test file `tests/unit/test_guided_setup_client_setup_screen.py`

#### Remove SetupActionsScreen

1. Delete or archive `gatekit/tui/screens/guided_setup/setup_actions.py`
2. Remove from `gatekit/tui/screens/guided_setup/__init__.py`
3. Remove test file `tests/unit/test_guided_setup_setup_actions_screen.py`
4. **Note:** Keep existing generation modules (config_generation.py, migration_instructions.py, restore_scripts.py) - ConfigurationSummaryScreen will call them, not reimplement them

#### WizardNavigator Updates

**Remove SetupActionsScreen from flow:**

```python
async def launch(self) -> Optional[Path]:
    """Launch wizard with automatic back navigation.

    Navigation Flow:
    1. ServerSelectionScreen: Select servers + detect clients
    2. ConfigLocationScreen: Choose gatekit.yaml path
    3. ConfigurationSummaryScreen: Review servers, select clients, generate files
    4. SetupCompleteScreen: Show interactive instructions

    Returns:
        Path to created config file, or None if cancelled
    """
    # Import screens
    from gatekit.tui.screens.guided_setup.server_selection import ServerSelectionScreen
    from gatekit.tui.screens.guided_setup.config_location import ConfigLocationScreen
    from gatekit.tui.screens.guided_setup.config_summary import ConfigurationSummaryScreen
    from gatekit.tui.screens.setup_complete import SetupCompleteScreen

    # Define navigable screens (support BACK/CONTINUE/CANCEL)
    screens = [
        ServerSelectionScreen,  # Populates state.detected_clients
        ConfigLocationScreen,
        ConfigurationSummaryScreen,  # Reuses state.detected_clients
    ]

    current_index = 0
    while current_index < len(screens):
        action = await self.navigate_to(screens[current_index])

        if action == NavigationAction.CANCEL:
            return None
        elif action == NavigationAction.BACK:
            current_index -= 1
            if current_index < 0:
                return None
        elif action == NavigationAction.CONTINUE:
            current_index += 1

    # Show completion screen (no BACK support - setup is done)
    await self.navigate_to(SetupCompleteScreen)

    return self.state.config_path
```

### DataTable Implementation Pattern

**Reuse from ServerSelectionScreen:**

```python
# Populate table with checkbox indicators
def _populate_clients_table(self) -> None:
    table = self.query_one("#clients_table", DataTable)

    # Initialize columns once
    if not self._clients_table_initialized:
        table.clear()
        table.add_column("")  # Checkbox
        table.add_column("Client")
        table.add_column("Configuration File")
        self._clients_table_initialized = True
    else:
        table.clear()

    # Add rows
    for client in self._available_clients:
        is_selected = client.client_type in self.state.selected_client_types

        # Check if client already uses Gatekit (look in state.already_configured_clients)
        is_already_configured = client in self.state.already_configured_clients

        # Checkbox indicator
        indicator = Text("[X]") if is_selected else Text("[ ]", style="dim")

        # Client name with ⚠️ indicator if already configured
        display_name = client.display_name()
        if is_already_configured:
            display_name = f"⚠️  {display_name}"
        name = Text(display_name, style="" if is_selected else "dim")

        # Config path
        config_path = Text(str(client.config_path), style="dim")

        table.add_row(
            indicator,
            name,
            config_path,
            key=str(client.config_path)  # Use config path as unique row key (supports multiple instances of same client type)
        )
```

### Restore Directory Default Logic

```python
def _get_default_restore_dir(self) -> Path:
    """Get default restore directory (same location as config)."""
    if self.state.config_path:
        return self.state.config_path.parent / "restore"
    else:
        # Fallback if config_path not set (shouldn't happen)
        return Path.home() / "gatekit" / "restore"
```

### CSS Updates

```css
ConfigurationSummaryScreen #clients_table {
    height: auto;
    max-height: 10;
    margin-bottom: 1;
}

ConfigurationSummaryScreen .selection-summary-row {
    height: auto;
    margin-bottom: 1;
}

ConfigurationSummaryScreen .selection-summary {
    text-style: bold;
    color: $accent;
}

/* Compact button styling for Select All/None (similar to Change button) */
ConfigurationSummaryScreen .compact-button {
    width: auto;
    min-width: 12;
    height: 1;
    padding: 0;
    margin-left: 1;
}
```

## Development Approach

**This feature MUST be implemented using Test-Driven Development (TDD).**

### TDD Process

For each phase below:
1. **Write tests first** - Define expected behavior in tests before writing implementation
2. **Run tests** - Verify they fail (red)
3. **Implement** - Write minimal code to make tests pass (green)
4. **Refactor** - Clean up code while keeping tests green
5. **Repeat** - Move to next test case

### Testing Strategy

**Unit tests** for:
- State initialization from detection results (empty, valid, invalid)
- Client identification logic (which ones already use Gatekit)
- Visual indicators for already-configured clients
- Selection state management (all clients selectable)
- DataTable population with checkboxes and warning indicators
- Select All/None button handlers
- Restore directory defaulting logic
- File generation methods (mock filesystem operations)

**Integration tests** for:
- Full screen interaction flow
- State preservation on BACK navigation
- Error handling modals
- File generation with real filesystem (use tempdir)

**Key testing principles:**
- Use pre-populated `state.detected_clients` in test fixtures (detection happens in ServerSelectionScreen)
- Test handling of empty/None `state.detected_clients` (upstream detection failure)
- Use `tempfile.TemporaryDirectory()` for file generation tests
- Test edge cases (no clients in state, all configured, empty detection results)
- Verify state updates correctly
- Test atomic file operations (failure scenarios)
- Mock file generation modules (config_generation, migration_instructions, restore_scripts) to test worker orchestration

## Implementation Checklist

### Phase 0: GuidedSetupState Model Updates (PREREQUISITE - Must Complete First)
**Update the shared state model before ConfigurationSummaryScreen can use it:**

- [ ] **Update `gatekit/tui/guided_setup/models.py`:**
  - [ ] Add `already_configured_clients: List[DetectedClient] = field(default_factory=list)` to GuidedSetupState dataclass
  - [ ] Update GuidedSetupState docstring to remove SetupActionsScreen (now deleted)
  - [ ] Update lifecycle to show ConfigurationSummaryScreen generates files and populates created_files, generation_errors, migration_instructions
  - [ ] Update lifecycle step 3 to mention ConfigurationSummaryScreen populates `already_configured_clients`
  - [ ] Update lifecycle step 4 to mention SetupCompleteScreen consuming `already_configured_clients`
  - [ ] Update comment on `created_files`, `generation_errors`, `migration_instructions` to say "populated by ConfigurationSummaryScreen" (not SetupActionsScreen)
  - [ ] Update comment on `selected_client_types` to say "modified by ConfigurationSummaryScreen" (not ClientMigrationScreen)
- [ ] **Update `tests/unit/test_guided_setup_models.py`:**
  - [ ] Test new field exists with correct default (empty list)
  - [ ] Test field can be set to list of DetectedClient objects
  - [ ] Test field persists through state updates/copies
- [ ] **Run Phase 0 tests:** `pytest tests/unit/test_guided_setup_models.py -v`
- [ ] **Verify:** All existing tests still pass after adding new field

**⚠️ BLOCKING:** Phases 1-6 cannot proceed until Phase 0 is complete. ConfigurationSummaryScreen will get AttributeError if it tries to access `state.already_configured_clients` before this field is added to the dataclass.

### Phase 1: ConfigurationSummaryScreen Updates (TDD)
**Write tests first, then implement each feature:**

- [ ] **Test:** Screen initializes from state.detected_clients (no re-scan)
- [ ] **Test:** Screen keeps ALL clients (including ones already using Gatekit)
- [ ] **Test:** Screen identifies which clients already use Gatekit
- [ ] **Test:** state.already_configured_clients populated with DetectedClient objects for clients already using Gatekit
- [ ] **Test:** state.already_configured_clients preserves full metadata (config paths, client types, all fields)
- [ ] **Test:** state.already_configured_clients cleared before repopulating (no duplicates on BACK navigation)
- [ ] **Test:** On second visit (BACK navigation), state.already_configured_clients rebuilt correctly without duplicates
- [ ] **Test:** state.selected_client_types initialized with all clients on first visit
- [ ] **Test:** state.selected_client_types preserved on BACK navigation
- [ ] **Implement:** Add `_initialize_from_state()` method (keep all clients, atomically rebuild state.already_configured_clients)
- [ ] **Test:** DataTable shows ALL detected clients with checkbox indicators
- [ ] **Test:** DataTable marks clients already using Gatekit with ⚠️ indicator
- [ ] **Implement:** Add DataTable and `_populate_clients_table()` method
- [ ] **Test:** Checkbox indicators update when selection state changes
- [ ] **Implement:** Wire DataTable updates to `state.selected_client_types`
- [ ] **Test:** Select All button checks all clients
- [ ] **Implement:** Add Select All button handler
- [ ] **Test:** Select None button unchecks all clients
- [ ] **Implement:** Add Select None button handler
- [ ] **Test:** Selection summary shows correct count
- [ ] **Implement:** Add selection summary with compact buttons in Horizontal
- [ ] **Test:** Space key toggles checkbox for highlighted row
- [ ] **Implement:** Add keyboard toggle handler
- [ ] **Test:** Clients already using Gatekit shown with ⚠️ indicator, remain selectable
- [ ] **Test:** Informational note shown when some/all clients already configured
- [ ] **Implement:** Add informational note (not blocking) for already-configured clients
- [ ] **Test:** Compact server summary shows count and server names
- [ ] **Implement:** Add compact server summary section
- [ ] **Run all Phase 1 tests:** `pytest tests/unit/test_guided_setup_config_summary_screen.py -v`

### Phase 2: Restore Directory Selection (TDD)
**Write tests first, then implement each feature:**

- [ ] **Test:** Restore directory defaults to `{config_dir}/restore/`
- [ ] **Implement:** Add `_get_default_restore_dir()` method
- [ ] **Test:** [Change] button opens SelectDirectory picker and updates path
- [ ] **Implement:** Add restore directory display with [Change] button (use SelectDirectory)
- [ ] **Test:** Restore checkbox state stored in `state.generate_restore`
- [ ] **Implement:** Add "Generate restore scripts" checkbox
- [ ] **Run all Phase 2 tests:** `pytest tests/unit/test_guided_setup_config_summary_screen.py::TestRestoreDirectory -v`

### Phase 3: Threaded File Generation (TDD)
**Write tests first, then implement each feature:**

- [ ] **Test:** `_generate_all_files_worker()` calls config_generation.generate_gatekit_config()
- [ ] **Test:** `_generate_all_files_worker()` calls migration_instructions.generate_migration_instructions()
- [ ] **Test:** `_generate_all_files_worker()` calls restore_scripts.generate_restore_scripts() when enabled
- [ ] **Test:** `_generate_all_files_worker()` skips restore scripts when checkbox disabled
- [ ] **Test:** Worker updates `state.created_files` and `state.migration_instructions`
- [ ] **Implement:** Add `_generate_all_files_worker()` as synchronous function (not async)
- [ ] **Test:** Next button spawns thread worker (doesn't block main thread)
- [ ] **Test:** Next button shows progress notification during generation
- [ ] **Test:** Next button dismisses progress notification on success
- [ ] **Test:** Next button dismisses progress notification and shows error modal on failure
- [ ] **Test:** Next button doesn't dismiss screen when generation fails
- [ ] **Test:** Next button dismisses and advances after successful generation
- [ ] **Implement:** Update Next button handler with thread worker and notification handling
- [ ] **Run all Phase 3 tests:** `pytest tests/unit/test_guided_setup_config_summary_screen.py::TestFileGeneration -v`

### Phase 4: Update Server Preview (TDD)
**Write tests first, then implement:**

- [ ] **Test:** Screen shows compact server summary (count + names)
- [ ] **Implement:** Replace ConfigPreview with compact server summary
- [ ] **Verify:** SetupCompleteScreen shows full server details (existing functionality)
- [ ] **Run all Phase 4 tests:** `pytest tests/unit/test_guided_setup_config_summary_screen.py -v`

### Phase 5: Cleanup (No new tests needed)
- [ ] Archive/delete ClientSetupScreen
- [ ] Remove ClientSetupScreen from `__init__.py`
- [ ] Delete ClientSetupScreen tests
- [ ] Archive/delete SetupActionsScreen
- [ ] Remove SetupActionsScreen from `__init__.py`
- [ ] Delete SetupActionsScreen tests
- [ ] Update WizardNavigator to remove SetupActionsScreen from flow
- [ ] Update WizardNavigator docstrings

### Phase 6: Integration Testing & Validation ✅
**Final verification after all phases:**

- [x] **Integration test:** Full wizard flow with client selection works end-to-end (test_complete_happy_path_forward_navigation)
- [x] **Integration test:** State preserves correctly on BACK navigation (test_back_navigation_preserves_state)
- [x] **Integration test:** Files generate successfully with real filesystem (test_file_generation_success_with_temp_directory)
- [x] **Integration test:** Cancel scenarios (test_cancel_from_first_screen, test_cancel_from_middle_screen, test_back_from_first_screen_acts_as_cancel)
- [x] **Integration test:** Multiple clients selection (test_multiple_clients_selection)
- [x] **Integration test:** Claude Code project servers detection (test_claude_code_project_servers_detection)
- [x] **Run full test suite:** `pytest tests/ -n auto` (2158 passed, 4 skipped)
- [x] **Run linting:** `uv run ruff check gatekit` (all checks passed)
- [x] **Verify coverage:** New code has ≥90% coverage (config_summary: 86%, models: 97%, wizard_navigator: tested via integration)

**Note:** Manual TUI testing recommended before release, but automated integration tests provide comprehensive coverage of wizard flow, state management, and file generation.

## Edge Cases to Handle

1. **Empty state.detected_clients** (no clients found by ServerSelectionScreen): Show empty state message, allow continuing
2. **None/invalid state.detected_clients** (detection failed upstream): Treat as empty, show empty state message
3. **All clients already using Gatekit**: Show informational note with ⚠️ indicators, all remain selectable
4. **Some clients already using Gatekit**: Show informational note, mark those clients with ⚠️ in table
5. **User unchecks all clients**: Allow (migration instructions optional)
6. **Restore directory doesn't exist**: Create parent directories during file generation
7. **Restore checkbox unchecked**: Skip restore script generation
8. **File generation fails**: Show error modal, don't dismiss screen, allow retry
9. **Gatekit config already exists**: Warn user and offer to overwrite or choose different path
10. **Permission denied writing files**: Show clear error message with path that failed

## Success Criteria

### Functional
- [ ] ConfigurationSummaryScreen shows client selection DataTable
- [ ] Screen reuses state.detected_clients (no re-scan)
- [ ] ALL clients shown in table (including ones already using Gatekit)
- [ ] Clients already using Gatekit marked with ⚠️ visual indicator
- [ ] Informational note shown for already-configured clients (not blocking)
- [ ] Selection state persists through BACK navigation
- [ ] Restore directory defaults correctly
- [ ] All clients selected by default on first visit
- [ ] Select All/None buttons work correctly (compact styling)
- [ ] Checkbox toggles work (Space key + mouse click)
- [ ] Compact server summary shows selected server count and names
- [ ] File generation happens via thread worker when clicking Next (doesn't block UI)
- [ ] "Generating..." notification appears during file generation
- [ ] Error modal appears if file generation fails
- [ ] Files are not created if error occurs (atomic operations)
- [ ] File generation calls existing modules (doesn't reimplement logic)

### Code Quality
- [ ] All features implemented using TDD (tests written first)
- [ ] No more ClientSetupScreen in codebase
- [ ] No more SetupActionsScreen in codebase
- [ ] All tests pass: `pytest tests/ -n auto`
- [ ] No linting issues: `uv run ruff check gatekit`
- [ ] Test coverage ≥90% for new code (project standard)
- [ ] Wizard flow works end-to-end (manual verification)

## File Generation Implementation

### Next Button Handler Pattern (Thread Worker)

```python
@on(Button.Pressed, "#next_button")
async def on_next(self) -> None:
    """Generate files via worker and advance to completion screen."""
    # Keep handle to notification so we can dismiss it later
    progress_notification = None

    try:
        # Show progress notification (permanent until explicitly dismissed)
        progress_notification = self.notify(
            "Generating configuration files...",
            timeout=None,
            severity="information"
        )

        # Spawn synchronous worker (file I/O is inherently blocking)
        # Note: thread=False would require async def worker, but file ops are sync
        worker = self.run_worker(self._generate_all_files_worker, thread=True, exclusive=True)
        await worker.wait()

        # Check if worker raised an exception
        if worker.error:
            raise worker.error

        # IMPORTANT: Dismiss the permanent notification before showing new one
        if progress_notification:
            progress_notification.dismiss()

        # Show success message
        self.notify("Configuration files created successfully!", severity="information", timeout=3)

        # Advance to completion screen
        self.dismiss(ScreenResult(action=NavigationAction.CONTINUE, state=self.state))

    except Exception as e:
        # IMPORTANT: Dismiss the permanent notification before showing error
        if progress_notification:
            progress_notification.dismiss()

        # Show error message
        self.notify("File generation failed", severity="error", timeout=5)

        # Show error modal
        await self.app.push_screen(
            ErrorModal(
                title="File Generation Failed",
                message=f"Failed to generate configuration files:\n\n{str(e)}",
            )
        )
        # Don't dismiss screen - user can retry or go back


def _generate_all_files_worker(self) -> None:
    """Worker that calls existing generation modules (synchronous).

    IMPORTANT: This is a synchronous function (not async def) because:
    - It runs in a thread (thread=True in run_worker)
    - The existing generation modules are synchronous
    - File I/O is inherently blocking anyway

    Calls:
    - config_generation.generate_gatekit_config()
    - migration_instructions.generate_migration_instructions()
    - restore_scripts.generate_restore_scripts()

    Does NOT reimplement file writing logic - delegates to existing modules.
    """
    # Implementation calls existing functions from:
    # - gatekit.tui.guided_setup.config_generation
    # - gatekit.tui.guided_setup.migration_instructions
    # - gatekit.tui.guided_setup.restore_scripts
```

### File Generation Implementation Notes

**Call existing modules, don't reimplement:**
- Use `config_generation.generate_gatekit_config()` for gatekit.yaml
- Use `migration_instructions.generate_migration_instructions()` for instruction files
- Use `restore_scripts.generate_restore_scripts()` for restore scripts
- These modules already handle atomic writes, error handling, and state updates
- Don't duplicate file I/O logic on the screen class

## Follow-up Work Required

**SetupCompleteScreen Updates** (separate from this spec):
- Add special handling for clients already using Gatekit
- **Data source:** Read from `state.already_configured_clients: List[DetectedClient]`
  - Each DetectedClient contains full metadata: config_path, client_type, display name, etc.
  - Can iterate over list to show per-client alerts and actions
  - Supports multiple instances of same client type (e.g., multiple Claude Code scopes)
- For each already-configured client in `state.already_configured_clients`:
  - Show alert box: "⚠️ {client.display_name()} Already Uses Gatekit"
  - Explain two options: Replace with new config OR edit existing config
  - Display path to existing Gatekit config: `{client.config_path}`
  - Add "Open Existing Config" button to launch editor with `client.config_path`
  - Standard instructions remain for creating new client entry
- This work should be tracked in a separate requirements doc/ticket

## References

- ServerSelectionScreen: `gatekit/tui/screens/guided_setup/server_selection.py` (DataTable pattern, client detection)
- Old ClientMigrationScreen: `git show c454da6~1:gatekit/tui/screens/guided_setup/client_migration.py` (checkbox logic)
- ConfigurationSummaryScreen: `gatekit/tui/screens/guided_setup/config_summary.py` (current implementation, will be updated with thread worker pattern per this spec)
- SetupCompleteScreen: `gatekit/tui/screens/setup_complete.py` (will need updates for already-configured clients)
- Client detection: `gatekit/tui/guided_setup/detection.py`
- Config generation: `gatekit/tui/guided_setup/config_generation.py`
- Migration instructions: `gatekit/tui/guided_setup/migration_instructions.py`
- Restore scripts: `gatekit/tui/guided_setup/restore_scripts.py`
- Models: `gatekit/tui/guided_setup/models.py`

**Note:** SetupActionsScreen and ClientSetupScreen will be removed as part of Phase 5 cleanup. The thread worker pattern is now implemented directly in ConfigurationSummaryScreen (see "File Generation Implementation" section above).
