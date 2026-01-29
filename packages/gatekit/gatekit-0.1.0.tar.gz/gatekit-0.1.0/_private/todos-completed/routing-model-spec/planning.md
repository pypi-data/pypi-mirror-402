# Routing Model Documentation Project

## Context & Timing

This documentation effort is being undertaken **after discovering critical routing issues during test fixing**, where the namespacing and denamespacing logic is spread across multiple components with unclear responsibilities and repeated parsing operations.

The immediate trigger for this documentation project is that during test fixing, we discovered:
1. **The same parsing happens 3 times** in different places (proxy extracts server, plugin manager denamespaces, proxy denamespaces again)
2. **Separation of concerns is broken** - routing logic is scattered between proxy and plugin manager
3. **The architecture smell is strong** - conditional logic and fallbacks indicate poor design
4. **Tests are failing** because of confusion about where namespacing should be preserved vs removed

## Problem Statement

The Gatekit routing model has evolved organically and now suffers from architectural issues:

### Current Complexity Points
1. **Triple Parsing** - The same namespaced string is parsed three times in different components
2. **Unclear Responsibilities** - Who owns routing? Who owns denamespacing? Currently both proxy and plugin manager
3. **Lost Context** - Server name is extracted then discarded, then re-extracted (and fails)
4. **Middleware Denamespacing** - Introduced to help plugins but broke routing
5. **No Single Source of Truth** - Routing logic scattered across multiple files
6. **Implicit Assumptions** - Code assumes namespace presence/absence without clear contracts

### Sources of Truth Conflicts
- **proxy/server.py** - Extracts server names, routes requests, denamespaces for upstream
- **plugins/manager.py** - Denamespaces for plugin processing, loses routing context
- **utils/namespacing.py** - Utility functions used inconsistently
- **Multi-server ADRs** - Original design intent vs current implementation
- **Tests** - Expect certain behaviors that may not match design

## Objectives

Create a **single source of truth** for the Gatekit routing model that:

1. **Documents the complete routing flow** from client to upstream server
2. **Clarifies responsibility boundaries** between components
3. **Eliminates redundant operations** like triple parsing
4. **Provides clear contracts** about when content is namespaced vs denamespaced
5. **Defines a clean architecture** that doesn't require conditional fallbacks

## Proposed Approach

### Phase 1: Analyze Current Implementation
Document what the code ACTUALLY does in `current-sources-of-truth.md`:
- Map the complete request flow with namespacing state at each step
- Document all parsing/extraction/denamespacing operations
- Identify where routing decisions are made
- Show where context is lost and why
- Include the bug that breaks routing for modified requests

### Phase 2: Design Target Architecture
Create `/docs/routing-model.md` that defines the IDEAL routing architecture:
- Single parsing operation (DRY principle)
- Clear component responsibilities
- Explicit contracts about namespacing
- No conditional fallbacks or "smell test" failures
- Consider a RoutingContext object to encapsulate routing state
- This becomes our single source of truth for how routing WILL work

### Phase 3: Create Migration Path
Document how to implement the new architecture:
- Identify minimal changes needed to fix immediate bugs
- Plan refactoring steps to reach target architecture
- Ensure backward compatibility where needed
- Define test strategy to validate changes

### Phase 4: Create Validation Tests
Create `/tests/unit/test_routing_model_validation.py`:
- Test every routing scenario documented
- Test namespace preservation through pipeline
- Test denamespacing for upstream communication
- Test multi-server routing scenarios
- Test single-server (no namespacing) scenarios

### Phase 5: Implementation Guidelines
Document implementation patterns:
- How to handle namespaced vs non-namespaced content
- When to parse/extract/denamescape
- How to preserve routing context through processing
- Error handling for routing failures

## Expected Deliverables

1. **`/docs/routing-model.md`** - The canonical routing model documentation describing the TARGET architecture (how routing WILL work)
2. **`/docs/todos/routing-model-spec/current-sources-of-truth.md`** - Analysis of current implementation (how it works NOW)
3. **`/tests/unit/test_routing_model_validation.py`** - Executable routing validation tests for the new model
4. **Migration plan** - Steps to move from current to target architecture
5. **Updated component docs** - Clear responsibilities for each component
6. **ADR for routing redesign** - If significant changes needed

## Success Criteria

- Single authoritative document explaining all routing behavior
- No more triple parsing of namespaced strings
- Clear component responsibilities (no overlap)
- Tests validate all routing scenarios
- No "smell test" failures in the architecture
- Routing works correctly for both modified and unmodified requests

## Key Scenarios to Document

### Basic Routing Scenarios
1. **Single server, no namespacing** - Simple passthrough
2. **Multiple servers, namespaced tools** - Server extraction and routing
3. **Broadcast methods** - tools/list, resources/list aggregation
4. **Modified requests** - Preserving routing after plugin modifications
5. **Error scenarios** - Missing server, unknown tool, connection failures

### Namespacing State Transitions
1. **Client → Proxy** - Namespaced (for multi-server)
2. **Proxy → Plugin Manager** - Currently namespaced (but should it be?)
3. **Plugin Manager → Plugins** - Denamespaced (clean names)
4. **Plugins → Plugin Manager** - Modified but still denamespaced
5. **Plugin Manager → Proxy** - Currently denamespaced (breaks routing)
6. **Proxy → Upstream** - Must be denamespaced

### Component Responsibilities (Current vs Target)

#### Current (Problematic)
- **Proxy**: Extracts server, routes, denamespaces for upstream, re-extracts server
- **Plugin Manager**: Denamespaces for plugins, loses context
- **Plugins**: See clean names, unaware of routing

#### Target (Clean)
- **Proxy**: Routing decisions, single parse operation, maintains context
- **Plugin Manager**: Plugin orchestration only (no routing concern)
- **Plugins**: See clean names with server context parameter

## Implementation Notes

### Immediate Bug Fix Options

1. **Option A: Preserve Original Request**
   - Plugin manager returns original request when unmodified
   - Proxy uses that for routing
   - Problem: What about modified requests?

2. **Option B: Pass Routing Context**
   - Extract routing info once, pass it through
   - Don't try to re-extract from denamespaced content
   - Clean separation of concerns

3. **Option C: Routing Object**
   - Create RoutingContext that encapsulates all routing state
   - Pass this through the pipeline
   - Components update content but preserve routing

### Architecture Smells to Address

1. **Conditional Fallbacks** - `final_content or original_request` logic
2. **Re-extraction** - Parsing already-parsed content
3. **Lost Context** - Extracting then discarding information
4. **Dual Responsibility** - Two components doing the same job
5. **Implicit State** - Assuming namespace presence without contracts

## Notes

- **Priority**: Fix routing bug first, then document and refactor
- **Current State**: Tests failing due to routing issues with denamespaced content
- **Approach**: Document reality first, then design improvements
- **Validation**: Every routing rule must have a test
- **Maintenance**: The routing-model.md becomes the reference going forward

## Related Documentation

- `/docs/decision-records/014-multi-server-support.md` - Original multi-server design
- `/docs/todos/middleware/requirements.md` - Where denamespacing was introduced
- `/docs/security-model.md` - How security processing interacts with routing
- `/gatekit/utils/namespacing.py` - Current namespacing utilities