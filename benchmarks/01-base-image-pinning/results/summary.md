# Results summary: 01-base-image-pinning

## Recommendation

✅ **Recommended:** `digest-pinned` — policy decision (security / reliability, not metric-driven)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| digest-pinned | 15 | 2390 | 1515 | 2096 | 100.40 | 86.7% |
| tag-only | 15 | 2296 | 1450 | 1801 | 100.62 | 86.7% |

## Reproduce or extend

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/01-base-image-pinning 10
python3 benchmarks/common/recommend.py benchmarks/01-base-image-pinning/results/raw.csv
```
