# WBAL State

- **Core primitives**: `Agent`/`Environment`/`LM` are stable; `OpenAIWBAgent` + `DataEnv`/`PollEnv`/`ChatEnv` form the primary stack.
- **YAML-first**: `AgentManifest`/`PromptManifest` + `YamlAgent`/`run_agent_spec` provide the canonical configuration path (prompts, LM selection, env kind, tool modules, delegates, template vars).
- **CLI coverage**: `wbal run|chat|poll` plus `wbal agents {run,validate,list}` and `wbal bundle {validate,run,shell}` mirror what is in code/tests.
- **Bundles**: `run.sh` required, `install.sh` optional; env contract matches WandBSwarm (`AGENT_DIR`, `TASK_DIR`, `WORKSPACE`, `RUN_ID`, `TASK_ID`, `EXPERIMENT_ID`, `BACKEND`).
- **LM adapters**: OpenAI Responses (generic + GPT5 presets), deterministic `ScriptedLM`, and W&B Inference-backed `KimiK2LM`.
- **Persistence**: `DataEnv`/`PollEnv` persist `_state` to `environment_state.json` when `working_directory` is set; observations are capped to the most recent 1000 entries.
