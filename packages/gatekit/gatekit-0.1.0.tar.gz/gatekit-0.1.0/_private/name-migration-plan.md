# Gatekit Rename Inventory

Complete mapping of all "gatekit" occurrences for future rename operation.

---

## Executive Summary

| Category | Count | Effort |
|----------|-------|--------|
| Package/directory structure | 1 dir + 60 files | High (foundational) |
| Import statements | ~200 | Automated (find/replace) |
| Entry points / CLI commands | 2 | High (user-facing) |
| String literals (MCP protocol) | ~10 | High (protocol-facing) |
| Default file paths | ~15 | Medium |
| JSON Schema URLs | 9 | Medium (domain decision) |
| Documentation files | ~35 | Medium (can batch) |
| Test files | ~60 | Medium (follows main code) |
| GitHub URLs | 3 | Low (once decided) |
| PyPI package name | 1 | Simple (fresh start at v0.1.0) |

**Total unique files to modify: ~130+**
**Total occurrences: ~500+**

---

## 1. CRITICAL: Package Identity

### 1.1 Package Name & Directory
```
gatekit/                    # Main package directory - RENAME
├── __init__.py
├── __main__.py
├── _version.py
├── main.py
├── server_manager.py
└── [all subdirectories]
```

### 1.2 pyproject.toml (lines 2, 50-51, 54-56, 63)
```toml
name = "gatekit"                                           # Package name
gatekit = "gatekit.main:tui_main"                        # TUI entry point
gatekit-gateway = "gatekit.main:gateway_main"            # Gateway entry point
Repository = "https://github.com/gatekit/gatekit"        # GitHub URL
Documentation = "https://github.com/gatekit/gatekit/tree/main/docs"
"Bug Tracker" = "https://github.com/gatekit/gatekit/issues"
path = "gatekit/_version.py"                               # Version file path
```

### 1.3 pyproject-gateway.toml (lines 2, 32)
```toml
name = "gatekit-gateway"
gatekit-gateway = "gatekit.main:gateway_main"
```

---

## 2. CRITICAL: MCP Protocol Identifiers

These appear in MCP handshakes and are visible to clients/servers.

### 2.1 Server Identity
**File:** `gatekit/proxy/server.py` (lines 40, 43, 1198)
```python
GATEKIT_VERSION = __version__
GATEKIT_METADATA_KEY = "_gatekit_metadata"
"serverInfo": {"name": "gatekit", "version": GATEKIT_VERSION}
```

### 2.2 Client Identity
**File:** `gatekit/server_manager.py` (line 133)
```python
"clientInfo": {"name": "gatekit", "version": __version__}
```

**File:** `gatekit/tui/utils/mcp_handshake.py` (lines 16, 34, 53)
```python
id="gatekit-handshake"
"clientInfo": {"name": "gatekit", "version": __version__}
id="gatekit-tools-probe"
```

---

## 3. HIGH: CLI Commands & Entry Points

### 3.1 Console Scripts
- `gatekit` → TUI launcher
- `gatekit-gateway` → MCP gateway/proxy

### 3.2 Help Text & Version Display
**File:** `gatekit/main.py` (lines ~648, 650, 772, 775, 781)
```python
"""Entry point for TUI (gatekit command)."""
"--version", action="version", version=f"Gatekit v{__version__}"
print("  pip install 'gatekit[tui]'")
print("  gatekit-gateway --config config.yaml")
"""Entry point for gateway (gatekit-gateway command)."""
```

### 3.3 Gateway Detection Logic
**File:** `gatekit/tui/guided_setup/detection.py`
- Detects `gatekit-gateway` in existing configs
- Detects `gatekit.main` module references
- Detects bare `gatekit` command

**File:** `gatekit/tui/guided_setup/gateway.py`
- `locate_gatekit_gateway()` function
- Searches PATH for `gatekit-gateway` executable

**File:** `gatekit/tui/guided_setup/migration_instructions.py`
- Hardcodes `"gatekit"` as server name in generated configs
- Detection patterns for existing gatekit installations

---

## 4. HIGH: File & Directory Paths

### 4.1 Debug Log Paths (Platform-Specific)
**File:** `gatekit/tui/debug/logger.py` (lines 42-43, 562, 729, 738)

| Platform | Directory | Files |
|----------|-----------|-------|
| macOS | `~/Library/Logs/gatekit/` | `gatekit_tui_debug.log`, `gatekit_tui_state_*.json` |
| Linux | `~/.local/state/gatekit/` | `gatekit_tui_debug.log`, `gatekit_tui_state_*.json` |
| Windows | `%LOCALAPPDATA%\gatekit\logs\` | `gatekit_tui_debug.log`, `gatekit_tui_state_*.json` |

**File:** `gatekit/diagnostics/collector.py` (lines 26, 29)
```python
log_dir = get_user_log_dir('gatekit')
debug_logs = glob.glob(os.path.join(log_dir, "gatekit_tui_debug*.log*"))
state_dumps = glob.glob(os.path.join(log_dir, "gatekit_tui_state_*.json"))
```

### 4.2 Configuration Paths
**File:** `gatekit/tui/guided_setup/detection.py`
- Linux: `~/.config/gatekit/gatekit.yaml`
- Windows: `%APPDATA%\gatekit\gatekit.yaml`

**File:** `gatekit/tui/recent_files.py`
- `get_user_state_dir('gatekit')` for recent files state

### 4.3 Default Audit Log Filenames
| File | Default Path |
|------|--------------|
| `gatekit/plugins/auditing/json_lines.py` (line 107) | `logs/gatekit_audit.jsonl` |
| `gatekit/plugins/auditing/csv.py` (line 117) | `logs/gatekit_audit.csv` |
| `gatekit/plugins/auditing/human_readable.py` (line 61) | `logs/gatekit_audit.log` |
| `gatekit/tui/guided_setup/config_generation.py` (line 125) | `logs/gatekit_audit.jsonl` |

### 4.4 Backup Directory
**File:** `gatekit/tui/screens/guided_setup/client_selection.py`
```python
Path.home() / "Documents" / "gatekit-restore"
```

---

## 5. MEDIUM: JSON Schema URLs (Domain Decision)

These reference `gatekit.ai` domain. Decision needed: keep domain or change?

| File | Schema URL |
|------|------------|
| `gatekit/plugins/middleware/tool_manager.py` | `https://gatekit.ai/schemas/tool-manager.json` |
| `gatekit/plugins/middleware/call_trace.py` | `https://gatekit.ai/schemas/call-trace.json` |
| `gatekit/plugins/security/secrets.py` | `https://gatekit.ai/schemas/secrets-filter.json` |
| `gatekit/plugins/security/prompt_injection.py` | `https://gatekit.ai/schemas/prompt-injection.json` |
| `gatekit/plugins/security/pii.py` | `https://gatekit.ai/schemas/pii-filter.json` |
| `gatekit/plugins/auditing/human_readable.py` | `https://gatekit.ai/schemas/human-readable-auditing.json` |
| `gatekit/plugins/auditing/csv.py` | `https://gatekit.ai/schemas/csv-auditing.json` |
| `gatekit/plugins/auditing/json_lines.py` | `https://gatekit.ai/schemas/json-lines-auditing.json` |
| `gatekit/tui/utils/json_form_adapter.py` | `https://gatekit.ai/schemas/common/tool-selection.json` |

---

## 6. MEDIUM: Function & Variable Names

### 6.1 Named Functions
| File | Function |
|------|----------|
| `gatekit/utils/version.py` | `get_gatekit_version()` |
| `gatekit/utils/version.py` | `get_gatekit_version_with_fallback()` |
| `gatekit/tui/guided_setup/config_generation.py` | `generate_gatekit_config()` |
| `gatekit/tui/guided_setup/gateway.py` | `locate_gatekit_gateway()` |

### 6.2 Constants
| File | Constant |
|------|----------|
| `gatekit/proxy/server.py` | `GATEKIT_VERSION` |
| `gatekit/proxy/server.py` | `GATEKIT_METADATA_KEY` |

### 6.3 Namespace Strings
**File:** `gatekit/plugins/auditing/base.py` (line 96)
```python
return f"gatekit.audit.{class_name}.{file_hash}"
```

**File:** `gatekit/plugins/manager.py`
```python
module_name = f"gatekit._plugins.{'.'.join(module_parts)}"
```

---

## 7. MEDIUM: TUI Display Text

### 7.1 App Title
**File:** `gatekit/tui/app.py`
```python
TITLE = "Gatekit Configuration Editor"
```

### 7.2 Welcome Screen
**File:** `gatekit/tui/screens/welcome.py`
```python
yield SelectableStatic("Gatekit Configuration Editor", classes="welcome-header")
```

### 7.3 Setup Complete Screen
**File:** `gatekit/tui/screens/setup_complete.py`
```python
yield SelectableStatic("Gatekit Config:", classes="file-label")
```

### 7.4 Client Setup Instructions
**File:** `gatekit/tui/screens/guided_setup/client_setup.py`
```python
command = f"gatekit {self.gatekit_config_path}"
id="gatekit_edit_command"
```

---

## 8. DOCUMENTATION FILES

### 8.1 Primary Documentation
| File | Occurrences | Notes |
|------|-------------|-------|
| `README.md` | ~15 | Title, install commands, usage |
| `CLAUDE.md` | ~45 | Project memory, commands, paths |
| `CHANGELOG.md` | ~10 | Release notes |
| `docs/configuration-specification.md` | ~20 | Config examples |
| `docs/security-model.md` | ~10 | Architecture docs |
| `docs/plugin-development-guide.md` | ~15 | Plugin examples |

### 8.2 Decision Records (24 files)
`docs/decision-records/001-024-*.md` - All reference gatekit in various contexts

### 8.3 Key ADRs with Heavy Usage
- `017-tui-invocation-pattern.md` - Command structure docs
- `005-configuration-management.md` - Config examples
- `012-configuration-path-resolution-strategy.md` - Path examples

### 8.4 Private Documentation
- `_private/todos/` - Active development tasks
- `_private/todos-completed/` - Historical records
- `_private/pre-release-tasks.md` - Release instructions
- `_private/web-presence-setup.md` - Domain setup (gatekit.ai)

---

## 9. TEST FILES

### 9.1 Test Classes Containing "gatekit"
- `TestGetGatekitVersion`
- `TestGetGatekitVersionWithFallback`
- `TestIsGatekitServer`
- `TestExtractGatekitConfigPath`
- `TestDetectGatekitInClient`
- `TestDetectedClientHasGatekit`
- `TestGenerateGatekitConfig`
- `TestUpdateGatekitInMigration`

### 9.2 Test Functions & Fixtures
```python
get_gatekit_exe()
get_gatekit_gateway_exe()
test_gatekit_gateway_help()
mock_clients_no_gatekit()
mock_clients_with_gatekit()
mock_clients_all_with_gatekit()
test_detects_gatekit_gateway_command()
test_has_gatekit_returns_true()
# ... many more
```

### 9.3 Test Config Files
- `tests/validation/manual-validation-config.yaml` - `/tmp/gatekit-validation/`
- `tests/validation/manual-validation-config-win.yaml` - `~/AppData/Local/gatekit/`
- `tests/validation/backups/claude-desktop-*.json` - Server registered as "gatekit"

---

## 10. IMPORT STATEMENTS (~200 occurrences)

All Python files in `gatekit/` and `tests/` contain imports like:
```python
from gatekit.main import tui_main
from gatekit._version import __version__
from gatekit.config.loader import ConfigLoader
from gatekit.plugins.manager import PluginManager
from gatekit.proxy.server import ProxyServer
# ... etc
```

**Files with most imports:**
- `gatekit/main.py`
- `gatekit/proxy/server.py`
- `gatekit/tui/app.py`
- `gatekit/plugins/manager.py`
- All test files

---

## 11. LOGGER NAMES (Automatic via `__name__`)

All loggers use `logging.getLogger(__name__)` which resolves to:
- `gatekit.proxy.server`
- `gatekit.proxy.stdio_server`
- `gatekit.main`
- `gatekit.server_manager`
- `gatekit.plugins.manager`
- `gatekit.plugins.security.pii`
- `gatekit.plugins.security.secrets`
- `gatekit.plugins.security.prompt_injection`
- `gatekit.plugins.auditing.json_lines`
- `gatekit.plugins.middleware.tool_manager`
- `gatekit.plugins.middleware.call_trace`
- `gatekit.tui.screens.config_editor.base`
- ... (~20+ more)

---

## 12. GENERATED / ARTIFACT FILES (Can Delete/Regenerate)

### 12.1 Config Files
- `configs/gatekit-*.yaml` (30+ files)
- `configs/logs/gatekit_audit.*`

### 12.2 Distribution
- `dist/gatekit-*.whl`
- `dist/gatekit-*.tar.gz`

---

## 13. EXTERNAL DEPENDENCIES

### 13.1 PyPI
- Current package name: `gatekit` (will be abandoned)
- New package: Fresh registration under new name, starting at v0.1.0

### 13.2 GitHub
- Repository URL: `https://github.com/gatekit/gatekit`
- Org name decision needed

### 13.3 Domain
- Current: `gatekit.ai`
- JSON Schema URLs reference this domain

---

## Rename Execution Plan

### Phase 1: Preparation
1. Choose new name
2. Verify PyPI availability
3. Register new domain (if applicable)
4. Create GitHub org/repo (if changing)

### Phase 2: Core Rename
1. Rename `gatekit/` directory to `{newname}/`
2. Update `pyproject.toml` package name and entry points
3. Update all import statements (IDE refactoring)
4. Update MCP protocol identifiers (serverInfo, clientInfo)

### Phase 3: Paths & Defaults
1. Update platform-specific paths (debug logs, config dirs)
2. Update default audit log filenames
3. Update JSON Schema URLs (if changing domain)

### Phase 4: User-Facing Text
1. Update CLI help text and version strings
2. Update TUI display text (titles, labels)
3. Update detection logic for gateway executable

### Phase 5: Documentation
1. Update README.md
2. Update CLAUDE.md
3. Update all docs/*.md files
4. Update decision records

### Phase 6: Tests
1. Update test class/function names
2. Update test fixtures
3. Update test config files
4. Run full test suite

### Phase 7: Distribution
1. Update GitHub URLs (new org/repo if applicable)
2. Reset version to 0.1.0 in `_version.py`
3. Clean up old artifacts (dist/, configs/)
4. Publish to PyPI under new name
5. Tag release as v0.1.0

### Verification
```bash
pytest tests/ -n auto          # All tests must pass
uv run ruff check {newname}    # Linting must pass
{newname} --version            # TUI works
{newname}-gateway --help       # Gateway works
```

---

## Notes

- **Total estimated effort**: 2-4 hours with IDE refactoring support
- **First release**: No backward compatibility needed - clean cut
- **Version reset**: New PyPI package starts at v0.1.0 (not 0.1.0)
- **No redirect needed**: Don't need to maintain old `gatekit` PyPI package
- **Domain**: Separate decision - can keep gatekit.ai or change
