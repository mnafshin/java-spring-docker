# Benchmark common tooling

## Files

- `run_scenario.sh`: builds and runs all variants in one scenario and appends metrics to CSV.
- `run_all_benchmarks.py`: manifest-driven orchestration for all benchmark scenarios.
- `run_all_benchmarks.sh`: shell wrapper for `run_all_benchmarks.py`.
- `scenarios.json`: scenario list, enablement, and profile defaults.
- `analyze_results.py`: summarizes CSV results into a markdown table.
- `recommend.py`: reads one or more CSVs, picks a winner per scenario with explicit decision rules, and explains why.

## Typical workflow

### Step 1 – run a scenario
```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/05-jep483-aot-cache 10
```

### Step 1b – run all scenarios and update markdown in one command
```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_all_benchmarks.sh --profile quick
bash benchmarks/common/run_all_benchmarks.sh --profile full
```

- Includes `10-native-vs-jvm` unless `--skip-native` is passed.
- Updates `benchmarks/*/results/summary.md`.
- Scenario deep-dive notes live in each `benchmarks/*/DEEP_DIVE.md` file.

## Profiles and metadata

- Profiles are configured in `benchmarks/common/scenarios.json`.
- `quick`: lower sample count for fast iteration.
- `full`: higher sample count for presentation-grade comparisons.
- New CSV rows include metadata columns: `host`, `docker_version`, and `run_profile`.

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

## Native vs JVM scenario

`benchmarks/10-native-vs-jvm/` uses dedicated scripts because it captures long-run throughput and latency in addition to startup and image/build metrics:

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/10-native-vs-jvm/run_native_vs_jvm.sh --duration 60m --vus 50
python3 benchmarks/10-native-vs-jvm/analyze_native_vs_jvm.py benchmarks/10-native-vs-jvm/results/raw.csv
```

