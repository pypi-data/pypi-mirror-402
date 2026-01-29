# GitHub Stars Launch Blueprint (Gatekit v0.1.0 Soft Launch)

  Purpose: Provide a checklist-driven strategy to earn early GitHub stars and feedback
  while shipping a solid infrastructure-only v0.1.0 that is not yet broadly useful.

  Scope: Soft launch now; hard launch after 2-3+ iterative releases.

  ## What matters for GitHub stars (short version)
  - Stars influence discovery (Trending and Explore). Trending explicitly tracks stars in daily/weekly/monthly windows.
  - Star velocity in a short window beats slow drip if you want a Trending shot.
  - Repo creation date matters far less than a concentrated burst of attention.

  References
  - https://github.com/trending
  - https://docs.github.com/en/get-started/exploring-projects-on-github/saving-repositories-with-stars
  - https://docs.github.com/en/get-started/exploring-projects-on-github/finding-ways-to-contribute-to-open-source-on-github
  - https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-
  your-repository-with-topics
  - https://blog.cwrichardkim.com/how-to-get-hundreds-of-stars-on-your-github-project-345b065e20a2
  - https://blog.innmind.com/how-to-launch-on-product-hunt-in-2026/

  -------------------------------------------------------------------------------

  ## Positioning (soft launch, infra-first)
  - Label v0.1.0 as "Developer Preview" or "Pre-release".
  - Set expectations in README and release notes:
    - "This is stable infra, not a complete product yet."
    - "Looking for feedback from early adopters."
    - "Who this is for right now" (short list).
    - "Not yet supported" (short list).
  - Publish a mini-roadmap for v0.2/v0.3.

  ## Soft launch goals
  - 5-20 high-signal early adopters.
  - 25-100 real stars to seed credibility.
  - 2-3 onboarding failures captured and fixed fast.

  -------------------------------------------------------------------------------

  ## Repo readiness checklist (pre-outreach)

  Clarity
  - 1-sentence value statement at top of README.
  - 3-bullet "why now" summary.
  - 5-10 minute "first success" path validated.

  Trust signals
  - License + CONTRIBUTING.md.
  - v0.1.0 release notes with "preview" disclaimer.
  - Roadmap linked from README.
  - 10-15 topics added for discoverability.

  Onboarding
  - Quickstart validated on a clean machine.
  - Guided config path (no default config shipped).
  - One minimal example flow documented.

  Feedback intake
  - GitHub Discussions enabled.
  - Two prompts:
    - "What is your use case?"
    - "Where did setup break or feel unclear?"
  - Issue templates:
    - Bug / setup failure
    - Feature request / roadmap item

  -------------------------------------------------------------------------------

  ## Soft launch execution (7-14 days)

  Day 0
  - Publish v0.1.0 as pre-release.
  - README positioning updated.
  - Discussions prompts live.

  Day 1-3 (private outreach)
  - Invite 10-20 targeted builders.
  - Ask for a single focused action: "Try quickstart, report first break."

  Day 4-7 (fast iteration)
  - Ship v0.1.1/v0.1.2 with quick fixes.
  - Post "you said / we did" in the same threads.

  Day 8-14 (second wave)
  - Invite a smaller new group using improvements as proof.

  Success metrics
  - 5+ detailed onboarding reports.
  - 2+ real workflows in progress.
  - 25-100 stars from real users.

  -------------------------------------------------------------------------------

  ## Early adopter channels (AI + MCP focus)

  Targeted and receptive (soft launch)
  - GitHub repos and Discussions tagged with "mcp", "model-context-protocol",
    "ai-tools", "agent-frameworks".
  - Maintainers of MCP-adjacent repos you integrate with.
  - Active contributors in adjacent AI infra/tooling repos (personal invites).
  - Small communities you already participate in (Discord/Slack/email lists).

  Defer for hard launch
  - LinkedIn, X/Twitter, HN, Product Hunt, broad subreddits, large newsletters.

  -------------------------------------------------------------------------------

  ## 3-Week Community Posting Plan

  Strategy: Start with smallest communities, scale up. Target only MCP-aware
  communities to avoid market education overhead. Two posts per week, paired
  to minimize audience overlap.

  ### Community Priority (MCP-aware, by size)

  | Community      | Size   | Knows MCP | Week | Notes                        |
  |----------------|--------|-----------|------|------------------------------|
  | r/mcp          | ~1K    | Yes       | 1    | Core MCP community           |
  | r/codex        | ~1K    | Yes       | 1    | OpenAI ecosystem             |
  | MCP Discord    | ~11K   | Yes       | 3    | Mix of hobbyists + production|
  | r/ClaudeCode   | ~49K   | Yes       | 2    | Claude Code specific         |
  | r/cursor       | ~73K   | Yes       | 3    | Cursor IDE users             |
  | r/LLMDevs      | ~125K  | Mostly    | 2    | General LLM developers       |

  Deferred (needs MCP education):
  - r/selfhosted (~650K) - would need to explain what MCP is
  - r/LocalLLaMA (~600K) - mixed awareness
  - r/ClaudeAI (~386K) - casual users

  ### Week 1: Smallest Communities (Different Ecosystems)

  Monday/Tuesday: r/mcp (~1K)
  - Title: "Built an open-source MCP gateway - looking for feedback"
  - Body: Gatekit sits between your client and servers. Adds audit logging,
    tool filtering, and has a plugin system for custom middleware. Curious
    if others have this need. What would you want from something like this?
  - Link: GitHub

  Thursday/Friday: r/codex (~1K)
  - Title: "Anyone using MCP servers with Codex? Built a gateway for visibility"
  - Body: Wanted to see what tools were being called and filter out ones I
    didn't need. Built an open-source gateway with audit logging and a plugin
    system. Works with Codex, Claude Code, Cursor, etc.
  - Link: GitHub

  Why orthogonal: r/mcp skews Anthropic/Claude. r/codex is OpenAI ecosystem.

  ### Week 2: Medium Communities (Different Focus)

  Monday/Tuesday: r/ClaudeCode (~49K)
  - Title: "What's your MCP visibility story?"
  - Body: Running several MCP servers with Claude Code. Realized I had no idea
    what was actually being called or when. Built Gatekit - open source gateway
    with audit logging and tool filtering. Anyone else care about this?
  - Link: GitHub

  Thursday/Friday: r/LLMDevs (~125K)
  - Title: "Built an MCP gateway with a plugin system - curious what you'd extend"
  - Body: Gatekit intercepts traffic between MCP clients and servers. Built-in
    plugins for audit logging, tool filtering, PII detection. The interesting
    part is writing your own - ~50 lines of Python. What would you build?
  - Link: GitHub

  Why orthogonal: r/ClaudeCode is product-specific. r/LLMDevs is broader.

  ### Week 3: Remaining MCP-Aware Communities

  Monday/Tuesday: MCP Discord (~11K)
  - Post in appropriate channel (casual intro)
  - Body: Hey all - built an open-source MCP gateway called Gatekit. Sits
    between your client and servers, adds audit logging, tool filtering, and
    has a plugin system. Looking for feedback. [GitHub link]

  Thursday/Friday: r/cursor (~73K)
  - Title: "How are you managing MCP servers in Cursor?"
  - Body: Running a few MCP servers and wanted more visibility into what's
    happening. Built a gateway that logs everything and lets me filter tools.
    Anyone else thinking about this?
  - Link: GitHub

  Why this timing: MCP Discord is 2 weeks after r/mcp (overlap buffer).
  r/cursor is 1 week after r/ClaudeCode (different product focus).

  ### Post-Week 3: Follow-Up Strategy

  If clear winners emerge:
  - Return with "you asked, I built" posts when shipping requested features
  - Become a regular contributor, not just a promoter

  If no signal:
  - Don't force it
  - Put Gatekit in maintenance mode
  - Revisit in 3-6 months when market may have evolved

  ### Release-to-Post Mapping

  | Release Type              | Post?  | Where?                              |
  |---------------------------|--------|-------------------------------------|
  | Bug fixes only            | No     | GitHub release notes only           |
  | Minor feature             | No     | Mention where already active        |
  | Feature someone requested | Yes    | Return to that specific community   |
  | Major new capability      | Yes    | Pick 1-2 communities, don't blast   |
  | Breaking change           | Yes    | Everywhere you've posted (heads up) |

  ### Anti-Spam Rules

  - Max 1 post per community per 3 weeks (unless responding to requests)
  - Never post same content to multiple communities in same week
  - If post flops (<5 comments), wait 6+ weeks before retrying that community
  - Engage in comments for several days after posting - don't post and ghost
  - Contribute non-promotional comments before and after your posts

  -------------------------------------------------------------------------------

  ## Star growth flywheel (hard launch later)

  Pre-launch (2-4 weeks before hard launch)
  - Tighten README and quickstart.
  - Add demo video/gif or screenshots.
  - Publish 1-2 external posts (dev.to, blog, etc.).
  - Build a launch list from early adopters.

  Launch day
  - Announce inside a 24-hour window (2-3 waves).
  - Encourage stars only after quickstart success.
  - Respond to issues quickly and publicly.

  Post-launch (weeks 1-4)
  - Ship visible improvements frequently.
  - Post "what changed since launch" updates.
  - Sustain star velocity across the week for weekly Trending.

  -------------------------------------------------------------------------------

  ## Guardrails (avoid star growth mistakes)

  Avoid
  - Ask-for-stars spam or artificial spikes.
  - Overpromising feature availability.
  - Broad announcements before onboarding is reliable.

  Do
  - Be explicit about "preview" status and missing pieces.
  - Ship fast, public fixes.
  - Keep the "first success" path working every time.

  -------------------------------------------------------------------------------

  ## Gatekit-specific checklist (soft launch)

  - v0.1.0 marked pre-release.
  - README: Developer Preview + Who this is for + Not yet sections.
  - Roadmap for v0.2/v0.3.
  - Discussions prompts live.
  - Quickstart verified with guided config.
  - Topics added: mcp, proxy, policy, ai-tools, agent, gateway, etc.
  - Early adopter list (10-20) with personal outreach.

  -------------------------------------------------------------------------------

  ## Notes
  - Soft launch is for product truth and high-signal feedback.
  - Hard launch is for concentrated momentum and broad distribution.
  - Treat the next 2-3 months as a public build cycle.