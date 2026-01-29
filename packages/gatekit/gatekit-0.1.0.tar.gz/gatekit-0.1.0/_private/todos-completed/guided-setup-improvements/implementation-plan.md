# Guided Setup Implementation Plan

## Revision History

**Phase 1 Complete**: Foundation & Data Models
- ✅ Implemented `NavigationAction` enum and `ScreenResult` type (models.py:131-151)
- ✅ Implemented `DeduplicatedServer` dataclass (models.py:154-170)
- ✅ Implemented `GuidedSetupState` with `update_deduplicated_servers()` method (models.py:173-258)
- ✅ Implemented server deduplication logic (deduplication.py)
- ✅ Implemented environment variable consolidation (config_generation.py:251-301)
- ✅ All 34 Phase 1 tests passing
- ✅ All existing tests passing (1995 total)

**Planning Updates**: Fixed critical architectural issues and added TDD strategy:

**Architectural Decisions**:
1. **Navigation ambiguity** - Designed `NavigationAction` enum and `ScreenResult` type to distinguish CONTINUE/BACK/CANCEL
2. **State construction** - Planned for screens to accept injected `GuidedSetupState` instead of creating their own
3. **Screen contract** - Specified `dismiss(ScreenResult(...))` contract for ALL screen templates (including SetupCompleteScreen)
4. **Back navigation** - Designed `WizardNavigator` helper class for clean back-navigation logic
5. **Rescan behavior** - Implemented `update_deduplicated_servers()` that handles selection preservation automatically
6. **Textual async handlers** - Documented that `on_button_pressed` should use `run_worker()` for async work (see line 744 in Discovery screen template)
7. **Code clarity** - Planned single `WizardNavigator` implementation approach
8. **SetupCompleteScreen contract** - Designed `Screen[ScreenResult]` inheritance and `dismiss()` call (see lines 876-924 in template)

**TDD Strategy** (lines 50-212):
- Added comprehensive TDD strategy for reworking existing functionality
- Phase-by-phase test-first workflow (Pure TDD for Phase 1, Hybrid for Phase 2, Pure TDD for Phase 3)
- `@pytest.mark.legacy` pattern for safely migrating existing tests
- Test checklist by phase with specific scenarios
- Example TDD cycle for `update_deduplicated_servers()`
- Integration test guidance with back navigation scenarios
- **Clarification**: Tests pass at Phase 1 and Phase 3+ only (Phase 2 has isolated screen tests that integrate in Phase 3)

## Reference Documents
- **UX Specification**: [ux-specification.md](./ux-specification.md) - Complete user flow, mockups, and requirements
- **Current Implementation**: [guided-setup.md](../../todos-completed/visual-configuration-interface/guided-setup.md) - Original specification

## Current State Analysis

### Existing Implementation
The current guided setup is a **single-step wizard** that:
- Runs detection immediately upon launch
- Asks for file paths upfront (config location, restore script directory)
- Generates files and shows a single "Setup Complete" screen
- Works but provides value only AFTER user commits with file paths

**Key Files:**
- `gatekit/tui/screens/welcome.py` - Welcome screen with "Guided Setup" button
- `gatekit/tui/screens/setup_complete.py` - Final instructions screen
- `gatekit/tui/guided_setup/` - Core logic (detection, parsing, generation)
  - `models.py` - Data models (DetectedClient, DetectedServer)
  - `detection.py` - Client detection
  - `parsers.py` - Config parsing
  - `config_generation.py` - Gatekit config generation
  - `migration_instructions.py` - Client-specific instructions
  - `restore_scripts.py` - Restore script generation
  - `connection_testing.py` - Server connection testing
  - `gateway.py` - Locating gatekit-gateway executable

### What Needs to Change
Transform from **ask-then-show** to **show-then-ask**:
- ❌ Current: File paths → Detection → Generation → Instructions
- ✅ New: Detection → Server Selection → Client Selection → Summary → File paths → Generation → Instructions

Add progressive disclosure with 6 screens instead of 2.

---

## TDD Strategy for Rework

**Approach**: Test-Driven Development with incremental migration from old to new implementation.

### Test Migration Strategy

1. **Identify Affected Tests** (Phase 0 - Before Implementation):
   - Run `pytest tests/ -v | grep guided_setup` to find all tests
   - Audit each test file to categorize:
     - ✅ **Keep as-is**: Tests of core logic that won't change (deduplication, env vars, etc.)
     - 🔄 **Update**: Tests that need new screen contracts (state injection, ScreenResult)
     - ❌ **Remove**: Tests of old single-screen flow
     - ➕ **Add new**: Tests for navigation logic, back button behavior

2. **Phase-by-Phase TDD Workflow**:

   **Phase 1 (Foundation)**: Pure TDD - no existing tests affected
   - Write tests FIRST for new models (`NavigationAction`, `ScreenResult`, `DeduplicatedServer`)
   - Write tests FIRST for `GuidedSetupState.update_deduplicated_servers()`
   - Write tests FIRST for deduplication logic
   - Write tests FIRST for env var consolidation
   - Run tests: `pytest tests/unit/test_guided_setup_*.py -v`
   - Implement until green

   **Phase 2 (Screens)**: Hybrid - update existing tests, add new ones
   - For each screen:
     1. **Copy existing test** to `test_guided_setup_[screen]_new.py` (temporary)
     2. **Update copied test** to use new contract (state injection, ScreenResult)
     3. **Write new tests** for button handlers (CONTINUE/BACK/CANCEL)
     4. **Implement screen** until tests pass
     5. **Delete old test** file once new screen works
     6. **Rename** `_new.py` → `.py`

   **Phase 3 (Navigation)**: Pure TDD - new functionality
   - Write tests FIRST for `WizardNavigator`:
     - Test forward navigation through all screens
     - Test back navigation from each screen
     - Test cancel at each screen
     - Test state preservation across navigation
   - Implement `WizardNavigator` until green
   - Write integration test for full flow

   **Phase 4 (Testing)**: Validation and cleanup
   - Run full test suite: `pytest tests/ -v`
   - Ensure no old tests remain
   - Verify coverage: `pytest --cov=gatekit/tui/guided_setup tests/`

3. **Test Checklist by Phase**:

   ```
   Phase 1 Foundation:
   [ ] test_navigation_action_enum.py
   [ ] test_screen_result.py
   [ ] test_deduplicated_server.py
   [ ] test_guided_setup_state.py
   [ ] test_update_deduplicated_servers.py (rescan scenarios)
   [ ] test_deduplication.py (conflict resolution, client dedup, complete key)
   [ ] test_env_var_consolidation.py (conflict detection, masking, determinism)

   Phase 2 Screens:
   [ ] test_discovery_screen.py (state injection, ScreenResult, rescan button)
   [ ] test_server_selection_screen.py (selection logic, back button)
   [ ] test_client_migration_screen.py (selection logic, back button)
   [ ] test_config_summary_screen.py (file path capture, back button)
   [ ] test_setup_actions_screen.py (atomic file ops, error handling)
   [ ] test_setup_complete_screen.py (done button, ScreenResult)

   Phase 3 Navigation:
   [ ] test_wizard_navigator.py (forward, back, cancel, state preservation)
   [ ] test_guided_setup_integration.py (full happy path, back navigation)

   Phase 4 Validation:
   [ ] All tests pass
   [ ] No old test files remain
   [ ] Coverage >= 85% for new code
   ```

4. **Example: Phase 1 TDD Cycle for `update_deduplicated_servers()`**:

   ```python
   # Step 1: Write test FIRST (RED)
   def test_update_deduplicated_servers_preserves_deselections():
       """Rescan should preserve user's intentional deselections."""
       state = GuidedSetupState()

       # Initial: A, B, C all selected
       state.deduplicated_servers = [server_a, server_b, server_c]
       state.selected_server_names = {"A", "B", "C"}

       # User deselects B
       state.selected_server_names.remove("B")

       # Rescan finds A, C, D (B is gone, D is new)
       new_servers = [server_a, server_c, server_d]
       state.update_deduplicated_servers(new_servers, [])

       # Result: A, C, D selected (B's deselection preserved)
       assert state.selected_server_names == {"A", "C", "D"}

   # Step 2: Run test - FAILS (method doesn't exist yet)
   # Step 3: Implement method (GREEN)
   # Step 4: Refactor if needed
   # Step 5: Move to next test
   ```

5. **Handling Existing Integration Tests**:
   - **Don't delete** working integration tests immediately
   - Mark old tests with `@pytest.mark.legacy` decorator
   - Run legacy tests to ensure old behavior still works during migration
   - Remove `@pytest.mark.legacy` tests only when new implementation is complete
   - Example:
     ```python
     @pytest.mark.legacy
     def test_old_guided_setup_flow():
         """Legacy test - remove when new multi-screen flow complete."""
         # Old single-screen test
     ```

### Benefits of This Approach

- ✅ **Safety**: Old tests keep running until new implementation is complete
- ✅ **Clarity**: Easy to see what needs migrating via `pytest -m legacy`
- ✅ **Confidence**: Each phase has its own green test suite
- ✅ **Incremental**: Can pause/resume work at phase boundaries
- ✅ **Documentation**: Tests document new contracts and expected behavior

### Can We Have All Tests Passing After Each Phase?

**Short answer**: No, not until Phase 3 is complete.

| Phase | All Tests Pass? | Notes |
|-------|-----------------|-------|
| **Phase 1** | ✅ **YES** | Pure additive - new models/functions don't break existing code. Run `pytest tests/` at end of phase. |
| **Phase 2** | ❌ **NO** | New screens exist but aren't wired up yet. Old implementation still in use. Write tests but they won't run in full suite until Phase 3. |
| **Phase 3** | ✅ **YES** | WizardNavigator wires up new screens, replace old implementation. All tests pass. |
| **Phase 4** | ✅ **YES** | Validation only - tests already passing from Phase 3. |

**Why Phase 2 Can't Have All Tests Passing**:

The new multi-screen implementation fundamentally replaces the old single-screen flow. You can't have both "active" at once, so:
- **During Phase 2**: Write tests for new screens, but they're isolated unit tests that don't run through the full flow
- **Phase 3**: Wire everything together with WizardNavigator, replace old flow in welcome.py, NOW all tests pass

**Practical Workflow**:
- Phase 1: Write tests → implement → `pytest tests/` ✅
- Phase 2: Write tests → implement → test individual screens in isolation → commit
- Phase 3: Wire up navigator → replace old flow → `pytest tests/` ✅ → commit
- Phase 4: Validate → `pytest tests/` ✅ → commit

You won't have full integration testing until Phase 3, but that's fine - it's a rework, not incremental enhancement.

## Implementation Phases

### Phase 1: Foundation & Data Models (4-6 hours)

**TDD Note**: This phase is pure TDD - write all tests FIRST, then implement. No existing tests affected.

**Architecture Overview**:

This phase addresses critical architectural requirements identified in code review:

1. **Navigation Contract** (`NavigationAction` + `ScreenResult`):
   - Distinguishes CONTINUE vs. BACK vs. CANCEL actions
   - Enables proper back navigation with selection preservation
   - Every screen explicitly returns `ScreenResult` via `dismiss()`

2. **State Injection** (`GuidedSetupState` constructor pattern):
   - Flow controller creates state once, injects into all screens
   - Enables rescan and back navigation without losing data
   - State flows through entire wizard lifecycle

3. **Smart Reconciliation** (`update_deduplicated_servers()` method):
   - Preserves user intent when rescanning or navigating back
   - Auto-selects newly discovered items
   - Maintains intentional deselections

#### Task 1.1: Extend Data Models
**File**: `gatekit/tui/guided_setup/models.py`

**Add New Models**:

```python
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set

class NavigationAction(Enum):
    """User navigation decision from a screen."""
    CONTINUE = "continue"  # Proceed to next screen
    BACK = "back"          # Return to previous screen
    CANCEL = "cancel"      # Abort wizard entirely

@dataclass
class ScreenResult:
    """Result returned by each wizard screen.

    Contract:
    - All screens MUST call dismiss(ScreenResult(...)) when transitioning
    - CONTINUE: User wants to proceed (state contains their selections)
    - BACK: User wants to go back (state contains preserved selections)
    - CANCEL: User wants to abort (state may be None)
    """
    action: NavigationAction
    state: Optional['GuidedSetupState'] = None

@dataclass
class DeduplicatedServer:
    """Represents a unique server after deduplication.

    Attributes:
        server: The detected server (may have renamed name)
        client_names: Display names of clients using this server
        is_shared: True if multiple clients use identical config
        was_renamed: True if name was changed due to conflict
        original_name: Original name before conflict resolution
    """
    server: DetectedServer
    client_names: List[str]  # e.g., ["Claude Desktop", "Codex"]
    is_shared: bool
    was_renamed: bool
    original_name: Optional[str] = None

@dataclass
class GuidedSetupState:
    """Wizard state that flows through all screens.

    Lifecycle:
    1. DiscoveryScreen: Populates detected_clients, deduplicated_servers
    2. ServerSelectionScreen: User modifies selected_server_names
    3. ClientMigrationScreen: User modifies selected_client_types
    4. ConfigurationSummaryScreen: User sets config_path, restore_dir, generate_restore
    5. SetupActionsScreen: Reads all fields to generate files
    6. SetupCompleteScreen: Displays results
    """
    # Populated by DiscoveryScreen
    detected_clients: List[DetectedClient] = field(default_factory=list)
    deduplicated_servers: List[DeduplicatedServer] = field(default_factory=list)

    # User selections (modified by ServerSelectionScreen, ClientMigrationScreen)
    selected_server_names: Set[str] = field(default_factory=set)
    selected_client_types: Set[ClientType] = field(default_factory=set)

    # File paths (set by ConfigurationSummaryScreen)
    config_path: Optional[Path] = None
    restore_dir: Optional[Path] = None
    generate_restore: bool = False

    # Results (populated by SetupActionsScreen)
    created_files: List[Path] = field(default_factory=list)
    generation_errors: List[str] = field(default_factory=list)

    def update_deduplicated_servers(
        self,
        new_servers: List[DeduplicatedServer],
        new_clients: List[DetectedClient]
    ) -> None:
        """Update after rescan, preserving user intent.

        Smart reconciliation:
        - Removes selections for servers/clients that no longer exist
        - Auto-selects NEWLY discovered servers/clients
        - Preserves user's intentional deselections

        Example:
            Initial: A, B, C all selected
            User unchecks B
            Rescan adds D
            Result: A, C, D selected (B stays unchecked)
        """
        # Capture old state
        old_server_names = {s.server.name for s in self.deduplicated_servers}
        old_client_types = {c.client_type for c in self.detected_clients}

        # Update data
        self.deduplicated_servers = new_servers
        self.detected_clients = new_clients

        # Reconcile servers
        valid_server_names = {s.server.name for s in new_servers}
        newly_discovered = valid_server_names - old_server_names

        self.selected_server_names = (
            (self.selected_server_names & valid_server_names)  # Keep valid selections
            | newly_discovered  # Auto-select new servers
        )

        # Reconcile clients (identical logic)
        valid_client_types = {c.client_type for c in new_clients}
        newly_detected = valid_client_types - old_client_types

        self.selected_client_types = (
            (self.selected_client_types & valid_client_types)
            | newly_detected
        )

    def get_selected_servers(self) -> List[DeduplicatedServer]:
        """Get deduplicated servers that user selected."""
        return [
            ds for ds in self.deduplicated_servers
            if ds.server.name in self.selected_server_names
        ]

    def get_selected_clients(self) -> List[DetectedClient]:
        """Get clients that user selected for migration."""
        return [
            c for c in self.detected_clients
            if c.client_type in self.selected_client_types
        ]
```

**Testing**:
- Unit test for `update_deduplicated_servers()` with scenarios from UX spec
- Test `get_selected_servers()` and `get_selected_clients()` filtering

#### Task 1.2: Server Deduplication Logic
**New File**: `gatekit/tui/guided_setup/deduplication.py`

**Implementation**:

```python
"""Server deduplication with conflict resolution."""

import hashlib
from pathlib import Path
from typing import List, Set

from .models import DetectedClient, DetectedServer, DeduplicatedServer


def _get_client_suffix(client_type: str) -> str:
    """Get short suffix for client type.

    Args:
        client_type: ClientType enum value (e.g., 'claude_desktop')

    Returns:
        Short suffix (e.g., 'desktop')
    """
    suffixes = {
        "claude_desktop": "desktop",
        "claude_code": "code",
        "codex": "codex",
    }
    return suffixes.get(client_type, client_type.replace("_", "-"))


def _generate_unique_name(
    server: DetectedServer,
    client_type: str,
    config_path: Path,
    used_names: Set[str],
    base_name: str
) -> str:
    """Generate unique name for conflicting server.

    Strategy: base-name + client-suffix + scope + config-hash + increment

    Args:
        server: Server being renamed
        client_type: Client type string
        config_path: Path to client config file
        used_names: Already-used names
        base_name: Original server name

    Returns:
        Unique server name
    """
    parts = [base_name, _get_client_suffix(client_type)]

    # Add scope if available (Claude Code only)
    if server.scope:
        parts.append(server.scope.value)

    # Add config path hash for multi-profile disambiguation
    path_hash = hashlib.sha256(str(config_path).encode()).hexdigest()[:6]
    parts.append(path_hash)

    candidate = "-".join(parts)

    # Add numeric suffix if still not unique
    if candidate not in used_names:
        return candidate

    counter = 1
    while f"{candidate}-{counter}" in used_names:
        counter += 1

    return f"{candidate}-{counter}"


def deduplicate_servers(
    detected_clients: List[DetectedClient]
) -> List[DeduplicatedServer]:
    """Deduplicate servers across all clients.

    Process:
    1. Collect all servers with (server, client_type, config_path) tuples
    2. Group by complete key: (name, transport, command, url, env, scope)
    3. Deduplicate client names within each group
    4. Identify name conflicts (same name, different config)
    5. Resolve conflicts with unique naming
    6. Return flat list with metadata

    Args:
        detected_clients: All detected clients

    Returns:
        Deduplicated servers with provenance metadata
    """
    # Collect all servers
    all_servers = []
    for client in detected_clients:
        for server in client.servers:
            all_servers.append((
                server,
                client.client_type.value,
                client.config_path
            ))

    # Group identical servers
    server_groups = {}
    for server, client_name, config_path in all_servers:
        # COMPLETE deduplication key
        key = (
            server.name,
            server.transport,
            tuple(server.command) if server.command else None,
            server.url,
            frozenset(server.env.items()) if server.env else frozenset(),
            server.scope,
        )

        if key not in server_groups:
            server_groups[key] = {
                'server': server,
                'clients': [],
                'config_paths': []
            }

        server_groups[key]['clients'].append(client_name)
        server_groups[key]['config_paths'].append(config_path)

    # Deduplicate client lists
    for group in server_groups.values():
        group['clients'] = list(dict.fromkeys(group['clients']))

    # Find name conflicts
    name_to_groups = {}
    for key, group in server_groups.items():
        name = key[0]  # First element is server name
        if name not in name_to_groups:
            name_to_groups[name] = []
        name_to_groups[name].append((key, group))

    conflicts = {
        name: groups
        for name, groups in name_to_groups.items()
        if len(groups) > 1
    }

    # Build result with unique names
    result = []
    used_names: Set[str] = set()

    for key, group in server_groups.items():
        server = group['server']
        clients = group['clients']
        config_paths = group['config_paths']
        original_name = server.name

        # Resolve conflicts
        if server.name in conflicts:
            new_name = _generate_unique_name(
                server,
                clients[0],
                config_paths[0],
                used_names,
                original_name
            )

            # Create new server with updated name
            server = DetectedServer(
                name=new_name,
                transport=server.transport,
                command=server.command,
                url=server.url,
                env=server.env,
                scope=server.scope,
                raw_config=server.raw_config,
            )
            was_renamed = True
        else:
            was_renamed = False

        used_names.add(server.name)

        result.append(DeduplicatedServer(
            server=server,
            client_names=clients,
            is_shared=len(clients) > 1,
            was_renamed=was_renamed,
            original_name=original_name if was_renamed else None,
        ))

    return result
```

**Testing**:
- Test identical servers merge correctly
- Test name conflicts resolve with unique suffixes
- Test client name deduplication
- Test complete deduplication key (transport, scope, env)

#### Task 1.3: Environment Variable Consolidation
**File**: `gatekit/tui/guided_setup/config_generation.py`

**Add Functions**:

```python
def _mask_env_value(key: str, value: str) -> str:
    """Mask sensitive environment variable values.

    Shows last 4 characters, masks rest.

    Args:
        key: Environment variable name
        value: Environment variable value

    Returns:
        Masked value like "********abc1"
    """
    if len(value) <= 4:
        return "********"
    return f"********{value[-4:]}"


def _collect_all_env_vars(
    servers: List[DetectedServer]
) -> tuple[dict[str, str], list[str]]:
    """Collect environment variables from servers.

    Detects conflicts (same key, different values).
    Last server's value wins (deterministic if servers sorted by name).

    Args:
        servers: Detected servers (should be sorted by name)

    Returns:
        (merged_env_vars, conflict_warnings)
    """
    all_env_vars = {}
    conflicts = []
    env_sources = {}

    for server in servers:
        if server.has_env_vars():
            for key, value in server.env.items():
                if key in all_env_vars and all_env_vars[key] != value:
                    # Conflict detected
                    masked_existing = _mask_env_value(key, all_env_vars[key])
                    masked_new = _mask_env_value(key, value)
                    conflicts.append(
                        f"Environment variable '{key}' has different values:\n"
                        f"  • {env_sources[key]}: {masked_existing}\n"
                        f"  • {server.name}: {masked_new}\n"
                        f"  Using value from {server.name}"
                    )

                all_env_vars[key] = value
                env_sources[key] = server.name

    return all_env_vars, conflicts
```

**Usage**: Integration in migration instruction generation (Task 3.3)

---

### Phase 2: Screen Implementations (12-16 hours)

**TDD Note**: Hybrid approach - copy existing test, update to new contract, write new tests for button handlers, implement screen, delete old test.

#### Task 2.1: Discovery Screen
**New File**: `gatekit/tui/screens/guided_setup/discovery.py`

**Features**:
- Animated progress bars for each client type
- Real-time updates as detection progresses
- Display found configs with paths
- Show parse errors (expandable)
- HTTP server visibility (informational)
- Rescan button
- Auto-transition when complete

**Key Components**:
```python
class DiscoveryScreen(Screen[ScreenResult]):
    """Screen 1: Detect MCP clients and servers.

    Contract:
    - Accepts optional GuidedSetupState (for rescan scenarios)
    - Returns ScreenResult with action and updated state
    - Calls dismiss(ScreenResult(...)) when transitioning
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, state: Optional[GuidedSetupState] = None):
        super().__init__()
        # Use provided state or create new one
        self.state = state or GuidedSetupState()
        self.scanning = False

    def compose(self) -> ComposeResult:
        """Build UI with progress bars for each client type."""
        yield Header()

        with VerticalScroll():
            yield Static("Detecting MCP Clients", classes="screen-title")
            yield Static("Scanning your system for MCP client configurations...")

            # Progress container
            with Container(id="progress_container"):
                # Create progress widget for each client type
                for client_type in [ClientType.CLAUDE_DESKTOP, ClientType.CLAUDE_CODE, ClientType.CODEX]:
                    yield ClientProgress(client_type)

            # Summary stats
            with Container(id="summary_stats"):
                yield Static("", id="found_summary")

            # Results container (hidden until scan complete)
            with Container(id="results_container", classes="hidden"):
                yield ClientResults()

            # Action buttons
            with Horizontal(id="action_buttons"):
                yield Button("Cancel", id="cancel_button")
                yield Button("Continue to Server Selection", id="continue_button", classes="hidden")
                yield Button("Rescan", id="rescan_button", classes="hidden")

        yield Footer()

    async def on_mount(self) -> None:
        """Start detection when screen mounts."""
        await self.run_detection()

    async def run_detection(self) -> None:
        """Run client detection and update UI in real-time.

        Uses state.update_deduplicated_servers() to preserve existing
        selections when rescanning (see lines 98-140 in models.py).
        """
        # Run detection
        detected_clients = await detect_all_clients()
        deduplicated_servers = deduplicate_servers(detected_clients)

        # Update state while preserving user selections (smart reconciliation)
        self.state.update_deduplicated_servers(deduplicated_servers, detected_clients)

        # Update UI...

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses and dismiss with explicit ScreenResult.

        Note: rescan_button triggers async work, so we schedule it with call_later.
        """
        if event.button.id == "continue_button":
            self.dismiss(ScreenResult(
                action=NavigationAction.CONTINUE,
                state=self.state
            ))
        elif event.button.id == "cancel_button":
            self.dismiss(ScreenResult(
                action=NavigationAction.CANCEL,
                state=None
            ))
        elif event.button.id == "rescan_button":
            # Rescan preserves selections via update_deduplicated_servers()
            # Schedule async work - don't await in sync handler
            self.run_worker(self.run_detection())
```

**UI Widgets**:
- `ClientProgress` - Progress bar + status for one client type
- `ClientResults` - Display of detected servers per client
- `ErrorDetails` - Collapsible parse error display

**Dependencies**:
- Reuse existing detection logic from `gatekit/tui/guided_setup/detection.py`
- Add `deduplicate_servers()` call after detection completes

#### Task 2.2: Server Selection Screen
**New File**: `gatekit/tui/screens/guided_setup/server_selection.py`

**Features**:
- Scrollable list of deduplicated servers
- Checkbox for each server (all checked by default)
- Server details (command, provenance)
- Conflict resolution callout
- Select All/None buttons
- Status footer showing selection count

**Implementation**:
```python
class ServerSelectionScreen(Screen[ScreenResult]):
    """Screen 2: Let user choose which servers to manage.

    Contract:
    - Requires GuidedSetupState from DiscoveryScreen
    - Returns ScreenResult with action and updated state
    - Calls dismiss(ScreenResult(...)) when transitioning
    """

    def __init__(self, state: GuidedSetupState):
        super().__init__()
        self.state = state
        # Initialize selected_server_names if empty
        if not self.state.selected_server_names:
            self.state.selected_server_names = {
                ds.server.name
                for ds in self.state.deduplicated_servers
            }

    def compose(self) -> ComposeResult:
        yield Header()

        with VerticalScroll():
            yield Static("Select Servers to Manage", classes="screen-title")

            # Conflict warning if any servers were renamed
            if any(ds.was_renamed for ds in self.state.deduplicated_servers):
                yield ConflictWarning()

            # Server list with checkboxes
            with Container(id="server_list"):
                for dedupe_server in self.state.deduplicated_servers:
                    yield ServerCheckbox(dedupe_server, checked=dedupe_server.server.name in self.state.selected_server_names)

            # Selection summary
            yield SelectionSummary()

            # Action buttons
            with Horizontal(id="action_buttons"):
                yield Button("Select All", id="select_all")
                yield Button("Select None", id="select_none")
                yield Button("Continue", id="continue", variant="primary")
                yield Button("Back", id="back")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses and dismiss with explicit ScreenResult."""
        if event.button.id == "select_all":
            self.state.selected_server_names = {ds.server.name for ds in self.state.deduplicated_servers}
            self.refresh_checkboxes()
        elif event.button.id == "select_none":
            self.state.selected_server_names.clear()
            self.refresh_checkboxes()
        elif event.button.id == "continue":
            self.dismiss(ScreenResult(
                action=NavigationAction.CONTINUE,
                state=self.state
            ))
        elif event.button.id == "back":
            self.dismiss(ScreenResult(
                action=NavigationAction.BACK,
                state=self.state  # Preserve selections
            ))
```

**UI Widgets**:
- `ServerCheckbox` - Checkbox + server details widget
- `ConflictWarning` - Callout box explaining renamed servers
- `SelectionSummary` - Footer showing "X servers selected"

#### Task 2.3: Client Migration Selection Screen
**New File**: `gatekit/tui/screens/guided_setup/client_migration.py`

**Features**:
- List of detected clients
- Checkboxes (all checked by default)
- Server breakdown per client
- Security messaging
- Clear explanation of manual migration

**Implementation**: Similar structure to ServerSelectionScreen

**Screen Contract**:
```python
class ClientMigrationScreen(Screen[ScreenResult]):
    """Screen 3: Select clients to migrate.

    Contract:
    - Requires GuidedSetupState from ServerSelectionScreen
    - Returns ScreenResult with action and updated state
    - Supports CONTINUE, BACK, and CANCEL actions
    """

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses and dismiss with explicit ScreenResult."""
        if event.button.id == "continue":
            self.dismiss(ScreenResult(action=NavigationAction.CONTINUE, state=self.state))
        elif event.button.id == "back":
            self.dismiss(ScreenResult(action=NavigationAction.BACK, state=self.state))
        elif event.button.id == "cancel":
            self.dismiss(ScreenResult(action=NavigationAction.CANCEL, state=None))
```

#### Task 2.4: Configuration Summary Screen
**New File**: `gatekit/tui/screens/guided_setup/config_summary.py`

**Features**:
- Preview of Gatekit config (server list, plugins)
- Client update summary
- Environment variable conflict display (expandable)
- File path inputs with Browse buttons
- Generate restore scripts checkbox
- Generate & Apply button

**Key Elements**:
```python
class ConfigurationSummaryScreen(Screen[ScreenResult]):
    """Screen 4: Review configuration and set file paths.

    Contract:
    - Requires GuidedSetupState from ClientMigrationScreen
    - Returns ScreenResult with action and updated state
    - Sets config_path, restore_dir, generate_restore in state
    """

    def __init__(self, state: GuidedSetupState):
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Header()

        with VerticalScroll():
            yield Static("Review Configuration", classes="screen-title")

            # Gatekit config preview
            with Container(id="config_preview"):
                yield ConfigPreview(self.state)

            # Client update summary
            with Container(id="client_summary"):
                yield ClientUpdateSummary(self.state)
                # Env var conflicts if any
                selected_servers = self.state.get_selected_servers()
                env_vars, conflicts = _collect_all_env_vars([ds.server for ds in selected_servers])
                if conflicts:
                    yield EnvVarConflicts(conflicts)

            # File path inputs
            with Container(id="file_paths"):
                yield Static("Save Locations:")
                yield Input(
                    value="configs/gatekit.yaml",
                    id="config_path_input",
                    placeholder="Gatekit config path"
                )
                yield Button("Browse...", id="browse_config")

                yield Checkbox("Generate restore scripts", id="restore_checkbox", value=False)
                yield Input(
                    value=str(Path.home() / "Documents" / "gatekit-restore"),
                    id="restore_path_input",
                    placeholder="Restore scripts directory"
                )
                yield Button("Browse...", id="browse_restore")

            # Action buttons
            with Horizontal(id="action_buttons"):
                yield Button("Generate & Apply", id="generate", variant="primary")
                yield Button("Back", id="back")
                yield Button("Cancel", id="cancel")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses and dismiss with explicit ScreenResult."""
        if event.button.id == "generate":
            # Capture file paths from inputs
            self.state.config_path = Path(self.query_one("#config_path_input").value)
            self.state.restore_dir = Path(self.query_one("#restore_path_input").value)
            self.state.generate_restore = self.query_one("#restore_checkbox").value

            self.dismiss(ScreenResult(action=NavigationAction.CONTINUE, state=self.state))
        elif event.button.id == "back":
            self.dismiss(ScreenResult(action=NavigationAction.BACK, state=self.state))
        elif event.button.id == "cancel":
            self.dismiss(ScreenResult(action=NavigationAction.CANCEL, state=None))
```

#### Task 2.5: Setup Actions Screen
**New File**: `gatekit/tui/screens/guided_setup/setup_actions.py`

**Features**:
- Progress indicators for each file operation
- Real-time status updates
- Checkmarks as operations complete
- Error handling with recovery options
- Auto-advance when complete

**Screen Contract**:
```python
class SetupActionsScreen(Screen[ScreenResult]):
    """Screen 5: Execute file generation operations.

    Contract:
    - Requires GuidedSetupState from ConfigurationSummaryScreen
    - Returns ScreenResult with CONTINUE action (no BACK support)
    - Populates state.created_files and state.generation_errors
    - Auto-advances when complete (no user interaction needed)
    """

    def __init__(self, state: GuidedSetupState):
        super().__init__()
        self.state = state

    async def on_mount(self) -> None:
        """Start file generation when screen mounts."""
        await self.generate_files()
        # Auto-advance when done
        self.dismiss(ScreenResult(action=NavigationAction.CONTINUE, state=self.state))
```

**Atomic File Operations**:
```python
async def _create_gatekit_config(self, config_path: Path, config_content: str) -> bool:
    """Create config with atomic write operation.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Write to temp file first
        with tempfile.NamedTemporaryFile(
            mode='w',
            delete=False,
            suffix='.yaml',
            dir=config_path.parent
        ) as tmp:
            tmp.write(config_content)
            tmp_path = Path(tmp.name)

        # Atomic move to final location
        tmp_path.replace(config_path)

        self.state.created_files.append(config_path)
        return True

    except Exception as exc:
        self.state.generation_errors.append(f"Failed to create {config_path}: {exc}")
        # Cleanup temp file if exists
        if tmp_path.exists():
            tmp_path.unlink()
        return False
```

**Error Recovery**: If any operation fails, show modal with options:
- Retry
- Change Path
- Skip This File
- Cancel Setup (cleanup all created files)

#### Task 2.6: Update Setup Complete Screen
**File**: `gatekit/tui/screens/setup_complete.py`

**Changes**:
- Add expandable migration instructions per client
- Improve organization of file paths
- Add [Copy Path] buttons
- Better visual hierarchy
- Update to return ScreenResult (required by WizardNavigator)

**Implementation**:
```python
class SetupCompleteScreen(Screen[ScreenResult]):
    """Screen 6: Display setup completion and next steps.

    Contract:
    - Requires GuidedSetupState from SetupActionsScreen
    - Returns ScreenResult with CONTINUE action (Done button)
    - No BACK support (setup is complete, can't undo)
    - CONTINUE indicates user has acknowledged completion
    """

    def __init__(self, state: GuidedSetupState):
        super().__init__()
        self.state = state

    def compose(self) -> ComposeResult:
        yield Header()

        with VerticalScroll():
            yield Static("Setup Complete", classes="screen-title")
            yield Static("✅ Gatekit has been successfully configured")

            # What was done summary
            with Container(id="summary"):
                yield WhatWasDone(self.state)

            # Next steps
            with Container(id="next_steps"):
                yield NextSteps(self.state)

            # Migration instructions (expandable per client)
            with Container(id="migration_instructions"):
                for client in self.state.get_selected_clients():
                    yield ExpandableMigrationInstructions(client, self.state)

            # Done button
            yield Button("Done", id="done", variant="primary")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses and dismiss with explicit ScreenResult."""
        if event.button.id == "done":
            # CONTINUE indicates user has acknowledged completion
            # (not CANCEL - setup was successful)
            self.dismiss(ScreenResult(
                action=NavigationAction.CONTINUE,
                state=self.state
            ))
```

**Navigation Note**: The "Done" button returns `CONTINUE` rather than `CANCEL` because:
- Setup completed successfully (not cancelled)
- WizardNavigator expects a return value
- Semantically, user is "continuing" out of the wizard (acknowledging completion)
- If we add a future "Close" button, it could return `CANCEL` to signal early exit

---

### Phase 3: Navigation & Integration (4-6 hours)

**TDD Note**: Pure TDD - write tests FIRST for WizardNavigator (forward, back, cancel, state preservation), then implement.

#### Task 3.1: Screen Navigation Flow
**New File**: `gatekit/tui/screens/guided_setup/__init__.py`

**Flow Manager with Back Navigation Support**:

The naive implementation of back navigation requires deeply nested loops. Instead, we use a clean index-based approach with a helper class:

```python
from typing import List, Optional, Type
from textual.app import App
from textual.screen import Screen
from pathlib import Path

from .models import GuidedSetupState, NavigationAction, ScreenResult
from .discovery import DiscoveryScreen
from .server_selection import ServerSelectionScreen
from .client_migration import ClientMigrationScreen
from .config_summary import ConfigurationSummaryScreen
from .setup_actions import SetupActionsScreen
from ..setup_complete import SetupCompleteScreen


class WizardNavigator:
    """Helper class to manage wizard screen navigation with back support.

    Provides clean index-based navigation through a sequence of screens,
    handling BACK/CONTINUE/CANCEL actions automatically.
    """

    def __init__(self, app: App):
        self.app = app
        self.state = GuidedSetupState()

    async def navigate_to(self, screen_class: Type[Screen]) -> NavigationAction:
        """Navigate to a screen and return the user's action.

        Args:
            screen_class: Screen class to instantiate and show

        Returns:
            The navigation action chosen by the user
        """
        result = await self.app.push_screen_wait(screen_class(self.state))

        # Update state regardless of action (preserves selections on BACK)
        if result.state is not None:
            self.state = result.state

        return result.action

    async def launch(self) -> Optional[Path]:
        """Launch wizard with automatic back navigation.

        Navigation Flow:
        1. Discovery → Server Selection → Client Migration → Config Summary
        2. User can go BACK from any screen (except first)
        3. Setup Actions and Complete screens don't support BACK
        4. State is preserved across all navigation

        Returns:
            Path to created config file, or None if cancelled
        """
        # Define the navigable screens (support BACK/CONTINUE/CANCEL)
        screens = [
            DiscoveryScreen,
            ServerSelectionScreen,
            ClientMigrationScreen,
            ConfigurationSummaryScreen,
        ]

        current_index = 0
        while current_index < len(screens):
            action = await self.navigate_to(screens[current_index])

            if action == NavigationAction.CANCEL:
                return None
            elif action == NavigationAction.BACK:
                current_index -= 1  # Go back one screen
                if current_index < 0:
                    return None  # Can't go back from first screen, treat as cancel
            elif action == NavigationAction.CONTINUE:
                current_index += 1  # Advance to next screen

        # Execute setup actions (no BACK support - operations are executing)
        action = await self.navigate_to(SetupActionsScreen)
        if action == NavigationAction.CANCEL:
            return None

        # Show completion screen (no BACK support - setup is done)
        await self.navigate_to(SetupCompleteScreen)

        return self.state.config_path


async def launch_guided_setup(app: App) -> Optional[Path]:
    """Launch guided setup wizard.

    Entry point for the guided setup flow. Creates a WizardNavigator
    and delegates to its launch() method.

    Args:
        app: The Textual app instance

    Returns:
        Path to created config file, or None if cancelled
    """
    navigator = WizardNavigator(app)
    return await navigator.launch()
```

#### Task 3.2: Update Welcome Screen
**File**: `gatekit/tui/screens/welcome.py`

**Changes**:
```python
async def on_button_pressed(self, event: Button.Pressed) -> None:
    if event.button.id == "guided_setup":
        from .guided_setup import launch_guided_setup
        config_path = await launch_guided_setup(self.app)
        if config_path:
            # User completed setup, load the config
            self.dismiss(str(config_path))
```

#### Task 3.3: Update Migration Instructions Generation
**File**: `gatekit/tui/guided_setup/migration_instructions.py`

**Add env var consolidation**:
```python
def _generate_claude_desktop_instructions(
    client: DetectedClient,
    selected_servers: List[DetectedServer],
    gatekit_gateway_path: Path,
    gatekit_config_path: Path,
) -> MigrationInstructions:
    """Generate Claude Desktop migration instructions with env vars."""

    # Sort servers by name for deterministic env var collection
    servers_sorted = sorted(selected_servers, key=lambda s: s.name)

    # Collect env vars and detect conflicts
    all_env_vars, env_conflicts = _collect_all_env_vars(servers_sorted)

    # Build gatekit entry
    gatekit_entry = {
        "gatekit": {
            "command": str(gatekit_gateway_path),
            "args": ["--config", str(gatekit_config_path)],
        }
    }

    if all_env_vars:
        gatekit_entry["gatekit"]["env"] = all_env_vars

    # Generate JSON snippet
    snippet = json.dumps(gatekit_entry, indent=2)

    # Build instructions with conflict warnings
    instructions = f"""
Update Claude Desktop Configuration

1. Open your config file:
   {client.config_path}

2. Remove these servers from mcpServers:
{chr(10).join(f"   - {s.name}" for s in selected_servers)}

3. Add this to your mcpServers section:

{snippet}

4. Restart Claude Desktop
"""

    if env_conflicts:
        warning = "\n⚠️ Environment Variable Conflicts:\n"
        warning += "\n".join(env_conflicts)
        instructions = warning + "\n" + instructions

    return MigrationInstructions(
        client_type=client.client_type,
        snippet=snippet,
        instructions=instructions,
        has_conflicts=bool(env_conflicts)
    )
```

---

### Phase 4: Testing & Validation (6-8 hours)

**Status**: ⚠️ **PARTIALLY COMPLETE** - Core tests pass, integration tests and coverage targets need work

**TDD Note**: This phase is primarily validation and cleanup - most tests were written during Phases 1-3. Focus on integration tests and removing `@pytest.mark.legacy` tests.

#### Task 4.1: Unit Tests Validation

**Validation Tasks**:
1. ✅ Verify all Phase 1 unit tests exist and pass (227 tests)
2. ✅ Verify all Phase 2 screen tests exist and pass
3. ✅ Remove all `@pytest.mark.legacy` tests (none found)
4. ✅ Run: `pytest tests/unit/test_guided_setup*.py -v` (all 227 pass)
5. ⚠️ **Coverage analysis shows gaps** - see actual numbers below

**Actual Test Files** (all exist and pass):
- ✅ `tests/unit/test_guided_setup_models.py` - 13 tests
- ✅ `tests/unit/test_guided_setup_deduplication.py` - 9 tests
- ✅ `tests/unit/test_guided_setup_env_consolidation.py` - 8 tests
- ✅ `tests/unit/test_guided_setup_discovery_screen.py` - 7 tests
- ✅ `tests/unit/test_guided_setup_server_selection_screen.py` - 8 tests
- ✅ `tests/unit/test_guided_setup_client_migration_screen.py` - 9 tests
- ✅ `tests/unit/test_guided_setup_config_summary_screen.py` - 9 tests
- ✅ `tests/unit/test_guided_setup_setup_actions_screen.py` - 12 tests (note: setup_actions vs expected actions)
- ✅ `tests/unit/test_guided_setup_setup_complete_screen.py` - 10 tests
- ✅ `tests/unit/test_guided_setup_wizard_navigator.py` - 11 tests (navigation integration)

**Actual Coverage Numbers** (from `pytest --cov=gatekit --cov-report=term tests/`):

**Overall Gatekit Coverage: 57%** (15,470 statements, 6,707 missed)

**Guided Setup Module Coverage:**
- ✅ `wizard_navigator.py`: **100%** - Perfect
- ✅ `models.py`: **97%** - Excellent
- ✅ `connection_testing.py`: **98%** - Excellent
- ✅ `restore_scripts.py`: **97%** - Excellent (was 60% in isolated run)
- ✅ `gateway.py`: **96%** - Excellent (was 26% in isolated run)
- ✅ `error_handling.py`: **95%** - Excellent
- ✅ `deduplication.py`: **94%** - Excellent
- ✅ `config_generation.py`: **92%** - Excellent
- ✅ `migration_instructions.py`: **92%** - Excellent
- ✅ `parsers.py`: **89%** - Good (was 64% in isolated run)
- ⚠️ `detection.py`: **81%** - Acceptable

**Screen Coverage** (UI composition code - harder to unit test):
- ⚠️ `setup_actions.py`: **55%** - UI-heavy
- ⚠️ `client_migration.py`: **52%** - UI-heavy
- ⚠️ `server_selection.py`: **46%** - UI-heavy
- ⚠️ `config_summary.py`: **40%** - UI-heavy
- ⚠️ `discovery.py`: **38%** - UI-heavy
- ✅ `__init__.py`: **85%** - Good

**Analysis**:
- **Core business logic has excellent coverage** (89-100%) - this is what matters
- **Screen UI code** has lower coverage (38-55%) because it's Textual composition code
- The critical state management, navigation, and data processing logic IS well tested
- **Overall 57% is accurate** but misleading - core logic is well covered, UI rendering is not

#### Task 4.2: Integration Tests

**Status**: ⚠️ **FILE CREATED, TESTS NEED IMPLEMENTATION**

**Test File**: ✅ `tests/integration/test_guided_setup_flow.py` (created)

**Test Scenarios** (placeholders exist, need full implementation):
1. ⚠️ Complete happy path (Claude Desktop only) - stub created
2. ⚠️ Multi-client scenario (Desktop + Code) - stub created
3. ⚠️ Name conflict resolution - stub created
4. ⚠️ Environment variable conflicts - stub created
5. ⚠️ Parse errors and recovery - partial setup
6. ⚠️ Rescan with selection preservation - stub created
7. ⚠️ HTTP server visibility - stub created
8. ⚠️ Back navigation preservation - stub created
9. ⚠️ Cancel at each screen - stub created
10. ⚠️ Atomic file operations - stub created

**Implementation Note**: These integration tests require:
- Mocking `get_default_config_paths()` to use test fixtures
- Running wizard with test Textual app instance
- Simulating user interactions (button clicks, navigation)
- Verifying file generation and state preservation

**Mock Strategy**:
- ✅ Helper functions created: `create_fake_claude_desktop_config()`, `create_fake_claude_code_config()`
- ⚠️ Detection mocking needs implementation
- ⚠️ User interaction simulation needs implementation
- ⚠️ Assertions need implementation

**Example Test**:
```python
@pytest.mark.asyncio
async def test_back_navigation_preserves_selections(tmp_path):
    """User can go back and forth without losing selections."""
    # Setup: Create fake client configs
    config = create_fake_claude_desktop_config(tmp_path, ["server-a", "server-b"])

    # Run wizard
    app = create_test_app()
    navigator = WizardNavigator(app)

    # 1. Discovery screen - continue
    # 2. Server selection - deselect server-b, continue
    # 3. Client migration - go BACK
    # 4. Server selection - verify server-b still deselected, continue
    # 5. Client migration - continue
    # Assert: server-b was not included in final config
```

#### Task 4.3: Cleanup and Validation

**Status**: ✅ **COMPLETE**

**Tasks**:
1. ✅ Remove all files with `@pytest.mark.legacy` decorator - **None found**
2. ✅ Update any imports in other test files - **N/A**
3. ✅ Run full test suite: `pytest tests/ -v` - **2,062 tests pass**
4. ✅ Verify no regressions in other modules - **All tests pass**
5. ✅ Run linting: `uv run ruff check gatekit` - **All checks pass** (after fixing 18 errors)
6. ✅ Run linting on tests: `uv run ruff check tests/unit/test_guided_setup*.py` - **All checks pass**
7. ✅ Verify all tests pass: `pytest tests/ --tb=short` - **2,062 tests pass in 73.82s**
8. ✅ Check coverage: `pytest --cov=gatekit tests/` - **57% overall, core logic 89-100%**

**Linting Fixes Applied**:
- Fixed 12 unused import errors (auto-fixed with `--fix`)
- Fixed 6 unused variable errors (renamed to `_screen` prefix)
- Files fixed:
  - `test_guided_setup_client_migration_screen.py`
  - `test_guided_setup_config_summary_screen.py`
  - `test_guided_setup_deduplication.py`
  - `test_guided_setup_discovery_screen.py`
  - `test_guided_setup_env_consolidation.py`
  - `test_guided_setup_migration_instructions_state.py`
  - `test_guided_setup_models.py`
  - `test_guided_setup_server_selection_screen.py`
  - `test_guided_setup_setup_actions_screen.py`
  - `test_guided_setup_wizard_navigator.py`

**Legacy Tests**:
- Search: `git grep "@pytest.mark.legacy" tests/` - **No results**
- No legacy tests to remove

---

## Phase 4 Summary

**Overall Status**: ⚠️ **PARTIALLY COMPLETE**

**What's Done**:
- ✅ All 227 unit tests exist and pass
- ✅ Core business logic has excellent coverage (89-100%)
- ✅ No legacy tests remain
- ✅ All linting issues resolved
- ✅ Full test suite passes (2,062 tests)
- ✅ Integration test file created with scaffolding

**What Needs Work**:
- ⚠️ **Screen UI coverage is low** (38-55%) - Textual composition code is hard to unit test
- ⚠️ **Integration tests are stubs** - `test_guided_setup_flow.py` has placeholders but needs full implementation
- ⚠️ **Overall coverage is 57%**, not 85% - But this is because UI rendering code is untested

**Decision Point**: Accept current state or invest in UI testing?

**Option A: Accept Current State** (RECOMMENDED)
- Core business logic has excellent coverage (what matters for correctness)
- Screen rendering is difficult to test without full Textual app integration
- Integration tests would require significant mocking infrastructure
- **Risk**: Low - business logic is well tested, UI bugs would be caught manually

**Option B: Invest in UI Testing**
- Implement full integration tests with Textual Pilot
- Add more unit tests for screen rendering logic
- Extract presenters/view models for easier testing
- **Effort**: 8-12 additional hours
- **Benefit**: Higher coverage numbers, more confidence in UI behavior

**Recommendation**: Accept Option A. The core logic is production-ready with excellent coverage. Screen UI testing would require disproportionate effort for marginal benefit.

---

## Dependencies & Ordering

### Critical Path
1. **Phase 1** (data models, deduplication) → Foundation for all screens
2. **Phase 2.1** (Discovery Screen) → Entry point, must work first
3. **Phase 2.2-2.5** (Other screens) → Can be parallel after Phase 1
4. **Phase 2.6** (Setup Complete updates) → Depends on env var consolidation
5. **Phase 3** (Navigation) → Integrates all screens
6. **Phase 4** (Testing) → Throughout, but comprehensive pass at end

### Parallelizable Work
- Screens 2.2, 2.3, 2.4 can be developed in parallel after Phase 1 completes
- Unit tests can be written alongside implementation
- UI polish can happen while core logic is being tested

---

## Risk Mitigation

### Risk 1: Textual UI Complexity
**Mitigation**:
- Start with simple Static/Container layouts
- Add interactivity incrementally
- Reference existing screens (welcome.py, setup_complete.py) for patterns

### Risk 2: State Management Across Screens
**Mitigation**:
- Use `push_screen_wait()` pattern (blocking, sequential flow)
- State passed explicitly between screens
- Clear ownership: each screen modifies specific fields

### Risk 3: Deduplication Edge Cases
**Mitigation**:
- Comprehensive unit tests covering all UX spec scenarios
- Test with real client configs (Claude Desktop, Claude Code, Codex)
- Manual testing with intentionally conflicting names

### Risk 4: Atomic File Operations
**Mitigation**:
- Use `tempfile` + `Path.replace()` pattern (proven cross-platform)
- Track all created files in state
- Provide cleanup on error
- Test on all platforms (macOS, Linux, Windows)

### Risk 5: Revisiting Discovery After Making Later Selections
**Question**: What happens if user goes back to DiscoveryScreen after configuring servers/clients?

**Resolution**: The `GuidedSetupState.update_deduplicated_servers()` method (lines 98-140) provides smart reconciliation:
- **Removes** selections for servers/clients that no longer exist
- **Auto-selects** newly discovered servers/clients
- **Preserves** user's intentional deselections

**Example Flow**:
1. Discovery finds servers A, B, C (all selected by default)
2. User deselects B in ServerSelectionScreen
3. User selects clients in ClientMigrationScreen
4. User hits BACK to DiscoveryScreen and rescans
5. Rescan finds A, C, D (B is gone, D is new)
6. **Result**: A, C, D are selected (B's deselection is preserved as "intentional")

**Implementation Note**: `DiscoveryScreen.run_detection()` (lines 514-527) calls `state.update_deduplicated_servers()` which handles this reconciliation automatically. No special cleanup needed.

---

## Success Criteria

### Functional
- ✅ All 6 screens implemented and navigable
- ✅ Server deduplication works correctly
- ✅ Environment variable conflicts detected and shown
- ✅ Rescan preserves user selections intelligently
- ✅ File generation uses atomic operations
- ✅ All existing tests pass
- ✅ New tests cover core logic (deduplication, env vars, rescan)

### User Experience
- ✅ Progressive disclosure feels natural
- ✅ User sees value before committing (file paths)
- ✅ Clear messaging about what's happening at each step
- ✅ Errors are recoverable with clear options
- ✅ Back navigation preserves selections

### Code Quality
- ✅ No hardcoded paths or platform-specific code
- ✅ Clear separation of concerns (screens, logic, models)
- ✅ Comprehensive docstrings
- ✅ Follows existing code patterns

---

## Implementation Timeline Estimate

- **Phase 1**: 4-6 hours (data models, deduplication, env vars)
- **Phase 2**: 12-16 hours (6 screens + widgets)
- **Phase 3**: 4-6 hours (navigation, integration)
- **Phase 4**: 6-8 hours (testing)

**Total**: 26-36 hours (~4-5 days full-time, 1-2 weeks part-time)

---

## Next Steps

1. Review this plan for completeness
2. Implement Phase 1 foundation (data models, deduplication)
3. Build screens iteratively (Phase 2)
4. Integrate and test (Phases 3-4)
5. Manual testing on all platforms
6. Documentation updates
