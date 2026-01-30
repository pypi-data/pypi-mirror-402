from __future__ import annotations

from typing import Any, Callable

from pydantic import Field, PrivateAttr, model_validator

from wbal.environment import Environment
from wbal.environments.chat_env import ChatEnv
from wbal.environments.data_env import DataEnv
from wbal.environments.poll_env import PollEnv
from wbal.tool_imports import load_bound_tools


class ToolConfiguredEnvMixin:
    """
    Mixin that augments an Environment with additional @tool/@weaveTool callables
    loaded from importable modules.

    The imported tool callables are *not* attached as attributes (Pydantic blocks
    dynamic fields); instead they're stored privately and merged into get_tools().
    """

    tool_modules: list[str] = Field(default_factory=list)
    _extra_tool_callables: dict[str, Callable[..., Any]] = PrivateAttr(
        default_factory=dict
    )

    @model_validator(mode="after")
    def _load_tool_modules(self) -> "ToolConfiguredEnvMixin":
        self._extra_tool_callables = load_bound_tools(self, self.tool_modules)
        return self

    def get_tools(self) -> dict[str, Any]:  # type: ignore[override]
        tools = super().get_tools()
        overlaps = set(tools).intersection(self._extra_tool_callables)
        if overlaps:
            raise ValueError(
                f"Duplicate @tool name(s) between env and tool modules: {sorted(overlaps)}"
            )
        return {**tools, **self._extra_tool_callables}


class ConfiguredEnvironment(ToolConfiguredEnvMixin, Environment):
    pass


class ConfiguredDataEnv(ToolConfiguredEnvMixin, DataEnv):
    pass


class ConfiguredChatEnv(ToolConfiguredEnvMixin, ChatEnv):
    pass


class ConfiguredPollEnv(ToolConfiguredEnvMixin, PollEnv):
    pass
