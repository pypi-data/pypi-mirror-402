# WBAL → ACP Compatibility Plan

Goal: expose WBAL agents/environments over the Agent Communication Protocol (ACP) without disrupting current APIs. Do this via adapters that translate WBAL’s internal structures to/from ACP envelopes.

## Concept Mapping
- Agent → ACP Agent; exposes capabilities (tools) and run loop.
- Environment → Context/Session state backing an ACP session; holds working directory + persistence.
- Message/history → ACP Messages with roles (user/assistant/system), ids, timestamps, and content blocks.
- @tool/@weaveTool → ACP Tool definitions (name, description, JSON schema inputs/outputs).
- Tool calls/results → ACP ToolCall/ToolResult with correlation ids and status.

## Adapter Surfaces
- Message adapter: wrap WBAL messages in ACP envelopes; parse inbound ACP messages into WBAL message dicts. Preserve message ids, timestamps, session id, and channel.
- Tool definition adapter: export tool metadata from `getToolDefinitions()` into ACP Tool descriptors (including input schema, return shape, optional auth/capabilities).
- Tool call adapter: accept ACP ToolCall objects, invoke `_tool_callables`, emit ACP ToolResult with outcome (`success`/`error` + message) and any payload.
- Session/context: propagate ACP session/context ids through Environment state; include in observations and persistence.
- Error/status: normalize exceptions/timeouts into ACP statuses (e.g., `validation_error`, `tool_error`, `aborted`).

## Transport Layer
- Start with HTTP JSON gateway: endpoints for capability discovery, start/resume session, send message (returns assistant message + optional tool calls), submit tool result.
- Optional WebSocket for streaming/duplex once stable.
- Keep gateway stateless aside from session lookup; Environment handles persistence.

## Rollout Steps
1) Outbound ACP logging: convert WBAL turns to ACP JSON for inspection; no behavior change.
2) Inbound ACP → WBAL: accept ACP message + session id, run agent once, return ACP-formatted response (messages + tool calls).
3) Full duplex gateway: add session lifecycle endpoints and tool-result ingestion; support resumable sessions.
4) Hardening: schema validation (pydantic/jsonschema), error mapping, capability listing, auth hooks if needed.

## Testing
- Golden-path: start session, user message, agent emits tool call, tool result returned, final message produced.
- Negative cases: invalid tool args (validation_error), missing tool (tool_error), timeout paths, malformed ACP envelope.
- Compatibility snapshots: ensure ACP JSON emitted stays stable (fixture-based).

## Open Questions
- Required ACP fields beyond core (attachments, modalities) we must support initially?
- Auth model for the gateway (bearer, API key, none).
- Streaming needed for first milestone or batch only?
