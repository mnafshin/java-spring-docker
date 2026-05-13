# Results summary: 08-jvm-container-flags

## Recommendation

✅ **Recommended:** `defaults-like` — metric-driven (primary weight: **startup time**)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| defaults-like | 5 | 635 | 1210 | 1644 | 103.02 | 100.0% |
| tuned-flags | 5 | 603 | 1275 | 1443 | 103.02 | 100.0% |

> **Context:** On a developer machine with ample RAM the tuned flags may show marginal
> extra overhead from ZGC initialization. The real benefit appears under memory-constrained
> containers (e.g. 256 Mi limit) where `MaxRAMPercentage=75` prevents heap over-allocation
> and `-XX:+ExitOnOutOfMemoryError` enables fast pod restart.

## Reproduce or extend

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/08-jvm-container-flags 10
python3 benchmarks/common/recommend.py benchmarks/08-jvm-container-flags/results/raw.csv
```
