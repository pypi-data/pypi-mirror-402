# Tool Discovery Pipeline

## Tasks
- [ ] Extend `_discover_identity_for_upstream` flow to also request `tools/list` after a successful handshake and cache `{server_alias: [tool]}` alongside a `last_refreshed` timestamp.
- [ ] Persist discovery results on `ConfigEditorScreen` (e.g., `self.server_tool_map`) and expose helper accessors that return the catalog for the active server only.
- [ ] Surface the cached tool metadata through `PluginActionsMixin._handle_plugin_configure` so the Tool Manager modal receives a `discovered_tools` payload when launched from a server row.
- [ ] When the modal is triggered without a server context, short-circuit with a guardrail message directing the user to configure Tool Manager per server.

## Open Questions
- How do we handle transports that cannot run `tools/list` (HTTP, drafts)? Plan: tag discovery as unavailable, supply an empty list, and let the modal show a warning banner while still rendering manual entries.
- Should discovery be refreshed on demand from the modal (e.g., refresh button) or rely on the background worker? Initial version will rely on the existing cadence but keep the timestamp so we can bolt on a refresh control later.

## Risks & Mitigations
- **Long-running discovery**: ensure we await the `tools/list` call with a timeout similar to handshake and fail gracefully with the warning state above.
- **Large tool lists**: cap the cached payload to what the modal can render efficiently; consider streaming later if needed.
