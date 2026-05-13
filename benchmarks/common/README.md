# Benchmark common tooling

## Files

- `run_scenario.sh`: builds and runs all variants in one scenario and appends metrics to CSV.
- `analyze_results.py`: summarizes CSV results into a markdown table.
- `recommend.py`: reads one or more CSVs, picks a winner per scenario with explicit decision rules, and explains why.

## Typical workflow

### Step 1 – run a scenario
```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/05-jep483-aot-cache 10
```

### Step 2 – raw summary table
```bash
python3 benchmarks/common/analyze_results.py benchmarks/05-jep483-aot-cache/results/raw.csv
```

### Step 3 – winner + recommendation
```bash
python3 benchmarks/common/recommend.py benchmarks/05-jep483-aot-cache/results/raw.csv
```

### Step 4 – full aggregate report across all scenarios
```bash
python3 benchmarks/common/recommend.py benchmarks/*/results/raw.csv
```

## Decision rules in `recommend.py`

Each scenario is classified as one of:

- **metric-driven**: a weighted score over build time, image size, and startup time determines the winner
- **policy-driven**: the best-practice variant always wins regardless of metrics (security and reliability scenarios)

Weights per scenario are tuned to reflect what matters most for each topic (e.g. startup time matters most for `05-jep483-aot-cache`, build time for `03-buildkit-gradle-cache`).

