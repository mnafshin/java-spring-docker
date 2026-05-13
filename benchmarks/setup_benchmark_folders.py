#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path('/Users/afshin/IdeaProjects/sandbox/java-spring-docker')
BENCH = ROOT / 'benchmarks'
BASE = (ROOT / 'Dockerfile').read_text()


def strip_digests(text: str) -> str:
    return re.sub(r'@sha256:[0-9a-f]+', '', text)


def remove_buildkit_mounts(text: str) -> str:
    t = text
    t = t.replace(
        'RUN --mount=type=cache,sharing=locked,target=/root/.gradle \\\n    ./gradlew --no-daemon dependencies -q',
        'RUN ./gradlew --no-daemon dependencies -q',
    )
    t = t.replace(
        'RUN --mount=type=cache,sharing=locked,target=/root/.gradle \\\n    ./gradlew --no-daemon bootJar -x test --no-build-cache',
        'RUN ./gradlew --no-daemon bootJar -x test --no-build-cache',
    )
    return t


def remove_aot_runtime_use(text: str) -> str:
    t = text
    t = t.replace('COPY --from=aot-trainer --chown=1001:1001 /app/app.aot ./app.aot\n\n', '')
    t = t.replace('            "-XX:AOTCache=app.aot", \\\n', '')
    return t


def root_runtime_variant(text: str) -> str:
    t = text
    t = t.replace(
        'RUN groupadd --system --gid 1001 javauser \\\n && useradd  --system --uid 1001 --gid 1001 \\\n             --no-create-home --shell /usr/sbin/nologin \\\n             --comment "java runtime user" javauser\n\n',
        '# Root-runtime variant for benchmark comparison\nRUN true\n\n',
    )
    t = t.replace(
        'RUN install -d -o javauser -g javauser -m 755  /app \\\n && install -d -o javauser -g javauser -m 1777 /tmp',
        'RUN install -d -m 755 /app \\\n && install -d -m 1777 /tmp',
    )
    t = t.replace('USER 1001\n\n', '')
    return t


def remove_healthcheck(text: str) -> str:
    return re.sub(
        r'# Docker-native health check; Kubernetes overrides this with its own probe spec\.\n'
        r'HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \\\n'
        r'  CMD curl -fsS http://localhost:8081/actuator/health/readiness \|\| exit 1\n\n',
        '',
        text,
    )


def default_jvm_flags(text: str) -> str:
    t = text
    t = t.replace('            "-XX:AOTCache=app.aot", \\\n', '')
    t = re.sub(
        r'ENTRYPOINT \["java", \\\n(?:.*\n)*?\s+"org\.springframework\.boot\.loader\.launch\.JarLauncher"\]\n',
        'ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]\n',
        t,
    )
    return t


def no_jlink_runtime(text: str) -> str:
    t = text
    t = t.replace(
        'FROM debian:bookworm-slim@sha256:d5d3f9c23164ea16f31852f95bd5959aad1c5e854332fe00f7b3a20fcc9f635c\n\n# OCI standard image labels',
        'FROM eclipse-temurin:25-jre\n\n# OCI standard image labels',
    )
    t = t.replace('COPY --from=jre-builder /jre/custom-jre $JAVA_HOME\n\n', '')
    return t


TWO_STAGE_SIMPLE = '''# syntax=docker/dockerfile:1
FROM eclipse-temurin:25-jdk AS build
WORKDIR /app
COPY gradlew build.gradle settings.gradle ./
COPY gradle ./gradle
RUN chmod +x gradlew
COPY src ./src
RUN ./gradlew --no-daemon bootJar -x test

FROM eclipse-temurin:25-jre
WORKDIR /app
RUN apt-get update \\
 && apt-get install -y --no-install-recommends curl \\
 && rm -rf /var/lib/apt/lists/*
COPY --from=build /app/build/libs/*-SNAPSHOT.jar app.jar
EXPOSE 8080
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \\
  CMD curl -fsS http://localhost:8081/actuator/health/readiness || exit 1
ENTRYPOINT ["java", "-jar", "app.jar"]
'''


SCENARIOS = {
    '01-base-image-pinning': {
        'desc': 'Compare digest-pinned base images vs floating tags.',
        'variants': {
            'digest-pinned': BASE,
            'tag-only': strip_digests(BASE),
        },
    },
    '02-multi-stage-build-structure': {
        'desc': 'Compare specialized multi-stage pipeline vs simpler two-stage pipeline.',
        'variants': {
            'specialized-multi-stage': BASE,
            'simple-two-stage': TWO_STAGE_SIMPLE,
        },
    },
    '03-buildkit-gradle-cache': {
        'desc': 'Compare BuildKit cache mounts vs no cache mounts in Docker build.',
        'variants': {
            'with-buildkit-cache': BASE,
            'without-buildkit-cache': remove_buildkit_mounts(BASE),
        },
    },
    '04-custom-jre-jlink': {
        'desc': 'Compare custom jlink runtime vs stock JRE runtime.',
        'variants': {
            'with-jlink-runtime': BASE,
            'without-jlink-runtime': no_jlink_runtime(BASE),
        },
    },
    '05-jep483-aot-cache': {
        'desc': 'Compare startup with and without JEP 483 runtime cache usage.',
        'variants': {
            'with-aot-cache': BASE,
            'without-aot-cache': remove_aot_runtime_use(BASE),
        },
    },
    '06-runtime-hardening-non-root-tmp': {
        'desc': 'Compare hardened non-root runtime vs root runtime defaults.',
        'variants': {
            'hardened-non-root': BASE,
            'root-runtime': root_runtime_variant(BASE),
        },
    },
    '07-healthcheck-readiness': {
        'desc': 'Compare readiness-based healthcheck vs no Docker healthcheck.',
        'variants': {
            'with-readiness-healthcheck': BASE,
            'without-healthcheck': remove_healthcheck(BASE),
        },
    },
    '08-jvm-container-flags': {
        'desc': 'Compare tuned JVM flags vs mostly-default JVM startup.',
        'variants': {
            'tuned-flags': BASE,
            'defaults-like': default_jvm_flags(BASE),
        },
    },
}


def write_common_tools() -> None:
    common = BENCH / 'common'
    common.mkdir(parents=True, exist_ok=True)

    run_script = '''#!/usr/bin/env bash
set -euo pipefail

SCENARIO_DIR="${1:-}"
RUNS="${2:-5}"
BASE_PORT="${BASE_PORT:-19081}"

if [[ -z "$SCENARIO_DIR" ]]; then
  echo "Usage: run_scenario.sh <scenario_dir> [runs]" >&2
  exit 1
fi

if [[ ! -d "$SCENARIO_DIR/variants" ]]; then
  echo "Missing variants directory: $SCENARIO_DIR/variants" >&2
  exit 1
fi

RAW_CSV="$SCENARIO_DIR/results/raw.csv"
mkdir -p "$SCENARIO_DIR/results"
if [[ ! -f "$RAW_CSV" ]]; then
  echo "date,scenario,variant,run,build_ms,image_bytes,startup_ms,status,notes" > "$RAW_CSV"
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
    if curl -fsS "http://localhost:${port}/actuator/health/readiness" >/dev/null 2>&1; then
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
      docker run -d --rm --name "$cname" -p "${port}:8081" "$image_tag" >/dev/null

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

      printf '%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
        "$(date +%F)" "$scenario_name" "$variant" "$run" "$build_ms" "$image_bytes" "$startup_ms" "$status" "$notes" \
        >> "$RAW_CSV"

      echo "run ${run}: build=${build_ms}ms size=${image_bytes} startup=${startup_ms} status=${status}"
    else
      printf '%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
        "$(date +%F)" "$scenario_name" "$variant" "$run" "-1" "-1" "-1" "build_failed" "docker build failed" \
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
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/05-jep483-aot-cache 10
python3 benchmarks/common/analyze_results.py benchmarks/05-jep483-aot-cache/results/raw.csv
```
'''

    (common / 'run_scenario.sh').write_text(run_script)
    (common / 'analyze_results.py').write_text(analyze_script)
    (common / 'README.md').write_text(common_readme)


def write_scenarios() -> None:
    for name, cfg in SCENARIOS.items():
        scenario_dir = BENCH / name
        variants_dir = scenario_dir / 'variants'
        results_dir = scenario_dir / 'results'
        variants_dir.mkdir(parents=True, exist_ok=True)
        results_dir.mkdir(parents=True, exist_ok=True)

        variants_list = '\n'.join(f'- `{v}`' for v in cfg['variants'].keys())
        scenario_readme = f'''# {name}

{cfg['desc']}

## Variants

{variants_list}

## Run benchmark

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/{name} 10
python3 benchmarks/common/analyze_results.py benchmarks/{name}/results/raw.csv
```

## Notes

- Keep environment stable across runs (CPU, memory, Docker version).
- Run at least 10 samples per variant.
- Change only one variable per scenario.
'''

        (scenario_dir / 'README.md').write_text(scenario_readme)
        (results_dir / 'raw.csv').write_text(
            'date,scenario,variant,run,build_ms,image_bytes,startup_ms,status,notes\n'
        )
        (results_dir / 'summary.md').write_text(
            '# Benchmark summary\n\nPaste the markdown table output from `analyze_results.py` here.\n'
        )

        for variant_name, dockerfile_content in cfg['variants'].items():
            variant_dir = variants_dir / variant_name
            variant_dir.mkdir(parents=True, exist_ok=True)
            (variant_dir / 'Dockerfile').write_text(dockerfile_content)


def main() -> None:
    write_common_tools()
    write_scenarios()


if __name__ == '__main__':
    main()

