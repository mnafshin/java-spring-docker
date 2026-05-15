from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import cast

from .analyze import format_json, format_table, summarize_csv
from .benchmarks.generate import generate_benchmark_assets
from .benchmarks.runner import run_benchmarks
from .compare import compare_summaries, format_delta_json, format_delta_table
from .config import render_default_config, write_default_config
from .dockerfile import DockerfileOptions, build_dockerfile, explain_dockerfile_text
from .errors import EXIT_FAILURE, EXIT_OK, EXIT_USAGE, print_error, print_warning
from .project_detect import inspect_project, inspect_project_details
from .regression import (
    RegressionViolation,
    detect_regressions,
    format_regression_json,
    format_regression_table,
    load_summaries,
)


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


def _render_inspect_table(info) -> str:
    lines = [
        "| Field | Value |",
        "|---|---|",
        f"| Project root | {info.root} |",
        f"| Build tool | {info.build_tool} |",
        f"| Spring markers | {'yes' if info.has_spring_markers else 'no'} |",
        f"| Java version | {info.java_version if info.java_version is not None else '-'} |",
        f"| Spring Boot version | {info.spring_boot_version or '-'} |",
        f"| Config exists | {'yes' if info.config_exists else 'no'} |",
        f"| Generated Dockerfiles | {', '.join(info.generated_dockerfiles) or '-'} |",
        f"| Direct dependencies | {', '.join(info.direct_dependencies) or '-'} |",
        f"| Reflection hits | {len(info.reflection_hits)} |",
        f"| Runtime compatibility | {info.runtime_compatibility} |",
        f"| Recommendations | {'; '.join(info.recommendations) or '-'} |",
    ]
    return "\n".join(lines)


def cmd_inspect(project_root: Path, build_tool: str | None, output_format: str) -> int:
    try:
        info = inspect_project_details(project_root, build_tool)
    except ValueError as exc:
        print_error(str(exc))
        return EXIT_USAGE

    payload = {
        "project_root": str(info.root),
        "build_tool": info.build_tool,
        "has_spring_markers": info.has_spring_markers,
        "java_version": info.java_version,
        "spring_boot_version": info.spring_boot_version,
        "direct_dependencies": list(info.direct_dependencies),
        "config_exists": info.config_exists,
        "generated_dockerfiles": list(info.generated_dockerfiles),
        "reflection_hits": list(info.reflection_hits),
        "runtime_compatibility": info.runtime_compatibility,
        "recommendations": list(info.recommendations),
    }
    if output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_render_inspect_table(info))
    return EXIT_OK


def _render_explain_table(payload: dict[str, object]) -> str:
    features = cast(list[dict[str, object]], payload.get("features", []))
    feature_names = ", ".join(
        str(feature["name"]) for feature in features if feature.get("enabled") and "name" in feature
    )
    notes = cast(list[str], payload.get("notes", []))
    return "\n".join(
        [
            "| Field | Value |",
            "|---|---|",
            f"| Source | {payload.get('source', '-')} |",
            f"| Build tool | {payload.get('build_tool') or '-'} |",
            f"| Java version | {payload.get('java_version') if payload.get('java_version') is not None else '-'} |",
            f"| Stage count | {payload.get('stage_count', '-')} |",
            f"| Features | {feature_names or '-'} |",
            f"| Summary | {payload.get('summary', '-')} |",
            f"| Notes | {'; '.join(notes) if notes else '-'} |",
        ]
    )


def cmd_benchmark_compare(
    project_root: Path,
    raw_csv: str,
    baseline_variant: str,
    output_format: str,
    scenario: str | None,
) -> int:
    csv_path = Path(raw_csv)
    if not csv_path.is_absolute():
        csv_path = project_root / csv_path
    if not csv_path.exists():
        print_error(f"missing CSV file: {csv_path}")
        return EXIT_USAGE

    try:
        summaries = summarize_csv(csv_path, scenario=scenario)
        deltas = compare_summaries(baseline_variant, summaries)
    except ValueError as exc:
        print_error(str(exc))
        return EXIT_USAGE

    rendered = format_delta_json(deltas) if output_format == "json" else format_delta_table(deltas)
    print(rendered)
    return EXIT_OK


def cmd_explain(project_root: Path, dockerfile_path: str, output_format: str) -> int:
    path = Path(dockerfile_path)
    if not path.is_absolute():
        path = project_root / path
    if not path.exists():
        print_error(f"missing Dockerfile: {path}")
        return EXIT_USAGE

    try:
        payload = explain_dockerfile_text(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        print_error(str(exc))
        return EXIT_USAGE

    payload = dict(payload)
    payload["path"] = str(path)
    if output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_render_explain_table(payload))
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
    must_have_modules_file: str | None,
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

    must_have_modules: tuple[str, ...] = ()
    if must_have_modules_file:
        modules_path = Path(must_have_modules_file)
        if not modules_path.is_absolute():
            modules_path = project_root / modules_path
        if not modules_path.exists():
            print_error(f"missing must-have modules file: {modules_path}")
            return EXIT_USAGE
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
                    print_error(f"invalid module name in {modules_path}: {token}")
                    return EXIT_USAGE
                if token not in seen:
                    parsed.append(token)
                    seen.add(token)
        must_have_modules = tuple(parsed)

    destination = Path(output)
    if not destination.is_absolute():
        destination = project_root / destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        build_dockerfile(
            DockerfileOptions(
                build_tool=info.build_tool,
                java_version=java_version,
                must_have_modules=must_have_modules,
            )
        ),
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
    cpuset_cpus: str | None,
    memory_limit: str | None,
    warmup_runs: int,
    normalized_runtime: bool,
    use_legacy_scripts: bool,
) -> int:
    try:
        info = inspect_project(project_root, build_tool)
    except ValueError as exc:
        print_error(str(exc))
        return EXIT_USAGE

    if use_legacy_scripts and any([cpuset_cpus, memory_limit, warmup_runs > 0, normalized_runtime]):
        print_error("benchmark reproducibility controls require the internal benchmark runner")
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
        cpuset_cpus=cpuset_cpus,
        memory_limit=memory_limit,
        warmup_runs=warmup_runs,
        normalized_runtime=normalized_runtime,
    )


def cmd_benchmark_analyze(
    project_root: Path,
    raw_csv: str,
    output_format: str,
    scenario: str | None,
    variant: str | None,
    output_path: str | None,
    fail_on_success_rate_below: float | None,
    baseline_path: str | None,
    fail_on_regression_above: float | None,
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

    if baseline_path is not None:
        baseline_file = Path(baseline_path)
        if not baseline_file.is_absolute():
            baseline_file = project_root / baseline_file
        if not baseline_file.exists():
            print_warning(f"baseline report not found; skipping regression check: {baseline_file}")
            return EXIT_OK
        try:
            baseline_summaries = load_summaries(baseline_file)
            regression_violations: list[RegressionViolation] = detect_regressions(
                baseline=baseline_summaries,
                current=summaries,
                threshold_pct=fail_on_regression_above or 20.0,
            )
        except ValueError as exc:
            print_error(str(exc))
            return EXIT_USAGE
        if regression_violations:
            rendered_violations = (
                format_regression_json(regression_violations)
                if output_format == "json"
                else format_regression_table(regression_violations)
            )
            print(rendered_violations)
            print_error(
                f"regressions above {fail_on_regression_above or 20.0:.1f}% detected against {baseline_file}"
            )
            return EXIT_FAILURE

    return EXIT_OK
