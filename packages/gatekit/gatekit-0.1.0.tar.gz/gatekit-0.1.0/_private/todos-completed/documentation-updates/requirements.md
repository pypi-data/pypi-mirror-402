# Documentation Updates Requirements

## Overview

Update all project documentation to reflect the new dual-license open core model, command structure changes, and distribution strategy outlined in ADR-019.

## Context

Following the TUI separation and licensing changes, all documentation needs to be updated to:
- Reflect new command structure (`gatekit` vs `gatekit-gateway`)
- Explain dual-license model clearly
- Update installation instructions
- Provide migration guidance for any existing users
- Ensure consistency across all documentation

## Scope

### Documentation to Update

**Core Documentation**:
- Root `README.md`
- Single comprehensive README.md for the unified package
- Installation guides
- Configuration documentation
- MCP client integration examples

**Developer Documentation**:
- Contributing guidelines
- Development setup instructions
- Build and release processes
- Testing documentation

**User Documentation**:
- Command line reference
- Configuration reference
- Security policy examples
- Troubleshooting guides

**Project Documentation**:
- License information and explanation
- Architecture overview
- Plugin development guides

## Detailed Requirements

### 1. Root README Update

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

# Core only (for servers/automation)
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

### 2. Package-Specific READMEs

**This section is obsolete** - flat structure uses single README.md

**Original content for reference:**

```markdown
# Gatekit Core

Core MCP security gateway functionality for Gatekit.

This package provides the essential proxy, security, and auditing capabilities that make up the Gatekit Security Gateway. It can be used standalone for server deployments or as part of the full Gatekit package with TUI.

## Features

- MCP protocol proxy with security filtering
- Plugin-based security and auditing architecture
- Comprehensive audit logging
- Configuration management
- High-performance async request handling

## Installation

```bash
# Standalone core
pip install gatekit

# Full package with TUI
pip install gatekit
```

## Usage

```bash
# Run security gateway
gatekit-gateway --config config.yaml

# Validate configuration
gatekit-gateway --config config.yaml --validate-only
```

## Configuration

See the [configuration documentation](../docs/configuration.md) for detailed setup instructions.

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
```

**This section is obsolete** - flat structure uses single README.md

**Original content for reference:**

```markdown
# Gatekit TUI

Terminal User Interface for Gatekit Security Gateway configuration.

This package provides an intuitive visual interface for configuring Gatekit security policies, managing MCP servers, and monitoring gateway status.

## Features

- Visual configuration editor
- MCP server management
- Security policy configuration
- Real-time status monitoring
- Configuration validation

## Installation

```bash
# Full Gatekit package (recommended)
pip install gatekit

# TUI only (advanced users)
# TUI is included in main package
pip install gatekit
```

## Usage

```bash
# Launch configuration interface
gatekit

# Open with specific configuration
gatekit --config config.yaml
```

## Requirements

- Python 3.11+
- Terminal with color support
- Gatekit core functionality

## License

Proprietary freeware - see [LICENSE.PROPRIETARY](LICENSE.PROPRIETARY) for details.
```

### 3. Installation Documentation

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

### Core Only Installation

For server deployments that don't need the visual interface:

```bash
pip install gatekit
```

This provides only:
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

### Import Errors

If you see import errors:

```bash
# Check installed packages
pip list | grep gatekit

# Reinstall if needed
pip uninstall gatekit
pip install gatekit
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

### 4. Command Reference Documentation

**File**: `docs/commands.md`

```markdown
# Command Reference

## gatekit

Launch the Gatekit configuration interface (TUI).

### Syntax

```bash
gatekit [--config CONFIG_FILE] [--verbose]
```

### Options

- `--config CONFIG_FILE`: Open TUI with specific configuration file
- `--verbose, -v`: Enable debug logging
- `--help`: Show help message

### Examples

```bash
# Launch with default/last configuration
gatekit

# Open specific configuration
gatekit --config /etc/gatekit/production.yaml

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

## Configuration File Format

See [Configuration Reference](configuration.md) for detailed configuration options.

## Environment Variables

- `GATEKIT_LOG_LEVEL`: Override log level (DEBUG, INFO, WARNING, ERROR)
- `GATEKIT_CONFIG_DIR`: Default directory for configuration files
- `GATEKIT_NO_TUI`: Set to disable TUI functionality
```

### 5. MCP Integration Documentation

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

## Gatekit Configuration

Create a Gatekit configuration file that specifies the upstream server:

```yaml
# gatekit.yaml
proxy:
  upstream:
    command: "npx"
    args: ["@modelcontextprotocol/server-filesystem", "/safe/path"]
  
security:
  plugins:
    - name: "path_security"
      config:
        allowed_paths:
          - "/safe/path/**"
        denied_paths:
          - "/safe/path/secrets/**"

auditing:
  plugins:
    - name: "json_logger"
      config:
        file: "/var/log/gatekit/audit.jsonl"
```

## Command Migration

If you're updating from development versions:

### Old Configuration (Pre-Release)
```json
{
  "command": "gatekit",
  "args": ["proxy", "--config", "config.yaml"]
}
```

### New Configuration (Current)
```json
{
  "command": "gatekit-gateway", 
  "args": ["--config", "config.yaml"]
}
```

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

### Performance Issues

Monitor proxy performance:

```bash
# Check audit logs for timing information
tail -f /var/log/gatekit/audit.jsonl | jq '.duration_ms'
```

## Best Practices

- **Configuration Validation**: Always validate configurations before deployment
- **Logging**: Enable appropriate logging levels for monitoring
- **Security Policies**: Start with restrictive policies and gradually open access
- **Performance Monitoring**: Monitor proxy latency in production
```

### 6. Migration Guide

**File**: `docs/migration.md`

```markdown
# Migration Guide

## Command Structure Changes

### Development Versions (Pre-v0.1.0)

If you were using development versions of Gatekit, update your MCP client configurations:

#### Old Command Structure
```json
{
  "command": "gatekit",
  "args": ["proxy", "--config", "config.yaml"]
}
```

#### New Command Structure  
```json
{
  "command": "gatekit-gateway",
  "args": ["--config", "config.yaml"]
}
```

### Migration Steps

1. **Update MCP client configuration**:
   - Replace `gatekit proxy` with `gatekit-gateway`
   - Remove the `proxy` subcommand

2. **Test configuration**:
   ```bash
   gatekit-gateway --config config.yaml --validate-only
   ```

3. **Restart MCP client** to pick up new configuration

## Package Changes

### If Installing from Source

The repository structure has changed:

#### Old Structure
```
gatekit/
├── gatekit/
│   ├── proxy/
│   ├── config/
│   └── tui/
```

#### New Structure
```
gatekit/
├── gatekit/  # Single package with both gateway and TUI
└── pyproject.toml
```

### Installation Updates

No changes needed for pip installations:

```bash
# This still works the same
pip install gatekit
```

## Configuration File Changes

No configuration file changes are required. All existing Gatekit configuration files remain compatible.

## Troubleshooting Migration

### Command Not Found

If `gatekit-gateway` command is not found:

```bash
# Check installation
pip show gatekit

# Reinstall if needed
pip install --upgrade gatekit
```

### Old Commands

If you see deprecation warnings about old commands, update your configuration as described above.

### Import Errors

If you see Python import errors after updating:

```bash
# Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete

# Reinstall
pip uninstall gatekit
pip install gatekit
```
```

### 7. License Documentation

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

## Why This Model?

### Open Core Benefits

- **Trust**: Security-critical code is auditable and transparent
- **Community**: Contributions to core functionality are welcome
- **Flexibility**: Apache 2.0 allows maximum reuse and integration
- **Innovation**: Protects user experience innovations while keeping core open

### Business Sustainability

- **Value Protection**: Prevents wholesale copying of complete solution
- **Competitive Advantage**: Maintains differentiation through user experience
- **Revenue Opportunity**: Creates foundation for future commercial offerings
- **Community Balance**: Gives back to community while protecting business interests

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

### Compliance

Using Gatekit in compliance with both licenses:

1. **Include attribution** for Apache 2.0 core components
2. **Respect restrictions** on TUI redistribution
3. **Follow terms** of both licenses in your usage

This dual-license model ensures Gatekit remains trustworthy and auditable while maintaining business sustainability.
```

## Validation Steps

After updating documentation:

1. **Review all links**: Ensure internal and external links work
2. **Test examples**: Verify all code examples are accurate
3. **Check consistency**: Ensure terminology is consistent across docs
4. **Validate formatting**: Check markdown rendering and formatting
5. **User testing**: Have someone unfamiliar try following the docs

## Success Criteria

- [ ] All documentation reflects new command structure
- [ ] Dual-license model is clearly explained
- [ ] Installation instructions are accurate and complete
- [ ] Migration guidance is provided for any existing users
- [ ] Examples and code snippets are updated and tested
- [ ] Licensing information is clear and comprehensive
- [ ] Documentation is professional and user-friendly

## Dependencies

- License header updates should be completed first
- Package structure changes from Phase 2 should be implemented
- Final licensing decisions should be made

## Timeline

- **Week 1**: Update core documentation (README, installation, commands)
- **Week 2**: Update user documentation (configuration, integration, examples)
- **Week 3**: Create migration guides and licensing documentation
- **Week 4**: Review, test, and polish all documentation

## Maintenance

Documentation should be updated whenever:
- Command structure changes
- Configuration options change
- New features are added
- License terms change
- Installation procedures change