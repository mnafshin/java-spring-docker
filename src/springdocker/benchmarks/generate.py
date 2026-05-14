from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from springdocker.dockerfile import DockerfileOptions, build_dockerfile

EXPECTED_CSV_HEADER = (
    "date,scenario,variant,run,build_ms,image_bytes,startup_ms,status,notes,host,docker_version,run_profile\n"
)


@dataclass(frozen=True)
class ScenarioDefinition:
    id: str
    variants: tuple[tuple[str, DockerfileOptions], ...]
    run_overrides: dict[str, int] | None = None
    scenario_type: str = "standard"


def default_scenarios(build_tool: str, java_version: int) -> list[ScenarioDefinition]:
    base = DockerfileOptions(build_tool=build_tool, java_version=java_version)
    return [
        ScenarioDefinition(
            id="01-base-image-pinning",
            variants=(
                ("digest-pinned", base),
                ("tag-only", DockerfileOptions(build_tool=build_tool, java_version=java_version, tuned_jvm_flags=False)),
            ),
        ),
        ScenarioDefinition(
            id="02-multi-stage-build-structure",
            variants=(
                ("specialized-multi-stage", base),
                ("simple-two-stage", DockerfileOptions(build_tool=build_tool, java_version=java_version, use_buildkit_cache=False)),
            ),
        ),
        ScenarioDefinition(
            id="03-buildkit-gradle-cache",
            variants=(
                ("with-buildkit-cache", base),
                ("without-buildkit-cache", DockerfileOptions(build_tool=build_tool, java_version=java_version, use_buildkit_cache=False)),
            ),
        ),
        ScenarioDefinition(
            id="04-custom-jre-jlink",
            variants=(
                ("with-jlink-runtime", base),
                ("without-jlink-runtime", DockerfileOptions(build_tool=build_tool, java_version=java_version, use_jlink=False)),
            ),
        ),
        ScenarioDefinition(
            id="05-jep483-aot-cache",
            variants=(
                ("with-aot-cache", base),
                ("without-aot-cache", DockerfileOptions(build_tool=build_tool, java_version=java_version, tuned_jvm_flags=False)),
            ),
            run_overrides={"quick": 8, "full": 15},
        ),
        ScenarioDefinition(
            id="06-runtime-hardening-non-root-tmp",
            variants=(
                ("hardened-non-root", base),
                ("root-runtime", DockerfileOptions(build_tool=build_tool, java_version=java_version, non_root=False, healthcheck=True)),
            ),
        ),
        ScenarioDefinition(
            id="07-healthcheck-readiness",
            variants=(
                ("with-readiness-healthcheck", base),
                ("without-healthcheck", DockerfileOptions(build_tool=build_tool, java_version=java_version, healthcheck=False)),
            ),
        ),
        ScenarioDefinition(
            id="08-jvm-container-flags",
            variants=(
                ("tuned-flags", base),
                ("defaults-like", DockerfileOptions(build_tool=build_tool, java_version=java_version, tuned_jvm_flags=False)),
            ),
        ),
        ScenarioDefinition(
            id="09-base-image-choice",
            variants=(
                ("temurin-jre", base),
                ("minimal-runtime", DockerfileOptions(build_tool=build_tool, java_version=java_version, use_buildkit_cache=False, tuned_jvm_flags=False)),
            ),
        ),
        ScenarioDefinition(
            id="10-native-vs-jvm",
            variants=(),
            scenario_type="native",
        ),
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

        if scenario.scenario_type == "standard":
            for name, opts in scenario.variants:
                variant_dir = variants_dir / name
                variant_dir.mkdir(parents=True, exist_ok=True)
                (variant_dir / "Dockerfile").write_text(build_dockerfile(opts), encoding="utf-8")

        csv = results_dir / "raw.csv"
        if not csv.exists():
            csv.write_text(EXPECTED_CSV_HEADER, encoding="utf-8")
