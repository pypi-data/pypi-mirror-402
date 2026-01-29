# Plugin Scope Architecture Refactor

**Status: ✅ COMPLETED**

## Overview

Fix the confusing "global/server/both" terminology in plugin display scope architecture and establish clear, logical plugin categories that properly reflect how plugins can be configured and used.

## Problem Statement

The current `DISPLAY_SCOPE` uses confusing terminology:
- `"global"` - Works but unclear what it means
- `"server"` - Ambiguous - could mean server-specific or just server-aware  
- `"both"` - Conceptually doesn't make sense and adds confusion

This creates architectural confusion about how plugins should be categorized and displayed in the TUI.

## Proposed Solution

### New Plugin Categories

Replace the current system with three clear categories:

1. **`"global"`** - Truly server-agnostic plugins
   - Can apply the same configuration to any server
   - Examples: PII Filter, Secrets Filter, Prompt Injection Defense
   - Can be configured in `_global` section or per-server sections

2. **`"server_aware"`** - Universal plugins requiring per-server configuration
   - Work with any server but need server-specific configuration
   - Examples: Tool Allowlist (needs server-specific tool names)
   - CANNOT be meaningfully configured in `_global` section
   - Must be configured in individual server sections

3. **`"server_specific"`** - Plugins for specific server implementations
   - Only work with specific server implementations
   - Examples: Filesystem Server Security (hardcoded for @modelcontextprotocol/server-filesystem)
   - Only appear in TUI for compatible servers

### Remove "both" Category

The `"both"` option doesn't make conceptual sense and should be eliminated entirely.

## Implementation Tasks

### Phase 1: Update Plugin Interface Documentation
- [x] Update `gatekit/plugins/interfaces.py` documentation
- [x] Remove references to `"both"` scope
- [x] Document the three new categories clearly
- [x] Add examples for each category

### Phase 2: Update All Plugin Display Metadata
- [x] Update PII Filter: `DISPLAY_SCOPE = "global"` (already correct)
- [x] Update Secrets Filter: `DISPLAY_SCOPE = "global"` (already correct)
- [x] Update Prompt Injection Defense: `DISPLAY_SCOPE = "global"` (already correct)
- [x] Update Tool Allowlist: `DISPLAY_SCOPE = "server_aware"`
- [x] Update Filesystem Server Security: `DISPLAY_SCOPE = "server_specific"`
- [x] Update all auditing plugins: `DISPLAY_SCOPE = "global"` (already correct)

### Phase 3: Update TUI Integration
- [x] Update `gatekit/tui/screens/config_editor.py` to handle new scope categories
- [x] Global section: Only show `"global"` plugins
- [x] Server sections: Show `"global"`, `"server_aware"`, and compatible `"server_specific"` plugins
- [x] Remove any logic that handles `"both"` scope

### Phase 4: Update Documentation
- [x] Update ADR-018 to reflect new terminology
- [x] Remove all references to `"both"` scope
- [x] Add clear explanations of each scope category
- [x] Provide examples of plugins in each category

### Phase 5: Validation and Testing
- [x] Run full test suite to ensure no regressions
- [x] Test TUI display with new scope categories
- [x] Verify scope filtering works correctly

## Acceptance Criteria

- [x] No plugin uses `DISPLAY_SCOPE = "both"`
- [x] All plugins have appropriate scope categories
- [x] TUI correctly filters plugins by scope
- [x] Documentation clearly explains the three categories
- [x] All tests pass

## Dependencies

This is foundational work that other todo items depend on. Must be completed before:
- 2-tool-allowlist-cleanup
- 4-tui-plugin-display-enhancement

## Breaking Changes

- Removing `"both"` scope option (low impact - not widely used)
- Changing some plugin scope values (TUI display only, no config impact)

## Success Metrics

- Clear, unambiguous plugin categorization
- No confusion about which plugins can be configured where
- Proper TUI display based on plugin capabilities