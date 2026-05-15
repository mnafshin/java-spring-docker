from __future__ import annotations

import argparse
import csv
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from springdocker.benchmarks.generate import EXPECTED_CSV_HEADER, default_scenarios


@dataclass(frozen=True)
class RunnerOptions:
    profile: str
    runs_override: int | None
    skip_native: bool
    native_duration: str | None
    native_vus: int | None
    native_cpu_work: int | None
    java_version: int
    regenerate_scenarios: bool


def parse_runner_args(profile: str, extra_args: list[str]) -> RunnerOptions:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--runs", type=int, default=None)
    parser.add_argument("--skip-native", action="store_true")
    parser.add_argument("--native-duration", default=None)
    parser.add_argument("--native-vus", type=int, default=None)
    parser.add_argument("--native-cpu-work", type=int, default=None)
    parser.add_argument("--java-version", type=int, default=25)
    parser.add_argument(
        "--regenerate-scenarios",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parsed, unknown = parser.parse_known_args(extra_args)
    if unknown:
        raise ValueError(f"unknown runner arguments: {' '.join(unknown)}")
    return RunnerOptions(
        profile=profile,
        runs_override=parsed.runs,
        skip_native=parsed.skip_native,
        native_duration=parsed.native_duration,
        native_vus=parsed.native_vus,
        native_cpu_work=parsed.native_cpu_work,
        java_version=parsed.java_version,
        regenerate_scenarios=parsed.regenerate_scenarios,
    )


def _docker_version() -> str:
    try:
        out = subprocess.run(
            ["docker", "--version"],
            check=False,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if out:
            return out.replace(",", "").split()[-1]
    except OSError:
        pass
    return "unknown"


def _wait_readiness(base_url: str, timeout_seconds: float = 40.0) -> int:
    start = time.time()
    while time.time() - start < timeout_seconds:
        probe = subprocess.run(
            ["curl", "-fsS", base_url],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if probe.returncode == 0:
            return int((time.time() - start) * 1000)
        time.sleep(0.25)
    return -1


def _append_row(path: Path, row: list[str]) -> None:
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(row)


def _ensure_csv(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(EXPECTED_CSV_HEADER, encoding="utf-8")


def _tag_for(scenario_id: str, variant_name: str) -> str:
    return f"bench-{scenario_id}:{variant_name}".replace("_", "-")


def _default_runs_for(profile: str, scenario_id: str) -> int:
    if scenario_id == "04-jep483-aot-cache":
        return 8 if profile == "quick" else 15
    return 3 if profile == "quick" else 10


def _run_standard_scenario(project_root: Path, scenario_dir: Path, runs: int, run_profile: str) -> None:
    raw_csv = scenario_dir / "results" / "raw.csv"
    _ensure_csv(raw_csv)
    host = socket.gethostname()
    docker_version = _docker_version()
    scenario = scenario_dir.name
    print(f"\n=== Scenario: {scenario} (runs={runs}, profile={run_profile}) ===")

    for index, variant_dir in enumerate(sorted((scenario_dir / "variants").glob("*"))):
        if not variant_dir.is_dir():
            continue
        dockerfile = variant_dir / "Dockerfile"
        if not dockerfile.exists():
            continue
        variant = variant_dir.name
        image_tag = _tag_for(scenario, variant)
        host_port = str(19081 + index)
        print(f"-- variant: {variant}")

        for run_number in range(1, runs + 1):
            build_start = time.time()
            build = subprocess.run(
                ["docker", "build", "-q", "-f", str(dockerfile), "-t", image_tag, "."],
                cwd=project_root,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            build_ms = int((time.time() - build_start) * 1000)
            if build.returncode != 0:
                _append_row(
                    raw_csv,
                    [
                        time.strftime("%Y-%m-%d"),
                        scenario,
                        variant,
                        str(run_number),
                        "-1",
                        "-1",
                        "-1",
                        "build_failed",
                        "docker build failed",
                        host,
                        docker_version,
                        run_profile,
                    ],
                )
                print(f"run {run_number}: build failed")
                continue

            image_size = subprocess.run(
                ["docker", "image", "inspect", image_tag, "--format", "{{.Size}}"],
                check=False,
                capture_output=True,
                text=True,
            ).stdout.strip() or "-1"

            container_name = f"{image_tag.replace(':', '-')}-{run_number}"
            subprocess.run(
                [
                    "docker",
                    "run",
                    "-d",
                    "--rm",
                    "--name",
                    container_name,
                    "-p",
                    f"{host_port}:8081",
                    image_tag,
                ],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            startup_ms = _wait_readiness("http://localhost:" + host_port + "/actuator/health/readiness")
            status = "ok" if startup_ms >= 0 else "readiness_failed"
            notes = "" if status == "ok" else "readiness endpoint not reachable"
            subprocess.run(["docker", "stop", container_name], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            _append_row(
                raw_csv,
                [
                    time.strftime("%Y-%m-%d"),
                    scenario,
                    variant,
                    str(run_number),
                    str(build_ms),
                    image_size,
                    str(startup_ms),
                    status,
                    notes,
                    host,
                    docker_version,
                    run_profile,
                ],
            )
            print(
                f"run {run_number}: build={build_ms}ms size={image_size} "
                f"startup={startup_ms} status={status}"
            )


def run_benchmarks(project_root: Path, build_tool: str, profile: str, extra_args: list[str]) -> int:
    options = parse_runner_args(profile=profile, extra_args=extra_args)
    print(f"Using profile: {options.profile}")
    print(f"Project root: {project_root}")
    print(f"Build tool: {build_tool}")
    scenarios = default_scenarios(build_tool=build_tool, java_version=options.java_version)
    print(f"Scenarios loaded: {len(scenarios)}")

    for scenario in scenarios:
        if scenario.scenario_type == "native":
            if options.skip_native:
                print(f"Skipping native scenario: {scenario.id}")
                continue
            print(f"Skipping native scenario in internal runner: {scenario.id}")
            continue
        scenario_dir = project_root / "benchmarks" / scenario.id
        if not (scenario_dir / "variants").exists():
            print(f"Skipping missing scenario directory: {scenario.id}")
            continue
        runs = options.runs_override or _default_runs_for(profile=options.profile, scenario_id=scenario.id)
        _run_standard_scenario(project_root=project_root, scenario_dir=scenario_dir, runs=runs, run_profile=options.profile)
    print("\nAll done. CSV results were updated.")
    return 0
