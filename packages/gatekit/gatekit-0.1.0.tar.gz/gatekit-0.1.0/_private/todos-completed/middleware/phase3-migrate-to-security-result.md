# Phase 3: Migrate Security Plugins to SecurityResult

## Prerequisites
- Phase 2 completed (new result types exist)
- All tests passing

## Overview
Mass migration from PolicyDecision to SecurityResult. This is the "rip off the band-aid" phase where we update all security plugins and tests in one coordinated change, then delete PolicyDecision.

## Implementation Tasks

### 1. Update SecurityPlugin Base Class

#### Location: `gatekit/plugins/interfaces.py`

#### Task 1.1: Update SecurityPlugin to use SecurityResult
```python
# Change all three abstract method signatures:
@abstractmethod
async def process_request(self, request: MCPRequest, server_name: str) -> SecurityResult:  # was PolicyDecision
    """Evaluate if request should be allowed."""
    pass

@abstractmethod
async def process_response(self, request: MCPRequest, response: MCPResponse, server_name: str) -> SecurityResult:  # was PolicyDecision
    """Evaluate if response should be allowed."""
    pass

@abstractmethod
async def process_notification(self, notification: MCPNotification, server_name: str) -> SecurityResult:  # was PolicyDecision
    """Evaluate if notification should be allowed."""
    pass
```

### 2. Update All Security Plugin Implementations

For each plugin, replace ALL occurrences of `PolicyDecision` with `SecurityResult`:

#### Task 2.1: Update pii.py
- Import: `from gatekit.plugins.interfaces import SecurityPlugin, SecurityResult`
- Replace all `PolicyDecision(` with `SecurityResult(`
- Update return type hints: `-> SecurityResult`

#### Task 2.2: Update secrets.py
- Same changes as pii.py

#### Task 2.3: Update filesystem_server.py
- Same changes as pii.py

#### Task 2.4: Update prompt_injection.py
- Same changes as pii.py

#### Task 2.5: Update tool_allowlist.py
- Same changes as pii.py

### 3. Update Plugin Manager

#### Location: `gatekit/plugins/manager.py`

#### Task 3.1: Update imports
```python
from gatekit.plugins.interfaces import (
    SecurityPlugin, AuditingPlugin, SecurityResult, 
    PathResolvablePlugin
)
# Remove PolicyDecision import
```

#### Task 3.2: Update all method signatures
- Change all `PolicyDecision` references to `SecurityResult`
- This includes return types and variable types

#### Task 3.3: Update all PolicyDecision instantiations
- Replace `PolicyDecision(` with `SecurityResult(`

### 4. Update AuditingPlugin Interface

#### Location: `gatekit/plugins/interfaces.py`

#### Task 4.1: Update method signatures
```python
@abstractmethod
async def log_request(self, request: MCPRequest, decision: SecurityResult, server_name: str) -> None:  # was PolicyDecision
    pass

@abstractmethod
async def log_response(self, request: MCPRequest, response: MCPResponse, decision: SecurityResult, server_name: str) -> None:  # was PolicyDecision
    pass

@abstractmethod
async def log_notification(self, notification: MCPNotification, decision: SecurityResult, server_name: str) -> None:  # was PolicyDecision
    pass
```

### 5. Update All Tests

#### Task 5.1: Bulk update test imports
In all test files:
```bash
# Replace in all test files
find tests/ -name "*.py" -type f -exec sed -i '' 's/PolicyDecision/SecurityResult/g' {} \;
```

#### Task 5.2: Fix any test-specific issues
Some tests may need manual adjustment if they test PolicyDecision-specific behavior.

### 6. Delete PolicyDecision

#### Location: `gatekit/plugins/interfaces.py`

#### Task 6.1: Remove PolicyDecision class
Delete the entire PolicyDecision dataclass definition.

#### Task 6.2: Update exports
Remove PolicyDecision from `gatekit/plugins/__init__.py`

### 7. Update Any Remaining References

Search for any remaining PolicyDecision references:
```bash
grep -r "PolicyDecision" gatekit/ tests/ --include="*.py"
```

## Testing Checklist

1. [ ] No import errors for PolicyDecision
2. [ ] All security plugin tests pass
3. [ ] All integration tests pass
4. [ ] Plugin manager tests pass
5. [ ] Auditing plugin tests pass
6. [ ] Run `pytest tests/` - ALL tests pass

## Automation Commands

```bash
# Step 1: Update all Python files
find gatekit/ tests/ -name "*.py" -type f -exec sed -i '' 's/PolicyDecision/SecurityResult/g' {} \;

# Step 2: Verify no PolicyDecision remains
grep -r "PolicyDecision" gatekit/ tests/ --include="*.py"

# Step 3: Run tests
pytest tests/
```

## Success Criteria

- PolicyDecision is completely removed from codebase
- All security plugins use SecurityResult
- All tests pass
- No backward compatibility code remains

## Risk Mitigation

This is a large change, but it's mostly mechanical:
1. SecurityResult has the same fields as PolicyDecision plus proper inheritance
2. The change is mostly find-and-replace
3. Tests will catch any issues

## Notes
- This is the "big bang" phase where we eliminate legacy
- After this phase, the codebase is clean with no PolicyDecision