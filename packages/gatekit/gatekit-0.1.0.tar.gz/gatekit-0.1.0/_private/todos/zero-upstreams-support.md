# Zero Upstreams Support

## Status: Future Enhancement (Post v0.1.0)

## Problem Statement

Currently, Gatekit requires at least one upstream MCP server to be configured. This requirement is enforced at multiple levels:

1. **Config validation** (`models.py:450-451`, `641-642`): Pydantic models raise `TypeError` if `upstreams` is empty
2. **Gateway startup** (`proxy/server.py:130-138`): Raises `RuntimeError` if zero servers connect successfully
3. **Guided setup** (`guided_setup/config_generation.py:165-168`): Raises `ValueError` if no stdio servers detected

However, there are legitimate use cases where zero upstreams might be desirable:

### Use Case 1: Plugin-Only Functionality
A middleware plugin could complete all tool requests without forwarding to any upstream servers. This is architecturally valid - the middleware plugin acts as the "server."

**Example:**
```yaml
proxy:
  transport: stdio
  upstreams: []  # No upstreams needed

plugins:
  middleware:
    _global:
      - handler: custom_tool_provider
        config:
          tools:
            - name: calculate
              description: "Built-in calculator"
            - name: timestamp
              description: "Get current time"
```

The middleware plugin's `process_request()` method would return `PluginResult(completed_response=...)` for all tool calls, never requiring upstream forwarding.

### Use Case 2: Incremental Configuration
User wants to:
1. Configure plugins first (security policies, auditing)
2. Save the configuration
3. Test/validate plugin behavior
4. Add upstream servers later

This workflow is reasonable for advanced users who want to build up their config incrementally.

### Use Case 3: Template/Starter Configs
Distribution of template configs with plugins pre-configured but no upstreams, expecting users to add their own servers.

### Use Case 4: TUI Workflow Edge Case
User creates new config in TUI, configures extensive plugin rules, then tries to save before adding any servers. Currently this would fail validation despite being a valid draft state.

## Current Behavior Analysis

### What Works with Zero Upstreams

1. **Config serialization** (`config/serialization.py:37`): Gracefully handles empty upstreams - simply omits the `upstreams` key from YAML
2. **TUI connection testing** (`tui/guided_setup/connection_testing.py:119`): Returns empty list if no upstreams
3. **TUI server probing** (`tui/screens/config_editor/base.py:704`): Silently returns if no upstreams
4. **Server manager** (`server_manager.py:68-75`): `connect_all()` would return `(0, 0)` - doesn't crash
5. **Middleware completion** (`proxy/server.py:326-353`): `COMPLETED_BY_MIDDLEWARE` path works without upstreams
6. **Routing logic** (`core/routing.py`): Parses namespaces, doesn't validate server existence

### What Breaks with Zero Upstreams

1. **Config Loading** (`models.py:450-451`, `641-642`)
   ```python
   if not self.upstreams:
       raise TypeError("At least one upstream server must be configured")
   ```
   - Fails immediately during Pydantic validation
   - Prevents loading any config with zero upstreams

2. **Gateway Startup** (`proxy/server.py:130-138`)
   ```python
   successful, failed = await self._server_manager.connect_all()

   if successful == 0:
       error_msg = f"All upstream servers failed to connect: {error_details}"
       raise RuntimeError(error_msg)
   ```
   - With zero upstreams: `connect_all()` returns `(0, 0)`
   - Condition `successful == 0` is true
   - Gateway refuses to start with "All upstream servers failed to connect"
   - Error message is misleading (implies connection failures, not zero config)

3. **Guided Setup** (`guided_setup/config_generation.py:165-168`)
   ```python
   if not stdio_servers:
       raise ValueError(
           "No stdio servers found. "
           "HTTP/SSE servers are not supported in this release."
       )
   ```
   - Prevents generating configs with zero servers
   - Error message is misleading (implies HTTP/SSE issue, not zero servers)
   - Blocks incremental configuration workflow

4. **Discovery/Capability Requests**
   - With zero upstreams, `tools/list`, `resources/list`, `prompts/list` would have no servers to query
   - Would return empty lists (not an error, but potentially confusing)
   - Might work correctly if middleware plugin completes these requests

### Behavior with Middleware Completion

The middleware plugin path (`COMPLETED_BY_MIDDLEWARE`) would theoretically work:

1. Request comes in
2. Middleware plugin returns `PluginResult(completed_response=...)`
3. Pipeline outcome: `COMPLETED_BY_MIDDLEWARE`
4. Response sent directly to client (lines 326-353)
5. Never attempts upstream forwarding

**However:** Can't test this because gateway won't start with zero upstreams.

## Implementation Complexity Analysis

### Changes Required

#### 1. Config Models (MEDIUM)
**Files:** `gatekit/config/models.py`

Remove/conditional validation at:
- Line 450-451: `ProxyConfigSchema` validator
- Line 641-642: `ProxyConfig` post-init

**Options:**
- **A) Remove validation entirely** - Allow empty upstreams always
- **B) Add `allow_empty_upstreams: bool` config field** - Let users opt-in explicitly
- **C) Validate based on plugins** - If middleware plugins present, allow empty upstreams

**Recommendation:** Option A (simplest, most flexible)

**Time:** 2 hours (including testing that nothing breaks)

#### 2. Gateway Startup Logic (MEDIUM-HIGH)
**File:** `gatekit/proxy/server.py:130-138`

Current check:
```python
if successful == 0:
    raise RuntimeError("All upstream servers failed to connect")
```

Needs to distinguish:
- Zero upstreams configured (potentially valid)
- All upstreams failed to connect (error)

**New logic:**
```python
if len(config.upstreams) == 0:
    logger.warning("No upstream servers configured - running in plugin-only mode")
elif successful == 0:
    error_msg = f"All {len(config.upstreams)} upstream servers failed to connect: {error_details}"
    raise RuntimeError(error_msg)
```

**Time:** 1 hour

#### 3. Request Handling (LOW-MEDIUM)
**File:** `gatekit/proxy/server.py` (various methods)

Need to handle cases where no servers exist:
- `tools/list`, `resources/list`, `prompts/list` with zero upstreams
- Namespaced tool calls when server doesn't exist
- Broadcast operations with empty server list

**Options:**
- Let existing code handle it (might already work)
- Add explicit empty-list handling for clarity
- Return helpful error messages for missing servers

**Time:** 2-3 hours (need careful testing)

#### 4. TUI Validation (LOW)
**File:** `gatekit/tui/screens/config_editor/base.py`

Add validation messages when saving with zero upstreams:
- Warning: "No servers configured - gateway will run in plugin-only mode"
- Or: Informational notice explaining zero-upstreams behavior

**Time:** 1 hour

#### 5. Guided Setup (EASY)
**File:** `gatekit/tui/guided_setup/config_generation.py:165-168`

Change from error to conditional:
```python
if not stdio_servers:
    logger.warning("No stdio servers selected - generating plugin-only config")
    # Continue with empty upstreams
```

**Time:** 30 minutes

### Testing Requirements (HIGH EFFORT)

#### Unit Tests (3-4 hours)
1. Config loading with zero upstreams
2. Gateway startup with zero upstreams (mock middleware completion)
3. Request handling with no servers:
   - Discovery methods (`tools/list`, etc.) → empty results
   - Namespaced calls to non-existent servers → error messages
   - Middleware completion path
4. Guided setup with zero servers selected

#### Integration Tests (3-4 hours)
1. Full gateway lifecycle with zero upstreams
2. Middleware-only request completion (custom plugin)
3. TUI save/load with zero upstreams
4. Error messages are helpful and accurate

#### Manual Testing (2 hours)
1. Real-world middleware plugin completing requests
2. TUI user experience with zero upstreams
3. Error messages when user tries to call tools with no servers

### Total Implementation: 11-16 hours (1.5-2 days)

## UX Considerations

### 1. Error Messages

**Current:** "All upstream servers failed to connect"
**Problem:** Misleading when zero upstreams configured

**Proposed:**
- Zero configured: "No upstream servers configured. Gateway running in plugin-only mode."
- All failed: "All 3 configured upstream servers failed to connect: [details]"

### 2. TUI Warnings

When saving config with zero upstreams, show clear warning:

```
⚠️  Warning: No servers configured

This configuration has no upstream servers. The gateway will:
- Only process requests via middleware plugins
- Return empty results for capability discovery
- Fail tool calls unless middleware completes them

Continue? [Yes] [No]
```

### 3. Guided Setup Messaging

If user selects zero servers:

**Option A: Allow and explain**
```
ℹ️  No servers selected

You can:
1. Continue without servers (plugin-only mode)
2. Go back and select servers
3. Add servers manually to config later

[Continue] [Go Back]
```

**Option B: Require at least one**
```
⚠️  Select at least one server

Gatekit requires at least one MCP server to be useful.
Advanced users can add servers manually to the config later.

[Go Back] [Add Manually (Expert)]
```

### 4. Documentation

Add to configuration docs:
```markdown
## Plugin-Only Mode (Advanced)

Gatekit can run without any upstream servers by omitting the `upstreams`
section entirely. In this mode:

- Middleware plugins must complete all requests
- Discovery methods return empty results
- Tool calls fail unless middleware handles them
- Primarily useful for custom middleware implementations

Example:
```yaml
proxy:
  transport: stdio
  # No upstreams configured

plugins:
  middleware:
    _global:
      - handler: my_custom_tool_provider
```

This is an advanced use case. Most users should configure upstream servers.
```

## Decision Points

### Should We Support Zero Upstreams in v0.1.0?

**Arguments For:**
1. Legitimate use case for middleware-only setups
2. Enables incremental configuration workflow
3. Better error messages needed anyway
4. Plugin architecture supports it conceptually

**Arguments Against:**
1. Implementation + testing = 1.5-2 days
2. Edge case use (vast majority want upstreams)
3. Potential for user confusion
4. Need clear documentation to avoid misuse
5. v0.1.0 scope creep risk

### Recommendation: **Defer to v0.2.0**

**Rationale:**
1. **Priority:** Fix existing issues (like the guided setup deletion bug) > add edge case feature
2. **Validation:** No users have requested this yet - wait for actual demand
3. **Design time:** Need to carefully think through UX messaging and error paths
4. **Testing burden:** Significant test matrix expansion for edge case
5. **Documentation:** Needs clear docs to avoid user confusion

**For v0.1.0, we should:**
1. Fix the guided setup server deletion bug (see partial migration analysis)
2. Improve error message for zero upstreams to be clearer:
   ```python
   if not self.upstreams:
       raise TypeError(
           "Configuration must include at least one upstream server. "
           "See docs/configuration-specification.md for examples."
       )
   ```
3. Document zero-upstreams as a future enhancement

**For v0.2.0:**
- Implement full zero-upstreams support with proper UX
- Add middleware-only example config
- Document plugin-only mode clearly
- Include integration tests with custom middleware

## Related Issues

- **Guided setup partial migration bug:** Users can accidentally delete servers from client configs
- **Middleware plugin capabilities:** Need clear docs on middleware completion path
- **Plugin-only examples:** Should add example of middleware plugin that completes requests

## Implementation Checklist (v0.2.0)

- [ ] Remove upstream validation from config models
- [ ] Update gateway startup logic to distinguish zero vs failed
- [ ] Test request handling with zero upstreams
- [ ] Add TUI warnings for zero upstreams
- [ ] Update guided setup to allow zero servers
- [ ] Write integration tests
- [ ] Add documentation section on plugin-only mode
- [ ] Create example middleware plugin that completes requests
- [ ] Update error messages throughout codebase
- [ ] Test empty discovery responses

## Migration Path

For users who want this now (v0.1.0):
1. Manually edit config YAML to have minimal upstream: `upstreams: []`
2. Patch config validation locally (comment out validation)
3. Won't work - gateway startup will still fail
4. **Workaround:** Add a dummy upstream that immediately completes in middleware

Actually, there's **no clean workaround** until we implement this properly.

## Questions for Future Implementation

1. Should we require an explicit opt-in flag for zero upstreams?
2. How verbose should warnings be in TUI?
3. Should discovery methods (`tools/list`) call into middleware plugins somehow?
4. What's the mental model we want users to have for "plugin-only mode"?
5. Should we validate that at least one middleware plugin exists if zero upstreams?

## References

- ADR-020: Middleware plugin architecture
- Configuration spec: `docs/configuration-specification.md`
- Plugin interfaces: `gatekit/plugins/interfaces.py`
- Gateway startup: `gatekit/proxy/server.py:105-150`
- Guided setup generation: `gatekit/tui/guided_setup/config_generation.py`
