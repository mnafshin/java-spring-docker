#!/usr/bin/env bash
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

      printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
        "$(date +%F)" "$scenario_name" "$variant" "$run" "$build_ms" "$image_bytes" "$startup_ms" "$status" "$notes" "$HOST_NAME" "$DOCKER_VERSION" "$RUN_PROFILE" >> "$RAW_CSV"

      echo "run ${run}: build=${build_ms}ms size=${image_bytes} startup=${startup_ms} status=${status}"
    else
      printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
        "$(date +%F)" "$scenario_name" "$variant" "$run" "-1" "-1" "-1" "build_failed" "docker build failed" "$HOST_NAME" "$DOCKER_VERSION" "$RUN_PROFILE" >> "$RAW_CSV"

      echo "run ${run}: build failed"
    fi
  done
done
