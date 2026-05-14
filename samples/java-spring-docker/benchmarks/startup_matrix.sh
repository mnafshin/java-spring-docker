#!/usr/bin/env bash
set -euo pipefail

RUNS=5
BASE_PORT=18080
VARIANTS=""

usage() {
  cat <<'EOF'
Usage:
  startup_matrix.sh --variants name=image,name2=image2 [--runs N] [--base-port P]

Example:
  startup_matrix.sh --variants baseline=myapp:baseline,aot=myapp:aot --runs 10
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --variants)
      VARIANTS="$2"
      shift 2
      ;;
    --runs)
      RUNS="$2"
      shift 2
      ;;
    --base-port)
      BASE_PORT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$VARIANTS" ]]; then
  echo "--variants is required" >&2
  usage
  exit 1
fi

wait_ready_ms() {
  local port="$1"
  local attempts=120
  local sleep_sec=0.25
  local start_ms end_ms

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

  echo "-1"
  return 1
}

summary() {
  local values="$1"
  python3 - <<PY
vals = [int(v) for v in "${values}".split(",") if v]
if not vals:
    print("count=0")
else:
    print(f"count={len(vals)} min={min(vals)}ms avg={sum(vals)/len(vals):.1f}ms max={max(vals)}ms")
PY
}

IFS=',' read -r -a pairs <<< "$VARIANTS"

for idx in "${!pairs[@]}"; do
  pair="${pairs[$idx]}"
  name="${pair%%=*}"
  image="${pair#*=}"
  port=$((BASE_PORT + idx))

  echo ""
  echo "=== Variant: ${name} (${image}) ==="

  times=""
  for run in $(seq 1 "$RUNS"); do
    container_name="startup-bench-${name}-${run}-$RANDOM"
    docker run -d --rm --name "$container_name" -p "${port}:8081" "$image" >/dev/null

    ms="-1"
    if ms=$(wait_ready_ms "$port"); then
      echo "run ${run}: ${ms} ms"
      if [[ -z "$times" ]]; then
        times="$ms"
      else
        times="${times},${ms}"
      fi
    else
      echo "run ${run}: FAILED readiness"
      docker logs "$container_name" | tail -n 30 | cat
    fi

    docker stop "$container_name" >/dev/null || true
  done

  echo "summary: $(summary "$times")"
done

