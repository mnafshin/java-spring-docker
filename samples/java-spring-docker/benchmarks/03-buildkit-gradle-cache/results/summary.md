# Results summary: 03-buildkit-gradle-cache

## Recommendation

✅ **Recommended:** `with-buildkit-maven-cache` — metric-driven (primary weight: **build time**)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| with-buildkit-cache | 13 | 622 | 1454 | 1813 | 100.40 | 100.0% |
| with-buildkit-maven-cache | 2 | - | - | - | - | 0.0% |
| without-buildkit-cache | 13 | 3410 | 1425 | 1440 | 100.40 | 100.0% |
| without-buildkit-maven-cache | 2 | - | - | - | - | 0.0% |

## Reproduce or extend

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/03-buildkit-gradle-cache 10
python3 benchmarks/common/recommend.py benchmarks/03-buildkit-gradle-cache/results/raw.csv
```
