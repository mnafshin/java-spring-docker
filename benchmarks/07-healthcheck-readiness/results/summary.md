# Results summary: 07-healthcheck-readiness

## Recommendation

✅ **Recommended:** `with-readiness-healthcheck` — policy decision (security / reliability, not metric-driven)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| with-readiness-healthcheck | 3 | 595 | 1432 | 1452 | 103.69 | 100.0% |
| without-healthcheck | 3 | 601 | 1423 | 1442 | 103.69 | 100.0% |

## Reproduce or extend

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/07-healthcheck-readiness 10
python3 benchmarks/common/recommend.py benchmarks/07-healthcheck-readiness/results/raw.csv
```
