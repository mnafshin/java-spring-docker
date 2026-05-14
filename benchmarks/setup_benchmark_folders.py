#!/usr/bin/env python3
"""Generate benchmark variant Dockerfiles for Java 25+ projects.

Each scenario variant is produced by calling build_dockerfile() from
tools/dockerfile_wizard.py with a tweaked WizardConfig, so there is
no fragile string manipulation and Maven / Gradle are both first-class.

Usage
-----
  python3 benchmarks/setup_benchmark_folders.py                    # Gradle (default)
  python3 benchmarks/setup_benchmark_folders.py --build-tool maven
  python3 benchmarks/setup_benchmark_folders.py --java-version 26

Java 25+ focus
--------------
Scenarios 04 (jlink/jdeps) and 05 (JEP 483 AOT cache) are the primary
Java-25+ differentiators.  The other scenarios are structural best-practices
that apply to any JVM image but are benchmarked here for completeness.
"""

from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmarks"
EXPECTED_CSV_HEADER = "date,scenario,variant,run,build_ms,image_bytes,startup_ms,status,notes,host,docker_version,run_profile\n"

# Make the wizard importable without installing it as a package.
sys.path.insert(0, str(ROOT / "tools"))
from dockerfile_wizard import WizardConfig, build_dockerfile  # noqa: E402


# ---------------------------------------------------------------------------
# Baseline config (all Java-25+ features ON, digest-pinned)
# ---------------------------------------------------------------------------

def base_config(build_tool: str, java_version: int) -> WizardConfig:
    """The 'gold standard' config that every scenario's primary variant uses."""
    return WizardConfig(
        runtime_base="debian-bookworm-slim",
        use_buildkit_cache=True,
        use_jlink=True,
        use_aot_cache=True,
        non_root=True,
        healthcheck=True,
        tuned_jvm_flags=True,
        pin_digests=True,
        use_native_image=False,
        output=Path("Dockerfile"),   # placeholder; overwritten per variant
        build_tool=build_tool,
        java_version=java_version,
    )


def two_stage_simple(build_tool: str, java_version: int) -> str:
    """Intentionally minimal two-stage Dockerfile for comparison (no jlink/AOT/layertools)."""
    if build_tool == "maven":
        setup = (
            "COPY mvnw pom.xml ./\n"
            "COPY .mvn ./.mvn\n"
            "RUN chmod +x mvnw\n"
            "COPY src ./src\n"
            "RUN ./mvnw -B -q package -DskipTests"
        )
        jar_src = "target/*.jar"
    else:
        setup = (
            "COPY gradlew build.gradle settings.gradle ./\n"
            "COPY gradle ./gradle\n"
            "RUN chmod +x gradlew\n"
            "COPY src ./src\n"
            "RUN ./gradlew --no-daemon bootJar -x test"
        )
        jar_src = "build/libs/*-SNAPSHOT.jar"

    return (
        f"# syntax=docker/dockerfile:1\n"
        f"# Simple two-stage build — intentionally minimal for benchmark comparison\n"
        f"# Java {java_version}  |  build-tool: {build_tool}\n"
        f"FROM eclipse-temurin:{java_version}-jdk AS build\n"
        f"WORKDIR /app\n"
        f"{setup}\n"
        f"\n"
        f"FROM eclipse-temurin:{java_version}-jre\n"
        f"WORKDIR /app\n"
        f"RUN apt-get update \\\n"
        f" && apt-get install -y --no-install-recommends curl \\\n"
        f" && rm -rf /var/lib/apt/lists/*\n"
        f"COPY --from=build /app/{jar_src} app.jar\n"
        f"EXPOSE 8080\n"
        f"EXPOSE 8081\n"
        f"HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \\\n"
        f"  CMD curl -fsS http://localhost:8081/actuator/health/readiness || exit 1\n"
        f'ENTRYPOINT ["java", "-jar", "app.jar"]\n'
    )


# ---------------------------------------------------------------------------
# Scenario definitions — each variant is a WizardConfig or a raw string
# ---------------------------------------------------------------------------

def make_scenarios(build_tool: str, java_version: int) -> dict:
    B = base_config(build_tool, java_version)
    r = dataclasses.replace  # shorthand
    aot_enabled = java_version >= 24

    cache_label = "maven-cache" if build_tool == "maven" else "gradle-cache"

    return {
        "01-base-image-pinning": {
            "desc": "Compare digest-pinned base images vs floating tags.",
            "variants": {
                "digest-pinned": build_dockerfile(B),
                "tag-only":      build_dockerfile(r(B, pin_digests=False)),
            },
        },
        "02-multi-stage-build-structure": {
            "desc": "Compare specialized multi-stage pipeline vs simpler two-stage pipeline.",
            "variants": {
                "specialized-multi-stage": build_dockerfile(B),
                "simple-two-stage":        two_stage_simple(build_tool, java_version),
            },
        },
        "03-buildkit-gradle-cache": {
            # Directory name kept for backward compatibility; description reflects build tool.
            "desc": f"Compare BuildKit {build_tool} cache mounts vs no cache mounts in Docker build.",
            "variants": {
                f"with-buildkit-{cache_label}":    build_dockerfile(B),
                f"without-buildkit-{cache_label}": build_dockerfile(r(B, use_buildkit_cache=False)),
            },
        },
        "04-custom-jre-jlink": {
            "desc": (
                "Compare custom jlink/jdeps runtime (Java 25+) vs stock JRE runtime. "
                "jdeps uses --multi-release to resolve modules accurately for this JVM version."
            ),
            "variants": {
                "with-jlink-runtime":    build_dockerfile(B),
                # Stock JRE: no jlink build stage, AOT also disabled (requires jlink JRE)
                "without-jlink-runtime": build_dockerfile(
                    r(B, use_jlink=False, use_aot_cache=False, runtime_base="eclipse-temurin-jre")
                ),
            },
        },
        "05-jep483-aot-cache": {
            "desc": (
                "Compare startup with and without JEP 483 AOT class-loading cache (Java 25+). "
                "Training run fires -Dspring.context.exit=onRefresh so every startup class is recorded."
            ),
            "variants": {
                "with-aot-cache":    build_dockerfile(r(B, use_aot_cache=aot_enabled)),
                "without-aot-cache": build_dockerfile(r(B, use_aot_cache=False)),
            },
        },
        "06-runtime-hardening-non-root-tmp": {
            "desc": "Compare hardened non-root runtime vs root runtime defaults.",
            "variants": {
                "hardened-non-root": build_dockerfile(B),
                "root-runtime":      build_dockerfile(r(B, non_root=False)),
            },
        },
        "07-healthcheck-readiness": {
            "desc": "Compare readiness-based healthcheck vs no Docker healthcheck.",
            "variants": {
                "with-readiness-healthcheck": build_dockerfile(B),
                "without-healthcheck":        build_dockerfile(r(B, healthcheck=False)),
            },
        },
        "08-jvm-container-flags": {
            "desc": "Compare tuned JVM container flags vs mostly-default JVM startup.",
            "variants": {
                "tuned-flags":   build_dockerfile(B),
                "defaults-like": build_dockerfile(r(B, tuned_jvm_flags=False)),
            },
        },
    }


# ---------------------------------------------------------------------------
# File writers
# ---------------------------------------------------------------------------

def write_common_tools() -> None:
    common = BENCH / "common"
    common.mkdir(parents=True, exist_ok=True)

    run_script = r'''#!/usr/bin/env bash
set -euo pipefail

SCENARIO_DIR="${1:-}"
RUNS="${2:-5}"
BASE_PORT="${BASE_PORT:-19081}"
CONTAINER_MGMT_PORT="${CONTAINER_MGMT_PORT:-8081}"
READINESS_PATH="${READINESS_PATH:-/actuator/health/readiness}"

if [[ -z "$SCENARIO_DIR" ]]; then
  echo "Usage: run_scenario.sh <scenario_dir> [runs]" >&2
  exit 1
fi

if [[ ! -d "$SCENARIO_DIR/variants" ]]; then
  echo "Missing variants directory: $SCENARIO_DIR/variants" >&2
  exit 1
fi

if [[ "$RUNS" -lt 1 ]]; then
  echo "RUNS must be >= 1 (got: $RUNS)" >&2
  exit 1
fi

RAW_CSV="$SCENARIO_DIR/results/raw.csv"
EXPECTED_HEADER="date,scenario,variant,run,build_ms,image_bytes,startup_ms,status,notes,host,docker_version,run_profile"
LEGACY_HEADER="date,scenario,variant,run,build_ms,image_bytes,startup_ms,status,notes"
HOST_NAME="$(hostname -s 2>/dev/null || hostname)"
DOCKER_VERSION="$(docker --version 2>/dev/null | sed 's/,//g' | awk '{print $3}' || echo unknown)"
RUN_PROFILE="${RUN_PROFILE:-manual}"
mkdir -p "$SCENARIO_DIR/results"
if [[ -f "$RAW_CSV" ]]; then
  current_header="$(head -n 1 "$RAW_CSV" | tr -d '\r')"
  if [[ "$current_header" == "$LEGACY_HEADER" ]]; then
    backup_csv="$SCENARIO_DIR/results/raw.legacy.$(date +%s).csv"
    mv "$RAW_CSV" "$backup_csv"
    echo "Archived legacy CSV header to: $backup_csv"
  fi
fi
if [[ ! -f "$RAW_CSV" ]]; then
  echo "$EXPECTED_HEADER" > "$RAW_CSV"
fi

scenario_name="$(basename "$SCENARIO_DIR")"

wait_ready_ms() {
  local port="$1"
  local attempts=160
  local sleep_sec=0.25
  local start_ms
  local end_ms

  start_ms=$(python3 - <<'PY'
import time
print(int(time.time() * 1000))
PY
)

  for ((i=1; i<=attempts; i++)); do
    if curl -fsS "http://localhost:${port}${READINESS_PATH}" >/dev/null 2>&1; then
      end_ms=$(python3 - <<'PY'
import time
print(int(time.time() * 1000))
PY
)
      echo $((end_ms - start_ms))
      return 0
    fi
    sleep "$sleep_sec"
  done

  echo -1
  return 1
}

idx=0
for variant_path in "$SCENARIO_DIR"/variants/*; do
  [[ -d "$variant_path" ]] || continue
  variant="$(basename "$variant_path")"
  dockerfile="$variant_path/Dockerfile"
  image_tag="bench-${scenario_name}:${variant}"
  port=$((BASE_PORT + idx))
  idx=$((idx + 1))

  echo "=== ${scenario_name} :: ${variant} ==="

  for run in $(seq 1 "$RUNS"); do
    build_start=$(python3 - <<'PY'
import time
print(int(time.time() * 1000))
PY
)

    if docker build -q -f "$dockerfile" -t "$image_tag" . >/dev/null; then
      build_end=$(python3 - <<'PY'
import time
print(int(time.time() * 1000))
PY
)
      build_ms=$((build_end - build_start))
      image_bytes=$(docker image inspect "$image_tag" --format '{{.Size}}')

      cname="bench-${scenario_name}-${variant}-${run}-$RANDOM"
      docker run -d --rm --name "$cname" -p "${port}:${CONTAINER_MGMT_PORT}" "$image_tag" >/dev/null

      status="ok"
      startup_ms="-1"
      notes=""
      if startup_ms=$(wait_ready_ms "$port"); then
        :
      else
        status="readiness_failed"
        notes="readiness endpoint not reachable"
      fi

      docker stop "$cname" >/dev/null || true

      printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
        "$(date +%F)" "$scenario_name" "$variant" "$run" "$build_ms" "$image_bytes" "$startup_ms" "$status" "$notes" "$HOST_NAME" "$DOCKER_VERSION" "$RUN_PROFILE" \
        >> "$RAW_CSV"

      echo "run ${run}: build=${build_ms}ms size=${image_bytes} startup=${startup_ms} status=${status}"
    else
      printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
        "$(date +%F)" "$scenario_name" "$variant" "$run" "-1" "-1" "-1" "build_failed" "docker build failed" "$HOST_NAME" "$DOCKER_VERSION" "$RUN_PROFILE" \
        >> "$RAW_CSV"

      echo "run ${run}: build failed"
    fi
  done
done
'''

    analyze_script = '''#!/usr/bin/env python3
import csv
import statistics
import sys
from collections import defaultdict

if len(sys.argv) != 2:
    print("Usage: analyze_results.py <raw.csv>")
    sys.exit(1)

path = sys.argv[1]
rows = []
with open(path, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

if not rows:
    print("No rows in input CSV")
    sys.exit(0)

groups = defaultdict(list)
for row in rows:
    groups[(row['scenario'], row['variant'])].append(row)

print("| Scenario | Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB avg | Success rate |")
print("|---|---|---:|---:|---:|---:|---:|---:|")

for (scenario, variant), items in sorted(groups.items()):
    build = [int(i['build_ms']) for i in items if int(i['build_ms']) >= 0]
    startup = [int(i['startup_ms']) for i in items if int(i['startup_ms']) >= 0]
    image = [int(i['image_bytes']) for i in items if int(i['image_bytes']) >= 0]
    ok = sum(1 for i in items if i['status'] == 'ok')
    total = len(items)

    build_avg = f"{statistics.mean(build):.1f}" if build else "-"
    startup_avg = f"{statistics.mean(startup):.1f}" if startup else "-"
    if len(startup) >= 2:
        p95 = statistics.quantiles(startup, n=20)[18]
        startup_p95 = f"{p95:.1f}"
    elif len(startup) == 1:
        startup_p95 = str(startup[0])
    else:
        startup_p95 = "-"
    image_mb = f"{(statistics.mean(image) / (1024 * 1024)):.2f}" if image else "-"
    success_rate = f"{(ok / total) * 100:.1f}%" if total else "0.0%"

    print(
        f"| {scenario} | {variant} | {total} | {build_avg} | {startup_avg} | {startup_p95} | {image_mb} | {success_rate} |"
    )
'''

    common_readme = '''# Benchmark common tooling

## Files

- `run_scenario.sh`: builds and runs all variants in one scenario and appends metrics to CSV.
- `analyze_results.py`: turns the raw CSV into a markdown summary table.

## Example

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/05-jep483-aot-cache 10
python3 benchmarks/common/analyze_results.py benchmarks/05-jep483-aot-cache/results/raw.csv
```
'''

    # Keep existing common tooling intact to avoid clobbering manual improvements.
    run_script_path = common / "run_scenario.sh"
    if not run_script_path.exists():
        run_script_path.write_text(run_script, encoding="utf-8")

    analyze_script_path = common / "analyze_results.py"
    if not analyze_script_path.exists():
        analyze_script_path.write_text(analyze_script, encoding="utf-8")

    common_readme_path = common / "README.md"
    if not common_readme_path.exists():
        common_readme_path.write_text(common_readme, encoding="utf-8")


def write_scenarios(build_tool: str, java_version: int) -> None:
    scenarios = make_scenarios(build_tool, java_version)

    for name, cfg in scenarios.items():
        scenario_dir = BENCH / name
        variants_dir = scenario_dir / "variants"
        results_dir = scenario_dir / "results"
        variants_dir.mkdir(parents=True, exist_ok=True)
        results_dir.mkdir(parents=True, exist_ok=True)

        # Scenario 03 changed variant naming when Maven support was added.
        # Prune only known stale names there to avoid mixed-tool runs while
        # preserving any manually added variants in other scenarios.
        if name == "03-buildkit-gradle-cache":
            stale_names = {
                "with-buildkit-cache",
                "without-buildkit-cache",
                "with-buildkit-gradle-cache",
                "without-buildkit-gradle-cache",
                "with-buildkit-maven-cache",
                "without-buildkit-maven-cache",
            } - set(cfg["variants"].keys())
            for stale in stale_names:
                stale_dir = variants_dir / stale
                if stale_dir.is_dir():
                    for f in stale_dir.rglob("*"):
                        if f.is_file():
                            f.unlink()
                    for d in sorted([p for p in stale_dir.rglob("*") if p.is_dir()], reverse=True):
                        d.rmdir()
                    stale_dir.rmdir()

        variants_list = "\n".join(f"- `{v}`" for v in cfg["variants"].keys())
        scenario_readme = (
            f"# {name}\n\n"
            f"{cfg['desc']}\n\n"
            f"## Variants\n\n"
            f"{variants_list}\n\n"
            f"## Run benchmark\n\n"
            f"```bash\n"
            f"cd /path/to/your-java25-project\n"
            f"bash benchmarks/common/run_scenario.sh benchmarks/{name} 10\n"
            f"python3 benchmarks/common/analyze_results.py benchmarks/{name}/results/raw.csv\n"
            f"```\n\n"
            f"## Notes\n\n"
            f"- Keep environment stable across runs (CPU, memory, Docker version).\n"
            f"- Run at least 10 samples per variant.\n"
            f"- Change only one variable per scenario.\n"
            f"- Build tool: **{build_tool}** | Java version: **{java_version}**\n"
        )

        (scenario_dir / "README.md").write_text(scenario_readme, encoding="utf-8")

        # Only reset the CSV if it does not exist yet (preserve existing results)
        csv_path = results_dir / "raw.csv"
        if not csv_path.exists():
            csv_path.write_text(EXPECTED_CSV_HEADER, encoding="utf-8")
        summary_path = results_dir / "summary.md"
        if not summary_path.exists():
            summary_path.write_text(
                "# Benchmark summary\n\nPaste the markdown table output from `analyze_results.py` here.\n",
                encoding="utf-8",
            )

        for variant_name, dockerfile_content in cfg["variants"].items():
            variant_dir = variants_dir / variant_name
            variant_dir.mkdir(parents=True, exist_ok=True)
            (variant_dir / "Dockerfile").write_text(dockerfile_content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate benchmark variant Dockerfiles for Java 25+ projects. "
            "Focuses on jlink/jdeps and JEP 483 AOT cache scenarios."
        )
    )
    parser.add_argument(
        "--build-tool",
        choices=["gradle", "maven"],
        default=None,
        help="Build tool used by the target project (auto-detected when only one marker exists)",
    )
    parser.add_argument(
        "--java-version",
        type=int,
        default=25,
        help="Java major version (default: 25; minimum 25 for full JEP 483 support)",
    )
    args = parser.parse_args()

    has_gradle = (ROOT / "gradlew").exists()
    has_maven = (ROOT / "pom.xml").exists()
    if args.build_tool:
        build_tool = args.build_tool
    elif has_gradle and has_maven:
        raise SystemExit(
            "Both gradlew and pom.xml were found. Pass --build-tool gradle|maven explicitly "
            "to avoid generating mixed-tool benchmark variants."
        )
    elif has_maven:
        build_tool = "maven"
    elif has_gradle:
        build_tool = "gradle"
    else:
        raise SystemExit("Could not detect build tool. Add gradlew or pom.xml, or pass --build-tool.")

    if args.java_version < 25:
        print(
            f"Warning: Java {args.java_version} < 25. "
            "JEP 483 AOT Cache requires Java 24+; scenario 05 will generate non-AOT variants."
        )

    print(f"Generating benchmark variants — build-tool={build_tool}, java={args.java_version}")
    write_common_tools()
    write_scenarios(build_tool, args.java_version)
    print("Done.")


if __name__ == "__main__":
    main()

