# 03 - BuildKit Gradle cache mount

## Current implementation

```dockerfile
RUN --mount=type=cache,sharing=locked,target=/root/.gradle \
    ./gradlew --no-daemon dependencies -q
```

and similar mount for `bootJar`.

## Why this matters

This cache speeds up repeated builds by reusing Gradle artifacts across Docker builds.

## Possible ways

### Option A: no BuildKit cache mount
- Pros: no special CI setup
- Cons: repeated dependency downloads, slower builds

### Option B: BuildKit cache mount local only
- Pros: great for developer machines
- Cons: limited benefit on ephemeral CI runners

### Option C: BuildKit cache + remote cache backend (recommended CI)
- Pros: cache persists across CI jobs/pipelines
- Cons: requires `buildx` + cache configuration

## Benchmark strategy

- Run 5 sequential builds on same commit
- Measure wall-clock build time for each run
- Compare local runner and CI runner behavior
- For CI: compare with and without `--cache-to/--cache-from`

## Result template

| Environment | Variant | Run 1 | Run 2 | Run 3 | Median | Notes |
|---|---|---:|---:|---:|---:|---|
| dev machine | A/B/C | | | | | |
| CI runner | A/B/C | | | | | |

## Benchmark results

**Winner:** `with-buildkit-cache` — primary metric: **build time**

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| with-buildkit-cache | 5 | 917 | 1263 | 1460 | 103.02 | 100.0% |
| without-buildkit-cache | 5 | 7187 | 1382 | 1463 | 103.02 | 100.0% |
