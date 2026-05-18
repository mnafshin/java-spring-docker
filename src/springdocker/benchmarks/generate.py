from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from springdocker.dockerfile import DockerfileOptions, build_dockerfile

EXPECTED_CSV_HEADER = (
    "date,scenario,variant,run,build_ms,image_bytes,startup_ms,status,notes,host,docker_version,run_profile,"
    "gc_pause_ms,alloc_mb,startup_phase_boot_ms,startup_phase_context_ms,startup_phase_web_server_ms\n"
)


@dataclass(frozen=True)
class ScenarioDefinition:
    id: str


@dataclass(frozen=True)
class StandardScenarioDefinition(ScenarioDefinition):
    variants: tuple[tuple[str, DockerfileOptions], ...]
    run_overrides: dict[str, int] | None = None

    def __post_init__(self) -> None:
        if not self.variants:
            raise ValueError("standard scenario must define at least one variant")


@dataclass(frozen=True)
class NativeScenarioDefinition(ScenarioDefinition):
    pass


def default_scenarios(build_tool: str, java_version: int) -> list[ScenarioDefinition]:
    base = DockerfileOptions(build_tool=build_tool, java_version=java_version)
    return [
        StandardScenarioDefinition(
            id="01-multi-stage-build-structure",
            variants=(
                ("specialized-multi-stage", base),
                ("simple-two-stage", DockerfileOptions(build_tool=build_tool, java_version=java_version, use_buildkit_cache=False)),
            ),
        ),
        StandardScenarioDefinition(
            id="02-buildkit-gradle-cache",
            variants=(
                ("with-buildkit-cache", base),
                ("without-buildkit-cache", DockerfileOptions(build_tool=build_tool, java_version=java_version, use_buildkit_cache=False)),
            ),
        ),
        StandardScenarioDefinition(
            id="03-custom-jre-jlink",
            variants=(
                ("with-jlink-runtime", base),
                ("without-jlink-runtime", DockerfileOptions(build_tool=build_tool, java_version=java_version, use_jlink=False)),
            ),
        ),
        StandardScenarioDefinition(
            id="04-jep483-aot-cache",
            variants=(
                ("with-aot-cache", base),
                ("without-aot-cache", DockerfileOptions(build_tool=build_tool, java_version=java_version, tuned_jvm_flags=False)),
            ),
            run_overrides={"quick": 8, "full": 15},
        ),
        StandardScenarioDefinition(
            id="05-jvm-container-flags",
            variants=(
                ("tuned-flags", base),
                ("defaults-like", DockerfileOptions(build_tool=build_tool, java_version=java_version, tuned_jvm_flags=False)),
            ),
        ),
        StandardScenarioDefinition(
            id="06-base-image-choice",
            variants=(
                ("temurin-jre", DockerfileOptions(build_tool=build_tool, java_version=java_version, use_jlink=False)),
                (
                    "distroless-nonroot",
                    DockerfileOptions(
                        build_tool=build_tool,
                        java_version=java_version,
                        use_jlink=False,
                        runtime_image="distroless",
                    ),
                ),
            ),
        ),
        NativeScenarioDefinition(id="07-native-vs-jvm"),
    ]


def generate_benchmark_assets(project_root: Path, build_tool: str, java_version: int) -> None:
    bench_root = project_root / "benchmarks"
    bench_root.mkdir(parents=True, exist_ok=True)

    for scenario in default_scenarios(build_tool=build_tool, java_version=java_version):
        scenario_dir = bench_root / scenario.id
        variants_dir = scenario_dir / "variants"
        results_dir = scenario_dir / "results"
        scenario_dir.mkdir(parents=True, exist_ok=True)
        variants_dir.mkdir(parents=True, exist_ok=True)
        results_dir.mkdir(parents=True, exist_ok=True)

        if isinstance(scenario, StandardScenarioDefinition):
            for name, opts in scenario.variants:
                variant_dir = variants_dir / name
                variant_dir.mkdir(parents=True, exist_ok=True)
                (variant_dir / "Dockerfile").write_text(build_dockerfile(opts), encoding="utf-8")
        elif isinstance(scenario, NativeScenarioDefinition):
            pass
        else:  # pragma: no cover - defensive guard for future extensions
            raise TypeError(f"unsupported scenario definition: {type(scenario)}")

        csv = results_dir / "raw.csv"
        if not csv.exists():
            csv.write_text(EXPECTED_CSV_HEADER, encoding="utf-8")
