from __future__ import annotations

from pathlib import Path

import pytest
from wbal.cli import build_parser
from wbal.manifests import build_agent_from_file


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_cli_has_run_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["run", "--project", "p", "--task", "t"])
    assert args.command == "run"


def test_cli_has_agents_run_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["agents", "run", "--spec", "a.yaml", "--task", "t"])
    assert args.command == "agents"
    assert args.agents_command == "run"


def test_build_agent_from_yaml_and_run_with_scripted_lm(tmp_path: Path) -> None:
    prompt_path = tmp_path / "prompt.yaml"
    agent_path = tmp_path / "agent.yaml"

    _write(
        prompt_path,
        """
system: |
  You are a test agent.
system_messages:
  - Extra message.
""".lstrip(),
    )

    _write(
        agent_path,
        f"""
name: test_agent
description: test
prompt: {prompt_path.name}
lm:
  kind: scripted
  script:
    - exit: done
env:
  kind: data
  env: env text
  working_directory: {str(tmp_path / "state")}
max_steps: 5
""".lstrip(),
    )

    agent = build_agent_from_file(agent_path, task="t")
    outputs: list[str] = []
    agent.env.output_handler = lambda x: outputs.append(x)

    result = agent.run(task="t")
    assert result["steps"] == 1
    assert agent._exit is True
    assert agent._exit_message == "done"
    assert outputs == ["done"]


def test_env_tool_modules_attached(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Create an importable tool module at runtime.
    tool_mod = tmp_path / "my_tools.py"
    _write(
        tool_mod,
        """
from wbal.helper import tool

@tool
def ping(self, x: str) -> str:
    \"\"\"Return pong.\"\"\"
    return f\"pong:{x}\"
""".lstrip(),
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    agent_path = tmp_path / "agent.yaml"
    _write(
        agent_path,
        """
name: tool_agent
lm:
  kind: scripted
  script:
    - exit: ok
env:
  kind: data
tools:
  env:
    - my_tools
""".lstrip(),
    )

    agent = build_agent_from_file(agent_path, task="t")
    assert "ping" in agent._tool_callables
    assert agent._tool_callables["ping"](x="a") == "pong:a"


def test_run_agent_delegation_uses_declared_delegates(tmp_path: Path) -> None:
    child_path = tmp_path / "child.yaml"
    parent_path = tmp_path / "parent.yaml"
    parent_state = tmp_path / "state"

    _write(
        child_path,
        """
name: child
description: child desc
lm:
  kind: scripted
  script:
    - exit: child_done
env:
  kind: data
""".lstrip(),
    )

    _write(
        parent_path,
        f"""
name: parent
lm:
  kind: scripted
  script:
    - exit: parent_done
env:
  kind: data
  working_directory: {str(parent_state)}
delegates:
  child: {child_path.name}
""".lstrip(),
    )

    parent = build_agent_from_file(parent_path, task="t")
    out = parent.run_agent(agent="child", task="do child")

    assert out["success"] is True
    assert out["agent"] == "child"
    assert out["description"] == "child desc"
    assert out["exit_message"] == "child_done"
    assert out["working_directory"] == str(parent_state)

    bad = parent.run_agent(agent="nope", task="x")
    assert bad["success"] is False
    assert "Allowed" in bad["error"]


def test_build_agent_from_yaml_with_lm_import_path_and_template_vars(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "prompt.yaml"
    agent_path = tmp_path / "agent.yaml"

    _write(
        prompt_path,
        """
system: |
  Hello {who}.
system_messages:
  - Extra {who}.
""".lstrip(),
    )

    _write(
        agent_path,
        f"""
name: test_agent
prompt: {prompt_path.name}
lm:
  import_path: wbal.lm:ScriptedLM
  kwargs:
    script:
      - exit: done
env:
  kind: basic
  env: Env for {{who}}.
system_messages:
  - Also {{who}}.
max_steps: 3
""".lstrip(),
    )

    agent = build_agent_from_file(agent_path, task="t", template_vars={"who": "world"})
    assert agent.system_prompt.strip() == "Hello world."
    assert agent.system_messages == ["Extra world.", "Also world."]
    assert agent.env.env.strip() == "Env for world."


def test_run_agent_spec_applies_set_overrides(tmp_path: Path) -> None:
    from wbal.runner import run_agent_spec

    prompt_path = tmp_path / "prompt.yaml"
    agent_path = tmp_path / "agent.yaml"

    _write(
        prompt_path,
        """
system: |
  Base prompt.
""".lstrip(),
    )

    _write(
        agent_path,
        f"""
name: test_agent
prompt: {prompt_path.name}
lm:
  import_path: wbal.lm:ScriptedLM
  kwargs:
    script:
      - exit: done
env:
  kind: basic
  env: Base env.
max_steps: 3
""".lstrip(),
    )

    meta = run_agent_spec(
        spec_path=agent_path,
        task="t",
        max_steps=1,
        set_overrides=[
            "system_prompt=Overridden prompt.",
            "env.env=Overridden env.",
        ],
    )
    assert meta["steps"] == 1
