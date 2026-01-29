# TUI Mockups - Horizontal Split Layout

These mockups show the preferred layout option (Horizontal Split) in various states, demonstrating how the interface responds to different user selections.

## Layout Overview

- **Top Section**: Global Security and Auditing (static, always visible)
- **Bottom Section**: Three-pane layout for server management
  - Left: MCP Servers list
  - Middle: Server plugins list  
  - Right: Configuration details

## 1. MCP Server Selected (No Plugin Selected)

```
╭─ Gatekit Security Configuration ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ ┌─ Global Security Policies (Applies to All MCP Servers) ───────────────┐ ┌─ Auditing Policies ────────────────────────────────────────────────────┐│
│ │ [☑] PII Filter      Redact: 4 PII types                              [Configure] │ │ [☑] CSV Logger      logs/audit.csv (not created, comma-delimited)   [Configure] ││
│ │ [☑] Prompt Injection Block: 3 methods (standard)                     [Configure] │ │ [☑] Human Readable  logs/audit.log (0.0MB, human readable)          [Configure] ││
│ │ [☑] Secrets Filter  Block: 5 detection types                         [Configure] │ │ [☑] JSON Logger     logs/audit.json (not created, JSON Lines)      [Configure] ││
│ │                                                                              │ │ [☑] Syslog Logger   audit.log (RFC 5424)                           [Configure] ││
│ │                                                                              │ │ [ ] CEF Logger      Export audit logs to CEF format                [Configure] ││
│ │                                                                              │ │ [ ] Debug Logger    Export detailed debug logs (high verbosity)     [Configure] ││
│ │                                                                              │ │ [ ] OpenTelemetry   Export audit logs to OpenTelemetry format       [Configure] ││
│ └──────────────────────────────────────────────────────────────────────────────┘ └────────────────────────────────────────────────────────────────────────┘│
├───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╤
│ ┌─ MCP Servers ──────────────┐ ┌─ Server Plugins ─────────────────────┐ ┌─ Server Overview ──────────────────────────────────────────────────────────────────────────────────────┐│
│ │                            │ │ filesystem server plugins:           │ │ filesystem MCP Server                                                                                   ││
│ │ ● filesystem   ←          │ │                                      │ │ ─────────────────────────────────────────────────────────────────────────────────────────            ││
│ │   /app/sandbox            │ │ • Tool Allowlist              ✅     │ │                                                                                                         ││
│ │   12 tools available      │ │   Allow 4/12 tools                  │ │ Status: ● Connected                                    PID: 12345                                      ││
│ │                            │ │                                      │ │ Command: npx @modelcontextprotocol/server-filesystem  Started: 2h 15m ago                             ││
│ │ ○ github                  │ │ • Path Security               ✅     │ │ Args: /app/sandbox                                                                                      ││
│ │   Not connected           │ │   Sandbox restricted                 │ │                                                                                                         ││
│ │   28 tools available      │ │                                      │ │ Available Tools (12):                                                                                   ││
│ │                            │ │ • Rate Limiting               ○     │ │ • read_file          • write_file         • list_directory      • create_dir                        ││
│ │ ○ sqlite                  │ │   Available to enable                │ │ • delete_file        • execute_command    • move_file           • copy_file                         ││
│ │   Not configured          │ │                                      │ │ • get_permissions    • set_permissions    • watch_directory     • search_files                      ││
│ │   8 tools available       │ │ • Custom Headers              ○     │ │                                                                                                         ││
│ │                            │ │   Available to enable                │ │ Resource Usage:                                                                                         ││
│ │ ────────────────          │ │                                      │ │ Memory: 45.2MB       CPU: 2.1%          Network: 1.2KB/s                                            ││
│ │ + Add Server               │ │ [+ Add Server Plugin]                │ │                                                                                                         ││
│ └────────────────────────────┘ └──────────────────────────────────────┘ │ [Test Connection] [View Logs] [Restart] [Remove Server]                                               ││
│                                                                          └─────────────────────────────────────────────────────────────────────────────────────────────────────┘│
│ Security: 3 active | Auditing: 1 active | Connected Servers: 1/3 | Total Tools: 48 | [Save Configuration] [Load Profile] [Export Config]                                        │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## 2. Global PII Filter Selected

```
╭─ Gatekit Security Configuration ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ ┌─ Global Security Policies (Applies to All MCP Servers) ───────────────┐ ┌─ Auditing Policies ────────────────────────────────────────────────────┐│
│ │ [☑] PII Filter      Redact: 4 PII types                     [Configure]← │ │ [☑] CSV Logger      logs/audit.csv (not created, comma-delimited)   [Configure] ││
│ │ [☑] Prompt Injection Block: 3 methods (standard)                     [Configure] │ │ [☑] Human Readable  logs/audit.log (0.0MB, human readable)          [Configure] ││
│ │ [☑] Secrets Filter  Block: 5 detection types                         [Configure] │ │ [☑] JSON Logger     logs/audit.json (not created, JSON Lines)      [Configure] ││
│ │                                                                              │ │ [☑] Syslog Logger   audit.log (RFC 5424)                           [Configure] ││
│ │                                                                              │ │ [ ] CEF Logger      Export audit logs to CEF format                [Configure] ││
│ │                                                                              │ │ [ ] Debug Logger    Export detailed debug logs (high verbosity)     [Configure] ││
│ │                                                                              │ │ [ ] OpenTelemetry   Export audit logs to OpenTelemetry format       [Configure] ││
│ └──────────────────────────────────────────────────────────────────────────────┘ └────────────────────────────────────────────────────────────────────────┘│
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────────────────────────────────┐│
│ │ PII Filter Configuration (Global - Applies to All Servers)                                  ││
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ││
│ │                                                                                             ││
│ │ Detection Action:                                                                           ││
│ │ ● Redact - Replace detected PII with [REDACTED]                                           ││
│ │ ○ Block - Reject requests containing PII                                                  ││
│ │ ○ Audit Only - Log detections but don't modify                                            ││
│ │                                                                                             ││
│ │ PII Types to Detect:                                                                       ││
│ │ ┌─ Personal Information ─────┐ ┌─ Financial ──────────────┐ ┌─ Network & Technical ──────┐││
│ │ │ ☑ Email Addresses         │ │ ☐ Credit Card Numbers    │ │ ☑ IP Addresses (IPv4/IPv6) │││
│ │ │ ☑ Phone Numbers           │ │ ☐ Bank Account Numbers   │ │ ☐ MAC Addresses            │││
│ │ │ ☑ Social Security Numbers │ │ ☐ Routing Numbers        │ │ ☐ URLs                     │││
│ │ │ ☐ Passport Numbers        │ │ ☐ IBAN                   │ │ ☐ Bitcoin Addresses        │││
│ │ │ ☐ Driver's License        │ │ ☐ CVV Codes              │ │                            │││
│ │ └─────────────────────────────┘ └──────────────────────────┘ └────────────────────────────┘││
│ │                                                                                             ││
│ │ Regional Formats:                      Advanced Options:                                   ││
│ │ ☑ US Formats (SSN, Phone)             ☐ Scan Base64 Encoded Content                       ││
│ │ ☑ EU Formats (VAT, Phone)             ☐ Case Sensitive Matching                          ││
│ │ ☐ UK Formats (NI, Postcode)           Priority: [20] (Lower = Higher Priority)           ││
│ │                                                                                             ││
│ │ Statistics: Redacted today: 156 items | Last triggered: 2 minutes ago                     ││
│ │ [Test Pattern] [Reset to Defaults] [Apply Changes] [Cancel]                               ││
│ └─────────────────────────────────────────────────────────────────────────────────────────────┘│
│ Esc: Back to Server View | Tab: Next Field | Space: Toggle Checkbox | Enter: Apply           │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## 3. Global Secrets Filter Selected

```
╭─ Gatekit Security Configuration ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ ┌─ Global Security Policies (Applies to All MCP Servers) ───────────────┐ ┌─ Auditing Policies ────────────────────────────────────────────────────┐│
│ │ [☑] PII Filter      Redact: 4 PII types                              [Configure] │ │ [☑] CSV Logger      logs/audit.csv (not created, comma-delimited)   [Configure] ││
│ │ [☑] Prompt Injection Block: 3 methods (standard)                     [Configure] │ │ [☑] Human Readable  logs/audit.log (0.0MB, human readable)          [Configure] ││
│ │ [☑] Secrets Filter  Block: 5 detection types                [Configure]← │ │ [☑] JSON Logger     logs/audit.json (not created, JSON Lines)      [Configure] ││
│ │                                                                              │ │ [☑] Syslog Logger   audit.log (RFC 5424)                           [Configure] ││
│ │                                                                              │ │ [ ] CEF Logger      Export audit logs to CEF format                [Configure] ││
│ │                                                                              │ │ [ ] Debug Logger    Export detailed debug logs (high verbosity)     [Configure] ││
│ │                                                                              │ │ [ ] OpenTelemetry   Export audit logs to OpenTelemetry format       [Configure] ││
│ └──────────────────────────────────────────────────────────────────────────────┘ └────────────────────────────────────────────────────────────────────────┘│
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────────────────────────────────┐│
│ │ Secrets Filter Configuration (Global - Applies to All Servers)                              ││
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ││
│ │                                                                                             ││
│ │ Detection Action:                                                                           ││
│ │ ○ Redact - Replace detected secrets with [REDACTED]                                       ││
│ │ ● Block - Reject requests containing secrets                                              ││
│ │ ○ Audit Only - Log detections but don't modify                                            ││
│ │                                                                                             ││
│ │ Secret Types to Detect:                                                                    ││
│ │ ┌─ API Keys & Tokens ────────┐ ┌─ Cloud Providers ──────────┐ ┌─ Authentication ─────────┐││
│ │ │ ☑ AWS Access Keys (AKIA...)│ │ ☑ GCP Service Account Keys│ │ ☑ JWT Tokens            │││
│ │ │ ☑ AWS Secret Keys         │ │ ☑ Azure Subscription Keys │ │ ☑ OAuth Tokens          │││
│ │ │ ☑ GitHub Tokens (ghp_...) │ │ ☑ DigitalOcean Tokens     │ │ ☑ Basic Auth Headers    │││
│ │ │ ☑ GitLab Tokens           │ │ ☑ Heroku API Keys         │ │ ☑ Bearer Tokens         │││
│ │ │ ☑ Slack Tokens            │ │ ☐ Alibaba Cloud Keys      │ │ ☐ Session Cookies       │││
│ │ └─────────────────────────────┘ └────────────────────────────┘ └──────────────────────────┘││
│ │                                                                                             ││
│ │ ┌─ Database & Services ──────┐ ┌─ Encryption Keys ──────────┐                             ││
│ │ │ ☑ Database Passwords      │ │ ☑ Private Keys (PEM/RSA)  │                             ││
│ │ │ ☑ Connection Strings      │ │ ☑ SSH Private Keys        │                             ││
│ │ │ ☑ Redis Passwords         │ │ ☐ GPG Private Keys        │                             ││
│ │ │ ☑ MongoDB URIs            │ │ ☐ Certificate Private Keys│                             ││
│ │ └─────────────────────────────┘ └────────────────────────────┘                             ││
│ │                                                                                             ││
│ │ Entropy Detection:                                                                         ││
│ │ ☑ Enable High-Entropy String Detection   Min Entropy: [4.5] Min Length: [10] chars        ││
│ │                                                                                             ││
│ │ Statistics: Blocked today: 23 secrets | Last detected: 5 minutes ago                      ││
│ │ [Test Pattern] [Import Rules] [Apply Changes] [Cancel]                                    ││
│ └─────────────────────────────────────────────────────────────────────────────────────────────┘│
│ Esc: Back to Server View | Tab: Next Field | Space: Toggle Checkbox | Enter: Apply           │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## 4. Tool Allowlist Selected (Server-Specific)

```
╭─ Gatekit Security Configuration ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ ┌─ Global Security Policies (Applies to All MCP Servers) ───────────────┐ ┌─ Auditing Policies ────────────────────────────────────────────────────┐│
│ │ [☑] PII Filter      Redact: 4 PII types                              [Configure] │ │ [☑] CSV Logger      logs/audit.csv (not created, comma-delimited)   [Configure] ││
│ │ [☑] Prompt Injection Block: 3 methods (standard)                     [Configure] │ │ [☑] Human Readable  logs/audit.log (0.0MB, human readable)          [Configure] ││
│ │ [☑] Secrets Filter  Block: 5 detection types                         [Configure] │ │ [☑] JSON Logger     logs/audit.json (not created, JSON Lines)      [Configure] ││
│ │                                                                              │ │ [☑] Syslog Logger   audit.log (RFC 5424)                           [Configure] ││
│ │                                                                              │ │ [ ] CEF Logger      Export audit logs to CEF format                [Configure] ││
│ │                                                                              │ │ [ ] Debug Logger    Export detailed debug logs (high verbosity)     [Configure] ││
│ │                                                                              │ │ [ ] OpenTelemetry   Export audit logs to OpenTelemetry format       [Configure] ││
│ └──────────────────────────────────────────────────────────────────────────────┘ └────────────────────────────────────────────────────────────────────────┘│
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌─ MCP Servers ──────┐ ┌─ Server Plugins ───────────┐ ┌─ Tool Allowlist Configuration ────────┐│
│ │                    │ │ filesystem plugins:        │ │ Server: filesystem                    ││
│ │ ● filesystem   ←  │ │                            │ │ ─────────────────────────────────     ││
│ │   /app/sandbox    │ │ • Tool Allowlist      ✅ ← │ │                                       ││
│ │   12 tools        │ │   Allow 4/12 tools        │ │ Access Control Mode:                 ││
│ │                    │ │                            │ │ ○ Allow All - No restrictions        ││
│ │ ○ github          │ │ • Path Security       ✅   │ │ ● Allowlist - Only allow selected    ││
│ │   Not connected   │ │   Sandbox restricted      │ │ ○ Blocklist - Block selected tools   ││
│ │   28 tools        │ │                            │ │                                       ││
│ │                    │ │ • Rate Limiting       ○   │ │ Available Tools (12):                 ││
│ │ ○ sqlite          │ │   Available to enable     │ │ ┌─ File Operations ───────────────┐  ││
│ │   Not configured  │ │                            │ │ │ ☑ read_file                    │  ││
│ │   8 tools         │ │ • Custom Headers      ○   │ │ │ ☑ write_file                   │  ││
│ │                    │ │   Available to enable     │ │ │ ☐ delete_file ⚠️ Dangerous     │  ││
│ │ ──────────────    │ │                            │ │ │ ☐ move_file                    │  ││
│ │ + Add Server       │ │ [+ Add Plugin]             │ │ │ ☐ copy_file                    │  ││
│ └────────────────────┘ └────────────────────────────┘ │ └───────────────────────────────┘  ││
│                                                        │ ┌─ Directory Operations ────────┐  ││
│                                                        │ │ ☑ list_directory              │  ││
│                                                        │ │ ☑ create_directory            │  ││
│                                                        │ │ ☐ remove_directory ⚠️         │  ││
│                                                        │ │ ☐ watch_directory             │  ││
│                                                        │ └───────────────────────────────┘  ││
│                                                        │ ┌─ System Operations ───────────┐  ││
│                                                        │ │ ☐ execute_command ⚠️ Dangerous│  ││
│                                                        │ │ ☐ get_permissions             │  ││
│                                                        │ │ ☐ set_permissions ⚠️          │  ││
│                                                        │ └───────────────────────────────┘  ││
│                                                        │                                       ││
│                                                        │ Custom Block Message:                 ││
│                                                        │ [Tool access denied by policy______] ││
│                                                        │                                       ││
│                                                        │ Summary: 4 of 12 tools allowed       ││
│                                                        │ [Safe Defaults] [Clear] [Apply]      ││
│                                                        └───────────────────────────────────────┘│
│ Security: 3 active | Auditing: 1 active | Servers: 1/3 connected | [Save] [Load Profile]     │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## 5. Path Security Selected (Filesystem Server)

```
╭─ Gatekit Security Configuration ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ ┌─ Global Security Policies (Applies to All MCP Servers) ───────────────┐ ┌─ Auditing Policies ────────────────────────────────────────────────────┐│
│ │ [☑] PII Filter      Redact: 4 PII types                              [Configure] │ │ [☑] CSV Logger      logs/audit.csv (not created, comma-delimited)   [Configure] ││
│ │ [☑] Prompt Injection Block: 3 methods (standard)                     [Configure] │ │ [☑] Human Readable  logs/audit.log (0.0MB, human readable)          [Configure] ││
│ │ [☑] Secrets Filter  Block: 5 detection types                         [Configure] │ │ [☑] JSON Logger     logs/audit.json (not created, JSON Lines)      [Configure] ││
│ │                                                                              │ │ [☑] Syslog Logger   audit.log (RFC 5424)                           [Configure] ││
│ │                                                                              │ │ [ ] CEF Logger      Export audit logs to CEF format                [Configure] ││
│ │                                                                              │ │ [ ] Debug Logger    Export detailed debug logs (high verbosity)     [Configure] ││
│ │                                                                              │ │ [ ] OpenTelemetry   Export audit logs to OpenTelemetry format       [Configure] ││
│ └──────────────────────────────────────────────────────────────────────────────┘ └────────────────────────────────────────────────────────────────────────┘│
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌─ MCP Servers ──────┐ ┌─ Server Plugins ───────────┐ ┌─ Path Security Configuration ─────────┐│
│ │                    │ │ filesystem plugins:        │ │ Server: filesystem                    ││
│ │ ● filesystem   ←  │ │                            │ │ ─────────────────────────────────     ││
│ │   /app/sandbox    │ │ • Tool Allowlist      ✅   │ │                                       ││
│ │   12 tools        │ │   Allow 4/12 tools        │ │ Path Access Control:                 ││
│ │                    │ │                            │ │ Restrict file operations to specific ││
│ │ ○ github          │ │ • Path Security       ✅ ← │ │ directories and block sensitive files││
│ │   Not connected   │ │   Sandbox restricted      │ │                                       ││
│ │   28 tools        │ │                            │ │ Allowed Paths:                        ││
│ │                    │ │ • Rate Limiting       ○   │ │ ┌─────────────────────────────────┐  ││
│ │ ○ sqlite          │ │   Available to enable     │ │ │ /app/sandbox/**                 │  ││
│ │   Not configured  │ │                            │ │ │ /shared/data/                   │  ││
│ │   8 tools         │ │ • Custom Headers      ○   │ │ │ ~/Documents/projects/           │  ││
│ │                    │ │   Available to enable     │ │ │ [+ Add Path]                    │  ││
│ │ ──────────────    │ │                            │ │ └─────────────────────────────────┘  ││
│ │ + Add Server       │ │ [+ Add Plugin]             │ │                                       ││
│ └────────────────────┘ └────────────────────────────┘ │ Blocked Patterns:                    ││
│                                                        │ ┌─────────────────────────────────┐  ││
│                                                        │ │ *.secret                        │  ││
│                                                        │ │ *.key                           │  ││
│                                                        │ │ *.pem                           │  ││
│                                                        │ │ .env*                           │  ││
│                                                        │ │ **/node_modules/**              │  ││
│                                                        │ │ **/.git/**                      │  ││
│                                                        │ │ [+ Add Pattern]                 │  ││
│                                                        │ └─────────────────────────────────┘  ││
│                                                        │                                       ││
│                                                        │ Additional Security:                  ││
│                                                        │ ☑ Block path traversal attempts      ││
│                                                        │ ☑ Prevent symlink escapes            ││
│                                                        │ ☑ Hide directory listings            ││
│                                                        │ ☐ Read-only mode                     ││
│                                                        │                                       ││
│                                                        │ [Test Path] [Apply] [Cancel]         ││
│                                                        └───────────────────────────────────────┘│
│ Security: 3 active | Auditing: 1 active | Servers: 1/3 connected | [Save] [Load Profile]     │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## 6. Prompt Injection Defense (When Enabling)

```
╭─ Gatekit Security Configuration ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ ┌─ Global Security Policies (Applies to All MCP Servers) ───────────────┐ ┌─ Auditing Policies ────────────────────────────────────────────────────┐│
│ │ [☑] PII Filter      Redact: 4 PII types                              [Configure] │ │ [☑] CSV Logger      logs/audit.csv (not created, comma-delimited)   [Configure] ││
│ │ [☑] Prompt Injection Block: 3 methods (standard)                     [Configure] │ │ [☑] Human Readable  logs/audit.log (0.0MB, human readable)          [Configure] ││
│ │ [☑] Secrets Filter  Block: 5 detection types                         [Configure] │ │ [☑] JSON Logger     logs/audit.json (not created, JSON Lines)      [Configure] ││
│ │ [ ] Prompt Defense  Click to enable injection protection   [Configure]← │ │ [☑] Syslog Logger   audit.log (RFC 5424)                           [Configure] ││
│ │                                                                              │ │ [ ] CEF Logger      Export audit logs to CEF format                [Configure] ││
│ │                                                                              │ │ [ ] Debug Logger    Export detailed debug logs (high verbosity)     [Configure] ││
│ │                                                                              │ │ [ ] OpenTelemetry   Export audit logs to OpenTelemetry format       [Configure] ││
│ └──────────────────────────────────────────────────────────────────────────────┘ └────────────────────────────────────────────────────────────────────────┘│
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────────────────────────────────┐│
│ │ Prompt Injection Defense Configuration (Global - Applies to All Servers)                    ││
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ││
│ │                                                                                             ││
│ │ ⚠️ This plugin protects against attempts to manipulate AI behavior through prompt injection ││
│ │                                                                                             ││
│ │ Detection Action:                                                                           ││
│ │ ● Block - Reject suspicious requests immediately                                           ││
│ │ ○ Audit Only - Log detections but allow through (testing mode)                            ││
│ │                                                                                             ││
│ │ Detection Sensitivity:                                                                      ││
│ │ ○ Standard - Balance between security and false positives                                 ││
│ │ ● Strict - Maximum protection, may have more false positives                              ││
│ │                                                                                             ││
│ │ Detection Methods:                                                                          ││
│ │ ┌─ Attack Patterns ──────────┐ ┌─ Behavioral Detection ─────┐ ┌─ Content Analysis ──────┐││
│ │ │ ☑ Delimiter Injection      │ │ ☑ Role Manipulation         │ │ ☑ Command Patterns      │││
│ │ │   (````, |||, <<<)         │ │   ("ignore previous")       │ │   (execute, run, eval)  │││
│ │ │ ☑ Context Breaking         │ │ ☑ System Prompt Override    │ │ ☑ Code Injection        │││
│ │ │   (END, STOP, IGNORE)      │ │   ("you are now")           │ │   (import, require)     │││
│ │ │ ☑ Encoding Bypass          │ │ ☑ Instruction Hijacking     │ │ ☑ Data Exfiltration     │││
│ │ │   (base64, unicode)        │ │   ("new instructions")      │ │   (send, post, leak)    │││
│ │ └─────────────────────────────┘ └──────────────────────────────┘ └────────────────────────┘││
│ │                                                                                             ││
│ │ Custom Patterns:                                                                            ││
│ │ ┌───────────────────────────────────────────────────────────────────────────────────┐     ││
│ │ │ Pattern Name          | Regex Pattern                     | Action                 │     ││
│ │ │ ─────────────────────────────────────────────────────────────────────────────────│     ││
│ │ │ Custom Delimiter      | \[\[SYSTEM\]\].*\[\[/SYSTEM\]\]  | Block                  │     ││
│ │ │ [+ Add Custom Pattern]                                                            │     ││
│ │ └───────────────────────────────────────────────────────────────────────────────────┘     ││
│ │                                                                                             ││
│ │ Exemptions:                                                                                 ││
│ │ Tools to exclude from checking: [None selected] [Select Tools...]                          ││
│ │                                                                                             ││
│ │ [Enable Protection] [Configure Later] [Cancel]                                             ││
│ └─────────────────────────────────────────────────────────────────────────────────────────────┘│
│ Esc: Cancel | Tab: Next Field | Space: Toggle | Enter: Enable                                │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Design Notes

### Navigation Flow
1. **Global plugins**: Click any global security/auditing item → full-screen configuration
2. **Server plugins**: Select server → see plugins → select plugin → detailed configuration in right pane
3. **Escape key**: Always returns to main server view
4. **Tab navigation**: Cycles through form fields in configuration views

### Visual Indicators
- **●** Connected/Active
- **○** Available/Disconnected  
- **❌** Disabled
- **✅** Enabled/Active
- **←** Currently selected
- **⚠️** Dangerous/Warning

### Key Features
- Global plugins always visible at top
- Server context preserved during plugin configuration
- Clear scope indication (Global vs Server-specific)
- Consistent configuration patterns across all plugins
- Status information and statistics where relevant