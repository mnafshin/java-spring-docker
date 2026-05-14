#!/bin/bash
# Usage: bash run_benchmark.sh [num_runs]

set -euo pipefail

NUM_RUNS="${1:-15}"
BENCHMARK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$BENCHMARK_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "==========================================="
echo "AOT CACHE COMPLEX BENCHMARK"
echo "==========================================="
echo "Scenario: benchmarks/05-jep483-aot-cache"
echo "Number of runs: $NUM_RUNS"
echo ""

bash benchmarks/common/run_scenario.sh "benchmarks/05-jep483-aot-cache" "$NUM_RUNS"
python3 benchmarks/common/analyze_results.py "benchmarks/05-jep483-aot-cache/results/raw.csv"

echo ""
echo "For detailed analysis, see: benchmarks/05-jep483-aot-cache/README.md"
echo ""

