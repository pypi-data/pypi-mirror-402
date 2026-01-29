# Framework Messaging Examples

## Complete Messaging Templates for Gatekit Launch

### 1. GitHub README (Full Version)

```markdown
# Gatekit

An MCP gateway framework for Python developers.

## Overview

Gatekit provides a plugin-based architecture for building MCP gateways with custom security, middleware, and auditing capabilities. Built on asyncio with full type hints.

## Features

- **Plugin Architecture** - Extend via Python classes implementing well-defined interfaces
- **Security Plugins** - Implement custom authorization and filtering logic  
- **Middleware Plugins** - Transform requests/responses, add caching, implement routing
- **Auditing Plugins** - Create audit trails in any format
- **Multi-Server Support** - Route to multiple upstream MCP servers
- **Processing Pipeline** - Observable pipeline with stages and outcomes
- **Async Throughout** - Built on asyncio for concurrent request handling
- **Type Safe** - Full type hints with Pydantic validation

## Installation

```bash
pip install gatekit
```

## Quick Start

```python
from gatekit.plugins.interfaces import SecurityPlugin, PluginResult

class CustomAuthPlugin(SecurityPlugin):
    """Implement your authentication logic."""
    
    async def process_request(self, request, server):
        if self.is_authorized(request):
            return PluginResult(allowed=True)
        return PluginResult(allowed=False, reason="Unauthorized")

# Register your plugin
HANDLERS = {
    "custom_auth": CustomAuthPlugin
}
```

Configure in YAML:

```yaml
plugins:
  security:
    _global:
      - handler: custom_auth
        config:
          api_key: "${API_KEY}"
```

## Plugin Development

Each plugin type has a specific interface:

### Security Plugin
```python
class PIIFilter(SecurityPlugin):
    async def process_request(self, request, server):
        if self.contains_pii(request):
            return PluginResult(allowed=False, reason="Contains PII")
        return PluginResult(allowed=True)
```

### Middleware Plugin
```python
class CacheMiddleware(MiddlewarePlugin):
    async def process_request(self, request, server):
        if cached := self.get_cached_response(request):
            return PluginResult(completed_response=cached)
        return PluginResult()  # Continue to upstream
```

### Auditing Plugin
```python
class CustomAuditor(AuditingPlugin):
    async def log_request(self, request, pipeline, server):
        await self.write_to_siem({
            'timestamp': time.time(),
            'request': request.to_dict(),
            'pipeline': pipeline.to_dict()
        })
```

## Documentation

- [Getting Started](docs/getting-started.md)
- [Plugin Development Guide](docs/plugins.md)
- [Configuration Reference](docs/configuration.md)
- [API Reference](docs/api.md)

## Requirements

- Python 3.11+
- asyncio
- pydantic

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

Apache 2.0
```

### 2. PyPI Description

```markdown
# Gatekit

An MCP gateway framework for Python developers.

Gatekit provides a plugin-based architecture for building MCP (Model Context Protocol) gateways with custom security, middleware, and auditing capabilities. 

## Key Features

- Write Python plugins to implement your specific requirements
- Security plugins for custom authorization and filtering
- Middleware plugins for transformation, caching, and routing
- Auditing plugins for any log format or destination
- Full async support with asyncio
- Type hints throughout
- Observable processing pipeline with detailed outcomes

## Use Cases

- Implement organization-specific security policies
- Add custom PII detection beyond regex patterns
- Create audit trails for compliance requirements
- Build tool filtering based on your RBAC system
- Add caching, rate limiting, or request routing

## Quick Example

```python
from gatekit.plugins.interfaces import SecurityPlugin, PluginResult

class MySecurityPlugin(SecurityPlugin):
    async def process_request(self, request, server):
        # Your security logic here
        if self.is_authorized(request):
            return PluginResult(allowed=True)
        return PluginResult(allowed=False, reason="Unauthorized")
```

## Installation

```bash
pip install gatekit
```

## Documentation

Full documentation available at: https://github.com/gatekit/gatekit

## License

Apache 2.0
```

### 3. Blog Post Announcement

```markdown
# Introducing Gatekit: An MCP Gateway Framework

We're releasing Gatekit, an MCP gateway framework that takes a different approach to gateway extensibility. Instead of configuration files and limited extension points, Gatekit lets you write Python code to implement your exact requirements.

## The Problem We Solved

Every organization has unique security requirements. Some need custom PII patterns. Others need specific audit formats for compliance. Many need to integrate with existing RBAC systems.

Existing gateways offer configuration options, but configuration only goes so far. When you need to implement your company's specific security patterns or integrate with your internal systems, you hit walls.

## Our Approach: Framework, Not Gateway

Gatekit is a framework. You write Python plugins that implement your logic:

```python
class CompanyPIIFilter(SecurityPlugin):
    def __init__(self, config):
        # Load your company's PII patterns
        self.patterns = load_company_patterns()
    
    async def process_request(self, request, server):
        if self.detect_pii(request, self.patterns):
            return PluginResult(
                allowed=False, 
                reason="Contains company-defined PII"
            )
        return PluginResult(allowed=True)
```

The framework handles:
- Plugin discovery and loading
- Message pipeline processing
- Error isolation
- Observable outcomes

You handle:
- Your business logic
- Your security requirements
- Your integration needs

## Architecture

Gatekit uses a pipeline architecture where messages flow through plugins in priority order:

1. Client sends request
2. Security plugins evaluate
3. Middleware plugins transform
4. Request goes to upstream server
5. Response flows back through plugins
6. Auditing plugins log everything

Each stage is observable, giving you full visibility into processing.

## Plugin Types

### Security Plugins
Make allow/block decisions based on your policies.

### Middleware Plugins  
Transform messages, implement caching, add routing logic.

### Auditing Plugins
Log to your systems in your format.

## Getting Started

```bash
pip install gatekit
```

Then write your first plugin:

```python
from gatekit.plugins.interfaces import SecurityPlugin, PluginResult

class MyFirstPlugin(SecurityPlugin):
    async def process_request(self, request, server):
        # Your logic here
        return PluginResult(allowed=True)

HANDLERS = {"my_plugin": MyFirstPlugin}
```

## Project Status

Version 0.1.0. Active development. API may evolve.

We're using it in production for our specific needs. Your mileage may vary.

## Links

- GitHub: https://github.com/gatekit/gatekit
- Documentation: https://gatekit.readthedocs.io
- PyPI: https://pypi.org/project/gatekit

---

Gatekit is open source under Apache 2.0. Contributions welcome.
```

### 4. Documentation Site Homepage

```markdown
# Gatekit Documentation

## What is Gatekit?

Gatekit is an MCP gateway framework for Python developers. It provides a plugin-based architecture for implementing custom security, middleware, and auditing capabilities in your MCP infrastructure.

## Core Concepts

**Plugins** are Python classes that process MCP messages according to your requirements.

**Pipeline** is the ordered sequence of plugins that process each message.

**Processing Stages** provide visibility into how each plugin handles messages.

## Getting Started

### Installation

```bash
pip install gatekit
```

### Your First Plugin

```python
from gatekit.plugins.interfaces import SecurityPlugin, PluginResult

class RateLimiter(SecurityPlugin):
    def __init__(self, config):
        self.max_requests = config.get('max_requests', 100)
        self.window = config.get('window', 60)
    
    async def process_request(self, request, server):
        if self.is_rate_limited(request):
            return PluginResult(
                allowed=False,
                reason=f"Rate limit exceeded: {self.max_requests}/{self.window}s"
            )
        return PluginResult(allowed=True)
```

### Configuration

```yaml
plugins:
  security:
    _global:
      - handler: rate_limiter
        config:
          max_requests: 100
          window: 60
```

### Running Gatekit

```bash
gatekit-gateway --config your-config.yaml
```

## Learn More

- [Architecture Overview](architecture.md) - Understand how Gatekit works
- [Plugin Development](plugins/index.md) - Build your own plugins
- [Configuration Guide](configuration.md) - Configure Gatekit
- [API Reference](api/index.md) - Detailed API documentation

## Who Uses Gatekit?

Developers who need:
- Custom security policies beyond basic authentication
- Specific audit requirements for compliance
- Middleware for caching, routing, or transformation
- Control over their MCP gateway behavior

## Contributing

Gatekit is open source. See our [Contributing Guide](contributing.md) to get involved.
```

### 5. Hacker News Submission

```
Show HN: Gatekit – MCP Gateway Framework for Python

I've been working on Gatekit, an MCP gateway framework that lets you write Python plugins instead of working within configuration constraints.

The main differentiator from other MCP gateways is that it's a framework, not a solution. You implement your requirements as code:

    class SQLInjectionFilter(SecurityPlugin):
        async def process_request(self, request, server):
            if self.contains_sql_injection(request):
                return PluginResult(allowed=False, reason="SQL injection detected")
            return PluginResult(allowed=True)

We built this because we needed:
- Custom PII detection (our customers use non-standard ID formats)
- Integration with our internal RBAC
- Specific audit formats for SOC2 compliance

Existing gateways either cost too much or couldn't be customized enough.

Technical details:
- Python 3.11+, built on asyncio
- ~300 tests, 90% coverage
- Plugin interfaces for security, middleware, and auditing
- Observable pipeline with detailed processing stages
- Type hints throughout

It's not trying to be everything to everyone. It's a framework for teams that need to build their own gateway logic.

GitHub: https://github.com/gatekit/gatekit
Docs: https://gatekit.readthedocs.io
PyPI: pip install gatekit

Apache 2.0 license. Feedback welcome.
```

### 6. Reddit r/Python Submission

```
Gatekit - MCP Gateway Framework in Python

I wanted to share a project I've been working on: Gatekit, an MCP gateway framework built with Python 3.11+ and asyncio.

**What it does:** Provides a framework for building MCP gateways where you implement your requirements as Python plugins rather than configuration.

**The architecture:**
- Plugin-based with clear interfaces (SecurityPlugin, MiddlewarePlugin, AuditingPlugin)
- Async throughout using asyncio
- Observable processing pipeline with stages and outcomes
- Type hints and Pydantic validation

**Example plugin:**

    from gatekit.plugins.interfaces import MiddlewarePlugin, PluginResult
    
    class ResponseCache(MiddlewarePlugin):
        async def process_request(self, request, server):
            if cached := await self.cache.get(request):
                return PluginResult(completed_response=cached)
            return PluginResult()  # Continue to upstream
        
        async def process_response(self, request, response, server):
            await self.cache.set(request, response)
            return PluginResult()

**Why we built it:** Needed custom security policies and audit formats that existing gateways couldn't provide. Configuration only goes so far when you need to integrate with internal systems.

**Tech stack:**
- Python 3.11+ with asyncio
- Pydantic for validation
- YAML for configuration
- ~300 tests, 90% coverage

GitHub: https://github.com/gatekit/gatekit

It's Apache 2.0 if anyone wants to use it or contribute. Happy to answer questions about the architecture or implementation decisions.
```

### 7. Twitter/X Thread

```
1/ Releasing Gatekit: An MCP gateway framework where you write Python plugins to implement your requirements instead of configuring someone else's.

2/ Core idea: Every org has different security needs. Instead of configuration options, you write Python:

class MySecurityPlugin(SecurityPlugin):
    async def process_request(self, request, server):
        # Your logic here

3/ Three plugin types:
- Security: Allow/block/modify requests
- Middleware: Transform, cache, route
- Auditing: Log to your systems, your format

4/ Built with Python 3.11+, asyncio, type hints throughout. Observable pipeline shows exactly what each plugin did to each message.

5/ pip install gatekit
GitHub: github.com/gatekit/gatekit
Docs: gatekit.readthedocs.io

Apache 2.0. Built for developers who need control.
```

### 8. LinkedIn Post

```
Announcing Gatekit: An MCP Gateway Framework for Python Developers

We're releasing Gatekit, an open-source MCP gateway framework that takes a code-first approach to gateway customization.

Instead of configuration files with limited options, Gatekit lets you write Python plugins that implement your exact requirements:

• Security plugins for custom authorization logic
• Middleware plugins for transformation and routing  
• Auditing plugins for compliance-specific formats

Key technical features:
- Built on Python 3.11+ with asyncio
- Full type hints for better IDE support
- Observable processing pipeline
- 90% test coverage

This is particularly useful for teams that need to:
- Implement company-specific security policies
- Integrate with existing RBAC systems
- Meet specific compliance requirements
- Add custom middleware behaviors

The framework handles the pipeline processing, error isolation, and plugin orchestration. You focus on implementing your business logic.

GitHub: https://github.com/gatekit/gatekit
Documentation: https://gatekit.readthedocs.io

Open source under Apache 2.0 license. Contributions and feedback welcome.

#Python #OpenSource #MCP #DeveloperTools #Security
```

## Summary

These examples maintain the framework documentation voice throughout:
- Factual descriptions without superlatives
- Code examples that demonstrate functionality
- Technical details without oversimplification
- Clear positioning as a framework, not another gateway
- Appropriate detail level for each platform