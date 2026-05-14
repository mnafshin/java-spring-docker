# Results summary: 04-custom-jre-jlink

## Recommendation

✅ **Recommended:** `with-jlink-runtime` — metric-driven (primary weight: **image size**)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| with-jlink-runtime | 15 | 607 | 1423 | 1437 | 100.40 | 86.7% |
| without-jlink-runtime | 15 | 1140 | 1446 | 1762 | 144.38 | 86.7% |

## Reproduce or extend

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/04-custom-jre-jlink 10
python3 benchmarks/common/recommend.py benchmarks/04-custom-jre-jlink/results/raw.csv
```
