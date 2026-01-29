# Setup Complete Screen: Master-Detail UI Pattern

**Status:** ✅ Completed
**Priority:** High
**Complexity:** Medium (~4-6 hours)

## Overview

Replace the current vertical-scroll instruction display in `SetupCompleteScreen` with a master-detail pattern that improves usability when multiple MCP clients are detected. Add clear file location reminders and special handling for clients already configured to use Gatekit.

## Problem Statement

Current `SetupCompleteScreen` implementation stacks all client instructions vertically, which creates UX issues:

1. **Overwhelming for multiple clients**: Users must scroll through all instructions even if they only care about one client
2. **No file location reminder**: Users don't see where gatekit.yaml and restore scripts were saved after scrolling past the top
3. **No already-configured detection**: Users aren't warned when a client already uses Gatekit, leading to confusion about whether to replace or modify existing configuration
4. **Inconsistent button layout**: Uses "Test All Connections" and "Done" buttons instead of matching wizard pattern
5. **Confusing migration instructions**: Tells users which servers to remove instead of simply replacing the entire mcpServers section

## Requirements

### Functional Requirements

#### FR-1: Master-Detail Layout
- **Master panel (left)**: List of detected clients, width determined by fitting to the longest MCP Client name (plus warning icon if required), capped at 35 cells (Textual cell-based layout used instead of percentage for consistent sizing across terminal widths)
  - Show client display name
  - Show warning icon (⚠️) for already-configured clients
  - Highlight selected client
  - Support arrow key navigation
  - Support click to select
- **Detail panel (right)**: Instructions for selected client, remaining width
  - Show all content for ONE client at a time
  - Scroll only within detail pane if needed
  - Default selection: First client in list

#### FR-2: File Location Reminder
- **Location**: Top of screen, above master-detail split
- **Content**:
  - Gatekit config path with [Copy Path] and [Open] buttons
  - Restore scripts directory (if generated) with [Copy Path] and [Open Folder] buttons
- **Styling**: Compact, non-intrusive, always visible (not scrollable)

#### FR-3: Already-Configured Client Detection
- **Data source**: `state.already_configured_clients: List[DetectedClient]`
- **Master panel indicators**:
  - ⚠️ icon next to client name
  - Different text color/style (e.g., yellow/orange)
- **Detail panel alert**:
  - Prominent alert box at top of instructions
  - Warning icon and clear message
  - Path to client's MCP config file that currently references Gatekit
  - Two clear action paths:
    1. "Follow instructions below to switch to the new Gatekit config" (default instructions)
    2. [Open Existing Config] button to open the client's MCP config file in editor
- **User choice**: Both options available, user decides based on their needs

#### FR-4: Simplified Migration Instructions

**For Claude Desktop (JSON config):**
- Config file path with [Open in Editor] and [Copy Path] buttons
- Simple instruction: "Replace your entire mcpServers section with:"
- JSON snippet in TextArea showing complete new mcpServers object
- [Copy Config Snippet] button
- Helper text: "Select all (Ctrl+A) then copy (Ctrl+C)"
- Restore instructions link (if available)
- Restart reminder

**For Claude Code/Codex (CLI commands):**
- Simple instruction: "Run these commands in your terminal:" (or "PowerShell" on Windows)
- CLI commands in TextArea with bash/PowerShell syntax
- [Copy Commands] button
- Restore instructions link (if available)
- Restart reminder

#### FR-5: Wizard-Consistent Bottom Actions
- **Button layout**: Match other wizard screens (ServerSelectionScreen, ConfigLocationScreen, etc.)
- **Buttons**:
  - [Back] - Return to ConfigurationSummaryScreen
  - [Cancel] - Exit wizard (dismiss with CANCEL action)
  - [Finish] - Complete wizard (dismiss with CONTINUE action)
- **No "Test All Connections" button** - Remove entirely from this screen
- **Layout**: Horizontal layout with Back on left, Cancel and Finish on right
- **Styling**: Consistent with other wizard screens

### Non-Functional Requirements

#### NFR-1: Keyboard Navigation
- `↑`/`↓` - Navigate client list **when focus is in master panel or on buttons**
  - Works immediately on screen mount (first client is auto-focused)
  - Updates selection and detail panel
  - Down arrow on last client moves focus to Back button
  - Up/Down from buttons navigates clients without changing button focus
  - **Arrows work normally in detail panel** (TextArea scrolling, cursor movement, etc.)
- `←`/`→` - Navigate between buttons (Back ← → Cancel ← → Finish)
- Mouse click on client - Select client (via ClientSelected message → `@on()` handler)
- `Escape` - Cancel wizard
- Visual highlight shows currently selected client in master panel

#### NFR-2: Responsive Layout
- Master panel: Dynamic width based on content (fits longest client name + warning icon), capped at 35 cells
- Detail panel: Remaining width (fills rest of container)
- Both panels scroll independently if needed
- File reminder section: Fixed height, always visible at top

#### NFR-3: Visual Consistency
- Use shared wizard styles (if available)
- Match color scheme and typography of other wizard screens
- Consistent button styling and spacing
- Professional, polished appearance

## UI Mockups

### Standard Flow (No Already-Configured Clients)

```
┌──────────────────────────────────────────────────────────────────┐
│ Setup Complete                                           [Header] │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│ ✅ Configuration created successfully                            │
│                                                                   │
│ Gatekit Config: ~/gatekit/gatekit.yaml                     │
│ [Copy Path] [Open]                                               │
│                                                                   │
│ Restore Scripts: ~/gatekit/restore/                            │
│ [Copy Path] [Open Folder]                                        │
│                                                                   │
├─────────────────┬────────────────────────────────────────────────┤
│                 │                                                 │
│ ▶ Claude Desktop│ Update Claude Desktop                          │
│   Claude Code   │                                                 │
│   Codex         │ Config: ~/.config/Claude/claude_desktop_co...  │
│                 │ [Open in Editor] [Copy Path]                   │
│                 │                                                 │
│                 │ Replace your entire mcpServers section with:   │
│                 │                                                 │
│                 │ ┌─────────────────────────────────────────┐   │
│                 │ │ {                                       │   │
│                 │ │   "mcpServers": {                       │   │
│                 │ │     "gatekit": {                      │   │
│                 │ │       "command": "gatekit-gateway",   │   │
│                 │ │       "args": ["--config", "/path/..."] │   │
│                 │ │     }                                    │   │
│                 │ │   }                                      │   │
│                 │ │ }                                        │   │
│                 │ └─────────────────────────────────────────┘   │
│                 │                                                 │
│                 │ Select all (Ctrl+A) then copy (Ctrl+C)         │
│                 │ [Copy Config Snippet]                           │
│                 │                                                 │
│                 │ ⓘ To restore later: ~/gatekit/restore/res... │
│                 │ [Open Restore Instructions]                     │
│                 │                                                 │
│                 │ After updating, restart Claude Desktop          │
│                 │                                                 │
├─────────────────┴────────────────────────────────────────────────┤
│                                                                   │
│ [Back]                                    [Cancel]    [Finish]   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### With Already-Configured Client

```
┌──────────────────────────────────────────────────────────────────┐
│ Setup Complete                                           [Header] │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│ ✅ Configuration created successfully                            │
│                                                                   │
│ Gatekit Config: ~/gatekit/gatekit.yaml                     │
│ [Copy Path] [Open]                                               │
│                                                                   │
│ Restore Scripts: ~/gatekit/restore/                            │
│ [Copy Path] [Open Folder]                                        │
│                                                                   │
├─────────────────┬────────────────────────────────────────────────┤
│                 │                                                 │
│ ▶ ⚠️ Claude Desktop│ Update Claude Desktop                          │
│   Claude Code   │                                                 │
│   Codex         │ ┌─────────────────────────────────────────────┐│
│                 │ │ ⚠️  Already Using Gatekit                 ││
│                 │ │                                             ││
│                 │ │ This client is currently configured to use  ││
│                 │ │ Gatekit via:                              ││
│                 │ │ ~/.config/Claude/claude_desktop_config.json ││
│                 │ │                                             ││
│                 │ │ You can:                                    ││
│                 │ │ 1. Follow instructions below to switch to   ││
│                 │ │    the new Gatekit config, OR             ││
│                 │ │ 2. [Open Existing Config] to modify the     ││
│                 │ │    active configuration instead             ││
│                 │ └─────────────────────────────────────────────┘│
│                 │                                                 │
│                 │ Config: ~/.config/Claude/claude_desktop_co...  │
│                 │ [Open in Editor] [Copy Path]                   │
│                 │                                                 │
│                 │ Replace your entire mcpServers section with:   │
│                 │                                                 │
│                 │ ┌─────────────────────────────────────────┐   │
│                 │ │ {                                       │   │
│                 │ │   "mcpServers": {                       │   │
│                 │ │     "gatekit": {                      │   │
│                 │ │       "command": "gatekit-gateway",   │   │
│                 │ │       "args": ["--config", "/path/..."] │   │
│                 │ │     }                                    │   │
│                 │ │   }                                      │   │
│                 │ │ }                                        │   │
│                 │ └─────────────────────────────────────────┘   │
│                 │                                                 │
│                 │ Select all (Ctrl+A) then copy (Ctrl+C)         │
│                 │ [Copy Config Snippet]                           │
│                 │                                                 │
│                 │ ⓘ To restore later: ~/gatekit/restore/res... │
│                 │ [Open Restore Instructions]                     │
│                 │                                                 │
│                 │ After updating, restart Claude Desktop          │
│                 │                                                 │
├─────────────────┴────────────────────────────────────────────────┤
│                 │                                                 │
│ [Back]                                    [Cancel]    [Finish]   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### CLI Client Example (Claude Code)

```
┌──────────────────────────────────────────────────────────────────┐
│ Setup Complete                                           [Header] │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│ ✅ Configuration created successfully                            │
│                                                                   │
│ Gatekit Config: ~/gatekit/gatekit.yaml                     │
│ [Copy Path] [Open]                                               │
│                                                                   │
│ Restore Scripts: ~/gatekit/restore/                            │
│ [Copy Path] [Open Folder]                                        │
│                                                                   │
├─────────────────┬────────────────────────────────────────────────┤
│                 │                                                 │
│   Claude Desktop│ Update Claude Code                             │
│ ▶ Claude Code   │                                                 │
│   Codex         │ Run these commands in your terminal:           │
│                 │                                                 │
│                 │ ┌─────────────────────────────────────────┐   │
│                 │ │ # Remove existing servers               │   │
│                 │ │ claude mcp remove filesystem-server     │   │
│                 │ │ claude mcp remove github-server         │   │
│                 │ │                                          │   │
│                 │ │ # Add Gatekit                          │   │
│                 │ │ claude mcp add gatekit \              │   │
│                 │ │   --scope user \                         │   │
│                 │ │   gatekit-gateway \                    │   │
│                 │ │   --config /path/to/gatekit.yaml       │   │
│                 │ └─────────────────────────────────────────┘   │
│                 │                                                 │
│                 │ [Copy Commands]                                 │
│                 │                                                 │
│                 │ ⓘ To restore later: ~/gatekit/restore/res... │
│                 │ [Open Restore Instructions]                     │
│                 │                                                 │
│                 │ After running commands, restart Claude Code     │
│                 │                                                 │
├─────────────────┴────────────────────────────────────────────────┤
│                                                                   │
│ [Back]                                    [Cancel]    [Finish]   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Empty State (No Clients Selected - Edge Case)

```
┌──────────────────────────────────────────────────────────────────┐
│ Setup Complete                                           [Header] │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│ ✅ Configuration created successfully                            │
│                                                                   │
│ Gatekit Config: ~/gatekit/gatekit.yaml                     │
│ [Copy Path] [Open]                                               │
│                                                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│                No MCP clients selected                            │
│                                                                   │
│    Your Gatekit configuration is ready to use.                 │
│    Configure MCP clients manually to use Gatekit.              │
│                                                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│ [Back]                                    [Cancel]    [Finish]   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Technical Design

### Widget Hierarchy

```
SetupCompleteScreen(Screen[ScreenResult])
├── Header
├── Container (outer container with vertical layout)
│   ├── FileLocationsSummary (Container, fixed height, always visible)
│   │   ├── Static (success message)
│   │   ├── Horizontal (gatekit config)
│   │   │   ├── Static (path)
│   │   │   ├── Button (Copy Path)
│   │   │   └── Button (Open)
│   │   └── Horizontal (restore scripts, if generated)
│   │       ├── Static (path)
│   │       ├── Button (Copy Path)
│   │       └── Button (Open Folder)
│   │
│   ├── Horizontal (master-detail container, id="master_detail", fills remaining space)
│   │   ├── VerticalScroll (master panel, id="master_panel", auto width, max 30%)
│   │   │   └── ClientListItem (repeated for each client)
│   │   │       ├── Static (icon + name)
│   │   │       └── click handler → select client
│   │   │
│   │   └── VerticalScroll (detail panel, id="detail_panel", remaining width)
│   │       ├── AlreadyConfiguredAlert (if applicable, id="already_configured_alert")
│   │       │   ├── Static (warning message)
│   │       │   └── Button (Open Existing Config)
│   │       ├── Static (client header - "Update [Client Name]")
│   │       ├── Static (config path, for Claude Desktop)
│   │       ├── Horizontal (action buttons - Open in Editor, Copy Path)
│   │       ├── Static (instruction label - "Replace your entire mcpServers section with:")
│   │       ├── TextArea (snippet with JSON or bash/PowerShell)
│   │       ├── Static (helper text for Claude Desktop - "Select all (Ctrl+A)...")
│   │       ├── Button (Copy Snippet or Copy Commands)
│   │       ├── Static (restore info, if available)
│   │       ├── Button (Open Restore Instructions, if available)
│   │       └── Static (restart note)
│   │
│   └── Horizontal (bottom actions, fixed height)
│       ├── Button (Back)
│       ├── Spacer (fills middle)
│       ├── Button (Cancel)
│       └── Button (Finish, variant="primary")
│
└── Footer
```

### New Widget Classes

**Required imports for implementation:**
```python
import platform
from pathlib import Path
from typing import List, Optional, Union

from textual import events, on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.events import Click
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static, TextArea

from ...guided_setup.models import (
    ClientType,
    DetectedClient,
    GuidedSetupState,
    MigrationInstructions,
    NavigationAction,
    ScreenResult,
)
```

#### ClientListItem

```python
class ClientListItem(Static):
    """A selectable client list item in the master panel.

    Displays client name and warning indicator if already configured.
    Changes appearance when selected.

    Attributes:
        client_type: Type of MCP client
        is_already_configured: Whether client already uses Gatekit
    """

    DEFAULT_CSS = """
    ClientListItem {
        height: auto;
        padding: 1 2;
        background: $surface;
        color: $text;
    }

    ClientListItem.selected {
        background: $accent;
        color: $text;
        text-style: bold;
    }

    ClientListItem:hover {
        background: $surface-lighten-1;
    }

    ClientListItem.already-configured {
        color: $warning;
    }
    """

    # Enable keyboard focus for navigation
    can_focus = True

    def __init__(
        self,
        client_type: ClientType,
        is_already_configured: bool = False,
        **kwargs
    ):
        """Initialize client list item.

        Args:
            client_type: Type of MCP client
            is_already_configured: Whether client already uses Gatekit
            **kwargs: Additional arguments passed to Static
        """
        icon = "⚠️  " if is_already_configured else ""
        display_name = client_type.display_name()
        content = f"{icon}{display_name}"

        super().__init__(content, **kwargs)

        self.client_type = client_type
        self.is_already_configured = is_already_configured

        if is_already_configured:
            self.add_class("already-configured")

    def on_click(self, event: Click) -> None:
        """Handle click to select this client.

        Args:
            event: Click event from Textual
        """
        self.post_message(self.ClientSelected(self.client_type))
        event.stop()  # Prevent event from bubbling to screen

    class ClientSelected(Message):
        """Message posted when client is selected.

        This message bubbles up to the screen to trigger selection.
        """

        def __init__(self, client_type: ClientType):
            super().__init__()
            self.client_type = client_type
```

#### AlreadyConfiguredAlert

```python
class AlreadyConfiguredAlert(Container):
    """Alert box shown when client is already configured to use Gatekit.

    Shows warning message, explains situation, displays the client's MCP config
    file path, and provides button to open that config file.

    Attributes:
        existing_config_path: Path to client's MCP config file (e.g., claude_desktop_config.json)
    """

    DEFAULT_CSS = """
    AlreadyConfiguredAlert {
        height: auto;
        border: solid $warning;
        background: $panel;
        padding: 1 2;
        margin-bottom: 2;
    }

    AlreadyConfiguredAlert .alert-title {
        text-style: bold;
        color: $warning;
        margin-bottom: 1;
        height: auto;
    }

    AlreadyConfiguredAlert .alert-message {
        color: $text;
        margin-bottom: 1;
        height: auto;
    }

    AlreadyConfiguredAlert .config-path {
        color: $text-muted;
        margin-bottom: 1;
        height: auto;
    }

    AlreadyConfiguredAlert Button {
        margin-top: 1;
        width: auto;
        min-width: 20;
    }
    """

    def __init__(self, existing_config_path: Path, **kwargs):
        """Initialize alert with existing config path.

        Args:
            existing_config_path: Path to client's config file
            **kwargs: Additional arguments passed to Container
        """
        super().__init__(**kwargs)
        self.existing_config_path = existing_config_path

    def compose(self) -> ComposeResult:
        """Build alert widget content."""
        yield Static("⚠️  Already Using Gatekit", classes="alert-title")
        yield Static(
            "This client is currently configured to use Gatekit via:",
            classes="alert-message"
        )
        yield Static(str(self.existing_config_path), classes="config-path")
        yield Static(
            "You can:\n"
            "1. Follow instructions below to switch to the new Gatekit config, OR\n"
            "2. Open the existing config to modify the active configuration instead",
            classes="alert-message"
        )
        yield Button(
            "Open Existing Config",
            id="open_existing_config",
            variant="default"
        )
```

#### FileLocationsSummary

```python
class FileLocationsSummary(Container):
    """Summary of created file locations displayed at top of screen.

    Shows gatekit config and restore scripts paths with action buttons.
    Always visible (not scrollable with detail content).

    Attributes:
        config_path: Path to created gatekit.yaml
        restore_dir: Optional path to restore scripts directory
    """

    DEFAULT_CSS = """
    FileLocationsSummary {
        height: auto;
        background: $panel;
        border-bottom: solid $primary;
        padding: 1 2;
        margin-bottom: 1;
    }

    FileLocationsSummary .success-message {
        text-style: bold;
        color: $success;
        margin-bottom: 1;
        height: auto;
    }

    FileLocationsSummary .file-row {
        height: auto;
        margin-bottom: 1;
    }

    FileLocationsSummary .file-label {
        color: $text;
        text-style: bold;
    }

    FileLocationsSummary .file-path {
        color: $text-muted;
    }

    FileLocationsSummary Button {
        margin-left: 1;
        width: auto;
        min-width: 12;
    }
    """

    def __init__(
        self,
        config_path: Path,
        restore_dir: Optional[Path] = None,
        **kwargs
    ):
        """Initialize file locations summary.

        Args:
            config_path: Path to created gatekit.yaml
            restore_dir: Optional path to restore scripts directory
            **kwargs: Additional arguments passed to Container
        """
        super().__init__(**kwargs)
        self.config_path = config_path
        self.restore_dir = restore_dir

    def compose(self) -> ComposeResult:
        """Build file locations summary content."""
        yield Static("✅ Configuration created successfully", classes="success-message")

        # Gatekit config
        with Horizontal(classes="file-row"):
            yield Static(f"Gatekit Config: {self.config_path}", classes="file-path")
            yield Button("Copy Path", id="copy_config_path")
            yield Button("Open", id="open_config_file")

        # Restore scripts (if generated)
        if self.restore_dir:
            with Horizontal(classes="file-row"):
                yield Static(f"Restore Scripts: {self.restore_dir}", classes="file-path")
                yield Button("Copy Path", id="copy_restore_path")
                yield Button("Open Folder", id="open_restore_folder")
```

### Screen State Management

```python
class SetupCompleteScreen(Screen[Union[ScreenResult, Optional[str]]]):
    """Setup complete screen with master-detail client instructions.

    Contract:
    - Requires GuidedSetupState from ConfigurationSummaryScreen
    - Returns ScreenResult with action (BACK, CANCEL, or CONTINUE)
    - BACK: Return to ConfigurationSummaryScreen with state preserved
    - CANCEL: Exit wizard entirely
    - CONTINUE: Finish wizard (user clicked Finish button)
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("up", "focus_up", "Up", show=False),
        Binding("down", "focus_down", "Down", show=False),
        Binding("left", "focus_left", "Left", show=False),
        Binding("right", "focus_right", "Right", show=False),
    ]

    def __init__(
        self,
        state: Optional[GuidedSetupState] = None,
        migration_instructions: Optional[List[MigrationInstructions]] = None,
        # Legacy parameters for backward compatibility
        gatekit_config_path: Optional[Path] = None,
        restore_script_dir: Optional[Path] = None,
    ) -> None:
        """Initialize setup complete screen.

        Args:
            state: State from ConfigurationSummaryScreen (new flow)
            migration_instructions: List of migration instructions
            gatekit_config_path: Legacy parameter for old flow
            restore_script_dir: Legacy parameter for old flow
        """
        super().__init__()

        # Support both old and new calling patterns
        if state is not None:
            # New flow: use state
            self.state = state
            self.gatekit_config_path = state.config_path
            self.restore_script_dir = state.restore_dir if state.generate_restore else None
            self.migration_instructions = state.migration_instructions or migration_instructions or []
            self.already_configured_clients = state.already_configured_clients or []
        else:
            # Old flow: use direct parameters
            self.state = None
            self.gatekit_config_path = gatekit_config_path
            self.restore_script_dir = restore_script_dir
            self.migration_instructions = migration_instructions or []
            self.already_configured_clients = []

        # Track selected client (index into migration_instructions)
        self.selected_client_index = 0 if self.migration_instructions else None

    def on_mount(self) -> None:
        """Called when screen is mounted.

        Triggers initial selection to populate detail panel with first client's instructions.
        """
        if self.selected_client_index is not None:
            # Trigger initial selection to populate detail panel
            self._select_client(0)

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard navigation between client list and buttons.

        Follows the same pattern as ServerSelectionScreen and ClientSelectionScreen:
        - Arrow keys handled here instead of in action_* methods
        - Checks self.focused to determine current focus
        - Only intercepts arrows when in master panel or buttons
        - Allows detail panel widgets (TextArea, etc.) to handle their own arrows

        Args:
            event: Key event from Textual
        """
        if not self.migration_instructions:
            return

        focused = self.focused

        # Check if focus is in master panel (client list navigation context)
        is_in_master_panel = False
        if isinstance(focused, ClientListItem):
            is_in_master_panel = True
        elif focused is not None:
            # Check if focused widget is a child of master_panel
            try:
                master_panel = self.query_one("#master_panel", VerticalScroll)
                # Walk up the widget tree to see if we're inside master panel
                parent = focused.parent
                while parent is not None:
                    if parent is master_panel:
                        is_in_master_panel = True
                        break
                    parent = parent.parent
            except Exception:
                pass

        # Handle up arrow - only for master panel or button navigation
        if event.key == "up":
            if is_in_master_panel:
                # In master panel - navigate to previous client
                if self.selected_client_index is not None and self.selected_client_index > 0:
                    self._select_client(self.selected_client_index - 1)
                    event.prevent_default()
                    event.stop()
            elif isinstance(focused, Button) and focused.id in ("back_button", "cancel_button", "finish_button"):
                # From buttons - move back to client navigation (no actual focus change, just stop propagation)
                # User can still navigate clients with arrows even when buttons have focus
                if self.selected_client_index is not None and self.selected_client_index > 0:
                    self._select_client(self.selected_client_index - 1)
                    event.prevent_default()
                    event.stop()

        # Handle down arrow - only for master panel or button navigation
        elif event.key == "down":
            if is_in_master_panel:
                # In master panel - navigate to next client or transition to buttons
                if self.selected_client_index is not None:
                    if self.selected_client_index < len(self.migration_instructions) - 1:
                        # Move to next client
                        self._select_client(self.selected_client_index + 1)
                        event.prevent_default()
                        event.stop()
                    else:
                        # On last client - move focus to Back button
                        try:
                            back_btn = self.query_one("#back_button", Button)
                            back_btn.focus()
                            event.prevent_default()
                            event.stop()
                        except Exception:
                            pass
            elif isinstance(focused, Button):
                if focused.id in ("back_button", "cancel_button", "finish_button"):
                    # On buttons - either navigate clients or block wrap-around
                    if self.selected_client_index is not None and self.selected_client_index < len(self.migration_instructions) - 1:
                        # Allow navigating clients even from button focus
                        self._select_client(self.selected_client_index + 1)
                    # Always prevent default to block wrap-around
                    event.prevent_default()
                    event.stop()

        # Handle left/right arrow navigation between buttons
        elif event.key == "left":
            if isinstance(focused, Button):
                if focused.id == "finish_button":
                    try:
                        self.query_one("#cancel_button", Button).focus()
                        event.prevent_default()
                        event.stop()
                    except Exception:
                        pass
                elif focused.id == "cancel_button":
                    try:
                        self.query_one("#back_button", Button).focus()
                        event.prevent_default()
                        event.stop()
                    except Exception:
                        pass
        elif event.key == "right":
            if isinstance(focused, Button):
                if focused.id == "back_button":
                    try:
                        self.query_one("#cancel_button", Button).focus()
                        event.prevent_default()
                        event.stop()
                    except Exception:
                        pass
                elif focused.id == "cancel_button":
                    try:
                        self.query_one("#finish_button", Button).focus()
                        event.prevent_default()
                        event.stop()
                    except Exception:
                        pass

    @on(ClientListItem.ClientSelected)
    def handle_client_selected(self, event: ClientListItem.ClientSelected) -> None:
        """Handle client selection from ClientListItem click or Enter key.

        Args:
            event: ClientSelected message containing the selected client type
        """
        # Find the index of the selected client type in migration_instructions
        for i, instr in enumerate(self.migration_instructions):
            if instr.client_type == event.client_type:
                self._select_client(i)
                break

    def _is_client_already_configured(self, client_type: ClientType) -> Optional[DetectedClient]:
        """Check if client is already configured to use Gatekit.

        Args:
            client_type: Type of MCP client to check

        Returns:
            DetectedClient if found in already_configured_clients, None otherwise
        """
        for client in self.already_configured_clients:
            if client.client_type == client_type:
                return client
        return None

    def _select_client(self, index: int) -> None:
        """Select a client and update UI.

        Args:
            index: Index into migration_instructions list
        """
        if index < 0 or index >= len(self.migration_instructions):
            return

        self.selected_client_index = index

        # Determine if we should move focus to the selected item
        # Only focus the item when:
        # 1. No widget currently has focus (initial mount), OR
        # 2. Focus is already in the master panel (user navigating list)
        # This allows navigating clients while keeping button focus (per NFR-1)
        focused = self.focused
        should_focus_item = focused is None

        if not should_focus_item and focused is not None:
            # Check if focus is in master panel
            if isinstance(focused, ClientListItem):
                should_focus_item = True
            else:
                # Walk up parent tree to check if inside master panel
                try:
                    master_panel = self.query_one("#master_panel", VerticalScroll)
                    parent = focused.parent
                    while parent is not None:
                        if parent is master_panel:
                            should_focus_item = True
                            break
                        parent = parent.parent
                except Exception:
                    pass

        # Update master panel selection visual (and optionally focus)
        master_panel = self.query_one("#master_panel", VerticalScroll)
        for i, item in enumerate(master_panel.query(ClientListItem)):
            if i == index:
                item.add_class("selected")
                # Only focus if appropriate (see logic above)
                if should_focus_item:
                    item.focus()
            else:
                item.remove_class("selected")

        # Rebuild detail panel with selected client's instructions
        self.call_later(self._rebuild_detail_panel)

    def _rebuild_detail_panel(self) -> None:
        """Rebuild detail panel with selected client's instructions.

        Clears detail panel and remounts content for currently selected client.
        Note: This method uses synchronous mounting - Textual queues the widgets internally.
        """
        if self.selected_client_index is None:
            return

        instr = self.migration_instructions[self.selected_client_index]
        detail_panel = self.query_one("#detail_panel", VerticalScroll)

        # Clear existing content
        detail_panel.remove_children()

        # Check if client is already configured
        already_configured = self._is_client_already_configured(instr.client_type)

        # Build list of widgets to mount
        widgets_to_mount = []

        # Already-configured alert (if applicable)
        if already_configured:
            widgets_to_mount.append(
                AlreadyConfiguredAlert(
                    already_configured.config_path,
                    id="already_configured_alert"
                )
            )

        # Client header
        widgets_to_mount.append(Static(
            f"Update {instr.client_type.display_name()}",
            classes="client-header"
        ))

        # Config path (for Claude Desktop only)
        if instr.client_type == ClientType.CLAUDE_DESKTOP:
            widgets_to_mount.append(Static(
                str(instr.config_path),
                classes="client-config-path"
            ))

            # Create action buttons container with buttons
            action_buttons = Horizontal(
                Button(
                    "Open in Editor",
                    id=f"open_editor_{self.selected_client_index}",
                    variant="default",
                    classes="path-button"
                ),
                Button(
                    "Copy Path",
                    id=f"copy_client_path_{self.selected_client_index}",
                    variant="default",
                    classes="path-button"
                ),
                classes="action-buttons"
            )
            widgets_to_mount.append(action_buttons)

        # Instruction label
        if instr.client_type == ClientType.CLAUDE_DESKTOP:
            instruction_label = "Replace your entire mcpServers section with:"
        else:
            shell_name = "PowerShell" if platform.system() == "Windows" else "terminal"
            instruction_label = f"Run these commands in your {shell_name}:"

        widgets_to_mount.append(Static(instruction_label, classes="instruction-label"))

        # TextArea with snippet
        if instr.client_type == ClientType.CLAUDE_DESKTOP:
            syntax_language = "json"
        else:
            syntax_language = "powershell" if platform.system() == "Windows" else "bash"

        textarea = TextArea(
            instr.migration_snippet,
            language=syntax_language,
            read_only=True,
            show_line_numbers=False,
            theme="monokai",
            id=f"snippet_{self.selected_client_index}"
        )
        widgets_to_mount.append(textarea)

        # Helper text (Claude Desktop only)
        if instr.client_type == ClientType.CLAUDE_DESKTOP:
            widgets_to_mount.append(Static(
                "Select all (Ctrl+A) then copy (Ctrl+C)",
                classes="helper-text"
            ))

        # Copy button
        button_label = (
            "Copy Config Snippet"
            if instr.client_type == ClientType.CLAUDE_DESKTOP
            else "Copy Commands"
        )
        widgets_to_mount.append(Button(
            button_label,
            id=f"copy_snippet_{self.selected_client_index}",
            variant="primary"
        ))

        # Restore instructions (if available)
        if self.restore_script_dir:
            restore_file = self._get_restore_filename(instr.client_type)
            restore_path = self.restore_script_dir / restore_file

            restore_text = f"ⓘ To restore later: {restore_path}"
            widgets_to_mount.append(Static(restore_text, classes="restore-info"))

            widgets_to_mount.append(Button(
                "Open Restore Instructions",
                id=f"open_restore_{self.selected_client_index}",
                variant="default",
                classes="path-button"
            ))

        # Restart note
        client_name = instr.client_type.display_name()
        widgets_to_mount.append(Static(
            f"After updating, restart {client_name}",
            classes="restart-note"
        ))

        # Mount all widgets at once (synchronous - Textual queues internally)
        detail_panel.mount(*widgets_to_mount)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events.

        Args:
            event: Button press event
        """
        button_id = event.button.id

        # Bottom action buttons
        if button_id == "back_button":
            if self.state is not None:
                self.dismiss(ScreenResult(
                    action=NavigationAction.BACK,
                    state=self.state
                ))
            else:
                # Old flow: return None
                self.dismiss(None)

        elif button_id == "cancel_button":
            if self.state is not None:
                self.dismiss(ScreenResult(
                    action=NavigationAction.CANCEL,
                    state=None
                ))
            else:
                # Old flow: return None
                self.dismiss(None)

        elif button_id == "finish_button":
            if self.state is not None:
                # New flow: CONTINUE indicates wizard completion
                self.dismiss(ScreenResult(
                    action=NavigationAction.CONTINUE,
                    state=self.state
                ))
            else:
                # Old flow: return string
                self.dismiss("done")

        # File location buttons
        elif button_id == "copy_config_path":
            self._copy_to_clipboard(str(self.gatekit_config_path))

        elif button_id == "open_config_file":
            self._open_in_editor(self.gatekit_config_path)

        elif button_id == "copy_restore_path" and self.restore_script_dir:
            self._copy_to_clipboard(str(self.restore_script_dir))

        elif button_id == "open_restore_folder" and self.restore_script_dir:
            self._open_folder(self.restore_script_dir)

        # Already-configured alert button
        elif button_id == "open_existing_config":
            if self.selected_client_index is not None:
                instr = self.migration_instructions[self.selected_client_index]
                already_configured = self._is_client_already_configured(instr.client_type)
                if already_configured:
                    self._open_in_editor(already_configured.config_path)

        # Client-specific buttons
        elif button_id.startswith("copy_snippet_"):
            index = int(button_id.split("_")[-1])
            snippet = self.migration_instructions[index].migration_snippet
            self._copy_to_clipboard(snippet)

        elif button_id.startswith("copy_client_path_"):
            index = int(button_id.split("_")[-1])
            path = str(self.migration_instructions[index].config_path)
            self._copy_to_clipboard(path)

        elif button_id.startswith("open_editor_"):
            index = int(button_id.split("_")[-1])
            config_path = self.migration_instructions[index].config_path
            self._open_in_editor(config_path)

        elif button_id.startswith("open_restore_"):
            index = int(button_id.split("_")[-1])
            if self.restore_script_dir:
                client_type = self.migration_instructions[index].client_type
                restore_file = self._get_restore_filename(client_type)
                restore_path = self.restore_script_dir / restore_file
                self._open_in_editor(restore_path)

    def action_cancel(self) -> None:
        """Handle cancel action (Escape key)."""
        if self.state is not None:
            self.dismiss(ScreenResult(
                action=NavigationAction.CANCEL,
                state=None
            ))
        else:
            self.dismiss(None)

    def action_focus_right(self) -> None:
        """Move focus right (no-op, handled in on_key)."""
        pass

    def action_focus_left(self) -> None:
        """Move focus left (no-op, handled in on_key)."""
        pass

    def action_focus_up(self) -> None:
        """Move focus up (no-op, handled in on_key)."""
        pass

    def action_focus_down(self) -> None:
        """Move focus down (no-op, handled in on_key)."""
        pass

    # ... existing helper methods (_copy_to_clipboard, _open_in_editor, etc.)
```

### CSS Styling

**IMPORTANT: Use Shared Wizard Styles**

This screen should import and use the shared wizard styles from `gatekit/tui/styles/wizard.tcss` for consistency with other wizard screens. These provide:
- Standard wizard layout and container styles
- Button layout patterns (Back/Cancel/Finish)
- Screen titles, descriptions, and section headers
- Consistent spacing and colors

**Implementation:**

```python
from pathlib import Path

# Load shared wizard styles
WIZARD_CSS_PATH = Path(__file__).resolve().parent.parent / "styles" / "wizard.tcss"
SHARED_WIZARD_CSS = WIZARD_CSS_PATH.read_text()

class SetupCompleteScreen(Screen):
    CSS = SHARED_WIZARD_CSS + """
    /* Screen-specific styles below */
    ...
    """
```

**Screen-Specific CSS** (in addition to shared wizard styles):

```css
/* Master-detail layout */
SetupCompleteScreen #master_detail {
    height: 1fr;
    layout: horizontal;
}

/* Master panel: Dynamic width based on content */
SetupCompleteScreen #master_panel {
    width: auto;           /* Fits content (longest client name + icon) */
    min-width: 20;         /* Minimum width in cells for very short names */
    max-width: 35;         /* Maximum width in cells (roughly 30% on typical screen) */
    border-right: solid $primary;
    height: 100%;
}

/* Detail panel: Takes remaining space */
SetupCompleteScreen #detail_panel {
    width: 1fr;            /* Fills remaining horizontal space */
    height: 100%;
    padding: 1 2;
}

/* Master panel items */
SetupCompleteScreen ClientListItem {
    height: auto;
    padding: 1 2;
    background: $surface;
    color: $text;
}

SetupCompleteScreen ClientListItem.selected {
    background: $accent;
    color: $text;
    text-style: bold;
}

SetupCompleteScreen ClientListItem:hover {
    background: $surface-lighten-1;
    cursor: pointer;
}

SetupCompleteScreen ClientListItem.already-configured {
    color: $warning;
}

/* Detail panel content */
SetupCompleteScreen .client-header {
    text-style: bold;
    color: $accent;
    margin-bottom: 1;
    height: auto;
}

SetupCompleteScreen .client-config-path {
    color: $text-muted;
    margin-bottom: 1;
    height: auto;
}

SetupCompleteScreen .instruction-label {
    text-style: bold;
    color: $text;
    margin-bottom: 1;
    margin-top: 1;
    height: auto;
}

SetupCompleteScreen .helper-text {
    color: $text-muted;
    margin-bottom: 1;
    height: auto;
}

SetupCompleteScreen .restore-info {
    color: $text-muted;
    margin-top: 1;
    margin-bottom: 1;
    height: auto;
}

SetupCompleteScreen .restart-note {
    color: $text-muted;
    text-style: italic;
    margin-top: 1;
    margin-bottom: 2;
    height: auto;
}

SetupCompleteScreen TextArea {
    height: auto;
    max-height: 15;
    margin-bottom: 1;
}

/* Action buttons */
SetupCompleteScreen .action-buttons {
    margin-bottom: 1;
    height: auto;
}

SetupCompleteScreen .action-buttons Button {
    margin-right: 1;
}

SetupCompleteScreen .path-button {
    width: auto;
    min-width: 15;
}

/* Bottom action bar (wizard-consistent) */
SetupCompleteScreen .bottom-actions {
    align: left middle;
    height: auto;
    margin-top: 2;
    padding-top: 1;
    border-top: solid $primary;
}

SetupCompleteScreen .bottom-actions Button {
    margin: 0 1;
}
```

## Migration Instructions Generation Updates

### Update migration_instructions.py

The migration instruction generation needs to be updated to provide complete mcpServers sections instead of individual entries:

**For Claude Desktop:**

```python
def _generate_claude_desktop_instructions(
    client: DetectedClient,
    selected_servers: List[DetectedServer],
    gatekit_gateway_path: Path,
    gatekit_config_path: Path,
) -> MigrationInstructions:
    """Generate Claude Desktop migration instructions.

    Returns complete mcpServers section to replace existing one.
    """
    # Collect env vars
    servers_sorted = sorted(selected_servers, key=lambda s: s.name)
    all_env_vars, env_conflicts = _collect_all_env_vars(servers_sorted)

    # Build complete mcpServers section with only Gatekit entry
    mcp_servers = {
        "gatekit": {
            "command": str(gatekit_gateway_path),
            "args": ["--config", str(gatekit_config_path)],
        }
    }

    if all_env_vars:
        mcp_servers["gatekit"]["env"] = all_env_vars

    # Wrap in mcpServers key for complete replacement
    snippet_object = {"mcpServers": mcp_servers}
    snippet = json.dumps(snippet_object, indent=2)

    # Build instructions
    instructions = f"""
Update Claude Desktop Configuration

1. Open your config file:
   {client.config_path}

2. Replace your entire mcpServers section with:

{snippet}

3. Restart Claude Desktop
"""

    if env_conflicts:
        warning = "\n⚠️ Environment Variable Conflicts:\n"
        warning += "\n".join(env_conflicts)
        instructions = warning + "\n" + instructions

    return MigrationInstructions(
        client_type=client.client_type,
        config_path=client.config_path,
        migration_snippet=snippet,
        instructions=instructions,
        has_conflicts=bool(env_conflicts)
    )
```

## Implementation Plan

**Key Technical Considerations:**
1. **CSS Units**: Textual doesn't support percentage units - use cell counts (e.g., `max-width: 35`) or `fr` units
2. **Keyboard Navigation Pattern** (matches ServerSelectionScreen and ClientSelectionScreen):
   - **BINDINGS**: Declare arrow key bindings pointing to `action_focus_*` methods
   - **action_* methods**: Empty (pass only) - bindings require them to exist
   - **on_key() handler**: Implements ALL custom navigation logic
     - Checks `self.focused` to determine current widget
     - **CRITICAL**: Only intercept arrows when in master panel or on buttons
     - Must check if focused widget is in master panel (walk parent tree)
     - Let detail panel widgets (TextArea, etc.) handle their own arrows for scrolling/cursor movement
     - Handles transitions between client list, buttons, and widgets
     - Calls `event.prevent_default()` and `event.stop()` to prevent default behavior
   - **@on() decorator**: Handles widget-specific events (button press, client selection)
3. **Synchronous Mounting**: Use `widget.mount(*children)` to mount multiple widgets - Textual queues them internally
   - ✅ Can be called from synchronous methods
   - ✅ Unpacking a list with `*` passes all widgets as individual arguments
4. **Scheduling UI Updates**: Use `call_later(callback)` to defer synchronous methods to next event loop tick
   - Callback must be a regular function (not async)
   - Used to avoid modifying widgets during event handling
5. **Widget Construction**: Containers like `Horizontal()` accept child widgets in `__init__()` - don't use `with` blocks for runtime mounting
6. **Selection and Focus Management**:
   - Call `_select_client(0)` in `on_mount()` to populate detail panel on screen load
   - **CRITICAL**: `_select_client()` must conditionally focus the selected item:
     - Focus when `self.focused is None` (initial mount - accessibility requirement)
     - Focus when current focus is in master panel (user navigating list)
     - Do NOT focus when current focus is on buttons (preserves button highlight per NFR-1)
   - This enables both: (1) immediate keyboard navigation on mount, AND (2) navigating clients while keeping button focused

### Phase 1: Widget Classes (2 hours)
- [ ] Add all required imports (see "Required imports for implementation" section)
  - Textual core: events, on, ComposeResult, Binding, Message, Screen
  - Textual containers: Container, Horizontal, VerticalScroll
  - Textual widgets: Button, Footer, Header, Static, TextArea
  - Textual events: Click
  - Standard library: platform, Path, typing
  - Guided setup models: ClientType, DetectedClient, GuidedSetupState, etc.
- [ ] Create `ClientListItem` widget with selection state
  - **REQUIRED**: Set `can_focus = True` class attribute (needed for `item.focus()` to work)
  - Implement `on_click()` to post `ClientSelected` message with `event.stop()`
  - Define `ClientSelected` message class (extends Message)
  - **DO NOT implement on_key()** - all keyboard navigation handled at screen level (established pattern)
- [ ] Create `AlreadyConfiguredAlert` widget
- [ ] Create `FileLocationsSummary` widget
- [ ] Import shared wizard styles from `gatekit/tui/styles/wizard.tcss`
- [ ] Write screen-specific CSS for new widgets (master-detail layout, client list items, alerts)
- [ ] Test widgets in isolation with sample data

### Phase 2: Update Migration Instructions (1 hour)
- [ ] Update `_generate_claude_desktop_instructions()` to return complete mcpServers section
- [ ] Update instruction text to say "Replace your entire mcpServers section with:"
- [ ] Remove server list from instruction generation
- [ ] Test updated instruction format

### Phase 3: Screen Refactoring (2-3 hours)
- [ ] Add BINDINGS at class level (escape, up, down, left, right)
- [ ] Add empty action_* methods (action_focus_up, action_focus_down, action_focus_left, action_focus_right)
- [ ] Refactor `SetupCompleteScreen.compose()` to use master-detail layout
- [ ] Implement `on_mount()` to trigger initial selection (calls `_select_client(0)`)
- [ ] Implement screen-level `on_key()` handler following established pattern
  - Check `self.focused` to determine current widget
  - **CRITICAL**: Check if focus is in master panel (isinstance or walk parent tree)
    - Only intercept arrows when `is_in_master_panel` or on buttons
    - Let detail panel widgets (TextArea) handle their own arrows
  - Handle `up`/`down` for client navigation (when in master panel, not on buttons)
  - Handle `up` from buttons → navigate to previous client
  - Handle `down` on last client in master panel → move to Back button
  - Handle `down` from buttons → navigate to next client or block wrap-around
  - Handle `left`/`right` for button navigation
  - Call `event.prevent_default()` and `event.stop()` for each case
- [ ] Implement `@on(ClientListItem.ClientSelected)` handler
  - Receives message when client is clicked
  - Finds index of selected client type
  - Calls `_select_client()` with that index
- [ ] Implement `_select_client()` method (sync, schedules rebuild via `call_later()`)
  - Updates `selected_client_index`
  - Updates visual selection in master panel (add/remove "selected" class)
  - **CRITICAL**: Conditionally call `item.focus()` on selected item
    - Focus ONLY when: (1) no widget has focus (initial mount), OR (2) focus is in master panel
    - Do NOT focus when focus is on buttons (allows navigating clients while keeping button highlighted)
    - This preserves NFR-1 behavior: "Up/Down from buttons navigates clients without changing button focus"
    - Check `self.focused` and walk parent tree to determine if in master panel
  - Schedules `_rebuild_detail_panel()` via `call_later()`
- [ ] Implement `_rebuild_detail_panel()` method (sync, uses `mount(*widgets)` to add widgets)
  - Build list of widgets to mount
  - Clear existing children with `remove_children()`
  - Mount all new widgets with `detail_panel.mount(*widgets_to_mount)`
- [ ] Implement `_is_client_already_configured()` method
- [ ] Update button layout to match wizard pattern (Back/Cancel/Finish)
- [ ] Remove "Test All Connections" button

### Phase 4: Button Handlers (1 hour)
- [ ] Update `on_button_pressed()` for new button IDs:
  - `back_button` → dismiss with BACK action
  - `cancel_button` → dismiss with CANCEL action
  - `finish_button` → dismiss with CONTINUE action
  - File location buttons (copy/open)
  - `open_existing_config` button
  - Existing client-specific buttons
- [ ] Implement `_open_folder()` method for "Open Folder" button
- [ ] Test all button actions

### Phase 5: Testing (1-2 hours)
- [ ] Unit tests for `_is_client_already_configured()`
- [ ] Unit tests for `_select_client()` logic and conditional focus behavior
- [ ] Unit tests for updated instruction generation
- [ ] UI tests for keyboard navigation
  - Arrow keys work immediately on mount (no click required)
  - Up/Down from buttons navigates clients without stealing focus (NFR-1 requirement)
  - Arrow keys work normally in TextArea for scrolling/cursor movement
- [ ] UI tests for mouse selection
- [ ] Integration test: Full flow with already-configured client
- [ ] Integration test: Full flow with no already-configured clients
- [ ] Integration test: Empty migration_instructions list
- [ ] Integration test: Back navigation preserves state

## Testing Strategy

### Unit Tests

```python
def test_is_client_already_configured_returns_match():
    """Should find client in already_configured_clients list."""
    client = DetectedClient(
        client_type=ClientType.CLAUDE_DESKTOP,
        config_path=Path("~/.config/Claude/claude_desktop_config.json"),
        servers=[]
    )
    state = GuidedSetupState(already_configured_clients=[client])

    screen = SetupCompleteScreen(state=state)
    result = screen._is_client_already_configured(ClientType.CLAUDE_DESKTOP)

    assert result is not None
    assert result.client_type == ClientType.CLAUDE_DESKTOP
    assert result.config_path == client.config_path

def test_is_client_already_configured_returns_none_when_not_found():
    """Should return None when client not in already_configured_clients."""
    state = GuidedSetupState(already_configured_clients=[])
    screen = SetupCompleteScreen(state=state)

    result = screen._is_client_already_configured(ClientType.CLAUDE_DESKTOP)

    assert result is None

def test_migration_instructions_contain_complete_mcp_servers():
    """Generated snippet should include mcpServers wrapper."""
    instr = _generate_claude_desktop_instructions(...)
    snippet_data = json.loads(instr.migration_snippet)

    assert "mcpServers" in snippet_data
    assert "gatekit" in snippet_data["mcpServers"]
    assert snippet_data["mcpServers"]["gatekit"]["command"]
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_back_button_returns_to_config_summary():
    """Back button should dismiss with BACK action."""
    app = GatekitApp()
    state = GuidedSetupState(...)

    screen = SetupCompleteScreen(state=state)
    app.push_screen(screen)

    # Simulate clicking Back button
    back_button = screen.query_one("#back_button")
    back_button.press()

    result = await screen.wait_for_dismiss()
    assert result.action == NavigationAction.BACK
    assert result.state == state

@pytest.mark.asyncio
async def test_finish_button_completes_wizard():
    """Finish button should dismiss with CONTINUE action."""
    app = GatekitApp()
    state = GuidedSetupState(...)

    screen = SetupCompleteScreen(state=state)
    app.push_screen(screen)

    # Simulate clicking Finish button
    finish_button = screen.query_one("#finish_button")
    finish_button.press()

    result = await screen.wait_for_dismiss()
    assert result.action == NavigationAction.CONTINUE

@pytest.mark.asyncio
async def test_already_configured_alert_shown():
    """Alert should appear when client is already configured."""
    client = DetectedClient(
        client_type=ClientType.CLAUDE_DESKTOP,
        config_path=Path("~/.config/Claude/claude_desktop_config.json"),
        servers=[]
    )
    state = GuidedSetupState(
        already_configured_clients=[client],
        migration_instructions=[...]
    )

    screen = SetupCompleteScreen(state=state)
    app.push_screen(screen)

    # Select Claude Desktop (already configured)
    screen._select_client(0)

    # Assert alert is visible
    alert = screen.query_one("#already_configured_alert", AlreadyConfiguredAlert)
    assert alert is not None
    assert str(client.config_path) in alert.render()

@pytest.mark.asyncio
async def test_arrow_keys_from_button_preserve_button_focus():
    """Up/Down arrows from buttons should navigate clients without changing focus."""
    instr = [
        MigrationInstructions(client_type=ClientType.CLAUDE_DESKTOP, ...),
        MigrationInstructions(client_type=ClientType.CLAUDE_CODE, ...)
    ]
    screen = SetupCompleteScreen(migration_instructions=instr)
    app.push_screen(screen)

    # Focus the Finish button
    finish_button = screen.query_one("#finish_button", Button)
    finish_button.focus()
    assert screen.focused is finish_button

    # Press down arrow to navigate to next client
    screen.on_key(Key(key="down"))

    # Assert: client selection changed but focus stayed on button
    assert screen.selected_client_index == 1  # Client changed
    assert screen.focused is finish_button  # Button focus preserved

    # Press up arrow to navigate back
    screen.on_key(Key(key="up"))

    # Assert: client selection changed but focus stayed on button
    assert screen.selected_client_index == 0  # Client changed back
    assert screen.focused is finish_button  # Button focus still preserved
```

## Success Criteria

- [x] Master panel lists all clients with clear selection state
- [x] Detail panel shows instructions for selected client only
- [x] Arrow keys navigate client list smoothly
- [x] Arrow keys work immediately on screen mount (no click required)
- [x] Up/Down from buttons navigates clients WITHOUT stealing focus from button
- [x] Click on client in master panel selects it
- [x] File locations always visible at top (not scrolled away)
- [x] Already-configured clients show ⚠️ icon in master panel
- [x] Already-configured alert appears in detail panel when applicable
- [x] "Open Existing Config" button opens client's config file
- [x] Bottom buttons match wizard pattern: Back/Cancel/Finish
- [x] Back button returns to ConfigurationSummaryScreen with state preserved
- [x] Cancel button exits wizard
- [x] Finish button completes wizard successfully
- [x] No "Test All Connections" button present
- [x] Instructions say "Replace your entire mcpServers section with:"
- [x] Snippet contains complete mcpServers object, not individual entries
- [x] No "Servers to migrate (remove these)" list shown
- [x] All existing button functionality still works (copy, open editor, etc.)
- [x] Keyboard shortcuts work as documented
- [x] All tests pass (2135 tests passing)
- [x] No regressions in existing functionality

## Edge Cases

1. **No migration instructions**: Show empty state message with Finish button
2. **Single client**: Master panel still shown, client pre-selected
3. **All clients already configured**: All show ⚠️, alerts appear for each
4. **No restore scripts generated**: Restore section omitted from file summary
5. **Very long client names**: Truncate in master panel
6. **Very long file paths**: Truncate with `...`
7. **Back navigation**: State preserved, wizard can continue from ConfigurationSummaryScreen

## Future Enhancements

- **Search/filter**: Add search box above master panel to filter clients
- **Bulk operations**: "Copy All Instructions" to copy all clients at once
- **Progress tracking**: Show checkmarks for clients already updated
- **Expandable sections**: Collapse/expand sections in detail panel
- **Reconnection testing**: Add "Test Connection" button per client (not "Test All")

## References

- Current implementation: `gatekit/tui/screens/setup_complete.py`
- State model: `gatekit/tui/guided_setup/models.py` (GuidedSetupState, already_configured_clients)
- Migration instructions: `gatekit/tui/guided_setup/migration_instructions.py`
- **Shared wizard styles**: `gatekit/tui/styles/wizard.tcss` (MUST USE for consistency)
- Other wizard screens for button layout reference:
  - `gatekit/tui/screens/guided_setup/server_selection.py`
  - `gatekit/tui/screens/guided_setup/config_location.py`
- Textual layouts: https://textual.textualize.io/guide/layout/
- Textual messages: https://textual.textualize.io/guide/events/
