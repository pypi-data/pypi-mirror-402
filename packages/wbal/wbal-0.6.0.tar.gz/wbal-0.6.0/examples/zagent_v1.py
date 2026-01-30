"""
zagent_v1

An example "orchestrator" agent built on WBAL's OpenAIWBAgent.

Features:
- Notes dict persisted via the env (create/update/remove tools)
- Notes injected as the 2nd system message (kept up-to-date each step)
- Bash tool for running shell commands
- Optional check that `codex` is installed locally
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime
from typing import Any

import weave
from pydantic import Field

from wbal.agents.openai_agent import OpenAIWBAgent
from wbal.environments.chat_env import ChatEnv
from wbal.environments.poll_env import PollEnv
from wbal.helper import weaveTool
from wbal.lm import LM, GPT5MiniTester

ZAGENT_V1_SYSTEM_PROMPT = """You are zagent_v1, an orchestrator system.

You are responsible for coordinating work across tools, keeping durable notes, and producing crisp outcomes.

Operating principles:
- Be decisive and structured: break tasks into steps, execute, and summarize.
- Prefer tools over guesses: verify with tools (especially bash) when correctness matters.
- Maintain a durable notes dictionary as shared state:
  - Use write_note/update_note/remove_note to keep notes accurate and minimal.
  - Treat the system-provided notes as the source of truth.
  - Store decisions, TODOs, constraints, and key facts (not long transcripts).
- Use bash safely:
  - Default to read-only commands (`ls`, `rg`, `cat`, `python -c`, etc.).
  - Avoid destructive commands unless explicitly asked (no `rm -rf`, no `git reset --hard`, etc.).
  - Return stdout/stderr/exit code; keep outputs concise.

When you are done, call exit() with a brief handoff summary."""


class ZAgentV1Env(ChatEnv, PollEnv):
    """
    An environment that supports:
    - chat() (from ChatEnv)
    - persistent notes + observations (from PollEnv/DataEnv)
    - explicit note CRUD tools (wrappers around PollEnv)
    - bash command execution
    """

    include_working_directory_listing: bool = False

    def _notes_content_map(self) -> dict[str, str]:
        notes: dict[str, Any] = self._state.get("notes", {})
        return {
            k: (v.get("content") if isinstance(v, dict) else str(v))
            for k, v in notes.items()
        }

    @weaveTool
    def write_note(
        self, key: str, content: str, category: str = "general"
    ) -> dict[str, Any]:
        """Create a new note. Fails if the key already exists."""
        if key in self._state.get("notes", {}):
            return {"success": False, "error": f"Note '{key}' already exists"}
        return self.store_note(key=key, content=content, category=category)

    @weaveTool
    def update_note(
        self, key: str, content: str, category: str = "general"
    ) -> dict[str, Any]:
        """Update an existing note. Fails if the key does not exist."""
        if key not in self._state.get("notes", {}):
            return {"success": False, "error": f"Note '{key}' does not exist"}
        return self.store_note(key=key, content=content, category=category)

    @weaveTool
    def remove_note(self, key: str) -> dict[str, Any]:
        """Remove an existing note."""
        return self.delete_note(key=key)

    @weaveTool
    def bash(
        self, command: str, timeout_seconds: int = 60, cwd: str | None = None
    ) -> dict[str, Any]:
        """
        Run a bash command locally and return stdout/stderr/returncode.

        Args:
            command: Bash command string (executed via `bash -lc`)
            timeout_seconds: Max runtime before killing the process
            cwd: Optional working directory
        """
        run_cwd = cwd or os.getcwd()
        try:
            completed = subprocess.run(
                ["bash", "-lc", command],
                cwd=run_cwd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
            return {
                "success": completed.returncode == 0,
                "returncode": completed.returncode,
                "cwd": run_cwd,
                "stdout": stdout[:8000],
                "stderr": stderr[:8000],
            }
        except subprocess.TimeoutExpired as e:
            return {
                "success": False,
                "returncode": 124,
                "cwd": run_cwd,
                "stdout": (e.stdout or "")[:8000] if isinstance(e.stdout, str) else "",
                "stderr": (e.stderr or "")[:8000] if isinstance(e.stderr, str) else "",
                "error": f"Timed out after {timeout_seconds}s",
            }


class ZAgentV1(OpenAIWBAgent):
    """zagent_v1: OpenAIWBAgent with notes injected as 2nd system message."""

    lm: LM = Field(default_factory=GPT5MiniTester)
    system_prompt: str = ZAGENT_V1_SYSTEM_PROMPT

    def _notes_system_message(self) -> str:
        env = self.env
        notes = env._notes_content_map() if isinstance(env, ZAgentV1Env) else {}
        return "Notes (JSON):\n" + json.dumps(notes, indent=2, sort_keys=True)

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
                self.messages.append(
                    {"role": "system", "content": self._notes_system_message()}
                )
                self.messages.append({"role": "system", "content": self.env.observe()})
            self.messages.append({"role": "user", "content": f"Task: {self.env.task}"})
        else:
            # Keep the "2nd system message" (notes) up to date.
            if len(self.messages) >= 2 and self.messages[1].get("role") == "system":
                self.messages[1]["content"] = self._notes_system_message()


def _ensure_codex_installed() -> None:
    if subprocess.run(["codex", "--version"], capture_output=True).returncode != 0:
        raise RuntimeError(
            "codex CLI not found. Install it first (e.g., ensure `codex --version` works)."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run zagent_v1")
    parser.add_argument(
        "--task", type=str, default="", help="Task string (overrides TASK.md if set)"
    )
    parser.add_argument(
        "--task-file",
        type=str,
        default="",
        help="Optional path to TASK.md (used if --task is empty)",
    )
    parser.add_argument(
        "--working-dir",
        type=str,
        default=os.getenv("WBAL_WORKING_DIR")
        or os.getenv("WORKSPACE")
        or "./.zagent_v1_state",
        help="Directory for state persistence (notes/observations)",
    )
    parser.add_argument(
        "--weave-project",
        type=str,
        default=os.getenv("WEAVE_PROJECT", ""),
        help="Optional Weave project to log to",
    )
    parser.add_argument(
        "--skip-codex-check",
        action="store_true",
        help="Skip checking that `codex` is installed",
    )
    args = parser.parse_args()

    if not args.skip_codex_check:
        _ensure_codex_installed()

    if args.weave_project:
        weave.init(args.weave_project)

    task = args.task.strip()
    if not task and args.task_file:
        try:
            task = open(args.task_file, "r", encoding="utf-8").read().strip()
        except OSError:
            task = ""
    if not task:
        task = "Introduce yourself, summarize available tools, then call exit()."

    env = ZAgentV1Env(task=task, working_directory=args.working_dir)
    env.env = "Local orchestrator environment (notes + bash)."
    agent = ZAgentV1(env=env, maxSteps=20)
    agent.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
