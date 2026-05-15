# Benchmark comparison report

This report summarizes the current sample benchmark snapshot used by `springdocker`.

## Decision matrix

| Scenario | Preferred strategy | Why |
|---|---|---|
| 01 Multi-stage structure | specialized multi-stage | lower image size and better build cost |
| 02 BuildKit cache | with-cache | much faster builds |
| 03 JLink + JDeps | with-jlink | smaller runtime image with similar startup |
| 04 JEP 483 AOT cache | with-aot-cache | better startup and tail latency |
| 05 JVM flags | workload-dependent | host sensitivity makes the winner variable |
| 06 Base image choice | debian-bookworm-slim | best size/startup balance in the sample runs |
| 07 Native vs JVM | workload-dependent | cold-start vs throughput tradeoff |

## Scenario tables

### 01 · Multi-stage structure

| Variant | Image MB | Build avg | Startup avg |
|---|---:|---:|---:|
| specialized-multi-stage | 100.40 | 645 ms | 1,428 ms |
| simple-two-stage | 131.54 | 4,135 ms | 1,240 ms |

### 02 · BuildKit cache

| Variant | Build avg |
|---|---:|
| with-cache | 622 ms |
| without-cache | 3,410 ms |

### 03 · JLink + JDeps

| Variant | Image MB | Startup avg |
|---|---:|---:|
| with-jlink | 100.40 | 1,423 ms |
| without-jlink | 144.38 | 1,446 ms |

### 04 · JEP 483 AOT cache

| Variant | Startup avg | p95 |
|---|---:|---:|
| with-aot-cache | 1,429 ms | 1,462 ms |
| without-aot-cache | 1,509 ms | 1,730 ms |

### 05 · JVM flags

| Variant | Result |
|---|---|
| tuned-flags | useful for some quick runs |
| defaults-like | better on this host in the full-profile run |

### 06 · Base image choice

| Variant | Result |
|---|---|
| temurin-jre | larger but simplest |
| minimal-runtime | smaller image, more constrained runtime |

### 07 · Native vs JVM

| Variant | Result |
|---|---|
| native | best for cold-start focused workloads |
| JVM | best when throughput and ecosystem compatibility matter more |

## Reproducibility

Generate benchmark assets, run the benchmarks, and re-run the analyzer before updating this report:

```bash
springdocker benchmark generate --project-root samples/java-spring-docker --java-version 25
springdocker benchmark run --project-root samples/java-spring-docker --profile full --runner-arg --skip-native
springdocker benchmark analyze --project-root samples/java-spring-docker benchmarks/03-custom-jre-jlink/results/raw.csv --format table
```

## Notes

- This report is a snapshot, not a promise about every workload.
- Historical comparison can be added by diffing future runs against the same scenario layout.
