from __future__ import annotations

import importlib
import inspect
import types
from types import ModuleType
from typing import Any, Callable


class ToolImportError(ValueError):
    pass


def _parse_import_spec(spec: str) -> tuple[str, str | None]:
    if not spec or not isinstance(spec, str):
        raise ToolImportError(f"Invalid tool import spec: {spec!r}")
    if ":" in spec:
        module_path, attr = spec.split(":", 1)
        module_path = module_path.strip()
        attr = attr.strip() or None
        if not module_path:
            raise ToolImportError(
                f"Invalid tool import spec (missing module): {spec!r}"
            )
        return module_path, attr
    return spec.strip(), None


def _resolve_import_spec(spec: str) -> Any:
    module_path, attr = _parse_import_spec(spec)
    try:
        module = importlib.import_module(module_path)
    except Exception as e:  # noqa: BLE001
        raise ToolImportError(
            f"Failed to import module {module_path!r} from {spec!r}: {e}"
        ) from e
    if not attr:
        return module
    try:
        return getattr(module, attr)
    except AttributeError as e:
        raise ToolImportError(
            f"Module {module_path!r} has no attribute {attr!r} (from {spec!r})"
        ) from e


def _is_tool_callable(obj: Any) -> bool:
    return callable(obj) and bool(getattr(obj, "_is_tool", False))


def _collect_tool_callables_from_module(
    module: ModuleType,
) -> dict[str, Callable[..., Any]]:
    tools: dict[str, Callable[..., Any]] = {}
    for name, value in vars(module).items():
        if name.startswith("_"):
            continue
        if _is_tool_callable(value):
            tools[name] = value
    return tools


def _collect_tool_callables(container: Any) -> dict[str, Callable[..., Any]]:
    if isinstance(container, ModuleType):
        return _collect_tool_callables_from_module(container)

    if isinstance(container, dict):
        tools: dict[str, Callable[..., Any]] = {}
        for name, value in container.items():
            if isinstance(name, str) and _is_tool_callable(value):
                tools[name] = value
        return tools

    if isinstance(container, (list, tuple, set)):
        tools_list: dict[str, Callable[..., Any]] = {}
        for item in container:
            if _is_tool_callable(item):
                tools_list[getattr(item, "__name__", "tool")] = item
        return tools_list

    if _is_tool_callable(container):
        return {getattr(container, "__name__", "tool"): container}

    raise ToolImportError(
        "Tool import spec must resolve to a module, a dict/list of tools, or a @tool/@weaveTool callable. "
        f"Got: {type(container).__name__}"
    )


def load_tool_callables(specs: list[str] | None) -> dict[str, Callable[..., Any]]:
    merged: dict[str, Callable[..., Any]] = {}
    for spec in specs or []:
        container = _resolve_import_spec(spec)
        tools = _collect_tool_callables(container)
        overlaps = set(merged).intersection(tools)
        if overlaps:
            raise ToolImportError(
                f"Duplicate tool name(s) across tool specs: {sorted(overlaps)}"
            )
        merged.update(tools)
    return merged


def bind_tools(
    instance: Any, tool_callables: dict[str, Callable[..., Any]]
) -> dict[str, Callable[..., Any]]:
    bound: dict[str, Callable[..., Any]] = {}
    for name, fn in tool_callables.items():
        if inspect.ismethod(fn):
            bound[name] = fn
            continue

        if inspect.isfunction(fn):
            try:
                params = list(inspect.signature(fn).parameters.values())
            except (TypeError, ValueError):
                params = []
            if params and params[0].name == "self":
                bound[name] = types.MethodType(fn, instance)
            else:
                bound[name] = fn
            continue

        bound[name] = fn

    return bound


def load_bound_tools(
    instance: Any, specs: list[str] | None
) -> dict[str, Callable[..., Any]]:
    return bind_tools(instance, load_tool_callables(specs))
