from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from pydantic import Field, PrivateAttr

from wbal.agents.openai_agent import OpenAIWBAgent
from wbal.environments.chat_env import ChatEnv
from wbal.helper import (
    extract_tool_schema,
    get_tools,
    to_openai_tool,
    weaveTool,
)
from wbal.tool_imports import ToolImportError, load_bound_tools


class YamlAgent(OpenAIWBAgent):
    """
    OpenAIWBAgent configured from YAML manifests.

    Supports:
    - Extra agent tools loaded from import specs (agent_tool_modules)
    - Delegation to explicitly-declared subagents (delegates) via run_agent()
    - Optional extra system messages (system_messages) in addition to system_prompt
    """

    system_messages: list[str] = Field(default_factory=list)
    agent_tool_modules: list[str] = Field(default_factory=list)
    delegates: dict[str, str] = Field(default_factory=dict)
    manifest_path: str | None = None
    share_working_directory: bool = True

    _extra_tool_callables: dict[str, Callable[..., Any]] = PrivateAttr(
        default_factory=dict
    )
    _delegate_cache: dict[str, dict[str, Any]] = PrivateAttr(default_factory=dict)

    def _base_dir(self) -> Path:
        if self.manifest_path:
            return Path(self.manifest_path).expanduser().resolve().parent
        return Path.cwd()

    def _resolve_delegate_spec(self, spec_path: str) -> Path:
        candidate = Path(spec_path).expanduser()
        if candidate.is_absolute():
            return candidate.resolve()
        return (self._base_dir() / candidate).resolve()

    def _load_delegate_info(self) -> dict[str, dict[str, Any]]:
        if self._delegate_cache:
            return dict(self._delegate_cache)

        info: dict[str, dict[str, Any]] = {}
        for name, rel_path in (self.delegates or {}).items():
            spec_path = self._resolve_delegate_spec(rel_path)
            try:
                from wbal.manifests import (
                    load_agent_manifest,
                )  # local import to avoid cycles

                manifest = load_agent_manifest(spec_path)
                info[name] = {
                    "name": manifest.name,
                    "description": manifest.description or "",
                    "spec": str(spec_path),
                }
            except Exception as e:  # noqa: BLE001
                info[name] = {
                    "name": name,
                    "description": "",
                    "spec": str(spec_path),
                    "error": str(e),
                }

        self._delegate_cache = dict(info)
        return info

    def _delegates_system_message(self) -> str | None:
        info = self._load_delegate_info()
        if not info:
            return None

        lines = ["Available subagents (call via run_agent):"]
        for alias in sorted(info.keys()):
            desc = (info[alias].get("description") or "").strip()
            if desc:
                lines.append(f"- {alias}: {desc}")
            else:
                lines.append(f"- {alias}")
        return "\n".join(lines)

    def getToolDefinitions(self) -> tuple[list[dict[str, Any]], dict[str, Callable]]:  # type: ignore[override]
        definitions: list[dict[str, Any]] = []
        callables: dict[str, Callable] = {}
        formatter = self.toolDefinitionFormatter or to_openai_tool

        # 1) Agent tools declared as methods
        agent_tools = get_tools(self)
        for name, method in agent_tools.items():
            if name in callables:
                raise ValueError(
                    f"Duplicate @tool name '{name}' found. "
                    "You are not allowed to have any @tool-decorated methods with the same name."
                )
            schema = extract_tool_schema(method)
            definitions.append(formatter(schema))
            callables[name] = method

        # 2) Extra agent tools from import specs
        try:
            self._extra_tool_callables = load_bound_tools(self, self.agent_tool_modules)
        except ToolImportError as e:
            raise ValueError(str(e)) from e

        for name, method in self._extra_tool_callables.items():
            if name in callables:
                raise ValueError(
                    f"Duplicate @tool name '{name}' found between agent and agent_tool_modules. "
                    "You are not allowed to have any @tool-decorated methods with the same name."
                )
            schema = extract_tool_schema(method)
            definitions.append(formatter(schema))
            callables[name] = method

        # 3) Environment tools (env may also be tool-configured)
        env_tools = self.env.get_tools()
        for name, method in env_tools.items():
            if name in callables:
                raise ValueError(
                    f"Duplicate @tool name '{name}' found between agent and environment. "
                    "You are not allowed to have any @tool-decorated methods with the same name."
                )
            schema = extract_tool_schema(method)
            definitions.append(formatter(schema))
            callables[name] = method

        return definitions, callables

    def perceive(self) -> None:  # type: ignore[override]
        if self._step_count == 0:
            if not self.messages:
                from datetime import datetime

                today = datetime.now().strftime("%Y-%m-%d")
                self.messages.append(
                    {
                        "role": "system",
                        "content": f"{self.system_prompt}\n\nToday's date: {today}",
                    }
                )
                for msg in self.system_messages:
                    msg = (msg or "").strip()
                    if msg:
                        self.messages.append({"role": "system", "content": msg})

                delegates_msg = self._delegates_system_message()
                if delegates_msg:
                    self.messages.append({"role": "system", "content": delegates_msg})

                env_obs = (self.env.observe() or "").strip()
                if env_obs:
                    self.messages.append({"role": "system", "content": env_obs})
            self.messages.append({"role": "user", "content": f"Task: {self.env.task}"})

    @weaveTool
    def list_agents(self) -> dict[str, Any]:
        """List the explicitly-declared subagents this agent can call."""
        return {
            "success": True,
            "agents": self._load_delegate_info(),
            "count": len(self.delegates or {}),
        }

    @weaveTool
    def run_agent(
        self, agent: str, task: str, max_steps: int | None = None
    ) -> dict[str, Any]:
        """
        Call a subagent declared in this agent's YAML manifest.

        This is the core multi-agent "edge" primitive: calling another agent produces a DAG edge.
        Only agents listed in `delegates` are callable.
        """
        if not agent or agent not in (self.delegates or {}):
            return {
                "success": False,
                "error": f"Unknown agent {agent!r}. Allowed: {sorted((self.delegates or {}).keys())}",
            }

        spec_path = self._resolve_delegate_spec(self.delegates[agent])

        # Default to sharing the parent's working directory (if any) unless the child specifies its own.
        parent_wd = getattr(self.env, "working_directory", None)
        working_directory_override = parent_wd if self.share_working_directory else None

        from wbal.manifests import (  # local import
            build_agent_from_file,
            load_agent_manifest,
        )

        child_manifest = load_agent_manifest(spec_path)
        if child_manifest.env.working_directory:
            working_directory_override = child_manifest.env.working_directory

        child_agent = build_agent_from_file(
            spec_path,
            task=task,
            max_steps=max_steps,
            working_directory=working_directory_override,
        )

        captured: list[str] = []
        child_agent.env.output_handler = lambda x: captured.append(x)
        if isinstance(child_agent.env, ChatEnv):
            child_agent.env.user_chat_input_handler = lambda prompt: ""

        run_result = child_agent.run(task=task, max_steps=max_steps)
        exit_message = getattr(child_agent, "_exit_message", "") or ""
        output_text = "\n".join([c for c in captured if c])[:8000]

        return {
            "success": True,
            "agent": agent,
            "spec": str(spec_path),
            "description": child_manifest.description or "",
            "steps": run_result.get("steps"),
            "working_directory": getattr(child_agent.env, "working_directory", None),
            "exit_message": exit_message[:8000],
            "output": output_text,
        }
