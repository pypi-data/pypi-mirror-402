# WBAL

**W**eights & **B**iases **A**gent **L**ibrary — a compact framework for wiring LLM agents, environments, and tools.

## What’s inside
- **Agent loop**: `Agent` implements the perceive → invoke → do cycle. `OpenAIWBAgent` is the reference implementation tuned for the OpenAI Responses API (adds `exit()`, reasoning/message rendering, optional parallel tool calls).
- **Environments**: `Environment` is the base; `DataEnv` adds persisted notes/observations; `PollEnv` adds write tools; `ChatEnv` adds a `chat()` tool and input gating. Configured variants can attach tools from importable modules.
- **LM adapters**: `OpenAIResponsesLM`, `GPT5Large`, `GPT5MiniTester`, `ScriptedLM` (deterministic), and `KimiK2LM` (W&B Inference chat-completions).
- **YAML-first agents**: `YamlAgent` + `AgentManifest`/`PromptManifest` wire prompts, LMs, env kind, tool modules, and explicit delegates (`run_agent` / `list_agents`).
- **CLI + bundles**: `wbal` CLI runs chat/poll/baseline or YAML agents and validates/runs WandBSwarm-compatible bundles (`run.sh` + optional `install.sh`).

## Installation
- Python `>=3.13,<3.14`
- LLMs require `OPENAI_API_KEY` (and `WANDB_API_KEY` for `KimiK2LM`)

From PyPI:
```bash
pip install wbal
```

From source:
```bash
git clone <this-repo>
cd wbal
uv sync
```

## Quick start (code)
```python
import os
import weave
from wbal import GPT5MiniTester, OpenAIWBAgent, weaveTool
from wbal.environments.chat_env import ChatEnv

weave.init(os.getenv("WEAVE_PROJECT", "my-project"))

class MyEnv(ChatEnv):
    env = "You are a helpful assistant."
    include_working_directory_listing = False

    @weaveTool
    def greet(self, name: str) -> str:
        """Greet someone by name."""
        return f"Hello, {name}!"

env = MyEnv(task="Use greet to say hello to Alice, then call exit().", working_directory="./.wbal_state")
agent = OpenAIWBAgent(
    env=env,
    lm=GPT5MiniTester(),
    maxSteps=10,
    system_prompt="Use tools when helpful. Call exit() when you're done.",
)
agent.run()
```

## CLI (high level)
```bash
# Baseline (non-interactive) run
wbal run --project myproj --task "Say hello"

# Interactive chat
wbal chat --project myproj --task "Help the user"

# Polling loop (optionally on an interval)
wbal poll --project myproj --task "Check status" --interval 300

# YAML-first (recommended)
wbal agents run --spec path/to/agent.yaml --task "Do the thing"
wbal agents validate --spec path/to/agent.yaml
wbal agents list --dir examples/agents

# Bundles (WandBSwarm contract: run.sh required, install.sh optional)
wbal bundle validate --agent-dir path/to/agent
wbal bundle run --agent-dir path/to/agent --task-dir ./task --workspace-dir ./workspace
wbal bundle shell --agent-dir path/to/agent --task-dir ./task --workspace-dir ./workspace
```
Common YAML flags: `--var KEY=VALUE` (prompt templating), `--set PATH=VALUE` (override instantiated fields), `--env KEY=VALUE` (env vars before load), `--weave-project`, `--metadata-out`.

## YAML agents (essentials)
`wbal.manifests.AgentManifest` fields:
```yaml
name: orchestrator
description: Optional summary

prompt: prompts/orchestrator.prompt.yaml    # or set system_prompt/system_messages inline

lm:
  kind: openai_responses                    # or gpt5_large, gpt5_mini, scripted
  model: gpt-5-mini
  temperature: 1.0
  reasoning: { effort: minimal }

env:
  kind: poll                                # basic | data | chat | poll
  env: "Context shown to the agent"
  working_directory: ./.wbal_state
  include_working_directory_listing: true
  include_tools_in_observe: false

tools:
  env: [wbal.tools.bash]                    # import specs; merged with env methods
  agent: []                                 # import specs; merged with agent methods

delegates:                                  # explicit subagents for run_agent()
  researcher: worker_research.agent.yaml
share_working_directory: true
max_steps: 30
tool_timeout: 60
parallel_tool_calls: true
max_concurrent_tool_calls: 4
```
Template vars (`--var key=val`) render `{key}` placeholders in prompts/env fields. Delegates resolve relative to the manifest path.

## Components (exports)
```python
from wbal import (
    # Core primitives
    WBALObject, Agent, Environment, StatefulEnvironment, LM,
    # Environments
    DataEnv, ChatEnv, PollEnv,
    # Agents
    OpenAIWBAgent, YamlAgent, ExitableAgent,
    # LMs
    GPT5Large, GPT5MiniTester, OpenAIResponsesLM, ScriptedLM, KimiK2LM,
    # Manifests + runner
    AgentManifest, PromptManifest, build_agent_from_file, load_agent_manifest,
    load_prompt_manifest, run_agent_spec,
    # Tooling
    tool, weaveTool, get_tools, extract_tool_schema, to_openai_tool, to_anthropic_tool,
    format_openai_tool_response, tool_timeout, ToolTimeoutError,
    # Bundles
    AgentBundleEntry, validate_agent_bundle, run_agent_bundle, shell_agent_bundle,
)
```

## Examples
- `examples/simple_example.py` — minimal ChatEnv + OpenAIWBAgent.
- `examples/zagent_v1.py` — orchestrator-style agent with persistent notes and bash tool wiring.
- `examples/agents/` — YAML manifests (baseline, orchestrator with delegates, worker agents + prompts).
- `examples/story_summarizer.py` — custom Agent/Environment pair that reads files and summarizes.
- `examples/bundles/hello_bundle` — minimal bundle exercising the WandBSwarm contract.

Run an example:
```bash
uv run python examples/zagent_v1.py --task "Inspect this repo, take notes, then exit()"
```

## Testing
```bash
uv run pytest
```

## Documentation
- [USER.md](USER.md) — usage guide and API reference
- [DEVELOPER.md](DEVELOPER.md) — architecture and contribution notes
- [Agent_Instructions.md](Agent_Instructions.md) — building agents/environments
