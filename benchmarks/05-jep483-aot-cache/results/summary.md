# Results summary: 05-jep483-aot-cache

## Recommendation

✅ **Recommended:** `without-aot-cache` — metric-driven (primary weight: **startup time**)

## Results table

| Variant | Runs | Build avg (ms) | Startup avg (ms) | Startup p95 (ms) | Image MB | Success |
|---|---:|---:|---:|---:|---:|---:|
| with-aot-cache | 8 | 700 | 1288 | 1437 | 103.02 | 100.0% |
| without-aot-cache | 8 | 592 | 1222 | 1437 | 90.49 | 100.0% |

> **Context:** The AOT cache is architecture-specific and regenerated at build time.
> A marginal startup difference here reflects a warm Docker layer cache run.
> The benefit is more pronounced at cold JVM start on a fresh container host.

## Reproduce or extend

```bash
cd /Users/afshin/IdeaProjects/sandbox/java-spring-docker
bash benchmarks/common/run_scenario.sh benchmarks/05-jep483-aot-cache 10
python3 benchmarks/common/recommend.py benchmarks/05-jep483-aot-cache/results/raw.csv
```
