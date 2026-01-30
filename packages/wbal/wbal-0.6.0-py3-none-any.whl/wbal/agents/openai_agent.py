from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import datetime
from typing import Any

from pydantic import Field

from wbal.agent import Agent
from wbal.environments.chat_env import ChatEnv
from wbal.helper import (
    TOOL_CALL_TYPE,
    format_openai_tool_response,
    tool_timeout,
    weaveTool,
)
from wbal.lm import LM, GPT5Large

DEFAULT_SYSTEM_PROMPT = (
    "You are a capable assistant. Use tools when available, be brief and factual."
)


def extract_reasoning_summary(reasoning_item: Any) -> str | None:
    summary = getattr(reasoning_item, "summary", None)
    if not summary:
        return None
    if isinstance(summary, list):
        texts = []
        for item in summary:
            if hasattr(item, "text"):
                texts.append(item.text)
            elif isinstance(item, str):
                texts.append(item)
        if texts:
            return " ".join(texts)
    if isinstance(summary, str):
        return summary
    return None


def extract_message_text(message_item: Any) -> str | None:
    content = getattr(message_item, "content", [])
    if not content:
        return None
    parts: list[str] = []
    for part in content:
        if hasattr(part, "text"):
            parts.append(part.text)
        elif getattr(part, "type", None) == "output_text":
            text = getattr(part, "text", "")
            if text:
                parts.append(text)
    return "\n".join(parts) if parts else None


class OpenAIWBAgent(Agent):
    """Reference WBAL agent tuned for OpenAI Responses API."""

    lm: LM = Field(default_factory=GPT5Large)
    messages: list[dict[str, Any]] = Field(default_factory=list)
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    tool_timeout: int = 60
    parallel_tool_calls: bool = False
    max_concurrent_tool_calls: int = 4
    _exit: bool = False
    _exit_message: str = ""

    @weaveTool
    def exit(self, exit_message: str) -> str:
        """Exit the run loop with a final message."""
        self._exit = True
        self._exit_message = exit_message
        if hasattr(self, "env") and hasattr(self.env, "output_handler"):
            self.env.output_handler(exit_message)
        return exit_message

    def reset(self, reset_messages: bool = False) -> None:
        self._exit = False
        self._exit_message = ""
        if reset_messages:
            self.messages = []
            self._last_response = None
        if isinstance(self.env, ChatEnv):
            self.env._waiting_for_input = False
            self.env._waiting_message = ""

    @property
    def stopCondition(self) -> bool:  # type: ignore[override]
        waiting = isinstance(self.env, ChatEnv) and self.env.has_pending_input_request()
        return self._exit or waiting

    def perceive(self) -> None:
        if self._step_count == 0:
            if not self.messages:
                today = datetime.now().strftime("%Y-%m-%d")
                self.messages.append(
                    {
                        "role": "system",
                        "content": f"{self.system_prompt}\n\nToday's date: {today}",
                    }
                )
                env_obs = (self.env.observe() or "").strip()
                if env_obs:
                    self.messages.append({"role": "system", "content": env_obs})
            self.messages.append({"role": "user", "content": f"Task: {self.env.task}"})

    def invoke(self) -> Any:
        if not self.lm or not self.messages:
            return None
        tools = self._tool_definitions if self._tool_definitions else None
        response = self.lm.invoke(messages=self.messages, tools=tools)
        self._last_response = response
        if hasattr(response, "output"):
            self.messages.extend(response.output)
        return response

    def do(self) -> None:
        if self._last_response is None:
            return
        output = getattr(self._last_response, "output", None)
        if output is None:
            return

        reasoning_items = [o for o in output if getattr(o, "type", None) == "reasoning"]
        message_items = [o for o in output if getattr(o, "type", None) == "message"]
        tool_calls = [o for o in output if getattr(o, "type", None) == TOOL_CALL_TYPE]

        for reasoning in reasoning_items:
            text = extract_reasoning_summary(reasoning)
            if text:
                self.env.output_handler(f"💭 {text}\n")

        for msg in message_items:
            text = extract_message_text(msg)
            if text:
                self.env.output_handler(text)

        if not tool_calls:
            return

        def _execute_tool(name: str, args: dict[str, Any]) -> Any:
            if name not in self._tool_callables:
                return f"Unknown tool: {name}"
            return self._tool_callables[name](**args)

        has_chat_tool_call = any(getattr(tc, "name", "") == "chat" for tc in tool_calls)
        run_parallel = (
            self.parallel_tool_calls
            and (not has_chat_tool_call)
            and len(tool_calls) > 1
        )

        if run_parallel:
            max_workers = max(1, int(self.max_concurrent_tool_calls or 1))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures: list[tuple[str, str, Any]] = []
                for tc in tool_calls:
                    name = getattr(tc, "name", "")
                    raw_args = getattr(tc, "arguments", "{}")
                    call_id = getattr(tc, "call_id", "")
                    if isinstance(raw_args, str):
                        try:
                            args = json.loads(raw_args)
                        except json.JSONDecodeError:
                            args = {}
                    else:
                        args = raw_args or {}
                    futures.append(
                        (name, call_id, executor.submit(_execute_tool, name, args))
                    )

                for name, call_id, fut in futures:
                    try:
                        result = fut.result(timeout=self.tool_timeout)
                    except FutureTimeoutError:
                        result = f"Error executing {name}: timed out after {self.tool_timeout}s"
                    except Exception as e:  # noqa: BLE001
                        result = f"Error executing {name}: {e}"
                    self.messages.append(format_openai_tool_response(result, call_id))
            return

        for tc in tool_calls:
            name = getattr(tc, "name", "")
            raw_args = getattr(tc, "arguments", "{}")
            call_id = getattr(tc, "call_id", "")
            if isinstance(raw_args, str):
                try:
                    args = json.loads(raw_args)
                except json.JSONDecodeError:
                    args = {}
            else:
                args = raw_args or {}

            if name in self._tool_callables:
                try:
                    if name == "chat":
                        result = self._tool_callables[name](**args)
                    else:
                        with tool_timeout(self.tool_timeout, name):
                            result = self._tool_callables[name](**args)
                except Exception as e:  # noqa: BLE001
                    result = f"Error executing {name}: {e}"
            else:
                result = f"Unknown tool: {name}"

            self.messages.append(format_openai_tool_response(result, call_id))
