from __future__ import annotations

import json
import os
from types import SimpleNamespace
from typing import Any

import weave
from openai import OpenAI
from openai.types.responses import Response
from pydantic import Field, PrivateAttr

from wbal.helper import TOOL_CALL_TYPE, TOOL_RESULT_TYPE
from wbal.object import WBALObject


class LM(WBALObject):
    """
    Base class for language models.

    Subclasses must implement the invoke() method to call the underlying LLM API.
    """

    def invoke(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        mcp_servers: list[dict[str, Any]] | None = None,
    ) -> Any:
        """
        Invoke the language model.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            tools: Optional list of tool definitions in provider format.
            mcp_servers: Optional list of MCP server tool definitions.

        Returns:
            The LLM response object (format depends on provider).

        Raises:
            NotImplementedError: If not overridden by subclass.
        """
        raise NotImplementedError("Subclasses must implement invoke method")


class OpenAIResponsesLM(LM):
    """
    Generic OpenAI Responses API LM wrapper.

    Use this when you want to select arbitrary model names via config/YAML.

    Note: temperature is optional. Some models (especially reasoning models)
    reject the temperature parameter. Only set it if you need it.
    """

    model: str = "gpt-5-mini"
    temperature: float | None = None  # Optional - only sent if explicitly set
    reasoning: dict[str, Any] | None = None
    include: list[str] | None = None
    client: OpenAI = Field(
        default_factory=lambda: OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    )

    def observe(self) -> str:
        return f"OpenAIResponsesLM(model={self.model}, temperature={self.temperature})"

    @weave.op()
    def invoke(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        mcp_servers: list[dict[str, Any]] | None = None,
    ) -> Response:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "input": messages,
        }
        # Only include temperature if explicitly set
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        if self.reasoning is not None:
            kwargs["reasoning"] = self.reasoning
        if self.include is not None:
            kwargs["include"] = self.include
        if tools or mcp_servers:
            combined_tools = list(tools) if tools else []
            if mcp_servers:
                combined_tools.extend(mcp_servers)
            kwargs["tools"] = combined_tools
        return self.client.responses.create(**kwargs)


class ScriptedLM(LM):
    """
    Deterministic LM for tests/examples.

    The script is a list of steps. Supported step shapes:
      - {"exit": "<message>"}  -> emits a function_call to exit(exit_message=...)
    """

    script: list[dict[str, Any]] = Field(default_factory=list)
    _index: int = PrivateAttr(default=0)

    def observe(self) -> str:
        return f"ScriptedLM(steps={len(self.script)}, index={self._index})"

    def invoke(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        mcp_servers: list[dict[str, Any]] | None = None,
    ) -> Any:
        if self._index >= len(self.script):
            return SimpleNamespace(output=[], output_text="")

        step = self.script[self._index]
        self._index += 1

        if "exit" in step:
            msg = str(step.get("exit", ""))
            return SimpleNamespace(
                output=[
                    SimpleNamespace(
                        type="function_call",
                        name="exit",
                        arguments=json.dumps({"exit_message": msg}),
                        call_id=f"call_{self._index}",
                    )
                ],
                output_text="",
            )

        return SimpleNamespace(output=[], output_text="")


def _default_weave_project() -> str:
    """
    Return the default Weave project for logging.
    """
    return os.getenv("WEAVE_PROJECT", "wandb/zubin-dump")


def _create_kimi_client(*, api_key: str, base_url: str, project: str) -> OpenAI:
    """
    Create an OpenAI client pointed at W&B Inference for Kimi-K2.

    Note: Weave initialization is intentionally *not* performed here.
    Prefer runner/CLI-level `weave.init(...)` for deterministic tracing.
    """
    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        project=project,
    )


class GPT5Large(LM):
    model: str = "gpt-5"
    include: list[str] = ["reasoning.encrypted_content"]
    temperature: float = 1.0
    client: OpenAI = Field(
        default_factory=lambda: OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    )

    def observe(self) -> str:
        """
        Return a concise description of the model configuration.
        """
        return f"GPT5Large(model={self.model}, temperature={self.temperature})"

    @weave.op()
    def invoke(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        mcp_servers: list[dict[str, Any]] | None = None,
    ) -> Response:
        """
        Invoke the language model.
        """
        kwargs: dict[str, Any] = {
            "model": self.model,
            "input": messages,
            "temperature": self.temperature,
            "include": self.include,
        }
        # Combine tools and mcp_servers without mutating input lists
        if tools or mcp_servers:
            combined_tools = list(tools) if tools else []
            if mcp_servers:
                combined_tools.extend(mcp_servers)
            kwargs["tools"] = combined_tools
        response: Response = self.client.responses.create(**kwargs)
        return response


class GPT5LargeVerbose(GPT5Large):
    reasoning: dict[str, str] = {"effort": "high", "summary": "detailed"}

    def observe(self) -> str:
        """
        desc
        """
        return "GPT5LargeVerbose"

    @weave.op()
    def invoke(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        mcp_servers: list[dict[str, Any]] | None = None,
    ) -> Response:
        """
        Invoke the language model.
        """
        kwargs: dict[str, Any] = {
            "model": self.model,
            "input": messages,
            "temperature": self.temperature,
            "include": self.include,
            "reasoning": self.reasoning,
        }
        # Combine tools and mcp_servers without mutating input lists
        if tools or mcp_servers:
            combined_tools = list(tools) if tools else []
            if mcp_servers:
                combined_tools.extend(mcp_servers)
            kwargs["tools"] = combined_tools
        response: Response = self.client.responses.create(**kwargs)
        return response


class GPT5MiniTester(LM):
    model: str = "gpt-5-mini"
    client: OpenAI = Field(
        default_factory=lambda: OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    )
    reasoning: dict[str, Any] = {"effort": "minimal"}
    temperature: float | None = None  # Optional - some models reject temperature

    def observe(self) -> str:
        """
        Return a concise description of the model configuration.
        """
        return f"GPT5MiniTester(model={self.model}, temperature={self.temperature})"

    @weave.op()
    def invoke(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        mcp_servers: list[dict[str, Any]] | None = None,
    ) -> Response:
        """
        Invoke the language model.
        """
        kwargs: dict[str, Any] = {
            "model": self.model,
            "input": messages,
            "reasoning": self.reasoning,
        }
        # Only include temperature if explicitly set
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        # Combine tools and mcp_servers without mutating input lists
        if tools or mcp_servers:
            combined_tools = list(tools) if tools else []
            if mcp_servers:
                combined_tools.extend(mcp_servers)
            kwargs["tools"] = combined_tools
        return self.client.responses.create(**kwargs)


class KimiK2LM(LM):
    """
    Kimi-K2 model running through W&B Inference chat completions.
    """

    model: str = "moonshotai/Kimi-K2-Instruct-0905"
    project: str = Field(default_factory=_default_weave_project)
    temperature: float | None = None
    base_url: str = "https://api.inference.wandb.ai/v1"
    client: Any = None
    tool_call_verify_retries: int = 3
    _client_initialized: bool = PrivateAttr(default=False)

    def observe(self) -> str:
        """
        Return a concise description of the model configuration.
        """
        return (
            f"KimiK2LM(model={self.model}, project={self.project}, "
            f"temperature={self.temperature})"
        )

    def _ensure_client(self) -> None:
        if self.client is not None:
            return
        api_key = os.getenv("WANDB_API_KEY")
        if not api_key:
            raise ValueError("WANDB_API_KEY must be set to use KimiK2LM")
        self.client = _create_kimi_client(
            api_key=api_key, base_url=self.base_url, project=self.project
        )

    @staticmethod
    def _get_field(msg: Any, key: str) -> Any:
        if isinstance(msg, dict):
            return msg.get(key)
        return getattr(msg, key, None)

    def _coerce_content(self, content: Any) -> str:
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for part in content:
                if isinstance(part, str):
                    parts.append(part)
                else:
                    text_val = self._get_field(part, "text")
                    if text_val:
                        parts.append(str(text_val))
            return "\n".join(parts)
        return str(content)

    def _to_chat_messages(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        chat_messages: list[dict[str, Any]] = []
        for msg in messages:
            msg_type = self._get_field(msg, "type")
            if msg_type == TOOL_RESULT_TYPE:
                call_id = self._get_field(msg, "call_id") or self._get_field(msg, "id")
                chat_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": self._get_field(msg, "output") or "",
                    }
                )
                continue

            if msg_type == TOOL_CALL_TYPE:
                call_id = (
                    self._get_field(msg, "call_id")
                    or self._get_field(msg, "id")
                    or "call_0"
                )
                name = self._get_field(msg, "name") or "unknown_function"
                arguments = self._get_field(msg, "arguments") or ""
                if not isinstance(arguments, str):
                    arguments = json.dumps(arguments)
                chat_messages.append(
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": call_id,
                                "type": "function",
                                "function": {"name": name, "arguments": arguments},
                            }
                        ],
                    }
                )
                continue

            role = self._get_field(msg, "role")
            if msg_type == "message" and not role:
                role = "assistant"
            if role:
                chat_messages.append(
                    {
                        "role": role,
                        "content": self._coerce_content(
                            self._get_field(msg, "content")
                        ),
                    }
                )

        return chat_messages

    def _to_chat_tools(
        self, tools: list[dict[str, Any]] | None
    ) -> list[dict[str, Any]]:
        """
        Convert OpenAI Responses-style tool defs into chat-completions format.
        """
        if not tools:
            return []

        chat_tools: list[dict[str, Any]] = []
        for tool in tools:
            if not isinstance(tool, dict):
                chat_tools.append(tool)
                continue

            if tool.get("function"):
                chat_tools.append(tool)
                continue

            if tool.get("type") != "function":
                chat_tools.append(tool)
                continue

            chat_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.get("name"),
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {}),
                    },
                }
            )
        return chat_tools

    @staticmethod
    def _normalize_arguments(raw_args: Any) -> tuple[Any, bool]:
        """
        Try to produce JSON-parseable tool call arguments.
        Returns (normalized_args, is_parseable).
        """
        if raw_args is None:
            return "", True
        if not isinstance(raw_args, str):
            try:
                json.dumps(raw_args)
                return raw_args, True
            except Exception:
                return raw_args, False

        stripped = raw_args.strip()
        candidates = [stripped, stripped.rstrip("`"), stripped.rstrip("`'\"")]

        for candidate in candidates:
            try:
                json.loads(candidate)
                return candidate, True
            except Exception:
                continue

        return stripped, False

    def _tool_calls_parseable(self, output: list[SimpleNamespace]) -> bool:
        all_ok = True
        for item in output:
            if getattr(item, "type", None) != TOOL_CALL_TYPE:
                continue
            args = getattr(item, "arguments", "")
            normalized, ok = self._normalize_arguments(args)
            item.arguments = normalized
            if not ok:
                all_ok = False
        return all_ok

    def _convert_completion_to_output(
        self, completion: Any
    ) -> tuple[str, list[SimpleNamespace]]:
        output: list[SimpleNamespace] = []
        output_text = ""

        choices = getattr(completion, "choices", None) or []
        if not choices:
            return output_text, output

        message = getattr(choices[0], "message", None)
        if message is None:
            return output_text, output

        text_content = self._coerce_content(getattr(message, "content", ""))
        if text_content:
            output_text = text_content
            output.append(
                SimpleNamespace(
                    type="message",
                    role=getattr(message, "role", "assistant"),
                    content=[SimpleNamespace(type="text", text=text_content)],
                )
            )

        tool_calls = getattr(message, "tool_calls", None) or []
        for tc in tool_calls:
            fn = getattr(tc, "function", None)
            name = getattr(fn, "name", "") if fn else ""
            arguments = getattr(fn, "arguments", "") if fn else ""
            if not isinstance(arguments, str):
                arguments = json.dumps(arguments)
            arguments, _ = self._normalize_arguments(arguments)
            output.append(
                SimpleNamespace(
                    type=TOOL_CALL_TYPE,
                    name=name,
                    arguments=arguments,
                    call_id=getattr(tc, "id", "") or getattr(tc, "call_id", ""),
                )
            )

        return output_text, output

    @weave.op()
    def invoke(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        mcp_servers: list[dict[str, Any]] | None = None,
    ) -> Any:
        """
        Invoke the Kimi-K2 chat completion model via W&B Inference.
        """
        self._ensure_client()
        chat_messages = self._to_chat_messages(messages)
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": chat_messages,
        }
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature

        if tools or mcp_servers:
            combined_tools = list(tools) if tools else []
            if mcp_servers:
                combined_tools.extend(mcp_servers)
            kwargs["tools"] = self._to_chat_tools(combined_tools)

        attempts = max(0, int(self.tool_call_verify_retries or 0))
        last_output: list[SimpleNamespace] = []
        last_text = ""
        last_completion: Any = None

        for attempt in range(attempts + 1):
            completion = self.client.chat.completions.create(**kwargs)  # type: ignore[union-attr]
            output_text, output = self._convert_completion_to_output(completion)
            if self._tool_calls_parseable(output):
                return SimpleNamespace(
                    output=output,
                    output_text=output_text,
                    raw_response=completion,
                )
            last_output = output
            last_text = output_text
            last_completion = completion

        return SimpleNamespace(
            output=last_output,
            output_text=last_text,
            raw_response=last_completion,
        )
