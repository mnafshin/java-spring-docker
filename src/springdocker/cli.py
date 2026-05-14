from __future__ import annotations

import argparse
from pathlib import Path

from .commands import (
    cmd_benchmark_analyze,
    cmd_benchmark_generate,
    cmd_benchmark_run,
    cmd_dockerfile_generate,
    cmd_doctor,
    cmd_init,
)
from .config import load_config, resolve_benchmark_run_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="springdocker",
        description="CLI for Dockerfile and benchmark workflows in Spring Boot Maven/Gradle projects.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common_options(p: argparse.ArgumentParser, with_build_tool: bool = True) -> None:
        p.add_argument("--project-root", default=".", help="Project root path (default: current directory)")
        if with_build_tool:
            p.add_argument("--build-tool", choices=["maven", "gradle"], default=None,
                           help="Override auto-detected build tool")

    init = sub.add_parser("init", help="Generate starter .springdocker.toml for this project")
    add_common_options(init)
    init.add_argument("--config", default=".springdocker.toml", help="Config file path to create")
    init.add_argument("--force", action="store_true", help="Overwrite existing config file")

    doctor = sub.add_parser("doctor", help="Detect project and validate basic prerequisites")
    add_common_options(doctor)

    dockerfile = sub.add_parser("dockerfile", help="Dockerfile operations")
    dockerfile_sub = dockerfile.add_subparsers(dest="dockerfile_command", required=True)
    gen = dockerfile_sub.add_parser("generate", help="Generate Dockerfile via existing wizard")
    add_common_options(gen)
    gen.add_argument("--output", default="Dockerfile.generated", help="Output Dockerfile path")
    gen.add_argument(
        "--wizard-arg",
        action="append",
        default=[],
        help="Extra argument forwarded to tools/dockerfile_wizard.py; repeat for multiple args",
    )

    bench = sub.add_parser("benchmark", help="Benchmark operations")
    bench_sub = bench.add_subparsers(dest="benchmark_command", required=True)

    bench_gen = bench_sub.add_parser("generate", help="Generate benchmark variants for selected build tool")
    add_common_options(bench_gen)
    bench_gen.add_argument("--java-version", type=int, default=25)

    bench_run = bench_sub.add_parser("run", help="Run benchmark orchestration")
    add_common_options(bench_run)
    bench_run.add_argument("--profile", choices=["quick", "full"], default=None)
    bench_run.add_argument(
        "--config",
        default=".springdocker.toml",
        help="Path to TOML config file relative to project root (default: .springdocker.toml)",
    )
    bench_run.add_argument(
        "--runner-arg",
        action="append",
        default=None,
        help="Extra argument forwarded to benchmarks/common/run_all_benchmarks.py; repeat for multiple args",
    )

    bench_analyze = bench_sub.add_parser("analyze", help="Analyze benchmark CSV")
    add_common_options(bench_analyze, with_build_tool=False)
    bench_analyze.add_argument("raw_csv", help="Path to results raw.csv")
    bench_analyze.add_argument("--format", choices=["table", "json"], default="table")
    bench_analyze.add_argument("--scenario", default=None, help="Filter by scenario id")
    bench_analyze.add_argument("--variant", default=None, help="Filter by variant name")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    project_root = Path(args.project_root).resolve()

    if args.command == "init":
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = project_root / config_path
        return cmd_init(project_root, args.build_tool, config_path, args.force)

    if args.command == "doctor":
        return cmd_doctor(project_root, args.build_tool)

    if args.command == "dockerfile" and args.dockerfile_command == "generate":
        return cmd_dockerfile_generate(
            project_root=project_root,
            build_tool=args.build_tool,
            output=args.output,
            extra_args=args.wizard_arg,
        )

    if args.command == "benchmark" and args.benchmark_command == "generate":
        return cmd_benchmark_generate(
            project_root=project_root,
            build_tool=args.build_tool,
            java_version=args.java_version,
        )

    if args.command == "benchmark" and args.benchmark_command == "run":
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = project_root / config_path
        loaded = load_config(config_path)
        resolved = resolve_benchmark_run_config(
            cli_build_tool=args.build_tool,
            cli_profile=args.profile,
            cli_runner_args=args.runner_arg,
            loaded_config=loaded,
        )
        return cmd_benchmark_run(
            project_root=project_root,
            build_tool=resolved.build_tool,
            profile=resolved.profile,
            extra_args=resolved.runner_args,
        )

    if args.command == "benchmark" and args.benchmark_command == "analyze":
        return cmd_benchmark_analyze(
            project_root=project_root,
            raw_csv=args.raw_csv,
            output_format=args.format,
            scenario=args.scenario,
            variant=args.variant,
        )

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())


