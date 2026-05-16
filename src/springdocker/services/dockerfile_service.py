from __future__ import annotations

import re
from pathlib import Path

from ..dockerfile import DockerfileOptions, build_dockerfile, explain_dockerfile_text


def resolve_path(project_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = project_root / path
    return path


def parse_must_have_modules(project_root: Path, must_have_modules_file: str | None) -> tuple[str, ...]:
    if not must_have_modules_file:
        return ()
    modules_path = resolve_path(project_root, must_have_modules_file)
    if not modules_path.exists():
        raise ValueError(f"missing must-have modules file: {modules_path}")
    parsed: list[str] = []
    seen: set[str] = set()
    for line in modules_path.read_text(encoding="utf-8").splitlines():
        entry = line.split("#", 1)[0].strip()
        if not entry:
            continue
        for token in [part.strip() for part in entry.split(",")]:
            if not token:
                continue
            if not re.fullmatch(r"[A-Za-z0-9._-]+", token):
                raise ValueError(f"invalid module name in {modules_path}: {token}")
            if token not in seen:
                parsed.append(token)
                seen.add(token)
    return tuple(parsed)


def generate_dockerfile(
    project_root: Path,
    output_path: str,
    build_tool: str,
    java_version: int,
    must_have_modules_file: str | None,
) -> Path:
    must_have_modules = parse_must_have_modules(project_root, must_have_modules_file)
    destination = resolve_path(project_root, output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        build_dockerfile(
            DockerfileOptions(
                build_tool=build_tool,
                java_version=java_version,
                must_have_modules=must_have_modules,
            )
        ),
        encoding="utf-8",
    )
    return destination


def explain_dockerfile(project_root: Path, dockerfile_path: str) -> dict[str, object]:
    path = resolve_path(project_root, dockerfile_path)
    if not path.exists():
        raise ValueError(f"missing Dockerfile: {path}")
    payload = dict(explain_dockerfile_text(path.read_text(encoding="utf-8")))
    payload["path"] = str(path)
    return payload

