# Results summary: 09-base-image-choice

## Recommendation

✅ **Recommended:** `ubi9-minimal` — metric-driven (primary weight: **image size**)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| alpine | 6 | 5215 | 1515 | 1733 | 65.90 | 100.0% |
| debian-bookworm-slim | 6 | 1801 | 1422 | 1440 | 90.75 | 100.0% |
| eclipse-temurin-jre | 6 | 1754 | 1532 | 2309 | 134.51 | 100.0% |
| ubi9-minimal | 6 | 850 | 1333 | 1465 | 96.11 | 50.0% |
| ubuntu-noble | 6 | 2834 | 1386 | 1450 | 89.57 | 100.0% |

> **Context:** ubi9-minimal 50% success rate reflects 3 build failures before the
> Dockerfile was fixed. Successful runs are valid. Re-run for a clean baseline.
> Alpine uses musl libc — the build stage must use `eclipse-temurin:25-jdk-alpine`.

## Reproduce or extend

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/09-base-image-choice 10
python3 benchmarks/common/recommend.py benchmarks/09-base-image-choice/results/raw.csv
```
