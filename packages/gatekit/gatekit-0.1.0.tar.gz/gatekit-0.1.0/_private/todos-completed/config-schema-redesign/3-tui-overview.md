# Phase 3: TUI JSON Schema Integration - Overview

## Purpose
This overview document coordinates the TUI JSON Schema integration effort. Implementation details are split into focused, manageable documents.

## ⚠️ CRITICAL: Apply Fixes First
Before implementing any of the stages below, the architectural corrections in **[3-critical-fixes.md](3-critical-fixes.md)** must be incorporated into each implementation document. These fixes address fundamental design flaws that would break the implementation.

## Architecture Decisions

### Core Principles (Updated)
1. **Canonical JSON Pointer Form** - Use schema-relative paths with `/properties/` and `/items/` segments
2. **FieldRegistry Pattern** - Central registry maps JSON Pointers to widgets bidirectionally
3. **Cached Validator Singleton** - True module-level caching of SchemaValidator instance
4. **JSON Schema as Single Source of Truth** - Both validation AND UI generation
5. **No Plugin-Specific Code** - Generic widgets only (but structured editors allowed)
6. **Full Validation Feedback** - Inline errors with proper error mapping

### Key Design Choices
- **Enum Detection First** - Check for `enum` before `type` to avoid data corruption
- **Modal Editing for Object Arrays** - Full forms, not lossy inline editing
- **Tool Manager Workflow Focus** - Present as workflow curation tool, not primarily security
- **Required Leaf Fields Only** - Don't mark parent objects as required
- **Force Mode Selection** - Mixed tool configs require explicit user choice

## Implementation Documents

### Critical Fixes (Apply First)
**[3-critical-fixes.md](3-critical-fixes.md)**
- Canonical JSON Pointer form throughout
- FieldRegistry for centralized mapping
- Real validator caching singleton
- Complete error parsing implementation
- Correct Tool Manager workflow messaging

### Stage 1: Validation Infrastructure
**[3a-tui-validation.md](3a-tui-validation.md)** *(with fixes applied)*
- FieldRegistry implementation
- Cached validator singleton
- JSON Pointer utilities for widget IDs
- Complete error parser with path extraction
- Inline validation on field blur
- Full validation on save

### Stage 2: Form Generation

**[3b-tui-core-generation.md](3b-tui-core-generation.md)** *(with fixes applied)*
- JSONFormAdapter using FieldRegistry
- Accurate capability documentation (not "ALL types")
- Simple type widgets (string, number, boolean)
- Enum handling (MUST check before type)
- No compound names - registry handles all mapping
- Required leaf field indicators only

**[3c-tui-array-handling.md](3c-tui-array-handling.md)** *(with fixes applied)*
- ArrayEditor widget with FieldRegistry integration
- Simple arrays (inline add/remove)
- Object arrays (modal editing via ObjectItemModal)
- Multi-select for enum arrays
- Validation hooks for array changes

**[3d-tui-tool-manager.md](3d-tui-tool-manager.md)** *(with fixes applied)*
- ToolManagerModeSelector widget
- Workflow curation messaging (not "Security Mode")
- Forced explicit mode choice for mixed configs
- Allowlist vs blocklist enforcement
- Action field constraints based on mode
- No hardcoded plugin names

## Limitations (Initial Implementation)

These features are explicitly out of scope:
- **Conditional schemas**: `oneOf`, `anyOf`, `allOf`, `if/then/else`
- **Advanced keywords**: `patternProperties`, `dependencies`, `additionalItems`
- **Format validation**: Beyond basic `pattern` support
- **Dynamic UI**: No conditional field enable/disable
- **Deep merging**: `$ref` resolution limited to single-level

## Success Criteria

### Stage 1 (Validation)
- [ ] Centralized validator imported and cached
- [ ] JSON Pointer utilities working
- [ ] Inline validation provides immediate feedback
- [ ] Validation errors map to correct widgets
- [ ] Full validation prevents invalid saves

### Stage 2 (Generation)
- [ ] All plugins generate forms from JSON Schema
- [ ] Enum fields detected correctly (before type check)
- [ ] Arrays handled with appropriate UI (inline vs modal)
- [ ] Tool manager mode enforcement working
- [ ] No plugin-specific code in TUI

## Testing Strategy

Each implementation document includes specific tests. Key test areas:
- **JSON Pointer escaping** - Special characters handled correctly
- **Enum detection ordering** - Enums not treated as free-form
- **Required field extraction** - Nested required fields found
- **Array modal round-trip** - Data preserved through edit
- **Tool manager mode** - Mixed actions rejected

## Risk Mitigation

### High-Risk Areas Addressed
1. **Path ambiguity** → JSON Pointer IDs
2. **Enum data loss** → Check enum before type
3. **Object array editing** → Full modal, not inline
4. **Tool manager security** → Mode enforcement
5. **Required field confusion** → Recursive extraction

### Remaining Risks
1. **Unsupported schema features** → Show warning banner
2. **Performance with large forms** → Cache validators
3. **Complex validation errors** → Map to closest field

## Implementation Order

1. **Critical Fixes First** - Apply all corrections from 3-critical-fixes.md to the implementation documents
2. **3a-tui-validation.md** - Foundation with FieldRegistry and error parsing
3. **3b-tui-core-generation.md** - Core form generation using FieldRegistry
4. **3c-tui-array-handling.md** - Array handling with proper validation hooks
5. **3d-tui-tool-manager.md** - Tool Manager with workflow focus

The critical fixes MUST be incorporated before starting any implementation. After that, 3c and 3d can be worked on in parallel once 3b is complete.