# WBAL Developer Guide

Notes for working on the WBAL codebase.

## Architecture (code-level)
- **Primitives** (`wbal/object.py`): `WBALObject` is a Pydantic `BaseModel` with `observe()` and optional async `setup()`.
- **Agents**:
  - `Agent` (`wbal/agent.py`): perceive → invoke → do loop; discovers tools on itself and its env; tracks messages and tool definitions.
  - `OpenAIWBAgent` (`wbal/agents/openai_agent.py`): Responses API-oriented loop, built-in `exit()`, reasoning/message rendering via `env.output_handler`, optional parallel tool execution, special handling for `chat` calls.
  - `YamlAgent` (`wbal/agents/yaml_agent.py`): `OpenAIWBAgent` configured from YAML; loads agent/env tool modules, merges extra system messages, exposes `list_agents()` / `run_agent()` for declared delegates.
  - `ExitableAgent` (`wbal/mixins.py`): mixin adding `exit()` tool and stop condition.
- **Environments**:
  - `Environment` (`wbal/environment.py`): context + tool surface; optional tool descriptions in `observe()`.
  - `StatefulEnvironment`: generic persisted state helper.
  - `DataEnv` / `PollEnv` / `ChatEnv` (`wbal/environments/`): stateful notes/observations, write tools, and chat tool/input gating.
  - Configured variants (`configured_env.py`): allow attaching tool modules via import specs.
- **LMs** (`wbal/lm.py`): `OpenAIResponsesLM`, `GPT5Large`, `GPT5MiniTester`, `ScriptedLM`, `KimiK2LM` (chat-completions via W&B Inference).
- **YAML + runner** (`wbal/manifests.py`, `wbal/runner.py`): `AgentManifest`/`PromptManifest`, template rendering, `build_agent_from_file`, `run_agent_spec`, `apply_overrides`.
- **Tools + schema helpers** (`wbal/helper.py`, `wbal/tool_imports.py`): decorators, timeout utility, schema extraction/formatting for OpenAI/Anthropic, dynamic tool importing/binding.
- **CLI** (`wbal/cli.py`): `wbal` entrypoint with `run`, `chat`, `poll`, `agents {run,validate,list}`, and `bundle {validate,run,shell}`.
- **Bundles** (`wbal/bundle.py`): validate/run/shell helpers for WandBSwarm-style bundles (`run.sh` required, `install.sh` optional).
- **Sandbox stubs** (`wbal/sandbox_stub.py`, `wbal/sandboxer.py`): minimal interface + helpers for optional sandbox integration.

## Repo layout
```
wbal/
├── wbal/                  # Library code
│   ├── agents/            # Agent implementations
│   ├── environments/      # Reference environments
│   ├── tools/             # Reusable tools (e.g., bash)
│   ├── scripts/           # CLI wrappers (wbal-chat, wbal-poll)
│   └── *.py               # Core modules (agent, env, lm, manifests, helper, runner, bundle, etc.)
├── examples/              # Sample agents, manifests, bundles
├── tests/                 # pytest suite
├── README.md              # User-facing overview
├── USER.md                # Detailed user guide
└── Agent_Instructions.md  # Agent-building notes
```

## Development setup
```bash
uv sync                         # install deps from pyproject/uv.lock
uv run pytest                   # run full test suite
uv run pytest tests/test_agent.py -q   # run a specific file
```

Entry points (pyproject):
- `wbal` → `wbal.cli:main`
- `wbal-chat` → `wbal.scripts.chat:main`
- `wbal-poll` → `wbal.scripts.poll:main`

## Behavioral notes (from code/tests)
- `OpenAIWBAgent.perceive()` seeds messages on step 0 with: dated system prompt, optional system messages/delegates info, `env.observe()`, then `Task: ...` as user content.
- Tool schemas are derived from type hints + docstrings via `extract_tool_schema` → `to_openai_tool`/`to_anthropic_tool`. Duplicate tool names across agent/env/imported modules raise `ValueError`.
- `OpenAIWBAgent` executes tool calls sequentially with `tool_timeout` unless `parallel_tool_calls=True` (skips parallelism if any call is `chat`). Outputs are appended via `format_openai_tool_response`.
- `YamlAgent.run_agent()` resolves delegate specs relative to the manifest path and can share or override `working_directory`.
- `DataEnv` persists `_state` to `environment_state.json` when `working_directory` is set; `PollEnv` caps observations to the last 1000 entries.

## Testing
- Main coverage areas: agent loop (`tests/test_agent.py`), helper utilities (`tests/test_helper.py`), environments (`tests/test_environment.py`), LM adapters (`tests/test_lm.py`), manifests/CLI (`tests/test_cli_run.py`), bundles (`tests/test_bundle.py`), and examples (`tests/test_story_summarizer.py`, `tests/test_zagent_v1.py`).
- Use `ScriptedLM` in tests for deterministic tool-call sequences.

## Contribution tips
- Keep tool names unique and documented; docstrings and type hints drive user-facing schemas.
- Prefer `@weaveTool` for observability.
- Maintain alignment between YAML schema (`AgentManifest`) and CLI help text.
- Avoid destructive commands in bundled tools (`bash` helpers truncate stdout/stderr to 8K for safety).
