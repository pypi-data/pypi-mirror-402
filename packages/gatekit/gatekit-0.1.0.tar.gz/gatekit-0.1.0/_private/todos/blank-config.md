# Create Blank Configuration from TUI Welcome Screen

## Summary

Implement "Create New" functionality that opens the config editor with an empty in-memory configuration. No file is created until the user saves. On first save, a FileSave dialog prompts for the filename. Saving is blocked if zero servers are configured.

## Current State

- Welcome screen has "Create New" button (button_id="create_new")
- Button dismisses with `"create_new"` string
- `app.py` shows warning: "Create New not yet implemented"
- `ProxyConfigSchema` and `ProxyConfig` both require at least one upstream server

## Design Decisions

1. **No file until save** - "Create New" opens editor with empty config in memory, no file path
2. **Empty config allowed in editor** - Empty upstreams list allowed during editing
3. **Block save without servers** - Must have at least one (non-draft) server to save
4. **FileSave on first save** - New documents prompt for filename on first save attempt

## Implementation Tasks

### Task 1: Add `ProxyConfig.create_empty_for_editing()` Factory Method

**File:** `gatekit/config/models.py`

Add class method that bypasses `__post_init__` validation:

```python
@classmethod
def create_empty_for_editing(cls) -> "ProxyConfig":
    """Create an empty config for TUI editing (bypasses validation).

    Used for "Create New" workflow where config starts empty and
    validation happens at save time.
    """
    instance = object.__new__(cls)
    instance.transport = "stdio"
    instance.upstreams = []
    instance.timeouts = TimeoutConfig()
    instance.http = None
    instance.plugins = None
    instance.logging = None
    return instance
```

### Task 2: Make `config_file_path` Optional in ConfigEditorScreen

**File:** `gatekit/tui/screens/config_editor/base.py`

Change `__init__` signature:
```python
def __init__(
    self,
    config_file_path: Optional[Path],  # Changed from Path
    loaded_config: ProxyConfig,
    initial_plugin_modal: Optional[PluginModalTarget] = None,
):
```

Add property to check if new document:
```python
@property
def is_new_document(self) -> bool:
    """True if this is a new unsaved document."""
    return self.config_file_path is None
```

### Task 3: Update Header Display for New Documents

**File:** `gatekit/tui/screens/config_editor/config_persistence.py`

`_update_header()` currently uses `self.config_file_path.name` which will fail if path is None.

Update to:
```python
def _update_header(self) -> None:
    """Update header to show dirty state."""
    try:
        dirty_indicator = " *" if self._config_dirty else ""
        if self.config_file_path:
            self.sub_title = f"{self.config_file_path.name}{dirty_indicator}"
        else:
            self.sub_title = f"[New Configuration]{dirty_indicator}"
    except Exception:
        pass
```

### Task 4: Guard Methods That Assume File Path Exists

**Files:**
- `gatekit/tui/screens/config_editor/base.py`
- `gatekit/tui/screens/config_editor/config_persistence.py`

These methods dereference `config_file_path.parent` and need guards for `config_file_path is None`:

1. **`_initialize_plugin_system()`** (base.py:604) - **CRITICAL: runs during `on_mount`, will crash immediately**
   ```python
   config_dir = self.config_file_path.parent if self.config_file_path else Path.cwd()
   self.plugin_manager = PluginManager(
       plugins_config, config_directory=config_dir
   )
   ```

2. `_rebuild_runtime_state()` (config_persistence.py) - Same pattern as above

3. `_load_config_from_disk()` - Should never be called for new document (add assertion)
   ```python
   def _load_config_from_disk(self) -> ProxyConfig:
       assert self.config_file_path is not None, "Cannot load from disk for new document"
       # ... existing code
   ```

4. `_reset_runtime_from_disk()` - Same, add guard

### Task 5: Update Save Logic to Handle New Documents

**File:** `gatekit/tui/screens/config_editor/config_persistence.py`

First, add a shared validation helper to enforce "must have ≥1 completed server" rule across ALL save entry points:

```python
def _validate_can_save(self) -> bool:
    """Check if config is valid for saving. Returns False and shows warning if not."""
    # Check for empty upstreams
    if not self.config.upstreams:
        self.app.notify(
            "At least one MCP server must be configured before saving.",
            severity="warning"
        )
        return False

    # Check that at least one server is complete (not draft)
    has_complete_server = any(
        not getattr(u, 'is_draft', False) for u in self.config.upstreams
    )
    if not has_complete_server:
        self.app.notify(
            "At least one MCP server must be fully configured before saving. "
            "Complete the server configuration (command or URL required).",
            severity="warning"
        )
        return False

    return True
```

**Why check for drafts here?** Without this, a user with only draft servers would:
1. Click Save → see FileSave dialog → pick location
2. Then get confusing error from `config_to_dict()` about drafts
Better UX: show clear warning before any modal interaction.

Modify `_save_config_with_notification()`:

```python
async def _save_config_with_notification(self) -> None:
    """Save config and show appropriate notification."""
    # Validate before any save attempt
    if not self._validate_can_save():
        return

    # New document needs Save As flow
    if self.is_new_document:
        await self._save_config_as_with_modal()
        return

    # Existing document - normal save
    # ... existing code ...
```

### Task 6: Update Save As for New Documents

**File:** `gatekit/tui/screens/config_editor/config_persistence.py`

Modify `_save_config_as_with_modal()` to:
1. **Use shared validation** - Users can hit Ctrl+Shift+S directly, bypassing normal save
2. Handle new documents (no existing path)

```python
async def _save_config_as_with_modal(self) -> None:
    """Show Save As modal and save configuration to new path."""
    # IMPORTANT: Validate here too - user can trigger Save As directly via Ctrl+Shift+S
    if not self._validate_can_save():
        return

    from textual_fspicker import FileSave

    # Determine start location
    if self.config_file_path:
        start_dir = self.config_file_path.parent
        default_file = self.config_file_path.name
    else:
        # New document - use configs dir or cwd
        configs_dir = Path.cwd() / "configs"
        start_dir = configs_dir if configs_dir.exists() else Path.cwd()
        default_file = "gatekit.yaml"

    new_path = await self.app.push_screen_wait(
        FileSave(location=start_dir, default_file=default_file)
    )
    # ... rest of existing implementation handles overwrite confirmation and save
```

### Task 7: Handle "create_new" in app.py

**File:** `gatekit/tui/app.py`

Replace the stub (lines 482-485) with:

```python
elif result == "create_new":
    self._create_new_config()

def _create_new_config(self) -> None:
    """Create new configuration in editor (no file yet)."""
    from gatekit.config.models import ProxyConfig
    from .screens.config_editor import ConfigEditorScreen

    empty_config = ProxyConfig.create_empty_for_editing()

    # NOTE: App-level state (self.config_path, self.config_exists) stays as-is
    # until first save. This is intentional - no file exists yet.
    # After first save, the editor updates these via callback (see Task 7b).
    # See also Task 7c for handling Ctrl+O cancel behavior.

    editor_screen = ConfigEditorScreen(
        config_file_path=None,  # New document, no path yet
        loaded_config=empty_config,
        initial_plugin_modal=None,
    )
    self.push_screen(editor_screen)
```

### Task 7c: Fix Ctrl+O Cancel Behavior for New Documents

**File:** `gatekit/tui/app.py`

**Problem:** When `config_exists=False` (new document), pressing Ctrl+O then Cancel dumps the user back to welcome screen, losing their editing session (lines 465-467).

**Solution:** Check if currently in ConfigEditorScreen before returning to welcome:

```python
async def _open_config_file_async(self) -> None:
    # ... existing code ...

    if selected_path:
        self._load_config(selected_path)
    else:
        # User cancelled
        from .screens.config_editor import ConfigEditorScreen

        # If we're in the config editor (including new documents), stay there
        if isinstance(self.screen, ConfigEditorScreen):
            return  # Just dismiss picker, keep editor open

        if not self.config_exists:
            # No config loaded and not in editor - return to welcome screen
            self._show_welcome_screen()
        # else: Config already loaded, just dismiss the picker (no action needed)
```

**Why not set `config_exists=True`?** The semantic meaning of `config_exists` should remain "a file exists on disk". A new unsaved document doesn't have a file yet, so we shouldn't lie about that. Instead, we check the screen type to determine behavior.

### Task 7b: Update App State After First Save

**File:** `gatekit/tui/screens/config_editor/config_persistence.py`

**IMPORTANT:** Capture `was_new_document` BEFORE setting `config_file_path`, otherwise `is_new_document` will already be `False`:

```python
async def _save_config_as_with_modal(self) -> None:
    # ... validation and FileSave dialog ...

    # CRITICAL: Capture this BEFORE setting config_file_path
    was_new_document = self.is_new_document  # or: self.config_file_path is None

    # Store old path in case we need to rollback
    old_path = self.config_file_path

    try:
        # Update config file path to new location
        self.config_file_path = new_path

        # Save to new path
        success = await self._save_and_rebuild()

        if success:
            self._mark_clean()
            # ... existing success handling ...

            # Update app-level state for first save of new document
            if was_new_document:
                self.app.config_path = self.config_file_path
                self.app.config_exists = True
        else:
            # Save failed, rollback to old path
            self.config_file_path = old_path
            self._update_header()
```

This ensures:
- `self.app.config_path` reflects the saved file path
- `self.app.config_exists = True` so UX hooks behave correctly
- File picker start directories use the new config's location

### Task 7d: Handle Save Failure for New Documents

**File:** `gatekit/tui/screens/config_editor/config_persistence.py`

**Problem:** `_save_and_rebuild()` calls `_load_config_from_disk()` on save failure (line 99). For a new document where the first save fails (permission denied, disk full), the file doesn't exist yet, so the reload crashes.

**Solution:** Modify `_save_and_rebuild()` to skip reload when there's no file to reload from:

```python
async def _save_and_rebuild(self) -> bool:
    """Save configuration and rebuild runtime state with concurrency safety."""
    async with self._save_lock:
        if not await self._persist_config():
            # Only reload from disk if file exists (not for new documents)
            if self.config_file_path and self.config_file_path.exists():
                # Reload from disk to discard in-memory drift
                self.config = self._load_config_from_disk()

                self.app.notify(
                    "Configuration reverted to last saved state due to save failure",
                    severity="warning",
                )

                # Refresh runtime state from disk
                await self._reset_runtime_from_disk()

                # Clear dirty flag since we've reverted to the last saved state
                self._mark_clean()
            else:
                # New document or file doesn't exist - keep in-memory config
                self.app.notify(
                    "Failed to save configuration. Your changes are still in memory.",
                    severity="error",
                )
                # Keep dirty flag - user needs to try saving again

            return False

        await self._rebuild_runtime_state()
        return True
```

**Why this matters:** Without this fix, a permission error on first save would crash the editor instead of gracefully keeping the user's work.

### Task 8: Handle New Document Dirty State

**File:** `gatekit/tui/screens/config_editor/base.py`

**Problem:** Current `__init__` (lines 435-436) sets `_config_dirty=False` and computes hash. For new empty documents, this incorrectly shows as "clean" when it should always appear dirty until first save.

**Solution:** Initialize dirty state based on whether this is a new document:

```python
# In __init__, after setting config_file_path:
# Dirty state tracking
if self.config_file_path is None:
    # New document - always dirty until first save
    self._config_dirty = True
    self._last_saved_config_hash = ""  # No saved state to compare against
else:
    # Existing document - start clean
    self._config_dirty = False
    self._last_saved_config_hash = self._compute_config_hash()
```

**Why this works:**
- `_config_dirty=True` ensures header shows `*` indicator
- `_last_saved_config_hash=""` means `_mark_clean()` will fail to mark clean (empty hash check on line 397)
- After first save sets `config_file_path`, normal dirty tracking resumes
- `_compute_config_hash()` returns `""` for unsaveable configs anyway, so this is consistent

### Task 9: Add to Recent Files After First Save

**File:** `gatekit/tui/screens/config_editor/config_persistence.py`

After successful first save of new document (in `_save_config_as_with_modal`), add to recent files:
```python
from gatekit.tui.recent_files import RecentFiles
recent_files = RecentFiles()
recent_files.add(self.config_file_path)
```

(Note: This is already done in the existing Save As implementation)

### Task 10: Tests

**Files:**
- `tests/unit/test_config_models.py` - Test `create_empty_for_editing()`
- `tests/unit/tui/test_config_editor_new_document.py` - Test new document flow

Test cases:
1. `create_empty_for_editing()` returns valid empty config with no upstreams
2. Empty config has `transport="stdio"` and empty upstreams list
3. New document has `is_new_document == True`
4. Save blocked with empty upstreams (warning shown) - via Ctrl+S
5. Save blocked with empty upstreams (warning shown) - via Ctrl+Shift+S (Save As)
6. Save blocked when only draft upstreams exist (warning shown) - via Ctrl+S
7. Save blocked when only draft upstreams exist (warning shown) - via Ctrl+Shift+S
8. FileSave shown on first save of new document (with at least one complete server)
9. After save, `is_new_document == False` (path is set)
10. After save, `app.config_path` and `app.config_exists` updated
11. File added to recent files after first save
12. Header shows "[New Configuration] *" for new documents (dirty indicator)
13. Header shows filename after save
14. New document starts with `_config_dirty=True`
15. Screen mounts without crash (guards `_initialize_plugin_system`)
16. Ctrl+O then Cancel keeps editor open for new document (doesn't dump to welcome)
17. Save failure on new document doesn't crash (no file to reload from)
18. Save failure on new document keeps in-memory config intact

## Critical Files Summary

| File | Change |
|------|--------|
| `gatekit/config/models.py` | Add `create_empty_for_editing()` factory |
| `gatekit/tui/screens/config_editor/base.py` | Optional `config_file_path`, `is_new_document` property, guard `_initialize_plugin_system()`, conditional dirty state init |
| `gatekit/tui/screens/config_editor/config_persistence.py` | Add `_validate_can_save()` helper (checks empty + drafts), handle new document save flow, fix methods that assume path exists, update app state after save, handle save failure gracefully for new docs |
| `gatekit/tui/app.py` | Handle "create_new" result, fix Ctrl+O cancel for new documents |

## Edge Cases

1. **User cancels FileSave** - Return to editor, doc remains unsaved
2. **File already exists** - FileSave widget handles overwrite confirmation (existing code)
3. **Save fails** - Show error, path remains None (still new document)
4. **Quit with unsaved new document** - Existing dirty check should prompt for save
5. **All servers deleted** - Config becomes empty, save blocked with warning
6. **Direct Save As on empty config** - Ctrl+Shift+S blocked with same warning as Ctrl+S
7. **Only draft servers exist** - Save blocked with clear message about completing config
8. **Ctrl+O then Cancel on new document** - Stay in editor, don't lose work
9. **First save fails (permission/disk)** - Keep in-memory config, don't try to reload nonexistent file
