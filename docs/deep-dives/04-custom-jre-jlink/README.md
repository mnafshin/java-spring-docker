# 04 - Custom JRE with jdeps/jlink

## Current implementation

- Use `jdeps --print-module-deps` to derive modules.
- Merge with `musthave_modules.txt`.
- Build custom runtime via `jlink`.

## Why this matters

A custom runtime removes unused modules and reduces runtime image footprint.

## Possible ways

### Option A: full JRE/JDK base image
- Pros: easiest compatibility
- Cons: larger image, broader attack surface

### Option B: jlink custom runtime (current)
- Pros: smaller image, tighter module set
- Cons: maintenance overhead when dependencies change

### Option C: distroless Java base (no jlink)
- Pros: hardened runtime footprint
- Cons: less control over exact module composition

## Benchmark strategy

- Measure image size and container startup time
- Measure memory footprint after warm-up
- Validate functional compatibility under integration tests

## Result template

| Variant | Image size | Startup to readiness | RSS at steady state | Compatibility issues |
|---|---:|---:|---:|---|
| A full JRE/JDK | | | | |
| B jlink custom | | | | |
| C distroless Java | | | | |

## Benchmark results

**Winner:** `with-jlink-runtime` — primary metric: **image size**

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| with-jlink-runtime | 5 | 641 | 1364 | 1428 | 103.02 | 100.0% |
| without-jlink-runtime | 5 | 3682 | 1435 | 1916 | 147.04 | 100.0% |
