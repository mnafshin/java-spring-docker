# Results summary: 02-multi-stage-build-structure

## Recommendation

✅ **Recommended:** `specialized-multi-stage` — metric-driven (primary weight: **image size**)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| simple-two-stage | 15 | 4135 | 1240 | 1455 | 131.54 | 86.7% |
| specialized-multi-stage | 15 | 645 | 1428 | 1449 | 100.40 | 86.7% |

## Reproduce or extend

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/02-multi-stage-build-structure 10
python3 benchmarks/common/recommend.py benchmarks/02-multi-stage-build-structure/results/raw.csv
```
