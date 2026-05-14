# Results summary: 09-base-image-choice

## Recommendation

✅ **Recommended:** `debian-bookworm-slim` — metric-driven (primary weight: **image size**)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| alpine | 15 | 2007 | 1561 | 2023 | 66.08 | 100.0% |
| debian-bookworm-slim | 15 | 1357 | 1464 | 1750 | 87.51 | 100.0% |
| eclipse-temurin-jre | 15 | 955 | 1486 | 2018 | 131.24 | 100.0% |
| ubi9-minimal | 15 | 1035 | 1637 | 2634 | 96.29 | 100.0% |
| ubuntu-noble | 15 | 1200 | 1607 | 1752 | 87.85 | 100.0% |

> **Context:** ubi9-minimal 50% success rate reflects 3 build failures before the
> Dockerfile was fixed. Successful runs are valid. Re-run for a clean baseline.
> Alpine uses musl libc — the build stage must use `eclipse-temurin:25-jdk-alpine`.

## Reproduce or extend

```bash
cd /path/to/your-java25-project
bash benchmarks/common/run_scenario.sh benchmarks/09-base-image-choice 10
python3 benchmarks/common/recommend.py benchmarks/09-base-image-choice/results/raw.csv
```
