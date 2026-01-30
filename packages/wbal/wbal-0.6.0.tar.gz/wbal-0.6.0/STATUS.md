# WBAL Project Status

Last updated: 2026-01-13

## Current state
- Core primitives, YAML manifests, CLI, and bundle helpers are implemented and covered by tests.
- Reference stack (`OpenAIWBAgent` + `DataEnv`/`PollEnv`/`ChatEnv` + OpenAI/Kimi LM adapters) is stable for local runs and bundle execution.
- Examples include code-first (`simple_example.py`, `zagent_v1.py`, `story_summarizer.py`) and YAML-first (`examples/agents/*`) patterns; bundle example lives at `examples/bundles/hello_bundle`.

## Known gaps/risks
- CLI import oversight: `wbal.cli` uses `Path` without importing it; code paths that rely on `_resolve_agent_spec_from_name` will error until the import is added.
- Two run-loop shapes exist (`Agent` base vs. `OpenAIWBAgent`); ensure features land in both when applicable.
- Tool execution is synchronous unless `parallel_tool_calls` is enabled; long-running tools will block the loop.

## Test coverage
- Agent loop, helper utilities, environments, manifests/CLI, bundles, LM adapters, and examples are exercised by the pytest suite (`uv run pytest`).

## Short-term focus
- Keep YAML schema/CLI help aligned with `AgentManifest`.
- Address the CLI import gap and continue consolidating run-loop behavior where possible.
