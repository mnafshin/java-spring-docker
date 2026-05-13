# Benchmark toolkit

This folder now contains per-topic benchmark scenarios, each with its own variant Dockerfiles and result files.

## Folder structure

- `benchmarks/common/`
  - `run_scenario.sh`: builds/runs all variants in a scenario and records metrics
  - `analyze_results.py`: summarizes CSV results into a markdown table
- `benchmarks/01-base-image-pinning/` ... `benchmarks/08-jvm-container-flags/`
  - `variants/<variant-name>/Dockerfile`
  - `results/raw.csv`
  - `results/summary.md`

## What is measured

- Build duration (`build_ms`)
- Runtime image size (`image_bytes`)
- Startup-to-readiness time (`startup_ms`)
- Run status (`ok`, `build_failed`, `readiness_failed`)

## Run one scenario

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/05-jep483-aot-cache 10
python3 benchmarks/common/analyze_results.py benchmarks/05-jep483-aot-cache/results/raw.csv
```

## Optional legacy script

- `benchmarks/startup_matrix.sh` is kept for simple startup-only comparisons.
