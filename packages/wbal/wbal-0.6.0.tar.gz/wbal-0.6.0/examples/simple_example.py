"""
Minimal WBAL example.

Run:
  uv run python examples/simple_example.py
"""

from __future__ import annotations

import os

import weave

from wbal import ChatEnv, GPT5MiniTester, OpenAIWBAgent, weaveTool


class SimpleEnv(ChatEnv):
    env = "You are a helpful assistant."
    include_working_directory_listing = False

    @weaveTool
    def greet(self, name: str) -> str:
        """Greet someone by name."""
        return f"Hello, {name}!"


def main() -> int:
    weave.init(os.getenv("WEAVE_PROJECT", "my-project"))
    env = SimpleEnv(
        task="Use greet to say hello to Alice, then call exit().",
        working_directory="./.wbal_state",
    )
    agent = OpenAIWBAgent(
        env=env,
        lm=GPT5MiniTester(),
        maxSteps=10,
        system_prompt="Use tools when helpful. Call exit() when you're done.",
    )
    agent.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
