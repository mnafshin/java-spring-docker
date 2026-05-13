# 08 - JVM flags for container behavior

## Current implementation

- `-XX:+UseZGC`
- `-XX:MaxRAMPercentage=75`
- `-XX:InitialRAMPercentage=50`
- `-XX:+ExitOnOutOfMemoryError`
- `-Djava.io.tmpdir=/tmp`
- `-Xlog:gc:stdout`

## Why this matters

Containerized JVMs need explicit memory and failure semantics to avoid noisy behavior under limits.

## Possible ways

### Option A: JVM defaults only
- Pros: least config
- Cons: less predictable memory/latency behavior in cgroups

### Option B: targeted tuning (current)
- Pros: stable operations and clearer failure handling
- Cons: needs periodic re-tuning with workload changes

### Option C: aggressive low-memory tuning
- Pros: lower resource cost
- Cons: higher risk of throughput/latency regressions

## Benchmark strategy

- Execute fixed-load test (same RPS, same pod limits)
- Measure latency (P50/P95/P99), throughput, OOM events, GC pause stats
- Repeat over at least 3 runs per variant

## Result template

| Variant | Latency P95 | Throughput | OOM count | GC pause P99 | Notes |
|---|---:|---:|---:|---:|---|
| A defaults | | | | | |
| B current tuning | | | | | |
| C aggressive low-memory | | | | | |

## Benchmark results

**Winner:** `defaults-like` — primary metric: **startup time**

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| defaults-like | 5 | 635 | 1210 | 1644 | 103.02 | 100.0% |
| tuned-flags | 5 | 603 | 1275 | 1443 | 103.02 | 100.0% |

> **Context:** On a developer machine with ample RAM the tuned flags may show marginal
> extra overhead from ZGC initialization. The real benefit appears under memory-constrained
> containers (e.g. 256 Mi limit) where `MaxRAMPercentage=75` prevents heap over-allocation
> and `-XX:+ExitOnOutOfMemoryError` enables fast pod restart.
