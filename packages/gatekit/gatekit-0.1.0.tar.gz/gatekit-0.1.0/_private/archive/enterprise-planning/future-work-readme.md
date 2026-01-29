# Future Work - Deferred Plugin Implementations

This directory contains plugin implementations and their tests that have been deferred from the initial release.

## Deferred Plugins

### CEF (Common Event Format) Auditing Plugin
**Status**: Complete implementation deferred for v0.2.0+  
**Location**: `plugins/auditing/common_event_format.py`  
**Description**: SIEM-ready audit logging in industry-standard CEF format with compliance extensions

### Syslog Auditing Plugin  
**Status**: Complete implementation deferred for v0.2.0+  
**Location**: `plugins/auditing/syslog.py`  
**Description**: RFC 5424/3164 syslog format with TLS transport support for centralized logging

### OpenTelemetry Auditing Plugin
**Status**: Complete implementation deferred for v0.2.0+
**Location**: `plugins/auditing/opentelemetry.py`
**Description**: OpenTelemetry integration for distributed tracing and observability of MCP interactions

### Filesystem Permissions Security Plugin
**Status**: Complete implementation deferred for v0.2.0+
**Location**: `plugins/security/filesystem_server.py`
**Description**: Path-based access control for @modelcontextprotocol/server-filesystem with read/write permission levels using glob patterns

## How to Restore These Plugins

When ready to implement these features, follow these steps:

### 1. Restore Plugin Files
```bash
# From project root directory
cp future-work/plugins/auditing/common_event_format.py gatekit/plugins/auditing/
cp future-work/plugins/auditing/syslog.py gatekit/plugins/auditing/
cp future-work/plugins/auditing/opentelemetry.py gatekit/plugins/auditing/
cp future-work/plugins/security/filesystem_server.py gatekit/plugins/security/
```

### 2. Restore Test Files
```bash
# Unit tests
cp future-work/tests/unit/test_cef_compliance.py tests/unit/
cp future-work/tests/unit/test_cef_formatter.py tests/unit/
cp future-work/tests/unit/test_cef_integration.py tests/unit/
cp future-work/tests/unit/test_otel_auditing.py tests/unit/
cp future-work/tests/unit/test_filesystem_server_security_plugin.py tests/unit/
cp future-work/tests/unit/test_filesystem_security_path_resolution.py tests/unit/

# Integration tests
cp future-work/tests/integration/test_otel_integration.py tests/integration/
cp future-work/tests/integration/test_filesystem_server_security_integration.py tests/integration/

# Validation tests
cp future-work/tests/validation/test_cef_validation.py tests/validation/
cp future-work/tests/validation/test_otel_validation.py tests/validation/
```

### 3. Verify Integration
After restoration, run these commands to ensure everything works:

```bash
# Run all tests
pytest tests/

# Test plugin discovery
python -c "
from gatekit.plugins.manager import PluginManager
manager = PluginManager({})
policies = manager._discover_policies('auditing')
print('CEF Plugin:', 'cef_auditing' in policies)
print('Syslog Plugin:', 'syslog_auditing' in policies)
print('OpenTelemetry Plugin:', 'otel_auditing' in policies)
"

# Test TUI (should show the restored plugins)
gatekit --tui
```

### 4. Update Configuration Examples
You may need to update example configurations to include these plugins:
- `configs/tutorials/2-implementing-audit-logging.yaml`
- `configs/dummy/*.yaml` files

### 5. Update Documentation
Consider updating:
- `docs/user/tutorials/2-implementing-audit-logging.md`
- Plugin documentation in `docs/user/guides/plugin-configuration.md`

## Plugin Implementation Status

All three plugins were fully implemented with:
- ✅ Complete core functionality
- ✅ Configuration schemas for TUI integration
- ✅ Comprehensive test coverage
- ✅ Validation with third-party tools (pycef, etc.)
- ✅ Error handling and logging
- ✅ Performance optimizations
- ✅ Security features (sanitization, field limits)

They were moved here to simplify the initial release, not because of implementation issues.

## Dependencies

When restoring these plugins, you may need to install additional dependencies:

```bash
# For CEF validation (optional, for tests/validation/)
pip install pycef

# For syslog TLS support
# No additional dependencies required - uses Python stdlib ssl

# For OpenTelemetry support (optional, for tests/validation/)
pip install opentelemetry-api opentelemetry-sdk
```

## Middleware Migration Changes

The core plugin system underwent significant refactoring while these plugins were in future-work. Key changes completed:

### Completed Changes (docs/todos-completed/middleware/)
- **Phase 1**: Renamed SecurityPlugin methods from `check_*` to `process_*` 
- **Phase 2**: Added new `MiddlewareResult` and `SecurityResult` types with inheritance structure
- **Phase 3**: **COMPLETED** - Migrated entire codebase from `PolicyDecision` to `SecurityResult`
- **Phase 4**: **COMPLETED** - Created `MiddlewarePlugin` base class and established plugin hierarchy

### Pending Changes (docs/todos/middleware/)
- **Phase 5**: Update `PluginManager` to support middleware plugin processing pipeline  
- **Phase 6**: Migrate `tool_allowlist` plugin to use new middleware capabilities

### Current Plugin Architecture (Phase 4 Complete)

The new plugin hierarchy is now established:

```
PluginInterface
├── MiddlewarePlugin (NEW)
│   └── SecurityPlugin (now extends MiddlewarePlugin)
├── AuditingPlugin (unchanged)
│   └── BaseAuditingPlugin (unchanged)
│       ├── CefAuditingPlugin
│       ├── OtelAuditingPlugin
│       └── SyslogAuditingPlugin
└── PathResolvablePlugin (unchanged)
```

**New capabilities available:**
- **ProcessingPipeline Types**: `PipelineStage` and `ProcessingPipeline` for full observability
- **MiddlewarePlugin Features**: Priority-based ordering (0-100), critical/non-critical configuration
- **Content Modification**: Future middleware plugins can modify content or complete requests early

### Impact on Future-Work Plugins

**✅ FULLY COMPATIBLE** - When restoring these plugins, they work without modification since:

1. **CEF and Syslog plugins**: Extend `BaseAuditingPlugin` → `AuditingPlugin` (interface unchanged)
2. **OpenTelemetry plugin**: Also extends `BaseAuditingPlugin` (interface unchanged)
3. **AuditingPlugin**: Still extends `PluginInterface` directly - no changes needed

The MiddlewarePlugin changes only affect SecurityPlugin inheritance, not auditing plugins.

### Migration Status

**✅ UPDATED FOR CURRENT INTERFACES** - The future-work plugins have been updated to be compatible with the current codebase:

- All `PolicyDecision` references migrated to `SecurityResult`
- Plugins and tests use current interface signatures  
- Compatible with Phase 4 MiddlewarePlugin architecture
- Ready to restore without additional migration work

Verification (already completed):
```bash
# ✅ No PolicyDecision references found
# ✅ Using current SecurityResult interface
# ✅ Compatible with MiddlewarePlugin hierarchy
```

## Notes

- The plugins follow the same architecture patterns as other auditing plugins
- They inherit from `BaseAuditingPlugin` for shared functionality
- Configuration uses the standard plugin schema system
- Both plugins support all standard auditing features (path resolution, rotation, etc.)