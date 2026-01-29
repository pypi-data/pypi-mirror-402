# Pre-Release Tasks

## Overview

Consolidated pre-release engineering tasks that should be completed before public launch. These tasks don't block current TUI development but are important for professional release.

## Context

This combines several release engineering tasks:
- Build automation and CI/CD setup
- TUI source protection decisions and implementation
- License header updates for source files
- Version management and PyPI publishing preparation
- Public repository synchronization and community setup
- Documentation updates for new command structure and licensing model
- Final release preparation and PyPI publishing

All tasks in this document can be deferred until preparing for launch without impacting development velocity.

## Combined Requirements

### 1. Build System Automation

**Objective**: Set up automated build system for the single Gatekit package with optional TUI source exclusion for distribution protection.

**Prerequisites**:
- Phase 1 (Command Structure) completed ✅
- Phase 2 (Flat Structure Setup) completed ✅
- Single package building successfully locally ✅

**Components**:

#### Version Management System
**File: `scripts/update-version.py`**
```python
#!/usr/bin/env python3
"""Update version across all relevant files"""

import re
import sys
from pathlib import Path


def update_version(new_version: str):
    """Update version in all relevant files"""
    
    files_to_update = [
        ("pyproject.toml", r'version\s*=\s*"[^"]+"', f'version = "{new_version}"'),
        ("gatekit/__init__.py", r'__version__\s*=\s*"[^"]+"', f'__version__ = "{new_version}"'),
    ]
    
    for file_path, pattern, replacement in files_to_update:
        path = Path(file_path)
        if not path.exists():
            print(f"Warning: {file_path} not found")
            continue
            
        content = path.read_text()
        updated_content = re.sub(pattern, replacement, content)
        
        if content != updated_content:
            path.write_text(updated_content)
            print(f"Updated {file_path}")
        else:
            print(f"No changes needed in {file_path}")


def get_current_version():
    """Get current version from pyproject.toml"""
    content = Path("pyproject.toml").read_text()
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    return match.group(1) if match else None


if __name__ == "__main__":
    if len(sys.argv) != 2:
        current = get_current_version()
        print(f"Current version: {current}")
        print("Usage: python update-version.py <new_version>")
        print("Example: python update-version.py 0.1.2")
        sys.exit(1)
    
    new_version = sys.argv[1]
    
    # Validate version format (basic)
    if not re.match(r'\d+\.\d+\.\d+', new_version):
        print("Error: Version must be in format X.Y.Z")
        sys.exit(1)
    
    update_version(new_version)
    print(f"Version updated to {new_version}")
```

#### Publishing Preparation Scripts
**File: `scripts/prepare-release.sh`**
```bash
#!/bin/bash
set -e

# This script prepares for release but does not publish
# Actual publishing is deferred to pre-launch phase

VERSION=$1
if [[ -z "$VERSION" ]]; then
    echo "Usage: ./prepare-release.sh <version>"
    echo "Example: ./prepare-release.sh 0.1.0"
    exit 1
fi

echo "Preparing release $VERSION..."

# Update versions
python scripts/update-version.py $VERSION

# Build packages
python -m build

# Run tests
echo "Running tests..."
pytest tests/ -v

if [[ $? -ne 0 ]]; then
    echo "Tests failed! Aborting release."
    exit 1
fi

# Create release directory
RELEASE_DIR="releases/$VERSION"
mkdir -p "$RELEASE_DIR"

# Copy build artifacts
cp dist/* "$RELEASE_DIR/"

# Create release notes template
cat > "$RELEASE_DIR/RELEASE_NOTES.md" << EOF
# Release $VERSION

## Changes

- [Add your changes here]

## Installation

\`\`\`bash
pip install gatekit==$VERSION
\`\`\`

## Files

- gatekit-$VERSION.tar.gz (source)
- gatekit-$VERSION-py3-none-any.whl

EOF

echo "Release $VERSION prepared in $RELEASE_DIR"
echo "Review RELEASE_NOTES.md before publishing"

# Show next steps
echo ""
echo "Next steps:"
echo "1. Review files in $RELEASE_DIR"
echo "2. Update $RELEASE_DIR/RELEASE_NOTES.md"
echo "3. Create git tag: git tag v$VERSION"
echo "4. Publish when ready (see publishing scripts)"
```

#### GitHub Actions Workflow
**File: `.github/workflows/build-packages.yml`**
```yaml
name: Build Packages

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  release:
    types: [ created ]

jobs:
  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install build dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build pytest pytest-asyncio
    
    - name: Install package in development mode
      run: |
        pip install -e .[dev]
    
    - name: Run tests
      run: |
        pytest tests/ -v
    
    - name: Build packages
      run: |
        python -m build
    
    - name: Test installation from wheels
      run: |
        # Create fresh virtual environment for testing
        python -m venv test-env
        source test-env/bin/activate
        
        # Install from built wheel
        WHEEL_FILE=$(ls dist/*.whl | head -n1)
        pip install "$WHEEL_FILE"
        
        # Test commands
        gatekit --help
        gatekit-gateway --help
    
    - name: Upload build artifacts
      uses: actions/upload-artifact@v3
      if: matrix.python-version == '3.11'  # Only upload once
      with:
        name: packages
        path: dist/
```

### 2. TUI Build Protection

**Objective**: Determine and implement appropriate level of code protection for TUI components to prevent easy source code access while maintaining functionality and reasonable build complexity.

**Decision Required**: Choose protection level for TUI source code distribution.

#### Recommended Approach: Start Simple, Upgrade If Needed

**Phase 1 (Immediate)**: Standard Wheel Distribution
- Implement wheel-only distribution immediately
- Focus on legal protection and professional presentation
- Monitor for actual copying attempts

**Phase 2 (If Needed)**: Bytecode Compilation
- Upgrade to bytecode if we see evidence of source code inspection
- Provides moderate deterrent with reasonable complexity

**Phase 3 (If Required)**: Evaluate Cython
- Only if significant competitive pressure emerges
- Requires major build infrastructure investment

#### Implementation Requirements

**Immediate (Phase 1)**:

1. **Update build scripts** to create wheel-only for TUI:
   ```bash
   # Build wheel-only (exclude source distribution)
   python -m build --wheel
   ```

2. **Add clear licensing** in wheel metadata and startup:
   ```python
   # In TUI startup
   print("Gatekit TUI - Proprietary Freeware")
   print("Copyright (c) 2025 Gatekit, LLC. Not for redistribution.")
   ```

3. **Document legal protection** is already in LICENSE.TUI ✅

**Future Phases (If Needed)**:

**Bytecode Compilation Script**:
```python
# scripts/compile-tui-bytecode.py
import py_compile
import shutil
from pathlib import Path

def compile_directory(source_dir, target_dir):
    if target_dir.exists():
        shutil.rmtree(target_dir)
    
    target_dir.mkdir(parents=True)
    
    for py_file in source_dir.rglob("*.py"):
        rel_path = py_file.relative_to(source_dir)
        target_file = target_dir / rel_path.with_suffix('.pyc')
        target_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            py_compile.compile(py_file, target_file, doraise=True)
            print(f"Compiled: {rel_path}")
        except Exception as e:
            print(f"Failed to compile {rel_path}: {e}")
            return False
    return True

if __name__ == "__main__":
    source_dir = Path("gatekit/tui")
    target_dir = Path("build/compiled-tui/gatekit/tui")
    
    if not source_dir.exists():
        print(f"Error: Source directory {source_dir} not found")
        sys.exit(1)
    
    if compile_directory(source_dir, target_dir):
        print("TUI compilation successful")
    else:
        print("TUI compilation failed")
        sys.exit(1)
```

### 3. License Header Updates

**Objective**: Add Apache 2.0 license headers to gateway source files and proprietary headers to TUI files.

**Context**: While license headers are not legally required (we have LICENSE and NOTICE files), they are recommended best practice for professional software distribution.

#### Target Header Formats

**Apache 2.0 Header (Gateway Files)**:
```python
# Copyright (c) 2025 Gatekit, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
```

**Proprietary Header (TUI Files)**:
```python
# Copyright (c) 2025 Gatekit, LLC
# Proprietary Software - All Rights Reserved
# Free to use but not for redistribution
```

#### Implementation

**License Header Update Script**:
**File: `scripts/update-license-headers.py`**
```python
#!/usr/bin/env python3
"""Update license headers from AGPL to Apache 2.0"""

import re
import sys
from pathlib import Path
from typing import List, Optional

# Apache 2.0 header template
APACHE_HEADER_TEMPLATE = '''# Copyright (c) {year} {copyright_holder}
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''

# TUI proprietary header template
PROPRIETARY_HEADER_TEMPLATE = '''# Copyright (c) {year} {copyright_holder}
# Proprietary Software - All Rights Reserved
# Free to use but not for redistribution
'''

class LicenseUpdater:
    def __init__(self, copyright_holder: str, year: str = "2025"):
        self.copyright_holder = copyright_holder
        self.year = year
        
    def detect_current_header(self, content: str) -> Optional[str]:
        """Detect type of current license header"""
        if "GNU Affero General Public License" in content:
            return "AGPL"
        elif "Apache License" in content:
            return "Apache"
        elif "Proprietary Software" in content:
            return "Proprietary"
        elif "Copyright" in content[:500]:  # Check first 500 chars
            return "Other"
        return None
    
    def extract_header_region(self, content: str) -> tuple[str, str, str]:
        """Extract header, main content, and determine boundaries"""
        lines = content.split('\n')
        
        # Find header boundaries
        header_start = 0
        header_end = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip shebang and encoding declarations
            if i == 0 and stripped.startswith('#!'):
                continue
            if stripped.startswith('# -*- coding:') or stripped.startswith('# coding:'):
                continue
                
            # Look for copyright or license indicators
            if any(keyword in stripped for keyword in ['Copyright', 'License', 'GNU', 'Apache']):
                if header_start == 0:
                    header_start = i
                header_end = i
            elif header_start > 0 and not stripped.startswith('#') and stripped:
                # Found non-comment, non-empty line after header
                break
        
        if header_start == 0 and header_end == 0:
            # No header found - add to beginning after shebang/encoding
            preamble_lines = []
            content_start = 0
            for i, line in enumerate(lines):
                if line.startswith('#!') or 'coding:' in line:
                    preamble_lines.append(line)
                    content_start = i + 1
                else:
                    break
            
            preamble = '\n'.join(preamble_lines)
            remainder = '\n'.join(lines[content_start:])
            return "", preamble + '\n' + remainder if preamble else remainder, content_start
        
        header_lines = lines[header_start:header_end + 1]
        remaining_lines = lines[header_end + 1:]
        
        # Handle module docstrings that come after headers
        while remaining_lines and not remaining_lines[0].strip():
            remaining_lines = remaining_lines[1:]
        
        header = '\n'.join(header_lines)
        remainder = '\n'.join(remaining_lines)
        
        return header, remainder, header_start
    
    def update_file_header(self, file_path: Path, target_license: str) -> bool:
        """Update license header in a single file"""
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError) as e:
            print(f"Skipping {file_path}: {e}")
            return False
        
        current_license = self.detect_current_header(content)
        
        if current_license == target_license:
            print(f"Already {target_license} license: {file_path}")
            return True
        
        # Extract current header and content
        old_header, remainder, header_start = self.extract_header_region(content)
        
        # Generate new header
        if target_license == "Apache":
            new_header = APACHE_HEADER_TEMPLATE.format(
                year=self.year,
                copyright_holder=self.copyright_holder
            ).strip()
        elif target_license == "Proprietary":
            new_header = PROPRIETARY_HEADER_TEMPLATE.format(
                year=self.year,
                copyright_holder=self.copyright_holder
            ).strip()
        else:
            print(f"Unknown target license: {target_license}")
            return False
        
        # Preserve any shebang or encoding
        lines = content.split('\n')
        preamble = []
        for line in lines[:header_start]:
            if line.startswith('#!') or 'coding:' in line:
                preamble.append(line)
            else:
                break
        
        # Reconstruct file
        if preamble:
            new_content = '\n'.join(preamble) + '\n\n' + new_header + '\n\n' + remainder
        else:
            new_content = new_header + '\n\n' + remainder
        
        # Write back
        file_path.write_text(new_content, encoding='utf-8')
        print(f"Updated {file_path}: {current_license} → {target_license}")
        return True
    
    def update_directory(self, directory: Path, target_license: str, 
                        patterns: List[str] = None) -> tuple[int, int]:
        """Update all files in directory matching patterns"""
        if patterns is None:
            patterns = ["*.py"]
        
        updated = 0
        failed = 0
        
        for pattern in patterns:
            for file_path in directory.rglob(pattern):
                if file_path.is_file():
                    if self.update_file_header(file_path, target_license):
                        updated += 1
                    else:
                        failed += 1
        
        return updated, failed


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Update license headers")
    parser.add_argument("--copyright-holder", default="Gatekit, LLC",
                       help="Copyright holder name")
    parser.add_argument("--year", default="2025",
                       help="Copyright year")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be updated without making changes")
    
    args = parser.parse_args()
    
    updater = LicenseUpdater(args.copyright_holder, args.year)
    
    if args.dry_run:
        print("DRY RUN - No files will be modified")
    
    # Update main package files to Apache 2.0  
    main_dir = Path("gatekit")
    if main_dir.exists():
        print(f"Updating main package files to Apache 2.0...")
        if not args.dry_run:
            # Update all files except TUI to Apache 2.0
            for py_file in main_dir.rglob("*.py"):
                if "tui" not in str(py_file):
                    updater.update_file_header(py_file, "Apache")
    
    # Update TUI files to Proprietary
    tui_dir = Path("gatekit/tui")
    if tui_dir.exists():
        print(f"Updating TUI files to Proprietary...")
        if not args.dry_run:
            updated, failed = updater.update_directory(tui_dir, "Proprietary")
            print(f"TUI: {updated} updated, {failed} failed")


if __name__ == "__main__":
    main()
```

**License Validation Script**:
**File: `scripts/validate-license-headers.py`**
```python
#!/usr/bin/env python3
"""Validate license headers are correct and consistent"""

import sys
from pathlib import Path
from collections import defaultdict


def check_file_license(file_path: Path) -> str:
    """Check what license a file has"""
    try:
        content = file_path.read_text(encoding='utf-8')
    except:
        return "ERROR"
    
    if "Apache License" in content:
        return "Apache"
    elif "GNU Affero General Public License" in content:
        return "AGPL"
    elif "Proprietary Software" in content:
        return "Proprietary"
    elif "Copyright" in content[:500]:
        return "Other"
    else:
        return "None"


def main():
    results = defaultdict(list)
    
    # Check main package files
    main_dir = Path("gatekit")
    if main_dir.exists():
        for py_file in main_dir.rglob("*.py"):
            license_type = check_file_license(py_file)
            if "tui" in str(py_file):
                results[f"TUI-{license_type}"].append(str(py_file))
            else:
                results[f"Core-{license_type}"].append(str(py_file))
    
    # Report results
    errors = 0
    
    print("License Header Validation Report")
    print("=" * 40)
    
    for category, files in sorted(results.items()):
        print(f"\n{category}: {len(files)} files")
        
        # Check for problems
        if "Core-AGPL" in category or "Core-Other" in category or "Core-None" in category:
            print("  ❌ ERROR: Core files should have Apache license")
            errors += len(files)
        elif "TUI-AGPL" in category or "TUI-Apache" in category or "TUI-None" in category:
            print("  ❌ ERROR: TUI files should have Proprietary license")
            errors += len(files)
        elif "Core-Apache" in category or "TUI-Proprietary" in category:
            print("  ✅ OK")
        
        # Show first few files for debugging
        for file_path in files[:3]:
            print(f"    {file_path}")
        if len(files) > 3:
            print(f"    ... and {len(files) - 3} more")
    
    if errors > 0:
        print(f"\n❌ {errors} files have incorrect licenses")
        return 1
    else:
        print("\n✅ All files have correct licenses")
        return 0


if __name__ == "__main__":
    sys.exit(main())
```

## Success Criteria

**Build System**:
- [ ] Package builds successfully via automation
- [ ] Version synchronization works across files
- [ ] Local testing scripts validate installation
- [ ] CI/CD pipeline runs and passes
- [ ] Release preparation creates correct artifacts

**TUI Protection**:
- [ ] TUI package builds as wheel-only (no .tar.gz source)
- [ ] Clear licensing messages displayed
- [ ] Legal terms easily discoverable
- [ ] Build process remains simple and reliable

**License Headers**:
- [ ] All gateway files have Apache 2.0 headers
- [ ] All TUI files have proprietary headers  
- [ ] No AGPL headers remain in codebase
- [ ] License validation script passes
- [ ] Build process includes license validation

**Public Repository**:
- [ ] Public repository contains only open source components
- [ ] Automated sync process works reliably
- [ ] Community can easily contribute to core functionality
- [ ] No sensitive information leaks to public repo
- [ ] Professional presentation for public audience
- [ ] Clear separation between private and public codebases

**Documentation**:
- [ ] All documentation reflects new command structure
- [ ] Dual-license model is clearly explained
- [ ] Installation instructions are accurate and complete
- [ ] Migration guidance is provided for any existing users
- [ ] Examples and code snippets are updated and tested
- [ ] Licensing information is clear and comprehensive
- [ ] Documentation is professional and user-friendly

**Release Preparation**:
- [ ] Author and contact information decided
- [ ] Project URLs configured
- [ ] PyPI API tokens configured
- [ ] SECURITY.md created
- [ ] Version bump script working
- [ ] Package builds successfully
- [ ] Package installs correctly from built wheel

## Implementation Timeline

This entire pre-release task list can be implemented when preparing for public launch:

- **Week 1**: Set up build automation scripts and CI/CD
- **Week 2**: Implement TUI protection (start with Phase 1 wheel-only)
- **Week 3**: Add license headers to all source files
- **Week 4**: Update all documentation for new command structure and licensing
- **Week 5**: Set up public repository synchronization and community infrastructure
- **Week 6**: Final release preparation (PyPI setup, metadata, version management)
- **Week 7**: Test and validate complete release process

## Dependencies

- Phases 1 and 2 of TUI separation completed ✅
- GitHub Actions runner configured (when ready for CI/CD)
- Decision on copyright holder name: "Gatekit, LLC" ✅
- PyPI accounts prepared (for actual publishing)

## Questions to Resolve

1. **TUI Protection Level**: Start with simple wheel-only distribution or implement bytecode compilation immediately?
2. **CI/CD Timing**: Set up GitHub Actions now or wait until closer to release?
3. **License Headers**: Add immediately or wait until all other development is complete?
4. **Public Repo Timing**: Set up public repository immediately or wait until first public release?
5. **Community Management**: Who will manage public repo issues/PRs and community engagement?
6. **Sync Frequency**: How often should we sync (every release, weekly, etc.)?
7. **Author Information**: What name and email should be used for package metadata?
8. **Project URLs**: Where will documentation be hosted?
9. **Copyright Holder**: Individual or company name?
10. **Contact Email**: For security reports and general contact?

### 4. Public Repository Synchronization

**Objective**: Set up automated synchronization between the private development repository and a public repository that contains only the Apache 2.0 licensed core functionality, enabling community access while protecting proprietary components.

**Context**: As part of the dual-license open core model, we need to:
- Maintain development in private repository with full history
- Publish only core functionality to public repository
- Filter out TUI code, private development history, and sensitive information
- Provide clean, professional public repository for community engagement

#### Repository Structure Planning

**Content to Include in Public Repo**:
- Core source code (`gatekit/` excluding `gatekit/tui/`)
- Core tests (`tests/` filtered for core-only)
- Public documentation (`docs/` filtered)
- Example configurations (`configs/`)
- Build scripts for core (`scripts/` filtered)
- Root package files (`pyproject.toml`, `LICENSE`, `README.md`)

**Content to Exclude from Public Repo**:
- TUI source code (`gatekit/tui/`)
- Private development scripts
- Sensitive documentation (todos with business info, ADRs with competitive details)
- Development artifacts and temporary files
- Private configuration examples
- Personal/company-specific information

#### Automated Sync Process

**File: `scripts/sync-public-repo.sh`**
```bash
#!/bin/bash
set -e

# Configuration
PRIVATE_REPO_PATH="."
PUBLIC_REPO_URL="git@github.com:user/gatekit.git"
TEMP_DIR=$(mktemp -d)
BRANCH="main"

echo "Syncing to public repository..."

# Validate we're in the right place
if [[ ! -f "pyproject.toml" ]] || [[ ! -d "gatekit" ]]; then
    echo "Error: Must run from private repo root"
    exit 1
fi

# Create working copy
echo "Creating filtered copy..."
cd "$TEMP_DIR"
git clone --no-hardlinks "$PRIVATE_REPO_PATH" private-copy
cd private-copy

# Apply filtering
echo "Filtering repository content..."

# Remove sensitive directories entirely
rm -rf gatekit/tui/
rm -rf docs/todos/
rm -rf scripts/private/
find . -name "*.private" -delete
find . -name ".env*" -delete

# Create public README
cat > README.md << 'EOF'
# Gatekit

Open source MCP (Model Context Protocol) security gateway.

## Overview

Gatekit is a security-focused proxy that sits between MCP clients and servers,
providing comprehensive auditing, access control, and threat protection for 
AI tool interactions.

## Features

- **Security Policies**: Configurable rules for MCP tool access
- **Audit Logging**: Comprehensive logging of all MCP interactions  
- **Plugin Architecture**: Extensible security and monitoring capabilities
- **Performance**: High-throughput async proxy with minimal latency
- **Standards Compliant**: Full MCP protocol compatibility

## Installation

```bash
pip install gatekit
```

## Quick Start

```bash
# Install and configure
pip install gatekit
gatekit-gateway --config config.yaml

# For interactive configuration
pip install gatekit[tui]
gatekit
```

## License

Apache License 2.0 - see LICENSE for details.

## Contributing

We welcome contributions! See CONTRIBUTING.md for guidelines.

## Documentation

- [Configuration Guide](docs/)
- [Plugin Development](docs/plugins/)
- [Security Policies](docs/security/)
EOF

# Stage all changes
git add -A
git commit -m "Sync from private repository $(date -I)" || echo "No changes to commit"

# Push to public repository
echo "Pushing to public repository..."
git remote add public "$PUBLIC_REPO_URL"
git push public main --force

# Cleanup
cd /
rm -rf "$TEMP_DIR"

echo "Public repository sync complete!"
```

#### GitHub Actions Integration

**File: `.github/workflows/sync-public.yml`**
```yaml
name: Sync Public Repository

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      force_sync:
        description: 'Force sync even without tag'
        required: false
        default: 'false'

jobs:
  sync-public:
    runs-on: ubuntu-latest
    if: github.repository == 'user/gatekit-private'  # Only run on private repo
    
    steps:
    - name: Checkout private repository
      uses: actions/checkout@v4
      with:
        fetch-depth: 0  # Need full history for filtering
        token: ${{ secrets.PRIVATE_REPO_TOKEN }}
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Configure Git
      run: |
        git config --global user.name "GitHub Actions"
        git config --global user.email "actions@github.com"
    
    - name: Set up SSH key for public repo
      uses: webfactory/ssh-agent@v0.7.0
      with:
        ssh-private-key: ${{ secrets.PUBLIC_REPO_SSH_KEY }}
    
    - name: Sync to public repository
      run: |
        chmod +x scripts/sync-public-repo.sh
        ./scripts/sync-public-repo.sh
      env:
        PUBLIC_REPO_URL: git@github.com:user/gatekit.git
```

#### Public Repository Setup

**Initial Setup Steps**:

1. **Create public GitHub repository**:
   - Repository name: `gatekit`
   - Description: "Open source MCP security gateway"
   - License: Apache 2.0
   - Initialize with basic README

2. **Configure repository settings**:
   - Enable Issues for community feedback
   - Enable Discussions for community questions
   - Set up branch protection rules
   - Configure security alerts

3. **Add community files**:
   ```
   .github/
   ├── ISSUE_TEMPLATE/
   │   ├── bug_report.md
   │   ├── feature_request.md
   │   └── security_report.md
   ├── PULL_REQUEST_TEMPLATE.md
   ├── CONTRIBUTING.md
   ├── CODE_OF_CONDUCT.md
   └── SECURITY.md
   ```

### 5. Documentation Updates

**Objective**: Update all project documentation to reflect the new dual-license open core model, command structure changes, and distribution strategy.

**Context**: Following the TUI separation and licensing changes, all documentation needs to be updated to:
- Reflect new command structure (`gatekit` vs `gatekit-gateway`)
- Explain dual-license model clearly
- Update installation instructions
- Provide migration guidance for any existing users
- Ensure consistency across all documentation

#### Root README Update

**File**: `README.md`

```markdown
# Gatekit

A secure MCP (Model Context Protocol) gateway with visual configuration interface.

Gatekit provides comprehensive security, auditing, and access control for AI tool interactions by sitting between MCP clients and servers as a transparent proxy.

## Features

- **🔒 Security Policies**: Configurable rules for MCP tool access and data protection
- **📊 Comprehensive Auditing**: Detailed logging of all MCP interactions and security decisions
- **🔌 Plugin Architecture**: Extensible security and monitoring capabilities
- **⚡ High Performance**: Async-first architecture with minimal latency impact
- **🎨 Visual Configuration**: Intuitive TUI for policy and server management
- **📋 Standards Compliant**: Full MCP protocol compatibility

## Quick Start

### Installation

```bash
# Full installation (recommended)
pip install gatekit
```

### Usage

```bash
# Interactive configuration interface
gatekit

# Run as MCP security gateway
gatekit-gateway --config config.yaml
```

### MCP Client Configuration

Update your MCP client configuration to use Gatekit:

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

## Architecture

Gatekit consists of two main components:

- **Gateway functionality**: The security proxy, plugin system, and audit engine (Apache 2.0)
- **Configuration TUI**: Visual interface for configuration management (Proprietary freeware)

## Documentation

- [Installation Guide](docs/installation.md)
- [Configuration Reference](docs/configuration.md)
- [Security Policies](docs/security-policies.md)
- [Plugin Development](docs/plugins.md)
- [MCP Integration](docs/mcp-integration.md)

## License

- **Core functionality**: Apache License 2.0 (open source)
- **TUI interface**: Proprietary freeware (free to use, not for redistribution)

See [LICENSE](LICENSE) for core license and [LICENSE.TUI](LICENSE.TUI) for TUI license details.

## Contributing

We welcome contributions to the core functionality! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Support

- [Documentation](docs/)
- [GitHub Issues](https://github.com/user/gatekit/issues) (core functionality)
- [Discussions](https://github.com/user/gatekit/discussions) (questions and ideas)
```

#### Installation Documentation

**File**: `docs/installation.md`

```markdown
# Installation Guide

## System Requirements

- Python 3.11 or later
- 50MB disk space
- Terminal access (for TUI features)

## Installation Options

### Full Installation (Recommended)

Install Gatekit with both core gateway functionality and TUI:

```bash
pip install gatekit
```

This provides both commands:
- `gatekit` - Configuration interface
- `gatekit-gateway` - Security gateway

### Development Installation

For contributing to core functionality:

```bash
git clone https://github.com/user/gatekit.git
cd gatekit
pip install -e .[dev]
```

## Verification

Verify installation:

```bash
# Check commands are available
gatekit --help
gatekit-gateway --help

# Validate with example config
gatekit-gateway --config examples/basic.yaml --validate-only
```

## Troubleshooting

### Command Not Found

If commands aren't found after installation:

```bash
# Check pip installation location
pip show gatekit

# Ensure pip bin directory is in PATH
export PATH="$PATH:$(python -m site --user-base)/bin"
```

### TUI Not Working

If the TUI fails to start:

```bash
# Check terminal capabilities
echo $TERM

# Try simplified terminal
TERM=xterm gatekit
```

## Next Steps

- [Configuration Guide](configuration.md)
- [MCP Integration](mcp-integration.md)
- [Quick Start Examples](examples.md)
```

#### Command Reference Documentation

**File**: `docs/commands.md`

```markdown
# Command Reference

## gatekit

Launch the Gatekit configuration interface (TUI).

### Syntax

```bash
gatekit [CONFIG_FILE] [--verbose]
```

### Options

- `CONFIG_FILE`: Configuration file to open (optional positional argument)
- `--verbose, -v`: Enable debug logging
- `--help`: Show help message

### Examples

```bash
# Launch with default/last configuration
gatekit

# Open specific configuration
gatekit /etc/gatekit/production.yaml

# Debug mode
gatekit --verbose
```

## gatekit-gateway

Run Gatekit as an MCP security gateway.

### Syntax

```bash
gatekit-gateway --config CONFIG_FILE [--verbose] [--validate-only]
```

### Options

- `--config CONFIG_FILE`: Path to configuration file (required)
- `--verbose, -v`: Enable debug logging
- `--validate-only`: Validate configuration and exit
- `--help`: Show help message

### Examples

```bash
# Run with configuration
gatekit-gateway --config config.yaml

# Validate configuration
gatekit-gateway --config config.yaml --validate-only

# Debug mode
gatekit-gateway --config config.yaml --verbose
```

### Exit Codes

- `0`: Success
- `1`: Configuration error
- `2`: Runtime error
- `3`: Permission error

## Environment Variables

- `GATEKIT_LOG_LEVEL`: Override log level (DEBUG, INFO, WARNING, ERROR)
- `GATEKIT_CONFIG_DIR`: Default directory for configuration files
- `GATEKIT_NO_TUI`: Set to disable TUI functionality
```

#### MCP Integration Documentation

**File**: `docs/mcp-integration.md`

```markdown
# MCP Client Integration

## Overview

Gatekit integrates with MCP clients by acting as a transparent security proxy between the client and upstream MCP servers.

## Configuration

### Claude Desktop

Update your Claude Desktop configuration file:

**Location**: `~/.claude/claude_desktop_config.json`

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

### Generic MCP Client

For other MCP clients, replace the server command:

```json
{
  "servers": {
    "protected-server": {
      "command": "gatekit-gateway",
      "args": ["--config", "/path/to/config.yaml"],
      "env": {
        "GATEKIT_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Migration Guide

### Command Structure Changes

#### Development Versions (Pre-v0.1.0)

If you were using development versions of Gatekit, update your MCP client configurations:

**Old Command Structure**:
```json
{
  "command": "gatekit",
  "args": ["proxy", "--config", "config.yaml"]
}
```

**New Command Structure**:  
```json
{
  "command": "gatekit-gateway",
  "args": ["--config", "config.yaml"]
}
```

#### Migration Steps

1. **Update MCP client configuration**:
   - Replace `gatekit proxy` with `gatekit-gateway`
   - Remove the `proxy` subcommand

2. **Test configuration**:
   ```bash
   gatekit-gateway --config config.yaml --validate-only
   ```

3. **Restart MCP client** to pick up new configuration

## Troubleshooting

### Gateway Not Starting

Check that Gatekit is installed and configuration is valid:

```bash
# Verify installation
gatekit-gateway --help

# Test configuration
gatekit-gateway --config config.yaml --validate-only
```

### Connection Issues

Check logs for connection problems:

```bash
# Run with verbose logging
gatekit-gateway --config config.yaml --verbose
```

## Best Practices

- **Configuration Validation**: Always validate configurations before deployment
- **Logging**: Enable appropriate logging levels for monitoring
- **Security Policies**: Start with restrictive policies and gradually open access
- **Performance Monitoring**: Monitor proxy latency in production
```

#### License Documentation

**File**: `docs/licensing.md`

```markdown
# Licensing Information

## Overview

Gatekit uses a dual-license model to balance open source transparency with business sustainability.

## Core Functionality - Apache 2.0

The core security gateway functionality is licensed under Apache License 2.0:

- **What's included**: Proxy engine, security plugins, audit system, configuration management
- **License**: Apache 2.0 (permissive open source)
- **Source code**: Available on GitHub
- **Commercial use**: Permitted
- **Modifications**: Permitted
- **Distribution**: Permitted with attribution

### Files Covered

- All gateway code in `gatekit/` (except TUI)
- Core proxy and security functionality
- Plugin system and built-in plugins
- Configuration management
- Documentation and examples

## TUI Interface - Proprietary Freeware

The Terminal User Interface is proprietary freeware:

- **What's included**: Visual configuration editor, server management interface
- **License**: Proprietary freeware
- **Source code**: Not available
- **Personal use**: Free
- **Commercial use**: Free
- **Redistribution**: Not permitted
- **Modifications**: Not possible (binary distribution)

### Terms Summary

You may:
- ✅ Use the TUI free of charge
- ✅ Use it in commercial environments
- ✅ Install it on multiple systems

You may NOT:
- ❌ Redistribute the TUI as part of other products
- ❌ Reverse engineer or decompile the TUI
- ❌ Rebrand or white-label the TUI
- ❌ Include the TUI in competitive products

## Contributing

### Core Functionality

Contributions to core functionality are welcome under Apache 2.0:

- Submit pull requests to [GitHub repository](https://github.com/user/gatekit)
- All contributions licensed under Apache 2.0
- See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines

### TUI Improvements

TUI improvements are not open for external contribution since the TUI is proprietary. However:

- Feature requests are welcome via GitHub Issues
- Bug reports help improve the TUI for everyone
- Feedback and suggestions are always appreciated

## Legal

### Full License Texts

- [Apache 2.0 License](../LICENSE) - Core functionality
- [Proprietary License](../LICENSE.TUI) - TUI interface

### Questions

For licensing questions or commercial inquiries, contact [email].

This dual-license model ensures Gatekit remains trustworthy and auditable while maintaining business sustainability.
```

### 6. First Release Preparation

**Objective**: Essential requirements for the first public release (v0.1.0) of Gatekit, focusing only on what's absolutely necessary for launch.

**Context**: Since package names are already reserved on PyPI at v0.1.0, the first real release will be v0.1.0.

#### PyPI Setup and Publishing

**Author Information and Metadata**:
- [ ] **Author Information**: Decide on author name and email for package metadata
- [ ] **Project URLs**: Homepage, repository, documentation URLs
- [ ] **API Tokens**: Set up PyPI API tokens for automated publishing
- [ ] **Trusted Publishing**: Configure GitHub Actions → PyPI trusted publishing

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

#### Legal Compliance Files

**Files needed:**

1. **NOTICE** (Apache 2.0 requirement) ✅ - Already exists
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

#### Build Configuration

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

#### Version Synchronization

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
        "gatekit/_version.py",
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

## Notes

- All tasks in this document are "release engineering" and don't block current TUI development
- Can be implemented incrementally or all at once before launch
- Focus on getting TUI functionality complete first, then return to these tasks