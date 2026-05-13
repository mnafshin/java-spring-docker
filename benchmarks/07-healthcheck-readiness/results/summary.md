# Results summary: 07-healthcheck-readiness

## Recommendation

✅ **Recommended:** `with-readiness-healthcheck` — policy decision (security / reliability, not metric-driven)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| with-readiness-healthcheck | 6 | 1984 | 1294 | 1458 | 103.02 | 100.0% |
| without-healthcheck | 6 | 619 | 1288 | 1423 | 103.02 | 100.0% |

## Reproduce or extend

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/07-healthcheck-readiness 10
python3 benchmarks/common/recommend.py benchmarks/07-healthcheck-readiness/results/raw.csv
```
