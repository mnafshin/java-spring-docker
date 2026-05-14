# Benchmark toolkit

This folder now contains per-topic benchmark scenarios, each with its own variant Dockerfiles and result files.

`05-jep483-aot-cache` is the canonical complex-app AOT benchmark.

## Folder structure

- `benchmarks/common/`
  - `run_scenario.sh`: builds/runs all variants in a scenario and records metrics
  - `scenarios.json`: single source of truth for scenario enablement and profile defaults
  - `run_all_benchmarks.py`: manifest-driven runner (`--profile quick|full`)
  - `analyze_results.py`: summarizes CSV results into a markdown table
- `benchmarks/01-base-image-pinning/` ... `benchmarks/08-jvm-container-flags/`
- `benchmarks/01-base-image-pinning/` ... `benchmarks/10-native-vs-jvm/`
  - `variants/<variant-name>/Dockerfile`
  - `results/raw.csv`
  - `results/summary.md`

## Native vs JVM scenario

- `benchmarks/10-native-vs-jvm/` compares long-run JVM vs native image behavior.
- Includes dedicated scripts:
  - `run_native_vs_jvm.sh`
  - `analyze_native_vs_jvm.py`
  - `k6-mixed.js`

## What is measured

- Build duration (`build_ms`)
- Runtime image size (`image_bytes`)
- Startup-to-readiness time (`startup_ms`)
- Run status (`ok`, `build_failed`, `readiness_failed`)

## Run one scenario

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/05-jep483-aot-cache 10
python3 benchmarks/common/analyze_results.py benchmarks/05-jep483-aot-cache/results/raw.csv
```

Optional overrides for services that do not use default management settings:

```bash
cd /path/to/your-java25-project
CONTAINER_MGMT_PORT=9001 READINESS_PATH=/readyz bash benchmarks/common/run_scenario.sh benchmarks/05-jep483-aot-cache 10
```

## Run all benchmarks and refresh markdown reports

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_all_benchmarks.sh --profile quick
bash benchmarks/common/run_all_benchmarks.sh --profile full
```

For Maven-targeted runs, regenerate variants/docs for Maven first:

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_all_benchmarks.sh --profile quick --build-tool maven
bash benchmarks/common/run_all_benchmarks.sh --profile full --build-tool maven
```

- Runs enabled scenarios from `benchmarks/common/scenarios.json`.
- Runs `10-native-vs-jvm` via its dedicated long-run script unless `--skip-native` is set.
- Refreshes scenario `results/summary.md` files and deep-dive `README.md` files.

## Optional legacy script

- `benchmarks/startup_matrix.sh` is kept for simple startup-only comparisons.
