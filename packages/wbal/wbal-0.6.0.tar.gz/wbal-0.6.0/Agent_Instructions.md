# Agent Instructions

Practical notes for building agents with WBAL’s reference stack (`OpenAIWBAgent`, `DataEnv`/`PollEnv`/`ChatEnv`, YAML manifests).

## Building blocks
- **Environment**: supplies context + tools. `DataEnv` tracks notes/observations and can persist them to `environment_state.json` when `working_directory` is set. `PollEnv` adds write tools (`store_note`, `delete_note`, `add_observation`). `ChatEnv` adds `chat()` plus input gating (`has_pending_input_request`).
- **Agent**: `OpenAIWBAgent` runs the perceive → invoke → do loop for the OpenAI Responses API. It injects a dated system prompt, optional extra system messages, the env observation, and a `Task: ...` user message on step 0.
- **LM**: pass any `LM` subclass (default: `GPT5Large`; tests/examples use `GPT5MiniTester`). `ScriptedLM` is available for deterministic flows.
- **Tools**: mark env/agent methods with `@weaveTool` (or `@tool`). Docstrings become descriptions; type hints drive schemas.

## Adding tools (examples)
Env tool:
```python
from wbal import weaveTool
from wbal.environments.data_env import DataEnv

class MyDataEnv(DataEnv):
    @weaveTool
    def fetch_user(self, user_id: str) -> dict[str, str]:
        """Return user info from your service."""
        return {"id": user_id}
```
Agent tool:
```python
from wbal import weaveTool
from wbal.agents.openai_agent import OpenAIWBAgent

class MyAgent(OpenAIWBAgent):
    @weaveTool
    def jot(self, note: str) -> str:
        """Keep a local note during reasoning."""
        return f"Noted: {note}"
```
You can also import tool modules via manifest fields (`tools.agent`, `tools.env`) or mixins; names must be unique across agent/env/tools.

## Running agents
```python
from wbal.agents.openai_agent import OpenAIWBAgent
from wbal.environments.chat_env import ChatEnv

env = ChatEnv(task="help the user", working_directory="/tmp/state")
agent = OpenAIWBAgent(env=env, maxSteps=20)
agent.run(task="Find recent deploys")
```
- Stop conditions: `exit()` tool call, or (for `ChatEnv`) waiting for user input.
- Output: reasoning summaries and assistant messages are routed through `env.output_handler` (defaults to `print`).
- Tool execution: sequential by default; set `parallel_tool_calls=True` to fan out (skips parallelism when a `chat` call is present). `tool_timeout` governs per-tool timeouts except for `chat`.

## Persistence and state
- `DataEnv`/`PollEnv` store notes/observations in `_state`; set `working_directory` to persist to `environment_state.json`.
- `StatefulEnvironment` offers a generic persisted state pattern if you need a custom structure.

## YAML-first flow
- `YamlAgent` wires prompts, LMs, env kind, tool modules, and delegates from `.agent.yaml`.
- Delegation: declare `delegates` in the manifest; the agent gains `list_agents()` and `run_agent(agent, task, max_steps=None)`. Delegates resolve relative to the manifest path; `share_working_directory` controls whether child agents reuse the parent `working_directory`.
- Template vars: `--var key=val` renders `{key}` placeholders in prompts and env fields before instantiation.

## CLI shortcuts
- Chat: `wbal chat --project myproj --task "Assist the user" --working-dir /tmp/state`
- Poll: `wbal poll --project myproj --task "Monitor health" --working-dir /tmp/state --interval 300`
- YAML: `wbal agents run --spec path/to/agent.yaml --task "Do the thing" --var who=world --set lm.model=gpt-5-mini`

## Bundles (WandBSwarm contract)
- Bundle layout: `run.sh` (required) + `install.sh` (optional).
- Both run with `cwd=$TASK_DIR` and env vars `AGENT_DIR`, `TASK_DIR`, `WORKSPACE`, `RUN_ID`, `TASK_ID`, `EXPERIMENT_ID`, `BACKEND`.
- Local helpers: `wbal bundle validate ...`, `wbal bundle run ...`, `wbal bundle shell ...`.
