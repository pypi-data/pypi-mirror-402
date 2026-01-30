from __future__ import annotations

import os
import subprocess
from typing import Any

from wbal.helper import weaveTool


@weaveTool
def bash(
    self,
    command: str,
    timeout_seconds: int = 60,
    cwd: str | None = None,
) -> dict[str, Any]:
    """
    Run a local bash command and return stdout/stderr/returncode.

    Notes:
    - This executes on the host running the agent (no sandbox).
    - Prefer read-only commands unless explicitly asked to modify state.
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
