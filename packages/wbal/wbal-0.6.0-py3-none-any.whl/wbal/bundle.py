from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AgentBundleEntry:
    """
    Agent bundle entrypoints.

    Mirrors the WandBSwarm contract:
    - run.sh is required
    - install.sh is optional
    """

    run: str = "run.sh"
    install: str = "install.sh"


def validate_agent_bundle(
    agent_dir: str | Path, *, entry: AgentBundleEntry | None = None
) -> None:
    entry = entry or AgentBundleEntry()
    agent_path = Path(agent_dir)
    if not agent_path.exists():
        raise ValueError(f"Agent bundle path does not exist: {agent_path}")
    if not agent_path.is_dir():
        raise ValueError(f"Agent bundle path is not a directory: {agent_path}")

    run_path = agent_path / entry.run
    if not run_path.exists():
        raise ValueError(f"Missing required agent bundle entrypoint: {run_path}")
    if not run_path.is_file():
        raise ValueError(f"Agent bundle entrypoint is not a file: {run_path}")

    install_path = agent_path / entry.install
    if install_path.exists() and not install_path.is_file():
        raise ValueError(
            f"Agent bundle install entrypoint is not a file: {install_path}"
        )


def run_agent_bundle(
    *,
    agent_dir: str | Path,
    task_dir: str | Path,
    workspace_dir: str | Path,
    entry: AgentBundleEntry | None = None,
    install: bool = True,
    run_id: str = "local",
    task_id: str = "local",
    experiment_id: str = "local",
    backend: str = "local",
    extra_env: dict[str, str] | None = None,
) -> int:
    """
    Run a WandBSwarm-compatible agent bundle locally.

    Contract (mirrors WandBSwarm):
    - Executes install.sh (if present) then run.sh
    - Uses cwd=TASK_DIR for both steps
    - Injects env vars: AGENT_DIR, TASK_DIR, WORKSPACE, RUN_ID, TASK_ID, EXPERIMENT_ID, BACKEND
    """
    entry = entry or AgentBundleEntry()
    validate_agent_bundle(agent_dir, entry=entry)

    agent_path = Path(agent_dir).resolve()
    task_path = Path(task_dir).resolve()
    workspace_path = Path(workspace_dir).resolve()

    if not task_path.exists() or not task_path.is_dir():
        raise ValueError(f"Task dir is not a directory: {task_path}")

    workspace_path.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.update(
        {
            "AGENT_DIR": str(agent_path),
            "TASK_DIR": str(task_path),
            "WORKSPACE": str(workspace_path),
            "RUN_ID": run_id,
            "TASK_ID": task_id,
            "EXPERIMENT_ID": experiment_id,
            "BACKEND": backend,
        }
    )

    if extra_env:
        reserved = {
            "AGENT_DIR",
            "TASK_DIR",
            "WORKSPACE",
            "RUN_ID",
            "TASK_ID",
            "EXPERIMENT_ID",
            "BACKEND",
        }
        overlaps = reserved.intersection(extra_env.keys())
        if overlaps:
            raise ValueError(
                f"extra_env cannot override reserved vars: {sorted(overlaps)}"
            )
        env.update(extra_env)

    install_path = agent_path / entry.install
    if install and install_path.exists():
        install_proc = subprocess.run(
            ["bash", str(install_path)], cwd=str(task_path), env=env, check=False
        )
        if install_proc.returncode != 0:
            return int(install_proc.returncode)

    run_path = agent_path / entry.run
    run_proc = subprocess.run(
        ["bash", str(run_path)], cwd=str(task_path), env=env, check=False
    )
    return int(run_proc.returncode)


def shell_agent_bundle(
    *,
    agent_dir: str | Path,
    task_dir: str | Path,
    workspace_dir: str | Path,
    run_id: str = "local",
    task_id: str = "local",
    experiment_id: str = "local",
    backend: str = "local",
    extra_env: dict[str, str] | None = None,
    shell: str = "bash",
    shell_args: list[str] | None = None,
) -> int:
    """Open an interactive shell with the same env contract as run_agent_bundle()."""
    shell_args = shell_args or []
    validate_agent_bundle(agent_dir)

    agent_path = Path(agent_dir).resolve()
    task_path = Path(task_dir).resolve()
    workspace_path = Path(workspace_dir).resolve()

    if not task_path.exists() or not task_path.is_dir():
        raise ValueError(f"Task dir is not a directory: {task_path}")

    workspace_path.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.update(
        {
            "AGENT_DIR": str(agent_path),
            "TASK_DIR": str(task_path),
            "WORKSPACE": str(workspace_path),
            "RUN_ID": run_id,
            "TASK_ID": task_id,
            "EXPERIMENT_ID": experiment_id,
            "BACKEND": backend,
        }
    )
    if extra_env:
        reserved = {
            "AGENT_DIR",
            "TASK_DIR",
            "WORKSPACE",
            "RUN_ID",
            "TASK_ID",
            "EXPERIMENT_ID",
            "BACKEND",
        }
        overlaps = reserved.intersection(extra_env.keys())
        if overlaps:
            raise ValueError(
                f"extra_env cannot override reserved vars: {sorted(overlaps)}"
            )
        env.update(extra_env)

    proc = subprocess.run(
        [shell, *shell_args], cwd=str(task_path), env=env, check=False
    )
    return int(proc.returncode)
