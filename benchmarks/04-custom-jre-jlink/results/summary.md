# Results summary: 04-custom-jre-jlink

## Recommendation

✅ **Recommended:** `with-jlink-runtime` — metric-driven (primary weight: **image size**)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| with-jlink-runtime | 5 | 641 | 1364 | 1428 | 103.02 | 100.0% |
| without-jlink-runtime | 5 | 3682 | 1435 | 1916 | 147.04 | 100.0% |

## Reproduce or extend

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/04-custom-jre-jlink 10
python3 benchmarks/common/recommend.py benchmarks/04-custom-jre-jlink/results/raw.csv
```
