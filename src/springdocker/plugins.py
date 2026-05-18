from __future__ import annotations

import os
from dataclasses import dataclass
from importlib.metadata import EntryPoint, entry_points
from pathlib import Path
from typing import Any, Protocol, cast

from .dockerfile import DockerfileOptions

DOCKERFILE_MUTATOR_GROUP = "springdocker.dockerfile_mutators"
PROJECT_DETECTOR_GROUP = "springdocker.project_detectors"
RECIPE_GROUP = "springdocker.recipes"
VERIFIER_GROUP = "springdocker.verifiers"
VERIFY_RENDERER_GROUP = "springdocker.verify_renderers"
COMMAND_GROUP = "springdocker.commands"


class DockerfileMutator(Protocol):
    name: str

    def mutate_dockerfile(self, dockerfile_text: str, options: DockerfileOptions) -> str: ...


@dataclass(frozen=True)
class PluginExecution:
    dockerfile_text: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class PluginRenderExecution:
    rendered: str | None
    handled: bool
    warnings: tuple[str, ...]


def _iter_entry_points(group: str) -> list[EntryPoint]:
    discovered = entry_points()
    if hasattr(discovered, "select"):
        selected = list(discovered.select(group=group))
    else:
        legacy = cast(dict[str, list[EntryPoint]], discovered)
        selected = list(legacy.get(group, []))
    return sorted(selected, key=lambda entry: entry.name)


def _plugins_disabled() -> bool:
    return os.environ.get("SPRINGDOCKER_DISABLE_PLUGINS", "").lower() in {"1", "true", "yes", "on"}


def _to_callable(candidate: Any, method_name: str) -> Any:
    instance = candidate() if isinstance(candidate, type) else candidate
    if hasattr(instance, method_name) and callable(getattr(instance, method_name)):
        return getattr(instance, method_name)
    if callable(instance):
        return instance
    raise TypeError(f"plugin must define {method_name}(...) or be callable")


def detect_build_tool_from_plugins(root: Path) -> str | None:
    if _plugins_disabled():
        return None
    selected: list[str] = []
    for plugin_entry in _iter_entry_points(PROJECT_DETECTOR_GROUP):
        try:
            detector = _to_callable(plugin_entry.load(), "detect_build_tool")
            resolved = detector(root)
        except Exception:
            continue
        if resolved is None:
            continue
        if resolved not in {"maven", "gradle"}:
            continue
        selected.append(resolved)
    if not selected:
        return None
    if len(set(selected)) > 1:
        raise ValueError("conflicting build-tool detector plugins resolved both Maven and Gradle")
    return selected[0]


def render_recipe_from_plugins(recipe: str, options: DockerfileOptions) -> PluginRenderExecution:
    if _plugins_disabled():
        return PluginRenderExecution(rendered=None, handled=False, warnings=())
    matching = [entry for entry in _iter_entry_points(RECIPE_GROUP) if entry.name == recipe]
    if not matching:
        return PluginRenderExecution(rendered=None, handled=False, warnings=())

    warnings: list[str] = []
    for entry in matching:
        try:
            renderer = _to_callable(entry.load(), "render_recipe")
            rendered = renderer(options)
            if not isinstance(rendered, str):
                raise TypeError("recipe plugin must return str")
            return PluginRenderExecution(rendered=rendered, handled=True, warnings=tuple(warnings))
        except Exception as exc:
            warnings.append(f"plugin recipe '{entry.name}' failed: {exc}")
    return PluginRenderExecution(rendered=None, handled=True, warnings=tuple(warnings))


def render_verify_with_plugins(output_format: str, outcome: Any) -> PluginRenderExecution:
    if _plugins_disabled():
        return PluginRenderExecution(rendered=None, handled=False, warnings=())
    matching = [entry for entry in _iter_entry_points(VERIFY_RENDERER_GROUP) if entry.name == output_format]
    if not matching:
        return PluginRenderExecution(rendered=None, handled=False, warnings=())

    warnings: list[str] = []
    for entry in matching:
        try:
            renderer = _to_callable(entry.load(), "render")
            rendered = renderer(outcome)
            if not isinstance(rendered, str):
                raise TypeError("verify renderer plugin must return str")
            return PluginRenderExecution(rendered=rendered, handled=True, warnings=tuple(warnings))
        except Exception as exc:
            warnings.append(f"verify renderer '{entry.name}' failed: {exc}")
    return PluginRenderExecution(rendered=None, handled=True, warnings=tuple(warnings))


def register_command_plugins(subparsers: Any) -> tuple[str, ...]:
    if _plugins_disabled():
        return ()
    warnings: list[str] = []
    for entry in _iter_entry_points(COMMAND_GROUP):
        try:
            register = _to_callable(entry.load(), "register")
            register(subparsers)
        except Exception as exc:
            warnings.append(f"command plugin '{entry.name}' failed: {exc}")
    return tuple(warnings)


def iter_verifier_entry_points() -> list[EntryPoint]:
    if _plugins_disabled():
        return []
    return _iter_entry_points(VERIFIER_GROUP)


def _to_mutator(candidate: Any, entry_point_name: str) -> DockerfileMutator:
    instance = candidate() if isinstance(candidate, type) else candidate
    if hasattr(instance, "mutate_dockerfile") and callable(instance.mutate_dockerfile):
        if hasattr(instance, "name"):
            return cast(DockerfileMutator, instance)

        class _NamedMutator:
            name = entry_point_name

            def mutate_dockerfile(self, dockerfile_text: str, options: DockerfileOptions) -> str:
                return cast(str, instance.mutate_dockerfile(dockerfile_text, options))

        return cast(DockerfileMutator, _NamedMutator())
    if callable(instance):
        fn = instance

        class _FunctionMutator:
            name = entry_point_name

            def mutate_dockerfile(self, dockerfile_text: str, options: DockerfileOptions) -> str:
                return cast(str, fn(dockerfile_text, options))

        return cast(DockerfileMutator, _FunctionMutator())
    raise TypeError("plugin must define mutate_dockerfile(...) or be a callable")


def apply_dockerfile_mutators(dockerfile_text: str, options: DockerfileOptions) -> PluginExecution:
    if _plugins_disabled():
        return PluginExecution(dockerfile_text=dockerfile_text, warnings=())

    warnings: list[str] = []
    rendered = dockerfile_text
    for plugin_entry in _iter_entry_points(DOCKERFILE_MUTATOR_GROUP):
        try:
            loaded = plugin_entry.load()
            mutator = _to_mutator(loaded, plugin_entry.name)
            mutated = mutator.mutate_dockerfile(rendered, options)
            if not isinstance(mutated, str):
                raise TypeError("plugin must return str from mutate_dockerfile")
            rendered = mutated
        except Exception as exc:  # pragma: no cover - covered through behavior tests
            warnings.append(f"plugin '{plugin_entry.name}' failed: {exc}")
    return PluginExecution(dockerfile_text=rendered, warnings=tuple(warnings))
