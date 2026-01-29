# What is Gatekit?

*[Home](../../README.md) > [User Guide](../README.md) > [Core Concepts](README.md) > What is Gatekit?*

Gatekit is a developer gateway that optimizes how AI agents interact with MCP servers. It helps you build better agentic applications by managing context, clarifying tools, and ensuring security—all while maintaining a security-first architecture.

## The Problems Gatekit Solves

Building production AI agents with MCP servers presents several challenges that Gatekit addresses:

### Developer Productivity Challenges
- **Context Window Bloat**: Too many tools consume valuable tokens and confuse the LLM
- **Poor Tool Names**: MCP servers often provide unclear tool names that agents struggle with
- **Performance Issues**: Repeated expensive operations slow down agent responses
- **Debugging Difficulty**: Hard to understand what the agent is doing and why

### Security Concerns (Handled Transparently)
- **Data Protection**: Prevent PII and secrets from leaking into model context
- **Safe Experimentation**: Control tool access while developing and testing
- **Audit Requirements**: Maintain compliance with comprehensive logging

## How Gatekit Works

Gatekit sits between your AI client and MCP servers, intercepting and evaluating every request:

```
AI Client (Claude Desktop) → Gatekit → MCP Server (Filesystem, etc.)
                          ↙         ↘
                   Security      Audit
                   Plugins       Plugins
```

### Request Flow

1. **AI client** sends a request to what it thinks is the MCP server
2. **Gatekit** intercepts the request
3. **Security plugins** evaluate whether the request should be allowed
4. **If allowed**: Request passes through to the actual MCP server
5. **If blocked**: Security policy message is returned to the AI client
6. **Audit plugins** log the entire interaction for compliance and monitoring

**Note**: Gatekit processes multiple requests concurrently, enabling high-performance scenarios with multiple clients or rapid request sequences.

## Core Capabilities

### Context Optimization
- **Tool Filtering**: Show only the tools your agent needs, reducing token usage
- **Tool Renaming**: Clarify confusing tool names for better agent understanding
- **Description Enhancement**: Improve tool descriptions to guide agent behavior

### Performance Enhancement
- **Response Caching**: Cache expensive operations for instant responses
- **Rate Limiting**: Prevent runaway agents from overwhelming servers
- **Concurrent Processing**: Handle multiple requests efficiently

### Security & Compliance (Built-in, Always Active)
- **Data Protection**: Automatic filtering of PII and sensitive information
- **Secret Detection**: Prevent API keys and tokens from entering model context
- **Comprehensive Auditing**: Full visibility for debugging and compliance
- **Complete Request Logs**: Every AI interaction is logged
- **Security Event Monitoring**: Special emphasis on blocked operations
- **Multiple Log Formats**: Simple text, JSON, or detailed formats for different use cases
- **Configurable Verbosity**: From critical security events to detailed debugging

### Plugin Architecture
- **Modular Design**: Add or remove security controls as needed
- **Priority System**: Control the order of security checks
- **Extensible**: Custom plugins for specialized security requirements

## Key Benefits

### Security
- **Zero Trust Model**: Every request is evaluated against security policies
- **Defense in Depth**: Multiple layers of protection (tool + content + audit)
- **Policy Enforcement**: Organizational security policies are automatically enforced
- **Risk Mitigation**: Prevents accidental or malicious operations

### Compliance
- **Audit Trail**: Complete logs of all AI agent activities
- **Policy Documentation**: Security rules are clearly defined and versioned
- **Compliance Reporting**: Logs support regulatory and internal audit requirements

### Operational Visibility
- **Real-Time Monitoring**: See exactly what AI agents are doing
- **Security Analytics**: Understand AI agent behavior patterns
- **Incident Response**: Detailed logs for investigating security events

### Developer Experience
- **Transparent Operation**: Works with existing MCP clients and servers
- **Easy Configuration**: YAML-based configuration with clear documentation
- **Flexible Policies**: Adapt security controls to different environments and use cases

## Use Cases

### Individual Users
- **Personal AI Safety**: Protect personal files from accidental AI operations
- **Workspace Protection**: Ensure AI agents only access intended directories
- **Learning and Development**: Safely experiment with AI tools

### Development Teams
- **Code Repository Protection**: Prevent AI from accessing sensitive code or credentials
- **Environment Separation**: Different security policies for dev/staging/production
- **Team Collaboration**: Consistent security policies across team members

### Enterprises
- **Data Loss Prevention**: Prevent AI agents from accessing confidential information
- **Compliance Requirements**: Meet regulatory requirements for AI system auditing
- **Policy Enforcement**: Implement organizational AI usage policies
- **Risk Management**: Control and monitor AI agent interactions with business systems

## Gatekit vs. Other Security Approaches

### Traditional Application Security
- **Gatekit**: Specialized for AI agent interactions and MCP protocol
- **Traditional**: Generic application security, not AI-aware

### Built-in MCP Server Security
- **Gatekit**: Centralized, configurable security policies across all MCP servers
- **Built-in**: Limited, server-specific, often hardcoded restrictions

### Client-Side Restrictions
- **Gatekit**: Server-side enforcement, cannot be bypassed by clients
- **Client-Side**: Relies on client compliance, can be bypassed or misconfigured

### Network-Level Security
- **Gatekit**: Application-aware, understands MCP semantics and AI context
- **Network-Level**: Protocol-agnostic, limited understanding of AI-specific risks

## When to Use Gatekit

### Perfect For
- **Production AI deployments** requiring security controls
- **Sensitive data environments** where AI access must be controlled
- **Compliance-required environments** needing audit trails
- **Multi-user AI systems** requiring consistent policies
- **Development environments** where you want to safely experiment

### Consider Alternatives When
- **Simple, trusted, single-user scenarios** with low-risk operations
- **Development environments** where you need unrestricted access for debugging
- **Performance-critical applications** where any proxy overhead is unacceptable

## Getting Started

Ready to protect your AI interactions? Start with:

1. **[Installation](../getting-started/installation.md)**: Get Gatekit installed on your system
2. **[Quick Setup](../getting-started/quick-setup.md)**: Configure basic protection in minutes
3. **[Your First Plugin](../getting-started/first-plugin.md)**: Learn how security plugins work

## Next Steps

- **Learn the Architecture**: Understand [how plugins work](plugin-architecture.md)
- **Understand Security**: Explore Gatekit's [security model](security-model.md)
- **See It in Action**: Follow the [securing tool access tutorial](../tutorials/securing-tool-access.md)
