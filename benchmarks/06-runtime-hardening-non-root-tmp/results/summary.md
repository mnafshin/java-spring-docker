# Results summary: 06-runtime-hardening-non-root-tmp

## Recommendation

✅ **Recommended:** `hardened-non-root` — policy decision (security / reliability, not metric-driven)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| hardened-non-root | 15 | 604 | 1620 | 1712 | 100.40 | 86.7% |
| root-runtime | 15 | 955 | 1485 | 1712 | 100.40 | 86.7% |

## Reproduce or extend

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/06-runtime-hardening-non-root-tmp 10
python3 benchmarks/common/recommend.py benchmarks/06-runtime-hardening-non-root-tmp/results/raw.csv
```
