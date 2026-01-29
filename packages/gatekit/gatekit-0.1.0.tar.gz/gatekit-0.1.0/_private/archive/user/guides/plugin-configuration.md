# Plugin Configuration Guide

*[Home](../../../README.md) → [User Documentation](../../README.md) → [Guides](../README.md) → Plugin Configuration Guide*

This comprehensive guide explains how to configure Gatekit's security and auditing plugins using the upstream-scoped configuration system. You'll learn the different configuration patterns, plugin scope categories, and best practices for real-world deployments.

## Table of Contents

1. [Understanding Plugin Scopes](#understanding-plugin-scopes)
2. [Configuration Patterns](#configuration-patterns)
3. [Real-World Examples](#real-world-examples)
4. [Common Use Cases](#common-use-cases)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

## Understanding Plugin Scopes

Gatekit categorizes plugins based on where they can be meaningfully configured. Understanding these categories is crucial for proper configuration.

### Global Scope Plugins

**What they are**: Server-agnostic plugins that can apply identical configuration to any MCP server.

**Available plugins**:
- **PII Filter** (`pii`) - Detects and handles personally identifiable information
- **Secrets Filter** (`secrets`) - Detects and handles API keys, tokens, and credentials  
- **Prompt Injection Defense** (`prompt_injection`) - Protects against prompt injection attacks
- **All auditing plugins** - JSON, CSV, line format, debug, etc.

**Key characteristic**: The same configuration works regardless of what MCP server you're connecting to.

**Example**: A PII filter with `action: "redact"` works the same whether you're connecting to a filesystem server, database server, or GitHub API server.

### Server-Aware Scope Plugins

**What they are**: Universal plugins that work with any server but require server-specific configuration.

**Available plugins**:
- **Tool Allowlist** (`tool_allowlist`) - Controls which tools are allowed

**Key characteristic**: The plugin concept is universal, but the configuration must be tailored to each server's available tools.

**Example**: Tool allowlist needs different tool names for different servers:
- Filesystem server: `["read_file", "write_file", "list_directory"]`
- Database server: `["read_query", "list_tables", "describe_table"]`
- GitHub server: `["create_issue", "get_repository", "search_code"]`

### Server-Specific Scope Plugins

**What they are**: Plugins designed for specific MCP server implementations.

**Available plugins**:
- **Filesystem Server Security** (`filesystem_server`) - Path-based access control for @modelcontextprotocol/server-filesystem

**Key characteristic**: Only works with specific server implementations. Attempting to use with incompatible servers will fail.

**Example**: Filesystem Server Security plugin only understands filesystem operations and path patterns - it cannot be used with a database or API server.

## Plugin Configuration Parameters

### Common Parameters

All plugins support these standard parameters:

- **`policy`** (string, required): The plugin identifier
- **`enabled`** (boolean, optional): Whether the plugin is active (default: true)
- **`config`** (object, optional): Plugin-specific configuration

### Security Plugin Parameters

Security plugins support additional parameters:

- **`priority`** (integer, 0-100, optional): Execution order - lower values execute first (default: 50)
- **`critical`** (boolean, optional): Whether failures should halt processing (default: true)

### Auditing Plugin Parameters

Auditing plugins support:

- **`critical`** (boolean, optional): Whether audit failures should halt operations (default: false)
  - When `true`: Initialization failures prevent startup, runtime failures raise errors
  - When `false`: Failures are logged but processing continues
  - See [Critical Auditing Guide](./critical-auditing.md) for detailed information

**Note**: Auditing plugins do not support `priority` - they execute in definition order.

## Configuration Patterns

Gatekit supports three distinct configuration patterns. Choose the pattern that best fits your security requirements and deployment complexity.

### Pattern 1: Global-Only Configuration

**When to use**: 
- Simple deployments with consistent security policies
- Development environments
- When all servers need identical protection

**Supported plugins**: Only global scope plugins (PII Filter, Secrets Filter, Prompt Injection Defense, all auditing plugins)

**Example**:
```yaml
# Global-only configuration - same security for all servers
plugins:
  security:
    _global:
      - policy: "pii"
        enabled: true
        config:
          action: "redact"
          pii_types:
            email: {"enabled": true}
            phone: {"enabled": true}
            credit_card: {"enabled": true}
      
      - policy: "secrets"
        enabled: true
        config:
          action: "block"
          secret_types:
            aws_access_keys: {"enabled": true}
            github_tokens: {"enabled": true}
            google_api_keys: {"enabled": true}

  auditing:
    _global:
      - policy: "json_auditing"
        enabled: true
        config:
          output_file: "logs/global-audit.jsonl"
          mode: "all_events"
```

**Result**: Every server gets identical PII redaction, secrets blocking, and JSON audit logging.

### Pattern 2: Server-Specific Only Configuration

**When to use**:
- Servers need completely different security policies
- Maximum granular control
- Complex enterprise environments with varying security requirements

**Supported plugins**: All plugin types (global, server-aware, server-specific)

**Example**:
```yaml
# Server-specific only - each server has independent configuration
plugins:
  security:
    # Production database - maximum security
    production_db:
      - policy: "pii"
        enabled: true
        config:
          action: "block"          # Strict: block any PII
          pii_types:
            email: {"enabled": true}
            phone: {"enabled": true}
            credit_card: {"enabled": true}
            national_id: {"enabled": true}
      
      - policy: "secrets"
        enabled: true
        config:
          action: "block"
          secret_types:
            aws_access_keys: {"enabled": true}
            github_tokens: {"enabled": true}
            jwt_tokens: {"enabled": true}
      
      - policy: "tool_allowlist"
        enabled: true
        config:
          mode: "allowlist"
          tools: ["read_query", "list_tables"]  # Read-only access
    
    # Development filesystem - permissive with auditing
    dev_filesystem:
      - policy: "pii"
        enabled: true
        config:
          action: "audit_only"     # Permissive: log but allow
          pii_types:
            email: {"enabled": true}
      
      - policy: "tool_allowlist"
        enabled: true
        config:
          mode: "allowlist"
          tools: ["read_file", "write_file", "list_directory", "create_directory"]
      
      - policy: "filesystem_server"
        enabled: true
        config:
          read: ["**/*"]           # Read everything
          write: ["temp/**/*", "docs/**/*"]  # Restrict writes

  auditing:
    production_db:
      - policy: "json_auditing"
        enabled: true
        config:
          output_file: "logs/production-audit.jsonl"
          mode: "all_events"
          critical: true           # Audit failures block operations
    
    dev_filesystem:
      - policy: "line_auditing"
        enabled: true
        config:
          output_file: "logs/dev-audit.log"
          mode: "security_only"
          critical: false          # Graceful audit failures
```

**Result**: Production database gets strict security with mandatory auditing. Development filesystem gets permissive security with optional auditing.

### Pattern 3: Mixed Global + Server Override Configuration

**When to use**:
- Most servers use standard policies with few exceptions
- Balanced approach between simplicity and flexibility
- Common enterprise pattern

**Supported plugins**: All plugin types, with strategic use of global defaults and targeted overrides

**Example**:
```yaml
# Mixed configuration - global defaults with targeted overrides
plugins:
  security:
    # Global defaults - apply to all servers unless overridden
    _global:
      - policy: "pii"
        enabled: true
        config:
          action: "redact"         # Standard: redact PII
          pii_types:
            email: {"enabled": true}
            phone: {"enabled": true}
            credit_card: {"enabled": true}
      
      - policy: "secrets"
        enabled: true
        config:
          action: "redact"         # Standard: redact secrets
          secret_types:
            aws_access_keys: {"enabled": true}
            github_tokens: {"enabled": true}

    # Production server - override for stricter security
    production_server:
      - policy: "pii"
        enabled: true
        config:
          action: "block"          # Override: stricter than global
          pii_types:
            email: {"enabled": true}
            phone: {"enabled": true}
            credit_card: {"enabled": true}
            national_id: {"enabled": true}  # Additional PII type
      
      - policy: "secrets"
        enabled: true
        config:
          action: "block"          # Override: stricter than global
          secret_types:
            aws_access_keys: {"enabled": true}
            github_tokens: {"enabled": true}
            jwt_tokens: {"enabled": true}    # Additional secret type

    # Development server - add tool restrictions
    dev_server:
      # Inherits global PII and secrets policies (redaction)
      - policy: "tool_allowlist"   # Additional plugin: not in global
        enabled: true
        config:
          mode: "allowlist"
          tools: ["read_file", "write_file", "list_directory"]

    # Public demo server - disable PII protection
    demo_server:
      - policy: "pii"
        enabled: false             # Override: disable global PII policy
      # Inherits global secrets policy (redaction)

  auditing:
    _global:
      - policy: "json_auditing"
        enabled: true
        config:
          output_file: "logs/audit.jsonl"
          mode: "all_events"
```

**Resolution Results**:

**production_server gets**:
- PII Filter: `action: "block"` (overridden from global)
- Secrets Filter: `action: "block"` (overridden from global)  
- JSON Auditing: `output_file: "logs/audit.jsonl"` (from global)

**dev_server gets**:
- PII Filter: `action: "redact"` (from global)
- Secrets Filter: `action: "redact"` (from global)
- Tool Allowlist: `tools: [...]` (added, not in global)
- JSON Auditing: `output_file: "logs/audit.jsonl"` (from global)

**demo_server gets**:
- PII Filter: `enabled: false` (overridden from global)
- Secrets Filter: `action: "redact"` (from global)
- JSON Auditing: `output_file: "logs/audit.jsonl"` (from global)

## Real-World Examples

### Example 1: Multi-Environment Development Setup

**Scenario**: Development team with local filesystem access and production database access requiring different security levels.

```yaml
proxy:
  transport: "stdio"
  upstreams:
    - name: "local_files"
      command: "npx @modelcontextprotocol/server-filesystem ~/projects"
    - name: "prod_database"
      command: "npx mcp-server-sqlite ~/data/production.db"
    - name: "staging_api"
      command: "python -m company.staging_api_server"

plugins:
  security:
    _global:
      # Standard PII protection across all environments
      - policy: "pii"
        enabled: true
        config:
          action: "redact"
          pii_types:
            email: {"enabled": true}
            phone: {"enabled": true}

    # Local development - permissive with path restrictions
    local_files:
      - policy: "filesystem_server"
        enabled: true
        config:
          read: ["**/*", "!**/.env*", "!**/secrets/*"]
          write: ["src/**/*", "docs/**/*", "temp/**/*"]
      
      - policy: "tool_allowlist"
        enabled: true
        config:
          mode: "allowlist"
          tools: ["read_file", "write_file", "list_directory", "create_directory", "search_files"]

    # Production database - strict security
    prod_database:
      - policy: "pii"
        enabled: true
        config:
          action: "block"          # Override: block PII in production
          pii_types:
            email: {"enabled": true}
            phone: {"enabled": true}
            credit_card: {"enabled": true}
            national_id: {"enabled": true}
      
      - policy: "secrets"
        enabled: true
        config:
          action: "block"
          secret_types:
            aws_access_keys: {"enabled": true}
            database_urls: {"enabled": true}
      
      - policy: "tool_allowlist"
        enabled: true
        config:
          mode: "allowlist"
          tools: ["read_query", "list_tables"]  # Read-only

    # Staging API - moderate security
    staging_api:
      - policy: "tool_allowlist"
        enabled: true
        config:
          mode: "blocklist"
          tools: ["delete_user", "reset_database", "admin_override"]

  auditing:
    _global:
      - policy: "json_auditing"
        enabled: true
        config:
          output_file: "logs/dev-audit.jsonl"
          mode: "security_only"    # Focus on security events
          
    prod_database:
      - policy: "json_auditing"
        enabled: true
        config:
          output_file: "logs/production-audit.jsonl"
          mode: "all_events"       # Override: comprehensive logging
          critical: true           # Override: mandatory auditing
```

### Example 2: Enterprise Compliance Setup

**Scenario**: Enterprise environment with strict compliance requirements, multiple data sources, and regulatory auditing needs.

```yaml
proxy:
  transport: "stdio"
  upstreams:
    - name: "customer_database"
      command: "npx mcp-server-sqlite /data/customers.db"
    - name: "financial_documents"
      command: "npx @modelcontextprotocol/server-filesystem /secure/financial"
    - name: "external_api"
      command: "python -m company.external_integration"

plugins:
  security:
    _global:
      # Enterprise-wide PII protection
      - policy: "pii"
        enabled: true
        config:
          action: "block"          # Strict: block all PII by default
          pii_types:
            email: {"enabled": true}
            phone: {"enabled": true}
            credit_card: {"enabled": true}
            national_id: {"enabled": true}
            ip_address: {"enabled": true}
      
      # Enterprise-wide secrets protection
      - policy: "secrets"
        enabled: true
        config:
          action: "block"
          secret_types:
            aws_access_keys: {"enabled": true}
            github_tokens: {"enabled": true}
            google_api_keys: {"enabled": true}
            jwt_tokens: {"enabled": true}
          entropy_detection:
            enabled: true
            min_entropy: 5.5

    # Customer database - maximum data protection
    customer_database:
      - policy: "tool_allowlist"
        enabled: true
        priority: 5              # Execute before other plugins
        config:
          mode: "allowlist"
          tools: ["read_query"]  # Read-only access
          block_message: "Database write operations not permitted"

    # Financial documents - path-based access control
    financial_documents:
      - policy: "filesystem_server"
        enabled: true
        config:
          read: [
            "public/**/*",         # Public documents
            "reports/quarterly/*", # Quarterly reports
            "!reports/quarterly/drafts/*"  # Exclude drafts
          ]
          write: [
            "temp/**/*",           # Temporary files only
            "archive/**/*"         # Archive access
          ]
      
      - policy: "tool_allowlist"
        enabled: true
        config:
          mode: "allowlist"
          tools: ["read_file", "list_directory", "search_files", "get_file_info"]

    # External API - additional prompt injection protection
    external_api:
      - policy: "prompt_injection"
        enabled: true
        config:
          action: "block"
          detection_patterns:
            delimiters: {"enabled": true}
            role_manipulation: {"enabled": true}
            context_breaking: {"enabled": true}

  auditing:
    _global:
      # Compliance-grade JSON auditing
      - policy: "json_auditing"
        enabled: true
        config:
          output_file: "logs/compliance-audit.jsonl"
          mode: "all_events"
          include_request_body: true
          critical: true           # Audit failures block operations
      
      # CEF format for SIEM integration
      - policy: "cef_auditing"
        enabled: true
        config:
          output_file: "logs/siem-audit.cef"
          cef_config:
            device_vendor: "Company"
            device_product: "Gatekit-MCP-Proxy"
            device_version: "1.0.0"
          critical: true
      
      # CSV format for compliance reporting
      - policy: "csv_auditing"
        enabled: true
        config:
          output_file: "logs/compliance-report.csv"
          csv_config:
            include_compliance_columns: true
            audit_trail_format: "SOX_404"
            regulatory_schema: "financial_services"
          critical: true
```

### Example 3: Development Team Onboarding

**Scenario**: Onboarding new developers with progressive access levels based on experience and trust.

```yaml
proxy:
  transport: "stdio"
  upstreams:
    - name: "sandbox"
      command: "npx @modelcontextprotocol/server-filesystem ~/sandbox"
    - name: "shared_docs"
      command: "npx @modelcontextprotocol/server-filesystem ~/team/docs"
    - name: "staging_db"
      command: "npx mcp-server-sqlite ~/team/staging.db"

plugins:
  security:
    # New developers - sandbox access only
    sandbox:
      - policy: "pii"
        enabled: true
        config:
          action: "audit_only"    # Permissive: learn from mistakes
          pii_types:
            email: {"enabled": true}
            phone: {"enabled": true}
      
      - policy: "filesystem_server"
        enabled: true
        config:
          read: ["**/*"]
          write: ["**/*"]         # Full access to sandbox
      
      - policy: "tool_allowlist"
        enabled: true
        config:
          mode: "allowlist"
          tools: [
            "read_file", "write_file", "list_directory", 
            "create_directory", "search_files"
          ]

    # Experienced developers - documentation access
    shared_docs:
      - policy: "pii"
        enabled: true
        config:
          action: "redact"        # Moderate: redact PII
          pii_types:
            email: {"enabled": true}
            phone: {"enabled": true}
      
      - policy: "filesystem_server"
        enabled: true
        config:
          read: ["**/*", "!**/confidential/*"]  # Most docs, no confidential
          write: ["public/**/*", "drafts/**/*"] # Limited write access

    # Senior developers - staging database access  
    staging_db:
      - policy: "pii"
        enabled: true
        config:
          action: "block"         # Strict: block PII
          pii_types:
            email: {"enabled": true}
            phone: {"enabled": true}
            credit_card: {"enabled": true}
      
      - policy: "tool_allowlist"
        enabled: true
        config:
          mode: "allowlist"
          tools: ["read_query", "list_tables", "describe_table"]  # Read-only

  auditing:
    _global:
      - policy: "line_auditing"
        enabled: true
        config:
          output_file: "logs/team-activity.log"
          mode: "security_only"
          critical: false
```

## Common Use Cases

### Use Case 1: PII Protection with Regional Compliance

Different regions have different PII regulations (GDPR, CCPA, etc.). Configure region-specific PII handling:

```yaml
plugins:
  security:
    eu_customer_data:
      - policy: "pii"
        enabled: true
        config:
          action: "block"         # GDPR: strict data protection
          pii_types:
            email: {"enabled": true}
            phone: {"enabled": true}
            ip_address: {"enabled": true}  # IP addresses are PII under GDPR
            national_id: {"enabled": true}
    
    us_customer_data:
      - policy: "pii"
        enabled: true
        config:
          action: "redact"        # CCPA: allow with redaction
          pii_types:
            email: {"enabled": true}
            phone: {"enabled": true}
            credit_card: {"enabled": true}
            national_id: {"enabled": true, "formats": ["us"]}  # US SSN only
```

### Use Case 2: Progressive Security Hardening

Start with permissive policies and gradually increase security:

```yaml
plugins:
  security:
    _global:
      # Phase 1: Audit-only mode to understand data patterns
      - policy: "pii"
        enabled: true
        config:
          action: "audit_only"   # Learn what PII exists
      
      - policy: "secrets"
        enabled: true
        config:
          action: "audit_only"   # Learn what secrets exist

    # Phase 2: Enable redaction on non-critical servers
    development_server:
      - policy: "pii"
        enabled: true
        config:
          action: "redact"       # Override: start redacting
      
      - policy: "secrets"
        enabled: true
        config:
          action: "redact"       # Override: start redacting

    # Phase 3: Full blocking on production (add this configuration later)
    # production_server:
    #   - policy: "pii"
    #     enabled: true
    #     config:
    #       action: "block"      # Future: full blocking
```

### Use Case 3: Tool Access Management by Role

Control tool access based on user roles or server purposes:

```yaml
plugins:
  security:
    # Read-only analyst access
    analytics_db:
      - policy: "tool_allowlist"
        enabled: true
        config:
          mode: "allowlist"
          tools: ["read_query", "list_tables", "describe_table"]

    # Developer filesystem access
    dev_files:
      - policy: "tool_allowlist"
        enabled: true
        config:
          mode: "allowlist"
          tools: [
            "read_file", "write_file", "list_directory", 
            "create_directory", "search_files"
          ]
      
      - policy: "filesystem_server"
        enabled: true
        config:
          read: ["src/**/*", "docs/**/*", "tests/**/*"]
          write: ["src/**/*", "tests/**/*", "temp/**/*"]

    # Admin server access
    admin_server:
      - policy: "tool_allowlist"
        enabled: true
        config:
          mode: "blocklist"
          tools: ["format_disk", "delete_database", "reset_system"]
```

### Use Case 4: Comprehensive Audit Trail Setup

Create multiple audit formats for different purposes:

```yaml
plugins:
  auditing:
    _global:
      # Human-readable logs for developers
      - policy: "line_auditing"
        enabled: true
        config:
          output_file: "logs/human-readable.log"
          mode: "security_only"
          critical: false

      # Machine-readable logs for automated analysis
      - policy: "json_auditing"
        enabled: true
        config:
          output_file: "logs/machine-readable.jsonl"
          mode: "all_events"
          include_request_body: true
          critical: false

      # Compliance logs for auditors
      - policy: "csv_auditing"
        enabled: true
        config:
          output_file: "logs/compliance.csv"
          csv_config:
            include_compliance_columns: true
            audit_trail_format: "standard"
          critical: true        # Compliance auditing must not fail

      # SIEM integration
      - policy: "cef_auditing"
        enabled: true
        config:
          output_file: "logs/siem-feed.cef"
          cef_config:
            device_vendor: "YourCompany"
            device_product: "Gatekit"
          critical: false
```

## Best Practices

### 1. Start Simple, Scale Complex

**Recommendation**: Begin with global-only configuration, then add server-specific overrides as needed.

```yaml
# Phase 1: Start simple
plugins:
  security:
    _global:
      - policy: "pii"
        enabled: true
        config:
          action: "audit_only"  # Learn first

# Phase 2: Add targeted improvements  
plugins:
  security:
    _global:
      - policy: "pii"
        enabled: true
        config:
          action: "redact"      # Improve security

    production_server:
      - policy: "pii"
        enabled: true
        config:
          action: "block"       # Override: stricter for production
```

### 2. Use Descriptive Server Names

**Good**:
```yaml
upstreams:
  - name: "customer_database_prod"
  - name: "financial_docs_secure" 
  - name: "analytics_read_only"

plugins:
  security:
    customer_database_prod:  # Clear what this server does
      - policy: "pii"
        config: {action: "block"}
```

**Avoid**:
```yaml
upstreams:
  - name: "server1"
  - name: "db"
  - name: "api"
```

### 3. Layer Security Controls

**Recommendation**: Use multiple complementary plugins rather than relying on a single security control.

```yaml
plugins:
  security:
    sensitive_server:
      # Layer 1: Tool access control (what can be done)
      - policy: "tool_allowlist"
        priority: 10           # Execute first
        config:
          mode: "allowlist"
          tools: ["read_file", "list_directory"]

      # Layer 2: Path access control (where it can be done)  
      - policy: "filesystem_server"
        priority: 20
        config:
          read: ["public/**/*", "docs/**/*"]

      # Layer 3: Content filtering (what data can be accessed)
      - policy: "pii"
        priority: 30
        config:
          action: "block"
```

### 4. Configure Appropriate Audit Levels

**Development**: Minimal auditing for performance
```yaml
auditing:
  _global:
    - policy: "line_auditing"
      config:
        mode: "security_only"   # Only log security events
        critical: false         # Don't break on audit failures
```

**Production**: Comprehensive auditing for compliance
```yaml
auditing:
  _global:
    - policy: "json_auditing"
      config:
        mode: "all_events"      # Log everything
        critical: true          # Audit failures block operations
```

### 5. Use Plugin Priorities Strategically

**Recommendation**: Use priority to ensure security plugins execute in the correct order.

```yaml
plugins:
  security:
    server:
      # Execute tool allowlist first to block unwanted tools entirely
      - policy: "tool_allowlist"
        priority: 10            # Highest priority
        config:
          mode: "allowlist"
          tools: ["read_file"]

      # Then check paths for allowed tools
      - policy: "filesystem_server"  
        priority: 20
        config:
          read: ["safe/**/*"]

      # Finally scan content of allowed file reads
      - policy: "pii"
        priority: 30            # Lowest priority
        config:
          action: "redact"
```

### 6. Test Configuration Changes Safely

**Recommendation**: Use audit-only mode to test new security policies before enforcing them.

```yaml
# Testing phase: audit-only to understand impact
plugins:
  security:
    production_server:
      - policy: "new_security_plugin"
        enabled: true
        config:
          action: "audit_only"  # Test mode: log but don't block

# After testing: enable enforcement
plugins:
  security:
    production_server:  
      - policy: "new_security_plugin"
        enabled: true
        config:
          action: "block"       # Enforcement mode
```

### 7. Document Server-Specific Configurations

**Recommendation**: Use YAML comments to explain why servers have specific configurations.

```yaml
plugins:
  security:
    _global:
      - policy: "pii"
        config: {action: "redact"}

    # Production customer database requires PII blocking due to GDPR compliance
    customer_db_prod:
      - policy: "pii"
        config: {action: "block"}  # Override: GDPR requires blocking

    # Demo server allows PII for realistic demonstrations
    demo_server:
      - policy: "pii"
        enabled: false            # Override: demo needs real-looking data
```

## Troubleshooting

### Common Configuration Errors

#### Error: "Plugin has scope 'server_aware' and cannot be configured in _global section"

**Problem**: Attempting to configure a server-aware plugin globally.

```yaml
# WRONG
plugins:
  security:
    _global:
      - policy: "tool_allowlist"  # ❌ Server-aware plugins need per-server config
```

**Solution**: Move to server-specific sections.

```yaml
# CORRECT
plugins:
  security:
    filesystem:
      - policy: "tool_allowlist"  # ✅ Configured per-server
        config:
          tools: ["read_file", "write_file"]
    database:
      - policy: "tool_allowlist"  # ✅ Different config per server
        config:
          tools: ["read_query", "list_tables"]
```

#### Error: "Plugin configuration references unknown upstream 'server_name'"

**Problem**: Plugin configured for a server that doesn't exist in upstreams.

```yaml
# Configuration mismatch
proxy:
  upstreams:
    - name: "filesystem"      # Server is named "filesystem"

plugins:
  security:
    file_server:              # ❌ "file_server" doesn't match "filesystem"
      - policy: "pii"
```

**Solution**: Ensure server names match exactly.

```yaml
# CORRECT
proxy:
  upstreams:
    - name: "filesystem"      # Server name

plugins:
  security:
    filesystem:               # ✅ Matches server name exactly
      - policy: "pii"
```

#### Error: Plugin not compatible with server type

**Problem**: Using server-specific plugins with incompatible servers.

```yaml
# WRONG
plugins:
  security:
    database_server:
      - policy: "filesystem_server"  # ❌ Filesystem plugin on database server
```

**Solution**: Use appropriate plugins for each server type.

```yaml
# CORRECT
plugins:
  security:
    database_server:
      - policy: "tool_allowlist"     # ✅ Universal plugin works with any server
        config:
          tools: ["read_query"]
          
    filesystem_server:
      - policy: "filesystem_server"  # ✅ Filesystem plugin on filesystem server
        config:
          read: ["docs/**/*"]
```

### Debugging Configuration Issues

#### 1. Use Gatekit's validation mode

```bash
# Test configuration without starting the server
gatekit --config your-config.yaml --validate
```

#### 2. Enable debug logging

```yaml
logging:
  level: "DEBUG"              # Show detailed plugin loading information
  handlers: ["stderr"]
```

#### 3. Start with minimal configuration

If complex configuration isn't working, start minimal and add incrementally:

```yaml
# Minimal working configuration
proxy:
  transport: "stdio"
  upstreams:
    - name: "test"
      command: "npx @modelcontextprotocol/server-filesystem /tmp"

plugins:
  security:
    _global:
      - policy: "pii"
        enabled: true
        config:
          action: "audit_only"  # Safe: only logs, doesn't block
```

#### 4. Check plugin availability

```bash
# List available plugins
gatekit --list-plugins
```

### Configuration Testing Checklist

Before deploying new plugin configurations:

- [ ] **Validation**: Configuration passes `--validate` check
- [ ] **Server names**: All plugin server keys match upstream names exactly
- [ ] **Plugin scopes**: No server-aware plugins in `_global` section
- [ ] **Plugin compatibility**: Server-specific plugins only used with compatible servers
- [ ] **Testing**: Audit-only mode tested before enforcement
- [ ] **Logging**: Appropriate audit logging configured
- [ ] **Documentation**: Server-specific configurations documented with comments
- [ ] **Backup**: Previous working configuration backed up

---

## Next Steps

- **Reference**: See [Configuration Reference](../reference/configuration-reference.md) for complete field documentation
- **Tutorials**: Follow specific tutorials for common scenarios
- **Troubleshooting**: Check [Troubleshooting Guide](../reference/troubleshooting.md) for additional help
- **Plugin Development**: Learn to create custom plugins in the development guide