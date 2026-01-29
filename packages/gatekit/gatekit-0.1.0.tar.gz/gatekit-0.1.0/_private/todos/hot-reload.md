# Configuration Hot-Reload - Design Document

## Status: Deferred to v0.2.0+

**Decision:** Plugin-only hot-reload implemented but being reverted from v0.1.x due to risk/complexity concerns for first release.

**Recommendation:** Re-implement in future release with full upstream hot-reload support and simplified validation logic.

---

## Executive Summary

### What We Built

A plugin-only configuration hot-reload system that:
- Detects config file changes via mtime monitoring
- Reloads plugin configuration without restarting MCP client
- Uses generation-based tracking to prevent plugin cleanup during in-flight requests
- Sends capability change notifications to clients
- Validates that only plugin config changed (rejects upstream/timeout/logging changes)

### Why We're Deferring

**Primary concerns for v0.1.x:**
1. **Critical unfixed bug:** Notification handlers don't acquire generation tokens (crash risk)
2. **Brittle validation:** 60+ lines of hardcoded field-by-field comparison (unmaintainable)
3. **Limited usefulness:** Can't reload upstreams (90% of real-world hot-reload value)
4. **Wrong priority:** First release should nail core proxying, not convenience features
5. **Risk to core:** Touches request processing hot path (every request checks mtime, acquires generation)

**Estimated time to production-ready:**
- Plugin-only (with fixes): 0.5-1 day
- Full hot-reload: 1-2 weeks (dev + testing)

**Decision:** Focus v0.1.x on rock-solid core proxying. Implement proper full hot-reload in v0.2.0+ with lessons learned.

---

## Restoration Instructions

All hot-reload implementation code has been preserved in the `hot-reload` branch (commit cd046b0).

### Quick Start

To restore this work and continue development:

```bash
# Option 1: Switch to the hot-reload branch
git checkout hot-reload

# Option 2: Merge hot-reload into your current branch
git merge hot-reload

# Option 3: Cherry-pick the commit onto current branch
git cherry-pick hot-reload

# Option 4: Create new branch from hot-reload
git checkout -b feature/hot-reload-v2 hot-reload
```

### What's Included

The `hot-reload` branch contains:
- Complete implementation (296 lines in `gatekit/proxy/server.py`)
- Comprehensive tests (1135 lines in `tests/unit/test_proxy_server.py`)
- Updated CLI integration (`gatekit/main.py`, `tests/unit/test_main_cli.py`)
- This design document

### Merge Conflicts

Yes, you'll likely encounter merge conflicts when bringing this forward, especially if:
- Core request handling in `MCPProxy.handle_request()` has changed
- Plugin manager interface has evolved
- Config models in `gatekit/config/models.py` have new fields

**Strategy for handling conflicts:**
1. The generation tracking pattern is solid - preserve it
2. The deep field comparison (60+ lines) should be deleted anyway
3. Notification handler generation protection needs to be added (was never implemented)
4. Update mtime detection to work with any new config loading changes

The design patterns (generation tracking, locking, mtime detection) are sound and should merge cleanly. The hardcoded field validation is brittle and should be replaced with a better approach.

---

## Requirements & Use Cases

### Primary Use Case: Development/Testing Workflow

**User story:** "I'm testing security rules and want to quickly iterate without restarting Claude Desktop."

**What users want to hot-reload:**
1. **Plugin configuration** (security rules, middleware settings, audit formats)
2. **Upstream servers** (add/remove servers to reduce context bloat, update versions)
3. **Timeouts** (adjust for debugging slow servers)
4. **Logging** (enable debug logging to troubleshoot issues)

**Current workaround:** Restart MCP client (Claude Desktop) for any config change.

**Pain points:**
- Lose conversation context when restarting
- Slow iteration cycle (restart takes 5-10 seconds)
- Can't easily A/B test configurations

### Secondary Use Case: Production Operations

**User story:** "I need to update server credentials or enable security rules without downtime."

**Requirements:**
- Zero-downtime configuration updates
- No request failures during reload
- Clear audit trail of config changes
- Rollback capability on errors

---

## Implementation Details

### Code Changes Made

#### 1. Core Hot-Reload Logic (gatekit/proxy/server.py)

**Added to MCPProxy.__init__():**
```python
# Hot-reload support
self._config_path = config_path
self._config_directory = config_directory
self._config_mtime: Optional[float] = None
self._config_reload_lock = asyncio.Lock()

# Generation-based tracking for safe plugin manager cleanup
self._plugin_manager_generation = 0
self._active_requests_per_generation: Dict[int, int] = {0: 0}
self._generation_lock = asyncio.Lock()

if config_path and config_path.exists():
    self._config_mtime = config_path.stat().st_mtime
```

**New methods added (~180 lines):**

1. `_check_and_reload_config()` - Main reload orchestration
   - Checks file mtime (quick check without lock)
   - Acquires lock for actual reload
   - Double-checks mtime inside lock (concurrent request protection)
   - Validates config changes (transport, upstream count, upstream names)
   - Deep compares non-plugin fields
   - Loads new plugin manager
   - Atomic swap with generation tracking
   - Schedules background cleanup
   - Sends capability change notifications
   - Updates only `self.config.plugins` (prevents config drift)

2. `_has_non_plugin_changes()` - Deep field comparison
   - Compares transport
   - Compares timeouts (connection_timeout, request_timeout)
   - Compares logging (7 fields: level, handlers, file_path, max_file_size_mb, backup_count, format, date_format)
   - Compares HTTP config (host, port)
   - Compares upstream configs (transport, command, url, restart_on_failure, max_restart_attempts)
   - Returns (has_changes: bool, description: str)

3. `_acquire_generation()` - Request starts using plugin manager
   - Acquires lock
   - Gets current generation number
   - Increments counter for that generation
   - Returns generation token

4. `_release_generation()` - Request finishes
   - Acquires lock
   - Decrements counter for that generation
   - Cleans up counter if reaches zero

5. `_cleanup_old_plugin_manager()` - Safe cleanup
   - Polls `_active_requests_per_generation` every 50ms
   - Waits until old generation has zero active requests
   - Calls `old_plugin_manager.cleanup()`
   - Logs success/errors

6. `_notify_capability_changes()` - Client notifications
   - Sends `notifications/tools/list_changed`
   - Sends `notifications/resources/list_changed`
   - Sends `notifications/prompts/list_changed`
   - Non-blocking (logs errors but doesn't fail reload)

**Modified handle_request():**
```python
async def handle_request(self, request):
    if not self._is_running:
        raise RuntimeError("Proxy is not running")

    # Check for config changes and reload if necessary
    await self._check_and_reload_config()  # ← ADDED

    # Acquire generation token
    generation = await self._acquire_generation()  # ← ADDED

    try:
        # ... existing request processing ...
    finally:
        await self._release_generation(generation)  # ← ADDED
        # ... existing cleanup ...
```

#### 2. Entry Point Changes

**gatekit/main.py:**
```python
# Pass config_path to proxy for hot-reload support
proxy = MCPProxy(config, config_loader.config_directory, config_path=config_path)
```

**tests/unit/test_main_cli.py:**
```python
# Updated test assertion
mock_proxy_class.assert_called_once_with(
    mock_config, mock_loader.config_directory, config_path=config_path
)
```

#### 3. Documentation Updates

**CLAUDE.md - Added to Key Concepts:**
> Configuration Hot-Reload: Gatekit automatically reloads plugin configuration when the config file changes, without requiring MCP client restart. Config file mtime is checked before each request. Uses asyncio.Lock to prevent concurrent reload race conditions. Generation-based tracking ensures plugin manager cleanup waits for all in-flight requests using that generation to complete before calling cleanup(), preventing resource corruption. Only plugin configuration is reloaded in `self.config.plugins` - changes to upstreams, transport, timeouts, or logging are rejected with clear error logs requiring restart (this prevents config drift where runtime and config disagree). Requests in-flight during reload may have incomplete audit data (acceptable trade-off). On successful reload, sends `notifications/tools/list_changed`, `notifications/resources/list_changed`, and `notifications/prompts/list_changed` to inform client that capabilities may have changed (client decides whether to refresh).

**Removed files:**
- `docs/decision-records/016-hot-swap-configuration-management.md` (281 lines)
- `docs/todos-completed/visual-configuration-interface/hot-swap-architecture.md` (309 lines)

These were over-engineered designs using watchdog, psutil, state files, and PID tracking. The simple mtime-based approach is better.

#### 4. Comprehensive Test Suite

**Added 12 new tests in tests/unit/test_proxy_server.py::TestConfigHotReload (1135 lines):**

1. `test_config_hot_reload_on_file_change` - Basic reload detection and execution
2. `test_config_reload_on_request` - Reload triggers during request processing
3. `test_config_reload_handles_invalid_config` - Error handling, keeps old config
4. `test_config_reload_rejects_upstream_changes` - Upstream name change rejected
5. `test_config_reload_rejects_transport_changes` - Transport change rejected
6. `test_concurrent_config_reload_attempts` - Lock prevents double-reload
7. `test_config_reload_sends_capability_notifications` - All 3 notifications sent
8. `test_config_reload_no_notifications_on_rejection` - No notifications on reject
9. `test_config_reload_waits_for_inflight_requests` - Generation tracking works
10. `test_config_reload_plugins_only_when_no_other_changes` - Success case
11. `test_config_reload_rejects_upstream_command_changes` - Deep comparison works
12. `test_config_reload_rejects_timeout_changes` - Deep comparison works

**Test coverage:**
- File change detection (mtime)
- Concurrent reload protection (locks)
- Validation logic (all rejection scenarios)
- Generation-based cleanup timing
- Notification sending
- Config drift prevention
- Error handling

---

## Technical Architecture

### Generation-Based Cleanup Pattern

**Problem:** Plugin cleanup can happen while requests still using old plugins.

**Example timeline without generation tracking:**
```
t=0ms:   Request A starts, uses plugin manager gen 0
t=100ms: Config changes, hot-reload starts
t=101ms: New plugin manager (gen 1) swapped in
t=102ms: Background task: wait 100ms for cleanup
t=150ms: Request A still processing with gen 0 plugins
t=202ms: Cleanup runs: old_plugin_manager.cleanup()
         ❌ Request A crashes - file handles closed mid-request
```

**Solution: Generation tracking (reference counting)**
```
t=0ms:   Request A: acquire_generation() → gen 0
         _active_requests_per_generation[0] = 1

t=100ms: Config changes, hot-reload starts

t=101ms: Generation incremented to 1
         New plugin manager swapped in
         Cleanup scheduled for gen 0

t=102ms: Cleanup task: poll _active_requests_per_generation[0]
         Count = 1, keep waiting...

t=150ms: Request A still processing with gen 0 plugins
         (cleanup still waiting)

t=200ms: Request A: release_generation(0)
         _active_requests_per_generation[0] = 0

t=205ms: Cleanup task: poll again
         Count = 0, safe to cleanup!
         old_plugin_manager.cleanup()
         ✅ Request A already finished, no crash
```

**Data structures:**
```python
self._plugin_manager_generation = 2  # Current generation
self._active_requests_per_generation = {
    0: 0,  # Generation 0 has 0 active requests (can be cleaned up)
    1: 3,  # Generation 1 has 3 active requests (cleanup would wait)
    2: 5,  # Generation 2 (current) has 5 active requests
}
```

**Key insight:** This is reference counting for async plugin managers. Each request holds a "reference" (generation token) that prevents cleanup.

### Validation Strategy

**Goal:** Prevent config drift where `self.config` shows values that runtime components aren't using.

**Approach: Layered validation**

**Layer 1: Structural changes (reject)**
```python
# Can't change fundamental structure
if new_config.transport != self.config.transport:
    return reject("transport changed")

if len(new_config.upstreams) != len(self.config.upstreams):
    return reject("upstream count changed")

if set(old_names) != set(new_names):
    return reject("upstream names changed")
```

**Layer 2: Deep field comparison (reject)**
```python
# Can't change upstream/timeout/logging details
if _has_non_plugin_changes(new_config):
    return reject(description)
```

**Layer 3: Plugin-only updates (allow)**
```python
# Only update plugins, leave everything else unchanged
self.config.plugins = new_config.plugins
```

**Problem with current approach:** Layer 2 is brittle - hardcodes every field in every config section. Any new config field requires updating comparison logic.

### Capability Change Notifications

**MCP spec guidance:** Servers should send `notifications/{type}/list_changed` when capabilities MIGHT have changed. Client decides whether to refresh.

**Why we always send notifications after plugin reload:**

1. **ANY plugin can affect capabilities:**
   - Security plugins block tools
   - Middleware plugins rename tools, modify descriptions
   - User plugins could do anything

2. **Can't cheaply detect actual changes:**
   - Would need to query all servers for all tools (expensive)
   - Plugins have runtime state (not just config)
   - Race conditions with server-aware plugins

3. **False positives are acceptable:**
   - Client calls `tools/list` (lightweight)
   - Sees tools haven't changed, uses cache
   - Small cost for reliability

4. **False negatives are bad UX:**
   - Client doesn't know tools changed
   - Stale tool list, LLM tries nonexistent tools
   - Errors and confusion

**Decision: Conservative approach - always notify.**

---

## QC Feedback & Issues

### Issue 1: Notification Handlers Lack Generation Protection (HIGH PRIORITY)

**Problem:** `handle_notification()` and `_listen_server_notifications()` call plugin manager without acquiring generation token.

**Code locations:**
- `handle_notification()` at gatekit/proxy/server.py:811-868
- `_listen_server_notifications()` at gatekit/proxy/server.py:1031-1104

**Race condition:**
```python
async def handle_notification(self, notification):
    # NO generation token acquired!
    await self._plugin_manager.process_notification(...)  # Could crash
    await self._plugin_manager.log_notification(...)      # Could crash
```

**Timeline:**
```
t=0ms:   Notification arrives from upstream server
         handle_notification() starts processing

t=50ms:  Config hot-reload happens
         Old plugin manager scheduled for cleanup

t=150ms: Cleanup runs (doesn't know notification handler is running)
         Closes audit log file handles

t=200ms: Notification handler tries to log
         ❌ CRASH - file handle closed
```

**Fix required:**
```python
async def handle_notification(self, notification):
    generation = await self._acquire_generation()
    try:
        await self._plugin_manager.process_notification(...)
        await self._plugin_manager.log_notification(...)
    finally:
        await self._release_generation(generation)
```

**Impact:** This is a CRITICAL crash risk. Must be fixed before shipping any hot-reload functionality.

### Issue 2: Deep Comparison Is Brittle (MEDIUM PRIORITY)

**Problem:** `_has_non_plugin_changes()` hardcodes every field in every config section (60+ lines).

**Example:**
```python
if old_log.level != new_log.level:
    return True, "logging level changed"
if old_log.handlers != new_log.handlers:
    return True, "logging handlers changed"
if old_log.file_path != new_log.file_path:
    return True, "logging file_path changed"
# ... 7 more logging fields ...
# ... 5 upstream fields per server ...
# ... 2 timeout fields ...
# ... 2 HTTP fields ...
```

**Problems:**
1. **Unmaintainable:** Every new config field requires updating comparison
2. **Error-prone:** Easy to miss a field and get config drift
3. **Verbose:** 60+ lines doing mechanical comparison
4. **Wrong abstraction:** Should use dataclass `__eq__` or full hot-reload

**Better approaches:**

**Option A: Use dataclass equality**
```python
def _has_non_plugin_changes(self, new_config):
    # Dataclasses have __eq__ built-in
    if new_config.upstreams != self.config.upstreams:
        return True, "upstream configuration changed"
    if new_config.timeouts != self.config.timeouts:
        return True, "timeout configuration changed"
    return False, ""
```

**Option B: Full hot-reload (delete comparison entirely)**
```python
def _has_non_reloadable_changes(self, new_config):
    # Only transport can't be hot-reloaded
    if new_config.transport != self.config.transport:
        return True, "transport changed"
    # Everything else: reload it!
    return False, ""
```

**Recommendation:** If keeping plugin-only hot-reload, use Option A. If implementing full hot-reload, use Option B.

### Issue 3: Limited Usefulness (DESIGN)

**Problem:** Can only reload plugins. Most real-world hot-reload needs involve upstreams.

**User scenarios that DON'T work:**
- "I want to disable github server temporarily" → Can't remove it
- "I need to upgrade to @latest version" → Can't change command
- "I found a typo in server args" → Can't fix it
- "I want to change API credentials" → Can't update them
- "I need to add a new server for testing" → Can't add it

**Current false-positive UX:**
```yaml
# User edits config
upstreams:
  - name: server1
    command: ["old-command"]  # Changes to ["new-command"]

# Logs show "Configuration reloaded successfully (plugins only)"
# But actually rejected the upstream change!
# User thinks it worked, but it didn't
```

**This is worse than no hot-reload at all** - creates confusion and false expectations.

**Solutions:**
1. **Short-term:** Make rejection clear, document limitations prominently
2. **Long-term:** Implement full hot-reload (see Proposed Enhancements)

---

## Proposed Enhancements (Future Work)

### Full Configuration Hot-Reload

**Goal:** Support hot-reloading everything except transport changes.

**What would be hot-reloadable:**
- ✅ Plugin changes (already done)
- ✅ Upstream additions (connect new servers)
- ✅ Upstream removals (disconnect servers)
- ✅ Upstream modifications (reconnect with new config)
- ✅ Timeout changes (apply to next request)
- ✅ Logging changes (call Python logging API)

**What still requires restart:**
- ❌ Transport changes (stdio ↔ http - fundamental networking change)

**Benefits:**
1. **Real usefulness:** Solves actual user needs (server management)
2. **Simpler code:** Delete 60 lines of brittle field comparison
3. **Better UX:** Config file is source of truth (removing server actually removes it)
4. **Easier validation:** Just check transport, reload everything else

**Implementation plan:**

#### Phase 1: Upstream Hot-Reload

**Calculate server diff:**
```python
async def _reload_upstreams(self, new_upstreams: List[UpstreamConfig]):
    old_servers = {s.name: s for s in self.config.upstreams}
    new_servers = {s.name: s for s in new_upstreams}

    # Calculate changes
    added = set(new_servers.keys()) - set(old_servers.keys())
    removed = set(old_servers.keys()) - set(new_servers.keys())
    potentially_modified = set(old_servers.keys()) & set(new_servers.keys())

    # Filter to actually modified (using dataclass __eq__)
    modified = {name for name in potentially_modified
                if old_servers[name] != new_servers[name]}
```

**Remove servers:**
```python
for name in removed:
    await self._disconnect_server_gracefully(name)

async def _disconnect_server_gracefully(self, name: str):
    # Wait for in-flight requests to this server
    while self._active_requests_per_server.get(name, 0) > 0:
        await asyncio.sleep(0.05)

    # Cancel notification listener
    if name in self._notification_listeners:
        self._notification_listeners[name].cancel()
        await self._notification_listeners[name]

    # Disconnect
    await self._server_manager.disconnect_server(name)
```

**Reconnect modified servers:**
```python
for name in modified:
    await self._reconnect_server(name, new_servers[name])

async def _reconnect_server(self, name: str, new_config: UpstreamConfig):
    # Wait for in-flight requests
    while self._active_requests_per_server.get(name, 0) > 0:
        await asyncio.sleep(0.05)

    # Cancel notification listener
    if name in self._notification_listeners:
        self._notification_listeners[name].cancel()
        await self._notification_listeners[name]

    # Reconnect
    await self._server_manager.disconnect_server(name)
    await self._server_manager.connect_server(new_config)

    # Start new notification listener
    self._notification_listeners[name] = asyncio.create_task(
        self._listen_server_notifications(name)
    )
```

**Add new servers:**
```python
for name in added:
    await self._connect_server(new_servers[name])

async def _connect_server(self, config: UpstreamConfig):
    await self._server_manager.connect_server(config)

    # Start notification listener
    self._notification_listeners[config.name] = asyncio.create_task(
        self._listen_server_notifications(config.name)
    )
```

**Challenge: Server-specific request tracking**

**Option 1: Reuse generation system (simple)**
- Current generation tracks plugin manager version
- Server reconnect happens at same time as plugin swap
- Just wait for generation's requests to complete
- Coarse-grained but works

**Option 2: Server-specific counters (precise)**
```python
self._active_requests_per_server: Dict[str, int] = {}

# In request routing
async def _route_request(self, request, server_name):
    self._active_requests_per_server[server_name] = \
        self._active_requests_per_server.get(server_name, 0) + 1
    try:
        # ... routing ...
    finally:
        self._active_requests_per_server[server_name] -= 1
```

**Recommendation:** Start with Option 1 (reuse generation), optimize to Option 2 if needed.

#### Phase 2: Timeout Hot-Reload

**Trivial implementation:**
```python
self.config.timeouts = new_config.timeouts
# Values used on next request, no coordination needed
```

#### Phase 3: Logging Hot-Reload

**Call Python logging API:**
```python
async def _reload_logging(self, new_logging: LoggingConfig):
    root_logger = logging.getLogger("gatekit")

    # Update level
    root_logger.setLevel(new_logging.level)

    # Update handlers if changed
    if self.config.logging.handlers != new_logging.handlers:
        # Clear existing handlers
        root_logger.handlers.clear()

        # Add new handlers
        if "stderr" in new_logging.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)

        if "file" in new_logging.handlers and new_logging.file_path:
            handler = RotatingFileHandler(
                new_logging.file_path,
                maxBytes=new_logging.max_file_size_mb * 1024 * 1024,
                backupCount=new_logging.backup_count
            )
            handler.setFormatter(formatter)
            root_logger.addHandler(handler)

    self.config.logging = new_logging
```

#### Phase 4: Simplify Validation

**Delete `_has_non_plugin_changes()` entirely:**
```python
def _has_non_reloadable_changes(self, new_config):
    # Only transport changes require restart
    if new_config.transport != self.config.transport:
        return True, "transport changed from stdio to http"

    # Everything else is hot-reloadable
    return False, ""
```

**This deletes 60+ lines of brittle comparison code.**

#### Phase 5: Notification Listener Management

**Problem:** Each upstream has a background task. On reconnect, must cancel old and start new.

**Data structure:**
```python
self._notification_listeners: Dict[str, asyncio.Task] = {}
```

**Lifecycle:**
```python
# On server connect
self._notification_listeners[name] = asyncio.create_task(
    self._listen_server_notifications(name)
)

# On server reconnect
old_task = self._notification_listeners[name]
old_task.cancel()
try:
    await old_task
except asyncio.CancelledError:
    pass

# ... disconnect and reconnect server ...

self._notification_listeners[name] = asyncio.create_task(
    self._listen_server_notifications(name)
)

# On server removal
old_task = self._notification_listeners.pop(name)
old_task.cancel()
```

**Edge case:** Notification arrives during reconnect window
- Old listener cancelled
- Server disconnected
- New server not yet connected
- Notification lost

**Solution: Acceptable loss**
- MCP doesn't guarantee notification delivery
- Servers should handle missed notifications
- Alternative: Queue notifications during reconnect (complex)

### Estimated Effort

**Full hot-reload implementation:**
- Phase 1 (Upstream hot-reload): 2 days dev + 2 days testing = 4 days
- Phase 2 (Timeout hot-reload): 0.5 day
- Phase 3 (Logging hot-reload): 1 day
- Phase 4 (Simplify validation): 0.5 day
- Phase 5 (Notification listeners): Included in Phase 1
- **Total: 6 days (1-2 weeks with buffer)**

**Plugin-only (with fixes):**
- Fix notification handler generation: 0.5 day
- Simplify validation (use dataclass __eq__): 0.5 day
- **Total: 1 day**

---

## Alternatives Considered

### Alternative 1: watchdog-based file watching

**From removed ADR-016:**
- Use `watchdog` library to watch config file
- More complex (event handlers, background threads)
- Requires new dependency
- Doesn't handle concurrency any better

**Rejected because:** Simple mtime checking is sufficient and has no dependencies.

### Alternative 2: Reload on SIGHUP

**UNIX pattern:**
```bash
kill -HUP <gatekit-pid>  # Triggers reload
```

**Pros:**
- Explicit reload trigger
- Standard UNIX pattern
- No mtime polling overhead

**Cons:**
- Doesn't work on Windows
- Requires user to know PID
- Less convenient than automatic detection
- Doesn't help with TUI workflow

**Rejected because:** Automatic detection better for development workflow.

### Alternative 3: No hot-reload, just restart

**Conservative approach:**
- Document: "Restart required for config changes"
- Keep code simple
- Proven reliable

**Pros:**
- Zero complexity
- Zero risk to core proxying
- Clear user expectations

**Cons:**
- Slower development iteration
- Context loss when restarting Claude Desktop
- Not competitive with other MCP gateways

**Partially accepted:** This is the v0.1.x decision. Implement hot-reload properly in v0.2.0+.

### Alternative 4: enabled: false field for upstreams

**Add field to upstream config:**
```yaml
upstreams:
  - name: github
    command: ["npx", "github-server"]
    enabled: false  # Disabled but still in config
```

**How it would work:**
- Server stays in config (so validation passes)
- ServerManager skips connecting to it
- Can hot-reload: `enabled: false → true`

**Problems:**
1. Weird abstraction (config shows server, but it's not running)
2. TUI doesn't show enabled/disabled distinction
3. More complex than just removing the server
4. False sense of "server is there" when it's not

**Rejected because:** Just support adding/removing servers properly instead of this hack.

---

## Risk Analysis

### Plugin-Only Hot-Reload Risks

**LOW Risk (after fixes):**
- Notification handler generation tracking (MUST FIX)
- Simplify validation to use dataclass equality (SHOULD FIX)
- Isolated to plugin layer
- Fail-safe degradation (error → keep old plugins)
- Limited surface area

**Impact if bugs occur:**
- Plugin reload might fail → user restarts
- Notification handler crashes → process dies
- Config drift → user confusion

**Mitigation:**
- Comprehensive testing (12 tests)
- Clear error messages
- Fail-safe defaults

### Full Hot-Reload Risks

**MEDIUM-HIGH Risk:**
- Touches ServerManager (core infrastructure)
- Process lifecycle management (kill/spawn subprocesses)
- Request routing during server changes
- Notification listener task coordination
- Capability re-aggregation
- Many edge cases

**Impact if bugs occur:**
- Requests routed to wrong/dead server → hangs, crashes
- Process zombies → resource exhaustion
- Notification loss → incorrect behavior
- Capability mismatch → tools/list errors
- Race conditions → unpredictable failures

**Mitigation:**
- 30-40 comprehensive tests needed
- Extensive edge case testing
- Real MCP server integration tests
- Production monitoring
- Graceful fallback mechanisms

### Risk to Core Proxying

**Plugin-only:**
- **Request hot path:** `_check_and_reload_config()` on every request (file stat)
- **Generation tracking:** acquire/release on every request (dict increment/decrement)
- **Performance impact:** Negligible (microseconds per request)
- **Correctness impact:** LOW after fixing notification handlers

**Full hot-reload:**
- **Server routing:** Must handle routing during server reconnect
- **Connection state:** Must coordinate server lifecycle with requests
- **Notification delivery:** Must handle listener restart without loss
- **Correctness impact:** MEDIUM-HIGH due to complexity

---

## Recommendation

### For v0.1.x: Defer Hot-Reload

**Reasoning:**
1. **Wrong priority:** First release should nail core proxying reliability
2. **Unfixed critical bug:** Notification handlers lack generation protection
3. **Limited usefulness:** Plugin-only doesn't solve real user needs
4. **Complexity risk:** Touches request hot path (every request affected)
5. **Better later:** Can implement properly in v0.2.0+ with lessons learned

**What to ship in v0.1.x:**
- No hot-reload functionality
- Clear documentation: "Restart required for all config changes"
- Focus on rock-solid proxying, security, and auditing

### For v0.2.0+: Full Hot-Reload

**Reasoning:**
1. **Real usefulness:** Upstream hot-reload solves actual user needs
2. **Simpler validation:** Delete brittle comparison, just check transport
3. **User feedback:** Learn what users actually need from v0.1.x usage
4. **Proper testing:** 1-2 weeks to implement and test thoroughly
5. **Not rushed:** Can take time to get it right

**Implementation approach:**
1. Fix notification handler generation tracking first (critical)
2. Implement upstream hot-reload (add/remove/modify)
3. Implement timeout/logging hot-reload (trivial)
4. Delete brittle validation, use simple transport check
5. Comprehensive testing (30-40 tests)
6. Real MCP server integration tests
7. Production monitoring and metrics

---

## Testing Strategy (Future Work)

### Unit Tests (Already Have 12)

**Coverage:**
- File change detection
- Concurrent reload protection
- Validation logic
- Generation-based cleanup
- Notification sending
- Error handling

### Integration Tests (Need to Add)

**Server lifecycle:**
- Add server during active requests
- Remove server during active requests
- Modify server during active requests
- Concurrent server changes
- Server startup failure during reload
- Server shutdown timeout during reload

**Notification delivery:**
- Notification arrives during server reconnect
- Multiple notifications during reload
- Notification handler spans reload
- Notification listener restart

**Capability changes:**
- Tool list changes after reload
- Resource list changes after reload
- Client receives and acts on notifications
- Multiple clients receive notifications

**Real MCP servers:**
- Test with npx-based servers (filesystem, github, etc.)
- Server process lifecycle (spawn, kill, reconnect)
- Actual tool/resource/prompt changes
- Real notification delivery

### Performance Tests (Need to Add)

**Hot path overhead:**
- Measure mtime check overhead per request
- Measure generation acquire/release overhead
- Baseline: no hot-reload
- Target: <1% overhead

**Reload performance:**
- Time to reload plugins only
- Time to reload upstreams
- Time to reload with N servers
- Memory usage during reload

**Concurrency:**
- Reload during high request load (100+ req/s)
- Multiple concurrent reload attempts
- Server reconnect during request burst

### Failure Mode Tests (Need to Add)

**Error injection:**
- Config file becomes invalid mid-reload
- Plugin load fails
- Server connection timeout
- Server process crash during reconnect
- Notification listener crash
- Out of memory during reload
- Disk full (can't write temp files)

**Recovery:**
- Verify old config still works after failed reload
- Verify no resource leaks after failed reload
- Verify clear error messages
- Verify audit logs show failure

---

## Lessons Learned

### What Worked Well

1. **Generation-based cleanup pattern**
   - Conceptually clean (reference counting)
   - Prevents resource corruption
   - Reusable for other hot-reload scenarios

2. **mtime-based detection**
   - Simple, no dependencies
   - Works cross-platform
   - Efficient (microseconds)

3. **Lock-based concurrency control**
   - Prevents double-reload races
   - Double-check pattern inside lock
   - Clear reasoning

4. **Capability change notifications**
   - Follows MCP spec properly
   - Conservative approach (always notify)
   - Client decides whether to refresh

5. **Fail-safe degradation**
   - Errors keep old config
   - Proxying continues
   - Clear error messages

### What Didn't Work Well

1. **Brittle field-by-field comparison**
   - 60+ lines of hardcoded fields
   - Unmaintainable as config evolves
   - Wrong abstraction

2. **Plugin-only scope**
   - Doesn't solve real user needs
   - False-positive UX confusion
   - Not worth the complexity

3. **Notification handler gap**
   - Critical bug we didn't catch initially
   - Shows generation pattern needs to be comprehensive
   - Easy to forget edge cases

4. **Incomplete implementation**
   - Can't do what users actually want (upstream changes)
   - Creates false expectations
   - Better to not have feature at all

### Design Principles for Future Work

1. **Do it fully or not at all**
   - Plugin-only hot-reload is worse than nothing
   - Partial features create confusion
   - Users expect consistency

2. **Use abstraction boundaries**
   - Dataclass `__eq__` instead of field-by-field
   - Let Python do the comparison work
   - Don't duplicate logic

3. **Consider all code paths**
   - Requests are obvious
   - Notifications are easy to miss
   - Background tasks need generation tracking too

4. **Test edge cases thoroughly**
   - Concurrent operations
   - Failure modes
   - Real-world scenarios
   - Long-running operations

5. **Document limitations clearly**
   - Don't create false expectations
   - Show what works AND what doesn't
   - Clear upgrade path

---

## References

### Related Documentation

- `gatekit/proxy/server.py:217-496` - Implementation code
- `tests/unit/test_proxy_server.py:912-2050` - Test suite
- `CLAUDE.md` - Updated with hot-reload documentation
- Removed ADR-016 (over-engineered design)
- Removed hot-swap-architecture.md (over-engineered design)

### External References

- MCP Specification: Capability change notifications
- Python asyncio documentation: Locks and task coordination
- Python dataclasses: `__eq__` for structural comparison
- Reference counting pattern in async contexts

### Discussion Archive

**Key conversations:**
1. Initial implementation plan (simple vs complex)
2. QC feedback on race conditions and config drift
3. Upstream hot-reload debate (why it's needed)
4. Risk analysis for v0.1.x inclusion
5. Recommendation to defer to v0.2.0+

---

## Appendix: Complete Code Diff

See git diff output:
```bash
git diff HEAD~1  # Before hot-reload work
```

**Files changed:**
- `gatekit/proxy/server.py`: +296 lines (hot-reload implementation)
- `tests/unit/test_proxy_server.py`: +1135 lines (comprehensive tests)
- `gatekit/main.py`: +1 line (pass config_path)
- `tests/unit/test_main_cli.py`: +1 line (update test assertion)
- `CLAUDE.md`: +1 line (documentation)
- Deleted: `docs/decision-records/016-hot-swap-configuration-management.md` (-281 lines)
- Deleted: `docs/todos-completed/visual-configuration-interface/hot-swap-architecture.md` (-309 lines)

**Net change:** +844 lines of production code and tests, -590 lines of over-engineered design docs.

---

## Next Steps When Resuming

### Phase 0: Restore and Review (15 minutes)

| Step | Files/Actions |
|------|---------------|
| Restore branch | `git checkout hot-reload` or `git merge hot-reload` |
| Review design doc | Read this entire document |
| Run existing tests | `pytest tests/unit/test_proxy_server.py::TestConfigHotReload -v` |
| Verify 12 tests pass | All hot-reload tests should be green |

### Phase 1: Fix Critical Bugs (2-4 hours)

| Step | Files to Modify | Tests to Add/Update |
|------|-----------------|---------------------|
| **Fix notification handler generation tracking** | `gatekit/proxy/server.py:handle_notification()` | `tests/unit/test_proxy_server.py::test_notification_generation_tracking` (NEW) |
| Add `_acquire_generation()` call | `gatekit/proxy/server.py:_listen_server_notifications()` | `tests/unit/test_proxy_server.py::test_server_listener_generation_tracking` (NEW) |
| Wrap in try/finally | Both methods above | Update `test_config_reload_waits_for_inflight_requests` |
| **Simplify validation logic** | `gatekit/proxy/server.py:_has_non_plugin_changes()` - DELETE 60 lines | `tests/unit/test_proxy_server.py::test_config_reload_rejects_upstream_command_changes` - simplify |
| Replace with allow-list | Keep only upstream names/count/transport validation | `tests/unit/test_proxy_server.py::test_config_reload_rejects_timeout_changes` - DELETE |
| Update tests | Remove deep comparison tests | Delete test methods for field-by-field validation |

### Phase 2: Plugin-Only Polish (2-4 hours)

Only needed if staying with plugin-only approach.

| Step | Files to Modify | Tests to Add |
|------|-----------------|--------------|
| Improve error messages | `gatekit/proxy/server.py:_check_and_reload_config()` logging | N/A (manual testing) |
| Add --validate-only flag | `gatekit/main.py:gateway_main()` | `tests/unit/test_main_cli.py::test_validate_only_hot_reload` |
| Document limitations | Update CLAUDE.md, add user-facing docs | N/A |
| User acceptance testing | Manual testing with real configs | Create `tests/integration/test_hot_reload_real_configs.py` |

### Phase 3: Full Hot-Reload (1-2 weeks)

If implementing full hot-reload instead of plugin-only.

#### 3a. Upstream Hot-Reload (3-5 days)

| Step | Files to Modify | Tests to Add |
|------|-----------------|--------------|
| Server-specific request tracking | `gatekit/proxy/server.py`: Add `_active_requests_per_server: Dict[str, int]` | `tests/unit/test_proxy_server.py::test_server_request_tracking` |
| Track by (generation, server) | Update `_acquire_generation()` to take server_name | Update all 12 existing tests |
| Graceful server disconnection | `gatekit/proxy/server.py`: Add `_disconnect_server(name)` | `tests/unit/test_proxy_server.py::test_graceful_server_disconnect` |
| Wait for in-flight requests | Poll server-specific counter before disconnect | `tests/unit/test_proxy_server.py::test_disconnect_waits_for_requests` |
| Reconnect with new config | `gatekit/proxy/server.py`: Add `_reconnect_server(name, config)` | `tests/unit/test_proxy_server.py::test_server_reconnect` |
| Notification listener restart | Cancel old task, start new in `_reconnect_server()` | `tests/unit/test_proxy_server.py::test_listener_restart_on_reconnect` |
| Add server support | `gatekit/proxy/server.py:_reload_upstreams()` | `tests/unit/test_proxy_server.py::test_hot_reload_add_server` |
| Remove server support | Same method | `tests/unit/test_proxy_server.py::test_hot_reload_remove_server` |
| Modify server support | Same method | `tests/unit/test_proxy_server.py::test_hot_reload_modify_server` |

#### 3b. Other Config Hot-Reload (1-2 days)

| Step | Files to Modify | Tests to Add |
|------|-----------------|--------------|
| Timeout hot-reload | `gatekit/proxy/server.py`: Update `self.config.timeouts` | `tests/unit/test_proxy_server.py::test_hot_reload_timeouts` |
| Logging hot-reload | Call Python logging API to update levels | `tests/unit/test_proxy_server.py::test_hot_reload_logging` |
| HTTP config hot-reload | Update `self.config.http` | `tests/unit/test_proxy_server.py::test_hot_reload_http_config` |
| DELETE brittle validation | Remove `_has_non_plugin_changes()` entirely | DELETE 5-6 test methods |

#### 3c. Integration Testing (2-3 days)

| Test Category | Test File | Key Scenarios |
|---------------|-----------|---------------|
| Real MCP servers | `tests/integration/test_hot_reload_real_servers.py` | Add/remove filesystem, fetch servers during operation |
| Multiple reloads | Same file | 10+ successive reloads, verify no leaks |
| Concurrent requests | Same file | 100 requests in-flight during reload |
| Error scenarios | Same file | Invalid YAML, missing files, permission errors |
| Notification flow | Same file | Verify tools/resources/prompts notifications |

### Phase 4: Documentation & Release (1 day)

| Step | Files to Create/Update | Purpose |
|------|------------------------|---------|
| User guide | `docs/hot-reload-guide.md` | Explain what can reload, limitations, best practices |
| Configuration docs | `docs/configuration-specification.md` | Document hot-reload behavior |
| CLAUDE.md update | `CLAUDE.md` | Add to "Key Concepts" section |
| Changelog | `CHANGELOG.md` | Document new feature for v0.2.0 |
| Migration guide | `docs/migration/v0.1-to-v0.2.md` | How to leverage hot-reload |

### Decision Matrix

Choose your path:

| Scope | Effort | Risk | User Value | Recommendation |
|-------|--------|------|------------|----------------|
| **Fix bugs only** | 2-4 hours | LOW | LOW | Only if blocking v0.1.x release |
| **Plugin-only polish** | 1 day | LOW | LOW-MEDIUM | Good incremental step |
| **Full hot-reload** | 1-2 weeks | MEDIUM | HIGH | Best long-term solution for v0.2.0+ |

### Success Criteria

Before merging hot-reload:

- [ ] All existing tests pass (1000+ tests)
- [ ] All hot-reload tests pass (12 existing + 15-40 new)
- [ ] No memory leaks (run under memray)
- [ ] No generation tracking races (stress test with 1000 concurrent reloads)
- [ ] Clear error messages guide users
- [ ] Documentation complete
- [ ] Real user testing with Claude Desktop
- [ ] QC approval
