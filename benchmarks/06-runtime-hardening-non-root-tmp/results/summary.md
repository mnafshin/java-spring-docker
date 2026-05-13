# Results summary: 06-runtime-hardening-non-root-tmp

## Recommendation

✅ **Recommended:** `hardened-non-root` — policy decision (security / reliability, not metric-driven)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| hardened-non-root | 5 | 618 | 1204 | 1596 | 103.02 | 100.0% |
| root-runtime | 5 | 1001 | 1199 | 1593 | 103.02 | 100.0% |

## Reproduce or extend

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/06-runtime-hardening-non-root-tmp 10
python3 benchmarks/common/recommend.py benchmarks/06-runtime-hardening-non-root-tmp/results/raw.csv
```
