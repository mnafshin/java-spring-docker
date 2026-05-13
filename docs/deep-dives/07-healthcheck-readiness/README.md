# 07 - Healthcheck using readiness endpoint

## Current implementation

```dockerfile
HEALTHCHECK ... curl -fsS http://localhost:8081/actuator/health/readiness
```

## Why this matters

Readiness reflects whether the app should receive traffic, not just whether a process exists.

## Possible ways

### Option A: no healthcheck
- Pros: simple image
- Cons: slower local diagnostics, fewer signals outside orchestrator

### Option B: process/port-only check
- Pros: minimal implementation
- Cons: false positives when app is alive but not ready

### Option C: readiness endpoint check (current)
- Pros: application-aware health signal
- Cons: requires management endpoint configuration

## Benchmark strategy

- Induce dependency delays/failures during startup
- Compare false-ready and false-unhealthy rates
- Measure time-to-detect unhealthy state

## Result template

| Variant | False ready rate | False unhealthy rate | Detection time | Notes |
|---|---:|---:|---:|---|
| A none | | | | |
| B process/port | | | | |
| C readiness endpoint | | | | |

## Benchmark results

**Winner:** `with-readiness-healthcheck` — policy decision (security / reliability)

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| with-readiness-healthcheck | 6 | 1984 | 1294 | 1458 | 103.02 | 100.0% |
| without-healthcheck | 6 | 619 | 1288 | 1423 | 103.02 | 100.0% |
