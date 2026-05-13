# Deep dives for Dockerfile critical points

Each folder covers one critical Dockerfile decision and is designed for benchmark-first adoption.

## How to use

1. Read `Current implementation`.
2. Select one or more alternatives.
3. Execute the benchmark strategy in the same environment.
4. Record results in the template section.
5. Decide based on measured impact, not assumption.

## Benchmark assets

Concrete benchmark-ready variant Dockerfiles now live under `benchmarks/`:

- `benchmarks/01-base-image-pinning/` ... `benchmarks/08-jvm-container-flags/`
- Each includes `variants/<name>/Dockerfile` and `results/` files.
- Shared tooling is in `benchmarks/common/`.

## Folders

- `01-base-image-pinning`
- `02-multi-stage-build-structure`
- `03-buildkit-gradle-cache`
- `04-custom-jre-jlink`
- `05-jep483-aot-cache`
- `06-runtime-hardening-non-root-tmp`
- `07-healthcheck-readiness`
- `08-jvm-container-flags`
- `09-base-image-choice` _(alpine, debian-slim, ubuntu, eclipse-temurin-jre, ubi9-minimal)_
