# 02 - Multi-stage build structure

## Current implementation

Stages: `build` -> `jre-builder` -> `aot-trainer` -> runtime.

## Why this matters

Multi-stage builds keep compilers/tools out of the final image and reduce runtime attack surface.

## Possible ways

### Option A: single-stage image
- Build and run in same image
- Pros: easy to understand
- Cons: large image, more CVE exposure, slower pulls

### Option B: two-stage (build + runtime)
- Pros: significant size/security improvement
- Cons: less flexible for advanced optimizations

### Option C: specialized multi-stage (current)
- Dedicated stages for custom JRE and AOT training
- Pros: best control over size/startup
- Cons: more complexity

## Benchmark strategy

- Build time comparison across A/B/C
- Final image size and layer count
- Pull time from registry on clean nodes
- Cold-start time of container

## Result template

| Variant | Build time | Image size | Pull time | Startup to readiness | Notes |
|---|---:|---:|---:|---:|---|
| A single-stage | | | | | |
| B two-stage | | | | | |
| C specialized multi-stage | | | | | |

## Benchmark results

**Winner:** `specialized-multi-stage` — primary metric: **image size**

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| simple-two-stage | 5 | 7178 | 1336 | 1466 | 134.56 | 100.0% |
| specialized-multi-stage | 5 | 607 | 1367 | 1428 | 103.02 | 100.0% |
