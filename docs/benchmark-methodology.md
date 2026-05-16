# Benchmark methodology

This repository uses scenario-based Docker benchmarks against the sample Spring Boot project in `samples/java-spring-docker/`.

## Measurement model

Each benchmark run records one row per build-and-startup attempt with these fields:

- `date`
- `scenario`
- `variant`
- `run`
- `build_ms`
- `image_bytes`
- `startup_ms`
- `status`
- `notes`
- `host`
- `docker_version`
- `run_profile`

If available, the analyzer also reports RSS memory and CPU usage columns.

The runner writes rows into `results/raw.csv` next to each scenario.

## Run profiles

The CLI supports two profiles:

- `quick`
- `full`

Default run counts are scenario-aware:

- `04-jep483-aot-cache`: 8 runs for `quick`, 15 for `full`
- all other standard scenarios: 3 runs for `quick`, 10 for `full`

You can override the number of runs with `benchmark run --runner-arg --runs --runner-arg N`.

## What the runner measures

The internal runner captures:

1. Docker build time in milliseconds.
2. Image size from `docker image inspect`.
3. Startup time by probing `/actuator/health/readiness`.
4. Build or readiness failure status.
5. Host metadata and Docker version for traceability.

Warmup runs are optional and are executed before recording rows; they are excluded from `raw.csv`.

## Statistical handling

`springdocker benchmark analyze` summarizes the raw CSV with:

- mean build time
- build-time standard deviation
- build-time 95% confidence interval
- mean startup time
- startup standard deviation
- p95 startup time
- p99 startup time
- startup 95% confidence interval
- average image size
- average RSS memory
- average CPU usage
- success rate

Confidence intervals use a 95% normal-approximation interval (`mean ± 1.96 * stdev / sqrt(n)`) when at least two valid samples exist.

For historical regression tracking, save a baseline summary with `--output baseline.json` and compare later runs with `--baseline baseline.json --fail-on-regression-above 20`.

The CI workflow uses the checked-in sample baseline under `samples/java-spring-docker/benchmarks/09-base-image-choice/results/baseline.json` to fail fast when the sample report regresses beyond the configured threshold.

## Reproducibility controls

`springdocker benchmark run` supports optional isolation controls for more stable comparisons:

- `--cpuset-cpus` pins container execution to specific CPUs.
- `--memory` caps the container memory allocation.
- `--warmup-runs` performs discarded warmup probes before the measured runs.
- `--max-workers` runs standard scenarios concurrently with bounded worker parallelism.
- `--normalized-runtime` applies read-only/no-new-privileges/tmpfs runtime hardening.

The same keys can be set under `[benchmark.run]` in `.springdocker.toml`.

When a metric is missing, the analyzer leaves the field empty instead of failing the summary.

## Reproducibility notes

- Each scenario is stored in a stable directory name.
- Scenario variants are generated from the same `DockerfileOptions` inputs.
- The CSV schema is fixed and validated by the analyzer before aggregation.

## Current limitations

- The runner assumes Docker is available on the host.
- Native scenarios are skipped by the internal runner.
- The current reproducibility controls are opt-in and do not change defaults.
