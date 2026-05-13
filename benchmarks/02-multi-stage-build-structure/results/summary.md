# Results summary: 02-multi-stage-build-structure

## Recommendation

✅ **Recommended:** `specialized-multi-stage` — metric-driven (primary weight: **image size**)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| simple-two-stage | 3 | 14982 | 1358 | 1473 | 134.81 | 100.0% |
| specialized-multi-stage | 3 | 576 | 1417 | 1429 | 103.69 | 100.0% |

## Reproduce or extend

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/02-multi-stage-build-structure 10
python3 benchmarks/common/recommend.py benchmarks/02-multi-stage-build-structure/results/raw.csv
```
