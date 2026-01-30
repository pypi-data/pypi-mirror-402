from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

import weave

from wbal.manifests import build_agent_from_file


def parse_kv_pairs(pairs: list[str] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise ValueError(f"Invalid KEY=VALUE pair: {pair!r}")
        key, value = pair.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Invalid KEY=VALUE pair (empty key): {pair!r}")
        out[key] = value
    return out


def _coerce_value(raw: str) -> Any:
    raw = raw.strip()
    if raw == "":
        return ""
    try:
        return json.loads(raw)
    except Exception:
        return raw


def parse_set_overrides(pairs: list[str] | None) -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    for pair in pairs or []:
        if "=" not in pair:
            raise ValueError(f"Invalid --set value (expected PATH=VALUE): {pair!r}")
        path, raw_value = pair.split("=", 1)
        path = path.strip()
        if not path:
            raise ValueError(f"Invalid --set value (empty path): {pair!r}")
        out.append((path, _coerce_value(raw_value)))
    return out


def _resolve_path(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        if key not in obj:
            raise KeyError(key)
        return obj[key]
    return getattr(obj, key)


def _assign_path(obj: Any, key: str, value: Any) -> None:
    if isinstance(obj, dict):
        obj[key] = value
        return
    setattr(obj, key, value)


def apply_overrides(agent: Any, overrides: list[tuple[str, Any]]) -> None:
    """
    Apply dotted-path overrides to an instantiated agent.

    Supported roots:
    - `agent.*` (explicit)
    - `lm.*`
    - `env.*`
    - otherwise paths are relative to the agent object

    Examples:
    - `lm.model=gpt-5-mini`
    - `agent.tool_timeout=1800`
    - `system_prompt="..."`  (relative to agent)
    """
    for path, value in overrides:
        parts = [p for p in path.split(".") if p]
        if not parts:
            raise ValueError(f"Invalid override path: {path!r}")

        if parts[0] in {"agent", "lm", "env"}:
            root = parts[0]
            parts = parts[1:]
            if root == "agent":
                obj = agent
            else:
                obj = getattr(agent, root, None)
                if obj is None:
                    raise ValueError(f"Override root {root!r} is not present on agent")
        else:
            obj = agent

        if not parts:
            raise ValueError(f"Override path must include a field name: {path!r}")

        for key in parts[:-1]:
            try:
                obj = _resolve_path(obj, key)
            except Exception as e:  # noqa: BLE001
                raise ValueError(
                    f"Invalid override path segment {key!r} in {path!r}"
                ) from e

        leaf = parts[-1]
        try:
            _assign_path(obj, leaf, value)
        except Exception as e:  # noqa: BLE001
            raise ValueError(f"Failed to set {path!r} on {type(obj).__name__}") from e


def write_run_metadata(path: str | Path, payload: dict[str, Any]) -> None:
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def run_agent_spec(
    *,
    spec_path: str | Path,
    task: str,
    max_steps: int | None = None,
    working_directory: str | None = None,
    env_kind: Literal["basic", "data", "chat", "poll"] | None = None,
    env_description: str | None = None,
    template_vars: dict[str, Any] | None = None,
    set_overrides: list[str] | None = None,
    env_overrides: dict[str, str] | None = None,
    weave_project: str | None = None,
    metadata_out: str | None = None,
) -> dict[str, Any]:
    """
    Load a YAML agent spec and run it with consistent wiring.

    This is intended to be the shared implementation behind:
    - `wbal agents run`
    - lightweight wrappers in other packages (e.g. `factory-f1`)
    """
    if env_overrides:
        for k, v in env_overrides.items():
            os.environ[k] = v

    if weave_project:
        os.environ["WEAVE_PROJECT"] = weave_project
        weave.init(weave_project)

    agent = build_agent_from_file(
        spec_path,
        task=task,
        max_steps=max_steps,
        working_directory=working_directory,
        env_kind=env_kind,
        env_description=env_description,
        template_vars=template_vars,
    )

    overrides = parse_set_overrides(set_overrides)
    if overrides:
        apply_overrides(agent, overrides)

    run_result = agent.run(task=task, max_steps=max_steps)
    exit_message = getattr(agent, "_exit_message", "") or ""
    usage = getattr(agent, "usage_totals", lambda: {})()

    meta: dict[str, Any] = {
        "spec": str(getattr(agent, "manifest_path", "") or str(spec_path)),
        "task": task,
        "steps": run_result.get("steps"),
        "exit_message": exit_message,
        "model": getattr(getattr(agent, "lm", None), "model", None),
        "usage": usage,
    }

    if metadata_out:
        write_run_metadata(metadata_out, meta)

    return meta
