# Results summary: 06-runtime-hardening-non-root-tmp

## Recommendation

✅ **Recommended:** `hardened-non-root` — policy decision (security / reliability, not metric-driven)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| hardened-non-root | 3 | 602 | 1420 | 1441 | 103.69 | 100.0% |
| root-runtime | 3 | 1409 | 1424 | 1426 | 103.69 | 100.0% |

## Reproduce or extend

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/06-runtime-hardening-non-root-tmp 10
python3 benchmarks/common/recommend.py benchmarks/06-runtime-hardening-non-root-tmp/results/raw.csv
```
