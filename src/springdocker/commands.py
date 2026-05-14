from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .analyze import format_json, format_table, summarize_csv
from .benchmarks.generate import generate_benchmark_assets
from .benchmarks.runner import run_benchmarks
from .config import render_default_config, write_default_config
from .dockerfile import DockerfileOptions, build_dockerfile
from .errors import EXIT_FAILURE, EXIT_OK, EXIT_USAGE, print_error, print_warning
from .project_detect import inspect_project


def run_checked(command: list[str], cwd: Path) -> int:
    print("$ " + " ".join(command))
    completed = subprocess.run(command, cwd=cwd)
    return completed.returncode


def cmd_doctor(project_root: Path, build_tool: str | None) -> int:
    try:
        info = inspect_project(project_root, build_tool)
    except ValueError as exc:
        print_error(str(exc))
        return EXIT_USAGE

    print(f"project_root: {info.root}")
    print(f"build_tool: {info.build_tool}")
    print(f"spring_markers: {'yes' if info.has_spring_markers else 'no'}")
    if not info.has_spring_markers:
        print_warning("Spring Boot markers were not found; continue only if this is intentional.")
    return EXIT_OK


def cmd_init(
    project_root: Path,
    build_tool: str | None,
    config_path: Path,
    profile: str,
    force: bool,
    print_only: bool,
) -> int:
    try:
        info = inspect_project(project_root, build_tool)
    except ValueError as exc:
        print_error(str(exc))
        return EXIT_USAGE

    if print_only:
        print(render_default_config(build_tool=info.build_tool, profile=profile))
        return EXIT_OK

    try:
        write_default_config(path=config_path, build_tool=info.build_tool, profile=profile, force=force)
    except FileExistsError as exc:
        print_error(str(exc))
        print("hint: rerun with --force to overwrite", file=sys.stderr)
        return EXIT_USAGE

    print(f"wrote config: {config_path}")
    print("next: springdocker benchmark run")
    return EXIT_OK


def _use_legacy_scripts(explicit: bool) -> bool:
    if explicit:
        return True
    return os.environ.get("SPRINGDOCKER_LEGACY_SCRIPTS", "").lower() in {"1", "true", "yes", "on"}


def cmd_dockerfile_generate(
    project_root: Path,
    build_tool: str | None,
    output: str,
    java_version: int,
    extra_args: list[str],
    use_legacy_scripts: bool,
) -> int:
    try:
        info = inspect_project(project_root, build_tool)
    except ValueError as exc:
        print_error(str(exc))
        return EXIT_USAGE

    if _use_legacy_scripts(use_legacy_scripts):
        script = project_root / "tools" / "dockerfile_wizard.py"
        if not script.exists():
            print_error(f"missing script: {script}")
            return EXIT_USAGE

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

    destination = Path(output)
    if not destination.is_absolute():
        destination = project_root / destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        build_dockerfile(DockerfileOptions(build_tool=info.build_tool, java_version=java_version)),
        encoding="utf-8",
    )
    print(f"wrote dockerfile: {destination}")
    return EXIT_OK


def cmd_benchmark_generate(
    project_root: Path,
    build_tool: str | None,
    java_version: int,
    use_legacy_scripts: bool,
) -> int:
    try:
        info = inspect_project(project_root, build_tool)
    except ValueError as exc:
        print_error(str(exc))
        return EXIT_USAGE

    if _use_legacy_scripts(use_legacy_scripts):
        script = project_root / "benchmarks" / "setup_benchmark_folders.py"
        if not script.exists():
            print_error(f"missing script: {script}")
            return EXIT_USAGE

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

    generate_benchmark_assets(project_root=project_root, build_tool=info.build_tool, java_version=java_version)
    print("generated benchmark scenarios")
    return EXIT_OK


def cmd_benchmark_run(
    project_root: Path,
    build_tool: str | None,
    profile: str,
    extra_args: list[str],
    use_legacy_scripts: bool,
) -> int:
    try:
        info = inspect_project(project_root, build_tool)
    except ValueError as exc:
        print_error(str(exc))
        return EXIT_USAGE

    if _use_legacy_scripts(use_legacy_scripts):
        script = project_root / "benchmarks" / "common" / "run_all_benchmarks.py"
        if not script.exists():
            print_error(f"missing script: {script}")
            return EXIT_USAGE

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

    return run_benchmarks(
        project_root=project_root,
        build_tool=info.build_tool,
        profile=profile,
        extra_args=extra_args,
    )


def cmd_benchmark_analyze(
    project_root: Path,
    raw_csv: str,
    output_format: str,
    scenario: str | None,
    variant: str | None,
    output_path: str | None,
    fail_on_success_rate_below: float | None,
) -> int:
    csv_path = Path(raw_csv)
    if not csv_path.is_absolute():
        csv_path = project_root / csv_path
    if not csv_path.exists():
        print_error(f"missing CSV file: {csv_path}")
        return EXIT_USAGE

    if fail_on_success_rate_below is not None and (
        fail_on_success_rate_below < 0.0 or fail_on_success_rate_below > 100.0
    ):
        print_error("--fail-on-success-rate-below must be between 0 and 100")
        return EXIT_USAGE

    try:
        summaries = summarize_csv(csv_path, scenario=scenario, variant=variant)
    except ValueError as exc:
        print_error(str(exc))
        return EXIT_USAGE

    if not summaries:
        print("No rows matched the provided filters.")
        return EXIT_OK

    rendered = format_json(summaries) if output_format == "json" else format_table(summaries)
    if output_path:
        destination = Path(output_path)
        if not destination.is_absolute():
            destination = project_root / destination
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered + "\n", encoding="utf-8")
        print(f"wrote analysis: {destination}")
    else:
        print(rendered)

    if fail_on_success_rate_below is not None:
        violations = [s for s in summaries if s.success_rate_pct < fail_on_success_rate_below]
        if violations:
            for summary in violations:
                print_error(
                    f"success_rate below threshold for {summary.scenario}/{summary.variant}: "
                    f"{summary.success_rate_pct:.1f}% < {fail_on_success_rate_below:.1f}%"
                )
            return EXIT_FAILURE

    return EXIT_OK
