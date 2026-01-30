from __future__ import annotations

from pathlib import Path

import pytest

from wbal.bundle import run_agent_bundle, validate_agent_bundle


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestAgentBundle:
    def test_validate_requires_run_sh(self, tmp_path: Path) -> None:
        agent_dir = tmp_path / "agent"
        agent_dir.mkdir()
        with pytest.raises(
            ValueError, match="Missing required agent bundle entrypoint"
        ):
            validate_agent_bundle(agent_dir)

    def test_run_bundle_runs_run_sh(self, tmp_path: Path) -> None:
        agent_dir = tmp_path / "agent"
        task_dir = tmp_path / "task"
        workspace_dir = tmp_path / "workspace"
        agent_dir.mkdir()
        task_dir.mkdir()

        _write(task_dir / "TASK.md", "Hello\n")
        _write(
            agent_dir / "run.sh",
            """#!/usr/bin/env bash
set -euo pipefail

mkdir -p "${WORKSPACE}"
cp "${TASK_DIR}/TASK.md" "${WORKSPACE}/TASK.md.copy"
""",
        )

        rc = run_agent_bundle(
            agent_dir=agent_dir, task_dir=task_dir, workspace_dir=workspace_dir
        )
        assert rc == 0
        assert (workspace_dir / "TASK.md.copy").read_text(encoding="utf-8") == "Hello\n"

    def test_run_bundle_runs_install_sh_when_present(self, tmp_path: Path) -> None:
        agent_dir = tmp_path / "agent"
        task_dir = tmp_path / "task"
        workspace_dir = tmp_path / "workspace"
        agent_dir.mkdir()
        task_dir.mkdir()

        _write(task_dir / "TASK.md", "Hello\n")
        _write(
            agent_dir / "install.sh",
            """#!/usr/bin/env bash
set -euo pipefail

mkdir -p "${WORKSPACE}"
echo "installed" > "${WORKSPACE}/installed.txt"
""",
        )
        _write(
            agent_dir / "run.sh",
            """#!/usr/bin/env bash
set -euo pipefail

test -f "${WORKSPACE}/installed.txt"
""",
        )

        rc = run_agent_bundle(
            agent_dir=agent_dir, task_dir=task_dir, workspace_dir=workspace_dir
        )
        assert rc == 0
        assert (workspace_dir / "installed.txt").read_text(
            encoding="utf-8"
        ).strip() == "installed"
