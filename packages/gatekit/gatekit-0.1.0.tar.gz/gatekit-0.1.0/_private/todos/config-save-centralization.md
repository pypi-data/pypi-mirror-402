# Config Save Centralization

## Context

We currently serialize configurations through `gatekit/config/serialization.py`, but
three separate call sites are responsible for writing files:

- Config editor (`gatekit/tui/screens/config_editor/config_persistence.py`) – atomic write
- Guided setup save flow (`gatekit/tui/app.py`) – writes header comments + YAML string
- Connection test workflow (`gatekit/tui/app.py`) – rewrites YAML after identity discovery

Each path handles headers, validation flags, and error reporting differently, so the
written configuration is not fully canonical even though reading is centralized via
`ConfigLoader`.

## Requirements (Draft)

1. **Single entry point** for persisting `ProxyConfig`/config dicts.
2. **Atomic writes by default** (safe temp file + replace) with explicit opt-out if needed.
3. **UTF-8 encoding** and consistent indentation/ordering (leveraging `yaml.dump`).
4. **Optional header injection** to support guided-setup banners without duplicating logic.
5. **Explicit completeness toggle** – callers must opt in if they want to allow incomplete/draft configs (e.g., guided setup).
6. **Structured error handling** that surfaces `ConfigError` / actionable messaging.
7. **Documented concurrency expectations** (last write wins) so callers know we do not lock files today.
8. **Unit + integration coverage** ensuring round-trip stability and atomic-write behaviour.

## Proposed Implementation Sketch

1. Add a tiny filesystem helper, e.g. `gatekit/utils/filesystem.py::atomic_write_text(path, content)` to encapsulate safe temp-file writes.
2. Introduce `gatekit/config/persistence.py` with a single façade:
   ```python
   def save_config(path: Path, config: ProxyConfig, *,
                   allow_incomplete: bool = False,
                   header: Optional[str] = None,
                   atomic: bool = True) -> None
   ```
   - Internally call `config_to_dict(..., validate_drafts=not allow_incomplete)`.
   - Serialize with `yaml.dump` (sorted keys disabled, indent matches loader).
   - Delegate to `atomic_write_text` when `atomic=True`.
   - Wrap failures in `ConfigWriteError(path, reason, cause)`.
3. Update the three existing write paths to call `save_config`, passing `header` only from guided setup and `allow_incomplete=True` only where drafts are expected.
4. Update docs/ADR with the canonical save contract, including the note that comments/formatting are not preserved today.
5. Add tests covering:
   - Atomic swap behaviour (temp file cleaned up on success/failure).
   - Header passthrough (treat both `None` and empty string as “no header”).
   - `allow_incomplete=True` vs `False` behaviour, including an explicit regression test proving the inversion (`validate_drafts=not allow_incomplete`) does what we expect.
   - `ConfigWriteError` contents (inherits `ConfigError`, records `.path`, preserves the original exception via `__cause__`).
   - Round trip `load → save → load` semantic stability (resulting `ProxyConfig` equivalent even if formatting/order differs).

## Decisions / Notes

- **Headers:** start with a simple `Optional[str]` argument. If future flows need computed headers we can extend the API.
- **Completeness:** default to `allow_incomplete=False`. Callers must explicitly opt in when drafts are acceptable; no implicit sniffing.
- **Errors:** introduce `ConfigWriteError(ConfigError)` so TUI/CLI can show consistent messaging while retaining the original exception as `__cause__`.
  ```python
  from pathlib import Path
  from typing import Optional

  class ConfigWriteError(ConfigError):
      """Raised when configuration cannot be written to disk."""

      def __init__(self, path: Path, reason: str, cause: Optional[Exception] = None):
          self.path = path
          self.cause = cause
          super().__init__(
              f"Failed to write config to {path}: {reason}",
              error_type="write_error",
          )
  # Callers should use `raise ConfigWriteError(..., cause=err) from err` to preserve traceback.
  ```
- **Permissions:** rely on OS defaults + atomic rename semantics (no extra chmod handling for v0.1).
- **Comment/formatting loss:** document that saves overwrite user comments/formatting; acceptable for first release.
- **Temp files on crash:** atomic writes may leave `.tmp` files behind if the process dies mid-write; note this in docs and suggest users can safely delete them.
- **Concurrency:** last-write-wins; no file locking. Mention this in docs so expectations are clear.
- **Round-trip meaning:** tests cover semantic equivalence (`ProxyConfig` data matches) rather than byte-for-byte equality; defaults may become explicit in output and key order follows the serializer’s deterministic insertion order.

## Next Steps

1. Finalize the helper signature + error type in a brief design snippet (this doc).
2. Implement `atomic_write_text` + `save_config`.
3. Switch existing call sites to the helper (config editor → guided setup → connection test) and delete duplicated code.
4. Backfill the test cases listed above and update documentation references.
