# Results summary: 05-jep483-aot-cache

## Recommendation

✅ **Recommended:** `minimal-app` — metric-driven (primary weight: **startup time**)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| minimal-app | 17 | 585 | 1455 | 2026 | 86.40 | 100.0% |
| with-aot-cache | 17 | 636 | 1429 | 1462 | 99.41 | 88.2% |
| without-aot-cache | 17 | 590 | 1509 | 1730 | 86.40 | 88.2% |

> **Context:** This scenario is now the canonical complex-app AOT benchmark.
> Use at least 15 runs (`--profile full`) for stable startup deltas.
> Compare startup gain against added build complexity before rollout.

## Reproduce or extend

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/05-jep483-aot-cache 10
python3 benchmarks/common/recommend.py benchmarks/05-jep483-aot-cache/results/raw.csv
```
