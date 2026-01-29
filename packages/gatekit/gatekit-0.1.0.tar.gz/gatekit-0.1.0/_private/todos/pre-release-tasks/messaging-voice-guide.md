# Gatekit Messaging Voice Guide

## Overview

This document defines the messaging voice and positioning for Gatekit as an MCP Gateway Framework. The tone is framework-documentation style: factual, technically accurate, and developer-focused without being salesy or hyperbolic.

## Voice Characteristics

### Core Attributes

1. **Factual and Descriptive**
   - State what it does, not how amazing it is
   - "Plugin-based architecture" not "Powerful plugin system!"
   - "Provides" not "Empowers"

2. **Code-First Communication**
   - Show functionality through code examples
   - Let the code demonstrate capabilities
   - Minimal prose, maximum clarity

3. **Assumed Developer Competence**
   - No "easy!" or "simple!" - developers can judge difficulty
   - No hand-holding or over-explanation
   - Trust the reader to understand implications

4. **Framework Terminology**
   - Use standard framework language: "extends", "implements", "interfaces"
   - Reference patterns developers know: "middleware", "plugins", "pipeline"
   - Position alongside Django, Laravel, Express - not against other gateways

5. **Technical Honesty**
   - Clear version numbers and maturity status
   - "API may change" when appropriate
   - Acknowledge limitations without apology

6. **Documentation-Heavy**
   - Assume people want to learn, not be sold
   - Comprehensive guides over marketing copy
   - API references over feature lists

## Positioning Statement

**Short Version:**
"An MCP gateway framework for Python developers."

**Medium Version:**
"Gatekit is an MCP gateway framework that provides a plugin-based architecture for implementing custom security, middleware, and auditing capabilities."

**Long Version:**
"Gatekit is an MCP gateway framework for Python developers. When you need an MCP gateway with specific requirements - custom security policies, specialized audit formats, or unique middleware behaviors - Gatekit provides the framework to build exactly what you need."

## Key Differentiator

**Not:** "The best MCP gateway" or "The most secure gateway"
**But:** "A framework for building YOUR gateway with YOUR requirements"

We're not competing with other gateways - we're in a different category. Other gateways are solutions; Gatekit is a framework for building solutions.

## Messaging Examples

### GitHub README Opening

```markdown
# Gatekit

An MCP gateway framework for Python developers.

## Overview

Gatekit provides a plugin-based architecture for building MCP gateways with custom security, middleware, and auditing capabilities. Built on asyncio with full type hints.
```

### Feature Description

**Instead of:**
"Powerful and flexible plugin system that makes it easy to extend functionality!"

**Write:**
"Plugin architecture - Extend via Python classes implementing well-defined interfaces"

### Code Examples

Always lead with code when possible:

```python
from gatekit.plugins.interfaces import SecurityPlugin, PluginResult

class CustomAuthPlugin(SecurityPlugin):
    """Implement your authentication logic."""
    
    async def process_request(self, request, server):
        if self.is_authorized(request):
            return PluginResult(allowed=True)
        return PluginResult(allowed=False, reason="Unauthorized")
```

### Use Case Descriptions

**Instead of:**
"Perfect for enterprises needing bulletproof security!"

**Write:**
"Regulated Industries: Implement compliance-specific filtering"

### Documentation Introduction

```markdown
# Introduction

Gatekit is an MCP gateway framework for Python developers. It provides a plugin-based architecture for implementing custom security, middleware, and auditing capabilities.

## Philosophy

MCP gateways need to enforce organization-specific policies. Rather than trying to anticipate every possible requirement, Gatekit provides a framework where you implement exactly what you need through Python code.
```

## What to Avoid

### Marketing Superlatives
- ❌ "Revolutionary"
- ❌ "Game-changing"
- ❌ "Enterprise-grade"
- ❌ "Best-in-class"
- ❌ "Cutting-edge"

### Emotional Appeals
- ❌ "You'll love..."
- ❌ "Never worry about..."
- ❌ "Finally, a solution that..."
- ❌ "The last gateway you'll ever need"

### Comparative Claims
- ❌ "Better than [competitor]"
- ❌ "Unlike other gateways..."
- ❌ "The only gateway that..."

### Oversimplification
- ❌ "It's easy!"
- ❌ "Just three simple steps"
- ❌ "Anyone can do it"

## Voice Inspiration

Think of how these frameworks describe themselves:

**Django:**
"Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design."

**Laravel:**
"Laravel is a web application framework with expressive, elegant syntax."

**Express:**
"Fast, unopinionated, minimalist web framework for Node.js"

Notice: Factual. Descriptive. No superlatives. They state what they are and let developers decide if it fits their needs.

## Sample Announcements

### Hacker News

```
Gatekit - MCP Gateway Framework

We've been working on Gatekit, an MCP gateway framework that lets you write Python plugins to handle security, middleware, and auditing for MCP servers.

The main idea is that instead of configuring a gateway, you extend it with code. Each plugin type has a clear interface:

- SecurityPlugin: Make allow/block decisions
- MiddlewarePlugin: Transform or complete requests  
- AuditingPlugin: Log to your systems

Built with Python 3.11+, asyncio, full type hints. ~300 tests, 90% coverage.

Docs: github.com/gatekit/gatekit
PyPI: pip install gatekit
```

### Twitter/X

```
Gatekit: MCP gateway framework where you implement your requirements as Python plugins instead of working within configuration constraints.

Security, middleware, and auditing plugins with clear interfaces.

pip install gatekit
github.com/gatekit/gatekit
```

### Reddit r/Python

```
Built an MCP gateway framework in Python

Gatekit provides a plugin-based architecture for building MCP gateways. You write Python classes that implement your specific security, middleware, and auditing requirements.

Each plugin type has a clear interface. The framework handles pipeline processing, plugin ordering, and error isolation. You focus on your business logic.

Python 3.11+, asyncio, type hints throughout.

GitHub: github.com/gatekit/gatekit
```

## Summary

The Gatekit voice is that of a capable framework that doesn't need to sell itself. It describes what it does, shows how it works through code, and lets developers determine if it meets their needs. This positions Gatekit as a professional tool in the same category as Django, Laravel, or Express - frameworks that developers choose based on technical merit, not marketing promises.