# MCP Gateway Market Research: Problems & Reality Check

## Executive Summary

Three MCP gateway vendors (Runlayer, MCP Manager/mcpmanager.ai, Lunar.dev) claim to solve similar problems. Cross-referencing their claims against real user discussions reveals which problems are genuine and which are marketing amplification.

---

## Source Reliability Audit

**This research was audited for source quality. Each problem is rated for reliability.**

| Problem | Reliability | Primary Sources | Concerns |
|---------|-------------|-----------------|----------|
| 1. Security/Code Execution | MEDIUM | GitHub issues, CVEs | Some stats from vendor reports |
| 2. Credential Management | **LOW** | Single vendor report | Astrix Security stats unverified |
| 3. Token Consumption | MEDIUM-HIGH | Developer measurements | Tool caps unverified |
| 4. Configuration Hell | **HIGH** | Structural MCP fact | Multiple independent sources |
| 5. Restart Hell | MEDIUM-HIGH | GitHub issues | Some unsourced claims |
| 6. Black Box Debugging | **HIGH** | HN, blogs, tool creation | Multiple independent sources |
| 7. Access Control | MEDIUM | Independent blogs | Mixed with vendor marketing |
| 8. Security Review Bottleneck | **LOW** | Vendor case studies only | No independent verification |

**How to read this document:**
- **HIGH reliability**: Multiple independent, non-vendor sources confirm the problem
- **MEDIUM reliability**: Some independent sources, but mixed with vendor claims or unverified stats
- **LOW reliability**: Primarily vendor marketing or single-source claims

---

## The Problems (With Reliability Ratings)

### 1. Security: Users Don't Understand They're Running Arbitrary Code

**Reliability: MEDIUM**

**The Plain-Language Problem:** When you "connect to an MCP server," you're often downloading and executing code on your machine with your full user permissions. The term "server" makes people think it's remote and sandboxed—it's not.

**Well-Sourced Evidence:**
- GitHub Issue #630 documents this as a critical security concern ([source](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/630)) ✓ Verified
- Real CVE: **CVE-2025-6514** (CVSS 9.6) - Remote code execution in mcp-remote ([JFrog analysis](https://jfrog.com/blog/2025-6514-critical-mcp-remote-rce-vulnerability/)) ✓ Verified

**Poorly-Sourced Evidence (treat with skepticism):**
- "43% of MCP implementations found vulnerable to command injection" - Backslash Security blog. ⚠️ Vendor claim, methodology unverified
- "The 'S' in MCP stands for Security" joke - ⚠️ Claimed without specific source

**Who Has This Problem:** Anyone installing MCP servers from the 18,000+ public registry without vetting.

**Vendor Claims (marketing, not evidence):**
- Runlayer: "10% of MCP servers are malicious, the rest are exploitable" - ⚠️ No source provided
- MCP Manager: "MCP servers are vulnerable to unique security threats including prompt injection and rug pull attacks"
- Lunar.dev: References OWASP LLM07 "Excessive Agency"

---

### 2. Credentials: Most MCP Servers Use Insecure Static Secrets

**Reliability: LOW** ⚠️

**The Plain-Language Problem:** Many MCP servers need credentials to work. Many rely on long-lived API keys stored in config files—the kind that get leaked in git commits and never rotated.

**Evidence (single source, unverified methodology):**
- Astrix Security claims to have analyzed 5,200+ open-source MCP servers ([2025 report](https://astrix.security/learn/blog/state-of-mcp-server-security-2025/)):
  - 88% require credentials
  - 53% use insecure static secrets
  - Only 8.5% use OAuth

**⚠️ RELIABILITY WARNING:** These specific numbers come from a single vendor report. Astrix Security sells security solutions, giving them incentive to emphasize the problem's severity. The methodology was not independently verified. The general problem (credential management in MCP) is plausible, but the specific statistics should not be cited as fact.

**Who Has This Problem:** Likely enterprises that can't have API keys scattered across developer laptops, but magnitude is uncertain.

**Vendor Claims:**
- Runlayer: Offers SSO/SCIM integration with Okta, Entra
- MCP Manager: Identity management for people and AI agents
- Lunar.dev: "Basic API key and OAuth support"

---

### 3. Token Consumption: Tools Eat Your Context Window

**Reliability: MEDIUM-HIGH**

**The Plain-Language Problem:** Before Claude or another AI can do any work, it loads tool definitions. These definitions consume tokens. Users report significant token consumption just loading MCP tools.

**Well-Sourced Evidence:**
- User report: "178k/200k tokens (89%) consumed, with MCP tools alone using 63.7k tokens (31.8%)" ([Scott Spence blog](https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code)) ✓ Real developer measurement
- Speakeasy built dynamic toolsets specifically to address this ([blog post](https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2)) ✓ Tool created to solve this

**Unverified Claims:**
- "Cursor and Cline cap concurrent tools at 40" - ⚠️ Not verified against Cursor/Cline documentation

**Who Has This Problem:** Power users with many MCP servers enabled simultaneously.

**What Vendors Say:** Lunar.dev mentions "rate limiting" but none specifically address token consumption optimization.

---

### 4. Configuration Hell: Manual JSON Editing Across Multiple Clients

**Reliability: HIGH** ✓

**The Plain-Language Problem:** Every AI client (Claude Desktop, Cursor, VS Code, etc.) has its own config file. To use the same MCP server in all of them, you manually edit each config. Change a setting? Edit 5 files.

**Well-Sourced Evidence:**
- This is a structural fact about how MCP works - each client maintains its own configuration ✓
- DEV Community: "FastMCP's proxy capabilities transform MCP server management from a fragmented, per-client configuration nightmare into a streamlined, centralized approach" ([source](https://dev.to/alexretana/streamlining-mcp-management-bundle-multiple-servers-with-fastmcp-proxies-n3i)) ✓
- MCPM (mcpm.sh) exists specifically because: "A developer who works across a number of IDEs and CLIs will quickly find it frustrating to have to manage a multiplicity of MCP server definitions" ✓ Tool created to solve this

**Who Has This Problem:** Developers using multiple AI coding tools (Cursor + Claude Code + VS Code, etc.)

**What Vendors Offer:**
- MCP Manager (mcpmanager.ai): "Deploy with clicks, not code"
- MCPM: CLI-based centralized management with profiles
- Runlayer: Works with "all 300+ MCP clients"

---

### 5. Restart Hell: Lose Your Context Every Time You Change Config

**Reliability: MEDIUM-HIGH**

**The Plain-Language Problem:** When you update an MCP server or change its config, you have to restart your AI client. This loses your conversation context and breaks your workflow.

**Well-Sourced Evidence:**
- VS Code Issue #245018: "When working on local servers...getting VS Code to restart the server requires going into the command list servers, clicking into the server, and restarting there, which is very cumbersome" ([source](https://github.com/microsoft/vscode/issues/245018)) ✓ Real GitHub issue
- Multiple hot-reload tools created specifically to solve this (Reloaderoo, MCP-Server-HMR) ✓ Tools exist

**Unverified Claims:**
- "30-60 seconds lost per config change" - ⚠️ Claimed without specific source

**Who Has This Problem:** Anyone actively developing MCP servers.

**Vendor Response:** None of the three specifically address hot-reload. This is more of a client-side problem.

---

### 6. Black Box Debugging: No Visibility Into What's Happening

**Reliability: HIGH** ✓

**The Plain-Language Problem:** When an MCP tool doesn't work, you have no idea why. There's no logging, no tracing, no way to see what the AI sent to the tool or what the tool returned.

**Well-Sourced Evidence:**
- Moesif: "These servers are increasingly being labeled as black boxes—opaque components that handle critical tasks but offer little visibility" ([source](https://www.moesif.com/blog/monitoring/model-context-protocol/How-to-Setup-Observability-For-Your-MCP-Server-with-Moesif/)) ✓
- MCPShark traffic inspector created because "tools don't behave as expected" ([HN announcement](https://news.ycombinator.com/item?id=46220577)) ✓ Tool created to solve this
- HN user bsenftner: "The existing documentation is a confusing mess...very thin on actual conceptual explanation" ✓ Real user comment

**Who Has This Problem:** Anyone debugging MCP integrations.

**What Vendors Offer:**
- MCP Manager: "Verbose, end-to-end logs of all your organization's MCP traffic"
- Lunar.dev: "Track every LLM call and tool action with full visibility into token usage, cost, latency, and errors"
- Runlayer: "Full visibility into MCP usage across all teams and clients"

**Note:** Vendor claims about observability were not independently verified. See competitive strategy document for audit of actual vs. claimed observability features.

---

### 7. Enterprise Access Control: No Fine-Grained Permissions

**Reliability: MEDIUM**

**The Plain-Language Problem:** Traditional security grants access to entire applications. But an MCP server might expose 10 different tools—some safe, some dangerous. There's no built-in way to say "User X can use the 'read' tool but not the 'delete' tool."

**Well-Sourced Evidence:**
- Cerbos: "MCP requires much finer control since individual tools within an MCP server may need different permissions" ([source](https://www.cerbos.dev/blog/mcp-authorization)) ✓ Independent blog
- Christian Posta: "The new MCP Authorization specification is a mess for Enterprise" ([blog](https://blog.christianposta.com/the-updated-mcp-oauth-spec-is-a-mess/)) ✓ Independent blog

**Mixed with Vendor Marketing:**
- Runlayer example: "Scope bloated APIs like GitHub's 106 tools down to 4 safe ones" - ⚠️ Vendor marketing claim

**Who Has This Problem:** Enterprises with compliance requirements (HIPAA, SOC2, etc.)

**What Vendors Offer:**
- Runlayer: "Fine-grained permissions per tool and resource" + scopes entire APIs down to approved tools
- MCP Manager: "Granular access and permission controls"
- Lunar.dev: "Policies such as Access Control Lists (ACLs) and role-based profiles restrict which tools and methods an agent can call"

---

### 8. Security Review Bottleneck: Every New Server Needs Vetting

**Reliability: LOW** ⚠️

**The Plain-Language Problem:** In enterprises, security teams must approve each new MCP server before developers can use it. With many servers available, security can't keep up. Developers wait, security is overwhelmed, or people circumvent controls.

**Evidence (primarily vendor marketing):**
- Lunar.dev HiBob case study: "Each new MCP server required security review before being approved for use..." ([source](https://www.lunar.dev/post/hibob-scales-ai-and-mcp-adoption-without-slowing-engineering)) ⚠️ Vendor case study
- Runlayer: Signed "dozens of customers" in 4 months including 8 unicorns ([TechCrunch](https://techcrunch.com/2025/11/17/mcp-ai-agent-security-startup-runlayer-launches-with-8-unicorns-11m-from-khoslas-keith-rabois-and-felicis/)) ⚠️ Press reporting vendor claims

**⚠️ RELIABILITY WARNING:** This problem is supported primarily by vendor case studies and marketing claims. While the problem is plausible (enterprise security review processes exist), we have no independent verification that MCP-specific security review is a significant bottleneck. The vendor customer claims suggest market demand but don't prove the problem's severity.

**Who Has This Problem:** Possibly companies with security policies that require vendor/tool approval, but magnitude is uncertain.

**What Vendors Offer:**
- Runlayer: Pre-vetted server registry, every server "scored before it reaches your organization"
- MCP Manager: "AI-powered risk analysis"
- Lunar.dev: "MCP evaluation sandbox" (enterprise only)

---

## Vendor Comparison Table

| Problem | Runlayer | MCP Manager (mcpmanager.ai) | Lunar.dev |
|---------|----------|---------------------------|-----------|
| **Security threat detection** | Custom detectors for tool poisoning, shadowing, injection | Prompt sanitizing, anti-mimicry, rug pull protection | References OWASP, general threat detection |
| **Identity/SSO** | Okta, Entra, SCIM | Okta, Entra | "Basic OAuth support" |
| **Fine-grained permissions** | Per-tool permissions, scope reduction | Granular access controls | ACLs, role-based profiles |
| **Observability** | Full logging, adoption metrics | End-to-end logs with correlation IDs | Prometheus metrics, audit trails |
| **Server registry** | 18,000+ servers vetted and scored | Not emphasized | Aggregation of servers |
| **Deployment** | Self-hosted (Terraform/Helm) or SaaS | Managed deployment service | Self-hosted in customer VPC |
| **Sandbox/Testing** | Not mentioned | Not mentioned | MCP evaluation sandbox (enterprise) |
| **Named customers** | Gusto, dbt Labs, Instacart, Opendoor, Ramp, Rippling | Amazon, Duolingo, NASA, DoorDash (claimed) | HiBob |
| **Funding** | $11M seed (Khosla, Felicis) | Bessemer, General Catalyst, M13, Craft | Not disclosed |
| **Open source** | No | No | Yes (MCPX core) |

**Note:** This table reflects vendor claims. Observability capabilities were investigated further and found to be less differentiated than marketing suggests—see competitive strategy document.

---

## Problems That Are Probably Over-Hyped

### "10% of MCP Servers Are Malicious"
Runlayer claims this but provides no source. While there are documented vulnerabilities, "malicious" implies intentional harm. More accurate: many servers have unintentional security flaws.

### "Double the Accuracy of Industry Best"
Runlayer claims their threat detection has "roughly double the accuracy than the industry best"—no methodology or baseline provided.

### "Devastating Consequences"
MCP Manager uses dramatic language about "devastating consequences" but the documented incidents (GitHub prompt injection, Asana data exposure) were fixed before exploitation.

### Specific Vulnerability Statistics
The "43% vulnerable" (Backslash) and "88%/53%" (Astrix) statistics come from vendors with commercial interest in the problem being severe. Treat with skepticism.

---

## What You Can Reasonably Trust

**HIGH confidence (multiple independent sources):**
- Configuration complexity is a real structural problem (Problem 4)
- Debugging visibility is a real pain point (Problem 6)
- Token consumption is measurable and documented (Problem 3)
- Restart/reload friction exists (Problem 5)

**MEDIUM confidence (real but magnified):**
- Security vulnerabilities exist (Problem 1) - but severity stats are vendor-sourced
- Access control gaps are real (Problem 7) - but mixed with marketing

**LOW confidence (primarily vendor claims):**
- Specific statistics about vulnerability rates or credential usage (Problem 2)
- Enterprise security review as a major bottleneck (Problem 8)

---

## Who Actually Needs an MCP Gateway?

Based on the **high-confidence evidence only**:

**Probably need one:**
- Teams with configuration sprawl across multiple AI clients (Problem 4 - verified)
- Developers needing visibility into MCP traffic for debugging (Problem 6 - verified)
- Power users hitting context limits from tool definitions (Problem 3 - verified)

**Possibly need one (unverified demand):**
- Enterprises with compliance requirements - the need is plausible but our evidence is vendor case studies
- Organizations with security review bottlenecks - plausible but unverified

**Can probably skip:**
- Individual developers experimenting with MCP
- Small teams using only well-vetted servers
- Projects without sensitive data exposure

---

## Key Sources

### High-Quality Sources (Independent, Non-Vendor)
- [GitHub Issue #630: Server terminology security](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/630)
- [VS Code Issue #245018: Server restart during development](https://github.com/microsoft/vscode/issues/245018)
- [HN: Everything wrong with MCP](https://news.ycombinator.com/item?id=43676771)
- [HN: Model Context Protocol](https://news.ycombinator.com/item?id=42237424)
- [Scott Spence: Optimising MCP Server Context Usage](https://scottspence.com/posts/optimising-mcp-server-context-usage-in-claude-code)
- [Christian Posta: MCP Auth Spec Critique](https://blog.christianposta.com/the-updated-mcp-oauth-spec-is-a-mess/)
- [Cerbos: MCP Authorization](https://www.cerbos.dev/blog/mcp-authorization)
- [DEV Community: Streamlining MCP Management](https://dev.to/alexretana/streamlining-mcp-management-bundle-multiple-servers-with-fastmcp-proxies-n3i)
- [Moesif: MCP Server Observability](https://www.moesif.com/blog/monitoring/model-context-protocol/How-to-Setup-Observability-For-Your-MCP-Server-with-Moesif/)

### Lower-Quality Sources (Vendor Reports, Marketing)
- [Astrix Security: State of MCP Server Security 2025](https://astrix.security/learn/blog/state-of-mcp-server-security-2025/) - ⚠️ Vendor report
- [Backslash Security: Hundreds of MCP Servers Vulnerable](https://www.backslash.security/blog/hundreds-of-mcp-servers-vulnerable-to-abuse) - ⚠️ Vendor report
- [Runlayer $11M Raise Announcement](https://www.runlayer.com/blog/runlayer-raises-11m-to-scale-enterprise-mcp-infrastructure) - ⚠️ Vendor marketing
- [TechCrunch: Runlayer Launch](https://techcrunch.com/2025/11/17/mcp-ai-agent-security-startup-runlayer-launches-with-8-unicorns-11m-from-khoslas-keith-rabois-and-felicis/) - ⚠️ Press reporting vendor claims
- [MCP Manager Blog: MCP Gateway](https://mcpmanager.ai/blog/mcp-gateway/) - ⚠️ Vendor marketing
- [Lunar.dev: HiBob Case Study](https://www.lunar.dev/post/hibob-scales-ai-and-mcp-adoption-without-slowing-engineering) - ⚠️ Vendor case study

### Verified Technical Sources
- [JFrog: CVE-2025-6514 Analysis](https://jfrog.com/blog/2025-6514-critical-mcp-remote-rce-vulnerability/) - ✓ Real CVE analysis
- [Speakeasy: Reducing MCP token usage by 100x](https://www.speakeasy.com/blog/how-we-reduced-token-usage-by-100x-dynamic-toolsets-v2) - ✓ Technical solution to documented problem

---

## Additional Notes: MCP Manager Ecosystem

There are multiple products using the "MCP Manager" name:

| Product | URL | Focus |
|---------|-----|-------|
| MCP Manager (Enterprise) | mcpmanager.ai | Enterprise security gateway |
| MCP Manager (Desktop) | mcpmanager.app | Visual desktop configuration tool |
| MCPM | mcpm.sh | CLI package manager with router |
| petiky/mcp-manager | GitHub | Visual desktop client (macOS) |
| MCP Manager | Microsoft Store | Windows configuration sync |

The enterprise product (mcpmanager.ai) is the direct competitor to Runlayer and Lunar.dev. The others are developer tools for individual configuration management.

---

## Document History

- Initial research: Compiled from vendor websites, press coverage, user discussions
- Reliability audit: Each claim reviewed for source quality; ratings added
- Key finding from audit: Problems 2 and 8 were primarily supported by vendor marketing, not independent sources
