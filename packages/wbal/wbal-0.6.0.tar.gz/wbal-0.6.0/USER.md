# WBAL User Guide

WBAL (**W**eights & **B**iases **A**gent **L**ibrary) is a compact toolkit for composing LLM agents from three primitives: **Agent**, **Environment**, and **LM**. Everything is a Pydantic model with an `observe()` surface for transparency and tracing.

## Installation
- Python `>=3.13,<3.14`
- Real LMs require `OPENAI_API_KEY`; `KimiK2LM` also needs `WANDB_API_KEY`

```bash
pip install wbal
# or, from source
git clone <this-repo>
cd wbal
uv sync
```

## Quick start
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
agent = OpenAIWBAgent(env=env, lm=GPT5MiniTester(), maxSteps=10)
agent.run()
```

## Core concepts
### Agents
- `Agent` (base): perceive → invoke → do loop; discovers `@tool`/`@weaveTool` methods on itself and its environment.
- `OpenAIWBAgent`: OpenAI Responses-oriented loop with built-in `exit()`, optional parallel tool calls, and rendering of reasoning/message items to `env.output_handler`.
- `YamlAgent`: `OpenAIWBAgent` configured from `.agent.yaml` manifests; gains `list_agents()` and `run_agent()` for declared delegates.

### Environments
- `Environment`: context string + tool surface; `observe()` can include tool descriptions when `include_tools_in_observe` is true.
- `DataEnv`: persistent `_state` (notes/observations) + read-only tools `get_notes`, `get_observations`; includes optional working directory listing.
- `PollEnv`: adds write tools (`store_note`, `delete_note`, `add_observation`).
- `ChatEnv`: adds `chat(message_to_user, wait_for_user_input=False)` and input gating (`has_pending_input_request`).
- Configured variants (`ConfiguredEnvironment`, `ConfiguredDataEnv`, `ConfiguredChatEnv`, `ConfiguredPollEnv`) can attach extra tools from import specs via manifests.

### Tools
- Decorate methods with `@weaveTool` (or `@tool`). Docstrings become descriptions; type hints drive JSON schema.
- Tool names must be unique across agent, environment, and imported modules.
- `tool_timeout(seconds, name)` context manager is available; `OpenAIWBAgent` uses it for sequential tool calls (skips timeout for `chat`).

### Language models
- `OpenAIResponsesLM` (arbitrary model string), `GPT5Large`, `GPT5MiniTester`, `ScriptedLM` (deterministic for tests), `KimiK2LM` (chat-completions via W&B Inference).
- Swap by passing an `lm` instance/class to the agent. `GPT5Large`/`GPT5MiniTester` include defaults for reasoning/include fields.

## Running agents
- Python: instantiate env + agent and call `run(task=..., max_steps=...)`.
- CLI: see commands in [README.md](README.md) or below.

Baseline CLI examples:
```bash
wbal run --project myproj --task "Say hello"
wbal chat --project myproj --task "Assist the user" --working-dir ./.wbal_state
wbal poll --project myproj --task "Monitor" --interval 300
```

## YAML agents
`AgentManifest` + `PromptManifest` live in YAML. Key fields:
- `prompt`: path to prompt YAML (`system`, `system_messages`) or inline `system_prompt`/`system_messages`
- `lm`: `kind` (`openai_responses` | `gpt5_large` | `gpt5_mini` | `scripted`) or `import_path` + `kwargs`
- `env`: `kind` (`basic` | `data` | `chat` | `poll`), `env`, `task`, `working_directory`, `include_working_directory_listing`, `include_tools_in_observe`
- `tools.agent` / `tools.env`: import specs for extra tools
- `delegates`: `{alias: relative/path/to/agent.yaml}` + `share_working_directory`
- `max_steps`/`tool_timeout`/`parallel_tool_calls`/`max_concurrent_tool_calls`

Template vars (`--var key=val`) render `{key}` placeholders in prompts/env fields. `--set path=value` overrides instantiated fields (e.g., `lm.model=gpt-5-mini`).

Run via CLI:
```bash
wbal agents run --spec examples/agents/orchestrator.agent.yaml --task "Delegate work" --var who=world
wbal agents validate --spec examples/agents/baseline.agent.yaml
wbal agents list --dir examples/agents
```

## Bundles (WandBSwarm-compatible)
- Layout: `run.sh` (required), `install.sh` (optional). Both execute with `cwd=$TASK_DIR`.
- Env vars provided: `AGENT_DIR`, `TASK_DIR`, `WORKSPACE`, `RUN_ID`, `TASK_ID`, `EXPERIMENT_ID`, `BACKEND` (+ any `--env KEY=VALUE` overrides).
- Helpers: `wbal bundle validate ...`, `wbal bundle run ...`, `wbal bundle shell ...`.

## Observability
- `@weaveTool` wraps functions with `weave.op()`; call `weave.init(...)` before runs to trace.
- `OpenAIWBAgent` surfaces reasoning/message content via `env.output_handler` (defaults to `print`).

## API (exports)
```python
from wbal import (
    WBALObject, Agent, Environment, StatefulEnvironment,
    DataEnv, ChatEnv, PollEnv,
    OpenAIWBAgent, YamlAgent, ExitableAgent,
    LM, GPT5Large, GPT5MiniTester, OpenAIResponsesLM, ScriptedLM, KimiK2LM,
    AgentManifest, PromptManifest, build_agent_from_file, load_agent_manifest, load_prompt_manifest, run_agent_spec,
    tool, weaveTool, get_tools, extract_tool_schema, to_openai_tool, to_anthropic_tool, format_openai_tool_response,
    tool_timeout, ToolTimeoutError,
    AgentBundleEntry, validate_agent_bundle, run_agent_bundle, shell_agent_bundle,
)
```
