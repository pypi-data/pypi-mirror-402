# Phase 1: Method Rename - check_* to process_*

## Overview
Simple mechanical rename of all `check_*` methods to `process_*` across the entire codebase. This is a prerequisite for the middleware system but is a self-contained change.

## Important: No Backward Compatibility Required
**This is Gatekit v0.1.0 - our first release. No backward compatibility is required.** We can make breaking changes without maintaining old method names.

## Implementation Tasks

### 1. Update SecurityPlugin Base Class

#### Location: `gatekit/plugins/interfaces.py`

#### Task 1.1: Rename abstract methods in SecurityPlugin
Simply rename the existing methods:
- `check_request` → `process_request`
- `check_response` → `process_response`
- `check_notification` → `process_notification`

Keep everything else the same (signatures, return types, docstrings - just update method names in docstrings).

### 2. Update All Security Plugins

For each security plugin in `gatekit/plugins/security/`:
- `pii.py`
- `secrets.py`
- `filesystem_server.py`
- `prompt_injection.py`
- `tool_allowlist.py`

#### Task 2.1: Rename methods
For each plugin, rename:
- `check_request` → `process_request`
- `check_response` → `process_response`
- `check_notification` → `process_notification`

No other changes - keep the same logic, same return types (`SecurityResult`), same everything.

### 3. Update Plugin Manager

#### Location: `gatekit/plugins/manager.py`

#### Task 3.1: Update method calls
Find all places where the plugin manager calls `check_*` methods and rename to `process_*`:
- In `process_request` method: `plugin.check_request` → `plugin.process_request`
- In `process_response` method: `plugin.check_response` → `plugin.process_response`
- In `process_notification` method: `plugin.check_notification` → `plugin.process_notification`

### 4. Update All Tests

#### Task 4.1: Update test files
For all test files in `tests/`:
- Find and replace `check_request` with `process_request`
- Find and replace `check_response` with `process_response`
- Find and replace `check_notification` with `process_notification`

This includes:
- Unit tests for each security plugin
- Integration tests
- Any mocks or test doubles

### 5. Update Documentation Strings

#### Task 5.1: Update docstrings
After renaming methods, update their docstrings to reflect the new names:
- References to "check_request" in docstrings → "process_request"
- References to "check_response" in docstrings → "process_response"
- References to "check_notification" in docstrings → "process_notification"

## Testing Checklist

After completing all renames:

1. [ ] Run `pytest tests/` - ALL tests should pass
2. [ ] No references to `check_request`, `check_response`, or `check_notification` remain (except in comments explaining the rename)
3. [ ] All security plugins still work correctly
4. [ ] Plugin loading and discovery still works
5. [ ] Error messages have been updated if they referenced old method names

## Search Commands to Verify Completion

```bash
# Should return NO results after completion:
grep -r "check_request" gatekit/ --include="*.py"
grep -r "check_response" gatekit/ --include="*.py"
grep -r "check_notification" gatekit/ --include="*.py"

# Should return NO results in tests:
grep -r "check_request" tests/ --include="*.py"
grep -r "check_response" tests/ --include="*.py"
grep -r "check_notification" tests/ --include="*.py"
```

## Why This is Safe

This is a mechanical rename that:
- Doesn't change any logic
- Doesn't change any return types
- Doesn't change any signatures
- Is mostly find-and-replace
- Can be verified with simple grep commands

## Estimated Time
- 30-45 minutes for implementation
- 15 minutes for testing
- Low risk of introducing bugs

## Success Criteria
- All tests pass with `pytest tests/`
- No references to old method names remain in code
- System behavior is identical to before the rename