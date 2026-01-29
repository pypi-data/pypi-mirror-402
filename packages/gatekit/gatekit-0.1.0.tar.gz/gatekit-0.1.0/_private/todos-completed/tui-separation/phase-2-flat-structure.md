# Phase 2: Flat Structure Setup

## Overview

Set up proper licensing structure and entry points while maintaining the existing flat package organization. This phase is mostly about adding licensing files and preparing for selective source distribution.

## Prerequisites

- Phase 1 (Command Structure) must be completed
- All tests passing with new command structure

## Objectives

- Maintain existing flat package structure (Pythonic and simple)
- Add proper licensing files for dual-license model
- Prepare for selective TUI source exclusion in distribution
- Update entry points for the two commands

## Current State (Already Good!)

```
gatekit/
├── gatekit/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   ├── proxy/
│   ├── plugins/
│   ├── cli/
│   ├── utils/
│   └── tui/
├── pyproject.toml
├── LICENSE
└── tests/
```

## Target State (Minimal Changes)

```
gatekit/                       # Single package repository
├── gatekit/                   # The Python package (keep as-is!)
│   ├── __init__.py              # Update version to 0.1.0
│   ├── main.py                  # Update with two entry points
│   ├── config/                  # No changes
│   ├── proxy/                   # No changes
│   ├── plugins/                 # No changes
│   ├── cli/                     # No changes
│   ├── utils/                   # No changes
│   └── tui/                     # Add proprietary headers
├── pyproject.toml               # Update entry points and version
├── LICENSE                      # Keep Apache 2.0
├── LICENSE.TUI                  # Add proprietary license for TUI
├── NOTICE                       # Add for Apache 2.0 compliance
├── tests/                       # Update imports if needed
├── docs/                        # No changes
└── scripts/                     # Build scripts
```

## Detailed Requirements

### 1. Update Package Version and Metadata

**Update `gatekit/__init__.py`:**
```python
"""Gatekit - MCP Security Gateway with Terminal User Interface"""

__version__ = "0.1.0"  # Next version after PyPI reservation

# Main exports
from .config.loader import ConfigLoader
from .config.models import ProxyConfig
from .plugins.manager import PluginManager

__all__ = [
    'ConfigLoader',
    'ProxyConfig', 
    'PluginManager',
]
```

**Update `pyproject.toml`:**
```toml
[project]
name = "gatekit"
version = "0.1.0"  # Next version after PyPI reservation
description = "MCP Security Gateway with Terminal User Interface"
readme = "README.md"
license = {text = "Apache-2.0"}
requires-python = ">=3.11"
dependencies = [
    "pyyaml>=6.0.2",
    "aiohttp>=3.12.4",
    "pydantic>=2.11.5",
    "pathspec>=0.12.1",
    "textual>=0.47.0",  # For TUI functionality
]
authors = [
    {name = "[TO BE DECIDED]", email = "[TO BE DECIDED]"},
]

[project.scripts]
gatekit = "gatekit.main:tui_main"
gatekit-gateway = "gatekit.main:gateway_main"

[project.optional-dependencies]
dev = [
    "pytest>=8.3.5",
    "pytest-asyncio>=1.0.0",
    "pytest-cov>=6.1.1",
    "black>=25.1.0",
    "ruff>=0.11.12",
    "mypy>=1.16.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
```

### 2. Update Main Entry Points

**Update `gatekit/main.py` to have clean entry points:**

```python
"""Main entry points for Gatekit commands"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional


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
    
    # Set up logging if verbose
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    # Launch TUI
    try:
        from .tui.app import GatekitConfigApp
        app = GatekitConfigApp(args.config)
        app.run()
    except ImportError as e:
        print("Error: TUI functionality requires the Textual library.")
        print(f"Import error: {e}")
        print()
        print("To run the gateway without TUI:")
        print("  gatekit-gateway --config config.yaml")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching TUI: {e}", file=sys.stderr)
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
        try:
            from .config.loader import ConfigLoader
            loader = ConfigLoader()
            config = loader.load_from_file(args.config)
            print(f"Configuration valid: {args.config}")
            sys.exit(0)
        except Exception as e:
            print(f"Configuration invalid: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Run the gateway
    run_gateway(args.config, args.verbose)


def setup_logging(verbose: bool = False):
    """Configure logging for the gateway"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S.%fZ"
    )
    # Reduce noise from some third-party libraries
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def run_gateway(config_path: Path, verbose: bool = False):
    """Run Gatekit as MCP gateway/proxy"""
    # Import here to handle missing dependencies gracefully
    try:
        from .config.loader import ConfigLoader
        from .proxy.server import MCPProxy
        from .plugins.manager import PluginManager
        
        # Load configuration
        loader = ConfigLoader()
        config = loader.load_from_file(config_path)
        
        # Initialize plugin manager
        plugin_manager = PluginManager()
        plugin_manager.load_plugins(config)
        
        # Start proxy server
        proxy = MCPProxy(config, plugin_manager)
        
        # Run the proxy (this will block)
        import asyncio
        asyncio.run(proxy.run())
        
    except ImportError as e:
        print(f"Error: Missing required dependencies: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error running gateway: {e}", file=sys.stderr)
        sys.exit(1)


# Legacy support - can be removed in future versions
def main():
    """Legacy entry point - redirects to appropriate command"""
    if len(sys.argv) > 1 and sys.argv[1] == "proxy":
        print("DEPRECATED: Use 'gatekit-gateway' instead of 'gatekit proxy'", 
              file=sys.stderr)
        # Remove 'proxy' from args and run gateway
        sys.argv.pop(1)
        gateway_main()
    else:
        tui_main()


if __name__ == "__main__":
    main()
```

### 3. Add Licensing Files

**Create `LICENSE.TUI`:**
```
Gatekit TUI - Proprietary Freeware License

Copyright (c) 2025 [COPYRIGHT HOLDER]

Permission is hereby granted to use this software free of charge, subject to 
the following conditions:

1. The software may be used for any legal purpose
2. The software may NOT be redistributed as part of commercial products
3. The software may NOT be rebranded or white-labeled  
4. The software may NOT be included in competitive products

This software is provided "as is" without warranty of any kind.

Violators will be pursued under copyright law.
```

**Create `NOTICE` (required for Apache 2.0):**
```
Gatekit
Copyright 2025 [COPYRIGHT HOLDER]

This product includes software developed by [COPYRIGHT HOLDER].

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Third-party attributions:
[Add any required third-party attributions here]
```

### 4. Update README

**Update root `README.md`:**
```markdown
# Gatekit

A secure MCP (Model Context Protocol) gateway with visual configuration interface.

## Installation

```bash
pip install gatekit
```

## Usage

```bash
# Launch configuration interface
gatekit

# Run as MCP gateway  
gatekit-gateway --config config.yaml
```

## Commands

- **`gatekit`**: Interactive configuration interface (TUI)
- **`gatekit-gateway`**: Run as MCP security gateway

## MCP Client Configuration

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

## License

- **Gateway functionality**: Apache License 2.0 - see [LICENSE](LICENSE)
- **TUI interface**: Proprietary freeware - see [LICENSE.TUI](LICENSE.TUI)

Both components are free to use. The gateway is open source; the TUI is closed source but free.
```

### 5. Optional: Selective Source Exclusion

**If you want to exclude TUI source from distribution, add to `pyproject.toml`:**

```toml
[tool.setuptools.packages.find]
exclude = ["tests*", "docs*"]

# Optional: Exclude TUI source files from source distribution
[tool.setuptools]
exclude-package-data = {"gatekit.tui": ["*.py"]}
```

Or create `MANIFEST.in`:
```
include *
recursive-include gatekit *.py
# Optionally exclude TUI source files
# prune gatekit/tui
```

### 6. Build Scripts

**Create `scripts/build-package.sh`:**
```bash
#!/bin/bash
set -e

echo "Building Gatekit package..."

# Clean previous builds
rm -rf build/ dist/ *.egg-info/

# Build package
python -m build

echo "Package built successfully!"
echo "Built files:"
ls -la dist/
```

**Create `scripts/install-dev.sh`:**
```bash
#!/bin/bash
set -e

echo "Installing Gatekit in development mode..."

# Install in editable mode
pip install -e .[dev]

echo "Installation complete. Commands available:"
echo "  gatekit          - Launch TUI"
echo "  gatekit-gateway  - Run gateway"
```

## Validation Steps

**After setup:**

1. **Install in development mode:**
   ```bash
   pip install -e .
   ```

2. **Test commands:**
   ```bash
   gatekit --help
   gatekit-gateway --help
   ```

3. **Test imports:**
   ```python
   import gatekit
   from gatekit.config.loader import ConfigLoader
   from gatekit.tui.app import GatekitConfigApp
   ```

4. **Build and test package:**
   ```bash
   ./scripts/build-package.sh
   pip install dist/gatekit-*.whl
   ```

## Success Criteria

- [ ] Flat structure maintained (no unnecessary reorganization)
- [ ] Two commands work: `gatekit` and `gatekit-gateway`
- [ ] Licensing files added (LICENSE.TUI, NOTICE)
- [ ] Version updated to 0.1.0
- [ ] Package builds successfully
- [ ] All imports work as expected
- [ ] README updated with clear usage instructions

## Key Benefits of This Approach

1. **Minimal changes**: Keeps your existing code structure
2. **Pythonic**: Follows flat-is-better-than-nested principle
3. **Simple imports**: No deep nesting like `gatekit.gateway.config`
4. **Industry standard**: Matches how popular Python projects organize code
5. **Easy to understand**: Clear, straightforward structure

## Dependencies

- Phase 1 (Command Structure) completed
- Decision on copyright holder name for licenses
- PyPI account and tokens set up

## Timeline

This phase should be very quick since it's mostly adding files and updating configuration:

- **Day 1**: Update entry points and version
- **Day 2**: Add licensing files
- **Day 3**: Test and validate
- **Day 4**: Update documentation

Much simpler than the complex reorganization originally planned!