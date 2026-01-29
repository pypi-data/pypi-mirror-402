# Plugin Use Cases for Developer Adoption

**Status:** Living document - add use cases as discovered
**Purpose:** Capture high-value plugin use cases that drive developer adoption
**Audience:** Internal product strategy

## Strategic Context

The go-to-market strategy depends on developers finding immediate value in Gatekit's plugin architecture. Generic "manage servers and tools" isn't compelling enough. The killer app must come from the ability to intercept and transform MCP traffic.

### Core Insight

**Gatekit gives you control over MCP interactions without modifying the MCP server.**

This is the API gateway / reverse proxy pattern applied to MCP. When you:
- Can't modify the MCP server (it's third-party or another team owns it)
- Need to add business logic the server doesn't support
- Want to transform data for your specific use case

...you need a layer in between. That's Gatekit's defensible position.

---

## High-Value Use Cases

### Tier 1: Build Now (High impact, demo-able, validates strategy)

#### 1. Response Pruning / Field Filtering

**The Pain:** MCP servers often return way more data than needed. A database query returns 50 columns when you need 3. A file read returns the entire file when you need the first 100 lines. This wastes context window and money.

**Plugin Behavior:**
```yaml
plugins:
  middleware:
    internal-db:
      - handler: "response_filter"
        config:
          tools:
            - tool: "query_database"
              max_rows: 50
              include_fields: ["id", "name", "status", "assigned_to"]
              exclude_fields: ["internal_notes", "raw_json"]
            - tool: "read_document"
              max_chars: 10000
              truncation_message: "[Document truncated - {remaining} chars omitted]"
```

**Why This Matters:**
- Context window is precious and expensive
- LLMs get confused by irrelevant data
- You can't always modify the MCP server to return less

**Demo Potential:** Show a 50KB response being pruned to 2KB. Show the agent performing better with cleaner context.

**Validation Questions:**
- [ ] Can we find developers who have this problem today?
- [ ] What MCP servers return excessively large responses?
- [ ] Is there measurable improvement in agent reasoning with pruned responses?

---

#### 2. Request Augmentation / Context Injection

**The Pain:** The LLM doesn't know about your internal context - current user, their permissions, their team, their project. Every request needs this context, but you don't want to prompt-engineer it into every interaction.

**Plugin Behavior:**
```yaml
plugins:
  middleware:
    jira-server:
      - handler: "request_augment"
        config:
          inject_from_env:
            - param: "reporter"
              env_var: "CURRENT_USER_EMAIL"
            - param: "project_key"
              env_var: "CURRENT_PROJECT"
          inject_static:
            - param: "organization_id"
              value: "acme-corp"
          inject_from_header:
            - param: "user_permissions"
              header: "X-User-Permissions"
```

**Why This Matters:**
- Every tool call needs user context for proper authorization
- Without this, agents operate without identity
- Alternative is complex prompt engineering that's fragile

**Real Scenario:** Agent creates Jira tickets. Without context injection, you'd need to tell the LLM "always set reporter to john@acme.com" in the system prompt. With context injection, it happens automatically and can change per-session.

**Validation Questions:**
- [ ] How do internal IT teams currently handle user context in agentic systems?
- [ ] What parameters are most commonly needed for injection?

---

#### 3. Dry Run / Simulation Mode

**The Pain:** When developing agentic systems, you want to see what the agent *would* do without actually doing it. You don't want test runs creating real tickets, sending real emails, or modifying real databases.

**Plugin Behavior:**
```yaml
plugins:
  middleware:
    _global:
      - handler: "dry_run"
        config:
          enabled: true  # Toggle for dev vs prod
          intercept_methods:
            - "tools/call"
          write_tools:
            - "create_ticket"
            - "send_email"
            - "update_record"
            - "delete_*"  # Glob pattern
          mock_response:
            success: true
            message: "[DRY RUN] Would have executed: {tool_name}"
            simulated_id: "dry-run-{uuid}"
```

**Why This Matters:**
- Safe development and testing
- Show stakeholders what the agent will do before going live
- Catch dangerous behaviors before they cause damage

**Demo Potential:** Show an agent "sending emails" in dry run mode. Show the audit log of what would have happened. Toggle dry run off and show real execution.

**Validation Questions:**
- [ ] How do teams currently test agentic systems safely?
- [ ] What's the current workaround (separate test environments, manual review)?

---

### Tier 2: Build Soon (Clear value, moderate complexity)

#### 4. Intelligent Caching

**The Pain:** Agents are often redundant. They'll ask the same question multiple times, make the same API call repeatedly, or re-fetch data they already have. This wastes time and API costs.

**Plugin Behavior:**
```yaml
plugins:
  middleware:
    expensive-api:
      - handler: "cache"
        config:
          ttl_seconds: 300  # 5 minute cache
          cache_tools:
            - tool: "search_documents"
              key_params: ["query", "filters"]
            - tool: "get_user_profile"
              key_params: ["user_id"]
          invalidate_on:
            - tool: "update_user_profile"
              invalidates: ["get_user_profile"]
```

**Why This Matters:**
- Reduces API costs (real money)
- Reduces latency (better UX)
- Prevents hammering internal systems

**Advanced Version:** Semantic caching - "find documents about Q3 revenue" and "search for Q3 financial reports" could hit the same cache entry if embeddings are similar enough.

**Validation Questions:**
- [ ] How redundant are typical agent tool calls? (Need data)
- [ ] What's the cost impact of caching for heavy API users?

---

#### 5. Loop Detection and Breaking

**The Pain:** Agents sometimes get stuck in loops - making the same request repeatedly, retrying failed operations endlessly, or oscillating between states.

**Plugin Behavior:**
```yaml
plugins:
  middleware:
    _global:
      - handler: "loop_breaker"
        config:
          window_seconds: 60
          max_identical_requests: 3
          max_similar_requests: 5  # Based on param similarity
          on_loop_detected:
            action: "block"
            inject_response:
              error: "Loop detected - same request made {count} times in {window}s"
              suggestion: "Try a different approach or ask for clarification"
```

**Why This Matters:**
- Agents can burn through API limits quickly when looping
- Loops indicate the agent is stuck and needs intervention
- Without detection, loops can run for a long time before anyone notices

**Validation Questions:**
- [ ] How common are agent loops in practice?
- [ ] What triggers loops (failed operations, unclear instructions)?

---

### Tier 3: Build Later (Enterprise-oriented, less dev-adoption value)

#### 6. Response Enrichment / Joining

**The Pain:** An agent gets data from System A (user IDs) but needs correlated data from System B (user names, emails). Currently this requires multiple tool calls or custom code.

**Plugin Behavior:**
```yaml
plugins:
  middleware:
    crm-server:
      - handler: "enrich_response"
        config:
          enrichments:
            - tool: "list_deals"
              enrich_field: "owner_id"
              lookup:
                source: "user_directory"  # Another MCP server
                tool: "get_user"
                param: "user_id"
                return_fields: ["name", "email", "department"]
                as_field: "owner_details"
```

**Why This Matters:**
- Reduces round trips (agent doesn't need to make follow-up calls)
- Cleaner data for LLM reasoning
- Can't always modify the source MCP server to join data

**Real Scenario:** CRM returns deal records with `owner_id: "u123"`. Plugin enriches to `owner_details: {name: "Jane Smith", email: "jane@acme.com"}`. Agent can now reason about the deal without another lookup.

---

#### 7. Cost Attribution and Tracking

**The Pain:** Who's using the AI tools? Which teams are generating costs? Internal chargebacks require attribution.

**Plugin Behavior:**
```yaml
plugins:
  middleware:
    _global:
      - handler: "cost_tracker"
        config:
          cost_model:
            - tool: "*"
              base_cost: 0.001  # Base cost per call
            - tool: "search_*"
              cost_per_call: 0.01
            - tool: "generate_*"
              cost_per_call: 0.05
          attribution:
            from_env: "TEAM_ID"
            from_header: "X-Project-ID"
          output:
            file: "costs/{date}.jsonl"
            webhook: "https://internal.acme.com/cost-webhook"
```

**Why This Matters:**
- Finance wants to know where AI spending is going
- Teams need accountability
- Usage data informs capacity planning

---

#### 8. Graceful Degradation / Fallback

**The Pain:** What happens when an MCP server is down or slow? The agent fails ungracefully.

**Plugin Behavior:**
```yaml
plugins:
  middleware:
    primary-db:
      - handler: "fallback"
        config:
          timeout_ms: 5000
          on_timeout:
            fallback_server: "replica-db"
          on_error:
            fallback_response:
              message: "Primary database unavailable. Please try again later."
              cached_data: true  # Return stale cached data if available
          circuit_breaker:
            failure_threshold: 5
            reset_timeout_seconds: 60
```

**Why This Matters:**
- Production reliability
- Users don't see cryptic errors
- Agents can continue working with degraded functionality

---

## Additional Use Case Ideas (To Be Developed)

These emerged from brainstorming but need more thought:

- **Error Enhancement** - Translate cryptic MCP server errors to helpful messages
- **Backward Compatibility** - Translate between MCP server response format versions
- **Multi-tenant Isolation** - Inject tenant ID, filter responses by tenant
- **Request Batching** - Collect similar requests, batch them, distribute responses
- **Rate Limiting with Intelligence** - Not just "5/sec" but "detect loops and break them"
- **Semantic Caching** - Similar queries return cached results (requires embeddings)
- **Response Summarization** - Use LLM to summarize large responses before passing to main LLM

---

## Target Personas

### Primary: Internal IT Developer Building Agentic Systems

**Context:**
- Building AI tools for internal use
- Working with internal systems (databases, APIs, wikis)
- Dealing with corporate data (some of which is sensitive)
- Under pressure to deliver value quickly
- May not be AI/ML experts
- May have constraints on what they can change (can't modify the MCP server)

**Their specific pain points:**
- "The MCP server returns too much data"
- "I can't modify the MCP server to add the context I need"
- "I need to comply with corporate data policies"
- "I need to track usage for chargebacks"
- "I need to test safely"

### Secondary: Developer Using Claude Code / Cursor with Multiple MCP Servers

**Context:**
- Power user of AI coding assistants
- Has multiple MCP servers configured
- Experiences context bloat, tool confusion
- Values productivity optimization

**Their specific pain points:**
- "Too many tools in my context"
- "Tool names are confusing"
- "I want to see what my agent is doing"

---

## Validation Strategy

For each use case, validate:

1. **Problem exists** - Can we find people who have this problem today?
2. **Problem is painful** - Is it painful enough to justify gateway setup?
3. **Solution works** - Does the plugin actually solve the problem?
4. **Demo is compelling** - Can we show before/after that resonates?

### Where to look for validation:
- MCP Discord - what are people complaining about?
- Claude Code GitHub issues - what pain points come up?
- Twitter/X - search "MCP servers" + frustration keywords
- Direct outreach to developers building with MCP

---

## Competitive Considerations

### Risk: Anthropic/OpenAI Build This Natively

Claude Code or similar tools could add:
- Tool filtering/renaming
- Basic caching
- Audit logging

**Our differentiation:**
- Plugin architecture (they won't let you inject custom logic)
- Vendor-neutral (works with any MCP client)
- Enterprise features (compliance, central management)
- Open source core (transparency, no lock-in)

### Risk: Agentic Frameworks Have Overlapping Features

LangChain, CrewAI, etc. may have observability/guardrails.

**Our differentiation:**
- MCP-native (they're framework-specific)
- Works at transport layer (no code changes needed)
- Can sit in front of any MCP server regardless of framework

