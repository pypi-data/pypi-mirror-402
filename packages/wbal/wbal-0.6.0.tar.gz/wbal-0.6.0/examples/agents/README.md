# YAML Agents (Examples)

These files demonstrate WBAL's YAML-based agent manifests and prompt files.

Run (baseline):
```bash
uv run wbal run --project demo --agent-spec examples/agents/baseline.agent.yaml --task "Say hello, then call exit()."
```

Run (multi-agent orchestrator):
```bash
uv run wbal run --project demo --agent-spec examples/agents/orchestrator.agent.yaml --task "Draft a short plan, delegate research/coding, then call exit()."
```

