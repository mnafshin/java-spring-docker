# Results summary: 03-buildkit-gradle-cache

## Recommendation

✅ **Recommended:** `with-buildkit-cache` — metric-driven (primary weight: **build time**)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| with-buildkit-cache | 5 | 917 | 1263 | 1460 | 103.02 | 100.0% |
| without-buildkit-cache | 5 | 7187 | 1382 | 1463 | 103.02 | 100.0% |

## Reproduce or extend

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/03-buildkit-gradle-cache 10
python3 benchmarks/common/recommend.py benchmarks/03-buildkit-gradle-cache/results/raw.csv
```
