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

There is no separate warmup phase in the current runner; each recorded row is a full build-and-probe attempt.

## Statistical handling

`springdocker benchmark analyze` summarizes the raw CSV with:

- mean build time
- mean startup time
- p95 startup time
- average image size
- success rate

When a metric is missing, the analyzer leaves the field empty instead of failing the summary.

## Reproducibility notes

- Each scenario is stored in a stable directory name.
- Scenario variants are generated from the same `DockerfileOptions` inputs.
- The CSV schema is fixed and validated by the analyzer before aggregation.

## Current limitations

- The runner assumes Docker is available on the host.
- Native scenarios are skipped by the internal runner.
- Statistical thresholds currently exist only for success rate.
