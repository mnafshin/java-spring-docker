# Results summary: 01-base-image-pinning

## Recommendation

✅ **Recommended:** `digest-pinned` — policy decision (security / reliability, not metric-driven)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| digest-pinned | 5 | 615 | 1269 | 1455 | 103.02 | 100.0% |
| tag-only | 5 | 6581 | 1431 | 1443 | 103.23 | 100.0% |

## Reproduce or extend

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/01-base-image-pinning 10
python3 benchmarks/common/recommend.py benchmarks/01-base-image-pinning/results/raw.csv
```
