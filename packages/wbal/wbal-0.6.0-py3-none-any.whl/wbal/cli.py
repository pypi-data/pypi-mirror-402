from __future__ import annotations

import argparse
import time

from wbal.agents.openai_agent import OpenAIWBAgent
from wbal.bundle import run_agent_bundle, shell_agent_bundle, validate_agent_bundle
from wbal.environments.chat_env import ChatEnv
from wbal.environments.data_env import DataEnv
from wbal.environments.poll_env import PollEnv
from wbal.manifests import build_agent_from_file
from wbal.runner import parse_kv_pairs, run_agent_spec


def _parse_env(pairs: list[str] | None) -> dict[str, str]:
    env: dict[str, str] = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise ValueError(f"Invalid --env value (expected KEY=VALUE): {pair!r}")
        key, value = pair.split("=", 1)
        env[key] = value
    return env


def _resolve_agent_spec_from_name(name: str, search_dir: str) -> str:
    base = Path(search_dir).expanduser().resolve()
    candidates = [
        base / f"{name}.agent.yaml",
        base / f"{name}.yaml",
    ]
    for p in candidates:
        if p.exists():
            return str(p)

    matches = list(base.rglob(f"{name}.agent.yaml")) + list(base.rglob(f"{name}.yaml"))
    matches = [m for m in matches if m.is_file()]
    if len(matches) == 1:
        return str(matches[0])
    if len(matches) > 1:
        raise ValueError(
            f"Multiple specs matched name {name!r} under {str(base)!r}: {[str(m) for m in matches]}"
        )
    raise ValueError(f"No spec found for name {name!r} under {str(base)!r}")


def _cmd_agents_run(args: argparse.Namespace) -> int:
    if not args.spec and not args.name:
        raise ValueError("Provide either NAME or --spec PATH")

    spec = args.spec
    if not spec:
        spec = _resolve_agent_spec_from_name(args.name, args.dir)

    template_vars = parse_kv_pairs(args.var)
    env_overrides = parse_kv_pairs(args.env)

    run_agent_spec(
        spec_path=spec,
        task=args.task,
        max_steps=args.max_steps,
        working_directory=args.working_dir,
        env_kind=args.env_kind,
        template_vars=template_vars or None,
        set_overrides=args.set or None,
        env_overrides=env_overrides or None,
        weave_project=args.weave_project or None,
        metadata_out=args.metadata_out or None,
    )
    return 0


def _cmd_agents_validate(args: argparse.Namespace) -> int:
    template_vars = parse_kv_pairs(args.var)
    env_overrides = parse_kv_pairs(args.env)

    # Env overrides must be applied before instantiating LMs/tools.
    if env_overrides:
        import os

        for k, v in env_overrides.items():
            os.environ[k] = v

    # Validate by loading + instantiating (but not running).
    build_agent_from_file(
        args.spec,
        task=args.task or "",
        max_steps=0,
        working_directory=args.working_dir,
        env_kind=args.env_kind,
        template_vars=template_vars or None,
    )
    return 0


def _cmd_agents_list(args: argparse.Namespace) -> int:
    base = Path(args.dir).expanduser().resolve()
    patterns = ["*.agent.yaml", "*.yaml"]
    seen: set[Path] = set()
    matches: list[Path] = []
    for pat in patterns:
        matches.extend(base.rglob(pat) if args.recursive else base.glob(pat))
    for m in matches:
        if m.is_file():
            seen.add(m)

    for p in sorted(seen):
        print(str(p))
    return 0


def _cmd_chat(args: argparse.Namespace) -> int:
    env_description = f"Org: {args.org}\nProject: {args.project}"
    if args.agent_spec:
        template_vars = parse_kv_pairs(args.var)
        env_overrides = parse_kv_pairs(args.env)
        run_agent_spec(
            spec_path=args.agent_spec,
            task=args.task or "",
            max_steps=args.max_steps,
            working_directory=args.working_dir,
            env_kind="chat",
            env_description=env_description,
            template_vars=template_vars or None,
            set_overrides=args.set or None,
            env_overrides=env_overrides or None,
            weave_project=args.weave_project or None,
            metadata_out=args.metadata_out or None,
        )
        return 0

    env = ChatEnv(task=args.task or "", working_directory=args.working_dir)
    env.env = env_description
    OpenAIWBAgent(env=env).run(task=args.task, max_steps=args.max_steps)
    return 0


def _cmd_poll(args: argparse.Namespace) -> int:
    def run_once() -> None:
        env_description = f"Org: {args.org}\nProject: {args.project}"
        if args.agent_spec:
            template_vars = parse_kv_pairs(args.var)
            env_overrides = parse_kv_pairs(args.env)
            run_agent_spec(
                spec_path=args.agent_spec,
                task=args.task or "",
                max_steps=args.max_steps,
                working_directory=args.working_dir,
                env_kind="poll",
                env_description=env_description,
                template_vars=template_vars or None,
                set_overrides=args.set or None,
                env_overrides=env_overrides or None,
                weave_project=args.weave_project or None,
                metadata_out=args.metadata_out or None,
            )
            return

        env = PollEnv(task=args.task or "", working_directory=args.working_dir)
        env.env = env_description
        OpenAIWBAgent(env=env).run(task=args.task, max_steps=args.max_steps)

    if args.interval:
        while True:
            run_once()
            time.sleep(args.interval)
    else:
        run_once()

    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    env_description = f"Org: {args.org}\nProject: {args.project}"
    if args.agent_spec:
        template_vars = parse_kv_pairs(args.var)
        env_overrides = parse_kv_pairs(args.env)
        run_agent_spec(
            spec_path=args.agent_spec,
            task=args.task or "",
            max_steps=args.max_steps,
            working_directory=args.working_dir,
            env_description=env_description,
            template_vars=template_vars or None,
            set_overrides=args.set or None,
            env_overrides=env_overrides or None,
            weave_project=args.weave_project or None,
            metadata_out=args.metadata_out or None,
        )
        return 0

    env = DataEnv(task=args.task or "", working_directory=args.working_dir)
    env.env = env_description
    OpenAIWBAgent(env=env).run(task=args.task, max_steps=args.max_steps)
    return 0


def _cmd_bundle_validate(args: argparse.Namespace) -> int:
    validate_agent_bundle(args.agent_dir)
    return 0


def _cmd_bundle_run(args: argparse.Namespace) -> int:
    extra_env = _parse_env(args.env)
    return run_agent_bundle(
        agent_dir=args.agent_dir,
        task_dir=args.task_dir,
        workspace_dir=args.workspace_dir,
        install=not args.skip_install,
        run_id=args.run_id,
        task_id=args.task_id,
        experiment_id=args.experiment_id,
        backend=args.backend,
        extra_env=extra_env or None,
    )


def _cmd_bundle_shell(args: argparse.Namespace) -> int:
    extra_env = _parse_env(args.env)
    return shell_agent_bundle(
        agent_dir=args.agent_dir,
        task_dir=args.task_dir,
        workspace_dir=args.workspace_dir,
        run_id=args.run_id,
        task_id=args.task_id,
        experiment_id=args.experiment_id,
        backend=args.backend,
        extra_env=extra_env or None,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wbal", description="WBAL CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    agents_p = sub.add_parser("agents", help="Run YAML-first agents")
    agents_sub = agents_p.add_subparsers(dest="agents_command", required=True)

    agents_run_p = agents_sub.add_parser("run", help="Run an agent from YAML spec")
    agents_run_p.add_argument(
        "name", nargs="?", default=None, help="Agent name (optional)"
    )
    agents_run_p.add_argument(
        "--spec", type=str, default=None, help="Path to agent YAML spec"
    )
    agents_run_p.add_argument(
        "--dir",
        type=str,
        default=".",
        help="Directory to search for NAME (default: .)",
    )
    agents_run_p.add_argument(
        "--task", type=str, required=True, help="Task for the agent"
    )
    agents_run_p.add_argument(
        "--working-dir", type=str, default=None, help="Override env working directory"
    )
    agents_run_p.add_argument(
        "--max-steps",
        type=int,
        default=None,
        help="Override max steps (default: from YAML)",
    )
    agents_run_p.add_argument(
        "--env-kind",
        type=str,
        default=None,
        choices=["basic", "data", "chat", "poll"],
        help="Override env kind (default: from YAML)",
    )
    agents_run_p.add_argument(
        "--var",
        action="append",
        default=[],
        help="Template var for YAML prompts, in KEY=VALUE format (repeatable)",
    )
    agents_run_p.add_argument(
        "--set",
        action="append",
        default=[],
        help="Override a field on the instantiated agent, in PATH=VALUE format (repeatable)",
    )
    agents_run_p.add_argument(
        "--env",
        action="append",
        default=[],
        help="Set an env var for the run, in KEY=VALUE format (repeatable)",
    )
    agents_run_p.add_argument(
        "--weave-project",
        type=str,
        default="",
        help="Optional Weave project for tracing",
    )
    agents_run_p.add_argument(
        "--metadata-out",
        type=str,
        default="",
        help="Optional path to write JSON run metadata",
    )
    agents_run_p.set_defaults(func=_cmd_agents_run)

    agents_validate_p = agents_sub.add_parser(
        "validate", help="Validate a YAML spec without running it"
    )
    agents_validate_p.add_argument(
        "--spec", required=True, help="Path to agent YAML spec"
    )
    agents_validate_p.add_argument(
        "--working-dir", type=str, default=None, help="Override env working directory"
    )
    agents_validate_p.add_argument(
        "--env-kind",
        type=str,
        default=None,
        choices=["basic", "data", "chat", "poll"],
        help="Override env kind (default: from YAML)",
    )
    agents_validate_p.add_argument(
        "--task", type=str, default="", help="Optional task (defaults to empty)"
    )
    agents_validate_p.add_argument(
        "--var",
        action="append",
        default=[],
        help="Template var for YAML prompts, in KEY=VALUE format (repeatable)",
    )
    agents_validate_p.add_argument(
        "--env",
        action="append",
        default=[],
        help="Set an env var for validation, in KEY=VALUE format (repeatable)",
    )
    agents_validate_p.set_defaults(func=_cmd_agents_validate)

    agents_list_p = agents_sub.add_parser("list", help="List YAML specs in a directory")
    agents_list_p.add_argument(
        "--dir", type=str, default=".", help="Directory to scan (default: .)"
    )
    agents_list_p.add_argument(
        "--recursive", action="store_true", help="Scan recursively"
    )
    agents_list_p.set_defaults(func=_cmd_agents_list)

    chat_p = sub.add_parser("chat", help="Run an interactive chat agent")
    chat_p.add_argument(
        "--agent-spec",
        type=str,
        default=None,
        help="Path to an agent YAML manifest (optional).",
    )
    chat_p.add_argument("--task", type=str, default="", help="Task for the agent")
    chat_p.add_argument(
        "--working-dir", type=str, default=None, help="Directory for state persistence"
    )
    chat_p.add_argument(
        "--weave-project",
        type=str,
        default="",
        help="Optional Weave project for tracing",
    )
    chat_p.add_argument(
        "--metadata-out",
        type=str,
        default="",
        help="Optional path to write JSON run metadata",
    )
    chat_p.add_argument(
        "--max-steps",
        type=int,
        default=20,
        help="Max steps before stopping (default: 20)",
    )
    chat_p.add_argument(
        "--org", type=str, default="", help="Organization name (optional)"
    )
    chat_p.add_argument(
        "--project", type=str, required=True, help="Project name (required)"
    )
    chat_p.add_argument(
        "--var",
        action="append",
        default=[],
        help="Template var for YAML prompts, in KEY=VALUE format (repeatable)",
    )
    chat_p.add_argument(
        "--set",
        action="append",
        default=[],
        help="Override a field on the instantiated agent, in PATH=VALUE format (repeatable)",
    )
    chat_p.add_argument(
        "--env",
        action="append",
        default=[],
        help="Set an env var for the run, in KEY=VALUE format (repeatable)",
    )
    chat_p.set_defaults(func=_cmd_chat)

    poll_p = sub.add_parser("poll", help="Run a polling agent")
    poll_p.add_argument(
        "--agent-spec",
        type=str,
        default=None,
        help="Path to an agent YAML manifest (optional).",
    )
    poll_p.add_argument("--task", type=str, default="", help="Task for the agent")
    poll_p.add_argument(
        "--working-dir", type=str, default=None, help="Directory for state persistence"
    )
    poll_p.add_argument(
        "--weave-project",
        type=str,
        default="",
        help="Optional Weave project for tracing",
    )
    poll_p.add_argument(
        "--metadata-out",
        type=str,
        default="",
        help="Optional path to write JSON run metadata",
    )
    poll_p.add_argument(
        "--max-steps", type=int, default=20, help="Max steps per run (default: 20)"
    )
    poll_p.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Seconds to sleep between runs (if provided)",
    )
    poll_p.add_argument(
        "--org", type=str, default="", help="Organization name (optional)"
    )
    poll_p.add_argument(
        "--project", type=str, required=True, help="Project name (required)"
    )
    poll_p.add_argument(
        "--var",
        action="append",
        default=[],
        help="Template var for YAML prompts, in KEY=VALUE format (repeatable)",
    )
    poll_p.add_argument(
        "--set",
        action="append",
        default=[],
        help="Override a field on the instantiated agent, in PATH=VALUE format (repeatable)",
    )
    poll_p.add_argument(
        "--env",
        action="append",
        default=[],
        help="Set an env var for the run, in KEY=VALUE format (repeatable)",
    )
    poll_p.set_defaults(func=_cmd_poll)

    run_p = sub.add_parser("run", help="Run a baseline (non-interactive) agent")
    run_p.add_argument(
        "--agent-spec",
        type=str,
        default=None,
        help="Path to an agent YAML manifest (optional).",
    )
    run_p.add_argument("--task", type=str, default="", help="Task for the agent")
    run_p.add_argument(
        "--working-dir", type=str, default=None, help="Directory for state persistence"
    )
    run_p.add_argument(
        "--weave-project",
        type=str,
        default="",
        help="Optional Weave project for tracing",
    )
    run_p.add_argument(
        "--metadata-out",
        type=str,
        default="",
        help="Optional path to write JSON run metadata",
    )
    run_p.add_argument(
        "--max-steps",
        type=int,
        default=20,
        help="Max steps before stopping (default: 20)",
    )
    run_p.add_argument(
        "--org", type=str, default="", help="Organization name (optional)"
    )
    run_p.add_argument(
        "--project", type=str, required=True, help="Project name (required)"
    )
    run_p.add_argument(
        "--var",
        action="append",
        default=[],
        help="Template var for YAML prompts, in KEY=VALUE format (repeatable)",
    )
    run_p.add_argument(
        "--set",
        action="append",
        default=[],
        help="Override a field on the instantiated agent, in PATH=VALUE format (repeatable)",
    )
    run_p.add_argument(
        "--env",
        action="append",
        default=[],
        help="Set an env var for the run, in KEY=VALUE format (repeatable)",
    )
    run_p.set_defaults(func=_cmd_run)

    bundle_p = sub.add_parser(
        "bundle", help="Run/validate WandBSwarm-compatible agent bundles"
    )
    bundle_sub = bundle_p.add_subparsers(dest="bundle_command", required=True)

    validate_p = bundle_sub.add_parser(
        "validate", help="Validate an agent bundle directory"
    )
    validate_p.add_argument(
        "--agent-dir", required=True, help="Path to agent bundle directory"
    )
    validate_p.set_defaults(func=_cmd_bundle_validate)

    bundle_run_p = bundle_sub.add_parser("run", help="Run an agent bundle locally")
    bundle_run_p.add_argument(
        "--agent-dir", required=True, help="Path to agent bundle directory"
    )
    bundle_run_p.add_argument(
        "--task-dir", required=True, help="Path to task directory (cwd for scripts)"
    )
    bundle_run_p.add_argument(
        "--workspace-dir", required=True, help="Workspace directory for agent outputs"
    )
    bundle_run_p.add_argument(
        "--skip-install", action="store_true", help="Skip install.sh even if present"
    )
    bundle_run_p.add_argument("--run-id", default="local", help="RUN_ID env var")
    bundle_run_p.add_argument("--task-id", default="local", help="TASK_ID env var")
    bundle_run_p.add_argument(
        "--experiment-id", default="local", help="EXPERIMENT_ID env var"
    )
    bundle_run_p.add_argument("--backend", default="local", help="BACKEND env var")
    bundle_run_p.add_argument(
        "--env",
        action="append",
        default=[],
        help="Extra env var (KEY=VALUE). Can repeat.",
    )
    bundle_run_p.set_defaults(func=_cmd_bundle_run)

    shell_p = bundle_sub.add_parser(
        "shell", help="Open a shell with bundle env vars set"
    )
    shell_p.add_argument(
        "--agent-dir", required=True, help="Path to agent bundle directory"
    )
    shell_p.add_argument(
        "--task-dir", required=True, help="Path to task directory (cwd for shell)"
    )
    shell_p.add_argument(
        "--workspace-dir", required=True, help="Workspace directory for agent outputs"
    )
    shell_p.add_argument("--run-id", default="local", help="RUN_ID env var")
    shell_p.add_argument("--task-id", default="local", help="TASK_ID env var")
    shell_p.add_argument(
        "--experiment-id", default="local", help="EXPERIMENT_ID env var"
    )
    shell_p.add_argument("--backend", default="local", help="BACKEND env var")
    shell_p.add_argument(
        "--env",
        action="append",
        default=[],
        help="Extra env var (KEY=VALUE). Can repeat.",
    )
    shell_p.set_defaults(func=_cmd_bundle_shell)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
