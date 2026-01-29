# Name Availability Evaluation Framework

**Context:** Gatekit needs rebranding due to gatekit.io being taken by a competing security AI product. The new identity must support expansion beyond MCP to general LLM proxy, monitoring, and sandboxing.

## Product Positioning Summary

**What it is today:**
- Personal gateway between MCP clients (Claude Desktop, Cursor, Claude Code, Windsurf, Codex) and upstream MCP servers
- Security boundary: tool filtering, audit logging, PII/secrets detection
- Terminal UI for configuration
- Python plugin architecture

**Where it's going:**
- General LLM proxy and monitoring
- Sandboxing capabilities
- Protocol-agnostic (MCP today, whatever tomorrow)

**Core value:** Control, visibility, and security for AI tool interactions.

---

## Naming Preferences

### Semantic Clarity
The name should give an idea of what the product does. "Gatekit" worked well because telling someone "I have an AI security and auditing product called Gatekit" made the function and mechanism immediately obvious. We want that same quality - a name that carries meaning, not an arbitrary coined word.

**Product functions to evoke:**
- Security / protection
- Auditing / logging / observability
- Control / policy enforcement
- Gateway / proxy / intermediary
- Compliance

### Audience Evolution
**Current target:** Technically savvy power users (developers, security engineers)

**Future target:** Less technical users responsible for security, auditing, compliance, and policy enforcement (security managers, compliance officers, IT directors)

### Tone Constraints
- **Avoid:** Names that scream "technical power user" or "hacker tool"
- **Avoid:** Overly cute/clever dev-culture names (no `kubectl`-style abbreviations)
- **Seek:** Professional enough for enterprise, approachable enough for individuals
- **Seek:** Works in a sentence: "We use [Name] for AI compliance" should sound natural to both a developer and a CISO

### What Made "Gatekit" Work
1. **"Watch"** - evokes monitoring, observability, vigilance
2. **"Gate"** - evokes control, access, security boundary
3. **Compound word** - self-explanatory without being generic
4. **Professional tone** - wouldn't embarrass anyone in a board meeting

### Additional Constraints
- **Domain budget:** $500 max, prefer unparked/available domains
- **Similarity to Gatekit:** Open to anything - clean break is fine
- **Trendy patterns to avoid:** No "-ify", "-ly", "-io" suffixes, no "of the moment" naming conventions. Aim for timeless.
- **Approach:** Selective (10-15 strong candidates) rather than exhaustive list

---

## Competitive Landscape (January 2025)

### Commercial/Enterprise Products

| Name | Company | Positioning | Naming Pattern |
|------|---------|-------------|----------------|
| **Runlayer** | Runlayer ($11M funding) | "Simpler, safer way to connect MCPs" - enterprise security | Compound word (run + layer) |
| **MCPX** | Lunar.dev | "Traffic controls for AI" - gateway + metrics | Acronym + X suffix |
| **Peta** | Dunia Labs | "MCP Vault, Gateway, and Control Plane" - zero-trust | Short abstract noun |
| **AWS MCP Proxy** | Amazon | AWS-hosted, SigV4 auth | Generic descriptor |
| **Kong AI Gateway** | Kong | API gateway extended for MCP | Company + descriptor |
| **MCP Gateway** | Microsoft | Kubernetes reverse proxy | Generic descriptor |
| **MCP Gateway** | Docker | Centralized orchestration | Generic descriptor |

### Open Source Projects

| Name | Positioning | Naming Pattern |
|------|-------------|----------------|
| **Lasso MCP Gateway** | Security-first, plugin-based, guardrails | Metaphor (lasso = catching/constraining) |
| **ContextForge** | IBM - Gateway + registry, REST-to-MCP | Compound (context + forge) |
| **MCPJungle** | Self-hosted registry + proxy | Protocol + metaphor |
| **Agent Gateway** | Solo.io - Agent-to-agent communication | Generic descriptor |
| **Envoy AI Gateway** | MCP support in Envoy proxy | Company + descriptor |

### Naming Pattern Analysis

**Patterns in use:**
1. **Compound words:** Runlayer, ContextForge, MCPJungle, Gatekit
2. **Short abstract nouns:** Peta, Lasso
3. **Acronym + suffix:** MCPX
4. **Generic descriptors:** "MCP Gateway", "AI Gateway" (overused, avoid)

**Words/roots already claimed:**
- Layer (Runlayer)
- Forge (ContextForge)
- Jungle (MCPJungle)
- Lasso (Lasso Security)
- Peta (Dunia Labs)
- Gate/Gateway (heavily overused in space)

**Differentiation opportunity:**
Most competitors use either generic descriptors or protocol-specific names (MCP*). A semantically meaningful name that evokes security/auditing/control WITHOUT referencing MCP specifically would stand out and age better.

### Sources
- [Runlayer](https://www.runlayer.com/)
- [Lunar.dev MCPX](https://docs.lunar.dev/mcpx/)
- [Peta Documentation](https://docs.peta.io/)
- [Lasso MCP Gateway](https://github.com/lasso-security/mcp-gateway)
- [IBM ContextForge](https://github.com/IBM/mcp-context-forge)
- [MCPJungle](https://github.com/mcpjungle/MCPJungle)
- [Microsoft MCP Gateway](https://github.com/microsoft/mcp-gateway)
- [Docker MCP Gateway](https://docs.docker.com/ai/mcp-catalog-and-toolkit/mcp-gateway/)

---

## Evaluation Tiers

### Tier 1: Deal-Breakers (Any failure = disqualify)

| Check | Why It Matters |
|-------|---------------|
| **USPTO trademark search** | Legal risk. Search TESS for exact match + phonetic equivalents in Classes 9, 42 (software) |
| **`.com` domain** | Enterprise credibility. Check if available, parked, or actively used by competitor |
| **PyPI package name** | Primary distribution channel. Exact match required |
| **GitHub organization** | Essential for dev tools. Need both org name and repo name |

### Tier 2: High Priority (Strong preference for availability)

| Check | Why It Matters |
|-------|---------------|
| **`.io` domain** | Developer tool standard |
| **`.dev` or `.ai` domain** | Credible alternatives if .com is parked |
| **Google search landscape** | Is there an established player with this name in tech/security/AI? Even unregistered trademarks are risk |
| **Homebrew formula name** | Critical for macOS CLI distribution |
| **Twitter/X handle** | Brand presence, support channel |
| **Docker Hub namespace** | Future container distribution |

### Tier 3: Nice-to-Have (Check but not blocking)

| Check | Why It Matters |
|-------|---------------|
| **LinkedIn company page** | B2B credibility |
| **Discord server name** | Community building |
| **Reddit subreddit** | r/[name] availability |
| **VS Code Marketplace** | Future extension namespace |
| **npm package** | If any JS components planned |
| **Bluesky handle** | Growing dev community |

### Tier 4: Practical Constraints (Hard requirements)

| Constraint | Why |
|------------|-----|
| **Valid Python identifier** | Must be importable: `^[a-z][a-z0-9_]*$` |
| **No shell command conflicts** | Can't clash with common CLI tools |
| **≤12 characters** | Comfortable for CLI typing |
| **Obvious pronunciation** | Verbal communication, word-of-mouth |
| **No hyphens** | PyPI allows them but Python imports don't |

### Tier 5: Future-Proofing

| Check | Why |
|-------|-----|
| **Name doesn't constrain scope** | No "MCP" or "gateway" or protocol-specific terms |
| **Works for enterprise tier** | "[Name] Enterprise" sounds credible |
| **No dated technology references** | Avoid names that tie to 2024 trends |
| **Expansion potential** | Sub-products, verb potential, abbreviations |

---

## Evaluation Process

```
1. FAST FILTER (eliminates 90%)
   ├── Check .com availability
   ├── Check PyPI: pypi.org/project/{name}
   └── Check GitHub: github.com/{name}

2. LEGAL SCREEN (top candidates only)
   ├── USPTO TESS: tmsearch.uspto.gov
   ├── EUIPO (if EU market matters)
   └── Google "{name} software" and "{name} security"

3. DEEP VALIDATION
   ├── All remaining domain TLDs
   ├── Social handles (Twitter, LinkedIn, Discord)
   ├── Homebrew formula conflicts
   └── Competitive landscape (Product Hunt, Crunchbase, G2)

4. FINAL CHECKS
   ├── Pronunciation test (say it out loud to 3 people)
   ├── Multi-language connotation check
   └── CLI ergonomics test (type it 50 times)
```

---

## Automated Checking Tools

| Resource | What It Checks |
|----------|---------------|
| **namecheckr.com** | Social handles + domains in bulk |
| **instantdomainsearch.com** | Fast domain availability |
| **USPTO TESS** | US trademarks |
| **libraries.io** | Package registry search across ecosystems |
| **knowem.com** | 500+ social networks at once |

---

## Red Flags That Disqualify a Name

1. **.com owned by a funded company** in adjacent space (even if dormant)
2. **Existing trademark** in Class 9/42 (software), even if narrow
3. **Active GitHub org** with any following or activity
4. **Existing PyPI package** (even abandoned - squatting is common)
5. **First page Google results** dominated by a specific product/company
6. **Common English word** (impossible to SEO, trademark weak)
7. **Sounds like existing tool** (kubectl, docker, vault, etc.)

---

## What Can Be Checked Automatically vs Manually

### Automated (Claude can check)

- Domain availability (.com, .io, .dev, .ai, etc.)
- PyPI package availability
- npm package availability
- GitHub org/user existence
- Google search landscape
- Product Hunt / Crunchbase presence
- Homebrew formulae
- Docker Hub namespace

### Manual Verification Required

- Twitter/X handle (bot detection)
- LinkedIn company page (requires login)
- Discord server name (requires account)
- Reddit subreddit (creation rules complex)
- Bluesky handle (requires auth)
- Pronunciation test (need humans)
- Cultural/linguistic gut check (native speakers catch nuance)
- Final USPTO TESS confirmation (web interface unreliable for automation)

---

## Scoring Matrix Template

For each candidate name, score 1-5:

| Dimension | Weight | Score |
|-----------|--------|-------|
| .com available | Critical | |
| .io available | High | |
| .dev or .ai available | Medium | |
| USPTO appears clear | Critical | |
| GitHub available | Critical | |
| PyPI available | Critical | |
| Twitter available | Medium | |
| No major search conflicts | High | |
| CLI-friendly (short, typeable) | High | |
| Valid Python module name | Medium | |
| Memorable/pronounceable | Medium | |
| Future-proof scope | High | |
| **Total** | | |
