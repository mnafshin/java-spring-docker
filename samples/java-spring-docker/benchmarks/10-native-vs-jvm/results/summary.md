# Results summary: 10-native-vs-jvm

## Recommendation

✅ **Recommended:** `native` — metric-driven (primary weight: **startup time**)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| jvm | 1 | 8956 | 2025 | 2025 | 130.56 | 100.0% |
| native | 1 | 634891 | 308 | 308 | 55.71 | 100.0% |

> **Context:** Native typically wins on cold start and memory footprint, while JVM can
> win on long-run throughput due to JIT optimization. Use your 60-minute run results
> and endpoint mix to decide per service, not globally.

## Reproduce or extend

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/10-native-vs-jvm 10
python3 benchmarks/common/recommend.py benchmarks/10-native-vs-jvm/results/raw.csv
```
