# textual-fspicker Integration for File Operations

## Overview

Replace custom file operation screens (`ConfigSelectorScreen`, `SaveAsModal`) with textual-fspicker library dialogs (`FileOpen`, `FileSave`) to provide standard, maintained file picker UX for configuration file management.

## Motivation

**Why use textual-fspicker:**
- Standard, familiar file picker UX pattern that users recognize
- Maintained by third-party (handles Textual API changes, bugs, edge cases)
- Signals professional engineering practices
- Reduces technical debt and maintenance burden
- Allows focus on Gatekit's core security/auditing features

**Trade-offs accepted:**
- Lose custom metadata preview (server count, modification time in file listing)
- Lose custom path tab-completion (though library has its own path suggestions)
- Different UX (modal dialogs vs full-screen browsers)

**Decision rationale:**
Good enough for v0.1.0 initial release. Standard UX is more important than custom features for this use case.

## Current State

### Save As: ✅ COMPLETED
- `SaveAsModal` replaced with `FileSave` in config_persistence.py
- Working as of integration experiment
- Legacy `save_as_modal.py` slated for deletion in Phase 1

### Open File: 🔄 IN PROGRESS
- `ConfigSelectorScreen` still in use (full-screen file browser)
- Triggered by: startup without config, Ctrl+O binding
- Shows metadata: file modification time, MCP server count, validation status
- Legacy screen will be deleted after FileOpen migration

## Requirements

### Phase 1: Replace ConfigSelectorScreen with FileOpen

#### 1.1 FileOpen Dialog Integration

**Location:** `gatekit/tui/app.py`

Create new async method to show FileOpen modal:

```python
async def _open_config_file_async(self) -> None:
    """Show FileOpen modal and load selected config."""
    from textual_fspicker import FileOpen, Filters

    # Context-aware starting directory:
    # 1. If config already loaded, start where it is (better UX for switching configs)
    # 2. Otherwise, fall back to configs/ directory or cwd
    if self.config_path and self.config_path.parent.exists():
        start_dir = self.config_path.parent
    else:
        configs_dir = Path.cwd() / "configs"
        start_dir = configs_dir if configs_dir.exists() else Path.cwd()

    # Show FileOpen modal with YAML filters
    selected_path = await self.push_screen_wait(
        FileOpen(
            location=start_dir,
            title="Open Configuration File",
            filters=Filters(
                ("YAML", lambda p: p.suffix.lower() in ['.yaml', '.yml']),
                ("All", lambda _: True)
            )
        )
    )

    if selected_path:
        self._load_config(selected_path)
    else:
        # User cancelled - exit if no config loaded yet
        # This differs from ConfigSelectorScreen which had a Quit button
        # but provides better modal UX consistency (Cancel = dismiss)
        if not self.config_path:
            self.exit()
```

**Parameters explained:**
- `location`: Context-aware starting directory (current config's dir, or configs/, or cwd)
- `title`: Modal title shown to user
- `filters`: File type filtering (YAML files or all)

**Return behavior:**
- Returns `Path` if user selects a file
- Returns `None` if user cancels (Escape or Cancel button)

**Cancel behavior change:**
- **Old (ConfigSelectorScreen):** Full-screen with Quit button; user must explicitly quit
- **New (FileOpen modal):** Cancel dismisses modal; exits app only if no config loaded
- **Rationale:** Modal pattern matches Save As; clearer user intent (Cancel vs Quit)

#### 1.2 Update _show_config_selector()

**Location:** `gatekit/tui/app.py`

**Current behavior:**
```python
def _show_config_selector(self) -> None:
    """Show config selector screen directly."""
    from .screens.config_selector import ConfigSelectorScreen

    configs_dir = Path.cwd() / "configs"
    start_dir = configs_dir if configs_dir.exists() else Path.cwd()
    self.push_screen(ConfigSelectorScreen(start_dir))
```

**New behavior:**
```python
def _show_config_selector(self) -> None:
    """Show file picker modal to open a config."""
    self.run_worker(self._open_config_file_async())
```

**Why run_worker():**
- FileOpen uses `push_screen_wait()` (async)
- Must be called from async context
- `run_worker()` handles async execution in sync context
- Uses default error handling (exit_on_error=True) so failures are visible
- Errors in file selection will crash the app visibly rather than silently failing

#### 1.3 Update action_back_to_selector() in Config Editor

**Location:** `gatekit/tui/screens/config_editor/base.py:1282`

**CRITICAL:** This action is bound to Escape key in config editor and currently creates a ConfigSelectorScreen. Must be updated to use the new modal flow.

**Current behavior:**
```python
def action_back_to_selector(self) -> None:
    """Return to configuration selector."""
    # Replace this screen with the config selector
    from ..config_selector import ConfigSelectorScreen
    from pathlib import Path

    configs_dir = Path.cwd() / "configs"
    start_dir = configs_dir if configs_dir.exists() else Path.cwd()

    # Replace current screen with config selector
    config_selector = ConfigSelectorScreen(start_dir)
    self.app.switch_screen(config_selector)
```

**New behavior:**
```python
def action_back_to_selector(self) -> None:
    """Return to configuration selector."""
    # Delegate to app's existing method that handles the modal flow
    self.app._show_config_selector()
```

**Why delegate to app._show_config_selector():**
- Reuses existing worker setup (no duplication)
- Consistent error handling (no silent failures)
- Single source of truth for file opening flow
- Simpler implementation (no async complexity in sync action)

**Why this matters:**
- Escape key in editor currently triggers this action
- If not updated, users get old full-screen selector
- Creates inconsistent UX (modal from Ctrl+O, full-screen from Escape)
- Prevents full deprecation of ConfigSelectorScreen
- Without this fix, the migration is incomplete

#### 1.4 Remove legacy ConfigSelectorScreen implementation

**Location:** `gatekit/tui/screens/config_selector.py`

- Delete the module entirely (no longer shipped in v0.1.0)
- Remove any imports/exports referencing `ConfigSelectorScreen`
  - Update `gatekit/tui/screens/__init__.py`
  - Remove dead code paths that referenced the screen
- Document removal in CHANGELOG (see user-facing docs section)

**Rationale:**
- Keeps codebase lean for first release (no rollback-only baggage)
- Git history preserves implementation if we ever need to resurrect it
- Avoids confusion during future feature work or refactors

#### 1.5 Remove legacy SaveAsModal implementation

**Location:** `gatekit/tui/screens/save_as_modal.py`

- Delete the module (already replaced by textual-fspicker `FileSave`)
- Remove exports/imports and update any docs/tests still mentioning it
- Ensure `config_persistence.py` no longer references the old class (already verified)

**Rationale:**
- Matches decision to retire custom file pickers entirely
- Eliminates unused test fixtures and dead UI assets

## Implementation Details

### FileOpen API Parameters

From textual-fspicker 0.6.0:

```python
FileOpen(
    location: str | Path = '.',           # Starting directory
    title: str = 'Open',                  # Modal title
    *,
    open_button: ButtonLabel = '',        # Customize "Open" button label
    cancel_button: ButtonLabel = '',      # Customize "Cancel" button label
    filters: Filters | None = None,       # File type filters
    must_exist: bool = True,              # File must exist to select
    default_file: str | Path | None = None,  # Pre-fill filename
    double_click_directories: bool = True,   # Double-click to navigate
    suggest_completions: bool = True      # Enable path suggestions
)
```

**For our use case:**
- `location`: Context-aware (current config's parent, or configs/, or cwd)
- `title`: "Open Configuration File"
- `filters`: YAML only filter
- Rest: Use defaults

### FileSave API Parameters (for reference)

Already implemented:

```python
FileSave(
    location: str | Path = '.',           # Starting directory (NOT file path!)
    title: str = 'Save as',               # Modal title
    *,
    save_button: ButtonLabel = '',        # Customize button
    cancel_button: ButtonLabel = '',
    filters: Filters | None = None,
    can_overwrite: bool = True,           # Allow overwriting files
    default_file: str | Path | None = None,  # Pre-fill filename
    suggest_completions: bool = True
)
```

**Current usage in config_persistence.py:**
```python
FileSave(
    location=self.config_file_path.parent,  # Start in file's directory
    default_file=self.config_file_path.name  # Pre-fill current filename
)
```

### Filters Usage

The `Filters` class creates file type filters:

```python
from textual_fspicker import Filters

Filters(
    ("YAML", lambda p: p.suffix.lower() in ['.yaml', '.yml']),
    ("All", lambda _: True)
)
```

**Tuple format:** `(label: str, filter_function: Callable[[Path], bool])`

**Renders as:** Dropdown in modal showing "YAML" and "All" options

## User Experience Changes

### Before (ConfigSelectorScreen)

**Startup without config:**
```
┌──────────────────────────────────────────┐
│     Choose a Configuration File          │
├──────────────────────────────────────────┤
│ Current directory: configs/              │ ← Editable
├──────────────────────────────────────────┤
│ Name          Modified    MCP Servers    │
│ ──────────────────────────────────────── │
│ gatekit.yaml  2h ago    filesystem     │
│ test.yaml       Yesterday  None          │
│ demo/prod.yaml  2d ago    fs, brave      │
│                                          │
├──────────────────────────────────────────┤
│    [Select] [Refresh] [Quit]             │
└──────────────────────────────────────────┘
```

**Features:**
- Full-screen display
- Metadata: modification time, server count
- Directory browser modal (Ctrl+D)
- Shows validation status (Invalid YAML, Parse error)

### After (FileOpen from textual-fspicker)

**Startup without config:**
```
┌──────────────────────────────────────────┐
│      Open Configuration File             │
├──────────────────────────────────────────┤
│ configs/                                 │ ← Read-only display
├──────────────────────────────────────────┤
│ 📁 ..                                    │
│ 📄 gatekit.yaml                        │
│ 📄 test.yaml                             │
│ 📁 demo/                                 │
│   ├─ 📄 prod.yaml                        │
│   └─ 📄 dev.yaml                         │
│                                          │
├──────────────────────────────────────────┤
│ gatekit.yaml     [YAML ▾]              │
│                [Open] [Cancel]            │
└──────────────────────────────────────────┘
```

**Features:**
- Modal dialog (not full-screen)
- Tree-based navigation
- Path typing in filename input
- Path suggestions (library's own)
- File type filter dropdown
- Standard UX pattern

**Lost features:**
- ❌ Metadata preview (mod time, server count)
- ❌ Custom tab-completion with common paths
- ❌ Validation status preview

**Gained features:**
- ✅ Standard, familiar UX
- ✅ Maintained library (bug fixes, updates)
- ✅ Modal pattern (consistent with Save As)

## Testing Plan

### Manual Testing Checklist

**Scenario 1: Startup without config**
- [ ] Start TUI: `gatekit`
- [ ] FileOpen modal appears
- [ ] Starts in `configs/` directory (if exists)
- [ ] YAML filter dropdown works
- [ ] Can navigate directories via tree
- [ ] Can type path in filename input
- [ ] Can select .yaml file
- [ ] File loads and editor opens
- [ ] Cancel closes app (no config loaded)

**Scenario 2: Open from editor (Ctrl+O)**
- [ ] Start with config: `gatekit --config configs/gatekit.yaml`
- [ ] Press Ctrl+O
- [ ] FileOpen modal appears
- [ ] Can select different config
- [ ] New config loads
- [ ] Cancel returns to current config

**Scenario 3: Path typing**
- [ ] Type full path in input: `configs/test.yaml`
- [ ] Press Enter or click Open
- [ ] File loads correctly
- [ ] Type partial path: `test`
- [ ] Path suggestions appear
- [ ] Can autocomplete

**Scenario 4: File filtering**
- [ ] Switch filter to "All"
- [ ] Non-YAML files visible
- [ ] Switch back to "YAML"
- [ ] Only .yaml/.yml files shown

**Scenario 5: Navigation**
- [ ] Double-click directory in tree
- [ ] Directory opens
- [ ] Click ".." entry
- [ ] Navigates to parent
- [ ] Keyboard navigation (arrows, enter)
- [ ] Works correctly

**Scenario 6: Error handling**
- [ ] Select invalid YAML file
- [ ] Error modal appears (existing ConfigErrorModal)
- [ ] Can retry or cancel
- [ ] Select non-existent file
- [ ] Appropriate error shown

**Scenario 7: Save As (regression test)**
- [ ] Open config in editor
- [ ] Press Ctrl+Shift+S
- [ ] FileSave modal appears
- [ ] Pre-filled with current filename
- [ ] Can save to new location
- [ ] Overwrite confirmation works

### Integration Testing

**Automated test required (minimum):**

Add to `tests/unit/tui/test_file_open_integration.py`:

```python
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
import pytest

from gatekit.tui.app import GatekitConfigApp

async def test_open_config_file_async_success():
    """Test FileOpen modal integration with successful config loading."""
    app = GatekitConfigApp()
    test_config_path = Path("configs/test.yaml")

    async with app.run_test() as pilot:
        # CRITICAL: Use AsyncMock since push_screen_wait is async
        mock_push = AsyncMock(return_value=test_config_path)

        with patch.object(app, 'push_screen_wait', mock_push):
            with patch.object(app, '_load_config') as mock_load:
                await app._open_config_file_async()

                # Verify FileOpen was shown
                assert mock_push.called
                # Verify _load_config was called with selected path
                mock_load.assert_called_once_with(test_config_path)

async def test_open_config_file_async_cancel_with_config():
    """Test FileOpen cancellation when config already loaded."""
    app = GatekitConfigApp(config_path=Path("existing.yaml"))

    async with app.run_test() as pilot:
        # Mock push_screen_wait to return None (user cancelled)
        mock_push = AsyncMock(return_value=None)

        with patch.object(app, 'push_screen_wait', mock_push):
            with patch.object(app, 'exit') as mock_exit:
                await app._open_config_file_async()

                # Should NOT exit when config already loaded
                mock_exit.assert_not_called()

async def test_open_config_file_async_cancel_no_config():
    """Test FileOpen cancellation when no config loaded."""
    app = GatekitConfigApp()  # No config_path

    async with app.run_test() as pilot:
        # Mock push_screen_wait to return None (user cancelled)
        mock_push = AsyncMock(return_value=None)

        with patch.object(app, 'push_screen_wait', mock_push):
            with patch.object(app, 'exit') as mock_exit:
                await app._open_config_file_async()

                # SHOULD exit when no config loaded
                mock_exit.assert_called_once()
```

**Test requirements:**
- Use `AsyncMock` for `push_screen_wait` (returns awaitable)
- Use `MagicMock` for sync methods like `_load_config`, `exit`
- Import from `unittest.mock` (standard library)
- Test with `app.run_test()` context manager (Textual testing)

**Test existing flows still work:**
- Config loading with validation (via _load_config)
- Config error modal display (invalid YAML files)
- Editor opening after selection
- App exit on cancel (no config scenario)
- App return to editor on cancel (config loaded scenario)

## Files Modified

### Primary Changes
1. **gatekit/tui/app.py**
   - Add `_open_config_file_async()` method
   - Update `_show_config_selector()` to use worker

2. **gatekit/tui/screens/config_editor/base.py**
   - Update `action_back_to_selector()` to use new modal flow (line 1282)
   - Change from `ConfigSelectorScreen` instantiation to `app._show_config_selector()`

3. **gatekit/tui/screens/config_selector.py**
   - Remove file (legacy full-screen picker deleted)

4. **gatekit/tui/screens/save_as_modal.py**
   - Remove file (legacy save modal deleted)

5. **gatekit/tui/screens/__init__.py**
   - Drop exports for removed screens

### Already Completed (Phase 0)
1. **pyproject.toml** ✅
   - Added `textual-fspicker==0.6.0` dependency

2. **gatekit/tui/screens/config_editor/config_persistence.py** ✅
   - Replaced `SaveAsModal` with `FileSave`

### User-Facing Documentation
4. **CHANGELOG.md** (or equivalent)
   - Document UX change and lost features
   - Example entry:
     ```markdown
     ### Changed in v0.1.0
     - File opening now uses standard modal dialog (textual-fspicker) instead of
       custom full-screen browser
     - **Lost:** Metadata preview (modification time, server count in file list)
     - **Lost:** Custom path tab-completion (library provides basic path suggestions)
     - **Gained:** Standard, familiar UX pattern
     - **Gained:** Maintained third-party library (reduced maintenance burden)
     ```

5. **Release notes / migration guide**
   - Notify users of UX change
   - Explain why (focus on core features, standard UX)
   - Provide feedback channel if metadata preview is missed

### Test Coverage

6. **tests/unit/tui/test_file_open_integration.py** (new file)
   - Test successful file selection and loading
   - Test cancel behavior (with and without config loaded)
   - Test error handling in async flow
   - Uses `AsyncMock` for awaitable mocks
   - Uses `MagicMock` for sync method mocks

7. **tests/unit/test_tui_config_selector.py**
   - Remove file (legacy picker tests deleted)

### No Changes Required
- **gatekit/tui/app.py** `action_open_config()` - Already calls `_show_config_selector()`
- **gatekit/tui/app.py** `on_mount()` - Already calls `_show_config_selector()`

## Rollback Strategy

If FileOpen doesn't meet needs:

**Quick revert (via history):**
1. Restore `gatekit/tui/screens/config_selector.py` and `gatekit/tui/screens/save_as_modal.py` from git history (e.g., `git checkout <commit> -- <path>`)
2. Revert changes to `gatekit/tui/app.py` and `gatekit/tui/screens/config_editor/base.py`
3. Re-run tests covering the restored flows (legacy unit tests can be resurrected from history if needed)

**Longer-term options:**
1. Extend FileOpen via subclassing to add metadata
2. Build custom modal inspired by textual-fspicker design
3. Re-introduce custom screens only if future requirements demand bespoke UX

## Success Criteria

**Phase 1 is complete when:**
- [ ] FileOpen replaces ConfigSelectorScreen for all file opening
- [ ] `_show_config_selector()` updated in app.py
- [ ] `action_back_to_selector()` updated in config_editor/base.py (Escape key)
- [ ] Legacy `ConfigSelectorScreen`/`SaveAsModal` modules deleted
- [ ] Legacy selector tests deleted
- [ ] All manual tests pass
- [ ] Integration tests added and passing (with AsyncMock)
- [ ] No regressions in existing config loading/error handling
- [ ] User can open configs via startup, Ctrl+O, and Escape key
- [ ] Code is simpler (fewer custom screens to maintain)
- [ ] User-facing documentation updated (CHANGELOG, release notes)

**Long-term success:**
- Users find file picker intuitive and professional
- No critical metadata features are missed
- textual-fspicker updates don't break functionality
- Reduced maintenance burden vs custom screens

## Dependencies

**Required:**
- textual-fspicker==0.6.0 (already added to pyproject.toml)
- textual>=0.47.0 (already required)

**Compatibility:**
- Tested with Textual 5.3.0
- Python ≥3.10

## Future Enhancements (Optional)

**If metadata preview is needed:**
1. Subclass `FileOpen` to add metadata panel
2. Hook into file selection events
3. Display server count, mod time below file tree
4. More complex but keeps library benefits

**If custom path input is needed:**
1. Subclass `FileOpen`
2. Override `_input_bar()` method
3. Replace Input with custom PathInput (with tab completion)
4. Requires understanding library internals (coupling risk)

**Decision:** Ship without these for v0.1.0, evaluate based on user feedback.

## QC Review Findings (Addressed)

### Round 1 Review

**High Priority:**
- ✅ **Fixed:** Removed `exit_on_error=False` from `run_worker()` call
  - Now uses default error handling so failures are visible
  - Prevents silent error swallowing in file selection flow

**Medium Priority:**
- ✅ **Fixed:** Made FileOpen starting directory context-aware
  - Starts in current config's parent if config already loaded
  - Falls back to configs/ or cwd for initial startup
  - Better user experience when switching between configs

- ✅ **Documented:** Cancel behavior difference from ConfigSelectorScreen
  - Old: Full-screen with explicit Quit button
  - New: Modal with Cancel (dismisses, exits only if no config loaded)
  - Rationale: Modal pattern consistency with Save As

- ✅ **Added:** Integration test requirements
  - Minimum: 3 test cases covering success, cancel with/without config
  - Tests verify _load_config integration and error handling

**Suggestions:**
- ✅ **Updated:** Legacy picker strategy now mandates deletion
  - Custom screens removed rather than left deprecated
  - Keeps repository focused on textual-fspicker flow for v0.1.0

- ✅ **Added:** User-facing documentation requirements
  - CHANGELOG entry documenting lost/gained features
  - Release notes explaining the change
  - Feedback channel for users who miss metadata preview

### Round 2 Review

**High Priority:**
- ✅ **Fixed:** Added `action_back_to_selector()` update to plan
  - Found at `gatekit/tui/screens/config_editor/base.py:1282`
  - Bound to Escape key in config editor
  - Currently instantiates ConfigSelectorScreen (blocks full migration)
  - Updated to use `app._show_config_selector()` (delegates properly)
  - Without this fix, migration is incomplete

### Round 3 Review

**High Priority:**
- ✅ **Fixed:** Removed bad pattern from `action_back_to_selector()` example
  - Removed Option 1 with `exit_on_error=False` (reintroduced silent errors!)
  - Now shows only the correct approach: `self.app._show_config_selector()`
  - Prevents copy-paste of unsafe pattern
  - Consistent with Round 1 fix (no error swallowing)

**Medium Priority:**
- ✅ **Updated:** Plan now deletes legacy picker modules (`ConfigSelectorScreen`, `SaveAsModal`)
  - Modules removed from codebase instead of left for rollback
  - `gatekit/tui/screens/__init__.py` updated to drop exports
  - Ensures only textual-fspicker flows ship in v0.1.0

- ✅ **Fixed:** Integration test code now uses `AsyncMock`
  - Old (broken): `patch.object(app, 'push_screen_wait', return_value=path)`
  - New (correct): `AsyncMock(return_value=path)` for awaitable
  - Added imports: `from unittest.mock import AsyncMock, MagicMock`
  - Tests will now actually run without exploding

- ✅ **Resolved:** Removed legacy selector tests
  - Deleted `tests/unit/test_tui_config_selector.py`
  - Keeps CI focused on active FileOpen flow
  - History retains old tests if rollback ever needed

## References

- textual-fspicker docs: https://textual-fspicker.davep.dev/
- textual-fspicker GitHub: https://github.com/davep/textual-fspicker
- SaveAsModal replacement commit: [to be filled in after implementation]
- FileOpen integration commit: [to be filled in after implementation]
