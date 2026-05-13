# Results summary: 10-native-vs-jvm

## Recommendation

✅ **Recommended:** `native` — metric-driven (primary weight: **startup time**)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| jvm | 2 | 6255 | 1972 | 1976 | 134.77 | 100.0% |
| native | 1 | 154550 | 302 | 302 | 59.74 | 100.0% |

> **Context:** Native typically wins on cold start and memory footprint, while JVM can
> win on long-run throughput due to JIT optimization. Use your 60-minute run results
> and endpoint mix to decide per service, not globally.

## Reproduce or extend

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/10-native-vs-jvm 10
python3 benchmarks/common/recommend.py benchmarks/10-native-vs-jvm/results/raw.csv
```
