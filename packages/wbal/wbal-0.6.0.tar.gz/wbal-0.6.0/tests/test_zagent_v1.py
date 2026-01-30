"""Tests for the zagent_v1 example."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

# Add examples to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / "examples"))

from zagent_v1 import ZAgentV1, ZAgentV1Env


class TestZAgentV1Env:
    def test_note_crud(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = ZAgentV1Env(task="t", working_directory=tmp)

            created = env.write_note("a", "hello")
            assert created["success"] is True

            dup = env.write_note("a", "nope")
            assert dup["success"] is False

            updated = env.update_note("a", "world")
            assert updated["success"] is True

            missing_update = env.update_note("missing", "x")
            assert missing_update["success"] is False

            deleted = env.remove_note("a")
            assert deleted["success"] is True


class TestZAgentV1:
    def test_notes_are_second_system_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = ZAgentV1Env(task="t", working_directory=tmp)
            env.write_note("k", "v")

            agent = ZAgentV1(env=env, maxSteps=1)
            agent.perceive()

            assert len(agent.messages) == 4
            assert agent.messages[0]["role"] == "system"
            assert agent.messages[1]["role"] == "system"
            assert agent.messages[2]["role"] == "system"
            assert agent.messages[3]["role"] == "user"

            notes_msg = agent.messages[1]["content"]
            assert "Notes (JSON)" in notes_msg
            assert '"k": "v"' in notes_msg

    def test_notes_message_updates_on_next_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = ZAgentV1Env(task="t", working_directory=tmp)
            env.write_note("k", "v1")

            agent = ZAgentV1(env=env, maxSteps=2)
            agent.perceive()
            assert '"k": "v1"' in agent.messages[1]["content"]

            env.update_note("k", "v2")
            agent._step_count = 1
            agent.perceive()
            assert '"k": "v2"' in agent.messages[1]["content"]
