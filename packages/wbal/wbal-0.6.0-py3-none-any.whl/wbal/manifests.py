from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

from wbal.agents.yaml_agent import YamlAgent
from wbal.environments.configured_env import (
    ConfiguredChatEnv,
    ConfiguredDataEnv,
    ConfiguredEnvironment,
    ConfiguredPollEnv,
)
from wbal.lm import LM, GPT5Large, GPT5MiniTester, OpenAIResponsesLM, ScriptedLM


class PromptManifest(BaseModel):
    system: str = ""
    system_messages: list[str] = Field(default_factory=list)


class LMManifest(BaseModel):
    kind: Literal[
        "openai_responses",
        "gpt5_large",
        "gpt5_mini",
        "scripted",
    ] = "openai_responses"
    import_path: str | None = None
    kwargs: dict[str, Any] = Field(default_factory=dict)
    model: str = "gpt-5-mini"
    temperature: float | None = None
    reasoning: dict[str, Any] | None = None
    include: list[str] | None = None
    script: list[dict[str, Any]] = Field(default_factory=list)


class EnvManifest(BaseModel):
    kind: Literal["basic", "data", "chat", "poll"] = "data"
    env: str = ""
    task: str = ""
    working_directory: str | None = None
    include_working_directory_listing: bool = True
    include_tools_in_observe: bool = False


class ToolsManifest(BaseModel):
    agent: list[str] = Field(default_factory=list)
    env: list[str] = Field(default_factory=list)


class AgentManifest(BaseModel):
    name: str = "agent"
    description: str = ""

    agent_import_path: str | None = None

    prompt: str | None = None
    system_prompt: str | None = None
    system_messages: list[str] = Field(default_factory=list)

    lm: LMManifest = Field(default_factory=LMManifest)
    env: EnvManifest = Field(default_factory=EnvManifest)
    tools: ToolsManifest = Field(default_factory=ToolsManifest)

    max_steps: int = Field(default=20, validation_alias="maxSteps")
    tool_timeout: int = 60
    parallel_tool_calls: bool = False
    max_concurrent_tool_calls: int = 4

    delegates: dict[str, str] = Field(default_factory=dict)
    share_working_directory: bool = True


_TEMPLATE_VAR_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def _render_template(text: str, template_vars: dict[str, Any] | None) -> str:
    if not text or not template_vars:
        return text

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in template_vars:
            return match.group(0)
        return str(template_vars[key])

    return _TEMPLATE_VAR_RE.sub(_replace, text)


def _render_templates_in_prompt(
    prompt: PromptManifest | None, template_vars: dict[str, Any] | None
) -> None:
    if not prompt or not template_vars:
        return
    prompt.system = _render_template(prompt.system, template_vars)
    prompt.system_messages = [
        _render_template(msg, template_vars) for msg in (prompt.system_messages or [])
    ]


def _render_templates_in_agent_manifest(
    manifest: AgentManifest, template_vars: dict[str, Any] | None
) -> None:
    if not template_vars:
        return
    if manifest.system_prompt:
        manifest.system_prompt = _render_template(manifest.system_prompt, template_vars)
    manifest.system_messages = [
        _render_template(msg, template_vars) for msg in (manifest.system_messages or [])
    ]
    manifest.env.env = _render_template(manifest.env.env, template_vars)


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as e:
        raise ValueError(f"Failed to read YAML file: {path}: {e}") from e
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse YAML file: {path}: {e}") from e

    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"YAML file must contain a mapping at top-level: {path}")
    return raw


def _resolve_path(base_dir: Path, maybe_path: str | None) -> Path | None:
    if not maybe_path:
        return None
    candidate = Path(maybe_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return base_dir / candidate


def load_prompt_manifest(path: str | Path) -> PromptManifest:
    p = Path(path).expanduser().resolve()
    return PromptManifest.model_validate(_load_yaml_mapping(p))


def load_agent_manifest(path: str | Path) -> AgentManifest:
    p = Path(path).expanduser().resolve()
    return AgentManifest.model_validate(_load_yaml_mapping(p))


def build_lm(lm: LMManifest) -> LM:
    if lm.import_path:
        obj = _import_attr(lm.import_path)
        if not isinstance(obj, type):
            raise ValueError(
                f"lm.import_path must point to a class. Got: {type(obj).__name__}"
            )
        if not issubclass(obj, LM):
            raise ValueError("lm.import_path class must subclass wbal.lm.LM")
        inst = obj(**(lm.kwargs or {}))

        # Apply overrides only when explicitly provided in YAML.
        fields_set = getattr(lm, "model_fields_set", set())
        if "model" in fields_set and hasattr(inst, "model"):
            inst.model = lm.model
        if "temperature" in fields_set and hasattr(inst, "temperature"):
            inst.temperature = lm.temperature
        if "reasoning" in fields_set and hasattr(inst, "reasoning"):
            inst.reasoning = lm.reasoning
        if "include" in fields_set and hasattr(inst, "include"):
            inst.include = lm.include

        return inst

    if lm.kind == "gpt5_large":
        inst = GPT5Large()
        if lm.temperature is not None:
            inst.temperature = lm.temperature
        if lm.include is not None:
            inst.include = lm.include
        return inst

    if lm.kind == "gpt5_mini":
        inst = GPT5MiniTester()
        if lm.temperature is not None:
            inst.temperature = lm.temperature
        if lm.reasoning is not None:
            inst.reasoning = lm.reasoning
        return inst

    if lm.kind == "scripted":
        return ScriptedLM(script=lm.script)

    # Default: OpenAI Responses with arbitrary model string.
    return OpenAIResponsesLM(
        model=lm.model,
        temperature=lm.temperature,
        reasoning=lm.reasoning,
        include=lm.include,
    )


def build_env(
    env: EnvManifest,
    *,
    tool_modules: list[str] | None = None,
    task: str | None = None,
    working_directory: str | None = None,
) -> Any:
    env_task = task if task is not None else env.task
    env_wd = (
        working_directory if working_directory is not None else env.working_directory
    )
    tool_modules = tool_modules or []

    if env.kind == "chat":
        return ConfiguredChatEnv(
            task=env_task,
            env=env.env,
            working_directory=env_wd,
            include_working_directory_listing=env.include_working_directory_listing,
            tool_modules=tool_modules,
        )
    if env.kind == "poll":
        return ConfiguredPollEnv(
            task=env_task,
            env=env.env,
            working_directory=env_wd,
            include_working_directory_listing=env.include_working_directory_listing,
            tool_modules=tool_modules,
        )
    if env.kind == "basic":
        return ConfiguredEnvironment(
            task=env_task,
            env=env.env,
            include_tools_in_observe=env.include_tools_in_observe,
            tool_modules=tool_modules,
        )

    return ConfiguredDataEnv(
        task=env_task,
        env=env.env,
        working_directory=env_wd,
        include_working_directory_listing=env.include_working_directory_listing,
        tool_modules=tool_modules,
    )


def build_agent_from_file(
    path: str | Path,
    *,
    task: str | None = None,
    max_steps: int | None = None,
    working_directory: str | None = None,
    env_kind: Literal["basic", "data", "chat", "poll"] | None = None,
    env_description: str | None = None,
    template_vars: dict[str, Any] | None = None,
) -> YamlAgent:
    spec_path = Path(path).expanduser().resolve()
    manifest = load_agent_manifest(spec_path)
    base_dir = spec_path.parent

    prompt_path = _resolve_path(base_dir, manifest.prompt)
    prompt = load_prompt_manifest(prompt_path) if prompt_path else None

    _render_templates_in_prompt(prompt, template_vars)
    _render_templates_in_agent_manifest(manifest, template_vars)

    system_prompt = (
        manifest.system_prompt or (prompt.system if prompt else "")
    ).strip()
    if not system_prompt:
        system_prompt = "You are a capable assistant. Use tools when available, be brief and factual."

    system_messages: list[str] = []
    if prompt:
        system_messages.extend(prompt.system_messages or [])
    system_messages.extend(manifest.system_messages or [])

    env = EnvManifest.model_validate(
        {**manifest.env.model_dump(), "kind": env_kind or manifest.env.kind}
    )
    built_env = build_env(
        env,
        tool_modules=manifest.tools.env,
        task=task,
        working_directory=working_directory,
    )
    if env_description is not None:
        existing = getattr(built_env, "env", "") or ""
        built_env.env = (
            f"{env_description}\n\n{existing}".strip() if existing else env_description
        )

    agent_cls: type[YamlAgent] = YamlAgent
    if manifest.agent_import_path:
        agent_cls = _load_agent_class(manifest.agent_import_path)

    agent = agent_cls(
        env=built_env,
        lm=build_lm(manifest.lm),
        maxSteps=max_steps if max_steps is not None else manifest.max_steps,
        system_prompt=system_prompt,
        system_messages=system_messages,
        tool_timeout=manifest.tool_timeout,
        parallel_tool_calls=manifest.parallel_tool_calls,
        max_concurrent_tool_calls=manifest.max_concurrent_tool_calls,
        agent_tool_modules=manifest.tools.agent,
        delegates=manifest.delegates,
        share_working_directory=manifest.share_working_directory,
        manifest_path=str(spec_path),
    )
    return agent


def _import_attr(spec: str) -> Any:
    spec = (spec or "").strip()
    if not spec:
        raise ValueError("Import path is empty")

    if ":" in spec:
        module_path, attr = spec.split(":", 1)
        module_path = module_path.strip()
        attr = attr.strip()
        if not module_path or not attr:
            raise ValueError(f"Invalid import path (expected module:attr): {spec!r}")
    else:
        parts = spec.split(".")
        if len(parts) < 2:
            raise ValueError(
                f"Invalid import path (expected module:attr or module.attr): {spec!r}"
            )
        module_path, attr = ".".join(parts[:-1]), parts[-1]

    module = importlib.import_module(module_path)
    try:
        return getattr(module, attr)
    except AttributeError as e:
        raise ValueError(
            f"Module {module_path!r} has no attribute {attr!r} (from {spec!r})"
        ) from e


def _load_agent_class(spec: str) -> type[YamlAgent]:
    obj = _import_attr(spec)
    if not isinstance(obj, type):
        raise ValueError(
            f"agent_import_path must point to a class. Got: {type(obj).__name__}"
        )
    if not issubclass(obj, YamlAgent):
        raise ValueError(
            "agent_import_path class must subclass wbal.agents.yaml_agent.YamlAgent"
        )
    return obj
