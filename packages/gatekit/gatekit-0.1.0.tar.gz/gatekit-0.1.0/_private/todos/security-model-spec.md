# Security Model Documentation Project

## Context & Timing

This documentation effort is being undertaken **during the middle of phase8-pipeline-result-collection.md implementation**, while there are currently **many failing tests** that should be ignored during this documentation phase.

The immediate trigger for this documentation project is that during test fixing for phase8, we discovered the security model has become so complex that:
1. **We can't remember all our decisions** about how the security processing should work
2. **I (Claude) am having trouble** consistently applying the security model rules during test fixes
3. **Conflicting information exists** across code, ADRs, TODOs, tests, and documentation

## Problem Statement

The Gatekit security model involves extremely complex decision trees with multiple interacting components:

### Current Complexity Points
1. **Pipeline Outcomes vs Stage Outcomes** - 5 possible PipelineOutcomes × 5 possible StageOutcomes with complex interactions
2. **Critical vs Non-Critical Plugin Handling** - Different behaviors for plugin failures vs security decisions
3. **Content Clearing Logic** - Complex rules about when content gets cleared from pipeline stages
4. **Security Evaluation Semantics** - `NO_SECURITY_EVALUATION` vs `ALLOWED` vs `None` semantics are confusing
5. **Processing Stop Conditions** - Different stopping rules for BLOCKED, COMPLETED_BY_MIDDLEWARE, ERROR states
6. **Reason Concatenation** - New system just implemented for joining plugin reasons

### Sources of Truth Conflicts
- **Actual code behavior** (evolved during implementation)
- **docs/todos/middleware/phase8-pipeline-result-collection.md** (specification, partially outdated)
- **ADRs 021, 022, etc.** (written before ProcessingPipeline was fully implemented)
- **Tests** (mix of old assumptions and new behavior expectations)
- **CLAUDE.md** (no comprehensive security model documentation)
- **Code comments** (often stale or incomplete)

## Objectives

Create a **single source of truth** for the Gatekit security model that:

1. **Documents actual current behavior** (not aspirational behavior)
2. **Provides clear decision trees** for all security processing scenarios
3. **Includes executable validation** to prevent documentation drift
4. **Reconciles conflicts** between existing documentation sources
5. **Serves as reference** for future development and test fixing

## Proposed Approach

### Phase 1: Document Current Actual Behavior
Create `/docs/security-model.md` that describes what the code ACTUALLY does:
- Map all decision trees and outcome combinations
- Document critical vs non-critical plugin behavior  
- Explain content clearing rules and trigger conditions
- Define all enums (PipelineOutcome, StageOutcome) and their meanings
- Document processing stop conditions
- Include flow diagrams for request/response/notification processing

### Phase 2: Create Validation Tests  
Create `/tests/unit/test_security_model_validation.py`:
- Test every decision path documented in security-model.md
- These tests serve as executable documentation
- Any future changes that break these tests indicate a security model change
- Tests should be comprehensive enough to catch semantic drift

### Phase 3: Reconcile Documentation
Update conflicting documentation sources:
- Mark outdated ADRs with deprecation notices where needed
- Update phase8-pipeline-result-collection.md to reflect actual implementation
- Update CLAUDE.md with security model summary section
- Add cross-references between related documents

### Phase 4: Create Decision Tables
Add clear decision tables to security-model.md:
- Plugin Type × Outcome → Pipeline Behavior
- Pipeline Outcome × Had Security Plugin → is_allowed value
- Stage Outcome × Plugin Criticality → Continue Processing?
- Security Action × Content Clearing → Final Output

### Phase 5: Add Example Scenarios
Include comprehensive examples showing:
- Single security plugin (allow/block/modify scenarios)
- Multiple security plugins with mixed decisions
- Critical vs non-critical plugin failures
- Middleware completion scenarios
- No security plugins configured
- Content clearing scenarios with before/after states

## Expected Deliverables

1. **`/docs/security-model.md`** - The canonical, comprehensive security model documentation
2. **`/tests/unit/test_security_model_validation.py`** - Executable security model validation tests  
3. **Updated ADRs** with deprecation notices where documentation conflicts exist
4. **Updated CLAUDE.md** with security model summary section
5. **Updated phase8 documentation** to reflect actual implementation state

## Success Criteria

- Single authoritative document that answers any security model question
- Tests that validate every documented behavior
- No more confusion during test fixing about "what should happen"
- Documentation that stays accurate (validated by tests)
- Clear migration path for any future security model changes

## Notes

- **Priority**: This documentation work takes precedence over test fixing temporarily
- **Current State**: Many tests are failing due to phase8 implementation - this is expected
- **Approach**: Document what IS, not what we think SHOULD BE
- **Validation**: Every rule documented must have a corresponding test
- **Maintenance**: The security-model.md document becomes the authoritative reference going forward

## Implementation Notes

This documentation project should be treated as a **temporary pause** in test fixing to establish a solid foundation. Once the security model is properly documented and validated, test fixing can resume with a clear understanding of expected behaviors.

The failing tests will be addressed after the security model documentation is complete, using the documented model as the reference for what the correct behavior should be.