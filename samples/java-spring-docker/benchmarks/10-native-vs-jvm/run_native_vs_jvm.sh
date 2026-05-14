#!/usr/bin/env bash
set -euo pipefail

DURATION="60m"
VUS="50"
CPU_WORK="12000"
PORT="18080"
RUNS="1"
RUN_PROFILE="${RUN_PROFILE:-manual}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --duration) DURATION="$2"; shift 2 ;;
    --vus) VUS="$2"; shift 2 ;;
    --cpu-work) CPU_WORK="$2"; shift 2 ;;
    --port) PORT="$2"; shift 2 ;;
    --runs) RUNS="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BENCH_DIR="$ROOT_DIR/benchmarks/10-native-vs-jvm"
RESULTS_DIR="$BENCH_DIR/results"
RAW_CSV="$RESULTS_DIR/raw.csv"
SCENARIO="10-native-vs-jvm"
EXPECTED_HEADER="date,scenario,variant,run,build_ms,image_bytes,startup_ms,status,notes,host,docker_version,run_profile,duration,vus,rps,p95_ms,p99_ms,error_rate,cpu_pct,memory_mb"
LEGACY_HEADER="date,variant,build_ms,image_mb,startup_ms,duration,vus,rps,p95_ms,p99_ms,error_rate,cpu_pct,memory_mb,status,notes"
HOST_NAME="$(hostname -s 2>/dev/null || hostname)"
DOCKER_VERSION="$(docker --version 2>/dev/null | sed 's/,//g' | awk '{print $3}' || echo unknown)"

mkdir -p "$RESULTS_DIR"
if [[ -f "$RAW_CSV" ]]; then
  current_header="$(head -n 1 "$RAW_CSV" | tr -d '\r')"
  if [[ "$current_header" == "$LEGACY_HEADER" ]]; then
    backup_csv="$RESULTS_DIR/raw.legacy.$(date +%s).csv"
    mv "$RAW_CSV" "$backup_csv"
    echo "Archived legacy CSV header to: $backup_csv"
  fi
fi
if [[ ! -f "$RAW_CSV" ]]; then
  echo "$EXPECTED_HEADER" > "$RAW_CSV"
fi

wait_ready_ms() {
  local port="$1"
  local start_ms end_ms
  start_ms=$(python3 - <<'PY'
import time
print(int(time.time() * 1000))
PY
)
  for _ in $(seq 1 240); do
    if curl -fsS "http://localhost:${port}/actuator/health/readiness" >/dev/null 2>&1; then
      end_ms=$(python3 - <<'PY'
import time
print(int(time.time() * 1000))
PY
)
      echo $((end_ms - start_ms))
      return 0
    fi
    sleep 0.25
  done
  echo "-1"
  return 1
}

run_variant() {
  local variant="$1"
  local run_index="$2"
  local dockerfile="$BENCH_DIR/variants/$variant/Dockerfile"
  local image="bench-native-vs-jvm:$variant"
  local summary_json="$RESULTS_DIR/${variant}-${run_index}-summary.json"
  local container="bench-${variant}-${run_index}-$RANDOM"

  echo "=== Running variant: $variant ==="

  local bstart bend build_ms
  bstart=$(python3 - <<'PY'
import time
print(int(time.time() * 1000))
PY
)

  if ! docker build -q -f "$dockerfile" -t "$image" "$ROOT_DIR" >/dev/null; then
    printf '%s,%s,%s,%s,-1,-1,-1,%s,%s,%s,%s,%s,%s,%s,-1,-1,-1,-1,-1,-1\n' \
      "$(date +%F)" "$SCENARIO" "$variant" "$run_index" "build_failed" "docker build failed" "$HOST_NAME" "$DOCKER_VERSION" "$RUN_PROFILE" "$DURATION" "$VUS" >> "$RAW_CSV"
    echo "Build failed for $variant"
    return 1
  fi

  bend=$(python3 - <<'PY'
import time
print(int(time.time() * 1000))
PY
)
  build_ms=$((bend - bstart))

  local image_bytes
  image_bytes="$(docker image inspect "$image" --format '{{.Size}}')"

  docker run -d --rm --name "$container" -p "$PORT:8080" -p "$((PORT+1)):8081" "$image" >/dev/null

  local startup_ms
  startup_ms=$(wait_ready_ms "$((PORT+1))") || true

  # Load test via containerized k6
  # Run k6 in the same network namespace as the app container.
  # This avoids host.docker.internal portability issues.
  docker run --rm \
    --network "container:$container" \
    -v "$BENCH_DIR:/scripts" \
    grafana/k6 run /scripts/k6-mixed.js \
    --env BASE_URL="http://localhost:8080" \
    --env DURATION="$DURATION" \
    --env VUS="$VUS" \
    --env CPU_WORK="$CPU_WORK" \
    --summary-export "/scripts/results/${variant}-${run_index}-summary.json" >/dev/null

  local cpu_mem
  cpu_mem=$(docker stats --no-stream --format '{{.CPUPerc}},{{.MemUsage}}' "$container" | head -n1)
  local cpu_pct mem_mb
  cpu_pct=$(echo "$cpu_mem" | awk -F',' '{gsub(/%/,"",$1); print $1+0}')
  mem_mb=$(echo "$cpu_mem" | awk -F',' '{split($2,a,"/"); gsub(/MiB/ ,"",a[1]); gsub(/GiB/,"",a[1]); print a[1]+0}')

  local metrics
  metrics=$(python3 - <<PY
import json
from pathlib import Path
p = Path("$summary_json")
if not p.exists():
    print("-1,-1,-1,-1")
else:
    data = json.loads(p.read_text())
    m = data.get('metrics', {})
    rps = m.get('http_reqs', {}).get('rate', -1)
    p95 = m.get('http_req_duration', {}).get('values', {}).get('p(95)', -1)
    p99 = m.get('http_req_duration', {}).get('values', {}).get('p(99)', -1)
    err = m.get('http_req_failed', {}).get('values', {}).get('rate', -1)
    print(f"{rps},{p95},{p99},{err}")
PY
)

  docker stop "$container" >/dev/null || true

  IFS=',' read -r rps p95 p99 err <<< "$metrics"
  printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%.3f,%.3f,%.3f,%.6f,%s,%s\n' \
    "$(date +%F)" "$SCENARIO" "$variant" "$run_index" "$build_ms" "$image_bytes" "$startup_ms" "ok" "" "$HOST_NAME" "$DOCKER_VERSION" "$RUN_PROFILE" "$DURATION" "$VUS" \
    "$rps" "$p95" "$p99" "$err" "$cpu_pct" "$mem_mb" >> "$RAW_CSV"

  echo "$variant run ${run_index} done: build=${build_ms}ms startup=${startup_ms}ms rps=${rps} p95=${p95}"
}

for run_idx in $(seq 1 "$RUNS"); do
  run_variant jvm "$run_idx"
  run_variant native "$run_idx"
done

echo "Results written to $RAW_CSV"

