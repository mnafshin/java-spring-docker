from __future__ import annotations

import subprocess
from pathlib import Path

from .config import write_default_config
from .project_detect import inspect_project


def run_checked(command: list[str], cwd: Path) -> int:
    print("$ " + " ".join(command))
    completed = subprocess.run(command, cwd=cwd)
    return completed.returncode


def cmd_doctor(project_root: Path, build_tool: str | None) -> int:
    try:
        info = inspect_project(project_root, build_tool)
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    print(f"project_root: {info.root}")
    print(f"build_tool: {info.build_tool}")
    print(f"spring_markers: {'yes' if info.has_spring_markers else 'no'}")
    if not info.has_spring_markers:
        print("warning: Spring Boot markers were not found; continue only if this is intentional.")
    return 0


def cmd_init(project_root: Path, build_tool: str | None, config_path: Path, force: bool) -> int:
    try:
        info = inspect_project(project_root, build_tool)
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    try:
        write_default_config(path=config_path, build_tool=info.build_tool, force=force)
    except FileExistsError as exc:
        print(f"error: {exc}")
        print("hint: rerun with --force to overwrite")
        return 2

    print(f"wrote config: {config_path}")
    print("next: springdocker benchmark run")
    return 0


def cmd_dockerfile_generate(
    project_root: Path,
    build_tool: str | None,
    output: str,
    extra_args: list[str],
) -> int:
    try:
        info = inspect_project(project_root, build_tool)
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    script = project_root / "tools" / "dockerfile_wizard.py"
    if not script.exists():
        print(f"error: missing script: {script}")
        return 2

    cmd = [
        "python3",
        str(script),
        "--build-tool",
        info.build_tool,
        "--output",
        output,
    ]
    cmd.extend(extra_args)
    return run_checked(cmd, project_root)


def cmd_benchmark_generate(
    project_root: Path,
    build_tool: str | None,
    java_version: int,
) -> int:
    try:
        info = inspect_project(project_root, build_tool)
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    script = project_root / "benchmarks" / "setup_benchmark_folders.py"
    if not script.exists():
        print(f"error: missing script: {script}")
        return 2

    return run_checked(
        [
            "python3",
            str(script),
            "--build-tool",
            info.build_tool,
            "--java-version",
            str(java_version),
        ],
        project_root,
    )


def cmd_benchmark_run(
    project_root: Path,
    build_tool: str | None,
    profile: str,
    extra_args: list[str],
) -> int:
    try:
        info = inspect_project(project_root, build_tool)
    except ValueError as exc:
        print(f"error: {exc}")
        return 2

    script = project_root / "benchmarks" / "common" / "run_all_benchmarks.py"
    if not script.exists():
        print(f"error: missing script: {script}")
        return 2

    cmd = [
        "python3",
        str(script),
        "--profile",
        profile,
        "--build-tool",
        info.build_tool,
    ]
    cmd.extend(extra_args)
    return run_checked(cmd, project_root)


def cmd_benchmark_analyze(project_root: Path, raw_csv: str) -> int:
    script = project_root / "benchmarks" / "common" / "analyze_results.py"
    if not script.exists():
        print(f"error: missing script: {script}")
        return 2
    return run_checked(["python3", str(script), raw_csv], project_root)

