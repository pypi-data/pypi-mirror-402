# Tool Manager UI Refresh

Goal: replace the free-form tool array editor with a discovery-powered checklist while preserving JSON schema compatibility and keyboard workflows.

## Phases
- Tool discovery cache exposed to the PluginConfig modal
- Purpose-built tool selection widget powering the `tools` array
- Save/reset flows + schema validation integration
- QA: UX polish, focus handling, tests

## Dependencies & Notes
- Leverage existing handshake workers in `ConfigEditorScreen` for discovery
- Continue to respect manual tool entries for undiscovered tools
- Modal must remain usable for global and per-server contexts
