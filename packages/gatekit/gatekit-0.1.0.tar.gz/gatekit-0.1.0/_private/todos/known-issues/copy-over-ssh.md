# Clipboard Copy Does Not Work Over SSH

## Problem Statement

When running the Gatekit TUI over SSH, clipboard operations (copying text, "Copy Path" buttons, etc.) do not work. Text that should be copied to the user's local Mac clipboard either:
1. Gets copied to the remote machine's clipboard (useless)
2. Silently fails with no feedback

This affects all copy functionality in the TUI including:
- SelectableStatic text selection + Ctrl+C
- "Copy Path" buttons in plugin config modals
- "Copy Path" buttons in guided setup client configuration
- Error message copy in config error modals

## Guided Setup: The Worst Case

The clipboard issue is **particularly severe** in the guided setup flow. When displaying client configuration commands (e.g., the JSON snippet to add to Claude Desktop's config), users who try the native copy workaround (holding Fn/Option to bypass mouse mode) encounter a compounding problem:

**The terminal selection extends beyond the info box boundaries.**

This means:
- Selecting the multi-line JSON snippet selects content from the entire terminal width
- The selection includes decorative borders, padding, and adjacent UI elements
- Users must select and copy **each line individually**, then paste line-by-line into their shell or config file
- For a 10-line JSON config, this means 10 separate select-copy-paste operations

This transforms a "copy one snippet" task into a frustrating multi-minute ordeal.

### Potential Workaround: Write to File

A pragmatic workaround would be to **write the configuration snippet to a temporary file**:

```python
# Instead of just displaying the snippet
config_path = Path.home() / ".gatekit" / "client-config-snippet.json"
config_path.write_text(json_snippet)
# Show: "Config written to ~/.gatekit/client-config-snippet.json"
# User can then: cat ~/.gatekit/client-config-snippet.json | pbcopy (local)
# Or just: cat ~/.gatekit/client-config-snippet.json and copy from terminal
```

**Pros:**
- Works on ALL terminals regardless of OSC 52 support
- User can `cat` the file and use native terminal copy
- File persists for later reference
- Could include a "Copy to clipboard" shell command they can run locally

**Cons:**
- Creates files on the filesystem (cleanup needed?)
- Requires user to run additional commands
- Not as seamless as working clipboard

This workaround should be implemented alongside the general clipboard fixes.

## Root Cause Analysis

### Why Platform Commands Fail Over SSH

Our current implementation tries platform-specific clipboard commands first:
- macOS: `pbcopy`
- Linux: `xclip` / `xsel`
- Windows: `clip`

**Problem**: These commands run on the REMOTE machine and copy to the REMOTE clipboard, not the user's local Mac clipboard.

### Why OSC 52 Fails

OSC 52 is an ANSI escape sequence (`\x1b]52;c;<base64-text>\a`) that tells the terminal to copy text to the system clipboard. This is the only way to copy to the LOCAL clipboard over SSH.

**However, OSC 52 requires terminal support:**

| Terminal | OSC 52 Support | Notes |
|----------|----------------|-------|
| iTerm2 | Yes* | *Requires manual setting enabled |
| kitty | Yes | Works out of the box |
| Alacritty | Yes | Works out of the box |
| WezTerm | Yes | Works out of the box |
| Windows Terminal | Yes | Works out of the box |
| **macOS Terminal.app** | **No** | Not supported at all |
| GNOME Terminal | No | Not supported (as of 2024) |

### iTerm2 Requires Manual Configuration

Even in iTerm2, OSC 52 is **disabled by default**. Users must enable it:

**Preferences → General → Selection → "Applications in terminal may access clipboard"**

Without this setting enabled, OSC 52 sequences are silently ignored.

### tmux/screen Add Complexity

When running through tmux or GNU screen, OSC 52 sequences must be wrapped in DCS (Device Control String) escape sequences to pass through to the outer terminal:

- **tmux**: `\x1bPtmux;\x1b<OSC52>\x1b\\`
- **screen**: `\x1bP\x1b<OSC52>\x1b\\`

Additionally, tmux requires configuration:
```bash
# ~/.tmux.conf
set -g set-clipboard on
set -g allow-passthrough on
```

## What We've Tried

### 1. Direct TTY Write (Attempted)
Writing OSC 52 directly to `/dev/tty` instead of through Textual's buffered writer. This bypasses potential buffering issues but doesn't solve the fundamental terminal support problem.

### 2. Multiple Write Strategies (Attempted)
Trying both `/dev/tty` write and Textual's driver write to maximize compatibility. Still fails if terminal doesn't support OSC 52.

### 3. SSH Session Detection (Implemented)
Detecting SSH sessions via environment variables (`SSH_CLIENT`, `SSH_TTY`, `SSH_CONNECTION`) to use OSC 52 instead of platform commands. Correct approach, but still requires terminal support.

## Why Vim Works But We Don't

During investigation, we discovered that Vim's clipboard works over SSH. Research revealed:

1. **Vim's default `mouse` setting is empty** (`mouse=""`), meaning mouse mode is DISABLED
2. When mouse mode is disabled, the terminal handles all mouse events natively
3. Users can select text with their mouse and Cmd+C copies to the local clipboard
4. This is handled entirely by the terminal, not Vim

**Our situation is different**: Textual MUST enable mouse mode for interactivity (clicking buttons, scrolling, hover effects, etc.). When mouse mode is enabled, mouse events go to the application instead of the terminal.

## Workarounds

### Workaround 1: Bypass Key (Works Now)

Most terminals support a modifier key to bypass mouse reporting and let the terminal handle selection natively:

| Terminal | Bypass Key | How to Use |
|----------|------------|------------|
| macOS Terminal.app | **Fn** | Hold Fn while selecting text |
| iTerm2 | **Option** | Hold Option while selecting text |
| Most Linux terminals | **Shift** | Hold Shift while selecting text |
| WezTerm | **Shift** | Hold Shift while selecting text |

After selecting with the bypass key held, Cmd+C (or Ctrl+Shift+C on Linux) copies to the local clipboard.

**Pros**: Works immediately, no code changes needed
**Cons**: Users don't know about this; not discoverable

### Workaround 2: Enable OSC 52 in iTerm2

For iTerm2 users, enabling OSC 52 support allows our current implementation to work:

1. Open iTerm2 Preferences (Cmd+,)
2. Go to **General** → **Selection**
3. Check **"Applications in terminal may access clipboard"**
4. Restart iTerm2

**Pros**: Transparent to user after setup; works with our existing code
**Cons**: Only works in iTerm2; requires user configuration; doesn't help Terminal.app users

### Workaround 3: Copy Mode (Potential Implementation)

Implement a tmux-style "copy mode" that temporarily disables mouse reporting:

1. User presses a keybinding (e.g., `F7` or `Ctrl+Shift+C`)
2. TUI disables mouse reporting by writing escape sequences:
   ```python
   driver.write("\x1b[?1000l")  # Disable mouse reporting
   driver.write("\x1b[?1003l")
   driver.write("\x1b[?1015l")
   driver.write("\x1b[?1006l")
   ```
3. Show notification: "Copy mode: select text with mouse, Cmd+C to copy, Escape to exit"
4. Terminal handles mouse selection natively
5. User selects text and presses Cmd+C
6. User presses Escape to exit copy mode
7. TUI re-enables mouse reporting

**Pros**: Works on ALL terminals; no OSC 52 dependency; familiar to tmux users
**Cons**: Requires explicit mode switch; adds complexity; loses TUI interactivity while in copy mode

## Recommended Solution

Implement **all three workarounds**:

1. **Document the bypass key** in help/FAQ and show it in copy-related notifications
2. **Document iTerm2 setup** for users who want transparent clipboard
3. **Implement copy mode** as a fallback for users who can't or won't configure their terminal

## Technical References

- [Darren Burns: Copying and pasting in Textual](https://darren.codes/posts/textual-copy-paste/)
- [sunaku: Copying to clipboard from tmux and Vim using OSC 52](https://sunaku.github.io/tmux-yank-osc52.html)
- [tmux Clipboard Wiki](https://github.com/tmux/tmux/wiki/Clipboard)
- [Apple: Turn on Mouse Reporting in Terminal](https://support.apple.com/guide/terminal/turn-on-mouse-reporting-trmlc69728a5/mac)
- [iTerm2 FAQ](https://iterm2.com/faq.html)

## Files Affected

- `gatekit/tui/clipboard.py` - Main clipboard implementation
- `gatekit/tui/widgets/selectable_static.py` - Text selection widget
- `gatekit/tui/widgets/plugin_table.py` - Plugin status click-to-copy
- `gatekit/tui/screens/plugin_config/modal.py` - "Copy Path" button
- `gatekit/tui/screens/guided_setup/client_setup.py` - "Copy Path" button
- `gatekit/tui/screens/config_error_modal.py` - Error copy functionality
