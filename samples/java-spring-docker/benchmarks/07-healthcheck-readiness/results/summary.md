# Results summary: 07-healthcheck-readiness

## Recommendation

✅ **Recommended:** `with-readiness-healthcheck` — policy decision (security / reliability, not metric-driven)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| with-readiness-healthcheck | 15 | 599 | 1450 | 1803 | 100.40 | 86.7% |
| without-healthcheck | 15 | 613 | 1435 | 1467 | 100.40 | 86.7% |

## Reproduce or extend

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/07-healthcheck-readiness 10
python3 benchmarks/common/recommend.py benchmarks/07-healthcheck-readiness/results/raw.csv
```
