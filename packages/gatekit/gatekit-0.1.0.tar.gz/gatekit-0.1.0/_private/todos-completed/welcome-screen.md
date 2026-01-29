# TUI Welcome Screen with Recent Files

## Overview

Implement a full-screen welcome screen for the Gatekit TUI that displays on startup, prominently featuring recently opened configuration files to allow quick access while also providing options for new users to create configurations or use guided setup.

## Problem Statement

Currently, when a user runs `gatekit` without arguments, the TUI immediately shows a file picker dialog. This creates several issues:

1. **Poor first-run experience**: New users without a configuration file don't have guidance on how to get started
2. **No recent files access**: Experienced users must navigate the file picker every time, even for frequently-used configs
3. **Missing guided setup option**: No clear path for users who want assistance creating their first configuration
4. **No onboarding flow**: The immediate file picker doesn't communicate what Gatekit is or how to use it

## Requirements

### Functional Requirements

#### FR-1: Welcome Screen Display
- Display a full-screen welcome interface on TUI startup
- Show unless explicitly disabled via command-line argument
- Include application branding ("Gatekit Configuration Editor")
- Provide clear visual hierarchy with recent files as primary focus

#### FR-2: Recent Files Management
- Track up to 10 most recently opened configuration files
- Store recent files list in cross-platform state directory using our own path resolution
- Display recent files with:
  - Filename (basename)
  - Parent directory path (relative if in cwd, otherwise shortened)
  - Last opened timestamp (humanized: "2 hours ago", "yesterday", etc.)
- Filter out files that no longer exist when displaying
- Allow user to clear recent files list
- Update recent files list on successful file open and save operations

#### FR-3: Primary Actions
- **Open existing file**: Launch file picker to select a config file
- **Create new configuration**: Start with blank editor or template selector
- **Guided setup**: Launch interactive wizard to create first configuration (recommended for new users)
- **Open recent file**: Click/select any recent file to open immediately

#### FR-4: User Preferences and Empty State
- Respect command-line flag to re-enable welcome screen
- Skip welcome screen if config file provided via CLI argument
- Show helpful empty state when no recent files exist
- Recommend guided setup for first-time users
- Provide all primary actions even without recent files

### Non-Functional Requirements

#### NFR-1: Cross-Platform State Storage
- Implement our own cross-platform path resolution (no external dependencies)
- Store recent files in user state directory:
  - Linux: `~/.local/state/gatekit/recent.json` (XDG_STATE_HOME)
  - macOS: `~/Library/Application Support/gatekit/recent.json`
  - Windows: `%LOCALAPPDATA%\gatekit\recent.json`
- Follow XDG Base Directory Specification on Linux
- Set secure directory permissions (0700 on Unix)
- Handle corrupted state files gracefully (recreate)

#### NFR-2: Performance
- Welcome screen should appear quickly on app launch (target <200ms on local filesystems)
- Recent files list must load synchronously (no spinner needed)
- File existence checks are synchronous but fast for local files (note: network filesystems may be slower)

#### NFR-3: Accessibility
- Full keyboard navigation support (arrow keys, Enter, Tab, Esc)
- Mouse support for all interactive elements
- Clear visual focus indicators
- Tooltips showing full paths on hover

#### NFR-4: Error Handling
- Handle missing/corrupted recent.json file gracefully
- Handle permission errors accessing state directory
- Handle file paths with special characters or very long names
- Never crash due to state management issues

## Technical Design

### Architecture

```
GatekitApp
├── on_mount()
│   └── Checks: skip_welcome setting OR CLI args?
│       ├── Yes → push ConfigEditorScreen
│       └── No → push WelcomeScreen
│
├── WelcomeScreen (Screen[str])
│   ├── compose() - Build full-screen UI
│   ├── on_mount() - Load recent files
│   ├── on_button_pressed() - Handle action buttons
│   └── dismiss(choice) - Return user choice to app
│
└── RecentFiles (utility class)
    ├── add(path) - Add/update recent file
    ├── get_all() - Get all recent files (filtered)
    ├── remove(path) - Remove specific file
    └── clear() - Clear all recent files
```

### Data Structures

**Recent Files JSON Format:**
```json
{
  "version": 1,
  "max_items": 10,
  "recent_files": [
    {
      "path": "/Users/user/configs/gatekit.yaml",
      "last_opened": "2025-10-11T14:30:22Z",
      "display_name": "gatekit.yaml"
    }
  ]
}
```

**RecentFiles Class:**
```python
class RecentFiles:
    def __init__(self, max_items: int = 10)
    def add(self, file_path: Path) -> None
    def get_all(self) -> List[dict]
    def remove(self, file_path: Path) -> None
    def clear(self) -> None
    def _save(self, recent: List[dict]) -> None  # Writes atomically (temp + replace)
```

### UI Layout (Option 1 - Card Style)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  Gatekit Configuration Editor            ┃  ← Header
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
│                                             │
│  Recent Files                               │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ 📄 gatekit.yaml                   │   │
│  │    ~/mcp/gatekit/  2 hours ago    │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │ 📄 production.yaml                  │   │
│  │    ~/configs/  yesterday            │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ─────────────────────────────────────────  │
│                                             │
│  [ Open Another File... ]  [ Create New ]  │
│  [ 🎯 Guided Setup ]  [ Clear Recent ]     │
│                                             │
│  ☐ Don't show this again                   │
│                                             │
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ↑↓ Navigate  Enter Select  Esc Quit        ┃  ← Footer
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Keyboard Navigation

| Key | Action |
|-----|--------|
| `↑`/`↓` | Navigate recent files list |
| `Enter` | Open selected recent file |
| `Tab` | Move to action buttons |
| `Space` | Toggle checkbox |
| `Esc` | Quit application |
| `1-9` | Quick-select recent file by number (optional) |

### File Paths

- Store absolute paths internally
- Display relative paths when file is in current working directory
- Show `~/...` for home directory paths
- Truncate long paths intelligently: `~/very/.../long/path/file.yaml`
- Show full path in tooltip on hover

### Timestamp Humanization

Implement a simple time-ago formatter without external dependencies (no arrow, humanize, etc.):

```python
from datetime import datetime, timezone, timedelta

def humanize_timestamp(iso_timestamp: str) -> str:
    """
    Convert ISO timestamp to human-readable relative time.

    Returns "unknown" if timestamp is malformed (defensive against corrupted state).
    """
    try:
        then = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        delta = now - then

        seconds = delta.total_seconds()
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 172800:  # < 2 days
            return "yesterday"
        elif seconds < 604800:  # < 7 days
            days = int(seconds / 86400)
            return f"{days} days ago"
        elif seconds < 2419200:  # < 28 days
            weeks = int(seconds / 604800)
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        else:
            return then.strftime("%b %d, %Y")
    except (ValueError, OSError):
        # Corrupted timestamp - don't crash the UI
        return "unknown"
```

**Implementation note**: ~30 lines of code, uses only stdlib (datetime), easy to test.

## Dependencies

### New Dependencies Required

**None** - We implement cross-platform path resolution ourselves using Python stdlib only (sys, os, pathlib).

**Rationale**: As a security-first tool, we minimize external dependencies to reduce attack surface and supply chain risk. The path resolution logic is simple (~50 lines) and easy to audit.

### Existing Dependencies Used

- `textual>=0.47.0` - TUI framework (already present)
- `textual-fspicker==0.6.0` - File picker dialog (already present)
- `pydantic==2.11.5` - Settings validation (already present)

## Implementation Plan

### Phase 1: State Management (1-2 hours)
1. Implement `platform_paths.py` with `get_user_state_dir()` and `get_user_config_dir()`
2. Write unit tests for platform path resolution (mock sys.platform for all OSes)
3. Implement `RecentFiles` class in `gatekit/tui/recent_files.py`
4. Write unit tests for `RecentFiles` class
5. Test secure directory creation and permissions (0700 on Unix)

### Phase 2: Welcome Screen UI (2-3 hours)
1. Create `WelcomeScreen` class in `gatekit/tui/screens/welcome.py`
2. Implement layout with card-style recent files display
3. Add action buttons and checkbox
4. Implement keyboard navigation
5. Write TCSS styles for welcome screen

### Phase 3: Integration (1-2 hours)
1. Modify `GatekitApp.on_mount()` to show welcome screen
2. Hook up `RecentFiles.add()` calls on file open/save
3. Handle welcome screen dismissal and route to appropriate screen
4. Implement "skip welcome" preference storage

### Phase 4: Testing & Polish (1-2 hours)
1. Test all user flows (first run, with recent files, empty state)
2. Test cross-platform paths on Linux/macOS/Windows
3. Test edge cases (corrupted JSON, permission errors, special characters)
4. Polish animations and transitions
5. Add tooltips and help text

### Phase 5: Documentation (30 minutes)
1. Update user documentation with welcome screen screenshots
2. Document state file location for troubleshooting
3. Document command-line flags for skipping welcome screen
4. Add FAQ entry about clearing recent files

## Success Criteria

- [ ] Welcome screen appears on first run with helpful guidance
- [ ] Recent files list shows up to 10 most recent configs
- [ ] Clicking a recent file opens it immediately
- [ ] Empty state shows helpful message and all actions
- [ ] Recent files are stored in platform-appropriate location
- [ ] All keyboard shortcuts work as documented
- [ ] File existence checks don't cause lag or crashes
- [ ] Corrupted state files are handled gracefully
- [ ] UI looks professional and polished
- [ ] All tests pass on Linux, macOS, and Windows

## Open Questions

1. **Guided setup implementation**: This should be a placeholder button for now

2. **Pin favorites**: Should users be able to pin certain configs to the top?
   - **Recommendation**: Not for v1, can add later if requested

3. **Search/filter**: Should there be a search box for filtering recent files?
   - **Recommendation**: Not needed for 10 items, can add if we increase max_items

## Security Considerations

- **Path disclosure**: Recent files list may expose file paths to other users viewing the terminal
  - Mitigation: This is acceptable for a local configuration tool
  - Provide "Clear Recent" button for privacy-conscious users

- **State file permissions**: Ensure state directory has appropriate permissions (0700 on Unix)
  - Implementation: `path.mkdir(parents=True, exist_ok=True, mode=0o700)` followed by `path.chmod(0o700)`
  - The explicit chmod is required because mkdir's mode parameter only applies to newly-created directories
  - On existing directories, we must enforce permissions explicitly
  - Prevents other users from reading recent files list (especially important on multi-user systems)

- **Path traversal**: Malicious state file shouldn't allow path traversal attacks
  - Mitigation: Always resolve to absolute paths, validate paths exist before display
  - Never execute or interpret paths, only display them

- **No external dependencies**: By implementing platform paths ourselves, we reduce supply chain risk and maintain full control over security-sensitive directory operations

## Future Enhancements

- Import config from URL or clipboard
- Recent projects (groups of related configs)
- Search/filter recent files
- Template picker for new configs
- Pinned favorites
- Recently accessed servers/plugins (from config files)
- Quick actions (restart gateway, view logs)
- News/tips section for new features

## References

- XDG Base Directory Specification: https://specifications.freedesktop.org/basedir-spec/latest/
- Textual screens guide: https://textual.textualize.io/guide/screens/
- textual-fspicker: https://textual-fspicker.davep.dev/

## Implementation Notes

### Cross-Platform Path Resolution

Since Gatekit is a security-first tool, we implement cross-platform directory resolution ourselves rather than using external dependencies like `platformdirs`. This gives us:

1. **Zero supply chain risk** for path operations
2. **Full control** over directory creation and permissions
3. **Easy auditability** - ~50 lines of well-documented code
4. **No maintenance burden** - platform conventions change rarely

Implementation in `gatekit/tui/platform_paths.py`:

```python
import os
import sys
from pathlib import Path
from typing import Optional


def get_user_state_dir(appname: str, appauthor: Optional[str] = None) -> Path:
    """
    Get platform-appropriate user state directory.

    Returns:
        - Linux: $XDG_STATE_HOME/appname or ~/.local/state/appname
        - macOS: ~/Library/Application Support/appname
        - Windows: %LOCALAPPDATA%/appname

    The directory is created with secure permissions (0700 on Unix).
    """
    if sys.platform == "win32":
        appdata = os.getenv("LOCALAPPDATA")
        if not appdata:
            appdata = os.path.expanduser("~\\AppData\\Local")
        path = Path(appdata) / appname
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / appname
    else:  # Linux/Unix - follow XDG Base Directory Specification
        state_home = os.getenv("XDG_STATE_HOME")
        if state_home:
            path = Path(state_home) / appname
        else:
            path = Path.home() / ".local" / "state" / appname

    # Create directory if it doesn't exist
    path.mkdir(parents=True, exist_ok=True, mode=0o700)

    # CRITICAL: Enforce permissions even if directory already existed
    # mkdir's mode only applies to newly-created dirs
    try:
        path.chmod(0o700)
    except (OSError, NotImplementedError):
        # chmod not supported on Windows, that's OK
        pass

    return path


def get_user_config_dir(appname: str, appauthor: Optional[str] = None) -> Path:
    """
    Get platform-appropriate user config directory.

    Returns:
        - Linux: $XDG_CONFIG_HOME/appname or ~/.config/appname
        - macOS: ~/Library/Application Support/appname
        - Windows: %LOCALAPPDATA%/appname

    The directory is created with secure permissions (0700 on Unix).
    """
    if sys.platform == "win32":
        appdata = os.getenv("LOCALAPPDATA")
        if not appdata:
            appdata = os.path.expanduser("~\\AppData\\Local")
        path = Path(appdata) / appname
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / appname
    else:  # Linux/Unix - follow XDG Base Directory Specification
        config_home = os.getenv("XDG_CONFIG_HOME")
        if config_home:
            path = Path(config_home) / appname
        else:
            path = Path.home() / ".config" / appname

    path.mkdir(parents=True, exist_ok=True, mode=0o700)

    try:
        path.chmod(0o700)
    except (OSError, NotImplementedError):
        pass

    return path
```

### Atomic File Writes

For reliability and security, `RecentFiles._save()` writes atomically:

```python
def _save(self, recent: List[dict]) -> None:
    """Save recent files list atomically with secure permissions."""
    import os

    data = {
        "version": 1,
        "max_items": self.max_items,
        "recent_files": recent
    }
    json_data = json.dumps(data, indent=2)

    # Write to temp file with secure permissions from the start
    temp_file = self.recent_file.with_suffix('.tmp')

    # Create with 0600 (rw-------) to avoid world-readable window
    # Even with restrictive umask, be explicit about permissions
    try:
        # Unix: open with explicit mode
        fd = os.open(temp_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.write(fd, json_data.encode('utf-8'))
        os.close(fd)
    except (OSError, AttributeError):
        # Windows or permission error: fall back to write_text + chmod
        temp_file.write_text(json_data)
        try:
            temp_file.chmod(0o600)
        except (OSError, NotImplementedError):
            pass

    # Atomic replace (works on POSIX and Windows)
    temp_file.replace(self.recent_file)
```

**Why atomic writes matter**: If the process crashes mid-write, we don't corrupt the recent files list. The temp file + replace pattern is atomic on all modern filesystems.

This approach aligns with Gatekit's security-first philosophy of minimizing dependencies while maintaining professional cross-platform support.
