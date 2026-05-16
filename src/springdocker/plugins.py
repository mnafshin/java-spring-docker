from __future__ import annotations

import os
from dataclasses import dataclass
from importlib.metadata import EntryPoint, entry_points
from typing import Any, Protocol, cast

from .dockerfile import DockerfileOptions

DOCKERFILE_MUTATOR_GROUP = "springdocker.dockerfile_mutators"


class DockerfileMutator(Protocol):
    name: str

    def mutate_dockerfile(self, dockerfile_text: str, options: DockerfileOptions) -> str: ...


@dataclass(frozen=True)
class PluginExecution:
    dockerfile_text: str
    warnings: tuple[str, ...]


def _iter_entry_points(group: str) -> list[EntryPoint]:
    discovered = entry_points()
    if hasattr(discovered, "select"):
        return list(discovered.select(group=group))
    legacy = cast(dict[str, list[EntryPoint]], discovered)
    return list(legacy.get(group, []))


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
    if os.environ.get("SPRINGDOCKER_DISABLE_PLUGINS", "").lower() in {"1", "true", "yes", "on"}:
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
