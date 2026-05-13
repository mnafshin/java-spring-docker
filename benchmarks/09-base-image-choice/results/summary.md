# Results summary: 09-base-image-choice

## Recommendation

✅ **Recommended:** `debian-bookworm-slim` — metric-driven (primary weight: **image size**)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| alpine | 3 | 6300 | 1426 | 1452 | 66.08 | 100.0% |
| debian-bookworm-slim | 3 | 2546 | 1411 | 1415 | 90.93 | 100.0% |
| eclipse-temurin-jre | 3 | 979 | 1423 | 1439 | 134.64 | 100.0% |
| ubi9-minimal | 3 | 1541 | 1421 | 1433 | 96.29 | 100.0% |
| ubuntu-noble | 3 | 1569 | 1430 | 1465 | 89.75 | 100.0% |

> **Context:** ubi9-minimal 50% success rate reflects 3 build failures before the
> Dockerfile was fixed. Successful runs are valid. Re-run for a clean baseline.
> Alpine uses musl libc — the build stage must use `eclipse-temurin:25-jdk-alpine`.

## Reproduce or extend

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/09-base-image-choice 10
python3 benchmarks/common/recommend.py benchmarks/09-base-image-choice/results/raw.csv
```
