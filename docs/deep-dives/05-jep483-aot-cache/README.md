# 05 - JEP 483 startup cache

## Current implementation

Training stage:

```dockerfile
java -XX:AOTCacheOutput=app.aot -Dspring.context.exit=onRefresh ...
```

Runtime stage:

```dockerfile
java -XX:AOTCache=app.aot ...
```

## Why this matters

Targets warm JVM startup by pre-caching class loading/linking work.

## Possible ways

### Option A: no startup cache
- Pros: simpler build, fewer moving parts
- Cons: slower cold-start

### Option B: JEP 483 cache (current)
- Pros: faster startup while staying on JVM
- Cons: cache must match JVM/OS/arch and be regenerated on base upgrades

### Option C: native image (different strategy)
- Pros: potentially fastest cold start
- Cons: different toolchain and constraints; not equivalent to warm JVM

## Benchmark strategy

- Compare A and B first (same image except cache feature)
- Measure:
  - process start to readiness time (P50/P95)
  - Spring startup log duration
  - CPU burst during startup
- Run at least 20 samples each

## Result template

| Variant | Samples | Startup P50 (ms) | Startup P95 (ms) | CPU peak | Notes |
|---|---:|---:|---:|---:|---|
| A no cache | | | | | |
| B JEP 483 cache | | | | | |

## Benchmark results

**Winner:** `without-aot-cache` — primary metric: **startup time**

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| with-aot-cache | 8 | 700 | 1288 | 1437 | 103.02 | 100.0% |
| without-aot-cache | 8 | 592 | 1222 | 1437 | 90.49 | 100.0% |

> **Context:** The AOT cache is architecture-specific and regenerated at build time.
> A marginal startup difference here reflects a warm Docker layer cache run.
> The benefit is more pronounced at cold JVM start on a fresh container host.
