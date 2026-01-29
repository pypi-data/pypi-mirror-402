# First Release Checklist

## Overview

Essential requirements for the first public release (v0.1.0) of Gatekit, focusing only on what's absolutely necessary for launch.

## Context

Since package names are already reserved on PyPI at v0.1.0, the first real release will be v0.1.0.

## Requirements

### 1. PyPI Setup (COMPLETED ✅)

- [x] **Package Names Reserved**: `gatekit` and `gatekit-gateway` reserved on PyPI
- [ ] **Author Information**: Decide on author name and email for package metadata
- [ ] **Project URLs**: Homepage, repository, documentation URLs
- [ ] **API Tokens**: Set up PyPI API tokens for automated publishing
- [ ] **Trusted Publishing**: Configure GitHub Actions → PyPI trusted publishing

### 2. Package Metadata

**Update `pyproject.toml` with final metadata:**

```toml
[project]
name = "gatekit"
version = "0.1.0"
description = "MCP Security Gateway with Terminal User Interface"
readme = "README.md"
license = {text = "Apache-2.0"}
requires-python = ">=3.11"
authors = [
    {name = "[DECIDE]", email = "[DECIDE]@example.com"},
]
keywords = ["mcp", "security", "gateway", "proxy", "ai", "tools"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Security",
    "Topic :: System :: Networking :: Monitoring",
]

[project.urls]
Homepage = "[DECIDE]"
Repository = "[DECIDE]"
Documentation = "[DECIDE]"
Issues = "[DECIDE]/issues"
```

### 3. Legal Compliance

**Files needed:**

1. **NOTICE** (Apache 2.0 requirement):
   ```
   Gatekit
   Copyright 2025 [COPYRIGHT HOLDER]

   This product includes software developed by [COPYRIGHT HOLDER].

   [Add any third-party attributions here]
   ```

2. **SECURITY.md** (GitHub will prompt for this):
   ```markdown
   # Security Policy

   ## Supported Versions

   | Version | Supported          |
   | ------- | ------------------ |
   | 0.1.x   | :white_check_mark: |

   ## Reporting a Vulnerability

   Please report security vulnerabilities to [email].

   We will respond within 48 hours and provide updates every 5 business days.
   ```

### 4. Build Configuration

**For selective TUI source exclusion, update `pyproject.toml`:**

```toml
[tool.setuptools]
# Exclude TUI source files from distribution (keep only .pyc)
exclude = ["gatekit/tui/*.py"]
include-package-data = false

[tool.setuptools.packages.find]
exclude = ["tests*", "docs*"]
```

Or use `MANIFEST.in`:
```
# Include everything by default
include *

# Exclude TUI source files but include compiled versions
exclude gatekit/tui/*.py
```

### 5. Version Synchronization

**Script: `scripts/bump-version.py`**
```python
#!/usr/bin/env python3
"""Bump version across all relevant files"""

import re
import sys
from pathlib import Path

def bump_version(new_version: str):
    files_to_update = [
        "pyproject.toml",
        "gatekit/__init__.py",
        "gatekit/gateway/__init__.py",
    ]
    
    for file_path in files_to_update:
        path = Path(file_path)
        if path.exists():
            content = path.read_text()
            content = re.sub(r'version\s*=\s*"[^"]+"', f'version = "{new_version}"', content)
            content = re.sub(r'__version__\s*=\s*"[^"]+"', f'__version__ = "{new_version}"', content)
            path.write_text(content)
            print(f"Updated {file_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python bump-version.py 0.1.0")
        sys.exit(1)
    
    bump_version(sys.argv[1])
```

## Success Criteria

- [ ] Author and contact information decided
- [ ] Project URLs configured
- [ ] PyPI API tokens configured
- [ ] NOTICE file created
- [ ] SECURITY.md created
- [ ] Version bump script working
- [ ] Package builds successfully
- [ ] Package installs correctly from built wheel

## Questions to Resolve

1. **Author Information**: What name and email should be used?
2. **Project URLs**: Where will documentation be hosted?
3. **Copyright Holder**: Individual or company name?
4. **Contact Email**: For security reports and general contact?

## Implementation Timeline

- **Day 1**: Decide on author/contact information
- **Day 2**: Create NOTICE and SECURITY.md files
- **Day 3**: Configure PyPI tokens and trusted publishing
- **Day 4**: Test build and installation process
- **Day 5**: Finalize package metadata

## Dependencies

- None - this can be done independently of other phases

## Notes

This checklist focuses only on what's needed for the first release. Additional features like Docker images, alternative package managers, etc., can be added in future releases.