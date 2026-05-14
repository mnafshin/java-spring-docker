# Results summary: 08-jvm-container-flags

## Recommendation

✅ **Recommended:** `defaults-like` — metric-driven (primary weight: **startup time**)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| defaults-like | 15 | 625 | 1370 | 1459 | 100.40 | 86.7% |
| tuned-flags | 15 | 616 | 1468 | 1709 | 100.40 | 86.7% |

> **Context:** On a developer machine with ample RAM the tuned flags may show marginal
> extra overhead from ZGC initialization. The real benefit appears under memory-constrained
> containers (e.g. 256 Mi limit) where `MaxRAMPercentage=75` prevents heap over-allocation
> and `-XX:+ExitOnOutOfMemoryError` enables fast pod restart.

## Reproduce or extend

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/08-jvm-container-flags 10
python3 benchmarks/common/recommend.py benchmarks/08-jvm-container-flags/results/raw.csv
```
