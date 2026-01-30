from types import SimpleNamespace

import pytest

from wbal.helper import TOOL_CALL_TYPE
from wbal.lm import GPT5Large, GPT5MiniTester, KimiK2LM, LM


class DummyLM(LM):
    def observe(self) -> str:
        return "dummy"


class TestLMBase:
    """Tests for LM base class."""

    def test_lm_invoke_not_implemented(self):
        """Base LM.invoke() raises NotImplementedError."""
        dummy = DummyLM()
        with pytest.raises(NotImplementedError):
            dummy.invoke(messages=[])

    def test_lm_invoke_signature(self):
        """Base LM.invoke() has correct signature."""
        dummy = DummyLM()
        # Should accept these parameters without error (even though it raises)
        with pytest.raises(NotImplementedError):
            dummy.invoke(messages=[], tools=None, mcp_servers=None)


class TestGPT5Large:
    """Tests for GPT5Large."""

    def test_invoke_without_tools(self):
        """invoke() works without tools."""
        recorded_calls: list[dict] = []

        class DummyResponses:
            def create(self, **kwargs):
                recorded_calls.append(kwargs)
                return {"ok": True}

        class DummyClient:
            def __init__(self):
                self.responses = DummyResponses()

        lm = GPT5Large()
        lm.client = DummyClient()

        messages = [{"role": "user", "content": "hello"}]
        result = lm.invoke(messages=messages)

        assert result == {"ok": True}
        assert recorded_calls == [
            {
                "model": "gpt-5",
                "input": messages,
                "temperature": 1.0,
                "include": ["reasoning.encrypted_content"],
            }
        ]

    def test_invoke_with_tools_and_mcp(self):
        """invoke() combines tools and mcp_servers."""
        recorded_calls: list[dict] = []

        class DummyResponses:
            def create(self, **kwargs):
                recorded_calls.append(kwargs)
                return {"ok": True}

        class DummyClient:
            def __init__(self):
                self.responses = DummyResponses()

        lm = GPT5Large()
        lm.client = DummyClient()

        tools = [{"name": "tool1"}]
        mcp_servers = [{"name": "mcp1"}]

        result = lm.invoke(messages=[], tools=tools, mcp_servers=mcp_servers)

        assert result == {"ok": True}
        assert recorded_calls[0]["tools"] == [{"name": "tool1"}, {"name": "mcp1"}]

    def test_invoke_does_not_mutate_tools_list(self):
        """invoke() should NOT mutate the input tools list."""
        recorded_calls: list[dict] = []

        class DummyResponses:
            def create(self, **kwargs):
                recorded_calls.append(kwargs)
                return {"ok": True}

        class DummyClient:
            def __init__(self):
                self.responses = DummyResponses()

        lm = GPT5Large()
        lm.client = DummyClient()

        tools = [{"name": "tool1"}]
        mcp_servers = [{"name": "mcp1"}]

        lm.invoke(messages=[], tools=tools, mcp_servers=mcp_servers)

        # Original tools list should NOT be mutated
        assert tools == [{"name": "tool1"}], "tools list was mutated!"

    def test_invoke_with_only_mcp_servers(self):
        """invoke() works with only mcp_servers (no tools)."""
        recorded_calls: list[dict] = []

        class DummyResponses:
            def create(self, **kwargs):
                recorded_calls.append(kwargs)
                return {"ok": True}

        class DummyClient:
            def __init__(self):
                self.responses = DummyResponses()

        lm = GPT5Large()
        lm.client = DummyClient()

        mcp_servers = [{"name": "mcp1"}]
        lm.invoke(messages=[], tools=None, mcp_servers=mcp_servers)

        assert recorded_calls[0]["tools"] == [{"name": "mcp1"}]


class TestGPT5MiniTester:
    """Tests for GPT5MiniTester."""

    def test_invoke_basic(self):
        """invoke() works with basic parameters."""
        recorded_calls: list[dict] = []

        class DummyResponses:
            def create(self, **kwargs):
                recorded_calls.append(kwargs)
                return {"ok": True}

        class DummyClient:
            def __init__(self):
                self.responses = DummyResponses()

        lm = GPT5MiniTester()
        lm.client = DummyClient()

        messages = [{"role": "user", "content": "test"}]
        result = lm.invoke(messages=messages)

        assert result == {"ok": True}
        assert recorded_calls[0]["model"] == "gpt-5-mini"
        assert recorded_calls[0]["reasoning"] == {"effort": "minimal"}

    def test_invoke_does_not_mutate_tools_list(self):
        """GPT5MiniTester.invoke() should NOT mutate the input tools list."""
        recorded_calls: list[dict] = []

        class DummyResponses:
            def create(self, **kwargs):
                recorded_calls.append(kwargs)
                return {"ok": True}

        class DummyClient:
            def __init__(self):
                self.responses = DummyResponses()

        lm = GPT5MiniTester()
        lm.client = DummyClient()

        tools = [{"name": "tool1"}]
        mcp_servers = [{"name": "mcp1"}]

        lm.invoke(messages=[], tools=tools, mcp_servers=mcp_servers)

        # Original tools list should NOT be mutated
        assert tools == [{"name": "tool1"}], "tools list was mutated!"

    def test_observe(self):
        """observe() returns model description."""
        lm = GPT5MiniTester()
        obs = lm.observe()
        assert "GPT5MiniTester" in obs
        assert "gpt-5-mini" in obs


class TestKimiK2LM:
    """Tests for KimiK2LM."""

    def test_invoke_combines_tools_and_mcp(self):
        """invoke() combines tools and mcp_servers without mutation."""
        recorded_calls: list[dict] = []

        class DummyCompletions:
            def create(self, **kwargs):
                recorded_calls.append(kwargs)
                # Simulate a basic assistant reply
                message = SimpleNamespace(role="assistant", content="hello", tool_calls=[])
                return SimpleNamespace(choices=[SimpleNamespace(message=message)])

        class DummyClient:
            def __init__(self):
                self.chat = SimpleNamespace(completions=DummyCompletions())

        tools = [{"name": "tool1"}]
        mcp = [{"name": "mcp1"}]

        lm = KimiK2LM(client=DummyClient())
        result = lm.invoke(messages=[{"role": "user", "content": "hi"}], tools=tools, mcp_servers=mcp)

        assert result.output_text == "hello"
        assert recorded_calls[0]["tools"] == [{"name": "tool1"}, {"name": "mcp1"}]
        # Ensure tools list not mutated
        assert tools == [{"name": "tool1"}]

    def test_invoke_returns_tool_calls(self):
        """invoke() surfaces tool calls as function_call items."""

        class DummyFunction:
            def __init__(self, name, arguments):
                self.name = name
                self.arguments = arguments

        class DummyToolCall:
            def __init__(self, id, name, arguments):
                self.id = id
                self.type = "function"
                self.function = DummyFunction(name, arguments)

        class DummyCompletions:
            def create(self, **kwargs):
                tool_calls = [DummyToolCall("call_1", "do_work", '{"x": 1}')]
                message = SimpleNamespace(role="assistant", content=None, tool_calls=tool_calls)
                return SimpleNamespace(choices=[SimpleNamespace(message=message)])

        class DummyClient:
            def __init__(self):
                self.chat = SimpleNamespace(completions=DummyCompletions())

        lm = KimiK2LM(client=DummyClient())
        response = lm.invoke(messages=[{"role": "user", "content": "go"}])

        assert len(response.output) == 1
        tc = response.output[0]
        assert getattr(tc, "type", "") == TOOL_CALL_TYPE
        assert getattr(tc, "name", "") == "do_work"
        assert getattr(tc, "call_id", "") == "call_1"

    def test_observe_includes_project(self, monkeypatch):
        """observe() includes project and model info."""
        monkeypatch.setenv("WEAVE_PROJECT", "team/proj")

        class DummyClient:
            def __init__(self):
                self.chat = SimpleNamespace(completions=None)

        lm = KimiK2LM(client=DummyClient())
        obs = lm.observe()
        assert "KimiK2LM" in obs
        assert "team/proj" in obs
