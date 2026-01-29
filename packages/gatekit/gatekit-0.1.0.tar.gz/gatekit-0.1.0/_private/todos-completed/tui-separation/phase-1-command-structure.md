# Phase 1: Command Structure Implementation

## Overview

Implement the new command structure to replace `gatekit proxy` with `gatekit-gateway` as decided in ADR-019. This is the first phase of TUI separation and focuses on command structure changes only.

## Objectives

- Replace `gatekit proxy` command with `gatekit-gateway`
- Update all tests to use the new command structure
- Ensure no backward compatibility is needed (pre-release)
- Maintain current functionality while improving terminology clarity

## Current State

**Current Commands:**
```bash
gatekit                      # Launches TUI
gatekit proxy --config file  # Runs proxy/gateway
```

**Target Commands:**
```bash
gatekit                        # Launches TUI (unchanged)
gatekit-gateway --config file  # Runs proxy/gateway (renamed)
```

## Detailed Requirements

### 1. Update Main Entry Points

**File: `pyproject.toml`**

Current:
```toml
[project.scripts]
gatekit = "gatekit.main:main"
```

Required:
```toml
[project.scripts]
gatekit = "gatekit.main:tui_main"
gatekit-gateway = "gatekit.main:gateway_main"
```

### 2. Refactor Main Module

**File: `gatekit/main.py`**

**Add new entry point functions:**
```python
def tui_main():
    """Entry point for TUI (gatekit command)"""
    parser = argparse.ArgumentParser(
        description="Gatekit Security Gateway Configuration Interface"
    )
    parser.add_argument("--config", type=Path, 
                       help="Open TUI with specific configuration file")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    try:
        from gatekit.tui import run_tui
        run_tui(args.config)
    except ImportError:
        print("Error: TUI functionality requires the Textual library.")
        print()
        print("Install with TUI support:")
        print("  pip install 'gatekit[tui]'")
        print()
        print("To run the gateway without TUI:")
        print("  gatekit-gateway --config config.yaml")
        sys.exit(1)

def gateway_main():
    """Entry point for gateway (gatekit-gateway command)"""
    parser = argparse.ArgumentParser(
        description="Gatekit Security Gateway for MCP"
    )
    parser.add_argument("--config", type=Path, required=True,
                       help="Path to configuration file")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    parser.add_argument("--validate-only", action="store_true",
                       help="Validate configuration and exit")
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    if args.validate_only:
        # Load and validate config
        try:
            loader = ConfigLoader()
            config = loader.load_from_file(args.config)
            print(f"Configuration valid: {args.config}")
            sys.exit(0)
        except Exception as e:
            print(f"Configuration invalid: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Run the gateway
    run_gateway(args.config, args.verbose)

def main():
    """Legacy entry point - remove after Phase 1 complete"""
    # This function should be removed once new entry points are confirmed working
    print("DEPRECATED: Use 'gatekit' for TUI or 'gatekit-gateway' for proxy", 
          file=sys.stderr)
    sys.exit(1)
```

**Extract gateway functionality:**
```python
def run_gateway(config_path: Path, verbose: bool = False):
    """Run Gatekit as MCP gateway/proxy"""
    # Move existing proxy logic here from main()
    # This should contain all the current main() logic for proxy mode
    pass
```

### 3. Update TUI Entry Point

**File: `gatekit/tui/__init__.py`**

Ensure clean interface:
```python
"""Gatekit TUI module"""

def run_tui(config_path: Optional[Path] = None):
    """Launch the Gatekit TUI application"""
    from .app import GatekitConfigApp
    app = GatekitConfigApp(config_path)
    app.run()

__all__ = ['run_tui']
```

### 4. Test Updates

**Update all test files that reference the old command structure:**

1. **Find affected tests:**
   ```bash
   grep -r "gatekit proxy" tests/
   grep -r "proxy.*--config" tests/
   ```

2. **Update test patterns:**
   - Replace `gatekit proxy --config` with `gatekit-gateway --config`
   - Update subprocess calls in tests
   - Update documentation strings

3. **Specific files likely to need updates:**
   - `tests/unit/test_tui_invocation.py`
   - Any integration tests that spawn the proxy
   - CLI argument parsing tests

**Example test update:**
```python
# Before
result = subprocess.run(["gatekit", "proxy", "--config", "test.yaml"])

# After  
result = subprocess.run(["gatekit-gateway", "--config", "test.yaml"])
```

### 5. Configuration Examples

**Update example configurations and documentation:**

**File: `configs/dummy/basic.yaml` and similar**
- Update any comments that reference the old command structure

**MCP Client Examples:**
```json
{
  "mcpServers": {
    "secure-filesystem": {
      "command": "gatekit-gateway",
      "args": ["--config", "/path/to/gatekit.yaml"]
    }
  }
}
```

### 6. Help Text and Error Messages

**Update help text and error messages throughout codebase:**

1. **Search for references to old command:**
   ```bash
   grep -r "gatekit proxy" gatekit/
   grep -r "proxy.*config" gatekit/
   ```

2. **Update error messages:**
   ```python
   # Example error message update
   print("To run the gateway: gatekit-gateway --config config.yaml")
   ```

### 7. Validation Steps

**After implementation, verify:**

1. **Commands work correctly:**
   ```bash
   # Should launch TUI
   gatekit
   
   # Should launch TUI with specific config
   gatekit --config configs/dummy/basic.yaml
   
   # Should run gateway
   gatekit-gateway --config configs/dummy/basic.yaml
   
   # Should validate config
   gatekit-gateway --config configs/dummy/basic.yaml --validate-only
   ```

2. **Test suite passes:**
   ```bash
   pytest tests/ -v
   ```

3. **No references to old command remain:**
   ```bash
   grep -r "gatekit proxy" . --exclude-dir=.git
   # Should return no results (except this requirements file)
   ```

## Success Criteria

- [ ] `gatekit` command launches TUI successfully
- [ ] `gatekit-gateway --config file` runs the proxy successfully  
- [ ] All tests updated and passing
- [ ] No references to `gatekit proxy` remain in codebase
- [ ] Help text and error messages reference correct commands
- [ ] Both commands handle `--verbose` flag correctly
- [ ] `gatekit-gateway --validate-only` works for config validation

## Dependencies

- None (this is the first phase)

## Next Phase

After completing this phase, proceed to **Phase 2: Monorepo Setup** which will reorganize the codebase structure.

## Implementation Notes

### Testing Strategy

1. Test the new entry points manually first
2. Update tests incrementally, running the suite after each batch
3. Focus on maintaining existing functionality while changing only the command structure

### Rollback Plan

If issues arise:
1. Revert `pyproject.toml` changes
2. Revert `main.py` changes  
3. Restore original test files from git

### Performance Considerations

- No performance impact expected (same code, different entry points)
- Gateway startup time should remain identical

### Error Handling

- Provide clear error messages when users try old commands
- Ensure graceful handling when TUI dependencies are missing
- Validate config files early in gateway startup