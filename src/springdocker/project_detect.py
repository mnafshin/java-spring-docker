from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectInfo:
    root: Path
    build_tool: str
    has_spring_markers: bool


def detect_build_tool(root: Path, explicit: str | None = None) -> str:
    """Detect Maven or Gradle build tool from project markers."""
    if explicit:
        if explicit not in {"maven", "gradle"}:
            raise ValueError("build tool must be 'maven' or 'gradle'")
        return explicit

    has_maven = (root / "pom.xml").exists()
    has_gradle = (root / "gradlew").exists() or any(
        (root / name).exists() for name in ("build.gradle", "build.gradle.kts")
    )

    if has_maven and has_gradle:
        raise ValueError(
            "Both Maven and Gradle markers found. Pass --build-tool explicitly."
        )
    if has_maven:
        return "maven"
    if has_gradle:
        return "gradle"
    raise ValueError("Could not detect build tool. Expected pom.xml or gradle markers.")


def has_spring_project_markers(root: Path) -> bool:
    """Best-effort Spring Boot marker detection for Java projects."""
    if (root / "src" / "main" / "resources" / "application.properties").exists():
        return True
    if (root / "src" / "main" / "resources" / "application.yml").exists():
        return True

    # Lightweight content checks in build descriptors.
    for descriptor in ("pom.xml", "build.gradle", "build.gradle.kts"):
        path = root / descriptor
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "spring-boot" in text or "org.springframework.boot" in text:
            return True
    return False


def inspect_project(root: Path, explicit_build_tool: str | None = None) -> ProjectInfo:
    build_tool = detect_build_tool(root, explicit_build_tool)
    return ProjectInfo(
        root=root,
        build_tool=build_tool,
        has_spring_markers=has_spring_project_markers(root),
    )

