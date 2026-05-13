# Results summary: 01-base-image-pinning

## Recommendation

✅ **Recommended:** `digest-pinned` — policy decision (security / reliability, not metric-driven)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| digest-pinned | 3 | 7264 | 1431 | 1437 | 103.69 | 100.0% |
| tag-only | 3 | 6267 | 1415 | 1438 | 103.91 | 100.0% |

## Reproduce or extend

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/01-base-image-pinning 10
python3 benchmarks/common/recommend.py benchmarks/01-base-image-pinning/results/raw.csv
```
